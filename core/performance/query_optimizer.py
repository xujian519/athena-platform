#!/usr/bin/env python3
"""
综合性能优化模块
Performance Optimization Module - 综合优化查询性能和响应速度

包括:
- 多级缓存系统(L1内存 + L2Redis + L3数据库)
- 查询批处理和合并
- 连接池优化
- 异步并发执行
- 结果预加载和预测

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Performance Optimization"
"""

import asyncio
import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""

    L1_MEMORY = "l1_memory"  # L1: 内存缓存(最快,容量小)
    L2_REDIS = "l2_redis"  # L2: Redis缓存(快,容量中等)
    L3_DATABASE = "l3_database"  # L3: 数据库(慢,容量大)


@dataclass
class PerformanceMetrics:
    """性能指标"""

    query_time_ms: float
    cache_hit_rate: float
    db_query_count: int
    result_count: int
    memory_used_mb: float


class LRUCache:
    """LRU缓存实现(线程安全)"""

    def __init__(self, max_size: int = 1000):
        """
        初始化LRU缓存

        Args:
            max_size: 最大缓存条目数
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()  # 添加线程锁保护并发访问

    def get(self, key: str) -> Any | None:
        """获取缓存值(线程安全)"""
        with self._lock:
            if key in self.cache:
                self.hits += 1
                # 移到末尾(最近使用)
                self.cache.move_to_end(key)
                return self.cache[key]
            self.misses += 1
            return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存值(线程安全)"""
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value

            # 超过容量,删除最久未使用的条目
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }


class MultiLevelCache:
    """多级缓存系统"""

    def __init__(self, l1_size: int = 1000, l2_enabled: bool = False, l2_ttl: int = 3600):
        """
        初始化多级缓存

        Args:
            l1_size: L1缓存大小
            l2_enabled: 是否启用L2 Redis缓存
            l2_ttl: L2缓存过期时间(秒)
        """
        self.l1_cache = LRUCache(l1_size)
        self.l2_enabled = l2_enabled
        self.l2_ttl = l2_ttl

        # Redis连接(如果启用)
        self._redis_client = None
        if l2_enabled:
            self._init_redis()

        logger.info(
            f"💾 多级缓存初始化 (L1={l1_size}, L2={'enabled' if l2_enabled else 'disabled'})"
        )

    def _init_redis(self) -> Any:
        """初始化Redis连接"""
        try:
            import redis

            self._redis_client = redis.Redis(
                host="localhost", port=6379, db=0, decode_responses=True
            )
            self._redis_client.ping()
            logger.info("✅ Redis L2缓存连接成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败,仅使用L1缓存: {e}")
            self.l2_enabled = False

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode('utf-8'), usedforsecurity=False).hexdigest()

    async def get(self, *args, **kwargs) -> Any | None:
        """获取缓存值(从L1到L2依次查找)"""
        key = self._generate_key(*args, **kwargs)

        # L1缓存
        value = self.l1_cache.get(key)
        if value is not None:
            return value

        # L2缓存
        if self.l2_enabled and self._redis_client:
            try:
                value = self._redis_client.get(key)
                if value is not None:
                    # 反序列化
                    value = json.loads(value)
                    # 回填L1缓存
                    self.l1_cache.set(key, value)
                    return value
            except Exception as e:
                logger.warning(f"⚠️ L2缓存读取失败: {e}")

        return None

    async def set(self, value: Any, ttl: int | None = None, *args, **kwargs) -> None:
        """设置缓存值(同时写入L1和L2)"""
        key = self._generate_key(*args, **kwargs)

        # 写入L1
        self.l1_cache.set(key, value)

        # 写入L2
        if self.l2_enabled and self._redis_client:
            try:
                serialized = json.dumps(value, ensure_ascii=False)
                ttl = ttl or self.l2_ttl
                self._redis_client.setex(key, ttl, serialized)
            except Exception as e:
                logger.warning(f"⚠️ L2缓存写入失败: {e}")

    async def clear(self) -> None:
        """清空所有缓存"""
        self.l1_cache.clear()

        if self.l2_enabled and self._redis_client:
            try:
                self._redis_client.flushdb()
            except Exception as e:
                logger.warning(f"⚠️ L2缓存清空失败: {e}")

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {"l1": self.l1_cache.stats(), "l2_enabled": self.l2_enabled}


