#!/usr/bin/env python3
"""
正确合并OpenClaw数据和关系到当前Neo4j数据库
保留原始ID属性
"""

import logging

from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 连接配置
SOURCE_URI = 'bolt://localhost:7688'
TARGET_URI = 'bolt://localhost:7687'
TARGET_AUTH = ('neo4j', 'athena_neo4j_2024')


def merge_nodes(source_driver, target_driver):
    """合并OpenClaw节点，保留原始ID"""
    logger.info("📦 合并OpenClaw节点...")

    with source_driver.session() as source_session:
        with target_driver.session() as target_session:
            # 获取总数
            result = source_session.run("MATCH (n:OpenClawNode) RETURN count(n) as count")
            total_count = result.single()['count']
            logger.info(f"   源数据: {total_count:,}个节点")

            # 批量读取和导入
            batch_size = 1000
            offset = 0
            imported_count = 0

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
                    # 使用原始ID作为主键
                    original_id = props.get('id', str(node.element_id))
                    props['_original_id'] = original_id
                    batch.append(props)

                # 批量创建到目标数据库
                if batch:
                    target_session.run("""
                        UNWIND $batch AS data
                        MERGE (n:OpenClawNode {_original_id: data._original_id})
                        SET n += data
                    """, batch=batch)

                    imported_count += len(batch)
                    logger.info(f"   进度: {imported_count}/{total_count} ({imported_count*100//total_count}%)")

                offset += batch_size

            logger.info(f"✅ OpenClaw节点合并完成: {imported_count:,}个")


def merge_relationships(source_driver, target_driver):
    """合并OpenClaw关系"""
    logger.info("📦 合并OpenClaw关系...")

    with source_driver.session() as source_session:
        with target_driver.session() as target_session:
            # 获取总数
            result = source_session.run("MATCH ()-[r]->() RETURN count(r) as count")
            total_count = result.single()['count']
            logger.info(f"   源数据: {total_count:,}条关系")

            # 按关系类型分别导入
            rel_types = ['SIMILAR_TO', 'RELATED_TO', 'CITES', 'FREQUENTLY_DISCUSSES',
                        'DEFINES', 'BELONGS_TO', 'RELATES_TO', 'HIGH_RISK', 'FREQUENTLY_CITES']

            for rel_type in rel_types:
                logger.info(f"   导入 {rel_type} 关系...")

                # 分批导入
                offset = 0
                batch_size = 1000
                imported_count = 0

                while True:
                    # 从源数据库读取关系（使用id字段）
                    result = source_session.run(f"""
                        MATCH (a)-[r:{rel_type}]->(b)
                        RETURN a.id AS source_id, b.id AS target_id, properties(r) AS props
                        SKIP $offset
                        LIMIT $limit
                    """, offset=offset, limit=batch_size)

                    batch = list(result)
                    if not batch:
                        break

                    # 批量创建到目标数据库
                    for record in batch:
                        source_id = record['source_id']
                        target_id = record['target_id']
                        props = dict(record['props'])

                        try:
                            target_session.run(f"""
                                MATCH (s:OpenClawNode {{_original_id: $source_id}}), (t:OpenClawNode {{_original_id: $target_id}})
                                CREATE (s)-[r:{rel_type}]->(t)
                                SET r += $props
                            """, source_id=source_id, target_id=target_id, props=props)
                            imported_count += 1
                        except Exception as e:
                            logger.debug(f"   跳过关系: {e}")

                    if imported_count % 10000 == 0:
                        logger.info(f"     进度: {imported_count}条")

                    offset += batch_size

                logger.info(f"   ✅ {rel_type} 导入完成: {imported_count:,}条")


def verify_merge(target_driver):
    """验证合并结果"""
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

    return total_nodes, total_rels


def main():
    """主函数"""
    logger.info("🔗 连接数据库...")

    # 源数据库（无认证）
    source_driver = GraphDatabase.driver(SOURCE_URI, auth=())
    # 目标数据库
    target_driver = GraphDatabase.driver(TARGET_URI, auth=TARGET_AUTH)

    try:
        # 合并节点
        merge_nodes(source_driver, target_driver)

        # 合并关系
        merge_relationships(source_driver, target_driver)

        # 验证结果
        nodes, rels = verify_merge(target_driver)

        logger.info("=" * 60)
        logger.info("🎉 合并完成!")
        logger.info(f"   节点: {nodes:,}个")
        logger.info(f"   关系: {rels:,}条")
        logger.info("=" * 60)

    finally:
        source_driver.close()
        target_driver.close()


if __name__ == "__main__":
    main()
