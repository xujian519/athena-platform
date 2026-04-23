#!/usr/bin/env python3
from __future__ import annotations
"""
Query Engine缓存管理
Query Engine Cache Management

提供查询缓存策略和管理功能

作者: Athena平台团队
版本: 1.0.0
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from core.query_engine.base import CacheStrategy
from core.query_engine.types import CacheKey, QueryResult, QueryStatus

logger = logging.getLogger(__name__)


class MemoryCache(CacheStrategy):
    """
    内存缓存策略

    使用字典存储查询结果
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self._cache: dict[str, tuple[QueryResult, datetime]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> QueryResult | None:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            QueryResult | None: 缓存的结果
        """
        if key not in self._cache:
            self._misses += 1
            return None

        result, expiry = self._cache[key]

        # 检查是否过期
        if datetime.now() > expiry:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        # 更新状态为缓存命中
        result.status = QueryStatus.CACHED
        return result

    async def set(
        self,
        key: str,
        value: QueryResult,
        ttl: Optional[int] = None,
    ) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        # 检查缓存大小
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._evict_oldest()

        ttl = ttl or self._default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    async def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计

        Returns:
            dict: 缓存统计信息
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "type": "memory",
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2%}",
        }

    def _evict_oldest(self) -> None:
        """淘汰最旧的缓存条目"""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]


class RedisCache(CacheStrategy):
    """
    Redis缓存策略

    使用Redis存储查询结果
    """

    def __init__(self, redis_client, key_prefix: str = "query_cache:"):
        """
        初始化Redis缓存

        Args:
            redis_client: Redis客户端实例
            key_prefix: 键前缀
        """
        self._redis = redis_client
        self._key_prefix = key_prefix

    def _make_key(self, key: str) -> str:
        """生成Redis键"""
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> QueryResult | None:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            QueryResult | None: 缓存的结果
        """
        try:
            redis_key = self._make_key(key)
            data = await self._redis.get(redis_key)

            if not data:
                return None

            result_dict = json.loads(data)
            result = QueryResult(
                data=result_dict["data"],
                status=QueryStatus.CACHED,
                stats=QueryStats(**result_dict["stats"]),
                error=result_dict.get("error"),
                metadata=result_dict.get("metadata", {}),
            )
            return result
        except Exception as e:
            logger.error(f"Redis缓存读取失败: {e}")
            return None

    async def set(
        self,
        key: str,
        value: QueryResult,
        ttl: Optional[int] = None,
    ) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        try:
            redis_key = self._make_key(key)
            data = json.dumps(value.to_dict())

            if ttl:
                await self._redis.setex(redis_key, ttl, data)
            else:
                await self._redis.set(redis_key, data)
        except Exception as e:
            logger.error(f"Redis缓存写入失败: {e}")

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        try:
            redis_key = self._make_key(key)
            result = await self._redis.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis缓存删除失败: {e}")
            return False

    async def clear(self) -> None:
        """清空缓存"""
        try:
            pattern = self._make_key("*")
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis缓存清空失败: {e}")

    async def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计

        Returns:
            dict: 缓存统计信息
        """
        try:
            pattern = self._make_key("*")
            keys = await self._redis.keys(pattern)
            return {
                "type": "redis",
                "size": len(keys),
            }
        except Exception as e:
            logger.error(f"Redis缓存统计获取失败: {e}")
            return {"type": "redis", "size": 0}


class MultiLevelCache(CacheStrategy):
    """
    多级缓存策略

    L1: 内存缓存（快速访问）
    L2: Redis缓存（持久化）
    """

    def __init__(
        self,
        l1_cache: MemoryCache | None = None,
        l2_cache: RedisCache | None = None,
    ):
        """
        初始化多级缓存

        Args:
            l1_cache: 一级缓存（内存）
            l2_cache: 二级缓存（Redis）
        """
        self._l1 = l1_cache or MemoryCache()
        self._l2 = l2_cache

    async def get(self, key: str) -> QueryResult | None:
        """
        获取缓存（先L1后L2）

        Args:
            key: 缓存键

        Returns:
            QueryResult | None: 缓存的结果
        """
        # 先查L1
        result = await self._l1.get(key)
        if result:
            return result

        # 再查L2
        if self._l2:
            result = await self._l2.get(key)
            if result:
                # 回填L1
                await self._l1.set(key, result)
                return result

        return None

    async def set(
        self,
        key: str,
        value: QueryResult,
        ttl: Optional[int] = None,
    ) -> None:
        """
        设置缓存（同时写入L1和L2）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        await self._l1.set(key, value, ttl)
        if self._l2:
            await self._l2.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """
        删除缓存（同时从L1和L2删除）

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        l1_deleted = await self._l1.delete(key)
        l2_deleted = True
        if self._l2:
            l2_deleted = await self._l2.delete(key)
        return l1_deleted or l2_deleted

    async def clear(self) -> None:
        """清空所有缓存"""
        await self._l1.clear()
        if self._l2:
            await self._l2.clear()

    async def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计

        Returns:
            dict: 缓存统计信息
        """
        stats = {
            "type": "multi_level",
            "l1": await self._l1.get_stats(),
        }
        if self._l2:
            stats["l2"] = await self._l2.get_stats()
        return stats


__all__ = [
    "MemoryCache",
    "RedisCache",
    "MultiLevelCache",
]
