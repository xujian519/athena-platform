#!/usr/bin/env python3
"""
将向量数据导入到Qdrant数据库
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.getcwd())

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    logger.info('❌ qdrant-client 未安装，请运行: pip install qdrant-client')
    QDRANT_AVAILABLE = False

async def import_vectors_to_collection(collection_name, vectors_data, dimension):
    """导入向量到指定集合"""
    if not QDRANT_AVAILABLE:
        logger.info('❌ Qdrant客户端未安装')
        return False

    try:
        # 连接到Qdrant
        client = QdrantClient(host='localhost', port=6333)

        # 检查集合是否存在
        collections = client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections)

        # 如果集合不存在，创建它
        if not collection_exists:
            logger.info(f"  创建集合: {collection_name}")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )

        # 准备点数据
        points = []
        for i, (id, vector) in enumerate(vectors_data.items()):
            # 将字符串ID转换为数字ID（Qdrant要求）
            numeric_id = hash(id) & 0xFFFFFFFFFFFFFFFF  # 转换为正整数
            points.append(PointStruct(
                id=numeric_id,
                vector=vector,
                payload={'source': 'import', 'original_id': id, 'index': i}
            ))

        # 分批上传（每批100个）
        batch_size = 100
        total_uploaded = 0

        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            result = client.upsert(
                collection_name=collection_name,
                points=batch
            )
            total_uploaded += len(batch)
            logger.info(f"  上传进度: {total_uploaded}/{len(points)}")

        logger.info(f"✅ 成功导入 {len(points)} 个向量到 {collection_name}")
        return True

    except Exception as e:
        logger.info(f"❌ 导入失败: {e}")
        return False

def load_vectors_from_file(file_path):
    """从文件加载向量数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        vectors_data = {}

        # 处理不同的文件格式
        if 'vectors' in data:
            # 格式: {"vectors": [{"id": "...", "vector": [...]}]}
            if isinstance(data['vectors'], list):
                for item in data['vectors']:
                    if 'id' in item and 'vector' in item:
                        vectors_data[item['id']] = item['vector']
            elif isinstance(data['vectors'], dict):
                for key, value in data['vectors'].items():
                    if key.startswith('AITD-') and isinstance(value, list):
                        vectors_data[key] = value
        elif isinstance(data, dict) and any(k.startswith('AITD-') for k in data.keys()):
            # 格式: {"AITD-00000": [...], "AITD-00001": [...]}
            for key, value in data.items():
                if key.startswith('AITD-') and isinstance(value, list):
                    vectors_data[key] = value

        return vectors_data, data.get('metadata', {})

    except Exception as e:
        logger.info(f"❌ 加载文件失败 {file_path}: {e}")
        return {}, {}

async def main():
    """主函数"""
    logger.info('📥 导入向量数据到Qdrant数据库')
    logger.info(str('=' * 60))
    logger.info(f"导入时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if not QDRANT_AVAILABLE:
        logger.info('请先安装 qdrant-client: pip install qdrant-client')
        return

    # 要导入的向量文件
    vector_files = [
        {
            'path': '/Users/xujian/Athena工作平台/data/vectors_qdrant/embeddings/ai_terminology_vectors_20251205_104422.json',
            'collection': 'ai_technical_terms_vector_db',
            'name': 'AI技术术语向量'
        }
    ]

    total_imported = 0

    for file_info in vector_files:
        file_path = file_info['path']
        if not os.path.exists(file_path):
            logger.info(f"⚠️  文件不存在: {file_path}")
            continue

        logger.info(f"\n📁 处理文件: {file_info['name']}")
        logger.info(f"  路径: {file_path}")

        # 加载向量数据
        vectors_data, metadata = load_vectors_from_file(file_path)

        if vectors_data:
            logger.info(f"  发现向量: {len(vectors_data)} 个")

            if 'dimension' in metadata:
                dimension = metadata['dimension']
            elif vectors_data:
                # 检查第一个向量的维度
                first_vector = list(vectors_data.values())[0]
                dimension = len(first_vector)
            else:
                logger.info(f"  ⚠️  无法确定向量维度")
                continue

            logger.info(f"  向量维度: {dimension}")

            # 确定集合名称
            collection_name = file_info['collection']

            # 导入向量
            success = await import_vectors_to_collection(
                collection_name,
                vectors_data,
                dimension
            )

            if success:
                total_imported += len(vectors_data)

    logger.info(f"\n📊 导入总结:")
    logger.info(f"  • 总计导入: {total_imported} 个向量")
    logger.info(f"  • 成功集合数: {len([f for f in vector_files if os.path.exists(f['path'])])}")

if __name__ == '__main__':
    asyncio.run(main())