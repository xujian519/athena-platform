#!/usr/bin/env python3
# 启用延迟类型注解评估
from __future__ import annotations

"""
感知模块性能优化器
Perception Module Performance Optimizer

提供缓存、批处理、异步处理等性能优化功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import hashlib
import inspect
import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Any, Optional

from . import InputType, PerceptionResult
from .types import CacheConfig

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""

    total_requests: int = 0
    total_processing_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    last_reset_time: datetime = field(default_factory=datetime.now)

    @property
    def average_response_time(self) -> float:
        return self.total_processing_time / max(self.total_requests, 1)

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(total, 1)

    @property
    def error_rate(self) -> float:
        return self.errors / max(self.total_requests, 1)


class PerformanceOptimizer:
    """感知模块性能优化器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # 性能配置
        self.enable_cache = self.config.get("enable_cache", True)
        self.enable_batch_processing = self.config.get("enable_batch_processing", True)
        self.enable_async_processing = self.config.get("enable_async_processing", True)
        self.max_batch_size = self.config.get("max_batch_size", 10)
        self.max_workers = self.config.get("max_workers", 4)

        # 使用统一的缓存配置
        cache_config_dict = self.config.get("cache_config", {})
        if isinstance(cache_config_dict, dict):
            self.cache_config = CacheConfig(**cache_config_dict)
        else:
            self.cache_config = CacheConfig()

        # 获取性能缓存TTL(用于实时性能优化)
        self.cache_ttl = int(self.cache_config.performance_cache_ttl.total_seconds())

        # 缓存存储
        self.cache: dict[str, Any] = {}
        self.cache_timestamps: dict[str, datetime] = {}

        # 性能指标
        self.metrics = PerformanceMetrics()

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # 批处理队列
        self.batch_queue: list[dict[str, Any]] = []
        self.batch_timer: asyncio.Task | None = None

        logger.info("🚀 感知模块性能优化器初始化完成")

    def _generate_cache_key(self, data: Any, input_type: str, processor_id: str) -> str:
        """生成缓存键"""
        try:
            # 将数据序列化为字符串
            content = data if isinstance(data, str) else str(data)

            # 生成哈希
            content_hash = hashlib.md5(
                f"{processor_id}:{input_type}:{content}".encode('utf-8'), usedforsecurity=False
            ).hexdigest()
            return f"perception_{content_hash}"
        except Exception:
            # 如果生成哈希失败,使用简单组合
            return f"perception_{processor_id}_{input_type}_{len(str(data))}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if not self.enable_cache or cache_key not in self.cache:
            return False

        timestamp = self.cache_timestamps.get(cache_key)
        if not timestamp:
            return False

        return datetime.now() - timestamp < timedelta(seconds=self.cache_ttl)

    def _cleanup_expired_cache(self) -> Any:
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = []

        for cache_key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > timedelta(seconds=self.cache_ttl):
                expired_keys.append(cache_key)

        for key in expired_keys:
            self.cache.pop(key, None)
            self.cache_timestamps.pop(key, None)

        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")

    def cache_decorator(self, processor_func: Callable) -> Callable:
        """缓存装饰器"""

        @wraps(processor_func)
        async def wrapper(data: Any, input_type: str, **kwargs) -> PerceptionResult:
            # 获取处理器实例(self)
            processor = processor_func.__self__
            start_time = time.time()
            self.metrics.total_requests += 1

            try:
                # 检查缓存
                cache_key = self._generate_cache_key(data, input_type, processor.processor_id)

                if self._is_cache_valid(cache_key):
                    self.metrics.cache_hits += 1
                    cached_result = self.cache[cache_key]
                    logger.debug(f"缓存命中: {processor.processor_id}")
                    return cached_result

                self.metrics.cache_misses += 1

                # 执行处理
                result = await processor_func(data, input_type, **kwargs)

                # 缓存结果
                if self.enable_cache and result.confidence > 0.8:  # 只缓存高置信度结果
                    self.cache[cache_key] = result
                    self.cache_timestamps[cache_key] = datetime.now()

                # 更新指标
                processing_time = time.time() - start_time
                self.metrics.total_processing_time += processing_time

                return result

            except Exception as e:
                self.metrics.errors += 1
                logger.error(f"处理失败: {e}")
                raise

        return wrapper

    async def batch_process(
        self, processor, items: list[dict[str, Any]], max_concurrent: int | None = None
    ) -> list[PerceptionResult]:
        """批量处理

        Args:
            processor: 处理器实例
            items: 待处理项目列表
            max_concurrent: 最大并发数,None表示使用配置的max_workers值

        Returns:
            处理结果列表
        """
        if not self.enable_batch_processing or len(items) <= 1:
            # 降级到单个处理
            results = []
            for item in items:
                result = await processor.process(item["data"], item["input_type"])
                results.append(result)
            return results

        # 使用信号量限制并发数
        concurrency_limit = max_concurrent if max_concurrent is not None else self.max_workers
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def process_with_semaphore(item: dict[str, Any], index: int) -> PerceptionResult:
            """使用信号量限制的单项处理"""
            async with semaphore:
                try:
                    return await processor.process(item["data"], item["input_type"])
                except Exception as e:
                    logger.error(f"批量处理第 {index} 项失败: {e}")
                    # 创建错误结果
                    return PerceptionResult(
                        input_type=InputType.TEXT,
                        raw_content=item["data"],
                        processed_content=None,
                        features={"error": str(e)},
                        confidence=0.0,
                        metadata={"error": True, "batch_index": index},
                        timestamp=datetime.now(),
                    )

        start_time = time.time()
        logger.info(f"开始批量处理 {len(items)} 个项目,并发限制: {concurrency_limit}")

        # 创建带信号量限制的异步任务
        tasks: list[asyncio.Task[PerceptionResult]] = [
            asyncio.create_task(process_with_semaphore(item, i)) for i, item in enumerate(items)
        ]

        try:
            # 等待所有任务完成
            results = await asyncio.gather(*tasks)

            processing_time = time.time() - start_time
            logger.info(
                f"批量处理完成,耗时: {processing_time:.3f}秒,平均: {processing_time/len(items):.3f}秒/项"
            )

            return results

        except Exception as e:
            logger.error(f"批量处理失败: {e}")
            # 取消未完成的任务
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise

    def add_to_batch_queue(
        self, data: Any, input_type: str, callback: Callable | None = None
    ) -> None:
        """添加到批处理队列"""
        item = {
            "data": data,
            "input_type": input_type,
            "callback": callback,
            "timestamp": datetime.now(),
        }

        self.batch_queue.append(item)

        # 如果达到批处理大小或还没有批处理定时器,启动批处理
        if len(self.batch_queue) >= self.max_batch_size or not self.batch_timer:
            if self.batch_timer:
                self.batch_timer.cancel()
            self.batch_timer = asyncio.create_task(self._process_batch_queue())

    async def _process_batch_queue(self):
        """处理批处理队列"""
        if not self.batch_queue:
            return

        # 等待一小段时间以收集更多项目
        await asyncio.sleep(0.1)

        if not self.batch_queue:
            return

        # 获取当前队列中的所有项目
        current_batch = self.batch_queue.copy()
        self.batch_queue.clear()

        # 取消定时器
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None

        logger.info(f"处理批处理队列: {len(current_batch)} 个项目")

        # 这里应该调用相应的处理器
        # 由于这是通用优化器,我们只记录日志
        for item in current_batch:
            if item.get("callback"):
                try:
                    if inspect.iscoroutinefunction(item["callback"]):
                        await item["callback"](item["data"])
                    else:
                        item["callback"](item["data"])
                except Exception as e:
                    logger.error(f"批处理回调失败: {e}")

    def get_performance_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        self._cleanup_expired_cache()

        return {
            "total_requests": self.metrics.total_requests,
            "average_response_time": self.metrics.average_response_time,
            "cache_hit_rate": self.metrics.cache_hit_rate,
            "error_rate": self.metrics.error_rate,
            "cache_size": len(self.cache),
            "queue_size": len(self.batch_queue),
            "last_reset_time": self.metrics.last_reset_time.isoformat(),
        }

    def reset_metrics(self) -> Any:
        """重置性能指标"""
        self.metrics = PerformanceMetrics()
        logger.info("性能指标已重置")

    async def optimize_processor(self, processor):
        """优化处理器"""
        # 保存原始方法引用
        if not hasattr(processor, "_original_process"):
            processor._original_process = processor.process

        # 包装处理方法
        processor.process = self.cache_decorator(processor._original_process)

        # 添加批量处理方法
        if not hasattr(processor, "batch_process") or not hasattr(
            processor, "_original_batch_process"
        ):
            processor._original_batch_process = getattr(processor, "batch_process", None)
            processor.batch_process = lambda items: self.batch_process(processor, items)

        # 添加性能指标获取方法
        if not hasattr(processor, "_original_get_performance_metrics"):
            processor._original_get_performance_metrics = getattr(
                processor, "get_performance_metrics", None
            )
            processor.get_performance_metrics = lambda: self.get_performance_metrics()

        logger.info(f"处理器 {processor.processor_id} 优化完成")

        return processor

    async def cleanup(self):
        """清理资源"""
        # 取消批处理定时器
        if self.batch_timer:
            self.batch_timer.cancel()

        # 处理剩余的批处理队列
        if self.batch_queue:
            await self._process_batch_queue()

        # 关闭线程池
        self.executor.shutdown(wait=True)

        # 清理缓存
        self.cache.clear()
        self.cache_timestamps.clear()

        logger.info("性能优化器资源清理完成")


