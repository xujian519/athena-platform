#!/usr/bin/env python3
"""
Redis缓存管理器
Redis Cache Manager for Patent Vectors

提供高性能的向量缓存服务
"""

# Numpy兼容性导入
import hashlib
import json
import logging
import pickle
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import redis

from config.numpy_compatibility import random

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """缓存配置"""
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    health_check_interval: int = 30

class RedisCacheManager:
    """Redis缓存管理器"""

    def __init__(self, config: CacheConfig = None):
        """初始化缓存管理器

        Args:
            config: Redis配置
        """
        self.config = config or CacheConfig()
        self.redis_client = None
        self.lock = threading.Lock()
        self.connected = False
        self.connection_attempts = 0
        self.max_retry_attempts = 3
        self._initialize_connection()

        # 缓存统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0,
            'last_updated': datetime.now()
        }

        # 缓存键前缀
        self.prefix = 'patent_vector:'

    def _initialize_connection(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=False,  # 保持二进制数据
                health_check_interval=self.config.health_check_interval
            )

            # 测试连接
            self.redis_client.ping()
            self.connected = True
            logger.info('✅ Redis连接成功')

        except Exception as e:
            logger.warning(f"Redis连接失败: {e}，将使用内存缓存")
            self.connected = False
            # 回退到内存缓存
            self._init_memory_cache()

    def _init_memory_cache(self):
        """初始化内存缓存作为回退方案"""
        self.memory_cache = {}
        self.memory_cache_expiry = {}
        logger.info('使用内存缓存作为回退方案')

    def is_connected(self) -> bool:
        """检查Redis是否连接"""
        if not self.connected:
            return False
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
        except Exception:
            self.connected = False
            return False
        return False

    def _generate_key(self, key_prefix: str, *args) -> str:
        """生成缓存键"""
        content = '|'.join(str(arg) for arg in args)
        hash_value = hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()
        return f"{self.prefix}{key_prefix}:{hash_value}"

    def _serialize(self, data: Any) -> bytes:
        """序列化数据"""
        # 使用pickle进行序列化，支持numpy数组
        try:
            return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            logger.error(f"序列化失败: {e}")
            raise

    def _deserialize(self, data: bytes) -> Any:
        """反序列化数据"""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"反序列化失败: {e}")
            # 尝试使用JSON作为备用方案
            try:
                return json.loads(data.decode())
            except Exception:
                return data

    def get(self, key_prefix: str, *args) -> Any | None:
        """获取缓存值"""
        cache_key = self._generate_key(key_prefix, *args)

        try:
            if self.is_connected():
                # 使用Redis
                data = self.redis_client.get(cache_key)
                if data:
                    self.stats['hits'] += 1
                    return self._deserialize(data)
                else:
                    self.stats['misses'] += 1
                    return None
            else:
                # 使用内存缓存
                return self._get_memory_cache(cache_key)

        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            self.stats['errors'] += 1
            return None

    def _get_memory_cache(self, key: str) -> Any | None:
        """从内存缓存获取"""
        if key in self.memory_cache:
            # 检查是否过期
            if key in self.memory_cache_expiry:
                if datetime.now() < self.memory_cache_expiry[key]:
                    self.stats['hits'] += 1
                    return self.memory_cache[key]
                else:
                    # 删除过期缓存
                    del self.memory_cache[key]
                    if key in self.memory_cache_expiry:
                        del self.memory_cache_expiry[key]
            else:
                # 没有过期时间
                self.stats['hits'] += 1
                return self.memory_cache[key]

        self.stats['misses'] += 1
        return None

    def set(self, key_prefix: str, *args, value: Any, ttl: int = 3600):
        """设置缓存值

        Args:
            key_prefix: 键前缀
            *args: 键参数
            value: 缓存值
            ttl: 过期时间（秒），默认1小时
        """
        cache_key = self._generate_key(key_prefix, *args)

        try:
            if self.is_connected():
                # 使用Redis
                serialized_data = self._serialize(value)
                self.redis_client.setex(cache_key, ttl, serialized_data)
                self.stats['sets'] += 1
            else:
                # 使用内存缓存
                self._set_memory_cache(cache_key, value, ttl)

        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            self.stats['errors'] += 1

    def _set_memory_cache(self, key: str, value: Any, ttl: int):
        """设置内存缓存"""
        self.memory_cache[key] = value
        if ttl > 0:
            self.memory_cache_expiry[key] = datetime.now() + timedelta(seconds=ttl)
        self.stats['sets'] += 1

    def mget(self, keys: list[tuple]) -> dict[str, Any]:
        """批量获取缓存

        Args:
            keys: [(key_prefix, arg1, arg2, ...), ...]

        Returns:
            {cache_key: value} 的字典
        """
        results = {}

        # 生成所有缓存键
        cache_keys = [(self._generate_key(*key_tuple), key_tuple) for key_tuple in keys]

        try:
            if self.is_connected():
                # Redis批量获取
                key_list = [cache_key for cache_key, _ in cache_keys]
                values = self.redis_client.mget(key_list)

                for (cache_key, original_key), value in zip(cache_keys, values, strict=False):
                    if value:
                        results[f"{original_key}"] = self._deserialize(value)
                        self.stats['hits'] += 1
                    else:
                        self.stats['misses'] += 1
            else:
                # 内存缓存批量获取
                for cache_key, original_key in cache_keys:
                    value = self._get_memory_cache(cache_key)
                    if value:
                        results[f"{original_key}"] = value

        except Exception as e:
            logger.error(f"批量缓存获取失败: {e}")
            self.stats['errors'] += 1

        return results

    def mset(self, items: list[tuple], ttl: int = 3600):
        """批量设置缓存

        Args:
            items: [(key_prefix, arg1, arg2, ..., value), ...]
            ttl: 过期时间（秒）
        """
        try:
            if self.is_connected():
                # Redis批量设置
                pipe = self.redis_client.pipeline()
                for item in items:
                    if len(item) < 2:
                        continue
                    cache_key = self._generate_key(*item[:-1])
                    serialized_data = self._serialize(item[-1])
                    pipe.setex(cache_key, ttl, serialized_data)

                pipe.execute()
                self.stats['sets'] += len(items)
            else:
                # 内存缓存批量设置
                for item in items:
                    if len(item) < 2:
                        continue
                    cache_key = self._generate_key(*item[:-1])
                    self._set_memory_cache(cache_key, item[-1], ttl)

        except Exception as e:
            logger.error(f"批量缓存设置失败: {e}")
            self.stats['errors'] += 1

    def delete(self, key_prefix: str, *args):
        """删除缓存"""
        cache_key = self._generate_key(key_prefix, *args)

        try:
            if self.is_connected():
                self.redis_client.delete(cache_key)
            else:
                # 内存缓存删除
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
                if cache_key in self.memory_cache_expiry:
                    del self.memory_cache_expiry[cache_key]

        except Exception as e:
            logger.error(f"缓存删除失败: {e}")

    def clear_prefix(self, key_prefix: str):
        """清除指定前缀的所有缓存"""
        try:
            if self.is_connected():
                pattern = f"{self.prefix}{key_prefix}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"清除了 {len(keys)} 个缓存项")
            else:
                # 内存缓存清除
                prefix = f"{self.prefix}{key_prefix}:"
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    if key in self.memory_cache_expiry:
                        del self.memory_cache_expiry[key]
                logger.info(f"清除了 {len(keys_to_delete)} 个内存缓存项")

        except Exception as e:
            logger.error(f"清除缓存失败: {e}")

    def clear_all(self):
        """清除所有缓存"""
        try:
            if self.is_connected():
                pattern = f"{self.prefix}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"清除了 {len(keys)} 个缓存项")
            else:
                # 清除所有内存缓存
                self.memory_cache.clear()
                self.memory_cache_expiry.clear()
                logger.info('清除了所有内存缓存')

        except Exception as e:
            logger.error(f"清除所有缓存失败: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / max(1, total_requests)

        stats = {
            'connected': self.connected,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'errors': self.stats['errors'],
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'last_updated': self.stats['last_updated']
        }

        # 如果连接到Redis，获取Redis信息
        if self.is_connected():
            try:
                info = self.redis_client.info()
                stats['redis_info'] = {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            except Exception:
                pass

        # 如果使用内存缓存，获取内存缓存信息
        if not self.connected:
            stats['memory_cache_size'] = len(self.memory_cache)
            stats['memory_cache_expiry_size'] = len(self.memory_cache_expiry)

        return stats

    def cleanup(self):
        """清理资源"""
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info('Redis连接已关闭')
        except Exception:
            pass
        finally:
            self.connected = False

# 测试函数
def test_redis_cache():
    """测试Redis缓存功能"""
    logger.info("\n=== 测试Redis缓存管理器 ===\n")

    cache = RedisCacheManager()

    try:
        # 测试基本缓存操作
        logger.info('1. 测试基本缓存操作...')

        # 设置缓存
        test_data = {
            'vectors': random((3, 768)).astype(np.float32),
            'metadata': {'model': 'bge-base-zh-v1.5', 'timestamp': datetime.now().isoformat()}
        }

        cache.set('test', 'vector1', value=test_data, ttl=60)
        logger.info('   ✅ 缓存设置成功')

        # 获取缓存
        retrieved_data = cache.get('test', 'vector1')
        if retrieved_data:
            logger.info(f"   ✅ 缓存获取成功，向量形状: {retrieved_data['vectors'].shape}")
            logger.info(f"   模型: {retrieved_data['metadata']['model']}")
        else:
            logger.info('   ❌ 缓存获取失败')

        # 测试批量操作
        logger.info("\n2. 测试批量操作...")

        batch_data = [
            ('batch', 'item1', random(768).astype(np.float32)),
            ('batch', 'item2', random(768).astype(np.float32)),
            ('batch', 'item3', {'text': '测试文本', 'score': 0.95})
        ]

        cache.mset(batch_data, ttl=60)
        logger.info('   ✅ 批量设置成功')

        batch_keys = [('batch', 'item1'), ('batch', 'item2'), ('batch', 'item3')]
        batch_results = cache.mget(batch_keys)
        logger.info(f"   ✅ 批量获取成功，获取到 {len(batch_results)} 个值")

        # 测试缓存统计
        logger.info("\n3. 缓存统计:")
        stats = cache.get_stats()
        logger.info(f"   连接状态: {'Redis' if stats['connected'] else '内存缓存'}")
        logger.info(f"   命中率: {stats['hit_rate']:.2%}")
        logger.info(f"   总请求: {stats['total_requests']}")
        logger.info(f"   设置次数: {stats['sets']}")

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
    finally:
        cache.cleanup()

if __name__ == '__main__':
    test_redis_cache()
