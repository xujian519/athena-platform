#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化HNSW参数
针对不同大小的集合优化HNSW索引参数
"""

import json
import logging
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def optimize_hnsw_for_collection(collection_name: str, m: int = None, ef_construct: int = None):
    """为单个集合优化HNSW参数"""
    client = QdrantClient('http://localhost:6333')

    try:
        # 获取集合信息
        info = client.get_collection(collection_name)
        current_params = info.config.optimizer_config
        vector_count = client.count(collection_name).count

        logger.info(f"\n🔧 优化集合: {collection_name}")
        logger.info(f"  当前向量数: {vector_count:,}")
        logger.info(f"  当前HNSW参数: m={current_params.get('hnsw', {}).get('m', 'N/A')}")

        # 根据集合大小推荐参数
        if m is None:
            if vector_count > 100000:
                m = 32
            elif vector_count > 10000:
                m = 16
            else:
                m = 8

        if ef_construct is None:
            if vector_count > 100000:
                ef_construct = 200
            elif vector_count > 10000:
                ef_construct = 128
            else:
                ef_construct = 64

        # 构建优化配置
        optimizer_config = {
            'hnsw': {
                'm': m,
                'ef_construct': ef_construct,
                'full_scan_threshold': min(vector_count, 10000)
            }
        }

        # 应用优化
        client.update_collection(
            collection_name=collection_name,
            optimizer_config=optimizer_config
        )

        logger.info(f"  ✅ 已更新HNSW参数: m={m}, ef_construct={ef_construct}")

        # 记录优化结果
        return {
            'collection': collection_name,
            'vector_count': vector_count,
            'optimized_params': {'m': m, 'ef_construct': ef_construct},
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"  ❌ 优化失败 {collection_name}: {e}")
        return {
            'collection': collection_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def optimize_all_collections():
    """优化所有集合的HNSW参数"""
    client = QdrantClient('http://localhost:6333')

    # 获取所有集合
    collections = client.get_collections().collections

    # 按大小排序
    collection_sizes = []
    for collection in collections:
        try:
            count = client.count(collection.name).count
            if count > 0:
                collection_sizes.append((collection.name, count))
        except:
            continue

    collection_sizes.sort(key=lambda x: x[1], reverse=True)

    logger.info(f"📊 找到 {len(collection_sizes)} 个有数据的集合")

    # 优化每个集合
    results = []
    for collection_name, count in collection_sizes:
        result = optimize_hnsw_for_collection(collection_name)
        results.append(result)

    return results

def generate_hnsw_optimization_guide():
    """生成HNSW优化指南"""
    guide = {
        'hnsw_optimization_guide': {
            'description': 'HNSW参数优化指南',
            'parameters': {
                'm': {
                    'description': '每个节点的最大连接数',
                    'small_collections': '< 10K vectors: m=8',
                    'medium_collections': '10K-100K vectors: m=16',
                    'large_collections': '> 100K vectors: m=32',
                    'trade_off': '更大的m提高召回率但增加内存使用'
                },
                'ef_construct': {
                    'description': '构建时的动态候选列表大小',
                    'small_collections': '< 10K vectors: ef_construct=64',
                    'medium_collections': '10K-100K vectors: ef_construct=128',
                    'large_collections': '> 100K vectors: ef_construct=200',
                    'trade_off': '更大的ef_construct提高索引质量但增加构建时间'
                },
                'ef_search': {
                    'description': '搜索时的动态候选列表大小',
                    'recommended': 'ef_search = ef_construct',
                    'performance_tip': '可以适当降低ef_search以提高查询速度'
                }
            },
            'recommendations': [
                {
                    'scenario': '高召回率要求',
                    'settings': 'm=32, ef_construct=200, ef_search=256',
                    'use_case': '法律条款搜索、专利检索'
                },
                {
                    'scenario': '高速查询要求',
                    'settings': 'm=16, ef_construct=128, ef_search=64',
                    'use_case': '实时推荐、快速预览'
                },
                {
                    'scenario': '平衡模式',
                    'settings': 'm=24, ef_construct=150, ef_search=128',
                    'use_case': '通用搜索、混合查询'
                }
            ],
            'monitoring': {
                'metrics_to_track': [
                    '查询延迟(p95, p99)',
                    '召回率变化',
                    '内存使用',
                    '索引构建时间'
                ],
                'optimization_cycle': '每3-6个月根据查询模式调整'
            }
        }
    }

    # 保存指南
    with open('/Users/xujian/Athena工作平台/docs/hnsw_optimization_guide.json', 'w') as f:
        json.dump(guide, f, indent=2, ensure_ascii=False)

    logger.info('💾 HNSW优化指南已保存: docs/hnsw_optimization_guide.json')

def main():
    logger.info('🚀 开始HNSW参数优化...')

    # 1. 优化所有集合
    results = optimize_all_collections()

    # 2. 生成优化指南
    generate_hnsw_optimization_guide()

    # 3. 统计结果
    logger.info("\n📊 优化结果统计:")
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]

    logger.info(f"  ✅ 成功优化: {len(successful)} 个集合")
    logger.info(f"  ❌ 优化失败: {len(failed)} 个集合")

    if successful:
        total_vectors = sum(r['vector_count'] for r in successful)
        logger.info(f"  📦 涉及向量: {total_vectors:,}")

        logger.info("\n📋 优化详情:")
        for r in successful[:5]:  # 显示前5个
            params = r['optimized_params']
            logger.info(f"  • {r['collection']:30} : m={params['m']}, ef_construct={params['ef_construct']}")

    logger.info("\n✅ HNSW优化完成！")
    logger.info("\n后续建议:")
    logger.info('  1. 监控查询性能变化')
    logger.info('  2. 根据实际查询模式微调参数')
    logger.info('  3. 定期重新评估优化策略')

if __name__ == '__main__':
    main()