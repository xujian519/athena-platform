#!/usr/bin/env python3
from __future__ import annotations
"""
步骤执行结果缓存系统
Step Result Cache System

缓存步骤执行结果，避免重复执行，提升性能。

特性:
1. 基于 Redis 的缓存层
2. LRU 淘汰策略
3. 缓存过期时间
4. 缓存命中统计
5. 支持缓存预热

Author: Athena Team
Version: 1.0.0
Date: 2026-02-25
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ========== 缓存配置 ==========


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl: int = 3600  # 默认过期时间(秒)
    max_size: int = 10000  # 最大缓存条目数
    use_redis: bool = True  # 是否使用 Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    fallback_to_memory: bool = True  # Redis 不可用时回退到内存缓存


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: int = 3600
    size: int = 0

    @property
    def is_expired(self) -> bool:
        """是否过期"""
        return time.time() - self.created_at > self.ttl

    @property
    def age(self) -> float:
        """缓存年龄(秒)"""
        return time.time() - self.created_at


# ========== 缓存统计 ==========


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "hit_rate": f"{self.hit_rate:.2%}",
            "total_requests": self.hits + self.misses,
        }


# ========== 内存缓存实现 ==========


class MemoryCache:
    """内存缓存实现（Redis 不可用时使用）"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self._lock = asyncio.Lock()

        logger.info("💾 内存缓存初始化")

    async def get(self, key: str) -> Any | None:
        """获取缓存值"""
        async with self._lock:
            entry = self.cache.get(key)

            if entry is None:
                self.stats.misses += 1
                return None

            if entry.is_expired:
                await self.delete(key)
                self.stats.misses += 1
                return None

            entry.accessed_at = time.time()
            entry.access_count += 1
            self.stats.hits += 1

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """设置缓存值"""
        async with self._lock:
            ttl = ttl or self.config.ttl

            # 计算值大小
            try:
                if isinstance(value, (str, bytes)):
                    size = len(value)
                else:
                    size = len(pickle.dumps(value))
            except Exception:
                size = 1024  # 估算

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                access_count=0,
                ttl=ttl,
                size=size,
            )

            # 检查是否超过最大容量
            if len(self.cache) >= self.config.max_size:
                await self._evict_lru()

            self.cache[key] = entry
            self.stats.sets += 1

            return True

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.deletes += 1
                return True
            return False

    async def clear(self) -> bool:
        """清空缓存"""
        async with self._lock:
            self.cache.clear()
            return True

    async def _evict_lru(self) -> None:
        """淘汰最少使用的缓存"""
        if not self.cache:
            return

        # 找到最少使用的条目
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (
                self.cache[k].accessed_at,
                self.cache[k].access_count,
            ),
        )

        del self.cache[lru_key]
        self.stats.evictions += 1

        logger.debug(f"🗑️ 淘汰缓存: {lru_key}")

    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        return self.stats


# ========== Redis 缓存实现 ==========


