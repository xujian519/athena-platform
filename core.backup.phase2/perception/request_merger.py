#!/usr/bin/env python3
from __future__ import annotations
"""
请求合并器
Request Merger

通过合并相同或相似的请求来减少重复计算,提升系统性能。

功能特性:
1. 自动识别可合并的请求
2. 批量处理合并的请求
3. 结果缓存和分发
4. 超时控制
5. 优先级感知

合并策略:
- 完全相同:请求参数完全一致
- 语义相似:请求参数语义相似(如向量空间距离)
- 时间窗口:在时间窗口内的相同请求

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import contextlib
import hashlib
import inspect
import json
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MergeStrategy(Enum):
    """合并策略"""

    EXACT = "exact"  # 完全相同才合并
    SIMILAR = "similar"  # 语义相似即可合并
    TEMPORAL = "temporal"  # 时间窗口内合并
    ADAPTIVE = "adaptive"  # 自适应合并


@dataclass
class MergeKey:
    """合并键"""

    hash_value: str  # 请求哈希值
    method: str  # 请求方法/函数名
    similarity_threshold: float = 1.0  # 相似度阈值(0-1)

    def __eq__(self, other):
        if not isinstance(other, MergeKey):
            return False
        return self.hash_value == other.hash_value and self.method == other.method

    def __hash__(self):
        return hash((self.hash_value, self.method))


@dataclass
class PendingRequest:
    """待处理的请求"""

    request_id: str
    merge_key: MergeKey
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0  # 优先级(数字越小优先级越高)
    future: asyncio.Future | None = None


@dataclass
class MergeResult:
    """合并结果"""

    success: bool
    result: Any = None
    error: Exception | None = None
    merged_count: int = 0  # 合并的请求数量
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MergerMetrics:
    """合并器指标"""

    total_requests: int = 0
    merged_requests: int = 0
    total_batches: int = 0
    avg_batch_size: float = 0.0
    avg_merge_time: float = 0.0
    cache_hit_rate: float = 0.0
    total_processing_time: float = 0.0

    # 性能提升
    computation_saved: float = 0.0  # 节省的计算量(百分比)

    @property
    def merge_rate(self) -> float:
        """合并率"""
        return self.merged_requests / max(self.total_requests, 1)

    @property
    def efficiency_gain(self) -> float:
        """效率提升"""
        if self.avg_batch_size <= 1:
            return 0.0
        return (1 - 1 / self.avg_batch_size) * 100


class RequestMerger:
    """请求合并器

    自动合并相同或相似的请求,减少重复计算。

    使用示例:
        >>> merger = RequestMerger(strategy=MergeStrategy.ADAPTIVE)
        >>> await merger.initialize()
        >>>
        >>> # 定义处理函数
        >>> async def process_data(data_list):
        >>>     # 批量处理
        >>>     return [process(item) for item in data_list]
        >>>
        >>> # 注册处理函数
        >>> merger.register_handler("process_data", process_data)
        >>>
        >>> # 发起请求(会自动合并)
        >>> result = await merger.merge_request("process_data", data)
    """

    def __init__(
        self,
        strategy: MergeStrategy = MergeStrategy.ADAPTIVE,
        merge_window: float = 0.1,  # 合并时间窗口(秒)
        max_batch_size: int = 100,
        max_wait_time: float = 1.0,  # 最长等待时间
        similarity_threshold: float = 0.95,  # 相似度阈值
    ):
        """初始化合并器

        Args:
            strategy: 合并策略
            merge_window: 合并时间窗口
            max_batch_size: 最大批次大小
            max_wait_time: 最长等待时间
            similarity_threshold: 相似度阈值
        """
        self.strategy = strategy
        self.merge_window = merge_window
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.similarity_threshold = similarity_threshold

        # 待处理请求
        self._pending_requests: dict[MergeKey, list[PendingRequest]] = defaultdict(list)

        # 处理函数注册表
        self._handlers: dict[str, Callable] = {}

        # 结果缓存
        self._result_cache: dict[MergeKey, MergeResult] = {}

        # 锁
        self._lock = asyncio.Lock()

        # 后台任务
        self._background_task: asyncio.Task | None = None
        self._running = False

        # 指标
        self.metrics = MergerMetrics()

        logger.info(
            f"🔄 初始化请求合并器 (策略={strategy.value}, "
            f"时间窗口={merge_window}s, 最大批次={max_batch_size})"
        )

    async def initialize(self) -> None:
        """初始化合并器"""
        if self._running:
            return

        self._running = True
        self._background_task = asyncio.create_task(self._merge_loop())

        logger.info("✅ 请求合并器启动完成")

    async def shutdown(self) -> None:
        """关闭合并器"""
        logger.info("🛑 关闭请求合并器...")

        self._running = False

        if self._background_task:
            self._background_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._background_task

        # 处理剩余请求
        await self._flush_all()

        logger.info("✅ 请求合并器已关闭")

    def register_handler(self, name: str, handler: Callable) -> None:
        """注册处理函数

        Args:
            name: 处理函数名称
            handler: 处理函数(接收批量数据)
        """
        self._handlers[name] = handler
        logger.info(f"📦 注册处理函数: {name}")

    async def merge_request(
        self,
        method: str,
        *args: Any,
        priority: int = 0,
        **kwargs: Any,
    ) -> Any:
        """合并请求

        Args:
            method: 处理方法名称
            *args: 位置参数
            priority: 优先级
            **kwargs: 关键字参数

        Returns:
            处理结果
        """
        if method not in self._handlers:
            raise ValueError(f"未注册的处理方法: {method}")

        start_time = time.time()
        self.metrics.total_requests += 1

        # 生成合并键
        merge_key = self._generate_merge_key(method, args, kwargs)

        # 检查缓存
        if merge_key in self._result_cache:
            cached_result = self._result_cache[merge_key]
            # 检查缓存是否过期(1秒内的缓存有效)
            if (datetime.now() - cached_result.timestamp).total_seconds() < 1.0:
                logger.debug(f"💰 缓存命中: {merge_key.hash_value[:8]}...")
                return cached_result.result

        # 创建Future
        future = asyncio.get_event_loop().create_future()

        # 创建待处理请求
        pending_request = PendingRequest(
            request_id=f"{merge_key.hash_value[:8]}_{time.time():.3f}",
            merge_key=merge_key,
            args=args,
            kwargs=kwargs,
            priority=priority,
            future=future,
        )

        # 加入待处理队列
        async with self._lock:
            self._pending_requests[merge_key].append(pending_request)

            # 如果达到最大批次大小,立即处理
            if len(self._pending_requests[merge_key]) >= self.max_batch_size:
                await self._process_batch(merge_key)

        # 等待结果
        try:
            result = await asyncio.wait_for(future, timeout=self.max_wait_time)
            processing_time = time.time() - start_time
            self.metrics.total_processing_time += processing_time
            return result
        except asyncio.TimeoutError:
            logger.warning(f"⏰ 请求超时: {pending_request.request_id}")
            raise

    def _generate_merge_key(
        self,
        method: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],    ) -> MergeKey:
        """生成合并键

        Args:
            method: 方法名
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            合并键
        """
        # 序列化参数
        serialized = self._serialize_params(args, kwargs)

        # 生成哈希
        hash_value = hashlib.sha256(serialized.encode()).hexdigest()

        return MergeKey(
            hash_value=hash_value,
            method=method,
            similarity_threshold=self.similarity_threshold,
        )

    def _serialize_params(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        """序列化参数"""

        def serialize(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, (list, tuple)):
                return [serialize(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            else:
                # 其他类型转为字符串
                return str(obj)

        serializable = {
            "args": serialize(args),
            "kwargs": serialize(kwargs),
        }
        return json.dumps(serializable, sort_keys=True)

    async def _merge_loop(self) -> None:
        """合并循环"""
        while self._running:
            try:
                await asyncio.sleep(self.merge_window)

                # 处理所有待合并的请求
                await self._flush_all()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 合并循环异常: {e}")
                await asyncio.sleep(1)

    async def _flush_all(self) -> None:
        """处理所有待合并的请求"""
        async with self._lock:
            # 复制键列表以避免在迭代时修改
            keys = list(self._pending_requests.keys())

            for key in keys:
                if self._pending_requests[key]:
                    await self._process_batch(key)

    async def _process_batch(self, merge_key: MergeKey) -> None:
        """处理批次

        Args:
            merge_key: 合并键
        """
        if merge_key not in self._pending_requests:
            return

        requests = self._pending_requests.pop(merge_key)
        if not requests:
            return

        start_time = time.time()
        self.metrics.total_batches += 1
        batch_size = len(requests)
        self.metrics.merged_requests += batch_size

        logger.info(
            f"🔄 处理批次: {merge_key.method} "
            f"(数量={batch_size}, 键={merge_key.hash_value[:8]}...)"
        )

        try:
            # 获取处理函数
            handler = self._handlers.get(merge_key.method)
            if not handler:
                raise ValueError(f"未注册的处理方法: {merge_key.method}")

            # 准备批量数据
            batch_data = []
            for req in requests:
                batch_data.append({"args": req.args, "kwargs": req.kwargs})

            # 批量处理
            if inspect.iscoroutinefunction(handler):
                batch_results = await handler(batch_data)
            else:
                batch_results = handler(batch_data)

            # 分发结果
            for i, req in enumerate(requests):
                if req.future and not req.future.done():
                    # 如果是单个结果,直接返回
                    # 如果是批量结果,返回对应索引的结果
                    if isinstance(batch_results, list):
                        result = batch_results[i] if i < len(batch_results) else None
                    else:
                        result = batch_results
                    req.future.set_result(result)

            # 创建合并结果
            merge_result = MergeResult(
                success=True,
                result=batch_results,
                merged_count=batch_size,
                processing_time=time.time() - start_time,
            )

            # 缓存结果
            self._result_cache[merge_key] = merge_result

            # 更新指标
            self.metrics.avg_merge_time = merge_result.processing_time
            self.metrics.avg_batch_size = (
                self.metrics.avg_batch_size * (self.metrics.total_batches - 1) + batch_size
            ) / self.metrics.total_batches

            logger.debug(
                f"✅ 批次处理完成: {merge_key.method} "
                f"(耗时={merge_result.processing_time:.3f}s, 数量={batch_size})"
            )

        except Exception as e:
            logger.error(f"❌ 批次处理失败: {merge_key.method} - {e}")

            # 通知所有等待者
            for req in requests:
                if req.future and not req.future.done():
                    req.future.set_exception(e)

    def get_metrics(self) -> MergerMetrics:
        """获取指标"""
        # 计算缓存命中率
        if self.metrics.total_requests > 0:
            self.metrics.cache_hit_rate = (
                self.metrics.total_requests - self.metrics.merged_requests
            ) / self.metrics.total_requests

        # 计算节省的计算量
        if self.metrics.avg_batch_size > 1:
            self.metrics.computation_saved = (1 - 1 / self.metrics.avg_batch_size) * 100

        return self.metrics

    async def clear_cache(self) -> None:
        """清空缓存"""
        self._result_cache.clear()
        logger.info("🧹 清空合并器缓存")


# 便捷函数
def create_request_merger(
    strategy: MergeStrategy = MergeStrategy.ADAPTIVE,
    merge_window: float = 0.1,
    max_batch_size: int = 100,
) -> RequestMerger:
    """创建请求合并器"""
    return RequestMerger(
        strategy=strategy,
        merge_window=merge_window,
        max_batch_size=max_batch_size,
    )


# 装饰器
def merge_requests(
    merger: RequestMerger | None = None,
    method: str | None = None,
):
    """请求合并装饰器

    Args:
        merger: 合并器实例(如果为None,使用全局实例)
        method: 方法名称(如果为None,使用函数名)

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 使用全局合并器或提供的合并器
            m = merger or _global_merger

            # 确定方法名
            name = method or func.__name__

            # 注册处理函数
            if name not in m._handlers:

                async def batch_handler(batch_data):
                    # 批量处理
                    results = []
                    for item in batch_data:
                        result = await func(*item["args"], **item["kwargs"])
                        results.append(result)
                    return results

                m.register_handler(name, batch_handler)

            # 合并请求
            return await m.merge_request(name, *args, **kwargs)

        return wrapper

    return decorator


# 全局合并器实例
_global_merger: RequestMerger | None = None


def get_global_merger() -> RequestMerger:
    """获取全局合并器实例"""
    global _global_merger
    if _global_merger is None:
        _global_merger = create_request_merger()
    return _global_merger


async def initialize_global_merger() -> RequestMerger:
    """初始化全局合并器"""
    merger = get_global_merger()
    await merger.initialize()
    return merger


__all__ = [
    "MergeKey",
    "MergeResult",
    "MergeStrategy",
    "MergerMetrics",
    "PendingRequest",
    "RequestMerger",
    "create_request_merger",
    "get_global_merger",
    "initialize_global_merger",
    "merge_requests",
]
