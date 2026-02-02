#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查和恢复Neo4j知识图谱
Check and Restore Neo4j Knowledge Graphs

验证Neo4j中的法律知识图谱和专利知识图谱
"""

import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

async def check_neo4j_connection():
    """检查Neo4j连接"""
    logger.info("\n🔍 检查Neo4j服务状态...")
    logger.info(str('-' * 60))

    try:
        # 尝试连接Neo4j
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            'bolt://localhost:7687',
            auth=('neo4j', 'password')
        )

        with driver.session() as session:
            result = session.run('RETURN 1 as test')
            test_val = result.single()['test']

        if test_val == 1:
            logger.info('✅ Neo4j连接成功')

            # 获取节点和关系统计
            with driver.session() as session:
                # 节点数
                node_result = session.run('MATCH (n) RETURN count(n) as count')
                node_count = node_result.single()['count']

                # 关系数
                rel_result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
                rel_count = rel_result.single()['count']

                # 标签统计
                label_result = session.run("""
                    MATCH (n)
                    RETURN labels(n) as labels, count(n) as count
                    ORDER BY count DESC
                """)
                labels = list(label_result)

                # 关系类型统计
                rel_type_result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as type, count(r) as count
                    ORDER BY count DESC
                """)
                rel_types = list(rel_type_result)

            logger.info(f"\n📊 Neo4j知识图谱统计:")
            logger.info(f"  - 节点总数: {node_count:,}")
            logger.info(f"  - 关系总数: {rel_count:,}")

            if labels:
                logger.info(f"\n🏷️ 主要节点标签:")
                for label in labels[:10]:
                    logger.info(f"  - {label['labels']}: {label['count']:,}")

            if rel_types:
                logger.info(f"\n🔗 主要关系类型:")
                for rel in rel_types[:10]:
                    logger.info(f"  - {rel['type']}: {rel['count']:,}")

            driver.close()
            return True, node_count, rel_count, labels, rel_types

    except Exception as e:
        logger.info(f"❌ Neo4j连接失败: {e}")
        return False, 0, 0, [], []

async def check_specific_knowledge_graphs():
    """检查特定的知识图谱"""
    logger.info("\n\n🔍 检查专业知识图谱...")
    logger.info(str('-' * 60))

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            'bolt://localhost:7687',
            auth=('neo4j', 'password')
        )

        with driver.session() as session:
            # 检查法律知识图谱
            logger.info("\n⚖️ 法律知识图谱:")
            legal_nodes = session.run("""
                MATCH (n:LegalEntity)
                RETURN count(n) as count
            """)
            legal_count = legal_nodes.single()['count']
            logger.info(f"  - 法律实体数: {legal_count:,}")

            if legal_count > 0:
                # 获取一些法律实体示例
                examples = session.run("""
                    MATCH (n:LegalEntity)
                    RETURN n.name as name, n.type as type
                    LIMIT 5
                """)
                logger.info('  - 示例实体:')
                for ex in examples:
                    logger.info(f"    • {ex['name']} ({ex.get('type', 'N/A')})")

            # 检查专利知识图谱
            logger.info("\n📄 专利知识图谱:")
            patent_nodes = session.run("""
                MATCH (n:Patent)
                RETURN count(n) as count
            """)
            patent_count = patent_nodes.single()['count']
            logger.info(f"  - 专利节点数: {patent_count:,}")

            if patent_count > 0:
                # 获取一些专利示例
                examples = session.run("""
                    MATCH (n:Patent)
                    RETURN n.patent_number as number, n.title as title
                    LIMIT 5
                """)
                logger.info('  - 示例专利:')
                for ex in examples:
                    logger.info(f"    • {ex['number']}: {ex.get('title', 'N/A')[:50]}...")

            # 检查案例知识图谱
            logger.info("\n⚖️ 案例知识图谱:")
            case_nodes = session.run("""
                MATCH (n:Case)
                RETURN count(n) as count
            """)
            case_count = case_nodes.single()['count']
            logger.info(f"  - 案例节点数: {case_count:,}")

            # 检查技术知识图谱
            logger.info("\n🔧 技术知识图谱:")
            tech_nodes = session.run("""
                MATCH (n:TechnicalConcept)
                RETURN count(n) as count
            """)
            tech_count = tech_nodes.single()['count']
            logger.info(f"  - 技术概念数: {tech_count:,}")

        driver.close()

    except Exception as e:
        logger.info(f"❌ 检查专业知识图谱失败: {e}")

