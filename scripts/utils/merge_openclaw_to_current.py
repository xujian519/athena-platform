#!/usr/bin/env python3
"""
合并OpenClaw数据到当前Neo4j数据库
从athena-neo4j-data卷读取OpenClaw数据，导入到athena-neo4j-dev
"""

import logging
import time

from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OpenClawDataMerger:
    """OpenClaw数据合并器"""

    def __init__(self):
        # 源数据库（OpenClaw数据）- 无认证
        self.source_uri = 'bolt://localhost:7688'
        self.source_auth = ()  # 无认证

        # 目标数据库（当前数据）
        self.target_uri = 'bolt://localhost:7687'
        self.target_user = 'neo4j'
        self.target_password = 'athena_neo4j_2024'

        self.source_driver = None
        self.target_driver = None

    def connect(self):
        """建立数据库连接"""
        logger.info("🔗 连接数据库...")

        # 连接源数据库（OpenClaw）- 无认证
        try:
            logger.info(f"   连接源数据库: {self.source_uri}")
            self.source_driver = GraphDatabase.driver(self.source_uri, auth=self.source_auth)
            with self.source_driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ 源数据库（OpenClaw）连接成功")
        except Exception as e:
            logger.error(f"❌ 源数据库连接失败: {e}")
            import traceback
            traceback.print_exc()
            raise

        # 连接目标数据库（当前）
        try:
            logger.info(f"   连接目标数据库: {self.target_uri}")
            self.target_driver = GraphDatabase.driver(
                self.target_uri,
                auth=(self.target_user, self.target_password)
            )
            with self.target_driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ 目标数据库（当前）连接成功")
        except Exception as e:
            logger.error(f"❌ 目标数据库连接失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def close(self):
        """关闭连接"""
        if self.source_driver:
            self.source_driver.close()
        if self.target_driver:
            self.target_driver.close()

    def check_source_data(self):
        """检查源数据统计"""
        logger.info("🔍 检查源数据统计...")

        with self.source_driver.session() as session:
            # 节点统计
            result = session.run("MATCH (n:OpenClawNode) RETURN count(n) as count")
            nodes = result.single()['count']
            logger.info(f"   OpenClawNode: {nodes:,}个")

            # 关系统计
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            relations = result.single()['count']
            logger.info(f"   关系: {relations:,}条")

            # 关系类型
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC")
            logger.info("   关系类型:")
            for record in result:
                logger.info(f"     {record['type']}: {record['count']:,}条")

        return nodes, relations

    def check_target_data(self):
        """检查目标数据统计"""
        logger.info("🔍 检查目标数据统计...")

        with self.target_driver.session() as session:
            # 节点统计
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count")
            logger.info("   节点类型:")
            total_nodes = 0
            for record in result:
                labels = record['labels']
                count = record['count']
                label = labels[0] if labels else 'Unknown'
                total_nodes += count
                logger.info(f"     {label}: {count:,}个")
            logger.info(f"   总计: {total_nodes:,}个节点")

            # 关系统计
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC")
            logger.info("   关系类型:")
            total_rels = 0
            for record in result:
                total_rels += record['count']
                logger.info(f"     {record['type']}: {record['count']:,}条")
            logger.info(f"   总计: {total_rels:,}条关系")

        return total_nodes, total_rels

    def merge_nodes(self, batch_size=1000):
        """合并OpenClaw节点"""
        logger.info("📦 开始合并OpenClaw节点...")

        with self.source_driver.session() as source_session:
            with self.target_driver.session() as target_session:
                # 获取总数
                result = source_session.run("MATCH (n:OpenClawNode) RETURN count(n) as count")
                total_count = result.single()['count']
                logger.info(f"   源数据: {total_count:,}个节点")

                # 分批读取和导入
                offset = 0
                imported_count = 0
                start_time = time.time()

                while offset < total_count:
                    # 从源数据库读取节点
                    result = source_session.run("""
                        MATCH (n:OpenClawNode)
                        RETURN n
                        SKIP $offset
                        LIMIT $limit
                    """, offset=offset, limit=batch_size)

                    batch = []
                    for record in result:
                        node = record['n']
                        # 提取所有属性
                        props = dict(node)
                        props['id'] = str(node.element_id)
                        batch.append(props)

                    # 批量创建到目标数据库
                    if batch:
                        target_session.run("""
                            UNWIND $batch AS data
                            MERGE (n:OpenClawNode {id: data.id})
                            SET n += data
                        """, batch=batch)

                        imported_count += len(batch)
                        logger.info(f"   进度: {imported_count}/{total_count} ({imported_count*100//total_count}%)")

                    offset += batch_size

                elapsed = time.time() - start_time
                logger.info(f"✅ OpenClaw节点合并完成: {imported_count:,}个")
                logger.info(f"   耗时: {elapsed:.2f}秒")
                logger.info(f"   速度: {imported_count/elapsed:.0f} 节点/秒")

    def merge_relationships(self, batch_size=1000):
        """合并OpenClaw关系"""
        logger.info("📦 开始合并OpenClaw关系...")

        with self.source_driver.session() as source_session:
            with self.target_driver.session() as target_session:
                # 获取总数
                result = source_session.run("MATCH ()-[r]->() RETURN count(r) as count")
                total_count = result.single()['count']
                logger.info(f"   源数据: {total_count:,}条关系")

                # 分批读取和导入
                offset = 0
                imported_count = 0
                skipped_count = 0
                start_time = time.time()

                while offset < total_count:
                    # 从源数据库读取关系
                    result = source_session.run("""
                        MATCH (a)-[r]->(b)
                        RETURN id(a) as source_id, id(b) as target_id, type(r) as rel_type, properties(r) as props
                        SKIP $offset
                        LIMIT $limit
                    """, offset=offset, limit=batch_size)

                    batch = []
                    source_ids = []
                    target_ids = []

                    for record in result:
                        source_ids.append(str(record['source_id']))
                        target_ids.append(str(record['target_id']))
                        batch.append({
                            'source_id': str(record['source_id']),
                            'target_id': str(record['target_id']),
                            'rel_type': record['rel_type'],
                            'props': dict(record['props'])
                        })

                    # 批量创建到目标数据库
                    if batch:
                        # 需要通过element_id匹配节点
                        created = 0
                        for item in batch:
                            try:
                                # 查找源节点和目标节点
                                result = target_session.run("""
                                    MATCH (s:OpenClawNode), (t:OpenClawNode)
                                    WHERE s.id = $source_id AND t.id = $target_id
                                    CREATE (s)-[r:{}]->(t)
                                    SET r += $props
                                    RETURN count(r) as count
                                """.format(item['rel_type']),
                                source_id=item['source_id'],
                                target_id=item['target_id'],
                                props=item['props']
                                )

                                if result.single()['count'] > 0:
                                    created += 1

                            except Exception:
                                skipped_count += 1

                        imported_count += created
                        logger.info(f"   进度: {imported_count}/{total_count} ({imported_count*100//total_count}%) | 跳过: {skipped_count}")

                    offset += batch_size

                elapsed = time.time() - start_time
                logger.info(f"✅ OpenClaw关系合并完成: {imported_count:,}条")
                logger.info(f"   跳过: {skipped_count}条")
                logger.info(f"   耗时: {elapsed:.2f}秒")
                logger.info(f"   速度: {imported_count/elapsed:.0f} 条/秒")

    def verify_merge(self):
        """验证合并结果"""
        logger.info("🔍 验证合并结果...")

        with self.target_driver.session() as session:
            # 节点统计
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC")
            logger.info("   合并后的节点统计:")
            total_nodes = 0
            for record in result:
                labels = record['labels']
                count = record['count']
                label = labels[0] if labels else 'Unknown'
                total_nodes += count
                logger.info(f"     {label}: {count:,}个")
            logger.info(f"   总计: {total_nodes:,}个节点")

            # 关系统计
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC")
            logger.info("   合并后的关系统计:")
            total_rels = 0
            for record in result:
                total_rels += record['count']
                logger.info(f"     {record['type']}: {record['count']:,}条")
            logger.info(f"   总计: {total_rels:,}条关系")

        return total_nodes, total_rels

    def run_merge(self):
        """执行完整合并流程"""
        try:
            # 建立数据库连接
            self.connect()

            # 检查源数据
            source_nodes, source_rels = self.check_source_data()

            # 检查目标数据
            target_nodes, target_rels = self.check_target_data()

            logger.info("=" * 60)
            logger.info("📊 合并预期结果:")
            logger.info(f"   节点: {target_nodes:,} + {source_nodes:,} = {target_nodes + source_nodes:,}")
            logger.info(f"   关系: {target_rels:,} + {source_rels:,} = {target_rels + source_rels:,}")
            logger.info("=" * 60)

            # 合并节点
            self.merge_nodes()

            # 合并关系
            self.merge_relationships()

            # 验证结果
            final_nodes, final_rels = self.verify_merge()

            logger.info("=" * 60)
            logger.info("🎉 合并完成!")
            logger.info(f"   节点: {final_nodes:,}个")
            logger.info(f"   关系: {final_rels:,}条")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 合并失败: {e}")
            raise
        finally:
            self.close()


def main():
    """主函数"""
    merger = OpenClawDataMerger()

    try:
        merger.run_merge()
    except Exception as e:
        logger.error(f"合并失败: {e}")


if __name__ == "__main__":
    main()
