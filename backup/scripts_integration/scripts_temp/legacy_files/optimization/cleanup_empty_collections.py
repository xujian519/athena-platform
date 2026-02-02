#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理空的统一集合
"""

import logging

from qdrant_client import QdrantClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_empty_collections():
    client = QdrantClient('http://localhost:6333')

    # 空的统一集合列表
    empty_collections = [
        'legal_unified',
        'patents_unified',
        'memory_unified',
        'technical_unified',
        'legal_clauses_shard_0',
        'legal_clauses_shard_1',
        'legal_vector_db'
    ]

    logger.info('🧹 开始清理空集合...')

    for collection_name in empty_collections:
        try:
            count = client.count(collection_name).count
            if count == 0:
                # 删除空集合
                client.delete_collection(collection_name)
                logger.info(f"  ✅ 已删除空集合: {collection_name}")
            else:
                logger.info(f"  ⚠️ 集合不为空，跳过: {collection_name} ({count} vectors)")
        except Exception as e:
            logger.error(f"  ❌ 处理 {collection_name} 失败: {e}")

    # 检查清理结果
    collections = client.get_collections().collections
    logger.info(f"\n清理后剩余集合数: {len(collections)}")

    return collections

if __name__ == '__main__':
    cleanup_empty_collections()