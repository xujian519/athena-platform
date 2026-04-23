#!/usr/bin/env python3
"""
OpenClaw图谱导入脚本
从PostgreSQL的legal_world_model数据库导入数据到Neo4j
重建OpenClaw知识图谱（40,034节点+407,744关系）
"""

import logging
import time

import psycopg2
from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenClawGraphImporter:
    """OpenClaw图谱导入器"""

    def __init__(self):
        """初始化连接"""
        # PostgreSQL连接配置
        self.pg_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'legal_world_model',
            'user': 'postgres',
            'password': 'nxLVXyZ3e87L0kE8Xqx3AB9NK1z74pwOdjugqpc7hc'
        }

        # Neo4j连接配置
        self.neo4j_uri = 'bolt://localhost:7687'
        self.neo4j_user = 'neo4j'
        self.neo4j_password = 'athena_neo4j_2024'

        self.pg_conn = None
        self.neo4j_driver = None

        # 统计信息
        self.stats = {
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': 0
        }

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

    def clear_graph(self):
        """清空Neo4j图谱"""
        logger.info("🗑️  清空Neo4j图谱...")
        with self.neo4j_driver.session() as session:
            # 删除所有关系和节点
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("✅ 图谱已清空")

    def create_constraints(self):
        """创建约束和索引"""
        logger.info("🔧 创建约束和索引...")
        with self.neo4j_driver.session() as session:
            # 为常见节点类型创建唯一性约束
            constraints = [
                "CREATE CONSTRAINT case_id IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT judgment_id IF NOT EXISTS FOR (j:SupremeCourtJudgment) REQUIRE j.id IS UNIQUE",
                "CREATE CONSTRAINT guideline_id IF NOT EXISTS FOR (g:GuidelineRule) REQUIRE g.id IS UNIQUE",
                "CREATE CONSTRAINT ipc_id IF NOT EXISTS FOR (i:IPC) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ 创建约束: {constraint[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️  约束可能已存在: {e}")

    def import_patent_judgments(self, batch_size: int = 1000):
        """导入专利判决数据（Case节点）"""
        logger.info("📚 开始导入专利判决数据...")

        query = """
        SELECT
            judgment_id,
            case_cause,
            title,
            plaintiff,
            defendant
        FROM patent_judgments
        ORDER BY judgment_id
        LIMIT 10000
        """

        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute(query)

        total_count = 0

        with self.neo4j_driver.session() as session:
            for row in pg_cursor:
                judgment_id, cause, title, plaintiff, defendant = row

                # 创建Case节点
                cypher = """
                MERGE (c:Case {id: $id})
                SET c.case_cause = $cause,
                    c.title = $title,
                    c.plaintiff = $plaintiff,
                    c.defendant = $defendant
                """

                session.run(cypher, {
                    'id': str(judgment_id),
                    'cause': cause,
                    'title': title,
                    'plaintiff': plaintiff,
                    'defendant': defendant
                })

                total_count += 1
                self.stats['nodes_created'] += 1

                if total_count % batch_size == 0:
                    logger.info(f"   已导入 {total_count} 条Case数据")

        logger.info(f"✅ 专利判决数据导入完成，共 {total_count} 条")

    def import_judgment_entities(self, batch_size: int = 5000):
        """导入判决实体（Entity节点）"""
        logger.info("🏷️  开始导入判决实体...")

        query = """
        SELECT
            id,
            entity_text,
            entity_type
        FROM judgment_entities
        ORDER BY id
        LIMIT 50000
        """

        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute(query)

        total_count = 0

        with self.neo4j_driver.session() as session:
            for row in pg_cursor:
                entity_id, entity_text, entity_type = row

                cypher = """
                MERGE (e:Entity {id: $id})
                SET e.text = $text,
                    e.type = $type
                """

                session.run(cypher, {
                    'id': str(entity_id),
                    'text': entity_text[:500] if entity_text else '',
                    'type': entity_type or 'UNKNOWN'
                })

                total_count += 1
                self.stats['nodes_created'] += 1

                if total_count % batch_size == 0:
                    logger.info(f"   已导入 {total_count} 条Entity数据")

        logger.info(f"✅ 判决实体导入完成，共 {total_count} 条")

    def import_patent_invalid_entities(self, batch_size: int = 5000):
        """导入专利无效实体"""
        logger.info("🔍 开始导入专利无效实体...")

        query = """
        SELECT
            id,
            entity_text,
            entity_type
        FROM patent_invalid_entities
        ORDER BY id
        LIMIT 50000
        """

        # 使用服务器端游标
        pg_cursor = self.pg_conn.cursor(name='patent_invalid_cursor')
        pg_cursor.execute(query)

        total_count = 0

        with self.neo4j_driver.session() as session:
            for row in pg_cursor:
                entity_id, entity_text, entity_type = row

                cypher = """
                MERGE (e:PatentEntity {id: $id})
                SET e.text = $text,
                    e.type = $type
                """

                session.run(cypher, {
                    'id': str(entity_id),
                    'text': entity_text[:500] if entity_text else '',
                    'type': entity_type or 'UNKNOWN'
                })

                total_count += 1
                self.stats['nodes_created'] += 1

                if total_count % batch_size == 0:
                    logger.info(f"   已导入 {total_count} 条PatentEntity数据")

        logger.info(f"✅ 专利无效实体导入完成，共 {total_count} 条")

    def import_judgment_relations(self, batch_size: int = 5000):
        """导入判决关系"""
        logger.info("🔗 开始导入判决关系...")

        query = """
        SELECT
            source_entity,
            target_entity,
            relation_type,
            confidence
        FROM judgment_relations
        ORDER BY id
        LIMIT 50000
        """

        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute(query)

        total_count = 0

        with self.neo4j_driver.session() as session:
            for row in pg_cursor:
                source_entity, target_entity, relation_type, confidence = row

                # 通过文本查找实体并创建关系
                cypher = """
                MATCH (source:Entity {text: $source_text})
                MATCH (target:Entity {text: $target_text})
                MERGE (source)-[r:RELATED_TO]->(target)
                SET r.type = $relation_type,
                    r.confidence = $confidence
                """

                try:
                    session.run(cypher, {
                        'source_text': source_entity[:500] if source_entity else '',
                        'target_text': target_entity[:500] if target_entity else '',
                        'relation_type': relation_type,
                        'confidence': float(confidence) if confidence else 1.0
                    })
                    total_count += 1
                    self.stats['relationships_created'] += 1

                    if total_count % batch_size == 0:
                        logger.info(f"   已导入 {total_count} 条关系")
                except Exception as e:
                    self.stats['errors'] += 1
                    if self.stats['errors'] <= 10:
                        logger.warning(f"⚠️  关系创建失败: {e}")

        logger.info(f"✅ 判决关系导入完成，共 {total_count} 条")

    def import_legal_articles(self, batch_size: int = 1000):
        """导入法律条款"""
        logger.info("⚖️  开始导入法律条款...")

        query = """
        SELECT
            article_id,
            law_title,
            content
        FROM legal_articles_v2
        ORDER BY article_id
        LIMIT 10000
        """

        pg_cursor = self.pg_conn.cursor()
        pg_cursor.execute(query)

        total_count = 0

        with self.neo4j_driver.session() as session:
            for row in pg_cursor:
                article_id, law_title, content = row

                cypher = """
                MERGE (a:LegalArticle {id: $id})
                SET a.title = $title,
                    a.content = $content
                """

                session.run(cypher, {
                    'id': str(article_id),
                    'title': law_title,
                    'content': (content or '')[:1000]  # 限制长度
                })

                total_count += 1
                self.stats['nodes_created'] += 1

                if total_count % batch_size == 0:
                    logger.info(f"   已导入 {total_count} 条LegalArticle数据")

        logger.info(f"✅ 法律条款导入完成，共 {total_count} 条")

    def verify_graph(self):
        """验证图谱数据"""
        logger.info("🔍 验证图谱数据...")

        with self.neo4j_driver.session() as session:
            # 统计节点
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_result.single()['count']
            logger.info(f"✅ 节点总数: {node_count}")

            # 统计关系
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()['count']
            logger.info(f"✅ 关系总数: {rel_count}")

            # 节点类型分布
            type_result = session.run("""
                MATCH (n)
                RETURN labels(n) as types, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """)

            logger.info("📊 节点类型分布:")
            for record in type_result:
                types = record['types']
                count = record['count']
                logger.info(f"   {types[0] if types else 'Unknown'}: {count}")

    def run_full_import(self):
        """执行完整导入"""
        start_time = time.time()

        try:
            # 连接数据库
            self.connect()

            # 清空图谱
            self.clear_graph()

            # 创建约束
            self.create_constraints()

            # 导入数据
            logger.info("=" * 60)
            logger.info("🚀 开始OpenClaw图谱导入")
            logger.info("=" * 60)

            # 1. 导入专利判决
            self.import_patent_judgments()

            # 2. 导入判决实体
            self.import_judgment_entities()

            # 3. 导入专利无效实体（暂时跳过，数据量太大236万条）
            # self.import_patent_invalid_entities()
            logger.info("⏭️  跳过专利无效实体导入（数据量太大：236万条）")

            # 4. 导入判决关系
            self.import_judgment_relations()

            # 5. 导入法律条款
            self.import_legal_articles()

            # 验证图谱
            self.verify_graph()

            # 打印统计信息
            elapsed_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info("📊 导入完成统计")
            logger.info("=" * 60)
            logger.info(f"✅ 节点创建: {self.stats['nodes_created']}")
            logger.info(f"✅ 关系创建: {self.stats['relationships_created']}")
            logger.info(f"⚠️  错误数量: {self.stats['errors']}")
            logger.info(f"⏱️  总耗时: {elapsed_time:.2f}秒")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            raise
        finally:
            self.close()


def main():
    """主函数"""
    importer = OpenClawGraphImporter()
    importer.run_full_import()


if __name__ == "__main__":
    main()
