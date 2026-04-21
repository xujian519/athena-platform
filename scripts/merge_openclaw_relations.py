#!/usr/bin/env python3
"""
快速合并OpenClaw关系到当前Neo4j数据库
使用更高效的批量导入方法
"""

import logging
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 连接配置
SOURCE_URI = 'bolt://localhost:7688'
TARGET_URI = 'bolt://localhost:7687'
TARGET_AUTH = ('neo4j', 'athena_neo4j_2024')


def main():
    """主函数"""
    logger.info("🔗 连接数据库...")

    # 源数据库（无认证）
    source_driver = GraphDatabase.driver(SOURCE_URI, auth=())
    # 目标数据库
    target_driver = GraphDatabase.driver(TARGET_URI, auth=TARGET_AUTH)

    try:
        # 1. 检查源关系统计
        logger.info("🔍 检查源关系...")
        with source_driver.session() as session:
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            source_count = result.single()['count']
            logger.info(f"   源关系: {source_count:,}条")

            # 获取关系类型
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC")
            logger.info("   关系类型分布:")
            for record in result:
                logger.info(f"     {record['type']}: {record['count']:,}条")

        # 2. 使用Neo4j的CALL {...} IN TRANSACTIONS批量导入
        logger.info("📦 开始合并关系...")
        logger.info("   这可能需要几分钟，请耐心等待...")

        with target_driver.session() as target_session:
            # 为每种关系类型分别导入
            rel_types = ['SIMILAR_TO', 'RELATED_TO', 'CITES', 'FREQUENTLY_DISCUSSES',
                        'DEFINES', 'BELONGS_TO', 'RELATES_TO', 'HIGH_RISK', 'FREQUENTLY_CITES']

            for rel_type in rel_types:
                logger.info(f"   导入 {rel_type} 关系...")

                # 使用CALL {...} IN TRANSACTIONS批量处理
                target_session.run(f"""
                    CALL {{
                        WITH '{rel_type}' AS rel_type
                        MATCH (s:OpenClawNode)-[r:{rel_type}]->(t:OpenClawNode)
                        RETURN s.id AS source_id, t.id AS target_id, properties(r) AS props
                        LIMIT 10000
                    }} IN TRANSACTIONS OF 1000 rows
                    CALL {{
                        WITH source_id, target_id, props
                        MATCH (s:OpenClawNode {{id: source_id}}), (t:OpenClawNode {{id: target_id}})
                        CREATE (s)-[r:{rel_type}]->(t)
                        SET r += props
                    }} IN TRANSACTIONS OF 1000 rows
                    RETURN count(*) as imported
                """)
                logger.info(f"   ✅ {rel_type} 导入完成")

        # 3. 验证结果
        logger.info("🔍 验证合并结果...")
        with target_driver.session() as session:
            # 节点统计
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC")
            logger.info("   节点统计:")
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
            logger.info("   关系统计:")
            total_rels = 0
            for record in result:
                total_rels += record['count']
                logger.info(f"     {record['type']}: {record['count']:,}条")
            logger.info(f"   总计: {total_rels:,}条关系")

        logger.info("=" * 60)
        logger.info("🎉 合并完成!")
        logger.info(f"   节点: {total_nodes:,}个")
        logger.info(f"   关系: {total_rels:,}条")
        logger.info("=" * 60)

    finally:
        source_driver.close()
        target_driver.close()


if __name__ == "__main__":
    main()
