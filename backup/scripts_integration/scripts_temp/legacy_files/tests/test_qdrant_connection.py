#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qdrant向量数据库连接测试
Qdrant Vector Database Connection Test
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import logging

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

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
        logger.info(f"✅ 连接成功！现有集合: {[c.name for c in collections]}")

        # 获取集群信息
        cluster_info = client.get_cluster_info()
        logger.info(f"📊 集群信息: {cluster_info}")

        return client

    except Exception as e:
        logger.error(f"❌ 连接失败: {str(e)}")
        return None

def create_sample_collection(client):
    """创建示例集合"""
    logger.info('📝 创建示例向量集合...')

    try:
        collection_name = 'patent_vectors'

        # 检查集合是否已存在
        if collection_name in [c.name for c in client.get_collections().collections]:
            logger.info(f"⚠️ 集合 '{collection_name}' 已存在，删除重建...")
            client.delete_collection(collection_name)

        # 创建集合
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)  # 768维向量（BERT）
        )
        logger.info(f"✅ 创建集合 '{collection_name}' 成功")

        return collection_name

    except Exception as e:
        logger.error(f"❌ 创建集合失败: {str(e)}")
        return None

def generate_patent_vectors():
    """生成专利示例向量"""
    logger.info('🔢 生成专利示例向量...')

    # 模拟专利文本向量（实际应该使用BERT等模型生成）
    patents = [
        {
            'id': 1,
            'name': '基于深度学习的图像识别方法',
            'abstract': '本发明提供了一种基于深度学习的图像识别方法...',
            'field': '人工智能'
        },
        {
            'id': 2,
            'name': '区块链数据存储系统',
            'abstract': '一种基于区块链技术的分布式数据存储系统...',
            'field': '区块链'
        },
        {
            'id': 3,
            'name': '量子通信加密方法',
            'abstract': '利用量子纠缠原理实现的安全通信加密方法...',
            'field': '量子技术'
        },
        {
            'id': 4,
            'name': '自然语言处理系统',
            'abstract': '基于Transformer的自然语言处理和文本生成系统...',
            'field': '人工智能'
        },
        {
            'id': 5,
            'name': '物联网传感器网络',
            'abstract': '大规模物联网传感器的数据采集和传输网络...',
            'field': '物联网'
        }
    ]

    # 生成随机向量（实际应用中应该使用embedding模型）
    vectors = []
    for patent in patents:
        # 生成768维的随机向量（归一化）
        vector = random(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)  # 归一化

        vectors.append({
            'id': patent['id'],
            'vector': vector.tolist(),
            'payload': {
                'name': patent['name'],
                'abstract': patent['abstract'],
                'field': patent['field']
            }
        })

    logger.info(f"✅ 生成了 {len(vectors)} 个专利向量")
    return vectors

def upload_vectors(client, collection_name, vectors):
    """上传向量到Qdrant"""
    logger.info('📤 上传向量到Qdrant...')

    try:
        # 批量上传
        client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=v['id'],
                    vector=v['vector'],
                    payload=v['payload']
                )
                for v in vectors
            ]
        )

        logger.info(f"✅ 成功上传 {len(vectors)} 个向量")

        # 获取集合信息
        collection_info = client.get_collection(collection_name)
        logger.info(f"📊 集合信息: {collection_info.points_count} 个点")

    except Exception as e:
        logger.error(f"❌ 上传失败: {str(e)}")

def test_vector_search(client, collection_name):
    """测试向量搜索"""
    logger.info('🔍 测试向量搜索...')

    try:
        # 生成查询向量（与第一个专利相似）
        query_vector = random(768).astype(np.float32)
        query_vector = query_vector / np.linalg.norm(query_vector)

        # 执行搜索
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_vector.tolist(),
            limit=3,
            with_payload=True
        )

        logger.info("\n🎯 搜索结果:")
        for i, point in enumerate(search_result, 1):
            logger.info(f"\n{i}. 专利名称: {point.payload['name']}")
            logger.info(f"   技术领域: {point.payload['field']}")
            logger.info(f"   相似度分数: {point.score:.4f}")
            logger.info(f"   摘要: {point.payload['abstract'][:50]}...")

        # 带过滤条件的搜索
        logger.info("\n\n🔍 带过滤条件的搜索 (仅人工智能领域):")
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        filter_condition = Filter(
            must=[
                FieldCondition(
                    key='field',
                    match=MatchValue(value='人工智能')
                )
            ]
        )

        filtered_result = client.search(
            collection_name=collection_name,
            query_vector=query_vector.tolist(),
            query_filter=filter_condition,
            limit=5,
            with_payload=True
        )

        logger.info(f"\n找到 {len(filtered_result)} 个人工智能领域的专利:")
        for i, point in enumerate(filtered_result, 1):
            logger.info(f"{i}. {point.payload['name']} (相似度: {point.score:.4f})")

    except Exception as e:
        logger.error(f"❌ 搜索失败: {str(e)}")

def test_batch_operations(client, collection_name):
    """测试批量操作"""
    logger.info("\n🔧 测试批量操作...")

    try:
        # 批量删除
        ids_to_delete = [1, 2]
        client.delete(
            collection_name=collection_name,
            points_selector=ids_to_delete
        )
        logger.info(f"✅ 删除了点: {ids_to_delete}")

        # 检查剩余点数
        collection_info = client.get_collection(collection_name)
        logger.info(f"📊 剩余点数: {collection_info.points_count}")

        # 滚动获取
        logger.info("\n📜 滚动获取所有点:")
        all_points = []
        next_page_offset = None

        while True:
            points, next_page_offset = client.scroll(
                collection_name=collection_name,
                offset=next_page_offset,
                limit=2,
                with_payload=True
            )
            all_points.extend(points)

            if not next_page_offset:
                break

        for point in all_points:
            logger.info(f"  - ID: {point.id}, 名称: {point.payload['name']}")

    except Exception as e:
        logger.error(f"❌ 批量操作失败: {str(e)}")

def main():
    """主函数"""
    logger.info('🚀 Qdrant向量数据库测试开始')

    # 测试连接
    client = test_qdrant_connection()
    if not client:
        logger.error('无法连接到Qdrant，请检查服务是否启动')
        return

    # 创建集合
    collection_name = create_sample_collection(client)
    if not collection_name:
        return

    # 生成向量
    vectors = generate_patent_vectors()

    # 上传向量
    upload_vectors(client, collection_name, vectors)

    # 测试搜索
    test_vector_search(client, collection_name)

    # 测试批量操作
    test_batch_operations(client, collection_name)

    logger.info("\n✅ 测试完成")
    logger.info(f"\n📊 Qdrant Web UI: http://{QDRANT_HOST}:{QDRANT_PORT + 1}/dashboard")

if __name__ == '__main__':
    main()