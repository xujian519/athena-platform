#!/usr/bin/env python3
"""
优化的关系导入脚本
使用Neo4j全文索引快速匹配节点
"""

import logging
import time
from psycopg2 import pool
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OptimizedRelationImporter:
    """优化的关系导入器"""

    def __init__(self):
        self.pg_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'legal_world_model',
            'user': 'postgres',
            'password': 'nxLVXyZ3e87L0kE8Xqx3AB9NK1z74pwOdjugqpc7hc'
        }
        self.neo4j_uri = 'bolt://localhost:7687'
        self.neo4j_user = 'neo4j'
        self.neo4j_password = 'athena_neo4j_2024'
        self.pg_pool = None
        self.neo4j_driver = None

    def connect(self):
        """建立数据库连接"""
        logger.info("🔗 连接数据库...")
        self.pg_pool = pool.SimpleConnectionPool(1, 10, **self.pg_config)
        self.neo4j_driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        logger.info("✅ 连接成功")

    def close(self):
        """关闭连接"""
        if self.pg_pool:
            self.pg_pool.closeall()
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def create_text_index(self):
        """创建Entity.text的属性索引"""
        logger.info("⚙️  创建文本索引...")

        with self.neo4j_driver.session() as session:
            # 创建text属性索引（如果不存在）
            try:
                session.run("CREATE INDEX entity_text_index FOR (e:Entity) ON (e.text)")
                logger.info("   ✅ 文本索引创建成功")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("   ✅ 文本索引已存在")
                else:
                    logger.warning(f"   ⚠️  索引创建警告: {e}")

    def import_relations(self, batch_size=1000, limit=None):
        """导入关系（使用全文索引匹配）"""
        logger.info("📦 开始导入关系...")

        conn = self.pg_pool.getconn()

        # 获取总数
        count_cursor = conn.cursor()
        count_cursor.execute("SELECT COUNT(*) FROM judgment_relations")
        total_count_full = count_cursor.fetchone()[0]
        count_cursor.close()

        total_count = total_count_full
        if limit:
            total_count = min(total_count_full, limit)
            logger.info(f"   限制导入数量: {limit}")

        logger.info(f"   总计: {total_count}条关系（数据库共{total_count_full:,}条）")

        # 查询关系数据
        cursor = conn.cursor(name='relation_cursor', withhold=True)
        query = """
        SELECT id, judgment_id, source_entity, target_entity, relation_type, confidence
        FROM judgment_relations
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)

        batch = []
        imported_count = 0
        skipped_count = 0

        with self.neo4j_driver.session() as session:
            start_time = time.time()

            for row in cursor:
                rel_id, judgment_id, source_entity, target_entity, relation_type, confidence = row

                # 跳过空值
                if not source_entity or not target_entity:
                    skipped_count += 1
                    continue

                # 使用全文索引查找节点
                source_text = str(source_entity)[:500]
                target_text = str(target_entity)[:500]

                batch.append({
                    'source_text': source_text,
                    'target_text': target_text,
                    'type': relation_type or 'RELATED_TO',
                    'judgment_id': judgment_id,
                    'confidence': float(confidence) if confidence else 0.0
                })

                # 批量导入
                if len(batch) >= batch_size:
                    created, skipped = self._create_relations_batch(session, batch)
                    imported_count += created
                    skipped_count += skipped
                    logger.info(f"   进度: {imported_count}/{total_count} ({imported_count*100//total_count}%) | 跳过: {skipped_count}")
                    batch = []

            # 导入剩余数据
            if batch:
                created, skipped = self._create_relations_batch(session, batch)
                imported_count += created
                skipped_count += skipped

            elapsed = time.time() - start_time
            logger.info(f"✅ 关系导入完成: {imported_count}条")
            logger.info(f"   跳过: {skipped_count}条（节点未找到）")
            logger.info(f"   耗时: {elapsed:.2f}秒")
            logger.info(f"   速度: {imported_count/elapsed:.0f} 条/秒")

        cursor.close()
        self.pg_pool.putconn(conn)

    def _create_relations_batch(self, session, batch):
        """批量创建关系（使用文本索引）"""
        created = 0
        skipped = 0

        for data in batch:
            try:
                # 使用文本索引查找源节点
                source_result = session.run("""
                    MATCH (e:Entity {text: $source_text})
                    RETURN e
                    LIMIT 1
                """, source_text=data['source_text'])

                source_node = None
                for record in source_result:
                    source_node = record['e']
                    break

                if not source_node:
                    skipped += 1
                    continue

                # 使用文本索引查找目标节点
                target_result = session.run("""
                    MATCH (e:Entity {text: $target_text})
                    RETURN e
                    LIMIT 1
                """, target_text=data['target_text'])

                target_node = None
                for record in target_result:
                    target_node = record['e']
                    break

                if not target_node:
                    skipped += 1
                    continue

                # 创建关系
                session.run("""
                    MATCH (source), (target)
                    WHERE id(source) = $source_id AND id(target) = $target_id
                    CREATE (source)-[r:RELATION {
                        type: $type,
                        judgment_id: $judgment_id,
                        confidence: $confidence
                    }]->(target)
                """, source_id=source_node.id, target_id=target_node.id, **data)

                created += 1

            except Exception as e:
                skipped += 1
                logger.debug(f"   跳过关系: {e}")

        return created, skipped

    def verify_import(self):
        """验证导入结果"""
        logger.info("🔍 验证导入结果...")

        with self.neo4j_driver.session() as session:
            # 节点统计
            result = session.run("MATCH (n) RETURN count(n) as count")
            nodes = result.single()['count']
            logger.info(f"   节点: {nodes:,}个")

            # 关系统计
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            relations = result.single()['count']
            logger.info(f"   关系: {relations:,}条")

        return nodes, relations

    def run_import(self, relation_limit=None):
        """执行完整导入流程"""
        try:
            self.connect()

            # 创建文本索引
            self.create_text_index()

            # 导入关系
            self.import_relations(limit=relation_limit)

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

    parser = argparse.ArgumentParser(description='优化的关系导入')
    parser.add_argument('--limit', type=int, default=None, help='限制关系导入数量')
    parser.add_argument('--test', action='store_true', help='测试模式：限制导入1000条')

    args = parser.parse_args()

    limit = args.limit
    if args.test:
        limit = 1000
        logger.info("🧪 测试模式: 限制导入1000条关系")

    importer = OptimizedRelationImporter()
    importer.run_import(relation_limit=limit)


if __name__ == "__main__":
    main()
