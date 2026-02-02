#!/usr/bin/env python3
"""
🚀 查询缓存优化器
小诺的智能查询缓存系统

功能:
1. 实现查询结果缓存
2. 缓存策略优化
3. 缓存性能监控
4. 智能缓存清理

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from loguru import logger

logger = logging.getLogger(__name__)

# 配置日志
logger.add('query_cache.log', rotation='50 MB', level='INFO')

@dataclass
class CacheConfig:
    """缓存配置"""
    max_size: int = 10000  # 最大缓存条目数
    ttl_seconds: int = 3600  # 缓存过期时间（秒）
    cleanup_interval: int = 300  # 清理间隔（秒）
    similarity_threshold: float = 0.95  # 相似度阈值

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Dict
    timestamp: datetime
    hit_count: int = 0
    size_bytes: int = 0

class QueryCacheOptimizer:
    """查询缓存优化器"""

    def __init__(self, qdrant_url: str = 'http://localhost:6333', config: CacheConfig = None):
        self.qdrant_url = qdrant_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.config = config or CacheConfig()

        # 内存缓存存储
        self.cache: Dict[str, CacheEntry] = {}

        # 缓存统计
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_size': 0,
            'total_cached_bytes': 0,
            'last_cleanup': datetime.now()
        }

        # 缓存目录
        self.cache_dir = '.runtime/query_cache'
        os.makedirs(self.cache_dir, exist_ok=True)

        # 启动清理任务
        self._cleanup_task = None

    def _generate_cache_key(self, collection_name: str, vector: List[float],
                          limit: int = 10, with_payload: bool = True,
                          additional_params: Dict = None) -> str:
        """生成缓存键"""
        # 使用向量数据的前几个值来生成键
        vector_sample = vector[:min(10, len(vector))]  # 取前10个值

        key_data = {
            'collection': collection_name,
            'vector_sample': vector_sample,
            'limit': limit,
            'with_payload': with_payload,
            'additional_params': additional_params or {}
        }

        # 序列化并计算hash
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _serialize_entry(self, entry: CacheEntry) -> bytes:
        """序列化缓存条目"""
        data = {
            'key': entry.key,
            'data': entry.data,
            'timestamp': entry.timestamp.isoformat(),
            'hit_count': entry.hit_count
        }
        return pickle.dumps(data)

    def _deserialize_entry(self, data: bytes) -> CacheEntry:
        """反序列化缓存条目"""
        cache_data = pickle.loads(data)
        return CacheEntry(
            key=cache_data['key'],
            data=cache_data['data'],
            timestamp=datetime.fromisoformat(cache_data['timestamp']),
            hit_count=cache_data.get('hit_count', 0),
            size_bytes=len(data)
        )

    async def load_cache_from_disk(self) -> int:
        """从磁盘加载缓存"""
        loaded_count = 0

        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.cache')]

            for cache_file in cache_files:
                file_path = os.path.join(self.cache_dir, cache_file)

                try:
                    with open(file_path, 'rb') as f:
                        entry = self._deserialize_entry(f.read())

                    # 检查是否过期
                    if datetime.now() - entry.timestamp < timedelta(seconds=self.config.ttl_seconds):
                        self.cache[entry.key] = entry
                        loaded_count += 1
                    else:
                        # 删除过期文件
                        os.remove(file_path)

                except Exception as e:
                    logger.warning(f"加载缓存文件 {cache_file} 失败: {e}")
                    try:
                        os.remove(file_path)
                    except:
                        pass

            logger.info(f"从磁盘加载了 {loaded_count} 个缓存条目")
            return loaded_count

        except Exception as e:
            logger.error(f"从磁盘加载缓存失败: {e}")
            return 0

    async def save_cache_to_disk(self) -> int:
        """保存缓存到磁盘"""
        saved_count = 0

        try:
            for key, entry in self.cache.items():
                file_path = os.path.join(self.cache_dir, f"{key}.cache")

                try:
                    with open(file_path, 'wb') as f:
                        f.write(self._serialize_entry(entry))
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"保存缓存条目 {key} 失败: {e}")

            logger.info(f"保存了 {saved_count} 个缓存条目到磁盘")
            return saved_count

        except Exception as e:
            logger.error(f"保存缓存到磁盘失败: {e}")
            return 0

    async def cleanup_expired_cache(self) -> Dict:
        """清理过期缓存"""
        cleanup_start = time.time()
        current_time = datetime.now()

        expired_keys = []
        total_freed_bytes = 0

        for key, entry in self.cache.items():
            if current_time - entry.timestamp > timedelta(seconds=self.config.ttl_seconds):
                expired_keys.append(key)
                total_freed_bytes += entry.size_bytes

        # 从内存中删除过期条目
        for key in expired_keys:
            del self.cache[key]

            # 删除磁盘文件
            file_path = os.path.join(self.cache_dir, f"{key}.cache")
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"删除缓存文件 {file_path} 失败: {e}")

        # 如果缓存仍然过大，删除最旧的条目
        if len(self.cache) > self.config.max_size:
            # 按时间戳排序，删除最旧的条目
            sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].timestamp)
            excess_count = len(self.cache) - self.config.max_size

            for i in range(excess_count):
                key, entry = sorted_entries[i]
                del self.cache[key]
                total_freed_bytes += entry.size_bytes

                # 删除磁盘文件
                file_path = os.path.join(self.cache_dir, f"{key}.cache")
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.warning(f"删除缓存文件 {file_path} 失败: {e}")

        cleanup_time = time.time() - cleanup_start

        result = {
            'cleaned_entries': len(expired_keys),
            'excess_entries_removed': excess_count if 'excess_count' in locals() else 0,
            'total_freed_bytes': total_freed_bytes,
            'cleanup_time_seconds': round(cleanup_time, 3),
            'current_cache_size': len(self.cache),
            'timestamp': datetime.now().isoformat()
        }

        self.stats['last_cleanup'] = current_time
        logger.info(f"缓存清理完成: {result['cleaned_entries']}个过期条目, 释放{total_freed_bytes}字节")

        return result

    async def cached_search(self, collection_name: str, vector: List[float],
                          limit: int = 10, with_payload: bool = True,
                          additional_params: Dict = None) -> Dict:
        """缓存搜索查询"""
        self.stats['total_requests'] += 1

        # 生成缓存键
        cache_key = self._generate_cache_key(collection_name, vector, limit, with_payload, additional_params)

        # 检查缓存
        if cache_key in self.cache:
            entry = self.cache[cache_key]

            # 检查是否过期
            if datetime.now() - entry.timestamp < timedelta(seconds=self.config.ttl_seconds):
                entry.hit_count += 1
                self.stats['cache_hits'] += 1

                logger.debug(f"缓存命中: {cache_key}")
                return {
                    'cached': True,
                    'cache_key': cache_key,
                    'hit_count': entry.hit_count,
                    'result': entry.data,
                    'timestamp': entry.timestamp.isoformat()
                }
            else:
                # 删除过期条目
                del self.cache[cache_key]
                file_path = os.path.join(self.cache_dir, f"{cache_key}.cache")
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass

        # 缓存未命中，执行实际搜索
        self.stats['cache_misses'] += 1

        search_data = {
            'vector': vector,
            'limit': limit,
            'with_payload': with_payload
        }

        if additional_params:
            search_data.update(additional_params)

        try:
            start_time = time.time()
            response = await self.client.post(
                f"{self.qdrant_url}/collections/{collection_name}/points/search",
                json=search_data
            )
            search_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result_data = response.json()

                # 创建缓存条目
                cache_entry = CacheEntry(
                    key=cache_key,
                    data={
                        'result': result_data['result'],
                        'search_time_ms': round(search_time, 2),
                        'query_params': search_data
                    },
                    timestamp=datetime.now()
                )

                # 序列化以计算大小
                serialized = self._serialize_entry(cache_entry)
                cache_entry.size_bytes = len(serialized)

                # 添加到缓存
                self.cache[cache_key] = cache_entry
                self.stats['cache_size'] = len(self.cache)
                self.stats['total_cached_bytes'] += cache_entry.size_bytes

                # 异步保存到磁盘（不阻塞响应）
                asyncio.create_task(self._save_single_entry(cache_key, cache_entry))

                logger.debug(f"缓存添加: {cache_key} (大小: {cache_entry.size_bytes}字节)")

                return {
                    'cached': False,
                    'cache_key': cache_key,
                    'search_time_ms': round(search_time, 2),
                    'result': result_data['result']
                }
            else:
                logger.error(f"搜索请求失败: {response.status_code}")
                return {
                    'error': f"搜索失败: {response.status_code}",
                    'response': response.text
                }

        except Exception as e:
            logger.error(f"搜索请求异常: {e}")
            return {'error': str(e)}

    async def _save_single_entry(self, key: str, entry: CacheEntry):
        """保存单个缓存条目到磁盘"""
        try:
            file_path = os.path.join(self.cache_dir, f"{key}.cache")
            with open(file_path, 'wb') as f:
                f.write(self._serialize_entry(entry))
        except Exception as e:
            logger.warning(f"保存缓存条目 {key} 到磁盘失败: {e}")

    async def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        hit_rate = 0
        if self.stats['total_requests'] > 0:
            hit_rate = (self.stats['cache_hits'] / self.stats['total_requests']) * 100

        # 计算平均存储大小
        avg_entry_size = 0
        if self.cache:
            avg_entry_size = sum(entry.size_bytes for entry in self.cache.values()) / len(self.cache)

        return {
            'cache_config': {
                'max_size': self.config.max_size,
                'ttl_seconds': self.config.ttl_seconds,
                'cleanup_interval': self.config.cleanup_interval
            },
            'performance_stats': {
                'total_requests': self.stats['total_requests'],
                'cache_hits': self.stats['cache_hits'],
                'cache_misses': self.stats['cache_misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'cache_size': len(self.cache),
                'total_cached_bytes': self.stats['total_cached_bytes'],
                'avg_entry_size_bytes': round(avg_entry_size, 1)
            },
            'memory_usage': {
                'estimated_memory_mb': round(self.stats['total_cached_bytes'] / (1024 * 1024), 2),
                'cache_entries': len(self.cache),
                'max_entries': self.config.max_size
            },
            'last_cleanup': self.stats['last_cleanup'].isoformat(),
            'timestamp': datetime.now().isoformat()
        }

    async def performance_test(self, collection_name: str, test_count: int = 100) -> Dict:
        """性能测试"""
        logger.info(f"开始查询缓存性能测试 (集合: {collection_name}, 测试次数: {test_count})")

        # 获取集合信息
        try:
            response = await self.client.get(f"{self.qdrant_url}/collections/{collection_name}")
            response.raise_for_status()
            collection_info = response.json()['result']
            vector_size = collection_info['config']['params']['vectors']['size']
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {'error': str(e)}

        # 生成测试向量
        test_vectors = [[0.1 * i] * vector_size for i in range(test_count)]

        # 第一轮：冷缓存测试
        cold_times = []
        logger.info('第一轮：冷缓存测试...')

        for i, vector in enumerate(test_vectors[:min(20, test_count)]):
            start_time = time.time()
            result = await self.cached_search(collection_name, vector, limit=5)
            search_time = (time.time() - start_time) * 1000

            if 'search_time_ms' in result:
                cold_times.append(result['search_time_ms'])

            if i % 5 == 0:
                logger.info(f"  冷缓存测试进度: {i+1}/{min(20, test_count)}")

        # 第二轮：热缓存测试
        hot_times = []
        logger.info('第二轮：热缓存测试...')

        for i, vector in enumerate(test_vectors[:min(20, test_count)]):
            start_time = time.time()
            result = await self.cached_search(collection_name, vector, limit=5)
            search_time = (time.time() - start_time) * 1000

            if result.get('cached', False):
                hot_times.append(search_time)

            if i % 5 == 0:
                logger.info(f"  热缓存测试进度: {i+1}/{min(20, test_count)}")

        # 计算统计结果
        cold_avg = sum(cold_times) / len(cold_times) if cold_times else 0
        hot_avg = sum(hot_times) / len(hot_times) if hot_times else 0
        speedup = cold_avg / hot_avg if hot_avg > 0 else 0

        # 获取缓存统计
        cache_stats = await self.get_cache_stats()

        performance_result = {
            'test_info': {
                'collection': collection_name,
                'test_count': len(cold_times),
                'vector_dimension': vector_size
            },
            'cold_cache': {
                'avg_response_time_ms': round(cold_avg, 2),
                'min_time_ms': round(min(cold_times), 2) if cold_times else 0,
                'max_time_ms': round(max(cold_times), 2) if cold_times else 0,
                'total_queries': len(cold_times)
            },
            'hot_cache': {
                'avg_response_time_ms': round(hot_avg, 2),
                'min_time_ms': round(min(hot_times), 2) if hot_times else 0,
                'max_time_ms': round(max(hot_times), 2) if hot_times else 0,
                'total_queries': len(hot_times),
                'cache_hit_rate': len(hot_times) / len(cold_times) * 100 if cold_times else 0
            },
            'improvement': {
                'speedup_factor': round(speedup, 2),
                'latency_reduction_ms': round(cold_avg - hot_avg, 2),
                'latency_reduction_percent': round((cold_avg - hot_avg) / cold_avg * 100, 1) if cold_avg > 0 else 0
            },
            'cache_stats': cache_stats,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"性能测试完成 - 速度提升: {speedup:.2f}x, 延迟减少: {performance_result['improvement']['latency_reduction_percent']:.1f}%")

        return performance_result

    async def start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info(f"缓存清理任务已启动 (间隔: {self.config.cleanup_interval}秒)")

    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self.cleanup_expired_cache()
            except asyncio.CancelledError:
                logger.info('缓存清理任务已取消')
                break
            except Exception as e:
                logger.error(f"缓存清理任务出错: {e}")

    async def start(self):
        """启动缓存优化器"""
        logger.info('🚀 启动查询缓存优化器')

        # 加载现有缓存
        await self.load_cache_from_disk()

        # 启动清理任务
        await self.start_cleanup_task()

        logger.info('✅ 查询缓存优化器启动完成')

    async def stop(self):
        """停止缓存优化器"""
        logger.info('🛑 停止查询缓存优化器')

        # 停止清理任务
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 保存缓存到磁盘
        await self.save_cache_to_disk()

        # 关闭客户端
        await self.client.aclose()

        logger.info('✅ 查询缓存优化器已停止')

    async def close(self):
        """关闭客户端（兼容性方法）"""
        await self.stop()

async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='查询缓存优化器')
    parser.add_argument('--test-collection', type=str, default='',
                       help='测试指定集合的缓存性能')
    parser.add_argument('--test-count', type=int, default=100,
                       help='性能测试的查询次数')
    parser.add_argument('--stats', action='store_true',
                       help='显示缓存统计信息')
    parser.add_argument('--cleanup', action='store_true',
                       help='执行缓存清理')

    args = parser.parse_args()

    # 创建缓存优化器
    config = CacheConfig(
        max_size=5000,
        ttl_seconds=1800,  # 30分钟
        cleanup_interval=300  # 5分钟
    )

    optimizer = QueryCacheOptimizer(config=config)

    try:
        # 启动优化器
        await optimizer.start()

        if args.cleanup:
            # 执行清理
            logger.info('🧹 执行缓存清理...')
            cleanup_result = await optimizer.cleanup_expired_cache()
            print(json.dumps(cleanup_result, ensure_ascii=False, indent=2))

        if args.stats:
            # 显示统计信息
            stats = await optimizer.get_cache_stats()
            print(json.dumps(stats, ensure_ascii=False, indent=2))

        if args.test_collection:
            # 执行性能测试
            test_result = await optimizer.performance_test(args.test_collection, args.test_count)
            print(json.dumps(test_result, ensure_ascii=False, indent=2))

        if not any([args.cleanup, args.stats, args.test_collection]):
            # 演示缓存功能
            logger.info('演示查询缓存功能...')

            # 测试集合
            test_collection = 'ai_technical_terms_vector_db'
            test_vector = [0.1] * 384

            # 第一次查询（缓存未命中）
            result1 = await optimizer.cached_search(test_collection, test_vector)
            logger.info(f"第一次查询: 缓存={result1.get('cached', False)}")

            # 第二次查询（缓存命中）
            result2 = await optimizer.cached_search(test_collection, test_vector)
            logger.info(f"第二次查询: 缓存={result2.get('cached', False)}, 命中次数={result2.get('hit_count', 0)}")

            # 显示缓存统计
            stats = await optimizer.get_cache_stats()
            logger.info(f"\n缓存统计:")
            logger.info(f"  总请求数: {stats['performance_stats']['total_requests']}")
            logger.info(f"  缓存命中: {stats['performance_stats']['cache_hits']}")
            logger.info(f"  命中率: {stats['performance_stats']['hit_rate_percent']:.1f}%")
            logger.info(f"  缓存大小: {stats['memory_usage']['cache_entries']} 个条目")
            logger.info(f"  内存使用: {stats['memory_usage']['estimated_memory_mb']:.2f} MB")

    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断了缓存优化器")
    except Exception as e:
        logger.error(f"缓存优化器运行出错: {e}")
    finally:
        await optimizer.stop()

if __name__ == '__main__':
    asyncio.run(main())