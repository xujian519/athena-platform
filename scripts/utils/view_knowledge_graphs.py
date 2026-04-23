#!/usr/bin/env python3
"""
查看项目中可用的知识图谱
"""

import logging
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

def list_knowledge_graphs() -> Any:
    """列出所有可用的知识图谱"""
    base_dir = Path('/Users/xujian/Athena工作平台')

    logger.info(str('=' * 80))
    logger.info('Athena工作平台知识图谱总览')
    logger.info(str('=' * 80))

    # 1. 本地存储的知识图谱文件
    logger.info("\n📁 本地存储的知识图谱:")
    logger.info(str('-' * 60))

    # 查找JSON格式的知识图谱
    kg_files = []
    for pattern in ['data/**/*knowledge*.json', 'data/**/*kg*.json']:
        for file_path in base_dir.glob(pattern):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                kg_files.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'size_mb': size_mb
                })

    # 按大小排序
    kg_files.sort(key=lambda x: x['size_mb'], reverse=True)

    for i, kg in enumerate(kg_files[:10], 1):
        rel_path = kg['path'].replace(str(base_dir) + '/', '')
        logger.info(f"{i:2d}. {kg['name']:<30} {kg['size_mb']:>8.1f} MB")
        logger.info(f"     📍 {rel_path}")

    if len(kg_files) > 10:
        logger.info(f"     ... 还有 {len(kg_files) - 10} 个文件")

    # 2. 目录中的知识图谱
    logger.info("\n📂 知识图谱目录:")
    logger.info(str('-' * 60))

    kg_dirs = []
    for dir_path in base_dir.glob('data/**/*knowledge*'):
        if dir_path.is_dir():
            # 统计目录中的文件
            file_count = len(list(dir_path.glob('*.json')))
            if file_count > 0:
                total_size = sum(f.stat().st_size for f in dir_path.glob('*.json'))
                kg_dirs.append({
                    'path': str(dir_path),
                    'name': dir_path.name,
                    'file_count': file_count,
                    'size_mb': total_size / (1024 * 1024)
                })

    for i, kg_dir in enumerate(kg_dirs, 1):
        rel_path = kg_dir['path'].replace(str(base_dir) + '/', '')
        logger.info(f"{i:2d}. {kg_dir['name']:<30} {kg_dir['file_count']:>3} 个文件 {kg_dir['size_mb']:>6.1f} MB")
        logger.info(f"     📍 {rel_path}")

    # 3. 查看Neo4j中的知识图谱
    logger.info("\n🔗 Neo4j数据库中的知识图谱:")
    logger.info(str('-' * 60))

    try:
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

        with driver.session() as session:
            # 获取节点统计
            result = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count')
            node_stats = {}
            for record in result:
                labels = record['labels']
                label_name = ''.join(labels) if labels else 'Node'
                node_stats[label_name] = record['count']

            if node_stats:
                logger.info('节点类型统计:')
                for label, count in sorted(node_stats.items(), key=lambda x: x[1], reverse=True):
                    logger.info(f"  • {label:<20} {count:>10,} 个")

            # 获取关系统计
            result = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(r) as count')
            rel_stats = {}
            for record in result:
                rel_type = record['type'] or 'RELATED_TO'
                rel_stats[rel_type] = record['count']

            if rel_stats:
                logger.info("\n关系类型统计:")
                for rel_type, count in sorted(rel_stats.items(), key=lambda x: x[1], reverse=True):
                    logger.info(f"  • {rel_type:<20} {count:>10,} 个")

            # 总体统计
            total_nodes = sum(node_stats.values())
            total_rels = sum(rel_stats.values())
            logger.info("\n📊 总计:")
            logger.info(f"  • 总节点数: {total_nodes:,}")
            logger.info(f"  • 总关系数: {total_rels:,}")

    except Exception as e:
        logger.info(f"❌ 无法连接Neo4j: {e}")

    # 4. Qdrant向量库
    logger.info("\n🔍 Qdrant向量库:")
    logger.info(str('-' * 60))

    try:
        import requests
        response = requests.get('http://localhost:6333/collections', timeout=5)
        if response.status_code == 200:
            collections = response.json().get('result', {}).get('collections', [])
            if collections:
                logger.info('可用的向量集合:')
                for collection in collections:
                    name = collection.get('name', 'Unknown')
                    vectors_count = collection.get('vectors_count', 0)
                    collection.get('points_count', 0)
                    logger.info(f"  • {name:<20} {vectors_count:>10} 个向量")
            else:
                logger.info('  暂无向量集合')
        else:
            logger.info('  Qdrant服务未响应')
    except:
        logger.info('  无法连接Qdrant服务')

    logger.info(str("\n" + '=' * 80))

    # 5. 可用的知识图谱API
    logger.info("\n🚀 知识图谱API服务:")
    logger.info(str('-' * 60))

    api_endpoints = [
        ('知识图谱查询API', 'http://localhost:8001/docs', '提供Cypher查询接口'),
        ('向量搜索API', 'http://localhost:8000/docs', '提供向量检索服务'),
    ]

    for name, url, desc in api_endpoints:
        try:
            response = requests.get(url, timeout=2)
            status = '✅ 可用' if response.status_code == 200 else f"❌ {response.status_code}"
            logger.info(f"  • {name:<20} {url:<30} {status}")
            logger.info(f"    {desc}")
        except:
            logger.info(f"  • {name:<20} {url:<30} ❌ 不可用")
            logger.info(f"    {desc}")

if __name__ == '__main__':
    list_knowledge_graphs()