# 全局优化器实例
_global_optimizer: PerformanceOptimizer | None = None


async def get_global_optimizer(config: dict[str, Any] | None = None) -> PerformanceOptimizer:
    """获取全局性能优化器"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = PerformanceOptimizer(config)
    return _global_optimizer


# 性能优化装饰器
def optimize_performance(config: dict[str, Any] | None = None) -> Any:
    """性能优化装饰器"""

    def decorator(cls) -> Any:
        original_init = cls.__init__

        async def new_init(self, *args, **kwargs):
            await original_init(self, *args, **kwargs)

            # 获取全局优化器
            optimizer = await get_global_optimizer(config)

            # 优化当前处理器
            await optimizer.optimize_processor(self)

        cls.__init__ = new_init
        return cls

    return decorator


# 缓存管理器
class CacheManager:
    """统一缓存管理器

    使用统一的CacheConfig管理不同类型的缓存。
    支持多种缓存策略和TTL配置。
    """

    _instance: CacheManager | None = None
    _cache_config: CacheConfig

    def __new__(cls, cache_config: CacheConfig | None = None) -> 'CacheManager':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, cache_config: CacheConfig | None = None):
        """初始化缓存管理器"""
        if self._initialized:
            return

        self._cache_config = cache_config or CacheConfig()
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._initialized = True
        logger.info("统一缓存管理器初始化完成")

    @staticmethod
    @lru_cache(maxsize=1000)
    async def get_cached_result(cache_key: str) -> Any | None:
        """获取缓存结果(静态方法,用于向后兼容)"""
        return None

    async def get(self, cache_key: str, cache_type: str = "result") -> Any | None:
        """从缓存获取结果

        Args:
            cache_key: 缓存键
            cache_type: 缓存类型 ('ocr', 'result', 'metadata', 'performance', 'embedding')

        Returns:
            缓存的结果,如果不存在或已过期则返回None
        """
        if cache_key not in self._cache:
            return None

        result, timestamp = self._cache[cache_key]
        ttl = self._cache_config.get_ttl_for_cache_type(cache_type)

        if datetime.now() - timestamp > ttl:
            # 缓存已过期,删除
            del self._cache[cache_key]
            logger.debug(f"缓存已过期: {cache_key}")
            return None

        logger.debug(f"缓存命中: {cache_key}")
        return result

    async def set(self, cache_key: str, result: Any, cache_type: str = "result") -> None:
        """设置缓存结果

        Args:
            cache_key: 缓存键
            result: 要缓存的结果
            cache_type: 缓存类型 ('ocr', 'result', 'metadata', 'performance', 'embedding')
        """
        self._cache[cache_key] = (result, datetime.now())
        logger.debug(f"缓存已设置: {cache_key}, 类型: {cache_type}")

    @staticmethod
    async def set_cached_result(cache_key: str, result: Any, ttl: int = 3600):
        """设置缓存结果(静态方法,用于向后兼容)"""
        pass

    async def invalidate(self, cache_key: Optional[str] = None, pattern: str | None = None) -> None:
        """失效缓存

        Args:
            cache_key: 要失效的特定缓存键
            pattern: 要失效的缓存键模式(支持通配符)
        """
        if cache_key:
            self._cache.pop(cache_key, None)
            logger.debug(f"缓存已失效: {cache_key}")

        if pattern:
            import fnmatch

            keys_to_remove = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_remove:
                self._cache.pop(key, None)
            logger.debug(f"模式匹配失效了 {len(keys_to_remove)} 个缓存: {pattern}")

    @staticmethod
    async def invalidate_cache(pattern: str | None = None) -> None:
        """失效缓存(静态方法,用于向后兼容)"""
        pass

    async def cleanup_expired(self) -> int:
        """清理所有过期的缓存

        Returns:
            清理的缓存项数量
        """
        current_time = datetime.now()
        expired_keys = []

        for cache_key, (_, timestamp) in self._cache.items():
            # 检查各种TTL,使用最长的TTL来检查
            max_ttl = max(
                self._cache_config.ocr_cache_ttl,
                self._cache_config.result_cache_ttl,
                self._cache_config.metadata_cache_ttl,
            )
            if current_time - timestamp > max_ttl:
                expired_keys.append(cache_key)

        for key in expired_keys:
            self._cache.pop(key, None)

        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")

        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "total_cache_entries": len(self._cache),
            "ocr_ttl_seconds": int(self._cache_config.ocr_cache_ttl.total_seconds()),
            "result_ttl_seconds": int(self._cache_config.result_cache_ttl.total_seconds()),
            "metadata_ttl_seconds": int(self._cache_config.metadata_cache_ttl.total_seconds()),
            "performance_ttl_seconds": int(
                self._cache_config.performance_cache_ttl.total_seconds()
            ),
            "embedding_ttl_seconds": int(self._cache_config.embedding_cache_ttl.total_seconds()),
        }

    def clear_all(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        logger.info("所有缓存已清空")
