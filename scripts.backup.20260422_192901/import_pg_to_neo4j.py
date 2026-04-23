#!/usr/bin/env python3
"""
PostgreSQL到Neo4j数据导入脚本
使用source_file字段作为标识确保数据完整性
"""

import logging
import time
from typing import Dict, List, Optional

import psycopg2
from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PgToNeo4jImporter:
    """PostgreSQL到Neo4j的数据导入器"""

    def __init__(self):
        """初始化连接"""
        # PostgreSQL连接配置
        self.pg_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'postgres'
        }

        # Neo4j连接配置
        self.neo4j_uri = 'bolt://localhost:7687'
        self.neo4j_user = 'neo4j'
        self.neo4j_password = 'athena_neo4j_2024'

        self.pg_conn = None
        self.neo4j_driver = None

    def connect(self):
        """建立数据库连接"""
        try:
            # 连接PostgreSQL
            logger.info("🔗 连接PostgreSQL...")
            self.pg_conn = psycopg2.connect(**self.pg_config)
            logger.info("✅ PostgreSQL连接成功")

            # 连接Neo4j
            logger.info("🔗 连接Neo4j...")
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # 测试连接
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j连接成功")

        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("✅ PostgreSQL连接已关闭")
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info("✅ Neo4j连接已关闭")

    def import_law_documents(self, batch_size: int = 1000, limit: Optional[int] = None):
        """导入法律文档"""
        logger.info("📚 开始导入法律文档...")

        query = """
        SELECT
            article_id,
            law_id,
            article_title,
            content,
            category,
            source_file,
            article_number,
            article_order,
            paragraph_count,
            created_at
        FROM legal_articles_v2
        ORDER BY source_file, article_order
        """

        if limit:
            query += f" LIMIT {limit}"

        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute(query)

        total = 0
        batch = []

        with self.neo4j_driver.session() as session:
            while True:
                rows = pg_cursor.fetchmany(batch_size)
                if not rows:
                    break

                for row in rows:
                    (article_id, law_id, article_title, content, category,
                     source_file, article_number, article_order, paragraph_count,
                     created_at) = row

                    # 创建Cypher查询
                    cypher = """
                    MERGE (d:LawDocument {article_id: $article_id})
                    SET d.law_id = $law_id,
                        d.article_title = $article_title,
                        d.content = $content,
                        d.category = $category,
                        d.source_file = $source_file,
                        d.article_number = $article_number,
                        d.article_order = $article_order,
                        d.paragraph_count = $paragraph_count,
                        d.created_at = $created_at,
                        d.imported_at = datetime()
                    """

                    session.run(cypher, parameters={
                        'article_id': article_id,
                        'law_id': law_id,
                        'article_title': article_title,
                        'content': content,
                        'category': category,
                        'source_file': source_file,
                        'article_number': article_number,
                        'article_order': article_order,
                        'paragraph_count': paragraph_count,
                        'created_at': created_at
                    })

                    total += 1

                logger.info(f"   已导入 {total} 条法律文档")

        pg_cursor.close()
        logger.info(f"✅ 法律文档导入完成，共 {total} 条")

    def import_judgment_courts(self, batch_size: int = 1000):
        """导入法院信息"""
        logger.info("🏛️ 开始导入法院信息...")

        query = """
        SELECT DISTINCT
            court_name,
            COUNT(*) as case_count,
            MIN(created_at) as first_case,
            MAX(created_at) as last_case
        FROM judgment_courts
        GROUP BY court_name
        """

        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute(query)

        total = 0

        with self.neo4j_driver.session() as session:
            while True:
                rows = pg_cursor.fetchmany(batch_size)
                if not rows:
                    break

                for row in rows:
                    court_name, case_count, first_case, last_case = row

                    cypher = """
                    MERGE (c:Court {name: $court_name})
                    SET c.case_count = $case_count,
                        c.first_case = $first_case,
                        c.last_case = $last_case,
                        c.imported_at = datetime()
                    """

                    session.run(cypher, parameters={
                        'court_name': court_name,
                        'case_count': case_count,
                        'first_case': first_case,
                        'last_case': last_case
                    })

                    total += 1

                logger.info(f"   已导入 {total} 个法院")

        pg_cursor.close()
        logger.info(f"✅ 法院信息导入完成，共 {total} 个")

    def create_constraints(self):
        """创建Neo4j约束和索引"""
        logger.info("🔧 创建Neo4j约束和索引...")

        constraints = [
            "CREATE CONSTRAINT law_document_id IF NOT EXISTS FOR (d:LawDocument) REQUIRE d.article_id IS UNIQUE",
            "CREATE CONSTRAINT court_name IF NOT EXISTS FOR (c:Court) REQUIRE c.name IS UNIQUE",
            "CREATE INDEX law_document_law_id IF NOT EXISTS FOR (d:LawDocument) ON (d.law_id)",
            "CREATE INDEX law_document_category IF NOT EXISTS FOR (d:LawDocument) ON (d.category)",
            "CREATE INDEX law_document_source_file IF NOT EXISTS FOR (d:LawDocument) ON (d.source_file)",
        ]

        with self.neo4j_driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"   ✅ {constraint[:50]}...")
                except Exception as e:
                    logger.warning(f"   ⚠️ 约束可能已存在: {e}")

        logger.info("✅ 约束和索引创建完成")

    def verify_import(self):
        """验证导入结果"""
        logger.info("🔍 验证导入结果...")

        with self.neo4j_driver.session() as session:
            # 统计导入的节点数
            result = session.run("MATCH (d:LawDocument) RETURN count(*) as count")
            law_count = result.single()['count']
            logger.info(f"   LawDocument: {law_count} 个")

            result = session.run("MATCH (c:Court) RETURN count(*) as count")
            court_count = result.single()['count']
            logger.info(f"   Court: {court_count} 个")

        # 与PostgreSQL对比
        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute("SELECT COUNT(*) FROM legal_articles_v2")
        pg_law_count = pg_cursor.fetchone()[0]
        logger.info(f"   PostgreSQL法律文档: {pg_law_count} 条")

        pg_cursor.execute("SELECT COUNT(DISTINCT court_name) FROM judgment_courts")
        pg_court_count = pg_cursor.fetchone()[0]
        logger.info(f"   PostgreSQL法院: {pg_court_count} 个")

        pg_cursor.close()

        logger.info("✅ 验证完成")


def main():
    """主函数"""
    import sys

    # 检查是否启用完整导入
    full_import = '--full' in sys.argv

    logger.info("🚀 开始从PostgreSQL导入数据到Neo4j")
    if full_import:
        logger.info("✨ 完整导入模式：将导入所有295,733条法律文档")
    else:
        logger.info("⚠️ 测试模式：仅导入1,000条记录")

    importer = PgToNeo4jImporter()

    try:
        # 连接数据库
        importer.connect()

        # 创建约束
        importer.create_constraints()

        # 导入法院信息
        importer.import_judgment_courts()

        # 导入法律文档
        if full_import:
            logger.info("📚 开始导入完整法律文档...")
            importer.import_law_documents(batch_size=5000)
        else:
            logger.info("⚠️ 测试模式：导入1000条")
            importer.import_law_documents(limit=1000)

        # 验证结果
        importer.verify_import()

        logger.info("✅ 数据导入完成！")

        if not full_import:
            logger.info("")
            logger.info("💡 要导入完整数据，请运行：")
            logger.info("   python3 scripts/import_pg_to_neo4j.py --full")

    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
        raise
    finally:
        importer.close()


if __name__ == "__main__":
    main()
