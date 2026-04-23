#!/usr/bin/env python3
"""
从PostgreSQL judgment_entities和judgment_relations导入知识图谱到Neo4j
正确的导入脚本
"""

import logging
import time

from neo4j import GraphDatabase
from psycopg2 import pool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JudgmentGraphImporter:
    """判决图谱导入器"""

    def __init__(self):
        """初始化连接"""
        # PostgreSQL连接池
        self.pg_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'legal_world_model',
            'user': 'postgres',
            'password': 'nxLVXyZ3e87L0kE8Xqx3AB9NK1z74pwOdjugqpc7hc'
        }

        # Neo4j连接
        self.neo4j_uri = 'bolt://localhost:7687'
        self.neo4j_user = 'neo4j'
        self.neo4j_password = 'athena_neo4j_2024'

        self.pg_pool = None
        self.neo4j_driver = None

    def connect(self):
        """建立数据库连接"""
        try:
            # PostgreSQL连接池
            logger.info("🔗 创建PostgreSQL连接池...")
            self.pg_pool = pool.SimpleConnectionPool(1, 10, **self.pg_config)
            logger.info("✅ PostgreSQL连接池创建成功")

            # Neo4j连接
            logger.info("🔗 连接Neo4j...")
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j连接成功")

        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self.pg_pool:
            self.pg_pool.closeall()
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def clear_neo4j(self):
        """清空Neo4j中的所有数据"""
        logger.info("🗑️  清空Neo4j数据库...")

        with self.neo4j_driver.session() as session:
            # 删除所有关系
            result = session.run("MATCH ()-[r]->() DELETE r RETURN count(r) as count")
            count = result.single()['count']
            logger.info(f"   删除关系: {count}条")

            # 删除所有节点
            result = session.run("MATCH (n) DELETE n RETURN count(n) as count")
            count = result.single()['count']
            logger.info(f"   删除节点: {count}个")

        logger.info("✅ Neo4j已清空")

    def create_constraints(self):
        """创建Neo4j约束"""
        logger.info("⚙️  创建Neo4j约束...")

        with self.neo4j_driver.session() as session:
            # Entity节点约束
            try:
                session.run("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
                logger.info("   ✅ Entity: id唯一约束")
            except Exception as e:
                logger.warning(f"   ⚠️  Entity约束创建失败: {e}")

            # Case节点约束
            try:
                session.run("CREATE CONSTRAINT case_id IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE")
                logger.info("   ✅ Case: id唯一约束")
            except Exception as e:
                logger.warning(f"   ⚠️  Case约束创建失败: {e}")

    def import_entities(self, batch_size=10000, limit=None):
        """导入实体节点

        Args:
            batch_size: 批量大小
            limit: 限制导入数量（None表示全部导入）
        """
        logger.info("📦 开始导入Entity节点...")

        conn = self.pg_pool.getconn()

        # 获取总数（使用普通游标）
        count_cursor = conn.cursor()
        count_cursor.execute("SELECT COUNT(*) FROM judgment_entities")
        total_count_full = count_cursor.fetchone()[0]
        count_cursor.close()

        total_count = total_count_full
        if limit:
            total_count = min(total_count_full, limit)
            logger.info(f"   限制导入数量: {limit}")

        logger.info(f"   总计: {total_count}个实体（数据库共{total_count_full:,}个）")

        # 查询实体数据（使用命名游标进行流式读取）
        cursor = conn.cursor(name='entity_cursor', withhold=True)
        query = """
        SELECT id, judgment_id, entity_text, entity_type, start_pos, end_pos, confidence
        FROM judgment_entities
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)

        batch = []
        imported_count = 0

        with self.neo4j_driver.session() as session:
            start_time = time.time()

            for row in cursor:
                entity_id, judgment_id, entity_text, entity_type, start_pos, end_pos, confidence = row

                # 创建Cypher语句
                batch.append({
                    'id': str(entity_id),
                    'judgment_id': judgment_id,
                    'text': entity_text[:500] if entity_text else '',  # 限制文本长度
                    'type': entity_type or 'UNKNOWN',
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'confidence': float(confidence) if confidence else 0.0
                })

                # 批量导入
                if len(batch) >= batch_size:
                    self._create_entities_batch(session, batch)
                    imported_count += len(batch)
                    logger.info(f"   进度: {imported_count}/{total_count} ({imported_count*100//total_count}%)")
                    batch = []

            # 导入剩余数据
            if batch:
                self._create_entities_batch(session, batch)
                imported_count += len(batch)

            elapsed = time.time() - start_time
            logger.info(f"✅ Entity导入完成: {imported_count}个节点")
            logger.info(f"   耗时: {elapsed:.2f}秒")
            logger.info(f"   速度: {imported_count/elapsed:.0f} 节点/秒")

        cursor.close()
        self.pg_pool.putconn(conn)

    def _create_entities_batch(self, session, batch):
        """批量创建Entity节点"""
        session.run("""
        UNWIND $batch AS data
        MERGE (e:Entity {id: data.id})
        SET e.judgment_id = data.judgment_id,
            e.text = data.text,
            e.type = data.type,
            e.start_pos = data.start_pos,
            e.end_pos = data.end_pos,
            e.confidence = data.confidence
        """, batch=batch)

    def import_relations(self, batch_size=5000):
        """导入关系

        Args:
            batch_size: 批量大小
        """
        logger.info("📦 开始导入关系...")

        conn = self.pg_pool.getconn()

        # 获取总数（使用普通游标）
        count_cursor = conn.cursor()
        count_cursor.execute("SELECT COUNT(*) FROM judgment_relations")
        total_count = count_cursor.fetchone()[0]
        count_cursor.close()

        logger.info(f"   总计: {total_count}条关系")

        # 查询关系数据（使用命名游标进行流式读取）
        cursor = conn.cursor(name='relation_cursor', withhold=True)
        query = """
        SELECT id, judgment_id, source_entity, target_entity, relation_type, confidence, evidence
        FROM judgment_relations
        ORDER BY judgment_id
        """

        cursor.execute(query)

        batch = []
        imported_count = 0

        with self.neo4j_driver.session() as session:
            start_time = time.time()

            for row in cursor:
                rel_id, judgment_id, source_entity, target_entity, relation_type, confidence, evidence = row

                # 创建Cypher语句
                batch.append({
                    'source_text': str(source_entity)[:500] if source_entity else '',
                    'target_text': str(target_entity)[:500] if target_entity else '',
                    'type': relation_type or 'RELATED_TO',
                    'judgment_id': judgment_id,
                    'confidence': float(confidence) if confidence else 0.0
                })

                # 批量导入
                if len(batch) >= batch_size:
                    self._create_relations_batch(session, batch)
                    imported_count += len(batch)
                    logger.info(f"   进度: {imported_count}/{total_count} ({imported_count*100//total_count}%)")
                    batch = []

            # 导入剩余数据
            if batch:
                self._create_relations_batch(session, batch)
                imported_count += len(batch)

            elapsed = time.time() - start_time
            logger.info(f"✅ 关系导入完成: {imported_count}条")
            logger.info(f"   耗时: {elapsed:.2f}秒")
            logger.info(f"   速度: {imported_count/elapsed:.0f} 条/秒")

        cursor.close()
        self.pg_pool.putconn(conn)

    def _create_relations_batch(self, session, batch):
        """批量创建关系"""
        session.run("""
        UNWIND $batch AS data
        MATCH (source:Entity {text: data.source_text})
        MATCH (target:Entity {text: data.target_text})
        WITH source, target, data
        WHERE source IS NOT NULL AND target IS NOT NULL
        CREATE (source)-[r:RELATION {
            type: data.type,
            judgment_id: data.judgment_id,
            confidence: data.confidence
        }]->(target)
        """, batch=batch)

    def verify_import(self):
        """验证导入结果"""
        logger.info("🔍 验证导入结果...")

        with self.neo4j_driver.session() as session:
            # 节点统计
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count")
            logger.info("   节点统计:")
            total_nodes = 0
            for record in result:
                labels = record['labels']
                count = record['count']
                label = labels[0] if labels else 'Unknown'
                total_nodes += count
                logger.info(f"     {label}: {count:,}个")
            logger.info(f"     总计: {total_nodes:,}个节点")

            # 关系统计
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count")
            logger.info("   关系统计:")
            total_rels = 0
            for record in result:
                rel_type = record['type']
                count = record['count']
                total_rels += count
                logger.info(f"     {rel_type}: {count:,}条")
            logger.info(f"     总计: {total_rels:,}条关系")

        return total_nodes, total_rels

    def run_import(self, entity_limit=None):
        """执行完整导入流程

        Args:
            entity_limit: 限制实体导入数量（None表示全部）
        """
        try:
            # 连接数据库
            self.connect()

            # 清空Neo4j
            self.clear_neo4j()

            # 创建约束
            self.create_constraints()

            # 导入实体
            self.import_entities(limit=entity_limit)

            # 导入关系
            self.import_relations()

            # 验证导入
            nodes, relations = self.verify_import()

            logger.info("=" * 60)
            logger.info("🎉 导入完成!")
            logger.info(f"   节点: {nodes:,}个")
            logger.info(f"   关系: {relations:,}条")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            raise
        finally:
            self.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='导入判决图谱到Neo4j')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制实体导入数量（默认全部）')
    parser.add_argument('--test', action='store_true',
                        help='测试模式：限制导入10万实体')

    args = parser.parse_args()

    # 测试模式限制
    limit = args.limit
    if args.test:
        limit = 100000
        logger.info("🧪 测试模式: 限制导入10万个实体")

    importer = JudgmentGraphImporter()
    importer.run_import(entity_limit=limit)


if __name__ == "__main__":
    main()
