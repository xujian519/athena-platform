#!/usr/bin/env python3
"""
增强缓存管理器
Advanced Cache Manager

提供多级缓存、TTL管理、缓存预热等功能
"""

from __future__ import annotations
import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# 缓存配置
# =============================================================================


@dataclass
class CacheConfig:
    """缓存配置"""

    max_size: int = 1000  # 最大缓存条目数
    default_ttl: int = 3600  # 默认TTL(秒)
    enable_stats: bool = True  # 启用统计
    cleanup_interval: int = 300  # 清理间隔(秒)


# =============================================================================
# 缓存条目
# =============================================================================


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: int | None = None
    hits: int = 0
    misses: int = 0

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl

    @property
    def age(self) -> float:
        """获取缓存年龄(秒)"""
        return time.time() - self.created_at


# =============================================================================
# LRU缓存实现
# =============================================================================


class LRUCache:
    """
    LRU(最近最少使用)缓存实现

    提供高效的缓存管理,支持TTL、LRU淘汰和统计功能

    Examples:
        >>> cache = LRUCache(max_size=1000, default_ttl=3600)
        >>>
        >>> # 设置缓存
        >>> cache.set("key1", "value1", ttl=600)
        >>>
        >>> # 获取缓存
        >>> value = cache.get("key1")
        >>>
        >>> # 使用装饰器
        >>> @cache.cached(ttl=300)
        >>> def expensive_function(param):
        >>>     return compute(param)
    """

    def __init__(
        self, max_size: int = 1000, default_ttl: int = 3600, enable_stats: bool = True
    ):
        """
        初始化LRU缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL(秒)
            enable_stats: 是否启用统计
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats

        # 使用OrderedDict实现LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # 统计信息
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}
        self._lock = threading.RLock()

        logger.info(f"LRU缓存初始化: max_size={max_size}, default_ttl={default_ttl}")

    def _evict_if_needed(self) -> Any:
        """如果需要,淘汰最旧的条目"""
        with self._lock:
            while len(self._cache) >= self.max_size:
                # 移除最旧的条目
                oldest_key, _oldest_entry = self._cache.popitem(last=False)
                self._stats["evictions"] += 1
                logger.debug(f"淘汰缓存条目: {oldest_key}")

    def _cleanup_expired(self) -> Any:
        """清理过期条目"""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)

            for key in expired_keys:
                self._cache.pop(key, None)
                self._stats["expirations"] += 1

            if expired_keys:
                logger.debug(f"清理过期条目: {len(expired_keys)} 个")

    def get(self, key: str, default: T = None) -> Any | T:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                if self.enable_stats:
                    self._stats["misses"] += 1
                return default

            if entry.is_expired:
                # 过期,删除并返回默认值
                del self._cache[key]
                if self.enable_stats:
                    self._stats["misses"] += 1
                    self._stats["expirations"] += 1
                return default

            # 命中,更新LRU顺序
            self._cache.move_to_end(key)
            if self.enable_stats:
                self._stats["hits"] += 1
                entry.hits += 1

            return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL(秒),None表示使用默认值
        """
        with self._lock:
            # 确保有空间
            if key not in self._cache:
                self._evict_if_needed()

            # 创建缓存条目
            entry = CacheEntry(
                key=key, value=value, ttl=ttl if ttl is not None else self.default_ttl
            )

            self._cache[key] = entry
            self._cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        """
        删除缓存条目

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> Any:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            if self.enable_stats:
                self._stats["hits"] = 0
                self._stats["misses"] = 0
                self._stats["evictions"] = 0
                self._stats["expirations"] = 0
        logger.info("缓存已清空")

    def cached(self, ttl: int | None = None, key_fn: Callable | None = None) -> Any:
        """
        缓存装饰器

        Args:
            ttl: 缓存TTL
            key_fn: 自定义键生成函数

        Returns:
            装饰器函数

        Examples:
            >>> cache = LRUCache()
            >>>
            >>> @cache.cached(ttl=300)
            >>> def expensive_function(x, y):
            >>>     return x + y
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # 生成缓存键
                if key_fn:
                    cache_key = key_fn(*args, **kwargs)
                else:
                    # 默认键生成:函数名+参数哈希
                    params_str = json.dumps([args, kwargs], sort_keys=True, default=str)
                    params_hash = hashlib.md5(params_str.encode('utf-8'), usedforsecurity=False).hexdigest()
                    cache_key = f"{func.__name__}:{params_hash}"

                # 尝试从缓存获取
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl=ttl)

                return result

            # 添加缓存控制方法
            wrapper.cache = self
            wrapper.cache_key_prefix = func.__name__

            return wrapper

        return decorator

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"],
            }