async def start_neo4j_if_needed():
    """如果需要，启动Neo4j服务"""
    logger.info("\n🚀 尝试启动Neo4j服务...")
    logger.info(str('-' * 60))

    import subprocess

    # 检查Docker是否运行
    try:
        result = subprocess.run(
            ['docker', 'ps'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.info('❌ Docker未运行，无法启动Neo4j容器')
            return False
    except:
        logger.info('❌ Docker未安装')
        return False

    # 启动Neo4j容器
    try:
        # 先检查容器是否已存在
        check_result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', 'name=athena-neo4j'],
            capture_output=True,
            text=True
        )

        if 'athena-neo4j' in check_result.stdout:
            logger.info('📦 Neo4j容器已存在')
            # 检查是否运行
            if 'Up' in check_result.stdout:
                logger.info('✅ Neo4j容器正在运行')
            else:
                logger.info('🔄 启动Neo4j容器...')
                subprocess.run(
                    ['docker', 'start', 'athena-neo4j'],
                    capture_output=True
                )
                logger.info('✅ Neo4j容器已启动')
        else:
            logger.info('📥 创建并启动Neo4j容器...')
            subprocess.run(
                ['docker', 'run', '-d',
                 '--name', 'athena-neo4j',
                 '-p', '7474:7474',
                 '-p', '7687:7687',
                 '-e', 'NEO4J_AUTH=neo4j/password',
                 '-e', 'NEO4J_dbms_memory_heap_initial_size=1G',
                 '-e', 'NEO4J_dbms_memory_heap_max_size=2G',
                 'neo4j:5.15'],
                capture_output=True
            )
            logger.info('✅ Neo4j容器已创建并启动')

        # 等待服务启动
        logger.info("\n⏳ 等待Neo4j服务启动...")
        import time
        time.sleep(5)

        return True

    except Exception as e:
        logger.info(f"❌ 启动Neo4j失败: {e}")
        return False

async def main():
    """主函数"""
    logger.info(str("\n" + '='*80))
    logger.info('📊 Neo4j知识图谱系统检查')
    logger.info(str('='*80))

    # 首先尝试连接Neo4j
    connected, node_count, rel_count, labels, rel_types = await check_neo4j_connection()

    if not connected:
        # 尝试启动Neo4j
        if await start_neo4j_if_needed():
            logger.info("\n⏳ 等待10秒让Neo4j完全启动...")
            import time
            time.sleep(10)

            # 再次尝试连接
            connected, node_count, rel_count, labels, rel_types = await check_neo4j_connection()

    if connected:
        # 检查专业知识图谱
        await check_specific_knowledge_graphs()

        # 总结
        logger.info("\n\n📋 Neo4j知识图谱状态总结:")
        logger.info(str('-' * 60))

        has_legal = any('Legal' in str(l) for l in labels)
        has_patent = any('Patent' in str(l) for l in labels)
        has_case = any('Case' in str(l) for l in labels)
        has_tech = any('Technical' in str(l) for l in labels)

        logger.info(f"✅ Neo4j服务: 运行正常")
        logger.info(f"📊 总节点数: {node_count:,}")
        logger.info(f"🔗 总关系数: {rel_count:,}")
        logger.info(f"⚖️ 法律知识图谱: {'✅ 存在' if has_legal else '❌ 未发现'}")
        logger.info(f"📄 专利知识图谱: {'✅ 存在' if has_patent else '❌ 未发现'}")
        logger.info(f"📜 案例知识图谱: {'✅ 存在' if has_case else '❌ 未发现'}")
        logger.info(f"🔧 技术知识图谱: {'✅ 存在' if has_tech else '❌ 未发现'}")

        if node_count == 0:
            logger.info("\n⚠️ Neo4j中暂无数据，可能需要导入知识图谱")
            logger.info('建议运行知识图谱导入脚本')

    else:
        logger.info("\n❌ 无法连接到Neo4j服务")
        logger.info("\n💡 建议:")
        logger.info('1. 确保Docker已安装并运行')
        logger.info('2. 检查端口7687是否被占用')
        logger.info('3. 运行 docker ps -a 查看容器状态')

    logger.info(str("\n" + '='*80))

if __name__ == '__main__':
    asyncio.run(main())