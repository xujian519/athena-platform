#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据服务综合测试
Comprehensive Test for Intelligent Data Services
"""

import asyncio
import json
import logging
from datetime import datetime

import aiohttp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 服务地址
SERVICES = {
    'qdrant': 'http://localhost:6333',
    'qdrant_ui': 'http://localhost:6334',
    'neo4j': 'http://localhost:7474',
    'sqlite': 'http://localhost:8011',
    'intelligence': 'http://localhost:8010'
}

async def test_service(session, name, url):
    """测试单个服务"""
    logger.info(f"\n🔍 测试 {name} 服务...")
    logger.info(f"   URL: {url}")

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                logger.info(f"✅ {name} - 运行正常")

                # 获取响应内容
                if name in ['sqlite', 'intelligence']:
                    try:
                        data = await response.json()
                        logger.info(f"   📊 响应: {json.dumps(data, ensure_ascii=False)[:100]}...")
                    except:
                        logger.info(f"   📊 响应状态: HTTP {response.status}")
                else:
                    logger.info(f"   📊 响应状态: HTTP {response.status}")

                return True
            else:
                logger.warning(f"⚠️ {name} - HTTP {response.status}")
                return False

    except asyncio.TimeoutError:
        logger.error(f"❌ {name} - 连接超时")
        return False
    except Exception as e:
        logger.error(f"❌ {name} - 连接失败: {str(e)}")
        return False

async def test_qdrant_collections(session):
    """测试Qdrant集合"""
    logger.info("\n📦 测试Qdrant向量数据库集合...")

    try:
        async with session.get(f"{SERVICES['qdrant']}/collections") as response:
            if response.status == 200:
                data = await response.json()
                collections = data.get('result', {}).get('collections', [])
                logger.info(f"✅ 找到 {len(collections)} 个集合:")

                for collection in collections[:5]:  # 只显示前5个
                    logger.info(f"   - {collection['name']}")

                if len(collections) > 5:
                    logger.info(f"   ... (还有 {len(collections) - 5} 个集合)")

                return collections
            else:
                logger.error(f"❌ 获取集合失败: HTTP {response.status}")
                return []

    except Exception as e:
        logger.error(f"❌ 测试Qdrant集合失败: {str(e)}")
        return []

async def test_sqlite_databases(session):
    """测试SQLite数据库"""
    logger.info("\n📄 测试SQLite数据库...")

    try:
        async with session.get(f"{SERVICES['sqlite']}/api/databases") as response:
            if response.status == 200:
                data = await response.json()
                databases = data.get('databases', [])
                logger.info(f"✅ 找到 {len(databases)} 个数据库:")

                for db in databases:
                    status = '✅' if db['exists'] else '❌'
                    logger.info(f"   {status} {db['name']}: {len(db['tables'])} 个表 ({db['size']})")

                return databases
            else:
                logger.error(f"❌ 获取数据库列表失败: HTTP {response.status}")
                return []

    except Exception as e:
        logger.error(f"❌ 测试SQLite数据库失败: {str(e)}")
        return []

async def test_neo4j_connection():
    """测试Neo4j连接"""
    logger.info("\n🕸️ 测试Neo4j知识图谱...")

    try:
        from neo4j import GraphDatabase

        # 尝试连接
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

        with driver.session() as session:
            result = session.run("RETURN 'Hello Neo4j!' as message")
            message = result.single()['message']
            logger.info(f"✅ Neo4j连接成功: {message}")

            # 获取统计信息
            result = session.run('MATCH (n) RETURN count(n) as count')
            node_count = result.single()['count']

            result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
            rel_count = result.single()['count']

            logger.info(f"📊 知识图谱统计:")
            logger.info(f"   - 节点数: {node_count:,}")
            logger.info(f"   - 关系数: {rel_count:,}")

        driver.close()
        return True

    except Exception as e:
        logger.error(f"❌ Neo4j连接失败: {str(e)}")
        return False

async def test_patent_search(session):
    """测试专利搜索功能"""
    logger.info("\n🔍 测试专利搜索功能...")

    # 测试向量搜索
    logger.info('   测试向量搜索...')
    try:
        payload = {
            'query': '深度学习',
            'database': 'patent_index',
            'limit': 5
        }

        async with session.post(
            f"{SERVICES['sqlite']}/api/vector/search",
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get('results', [])
                logger.info(f"✅ 向量搜索找到 {len(results)} 个结果")
            else:
                logger.warning(f"⚠️ 向量搜索失败: HTTP {response.status}")
    except Exception as e:
        logger.warning(f"⚠️ 向量搜索错误: {str(e)}")

    # 测试图搜索
    logger.info('   测试图搜索...')
    try:
        payload = {
            'query': '人工智能',
            'database': 'knowledge_graph',
            'limit': 5
        }

        async with session.post(
            f"{SERVICES['sqlite']}/api/graph/search",
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get('results', [])
                logger.info(f"✅ 图搜索找到 {len(results)} 个结果")

                # 显示结果类型
                node_count = sum(1 for r in results if r.get('type') == 'node')
                edge_count = sum(1 for r in results if r.get('type') == 'edge')
                logger.info(f"   - 节点: {node_count}, 关系: {edge_count}")
            else:
                logger.warning(f"⚠️ 图搜索失败: HTTP {response.status}")
    except Exception as e:
        logger.warning(f"⚠️ 图搜索错误: {str(e)}")

async def main():
    """主测试函数"""
    logger.info('🚀 智能数据服务综合测试')
    logger.info('=' * 60)
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async with aiohttp.ClientSession() as session:
        # 测试所有服务
        logger.info("\n🌐 测试所有服务状态...")
        service_status = {}

        for name, url in SERVICES.items():
            if name == 'neo4j':  # Neo4j使用特殊测试
                status = await test_neo4j_connection()
            else:
                status = await test_service(session, name, url)
            service_status[name] = status

        # 显示服务状态汇总
        logger.info("\n📊 服务状态汇总:")
        logger.info('-' * 40)
        for name, status in service_status.items():
            icon = '✅' if status else '❌'
            logger.info(f"{icon} {name}: {'运行中' if status else '未运行'}")

        # 测试特定功能
        if service_status.get('qdrant'):
            await test_qdrant_collections(session)

        if service_status.get('sqlite'):
            await test_sqlite_databases(session)
            await test_patent_search(session)

        # 输出访问地址
        logger.info("\n🌐 服务访问地址:")
        logger.info('-' * 40)
        if service_status.get('qdrant'):
            logger.info(f"Qdrant API:     {SERVICES['qdrant']}/collections")
            logger.info(f"Qdrant Web UI:  {SERVICES['qdrant_ui']}/dashboard")
        if service_status.get('neo4j'):
            logger.info(f"Neo4j Web UI:   {SERVICES['neo4j']}/browser")
        if service_status.get('sqlite'):
            logger.info(f"SQLite API:     {SERVICES['sqlite']}/docs")
        if service_status.get('intelligence'):
            logger.info(f"专利智能API:    {SERVICES['intelligence']}/docs")

        # 测试完成
        logger.info("\n✅ 综合测试完成！")

        # 计算服务可用性
        available = sum(1 for status in service_status.values() if status)
        total = len(service_status)
        logger.info(f"\n📈 服务可用性: {available}/{total} ({available/total*100:.1f}%)")

if __name__ == '__main__':
    # 运行测试
    asyncio.run(main())