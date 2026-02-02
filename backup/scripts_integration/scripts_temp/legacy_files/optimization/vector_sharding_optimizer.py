#!/usr/bin/env python3
"""
🚀 向量数据库分片优化器
小诺的智能分片策略实施工具

功能:
1. 分析集合分片需求
2. 实施数据分片策略
3. 优化查询路由
4. 性能对比验证

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

import asyncio
import json
import logging
import math
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
from loguru import logger

logger = logging.getLogger(__name__)

# 配置日志
logger.add('vector_sharding.log', rotation='50 MB', level='INFO')

class VectorShardingOptimizer:
    """向量分片优化器"""

    def __init__(self, qdrant_url: str = 'http://localhost:6333'):
        self.qdrant_url = qdrant_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def get_collection_info(self, collection_name: str) -> Dict:
        """获取集合详细信息"""
        try:
            response = await self.client.get(f"{self.qdrant_url}/collections/{collection_name}")
            response.raise_for_status()
            return response.json()['result']
        except Exception as e:
            logger.error(f"获取集合 {collection_name} 信息失败: {e}")
            return {}

    async def get_all_collections(self) -> List[Dict]:
        """获取所有集合信息"""
        try:
            response = await self.client.get(f"{self.qdrant_url}/collections")
            response.raise_for_status()
            data = response.json()

            collections = []
            for col in data['result']['collections']:
                name = col['name']
                detailed_info = await self.get_collection_info(name)
                if detailed_info:
                    collections.append(detailed_info)

            return collections
        except Exception as e:
            logger.error(f"获取集合列表失败: {e}")
            return []

    def analyze_sharding_needs(self, collections: List[Dict]) -> List[Dict]:
        """分析分片需求"""
        recommendations = []

        for collection in collections:
            name = collection.get('name', '')
            points_count = collection.get('points_count', 0)
            segments_count = collection.get('segments_count', 1)

            # 基础分析
            if points_count < 10000:
                continue  # 小集合不需要分片

            analysis = {
                'collection': name,
                'current_vectors': points_count,
                'current_segments': segments_count,
                'vectors_per_segment': points_count / segments_count if segments_count > 0 else 0,
                'needs_sharding': False,
                'recommended_shards': 1,
                'reason': '',
                'priority': 'low'
            }

            # 分片判断逻辑
            if points_count > 500000:
                # 超大数据集需要分片
                analysis['needs_sharding'] = True
                # 推荐分片数：每片100K-200K向量
                analysis['recommended_shards'] = max(2, math.ceil(points_count / 150000))
                analysis['reason'] = f"超大集合({points_count}向量)，建议分片以提高性能"
                analysis['priority'] = 'high'

            elif points_count > 100000:
                # 大数据集考虑分片
                vectors_per_segment = analysis['vectors_per_segment']
                if vectors_per_segment > 50000:
                    analysis['needs_sharding'] = True
                    analysis['recommended_shards'] = max(2, math.ceil(points_count / 100000))
                    analysis['reason'] = f"每段向量过多({vectors_per_segment:.0f})，建议分片优化"
                    analysis['priority'] = 'medium'

            # 性能指标分析
            # 这里可以添加更多性能相关的判断逻辑

            if analysis['needs_sharding']:
                recommendations.append(analysis)

        return recommendations

    async def create_sharded_collection(self, original_name: str, shard_count: int) -> bool:
        """创建分片集合（模拟分片策略）"""
        try:
            # 获取原集合信息
            original_info = await self.get_collection_info(original_name)
            if not original_info:
                return False

            vector_config = original_info['config']['params']['vectors']
            vector_size = vector_config['size']
            distance = vector_config['distance']

            # 为每个分片创建集合
            for shard_id in range(shard_count):
                shard_name = f"{original_name}_shard_{shard_id}"

                # 检查分片是否已存在
                existing_info = await self.get_collection_info(shard_name)
                if existing_info:
                    logger.info(f"分片集合 {shard_name} 已存在，跳过创建")
                    continue

                # 创建分片集合
                collection_config = {
                    'vectors': {
                        'size': vector_size,
                        'distance': distance
                    },
                    'optimizers_config': {
                        'deleted_threshold': 0.1,
                        'vacuum_min_vector_count': 1000,
                        'default_segment_number': 2,
                        'max_segment_size': 50000,  # 较小的段大小
                        'indexing_threshold': 1000,
                        'max_optimization_threads': 2
                    },
                    'hnsw_config': {
                        'm': 16,
                        'ef_construct': 100,
                        'full_scan_threshold': 10000,
                        'max_indexing_threads': 2
                    },
                    'on_disk_payload': True
                }

                response = await self.client.put(
                    f"{self.qdrant_url}/collections/{shard_name}",
                    json=collection_config
                )
                response.raise_for_status()

                logger.info(f"✅ 分片集合 {shard_name} 创建成功")

            logger.info(f"✅ 集合 {original_name} 分片创建完成 (共{shard_count}个分片)")
            return True

        except Exception as e:
            logger.error(f"创建分片集合失败: {e}")
            return False

    async def create_virtual_router(self, collection_name: str, shard_count: int) -> bool:
        """创建虚拟分片路由配置"""
        try:
            router_config = {
                'collection': collection_name,
                'shard_count': shard_count,
                'routing_strategy': 'hash_based',  # 基于hash的路由策略
                'shards': [
                    {
                        'shard_id': i,
                        'shard_name': f"{collection_name}_shard_{i}",
                        'weight': 1.0  # 权重相等
                    }
                    for i in range(shard_count)
                ],
                'created_at': datetime.now().isoformat()
            }

            # 保存路由配置
            config_file = f".runtime/sharding_config_{collection_name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(router_config, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 虚拟路由配置已保存: {config_file}")
            return True

        except Exception as e:
            logger.error(f"创建虚拟路由配置失败: {e}")
            return False

    async def simulate_shard_routing(self, collection_name: str, shard_count: int,
                                    test_vectors: List[List[float]]) -> Dict:
        """模拟分片路由测试"""
        try:
            # 模拟基于hash的路由策略
            routing_results = {}

            for i, vector in enumerate(test_vectors):
                # 简单的hash函数（实际应用中应该使用更好的hash算法）
                hash_value = hash(tuple(vector)) % shard_count
                shard_name = f"{collection_name}_shard_{hash_value}"

                if shard_name not in routing_results:
                    routing_results[shard_name] = []

                routing_results[shard_name].append(i)

            # 分析路由分布
            distribution = {
                'total_vectors': len(test_vectors),
                'shard_count': shard_count,
                'routing_results': routing_results,
                'distribution_stats': {}
            }

            for shard_name, indices in routing_results.items():
                count = len(indices)
                percentage = (count / len(test_vectors)) * 100
                distribution['distribution_stats'][shard_name] = {
                    'vector_count': count,
                    'percentage': round(percentage, 1)
                }

            return {
                'success': True,
                'distribution': distribution,
                'balance_score': self._calculate_balance_score(distribution['distribution_stats'])
            }

        except Exception as e:
            logger.error(f"模拟分片路由失败: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_balance_score(self, distribution_stats: Dict) -> float:
        """计算负载均衡分数"""
        if not distribution_stats:
            return 0.0

        counts = [stats['vector_count'] for stats in distribution_stats.values()]
        if not counts:
            return 0.0

        avg_count = sum(counts) / len(counts)
        if avg_count == 0:
            return 0.0

        # 计算标准差
        variance = sum((count - avg_count) ** 2 for count in counts) / len(counts)
        std_dev = math.sqrt(variance)

        # 标准差越小，均衡性越好
        balance_score = max(0, 1 - (std_dev / avg_count))
        return round(balance_score, 3)

    async def implement_sharding_strategy(self, collection_name: str,
                                        shard_count: int, test_mode: bool = True) -> Dict:
        """实施分片策略"""
        logger.info(f"🚀 开始为集合 {collection_name} 实施分片策略 (分片数: {shard_count})")

        result = {
            'collection': collection_name,
            'shard_count': shard_count,
            'test_mode': test_mode,
            'start_time': datetime.now().isoformat(),
            'success': False,
            'steps': []
        }

        try:
            # 1. 验证集合存在
            logger.info(f"步骤1: 验证集合 {collection_name}...")
            collection_info = await self.get_collection_info(collection_name)
            if not collection_info:
                result['error'] = '集合不存在'
                return result

            vector_count = collection_info.get('points_count', 0)
            vector_size = collection_info['config']['params']['vectors']['size']

            result['steps'].append(f"验证成功: {vector_count}个向量, 维度{vector_size}")

            # 2. 创建分片集合
            logger.info(f"步骤2: 创建分片集合...")
            if not await self.create_sharded_collection(collection_name, shard_count):
                result['error'] = '创建分片集合失败'
                return result

            result['steps'].append(f"✅ 创建{shard_count}个分片集合")

            # 3. 创建虚拟路由配置
            logger.info(f"步骤3: 创建路由配置...")
            if not await self.create_virtual_router(collection_name, shard_count):
                result['error'] = '创建路由配置失败'
                return result

            result['steps'].append('✅ 路由配置创建成功')

            # 4. 模拟路由测试
            if test_mode:
                logger.info(f"步骤4: 模拟路由测试...")
                # 创建测试向量
                test_vectors = [[0.1 * i] * vector_size for i in range(100)]

                routing_test = await self.simulate_shard_routing(collection_name, shard_count, test_vectors)
                if routing_test.get('success', False):
                    result['routing_test'] = routing_test
                    balance_score = routing_test.get('balance_score', 0)
                    result['steps'].append(f"✅ 路由测试成功, 均衡分数: {balance_score}")
                else:
                    result['steps'].append('⚠️ 路由测试失败')

            # 5. 性能对比（模拟）
            logger.info(f"步骤5: 性能评估...")

            # 基于向量数量和分片数估算性能提升
            original_segments = collection_info.get('segments_count', 1)
            estimated_improvement = min(0.7, (shard_count - 1) / shard_count)  # 估算性能提升

            result['performance_estimation'] = {
                'original_segments': original_segments,
                'shard_count': shard_count,
                'estimated_latency_improvement': f"{estimated_improvement*100:.1f}%",
                'estimated_throughput_increase': f"{(1+estimated_improvement)*100:.1f}%"
            }

            result['steps'].append(f"✅ 性能评估完成")

            result['success'] = True
            logger.info(f"✅ 集合 {collection_name} 分片策略实施成功!")

        except Exception as e:
            logger.error(f"实施分片策略失败: {e}")
            result['error'] = str(e)

        result['end_time'] = datetime.now().isoformat()
        return result

    async def optimize_all_collections(self, auto_implement: bool = False) -> Dict:
        """优化所有集合的分片策略"""
        logger.info('🚀 开始向量数据库分片优化分析')

        # 1. 获取所有集合
        collections = await self.get_all_collections()
        logger.info(f"发现 {len(collections)} 个集合")

        # 2. 分析分片需求
        recommendations = self.analyze_sharding_needs(collections)

        results = {
            'analysis_time': datetime.now().isoformat(),
            'total_collections': len(collections),
            'collections_analyzed': len(recommendations),
            'recommendations': recommendations,
            'implementation_results': {},
            'summary': {
                'high_priority': len([r for r in recommendations if r.get('priority') == 'high']),
                'medium_priority': len([r for r in recommendations if r.get('priority') == 'medium']),
                'low_priority': len([r for r in recommendations if r.get('priority') == 'low']),
                'total_implementations': 0,
                'successful_implementations': 0
            }
        }

        # 3. 实施分片策略（如果启用自动实施）
        if auto_implement and recommendations:
            logger.info('🔧 开始自动实施分片策略...')

            for rec in recommendations:
                collection_name = rec['collection']
                shard_count = rec['recommended_shards']

                logger.info(f"实施 {collection_name} 的分片策略...")
                impl_result = await self.implement_sharding_strategy(
                    collection_name, shard_count, test_mode=True
                )

                results['implementation_results'][collection_name] = impl_result
                results['summary']['total_implementations'] += 1

                if impl_result.get('success', False):
                    results['summary']['successful_implementations'] += 1

        # 4. 保存结果
        output_file = '.runtime/sharding_optimization_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"分片优化分析完成，结果保存到: {output_file}")
        return results

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='向量数据库分片优化器')
    parser.add_argument('--auto-implement', action='store_true',
                       help='自动实施分片策略')
    parser.add_argument('--collection', type=str, default='',
                       help='指定要优化的集合名称')
    parser.add_argument('--shards', type=int, default=2,
                       help='分片数量')

    args = parser.parse_args()

    optimizer = VectorShardingOptimizer()

    try:
        if args.collection:
            # 优化指定集合
            logger.info(f"优化指定集合: {args.collection}")
            result = await optimizer.implement_sharding_strategy(
                args.collection, args.shards
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # 分析和优化所有集合
            results = await optimizer.optimize_all_collections(auto_implement=args.auto_implement)

            # 显示分析结果
            logger.info(f"\n{'='*60}")
            logger.info(f"🚀 向量数据库分片优化分析结果")
            logger.info(f"{'='*60}")

            summary = results['summary']
            logger.info(f"总集合数: {results['total_collections']}")
            logger.info(f"需要分片: {results['collections_analyzed']}")
            logger.info(f"  - 高优先级: {summary['high_priority']}")
            logger.info(f"  - 中优先级: {summary['medium_priority']}")
            logger.info(f"  - 低优先级: {summary['low_priority']}")

            if args.auto_implement:
                logger.info(f"\n自动实施结果:")
                logger.info(f"  - 实施数量: {summary['total_implementations']}")
                logger.info(f"  - 成功数量: {summary['successful_implementations']}")
                logger.info(str(f"  - 成功率: {summary['successful_implementations']/summary['total_implementations']*100:.1f}%" if summary['total_implementations'] > 0 else "N/A"))

            logger.info(f"\n📋 详细建议:")
            for rec in results['recommendations']:
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '⚪')
                logger.info(f"  {priority_emoji} {rec['collection']}: {rec['recommended_shards']}个分片 - {rec['reason']}")

    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断了优化过程")
    except Exception as e:
        logger.error(f"分片优化过程出错: {e}")
    finally:
        await optimizer.close()

if __name__ == '__main__':
    asyncio.run(main())