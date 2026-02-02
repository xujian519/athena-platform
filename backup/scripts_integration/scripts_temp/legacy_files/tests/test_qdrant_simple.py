#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qdrant向量数据库简单测试
Qdrant Vector Database Simple Test
"""

import json
import logging

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Qdrant API配置
QDRANT_URL = 'http://localhost:6333'
QDRANT_WEB_UI = 'http://localhost:6334/dashboard'

def test_qdrant_api():
    """测试Qdrant API"""
    logger.info('🔍 测试Qdrant API连接...')

    try:
        # 测试基本连接
        response = requests.get(f"{QDRANT_URL}/collections")
        response.raise_for_status()

        data = response.json()
        collections = data.get('result', {}).get('collections', [])

        logger.info(f"✅ API连接成功！")
        logger.info(f"📊 集合数量: {len(collections)}")

        # 显示集合列表
        logger.info("\n📋 现有集合:")
        for collection in collections[:10]:  # 只显示前10个
            logger.info(f"  - {collection['name']}")

        if len(collections) > 10:
            logger.info(f"  ... (还有 {len(collections) - 10} 个集合)")

        return collections

    except Exception as e:
        logger.error(f"❌ API连接失败: {str(e)}")
        return None

def get_collection_details(collection_name):
    """获取集合详情"""
    try:
        response = requests.get(f"{QDRANT_URL}/collections/{collection_name}")
        response.raise_for_status()

        data = response.json()
        result = data.get('result', {})

        config = result.get('config', {})
        params = config.get('params', {})
        vectors = params.get('vectors', {})

        return {
            'vectors_count': result.get('vectors_count', 0),
            'segments_count': result.get('segments_count', 0),
            'vector_size': vectors.get('size', 0) if isinstance(vectors, dict) else 0,
            'distance': vectors.get('distance', '') if isinstance(vectors, dict) else ''
        }

    except Exception as e:
        logger.error(f"获取集合 '{collection_name}' 详情失败: {str(e)}")
        return None

def test_collection_operations(collections):
    """测试集合操作"""
    logger.info("\n\n🧪 测试集合操作...")

    # 选择一个有数据的集合进行测试
    test_collection = None

    for collection in collections:
        details = get_collection_details(collection['name'])
        if details and details['vectors_count'] > 0:
            test_collection = collection['name']
            logger.info(f"\n📌 选择测试集合: {test_collection}")
            logger.info(f"  - 向量数量: {details['vectors_count']:,}")
            logger.info(f"  - 向量维度: {details['vector_size']}")
            logger.info(f"  - 距离度量: {details['distance']}")
            break

    if not test_collection:
        logger.warning('⚠️ 没有找到包含数据的集合')
        return

    # 测试搜索功能（使用随机向量）
    try:
        # 获取向量维度
        details = get_collection_details(test_collection)
        vector_size = details['vector_size']

        if vector_size > 0:
            # 生成随机向量
            import random
            random_vector = [random.random() for _ in range(vector_size)]

            # 执行搜索
            search_payload = {
                'vector': random_vector,
                'limit': 3,
                'with_payload': True,
                'with_vector': False
            }

            response = requests.post(
                f"{QDRANT_URL}/collections/{test_collection}/points/search",
                json=search_payload
            )
            response.raise_for_status()

            search_result = response.json()
            points = search_result.get('result', [])

            logger.info(f"\n🎯 搜索结果 (找到 {len(points)} 个相似向量):")
            for i, point in enumerate(points, 1):
                logger.info(f"\n{i}. 点ID: {point['id']}")
                logger.info(f"   相似度分数: {point['score']:.4f}")

                # 显示payload信息
                payload = point.get('payload', {})
                if payload:
                    # 只显示前3个字段
                    for key, value in list(payload.items())[:3]:
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + '...'
                        logger.info(f"   {key}: {value}")
                    if len(payload) > 3:
                        logger.info(f"   ... (还有 {len(payload) - 3} 个字段)")

    except Exception as e:
        logger.error(f"❌ 搜索测试失败: {str(e)}")

def test_health_info():
    """获取系统健康信息"""
    logger.info("\n\n💊 系统健康信息...")

    try:
        # 获取集群信息
        response = requests.get(f"{QDRANT_URL}/cluster")
        response.raise_for_status()

        cluster_info = response.json()
        logger.info(f"✅ 集群状态: 正常运行")

        # 获取Telemetry信息
        response = requests.get(f"{QDRANT_URL}/telemetry")
        if response.status_code == 200:
            logger.info('✅ Telemetry: 启用')

        logger.info(f"\n🌐 Web UI地址: {QDRANT_WEB_UI}")
        logger.info('💡 可以在浏览器中访问Web UI查看详细信息')

    except Exception as e:
        logger.warning(f"⚠️ 获取健康信息失败: {str(e)}")

def main():
    """主函数"""
    logger.info('🚀 Qdrant向量数据库简单测试')
    logger.info('='*50)
    logger.info(f"API地址: {QDRANT_URL}")
    logger.info(f"Web UI: {QDRANT_WEB_UI}")

    # 测试API连接
    collections = test_qdrant_api()
    if not collections:
        logger.error('无法连接到Qdrant API')
        return

    # 显示集合统计
    logger.info("\n📊 集合统计信息:")
    total_vectors = 0
    with_data = 0

    for collection in collections[:5]:  # 只统计前5个
        details = get_collection_details(collection['name'])
        if details:
            vectors_count = details['vectors_count']
            total_vectors += vectors_count
            if vectors_count > 0:
                with_data += 1
            logger.info(f"  {collection['name']}: {vectors_count:,} 个向量")

    if with_data < len(collections):
        logger.info(f"  ... (还有 {len(collections) - 5} 个集合未统计)")

    logger.info(f"\n📈 总计: {len(collections)} 个集合，约 {total_vectors:,} 个向量")

    # 测试集合操作
    test_collection_operations(collections)

    # 显示健康信息
    test_health_info()

    logger.info("\n✅ 测试完成")

if __name__ == '__main__':
    main()