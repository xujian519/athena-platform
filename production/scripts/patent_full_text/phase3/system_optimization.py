#!/usr/bin/env python3
"""
系统优化模块
System Optimization Module

提供缓存、批处理、并发控制、错误处理等优化功能

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import json
import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""
    NO_CACHE = "no_cache"
    MEMORY = "modules/modules/memory/modules/memory/modules/memory/memory"
    REDIS = "redis"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    ttl: int = 3600  # 秒
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > self.ttl


class MemoryCache:
    """内存缓存"""

    def __init__(self, max_size: int = 10000):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存条目数
        """
        self.cache: dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        with self.lock:
            entry = self.cache.get(key)
            if entry and not entry.is_expired():
                return entry.value
            elif entry:
                # 过期删除
                del self.cache[key]
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> Any:
        """设置缓存"""
        with self.lock:
            # LRU淘汰
            if len(self.cache) >= self.max_size:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].created_at
                )
                del self.cache[oldest_key]

            self.cache[key] = CacheEntry(key=key, value=value, ttl=ttl)

    def clear(self) -> Any:
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "usage": f"{len(self.cache)}/{self.max_size}"
            }


class CacheManager:
    """缓存管理器"""

    def __init__(self, enable_memory: bool = True, enable_redis: bool = False):
        """
        初始化缓存管理器

        Args:
            enable_memory: 启用内存缓存
            enable_redis: 启用Redis缓存
        """
        self.enable_memory = enable_memory
        self.enable_redis = enable_redis

        self.memory_cache = MemoryCache() if enable_memory else None
        self.redis_client = None

    def get_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_str = json.dumps([args, kwargs], sort_keys=True)
        return short_hash(key_str.encode())

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        if self.enable_memory and self.memory_cache:
            value = self.memory_cache.get(key)
            if value is not None:
                return value

        if self.enable_redis and self.redis_client:
            # Redis缓存实现
            pass

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> Any:
        """设置缓存"""
        if self.enable_memory and self.memory_cache:
            self.memory_cache.set(key, value, ttl)

        if self.enable_redis and self.redis_client:
            # Redis缓存实现
            pass

    def clear(self) -> Any:
        """清空所有缓存"""
        if self.memory_cache:
            self.memory_cache.clear()


# 缓存装饰器
def cached(
    cache_manager: CacheManager,
    ttl: int = 3600,
    key_func: Callable | None = None
):
    """
    缓存装饰器

    Args:
        cache_manager: 缓存管理器
        ttl: 过期时间
        key_func: 自定义键生成函数
    """
    def decorator(func) -> None:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager.get_cache_key(
                    func.__name__,
                    args,
                    kwargs
                )

            # 尝试获取缓存
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 设置缓存
            cache_manager.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


@dataclass
class BatchResult:
    """批处理结果"""
    total_count: int
    success_count: int
    failed_count: int
    results: list[Any] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    total_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count


