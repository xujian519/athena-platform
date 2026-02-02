#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qdrant向量数据库现有集合测试
Qdrant Vector Database Existing Collections Test
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import logging
import random

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Qdrant连接配置
QDRANT_HOST = 'localhost'
QDRANT_PORT = 6333

def test_qdrant_connection():
    """测试Qdrant连接"""
    logger.info('🔍 测试Qdrant连接...')

    try:
        # 创建客户端
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        # 获取集合列表
        collections = client.get_collections().collections
        logger.info(f"✅ 连接成功！")
        logger.info(f"📊 现有集合数: {len(collections)}")

        # 显示集合详情
        logger.info("\n📋 集合列表:")
        for collection in collections:
            logger.info(f"  - {collection.name}")

        # 检查特定集合的信息
        important_collections = [
            'legal_patent_vectors',
            'ai_technical_terms_vector_db',
            'legal_laws_comprehensive',
            'patent_review_db'
        ]

        logger.info("\n📊 重要集合详情:")
        for collection_name in important_collections:
            if collection_name in [c.name for c in collections]:
                try:
                    collection_info = client.get_collection(collection_name)
                    logger.info(f"\n集合: {collection_name}")
                    logger.info(f"  - 向量维度: {collection_info.config.params.vectors.size}")
                    logger.info(f"  - 距离度量: {collection_info.config.params.vectors.distance}")
                    logger.info(f"  - 点数量: {collection_info.points_count}")
                except Exception as e:
                    logger.error(f"  - 获取详情失败: {str(e)}")
            else:
                logger.warning(f"\n集合 {collection_name} 不存在")

        return client

    except Exception as e:
        logger.error(f"❌ 连接失败: {str(e)}")
        return None

def test_vector_search(client):
    """测试向量搜索功能"""
    logger.info("\n\n🔍 测试向量搜索功能...")

    try:
        # 选择一个有数据的集合
        collections = client.get_collections().collections
        target_collection = None

        # 优先使用legal_patent_vectors或ai_technical_terms_vector_db
        for collection_name in ['legal_patent_vectors', 'ai_technical_terms_vector_db']:
            if collection_name in [c.name for c in collections]:
                collection_info = client.get_collection(collection_name)
                if collection_info.points_count > 0:
                    target_collection = collection_name
                    break

        if not target_collection:
            # 找一个有数据的集合
            for collection in collections:
                try:
                    collection_info = client.get_collection(collection.name)
                    if collection_info.points_count > 0:
                        target_collection = collection.name
                        break
                except:
                    continue

        if not target_collection:
            logger.warning('⚠️ 没有找到包含数据的集合')
            return

        logger.info(f"\n📌 使用集合: {target_collection}")

        # 获取集合信息
        collection_info = client.get_collection(target_collection)
        vector_size = collection_info.config.params.vectors.size
        logger.info(f"📏 向量维度: {vector_size}")

        # 生成随机查询向量
        query_vector = random(vector_size).astype(np.float32)
        query_vector = query_vector / np.linalg.norm(query_vector)  # 归一化

        # 执行搜索
        search_result = client.search(
            collection_name=target_collection,
            query_vector=query_vector.tolist(),
            limit=5,
            with_payload=True
        )

        logger.info(f"\n🎯 搜索结果 (找到 {len(search_result)} 个相似向量):")
        for i, point in enumerate(search_result, 1):
            logger.info(f"\n{i}. 点ID: {point.id}")
            logger.info(f"   相似度分数: {point.score:.4f}")

            # 显示payload信息
            if point.payload:
                # 只显示前几个key
                for key, value in list(point.payload.items())[:3]:
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + '...'
                    logger.info(f"   {key}: {value}")
                if len(point.payload) > 3:
                    logger.info(f"   ... (还有 {len(point.payload) - 3} 个字段)")

        # 如果有payload字段，尝试过滤搜索
        if search_result and search_result[0].payload:
            # 获取第一个结果的payload用于过滤测试
            payload_keys = list(search_result[0].payload.keys())

            # 尝试使用字符串字段进行过滤
            for key in payload_keys:
                sample_value = search_result[0].payload.get(key)
                if isinstance(sample_value, str) and sample_value:
                    logger.info(f"\n🔍 使用字段 '{key}' 进行过滤搜索...")

                    filter_condition = Filter(
                        must=[
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=sample_value)
                            )
                        ]
                    )

                    filtered_result = client.search(
                        collection_name=target_collection,
                        query_vector=query_vector.tolist(),
                        query_filter=filter_condition,
                        limit=3,
                        with_payload=True
                    )

                    logger.info(f"找到 {len(filtered_result)} 个匹配的向量")
                    if filtered_result:
                        logger.info(f"过滤后的最高相似度: {filtered_result[0].score:.4f}")
                    break

    except Exception as e:
        logger.error(f"❌ 搜索测试失败: {str(e)}")

def test_scroll_and_count(client):
    """测试滚动获取和计数功能"""
    logger.info("\n\n📜 测试滚动获取功能...")

    try:
        collections = client.get_collections().collections

        for collection in collections[:3]:  # 只测试前3个集合
            collection_name = collection.name
            try:
                # 获取点数
                collection_info = client.get_collection(collection_name)
                points_count = collection_info.points_count
                logger.info(f"\n集合 '{collection_name}' 有 {points_count} 个点")

                if points_count > 0:
                    # 滚动获取前几个点
                    points, next_page_offset = client.scroll(
                        collection_name=collection_name,
                        limit=3,
                        with_payload=True
                    )

                    logger.info(f"前3个点的信息:")
                    for i, point in enumerate(points, 1):
                        logger.info(f"  {i}. ID: {point.id}")
                        if point.payload:
                            # 显示payload的key
                            keys = list(point.payload.keys())[:3]
                            logger.info(f"     Payload字段: {keys}")

            except Exception as e:
                logger.warning(f"处理集合 '{collection_name}' 时出错: {str(e)}")

    except Exception as e:
        logger.error(f"❌ 滚动测试失败: {str(e)}")

def test_health_check(client):
    """测试健康检查"""
    logger.info("\n\n💊 测试健康检查...")

    try:
        # 获取集群信息
        cluster_info = client.get_cluster_info()
        logger.info(f"✅ 集群状态: 正常")
        logger.info(f"集群信息: {len(cluster_info)} 个节点")

        # 测试ping
        logger.info('🏓 Ping 测试...')
        # Qdrant没有直接的ping，但通过列出集合来测试连接
        collections = client.get_collections()
        logger.info(f"✅ API响应正常")

    except Exception as e:
        logger.error(f"❌ 健康检查失败: {str(e)}")

def main():
    """主函数"""
    logger.info('🚀 Qdrant向量数据库测试开始')
    logger.info(f"连接地址: http://{QDRANT_HOST}:{QDRANT_PORT}")
    logger.info(f"Web UI: http://{QDRANT_HOST}:{QDRANT_PORT + 1}/dashboard")

    # 测试连接
    client = test_qdrant_connection()
    if not client:
        logger.error('无法连接到Qdrant，请检查服务是否启动')
        return

    # 测试健康检查
    test_health_check(client)

    # 测试搜索功能
    test_vector_search(client)

    # 测试滚动获取
    test_scroll_and_count(client)

    logger.info("\n✅ 所有测试完成")

if __name__ == '__main__':
    main()