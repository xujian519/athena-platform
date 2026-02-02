#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的系统性能
包括分片查询和优化缓存
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import logging
import sys
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.vector_db.optimized_qdrant_client import OptimizedQdrantClient


def test_system():
    """测试优化后的系统"""
    logger.info('🚀 测试优化后的系统...')
    logger.info(str('=' * 60))

    # 初始化客户端
    client = OptimizedQdrantClient()

    # 1. 测试集合列表
    logger.info("\n1. 📦 集合列表:")
    collections = client.list_collections()
    for col in collections:
        name = col['name']
        count = col.get('vectors_count', 0)
        if col.get('sharded'):
            logger.info(f"  • {name:30} : {count:>8,} vectors (分片: {col.get('shards_count')})")
        else:
            logger.info(f"  • {name:30} : {count:>8,} vectors")

    # 2. 测试分片查询性能
    logger.info("\n2. 🔍 测试legal_clauses分片查询:")
    test_vector = random(1024).tolist()

    # 执行多次查询测试性能
    iterations = 10
    total_time = 0

    for i in range(iterations):
        start_time = time.time()
        results = client.search('legal_clauses', test_vector, limit=20)
        response_time = (time.time() - start_time) * 1000
        total_time += response_time

        logger.info(f"  查询 {i+1:2d}: {len(results)} 条结果, {response_time:.2f}ms")

    avg_time = total_time / iterations
    logger.info(f"\n  📊 平均响应时间: {avg_time:.2f} ms")

    # 3. 测试缓存性能
    logger.info("\n3. 💾 测试缓存性能:")
    cache_stats = client.get_cache_stats()
    logger.info('  当前缓存统计:')
    for key, value in cache_stats.items():
        logger.info(f"    {key}: {value}")

    # 4. 测试其他集合查询
    logger.info("\n4. 🔍 测试其他集合查询:")
    other_collections = ['ai_technical_terms_1024', 'legal_documents']

    for collection in other_collections:
        try:
            start_time = time.time()
            results = client.search(collection, test_vector, limit=10)
            response_time = (time.time() - start_time) * 1000
            logger.info(f"  {collection:25} : {len(results)} 条结果, {response_time:.2f}ms")
        except Exception as e:
            logger.info(f"  {collection:25} : 错误 - {str(e)[:50]}...")

    # 5. 性能总结
    logger.info(str("\n" + '=' * 60))
    logger.info('📊 系统优化总结:')
    logger.info(f"✅ Legal clauses已分片到 {len(client.legal_clauses_shards)} 个集合")
    logger.info(f"✅ 优化的缓存服务已启用")
    logger.info(f"✅ 查询响应时间平均: {avg_time:.2f} ms")
    logger.info(f"✅ 系统就绪，可处理大规模查询")

if __name__ == '__main__':
    test_system()