class BatchProcessor:
    """批处理器"""

    def __init__(
        self,
        batch_size: int = 10,
        max_workers: int = 4,
        use_threading: bool = True
    ):
        """
        初始化批处理器

        Args:
            batch_size: 批次大小
            max_workers: 最大并发数
            use_threading: 是否使用线程池
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.use_threading = use_threading

    def process_batch(
        self,
        items: list[Any],
        process_func: Callable,
        show_progress: bool = False
    ) -> BatchResult:
        """
        批量处理

        Args:
            items: 待处理项列表
            process_func: 处理函数
            show_progress: 显示进度

        Returns:
            BatchResult
        """
        start_time = time.time()

        result = BatchResult(total_count=len(items))

        if self.use_threading and self.max_workers > 1:
            # 多线程处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交任务
                future_to_item = {
                    executor.submit(process_func, item): item
                    for item in items
                }

                # 收集结果
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        r = future.result(timeout=300)
                        result.results.append(r)
                        result.success_count += 1
                    except Exception as e:
                        result.failed_count += 1
                        result.errors.append({
                            "item": str(item)[:100],
                            "error": str(e)
                        })

                    if show_progress and (result.success_count + result.failed_count) % 10 == 0:
                        logger.info(
                            f"进度: {result.success_count + result.failed_count}/{len(items)} "
                            f"({result.success_count}成功, {result.failed_count}失败)"
                        )
        else:
            # 单线程处理
            for i, item in enumerate(items):
                try:
                    r = process_func(item)
                    result.results.append(r)
                    result.success_count += 1
                except Exception as e:
                    result.failed_count += 1
                    result.errors.append({
                        "item": str(item)[:100],
                        "error": str(e)
                    })

                if show_progress and (i + 1) % 10 == 0:
                    logger.info(f"进度: {i + 1}/{len(items)}")

        result.total_time = time.time() - start_time

        logger.info(
            f"✅ 批处理完成: {result.success_count}/{result.total_count}成功, "
            f"{result.failed_count}失败, 耗时{result.total_time:.2f}秒"
        )

        return result


class RetryHandler:
    """重试处理器"""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """
        初始化重试处理器

        Args:
            max_retries: 最大重试次数
            backoff_factor: 退避因子
            exceptions: 需要重试的异常类型
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        show_progress: bool = False,
        **kwargs
    ):
        """
        执行带重试的函数

        Args:
            func: 函数
            show_progress: 显示进度

        Returns:
            函数结果
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0 and show_progress:
                    logger.info(f"🔄 重试 {attempt}/{self.max_retries}...")

                return func(*args, **kwargs)

            except self.exceptions as e:
                last_exception = e

                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"⚠️  执行失败，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 重试{self.max_retries}次后仍失败")

        raise last_exception


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        """初始化性能监控器"""
        self.metrics: dict[str, list[float]] = {}
        self.lock = threading.RLock()

    def record(self, name: str, value: float) -> Any:
        """记录性能指标"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(value)

    def get_stats(self, name: str) -> dict[str, float]:
        """获取统计信息"""
        with self.lock:
            if name not in self.metrics or not self.metrics[name]:
                return {}

            values = self.metrics[name]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "total": sum(values)
            }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """获取所有统计"""
        with self.lock:
            return {
                name: self.get_stats(name)
                for name in self.metrics
            }

    def reset(self) -> Any:
        """重置指标"""
        with self.lock:
            self.metrics.clear()


# 全局性能监控器实例
_global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return _global_monitor


def monitor_performance(metric_name: str) -> Any:
    """
    性能监控装饰器

    Args:
        metric_name: 指标名称
    """
    def decorator(func) -> None:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                _global_monitor.record(metric_name, elapsed)
        return wrapper
    return decorator


# ========== 便捷函数 ==========

def create_cache_manager(**kwargs) -> CacheManager:
    """创建缓存管理器"""
    return CacheManager(**kwargs)


def create_batch_processor(**kwargs) -> BatchProcessor:
    """创建批处理器"""
    return BatchProcessor(**kwargs)


def create_retry_handler(**kwargs) -> RetryHandler:
    """创建重试处理器"""
    return RetryHandler(**kwargs)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("系统优化模块示例")
    print("=" * 70)

    # 1. 缓存管理器
    print("\n📦 缓存管理器:")
    cache_manager = create_cache_manager()

    key = cache_manager.get_cache_key("test", {"param": 1})
    cache_manager.set(key, "cached_value", ttl=60)

    cached = cache_manager.get(key)
    print(f"  缓存命中: {cached == 'cached_value'}")

    stats = cache_manager.memory_cache.get_stats()
    print(f"  缓存统计: {stats}")

    # 2. 批处理器
    print("\n⚙️  批处理器:")

    def sample_task(x) -> None:
        time.sleep(0.01)
        return x * 2

    batch_processor = create_batch_processor(
        batch_size=10,
        max_workers=2,
        use_threading=True
    )

    items = list(range(20))
    batch_result = batch_processor.process_batch(
        items,
        sample_task,
        show_progress=True
    )

    print(f"  处理结果: {batch_result.success_count}/{batch_result.total_count}成功")
    print(f"  成功率: {batch_result.success_rate:.1%}")

    # 3. 性能监控
    print("\n📊 性能监控:")
    monitor = get_performance_monitor()

    @monitor_performance("test_operation")
    def test_operation() -> Any:
        time.sleep(0.1)
        return "done"

    test_operation()
    test_operation()

    stats = monitor.get_stats("test_operation")
    print(f"  操作统计: {stats}")


if __name__ == "__main__":
    main()
