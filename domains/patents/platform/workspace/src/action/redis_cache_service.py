#!/usr/bin/env python3
"""
Redis分布式缓存服务
Redis Distributed Cache Service

功能特性：
- 分布式缓存支持
- 智能缓存策略
- 缓存预热机制
- 自动过期管理
- 序列化/反序列化支持

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import json
import logging
import pickle
import time
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Redis分布式缓存服务"""

    def __init__(self,
                 redis_url: str = 'redis://localhost:6379/0',
                 default_ttl: int = 300,
                 key_prefix: str = 'athena:patent:'):
        """
        初始化Redis缓存服务

        Args:
            redis_url: Redis连接URL
            default_ttl: 默认过期时间（秒）
            key_prefix: 键前缀
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._redis = None
        self._connection_pool = None
        self.logger = logging.getLogger(f"{__name__}.RedisCacheService")

    async def _get_redis(self):
        """获取Redis连接（懒加载）"""
        if self._redis is None:
            try:
                import aioredis
                self._redis = await aioredis.from_url(
                    self.redis_url,
                    encoding='utf-8',
                    decode_responses=False  # 需要原始bytes进行pickle
                )
                self.logger.info(f"✅ Redis连接成功: {self.redis_url}")
            except ImportError:
                self.logger.warning("⚠️ aioredis未安装，使用内存缓存替代")
                self._redis = InMemoryCache()
            except Exception as e:
                self.logger.error(f"❌ Redis连接失败: {e}，使用内存缓存替代")
                self._redis = InMemoryCache()
        return self._redis

    def _make_key(self, key: str) -> str:
        """生成带前缀的键"""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)

            # 尝试获取pickle序列化的数据
            value = await redis.get(full_key)

            if value is None:
                return None

            # 反序列化
            try:
                return pickle.loads(value)
            except (pickle.PickleError, EOFError):
                # 如果pickle失败，尝试JSON
                try:
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # 最后尝试直接返回字符串
                    return value.decode('utf-8')

        except Exception as e:
            self.logger.error(f"❌ 获取缓存失败 [{key}]: {e}")
            return None

    async def set(self,
                  key: str,
                  value: Any,
                  ttl: int | None = None) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None使用默认值

        Returns:
            是否设置成功
        """
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            ttl = ttl or self.default_ttl

            # 序列化：优先使用pickle，fallback到JSON
            try:
                serialized = pickle.dumps(value)
            except (pickle.PickleError, TypeError):
                try:
                    serialized = json.dumps(value).encode('utf-8')
                except (TypeError, ValueError):
                    serialized = str(value).encode('utf-8')

            # 设置缓存
            await redis.setex(full_key, ttl, serialized)

            self.logger.debug(f"✅ 缓存已设置: {full_key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            self.logger.error(f"❌ 设置缓存失败 [{key}]: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            await redis.delete(full_key)
            self.logger.debug(f"🗑️ 缓存已删除: {full_key}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 删除缓存失败 [{key}]: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            return await redis.exists(full_key) > 0
        except Exception as e:
            self.logger.error(f"❌ 检查缓存失败 [{key}]: {e}")
            return False

    async def get_batch(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取缓存

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_batch(self,
                       items: dict[str, Any],
                       ttl: int | None = None) -> dict[str, bool]:
        """
        批量设置缓存

        Args:
            items: 键值对字典
            ttl: 过期时间（秒）

        Returns:
            每个键的设置结果
        """
        result = {}
        for key, value in items.items():
            result[key] = await self.set(key, value, ttl)
        return result

    async def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存

        Args:
            pattern: 匹配模式（如 'patent:*'）

        Returns:
            清除的键数量
        """
        try:
            redis = await self._get_redis()
            full_pattern = self._make_key(pattern)

            # 搜索匹配的键
            keys = []
            async for key in redis.scan_iter(match=full_pattern):
                keys.append(key)

            # 批量删除
            if keys:
                await redis.delete(*keys)
                self.logger.info(f"🗑️ 清除了 {len(keys)} 个缓存键: {full_pattern}")
                return len(keys)

            return 0

        except Exception as e:
            self.logger.error(f"❌ 清除缓存失败 [{pattern}]: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        try:
            redis = await self._get_redis()

            # 获取Redis INFO
            if hasattr(redis, 'info'):
                info = await redis.info('stats')
                return {
                    'total_keys': info.get('keyspace', 0),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)
                }
            else:
                # 内存缓存统计
                return getattr(redis, 'stats', {})

        except Exception as e:
            self.logger.error(f"❌ 获取统计信息失败: {e}")
            return {}

    @asynccontextmanager
    async def cached(self,
                    key: str,
                    ttl: int | None = None):
        """
        缓存上下文管理器

        用法:
            async with cache_service.cached('my_key') as cached:
                if cached.found:
                    return cached.value
                else:
                    result = expensive_operation()
                    await cached.set(result)
                    return result
        """
        class CachedContext:
            def __init__(self, service, cache_key, cache_ttl):
                self.service = service
                self.key = cache_key
                self.ttl = cache_ttl
                self.found = False
                self.value = None

            async def set(self, value):
                await self.service.set(self.key, value, self.ttl)

        ctx = CachedContext(self, key, ttl)
        value = await self.get(key)
        if value is not None:
            ctx.found = True
            ctx.value = value

        yield ctx

    async def warm_up(self,
                     data_loader: dict[str, Any],
                     ttl: int | None = None) -> int:
        """
        缓存预热

        Args:
            data_loader: 数据加载器 {key: value}
            ttl: 过期时间

        Returns:
            预热的键数量
        """
        self.logger.info(f"🔥 开始缓存预热: {len(data_loader)} 项")
        start_time = time.time()

        success_count = 0
        for key, value in data_loader.items():
            if await self.set(key, value, ttl):
                success_count += 1

        elapsed = time.time() - start_time
        self.logger.info(f"✅ 缓存预热完成: {success_count}/{len(data_loader)} 项 (耗时: {elapsed:.2f}秒)")

        return success_count

    async def close(self):
        """关闭连接"""
        if self._redis and hasattr(self._redis, 'close'):
            await self._redis.close()
            self.logger.info("🔌 Redis连接已关闭")


class InMemoryCache:
    """内存缓存（fallback）"""

    def __init__(self):
        self._cache = {}
        self.stats = {
            'total_keys': 0,
            'hits': 0,
            'misses': 0
        }

    async def get(self, key: str):
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry is None or time.time() < expiry:
                self.stats['hits'] += 1
                return value
            else:
                del self._cache[key]
                self.stats['total_keys'] -= 1
        self.stats['misses'] += 1
        return None

    async def setex(self, key: str, ttl: int, value: bytes):
        expiry = time.time() + ttl if ttl > 0 else None
        if key not in self._cache:
            self.stats['total_keys'] += 1
        self._cache[key] = (value, expiry)

    async def set(self, key: str, value: Any):
        return await self.setex(key, 0, value)

    async def delete(self, *keys):
        count = 0
        for key in keys:
            if key in self._cache:
                del self._cache[key]
                self.stats['total_keys'] -= 1
                count += 1
        return count

    async def exists(self, key: str) -> bool:
        return key in self._cache

    async def scan_iter(self, match: str = None):
        for key in self._cache.keys():
            if match is None or key.match(match):
                yield key

    async def info(self, section: str = None):
        return {
            'keyspace': self.stats['total_keys'],
            'keyspace_hits': self.stats['hits'],
            'keyspace_misses': self.stats['misses']
        }

    async def close(self):
        self._cache.clear()
        self.stats['total_keys'] = 0


class SmartCacheStrategy:
    """智能缓存策略"""

    # 缓存策略配置
    STRATEGIES = {
        'patent_analysis': {
            'ttl': 3600,  # 1小时
            'warm_up': True,
            'prefetch': True
        },
        'patent_search': {
            'ttl': 1800,  # 30分钟
            'warm_up': True,
            'prefetch': False
        },
        'llm_result': {
            'ttl': 7200,  # 2小时
            'warm_up': False,
            'prefetch': False
        },
        'user_session': {
            'ttl': 86400,  # 24小时
            'warm_up': False,
            'prefetch': False
        }
    }

    @classmethod
    def get_strategy(cls, cache_type: str) -> dict[str, Any]:
        """获取缓存策略"""
        return cls.STRATEGIES.get(cache_type, {
            'ttl': 300,
            'warm_up': False,
            'prefetch': False
        })

    @classmethod
    def generate_cache_key(cls,
                          cache_type: str,
                          patent_data: dict[str, Any],
                          analysis_type: str = 'comprehensive') -> str:
        """
        生成智能缓存键

        Args:
            cache_type: 缓存类型
            patent_data: 专利数据
            analysis_type: 分析类型

        Returns:
            缓存键
        """
        import hashlib

        # 提取关键特征
        features = [
            cache_type,
            analysis_type,
            str(patent_data.get('title', '')),
            str(patent_data.get('abstract', ''))[:500]  # 摘要前500字符
        ]

        # 生成哈希
        content = ':'.join(features)
        hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()

        return f"{cache_type}:{analysis_type}:{hash_value}"


# =============================================================================
# 单例模式
# =============================================================================

_global_cache_service: RedisCacheService | None = None


def get_cache_service() -> RedisCacheService:
    """获取全局缓存服务实例"""
    global _global_cache_service
    if _global_cache_service is None:
        _global_cache_service = RedisCacheService()
    return _global_cache_service


# =============================================================================
# 测试代码
# =============================================================================

async def test_redis_cache():
    """测试Redis缓存服务"""
    logger.info("=" * 60)
    logger.info("🧪 测试Redis缓存服务")
    logger.info("=" * 60)

    # 创建缓存服务
    cache = RedisCacheService()

    # 测试基本操作
    logger.info("\n📝 测试1: 基本GET/SET操作")
    await cache.set('test_key', {'data': 'test_value'}, ttl=60)
    value = await cache.get('test_key')
    logger.info(f"✅ GET结果: {value}")

    # 测试批量操作
    logger.info("\n📦 测试2: 批量操作")
    batch_data = {
        'key1': 'value1',
        'key2': {'nested': 'data'},
        'key3': [1, 2, 3]
    }
    result = await cache.set_batch(batch_data, ttl=60)
    logger.info(f"✅ 批量SET结果: {result}")

    batch_get = await cache.get_batch(['key1', 'key2', 'key3'])
    logger.info(f"✅ 批量GET结果: {batch_get}")

    # 测试智能缓存键
    logger.info("\n🔑 测试3: 智能缓存键生成")
    patent_data = {
        'title': '基于深度学习的图像识别系统',
        'abstract': '本发明公开了一种基于深度学习的...'
    }
    cache_key = SmartCacheStrategy.generate_cache_key(
        'patent_analysis', patent_data, 'novelty'
    )
    logger.info(f"✅ 生成的缓存键: {cache_key}")

    # 测试缓存预热
    logger.info("\n🔥 测试4: 缓存预热")
    warm_up_data = {
        'warm_key1': 'data1',
        'warm_key2': 'data2',
        'warm_key3': 'data3'
    }
    count = await cache.warm_up(warm_up_data, ttl=60)
    logger.info(f"✅ 预热完成: {count} 项")

    # 测试统计信息
    logger.info("\n📊 测试5: 统计信息")
    stats = await cache.get_stats()
    logger.info(f"✅ 缓存统计: {json.dumps(stats, indent=2)}")

    # 测试模式清除
    logger.info("\n🗑️ 测试6: 模式清除")
    cleared = await cache.clear_pattern('warm_*')
    logger.info(f"✅ 清除了 {cleared} 个缓存")

    logger.info("\n" + "=" * 60)
    logger.info("🎉 所有测试完成！")
    logger.info("=" * 60)

    await cache.close()


if __name__ == '__main__':
    asyncio.run(test_redis_cache())