# =============================================================================
# 多级缓存
# =============================================================================


class MultiLevelCache:
    """
    多级缓存

    提供L1(内存)和L2(Redis)两级缓存

    Examples:
        >>> cache = MultiLevelCache()
        >>>
        >>> # 设置缓存
        >>> cache.set("key", "value", ttl=600)
        >>>
        >>> # 获取缓存(先查L1,再查L2)
        >>> value = cache.get("key")
    """

    def __init__(self, l1_size: int = 1000, l1_ttl: int = 300, l2_enabled: bool = True):
        """
        初始化多级缓存

        Args:
            l1_size: L1缓存大小
            l1_ttl: L1缓存TTL
            l2_enabled: 是否启用L2缓存(Redis)
        """
        # L1缓存(内存)
        self.l1 = LRUCache(max_size=l1_size, default_ttl=l1_ttl)

        # L2缓存(Redis)
        self.l2_enabled = l2_enabled
        self.l2_client = None

        if l2_enabled:
            try:
                import redis

                self.l2_client = redis.Redis(
                    host="localhost", port=6379, db=0, decode_responses=True
                )
                # 测试连接
                self.l2_client.ping()
                logger.info("✅ L2缓存(Redis)已启用")
            except Exception as e:
                logger.warning(f"⚠️ Redis连接失败,仅使用L1缓存: {e}")
                self.l2_enabled = False

    def get(self, key: str) -> Any | None:
        """
        获取缓存值(先L1,后L2)

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        # 先查L1
        value = self.l1.get(key)
        if value is not None:
            return value

        # 再查L2
        if self.l2_enabled and self.l2_client:
            try:
                l2_value = self.l2_client.get(key)
                if l2_value is not None:
                    # 反序列化并回填L1
                    value = json.loads(l2_value)
                    self.l1.set(key, value)
                    return value
            except Exception as e:
                logger.warning(f"L2缓存获取失败: {e}")

        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        设置缓存值(同时设置L1和L2)

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL(秒)
        """
        # 设置L1
        self.l1.set(key, value, ttl=ttl)

        # 设置L2
        if self.l2_enabled and self.l2_client:
            try:
                serialized = json.dumps(value, default=str)
                ttl_seconds = ttl if ttl is not None else 3600
                self.l2_client.setex(key, ttl_seconds, serialized)
            except Exception as e:
                logger.warning(f"L2缓存设置失败: {e}")

    def delete(self, key: str) -> None:
        """
        删除缓存值(同时删除L1和L2)

        Args:
            key: 缓存键
        """
        # 删除L1
        self.l1.delete(key)

        # 删除L2
        if self.l2_enabled and self.l2_client:
            try:
                self.l2_client.delete(key)
            except Exception as e:
                logger.warning(f"L2缓存删除失败: {e}")

    def clear(self) -> None:
        """清空所有缓存"""
        self.l1.clear()

        if self.l2_enabled and self.l2_client:
            try:
                self.l2_client.flushdb()
            except Exception as e:
                logger.warning(f"L2缓存清空失败: {e}")

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        stats = {"l1": self.l1.get_stats(), "l2_enabled": self.l2_enabled}

        if self.l2_enabled and self.l2_client:
            try:
                info = self.l2_client.info("stats")
                stats["l2"] = {
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            except Exception:
                pass

        return stats


# =============================================================================
# 全局缓存实例
# =============================================================================

_global_cache: MultiLevelCache | None = None


def get_cache() -> MultiLevelCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiLevelCache()
    return _global_cache


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "CacheConfig",
    "CacheEntry",
    "LRUCache",
    "MultiLevelCache",
    "get_cache",
]