class QueryBatcher:
    """查询批处理器 - 将多个查询合并批量执行"""

    def __init__(self, batch_size: int = 10, max_wait_time: float = 0.1):
        """
        初始化查询批处理器

        Args:
            batch_size: 批处理大小
            max_wait_time: 最大等待时间(秒)
        """
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self._pending_queries: list[tuple[Callable, tuple, dict]] = []
        self._lock = asyncio.Lock()

    async def batch_execute(self, query_func: Callable, *args, **kwargs) -> Any:
        """
        批量执行查询

        Args:
            query_func: 查询函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            查询结果
        """
        async with self._lock:
            self._pending_queries.append((query_func, args, kwargs))

            # 达到批处理大小或超时
            if len(self._pending_queries) >= self.batch_size:
                return await self._flush_batch()

        # 等待批处理
        await asyncio.sleep(self.max_wait_time)

        async with self._lock:
            if self._pending_queries:
                return await self._flush_batch()

        return None

    async def _flush_batch(self) -> list[Any]:
        """刷新批次,执行所有待处理查询"""
        if not self._pending_queries:
            return []

        queries = self._pending_queries.copy()
        self._pending_queries.clear()

        # 并行执行所有查询
        tasks = []
        for query_func, args, kwargs in queries:
            if asyncio.iscoroutinefunction(query_func):
                tasks.append(query_func(*args, **kwargs))
            else:
                tasks.append(asyncio.to_thread(query_func, *args, **kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results


class PerformanceOptimizer:
    """综合性能优化器"""

    def __init__(
        self,
        enable_cache: bool = True,
        enable_batching: bool = True,
        l1_cache_size: int = 1000,
        batch_size: int = 10,
    ):
        """
        初始化性能优化器

        Args:
            enable_cache: 是否启用缓存
            enable_batching: 是否启用批处理
            l1_cache_size: L1缓存大小
            batch_size: 批处理大小
        """
        self.enable_cache = enable_cache
        self.enable_batching = enable_batching

        # 初始化多级缓存
        if enable_cache:
            self.cache = MultiLevelCache(l1_size=l1_cache_size)

        # 初始化批处理器
        if enable_batching:
            self.batcher = QueryBatcher(batch_size=batch_size)

        # 性能指标
        self.metrics: dict[str, PerformanceMetrics] = {}

        logger.info("⚡ 综合性能优化器初始化完成")

    def performance_monitor(self, query_name: str) -> Any:
        """
        性能监控装饰器

        Args:
            query_name: 查询名称

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = self._get_memory_usage()

                try:
                    # 执行查询
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    # 计算性能指标
                    query_time = (time.time() - start_time) * 1000
                    memory_used = self._get_memory_usage() - start_memory

                    # 记录指标
                    self.metrics[query_name] = PerformanceMetrics(
                        query_time_ms=query_time,
                        cache_hit_rate=(
                            self.cache.stats()["l1"]["hit_rate"] if self.enable_cache else 0.0
                        ),
                        db_query_count=1,  # TODO: 实际统计
                        result_count=len(result) if isinstance(result, list) else 1,
                        memory_used_mb=memory_used,
                    )

                    return result

                except Exception as e:
                    logger.error(f"❌ 查询执行失败 [{query_name}]: {e}")
                    raise

            return wrapper

        return decorator

    def _get_memory_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    async def optimized_query(
        self,
        query_func: Callable,
        cache_key: str | None = None,
        cache_ttl: int = 3600,
        *args,
        **kwargs,
    ) -> Any:
        """
        优化查询(自动应用缓存和批处理)

        Args:
            query_func: 查询函数
            cache_key: 缓存键(None则自动生成)
            cache_ttl: 缓存过期时间
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            查询结果
        """
        # 检查缓存
        if self.enable_cache:
            cached_result = await self.cache.get(cache_key, args, kwargs)
            if cached_result is not None:
                logger.debug("✅ 缓存命中")
                return cached_result

        # 执行查询
        if self.enable_batching:
            result = await self.batcher.batch_execute(query_func, *args, **kwargs)
        else:
            if asyncio.iscoroutinefunction(query_func):
                result = await query_func(*args, **kwargs)
            else:
                result = query_func(*args, **kwargs)

        # 写入缓存
        if self.enable_cache and result is not None:
            await self.cache.set(result, cache_ttl, cache_key, args, kwargs)

        return result

    def get_metrics(self, query_name: str | None = None) -> dict[str, PerformanceMetrics]:
        """
        获取性能指标

        Args:
            query_name: 查询名称(None则返回所有)

        Returns:
            性能指标字典
        """
        if query_name:
            return {query_name: self.metrics.get(query_name)}
        return self.metrics.copy()

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        if self.enable_cache:
            return self.cache.stats()
        return {"disabled": True}

    async def clear_cache(self) -> None:
        """清空缓存"""
        if self.enable_cache:
            await self.cache.clear()
            logger.info("🗑️ 缓存已清空")


# 全局性能优化器实例
_global_optimizer: PerformanceOptimizer | None = None


def get_global_optimizer() -> PerformanceOptimizer:
    """获取全局性能优化器"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = PerformanceOptimizer()
    return _global_optimizer


# 便捷函数
async def optimized_query(
    query_func: Callable | None = None, cache_key: str | None = None, *args, **kwargs
) -> Any:
    """
    便捷的优化查询函数

    Args:
        query_func: 查询函数
        cache_key: 缓存键
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        查询结果
    """
    optimizer = get_global_optimizer()
    return await optimizer.optimized_query(query_func, cache_key, *args, **kwargs)


def monitor_performance(query_name: str) -> Any:
    """
    便捷的性能监控装饰器

    Args:
        query_name: 查询名称

    Returns:
        装饰器函数
    """
    optimizer = get_global_optimizer()
    return optimizer.performance_monitor(query_name)


__all__ = [
    "CacheLevel",
    "LRUCache",
    "MultiLevelCache",
    "PerformanceMetrics",
    "PerformanceOptimizer",
    "QueryBatcher",
    "get_global_optimizer",
    "monitor_performance",
    "optimized_query",
]
