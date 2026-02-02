#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱系统验证脚本
Verify Knowledge Graph System

验证项目中的知识图谱服务状态和资源
"""

import asyncio
import json
import logging
import sqlite3
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_sqlite_knowledge_graphs():
    """验证SQLite知识图谱"""
    logger.info('📊 验证SQLite知识图谱...')

    kg_dir = Path('/Users/xujian/Athena工作平台/data/knowledge')

    if not kg_dir.exists():
        logger.error('❌ 知识图谱数据目录不存在')
        return {}

    # 检查各个知识图谱文件
    graphs = {}

    for db_file in kg_dir.glob('*.db'):
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()

            # 获取表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            graph_info = {
                'path': str(db_file),
                'size_mb': round(db_file.stat().st_size / 1024 / 1024, 2),
                'tables': tables
            }

            # 获取数据统计
            if 'entities' in tables:
                cursor.execute('SELECT COUNT(*) FROM entities')
                entity_count = cursor.fetchone()[0]
                graph_info['entity_count'] = entity_count

                # 获取实体类型分布
                try:
                    cursor.execute('SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type LIMIT 10')
                    entity_types = dict(cursor.fetchall())
                    graph_info['entity_types'] = entity_types
                except:
                    pass

            if 'relations' in tables:
                cursor.execute('SELECT COUNT(*) FROM relations')
                relation_count = cursor.fetchone()[0]
                graph_info['relation_count'] = relation_count

            graphs[db_file.name] = graph_info

            conn.close()

        except Exception as e:
            logger.error(f"❌ 读取 {db_file} 失败: {e}")
            graphs[db_file.name] = {'error': str(e)}

    return graphs

def check_neo4j_service():
    """检查Neo4j服务状态"""
    logger.info('🔍 检查Neo4j服务...')

    try:
        import neo4j
        from neo4j import GraphDatabase

        # 尝试连接
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
        with driver.session() as session:
            result = session.run('RETURN 1 as test')
            test_val = result.single()['test']

        if test_val == 1:
            # 获取统计信息
            with driver.session() as session:
                # 节点数
                node_result = session.run('MATCH (n) RETURN count(n) as count')
                node_count = node_result.single()['count']

                # 关系数
                rel_result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
                rel_count = rel_result.single()['count']

                # 标签统计
                label_result = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC LIMIT 10')
                label_stats = [{'labels': record['labels'], 'count': record['count']} for record in label_result]

            driver.close()

            return {
                'status': 'running',
                'node_count': node_count,
                'relation_count': rel_count,
                'label_stats': label_stats
            }

    except Exception as e:
        return {
            'status': 'stopped',
            'error': str(e)
        }

def check_knowledge_graph_services():
    """检查知识图谱相关服务"""
    logger.info('🌐 检查知识图谱API服务...')

    import subprocess

    import requests

    services = {
        'knowledge_graph_query_api': {
            'port': 8088,
            'path': '/health'
        },
        'knowledge_retrieval_service': {
            'port': 8089,
            'path': '/health'
        }
    }

    service_status = {}

    for service_name, config in services.items():
        try:
            # 检查端口是否被占用
            result = subprocess.run(
                ['lsof', '-i', f":{config['port']}"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # 尝试HTTP请求
                url = f"http://localhost:{config['port']}{config['path']}"
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    service_status[service_name] = {
                        'status': 'running',
                        'port': config['port'],
                        'response': response.json() if response.content else 'OK'
                    }
                else:
                    service_status[service_name] = {
                        'status': 'error',
                        'port': config['port'],
                        'http_status': response.status_code
                    }
            else:
                service_status[service_name] = {
                    'status': 'stopped',
                    'port': config['port']
                }

        except Exception as e:
            service_status[service_name] = {
                'status': 'error',
                'error': str(e)
            }

    return service_status

def analyze_knowledge_integration():
    """分析知识图谱与记忆系统集成状态"""
    logger.info('🔗 分析知识图谱集成...')

    integration_status = {
        'memory_knowledge_link': False,
        'knowledge_graph_modules': [],
        'integration_points': []
    }

    # 检查记忆系统是否支持知识图谱
    memory_system_path = Path('/Users/xujian/Athena工作平台/core/memory')
    if memory_system_path.exists():
        for py_file in memory_system_path.glob('*.py'):
            content = py_file.read_text()
            if 'knowledge' in content.lower():
                integration_status['knowledge_graph_modules'].append(py_file.name)

    # 检查知识图谱相关模块
    kg_modules = [
        'core/knowledge',
        'services/knowledge_graph',
        'domains/patent/services/patent_knowledge_graph'
    ]

    for module in kg_modules:
        module_path = Path(f"/Users/xujian/Athena工作平台/{module}")
        if module_path.exists():
            integration_status['integration_points'].append(module)

    # 检查是否有集成代码
    integration_files = [
        'services/sqlite_patent_knowledge_service.py',
        'services/vector_knowledge_service.py',
        'services/optimization/knowledge_graph_integration.py'
    ]

    for file_path in integration_files:
        full_path = Path(f"/Users/xujian/Athena工作平台/{file_path}")
        if full_path.exists():
            integration_status['memory_knowledge_link'] = True
            break

    return integration_status

async def generate_knowledge_graph_report():
    """生成知识图谱系统报告"""
    logger.info(str("\n" + '='*80))
    logger.info('📊 Athena工作平台 - 知识图谱系统验证报告')
    logger.info(str('='*80))

    # 1. SQLite知识图谱验证
    logger.info("\n🗄️  SQLite知识图谱资源:")
    logger.info(str('-'*60))
    sqlite_graphs = verify_sqlite_knowledge_graphs()

    for db_name, info in sqlite_graphs.items():
        if 'error' in info:
            logger.info(f"\n❌ {db_name}: {info['error']}")
        else:
            logger.info(f"\n✅ {db_name}:")
            logger.info(f"  📁 路径: {info['path']}")
            logger.info(f"  📏 大小: {info['size_mb']} MB")
            logger.info(f"  📋 表数: {len(info['tables'])}")
            if 'entity_count' in info:
                logger.info(f"  🔢 实体数: {info['entity_count']:,}")
            if 'relation_count' in info:
                logger.info(f"  🔗 关系数: {info['relation_count']:,}")
            if 'entity_types' in info:
                logger.info(f"  📊 实体类型: {info['entity_types']}")

    # 2. Neo4j服务检查
    logger.info("\n\n🌐 Neo4j知识图谱服务:")
    logger.info(str('-'*60))
    neo4j_status = check_neo4j_service()

    if neo4j_status['status'] == 'running':
        logger.info('✅ Neo4j服务运行正常')
        logger.info(f"  🔢 节点总数: {neo4j_status['node_count']:,}")
        logger.info(f"  🔗 关系总数: {neo4j_status['relation_count']:,}")
        logger.info("\n📊 主要标签分布:")
        for label_stat in neo4j_status['label_stats'][:5]:
            logger.info(f"  - {label_stat['labels']}: {label_stat['count']:,}")
    else:
        logger.info(f"❌ Neo4j服务未运行: {neo4j_status.get('error', '未知错误')}")

    # 3. API服务检查
    logger.info("\n\n🚀 知识图谱API服务:")
    logger.info(str('-'*60))
    api_services = check_knowledge_graph_services()

    for service_name, status in api_services.items():
        if status['status'] == 'running':
            logger.info(f"✅ {service_name}:")
            logger.info(f"  🌐 端口: {status['port']}")
            logger.info(f"  💚 状态: 运行中")
        else:
            logger.info(f"❌ {service_name}:")
            logger.info(f"  🔌 端口: {status.get('port', 'N/A')}")
            logger.info(f"  ❌ 状态: {status.get('status', '未知')}")
            if 'error' in status:
                logger.info(f"  💥 错误: {status['error']}")

    # 4. 集成状态分析
    logger.info("\n\n🔗 知识图谱与记忆系统集成:")
    logger.info(str('-'*60))
    integration = analyze_knowledge_integration()

    logger.info(f"✅ 记忆-知识图谱链接: {'已建立' if integration['memory_knowledge_link'] else '未建立'}")
    logger.info(f"📦 知识图谱模块数: {len(integration['knowledge_graph_modules'])}")
    logger.info(f"🔌 集成点数量: {len(integration['integration_points'])}")

    if integration['knowledge_graph_modules']:
        logger.info("\n📋 相关模块:")
        for module in integration['knowledge_graph_modules'][:5]:
            logger.info(f"  - {module}")

    # 5. 总结
    logger.info("\n\n📋 知识图谱系统总结:")
    logger.info(str('-'*60))

    total_sqlite_entities = sum(
        info.get('entity_count', 0)
        for info in sqlite_graphs.values()
        if 'entity_count' in info
    )

    total_sqlite_relations = sum(
        info.get('relation_count', 0)
        for info in sqlite_graphs.values()
        if 'relation_count' in info
    )

    logger.info(f"🗄️  SQLite知识图谱: {len(sqlite_graphs)} 个")
    logger.info(f"   - 总实体数: {total_sqlite_entities:,}")
    logger.info(f"   - 总关系数: {total_sqlite_relations:,}")

    if neo4j_status['status'] == 'running':
        logger.info(f"🌐 Neo4j知识图谱: 运行中")
        logger.info(f"   - 节点数: {neo4j_status['node_count']:,}")
        logger.info(f"   - 关系数: {neo4j_status['relation_count']:,}")
    else:
        logger.info(f"🌐 Neo4j知识图谱: 未运行")

    running_services = sum(
        1 for status in api_services.values()
        if status['status'] == 'running'
    )
    logger.info(f"🚀 API服务: {running_services}/{len(api_services)} 运行中")

    # 6. 建议
    logger.info("\n\n💡 优化建议:")
    logger.info(str('-'*60))

    if neo4j_status['status'] != 'running':
        logger.info('• 建议启动Neo4j服务以支持图查询功能')

    if not integration['memory_knowledge_link']:
        logger.info('• 建议建立记忆系统与知识图谱的深度集成')

    if running_services < len(api_services):
        logger.info('• 建议启动所有知识图谱API服务')

    logger.info(str("\n" + '='*80))

if __name__ == '__main__':
    asyncio.run(generate_knowledge_graph_report())