#!/usr/bin/env python3
from __future__ import annotations
"""
缓存和性能优化工具

提供LRU缓存、批量操作和性能监控功能。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import hashlib
import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Python 3.9 兼容：使用typing_extensions
try:
    from typing_extensions import ParamSpec
except ImportError:
    # 如果没有typing_extensions，定义一个简单的替代
    class _ParamSpec:
        def __init__(self, name):
            self.name = name

    ParamSpec = _ParamSpec  # type: ignore

P = ParamSpec('P')
T = TypeVar('T')


class LRUCache:
    """
    线程安全的LRU缓存

    用于缓存频繁访问的数据，自动淘汰最少使用的项。
    """

    def __init__(self, max_size: int = 128, ttl: Optional[float] = None):
        """
        初始化LRU缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 生存时间（秒），None表示永不过期
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.timestamps: dict[str, float] = {}
        self.hits = 0
        self.misses = 0

    def _is_expired(self, key: str) -> bool:
        """检查条目是否过期"""
        if self.ttl is None:
            return False
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > self.ttl

    def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        if key not in self.cache:
            self.misses += 1
            return None

        if self._is_expired(key):
            del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
            self.misses += 1
            return None

        # 移到末尾（标记为最近使用）
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]

    def put(self, key: str, value: Any) -> None:
        """
        存储缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果已存在，先删除（后面会重新添加并移到末尾）
        if key in self.cache:
            del self.cache[key]

        # 如果缓存已满，删除最旧的项
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.timestamps:
                del self.timestamps[oldest_key]

        # 添加新条目
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def invalidate(self, key: str) -> bool:
        """
        使指定缓存失效

        Args:
            key: 缓存键

        Returns:
            是否找到并删除了缓存
        """
        if key in self.cache:
            del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "ttl": self.ttl
        }


def cached(
    cache_instance: LRUCache | None = None,
    key_func: Callable[..., str] | None = None,
    ttl: Optional[float] = None
):
    """
    函数结果缓存装饰器

    Args:
        cache_instance: 自定义缓存实例
        key_func: 自定义缓存键生成函数
        ttl: 生存时间（秒）

    Examples:
        >>> cache = LRUCache(max_size=256, ttl=300)
        >>>
        >>> @cached(cache_instance=cache)
        >>> def expensive_function(x, y):
        ...     return x + y
    """
    if cache_instance is None:
        cache_instance = LRUCache(max_size=128, ttl=ttl)

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数的hash
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_str = "|".join(key_parts)
                cache_key = hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()

            # 尝试从缓存获取
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_instance.put(cache_key, result)

            return result

        # 添加缓存访问方法
        wrapper.cache = cache_instance
        wrapper.cache_clear = cache_instance.clear
        wrapper.cache_info = cache_instance.get_stats

        return wrapper

    return decorator


def async_cached(
    cache_instance: LRUCache | None = None,
    key_func: Callable[..., str] | None = None,
    ttl: Optional[float] = None
):
    """
    异步函数结果缓存装饰器

    Args:
        cache_instance: 自定义缓存实例
        key_func: 自定义缓存键生成函数
        ttl: 生存时间（秒）

    Examples:
        >>> cache = LRUCache(max_size=256, ttl=300)
        >>>
        >>> @async_cached(cache_instance=cache)
        >>> async def expensive_function_async(x, y):
        ...     return x + y
    """
    if cache_instance is None:
        cache_instance = LRUCache(max_size=128, ttl=ttl)

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数的hash
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_str = "|".join(key_parts)
                cache_key = hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()

            # 尝试从缓存获取
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache_instance.put(cache_key, result)

            return result

        # 添加缓存访问方法
        wrapper.cache = cache_instance
        wrapper.cache_clear = cache_instance.clear
        wrapper.cache_info = cache_instance.get_stats

        return wrapper

    return decorator


class BatchProcessor:
    """
    批量处理器

    将多个操作批量执行，提升性能。
    """

    def __init__(
        self,
        batch_size: int = 10,
        timeout: float = 1.0,
        max_wait_time: float = 5.0
    ):
        """
        初始化批量处理器

        Args:
            batch_size: 批量大小
            timeout: 最大等待时间（秒）
            max_wait_time: 最大总等待时间（秒）
        """
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_wait_time = max_wait_time
        self.queue: list[Any] = []
        self.last_flush = time.time()

    async def add(self, item: Any, processor: Callable[[list[Any]], Any]) -> Any | None:
        """
        添加项目到批量队列

        Args:
            item: 要添加的项目
            processor: 批量处理函数

        Returns:
            处理结果（如果立即执行），否则返回None
        """
        self.queue.append(item)

        # 检查是否应该执行批量处理
        should_flush = (
            len(self.queue) >= self.batch_size or
            time.time() - self.last_flush > self.timeout or
            time.time() - self.last_flush > self.max_wait_time
        )

        if should_flush:
            return await self.flush(processor)

        return None

    async def flush(self, processor: Callable[[list[Any]], Any]) -> Any:
        """
        执行批量处理

        Args:
            processor: 批量处理函数

        Returns:
            处理结果
        """
        if not self.queue:
            return None

        batch = self.queue.copy()
        self.queue.clear()
        self.last_flush = time.time()

        return await processor(batch)


class PerformanceMonitor:
    """
    性能监控器

    记录函数执行时间和调用次数。
    """

    def __init__(self):
        """初始化性能监控器"""
        self.metrics: dict[str, dict[str, Any]] = {}

    def record(
        self,
        func_name: str,
        execution_time: float,
        success: bool = True
    ) -> None:
        """
        记录函数执行

        Args:
            func_name: 函数名
            execution_time: 执行时间（秒）
            success: 是否成功
        """
        if func_name not in self.metrics:
            self.metrics[func_name] = {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
                "last_called": None
            }

        metrics = self.metrics[func_name]
        metrics["calls"] += 1
        metrics["total_time"] += execution_time
        metrics["min_time"] = min(metrics["min_time"], execution_time)
        metrics["max_time"] = max(metrics["max_time"], execution_time)
        metrics["last_called"] = datetime.now()

        if success:
            metrics["successes"] += 1
        else:
            metrics["failures"] += 1

    def get_stats(self, func_name: str) -> Optional[dict[str, Any]]:
        """
        获取函数统计信息

        Args:
            func_name: 函数名

        Returns:
            统计信息字典
        """
        if func_name not in self.metrics:
            return None

        metrics = self.metrics[func_name].copy()
        if metrics["calls"] > 0:
            metrics["avg_time"] = metrics["total_time"] / metrics["calls"]
            metrics["success_rate"] = metrics["successes"] / metrics["calls"]
        else:
            metrics["avg_time"] = 0.0
            metrics["success_rate"] = 0.0

        return metrics

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """获取所有函数的统计信息"""
        return {
            name: self.get_stats(name)
            for name in self.metrics
        }


# 全局性能监控器实例
_global_monitor = PerformanceMonitor()


def monitor_performance(func: Callable[P, T]) -> Callable[P, T]:
    """
    性能监控装饰器

    记录函数的执行时间和成功率。

    Args:
        func: 要监控的函数

    Returns:
        包装后的函数
    """
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        success = False

        try:
            result = func(*args, **kwargs)
            success = True
            return result
        finally:
            execution_time = time.time() - start_time
            _global_monitor.record(func.__name__, execution_time, success)

    wrapper.performance_stats = lambda: _global_monitor.get_stats(func.__name__)
    return wrapper


def async_monitor_performance(func: Callable[P, Any]) -> Callable[P, Any]:
    """
    异步函数性能监控装饰器

    记录函数的执行时间和成功率。

    Args:
        func: 要监控的异步函数

    Returns:
        包装后的异步函数
    """
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
        start_time = time.time()
        success = False

        try:
            result = await func(*args, **kwargs)
            success = True
            return result
        finally:
            execution_time = time.time() - start_time
            _global_monitor.record(func.__name__, execution_time, success)

    wrapper.performance_stats = lambda: _global_monitor.get_stats(func.__name__)
    return wrapper


__all__ = [
    'BatchProcessor',
    'LRUCache',
    'PerformanceMonitor',
    'async_cached',
    'async_monitor_performance',
    'cached',
    'monitor_performance'
]