class RedisCache:
    """Redis 缓存实现"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.stats = CacheStats()
        self._client = None
        self._enabled = False

        logger.info("💾 Redis 缓存初始化")

    async def _get_client(self):
        """获取 Redis 客户端"""
        if self._client is not None:
            return self._client

        try:
            import redis.asyncio as redis

            self._client = await redis.from_url(
                f"redis://{self.config.redis_host}:{self.config.redis_port}/{self.config.redis_db}",
                password=self.config.redis_password,
                encoding="utf-8",
                decode_responses=False,  # 保持二进制模式以支持 pickle
            )

            # 测试连接
            await self._client.ping()

            self._enabled = True
            logger.info("✅ Redis 连接成功")

        except Exception as e:
            logger.warning(f"⚠️ Redis 连接失败: {e}")
            self._enabled = False
            self._client = None

        return self._client

    async def get(self, key: str) -> Any | None:
        """获取缓存值"""
        if not self._enabled:
            return None

        try:
            client = await self._get_client()
            if not client:
                return None

            data = await client.get(key)

            if data is None:
                self.stats.misses += 1
                return None

            # 反序列化
            try:
                value = pickle.loads(data)
            except Exception:
                try:
                    value = json.loads(data)
                except Exception:
                    value = data

            self.stats.hits += 1
            return value

        except Exception as e:
            logger.error(f"❌ Redis GET 失败: {e}")
            self.stats.misses += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """设置缓存值"""
        if not self._enabled:
            return False

        try:
            client = await self._get_client()
            if not client:
                return False

            # 序列化
            try:
                data = pickle.dumps(value)
            except Exception:
                data = json.dumps(value).encode()

            ttl = ttl or self.config.ttl

            await client.setex(key, ttl, data)
            self.stats.sets += 1

            return True

        except Exception as e:
            logger.error(f"❌ Redis SET 失败: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self._enabled:
            return False

        try:
            client = await self._get_client()
            if not client:
                return False

            result = await client.delete(key)

            if result:
                self.stats.deletes += 1

            return bool(result)

        except Exception as e:
            logger.error(f"❌ Redis DELETE 失败: {e}")
            return False

    async def clear(self) -> bool:
        """清空缓存"""
        if not self._enabled:
            return False

        try:
            client = await self._get_client()
            if not client:
                return False

            await client.flushdb()
            return True

        except Exception as e:
            logger.error(f"❌ Redis CLEAR 失败: {e}")
            return False

    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        return self.stats


# ========== 统一缓存接口 ==========


class StepResultCache:
    """步骤执行结果缓存"""

    def __init__(self, config: CacheConfig | None = None):
        self.config = config or CacheConfig()
        self.redis_cache = RedisCache(self.config)
        self.memory_cache = MemoryCache(self.config)

        logger.info("💾 步骤结果缓存初始化完成")

    def _generate_cache_key(
        self,
        agent: str,
        action: str,
        parameters: dict[str, Any],
    ) -> str:
        """生成缓存键"""
        # 规范化参数
        normalized_params = json.dumps(parameters, sort_keys=True)

        # 生成哈希
        key_content = f"{agent}:{action}:{normalized_params}"
        key_hash = hashlib.sha256(key_content.encode()).hexdigest()

        return f"step_result:{key_hash}"

    async def get(
        self,
        agent: str,
        action: str,
        parameters: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """获取缓存的步骤结果"""
        if not self.config.enabled:
            return None

        key = self._generate_cache_key(agent, action, parameters)

        # 优先使用 Redis
        if self.config.use_redis:
            value = await self.redis_cache.get(key)
            if value is not None:
                return value

        # 回退到内存缓存
        if self.config.fallback_to_memory:
            value = await self.memory_cache.get(key)
            if value is not None:
                return value

        return None

    async def set(
        self,
        agent: str,
        action: str,
        parameters: dict[str, Any],
        result: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """缓存步骤结果"""
        if not self.config.enabled:
            return False

        key = self._generate_cache_key(agent, action, parameters)

        success = False

        # 尝试 Redis
        if self.config.use_redis:
            success = await self.redis_cache.set(key, result, ttl)

        # 回退到内存缓存
        if not success and self.config.fallback_to_memory:
            success = await self.memory_cache.set(key, result, ttl)

        return success

    async def delete(
        self,
        agent: str,
        action: str,
        parameters: dict[str, Any],
    ) -> bool:
        """删除缓存的步骤结果"""
        if not self.config.enabled:
            return False

        key = self._generate_cache_key(agent, action, parameters)

        if self.config.use_redis:
            await self.redis_cache.delete(key)

        if self.config.fallback_to_memory:
            await self.memory_cache.delete(key)

        return True

    async def clear(self) -> bool:
        """清空所有缓存"""
        if self.config.use_redis:
            await self.redis_cache.clear()

        if self.config.fallback_to_memory:
            await self.memory_cache.clear()

        return True

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        stats = {
            "redis": self.redis_cache.get_stats().to_dict() if self.config.use_redis else {},
            "memory": self.memory_cache.get_stats().to_dict() if self.config.fallback_to_memory else {},
            "config": {
                "enabled": self.config.enabled,
                "use_redis": self.config.use_redis,
                "fallback_to_memory": self.config.fallback_to_memory,
                "ttl": self.config.ttl,
                "max_size": self.config.max_size,
            },
        }

        return stats


# ========== 导出 ==========


__all__ = [
    "CacheConfig",
    "CacheEntry",
    "CacheStats",
    "StepResultCache",
]
