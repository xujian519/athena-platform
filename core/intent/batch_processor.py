from __future__ import annotations
"""
意图识别服务 - 动态批处理引擎

实现智能批处理策略,动态调整批大小以优化性能。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""
import logging
import time
from collections import deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Any

import numpy as np

# ========================================================================
# 批处理策略枚举
# ========================================================================


class BatchStrategy(str, Enum):
    """批处理策略"""

    FIXED = "fixed"  # 固定批大小
    ADAPTIVE = "adaptive"  # 自适应批大小
    DYNAMIC = "dynamic"  # 动态批大小(基于系统负载)
    LATENCY_OPTIMIZED = "latency"  # 延迟优化(小批次)
    THROUGHPUT_OPTIMIZED = "throughput"  # 吞吐量优化(大批次)


# ========================================================================
# 批处理配置
# ========================================================================


@dataclass
class BatchConfig:
    """
    批处理配置

    定义批处理的各种参数和约束。
    """

    # 基础配置
    strategy: BatchStrategy = BatchStrategy.ADAPTIVE
    min_batch_size: int = 1
    max_batch_size: int = 32
    initial_batch_size: int = 8

    # 延迟约束
    max_wait_time_ms: float = 50.0  # 最大等待时间(毫秒)
    max_latency_ms: float = 100.0  # 最大端到端延迟(毫秒)

    # 吞吐量约束
    target_throughput: float = 100.0  # 目标吞吐量(请求/秒)

    # 资源约束
    max_memory_mb: int = 2048  # 最大内存使用(MB)
    max_queue_size: int = 100  # 最大队列大小

    # 自适应参数
    adjustment_factor: float = 1.5  # 批大小调整因子
    warmup_samples: int = 10  # 预热样本数
    stability_threshold: float = 0.1  # 稳定性阈值(标准差/均值)


# ========================================================================
# 批处理统计
# ========================================================================


@dataclass
class BatchStats:
    """批处理统计信息"""

    total_batches: int = 0
    total_items: int = 0
    total_time_ms: float = 0.0
    avg_batch_size: float = 0.0
    avg_latency_ms: float = 0.0
    avg_throughput: float = 0.0
    current_batch_size: int = 0
    cache_hit_rate: float = 0.0
    memory_usage_mb: float = 0.0


# ========================================================================
# 批处理项
# ========================================================================


@dataclass
class BatchItem:
    """
    批处理项

    包含输入文本、回调函数和时间戳。
    """

    text: str
    callback: Callable[..., Any] | None = None
    context: Optional[dict[str, Any]] = None
    timestamp: float = 0.0
    text_length: int = 0
    estimated_complexity: float = 1.0

    def __post_init__(self):
        """初始化后处理"""
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.text_length == 0:
            self.text_length = len(self.text)
        # 估算复杂度(基于文本长度)
        self.estimated_complexity = min(1.0 + self.text_length / 100.0, 5.0)


# ========================================================================
# 批处理结果
# ========================================================================


@dataclass
class BatchResult:
    """
    批处理结果

    包含处理结果和性能指标。
    """

    results: list[Any]
    batch_size: int
    processing_time_ms: float
    waiting_time_ms: float
    total_latency_ms: float
    throughput: float
    strategy_used: BatchStrategy


# ========================================================================
# 动态批处理器
# ========================================================================


class DynamicBatchProcessor:
    """
    动态批处理器

    根据系统负载和请求特征动态调整批处理策略。
    """

    def __init__(
        self, processor_func: Callable[[list[str]], list[Any]], config: BatchConfig | None = None
    ):
        """
        初始化批处理器

        Args:
            processor_func: 批处理函数,接收文本列表,返回结果列表
            config: 批处理配置
        """
        self.processor_func = processor_func
        self.config = config or BatchConfig()

        # 批处理队列
        self._queue: deque[BatchItem] = deque()
        self._queue_lock = Lock()

        # 性能跟踪
        self._latencies: list[float] = []
        self._batch_sizes: list[int] = []
        self._throughputs: list[float] = []

        # 当前状态
        self._current_batch_size = self.config.initial_batch_size
        self._is_processing = False

        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=2)

        # 统计信息
        self._stats = BatchStats()
        self._stats_lock = Lock()

        self.logger = logging.getLogger("intent.batch_processor")
        self.logger.info(
            f"动态批处理器初始化完成 (策略: {self.config.strategy.value}, "
            f"初始批大小: {self._current_batch_size})"
        )

    def submit(
        self,
        text: str,
        callback: Callable[..., Any] | None = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        提交单个文本到批处理队列

        Args:
            text: 输入文本
            callback: 结果回调函数
            context: 上下文信息
        """
        item = BatchItem(text=text, callback=callback, context=context)

        should_process = False

        with self._queue_lock:
            if len(self._queue) >= self.config.max_queue_size:
                self.logger.warning("批处理队列已满,强制触发处理")
                should_process = True

            self._queue.append(item)

            # 判断是否触发批处理
            if not should_process and self._should_trigger_batch():
                should_process = True

        # 在锁外触发批处理,避免死锁
        if should_process:
            self._process_batch()

    def submit_batch(
        self,
        texts: list[str],
        callbacks: list[Callable[..., Any]] | None = None,
        contexts: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        批量提交文本到批处理队列

        Args:
            texts: 输入文本列表
            callbacks: 回调函数列表
            contexts: 上下文列表
        """
        # 初始化默认值
        if callbacks is None:
            callbacks = []
        if contexts is None:
            contexts = []

        # 补齐长度
        while len(callbacks) < len(texts):
            callbacks.append(None)
        while len(contexts) < len(texts):
            contexts.append(None)

        # 提交每个文本
        for i, text in enumerate(texts):
            self.submit(text, callbacks[i], contexts[i])

    def _should_trigger_batch(self) -> bool:
        """
        判断是否应该触发批处理

        Returns:
            是否触发
        """
        if not self._queue:
            return False

        # 检查队列大小
        queue_size = len(self._queue)
        if queue_size >= self._current_batch_size:
            return True

        # 检查等待时间
        oldest_item = self._queue[0]
        wait_time = (time.time() - oldest_item.timestamp) * 1000

        return wait_time >= self.config.max_wait_time_ms

    def _process_batch(self) -> None:
        """
        处理一个批次

        从队列中取出项目并处理。
        """
        if self._is_processing:
            return

        self._is_processing = True

        try:
            # 从队列中提取批次
            batch_items = []
            with self._queue_lock:
                batch_size = min(len(self._queue), self._current_batch_size)
                for _ in range(batch_size):
                    if self._queue:
                        batch_items.append(self._queue.popleft())

            if not batch_items:
                self._is_processing = False
                return

            # 记录开始时间
            start_time = time.perf_counter()
            start_timestamp = time.time()

            # 提取文本和计算等待时间
            texts = [item.text for item in batch_items]
            waiting_times = [(start_timestamp - item.timestamp) * 1000 for item in batch_items]
            avg_waiting_time = np.mean(waiting_times)

            # 调用处理函数
            try:
                results = self.processor_func(texts)
            except Exception as e:
                self.logger.error(f"批处理失败: {e}")
                results = [None] * len(texts)

            # 计算处理时间
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            total_latencies = [
                waiting_times[i] + processing_time_ms for i in range(len(batch_items))
            ]
            avg_latency = np.mean(total_latencies)

            # 计算吞吐量
            throughput = len(batch_items) / (processing_time_ms / 1000.0)

            # 调用回调函数
            for item, result in zip(batch_items, results, strict=False):
                if item.callback:
                    try:
                        item.callback(result)
                    except Exception as e:
                        self.logger.error(f"回调函数执行失败: {e}")

            # 更新统计信息
            self._update_stats(
                batch_size=len(batch_items),
                processing_time_ms=float(processing_time_ms),
                waiting_time_ms=float(avg_waiting_time),
                throughput=float(throughput),
            )

            # 记录性能指标
            self._latencies.append(float(avg_latency))
            self._batch_sizes.append(len(batch_items))
            self._throughputs.append(float(throughput))

            # 动态调整批大小
            self._adjust_batch_size()

            self.logger.debug(
                f"批处理完成 (大小: {len(batch_items)}, "
                f"延迟: {avg_latency:.2f}ms, "
                f"吞吐量: {throughput:.2f} req/s)"
            )

        finally:
            self._is_processing = False

    def _adjust_batch_size(self) -> None:
        """
        动态调整批大小

        根据性能指标和配置的策略调整批大小。
        """
        if self.config.strategy == BatchStrategy.FIXED:
            return

        # 确保有足够的历史数据
        if len(self._latencies) < self.config.warmup_samples:
            return

        # 获取最近的性能指标
        recent_latencies = self._latencies[-self.config.warmup_samples :]
        recent_throughputs = self._throughputs[-self.config.warmup_samples :]

        avg_latency = float(np.mean(recent_latencies))
        std_latency = float(np.std(recent_latencies))
        avg_throughput = float(np.mean(recent_throughputs))

        # 计算稳定性
        stability = float(std_latency / avg_latency if avg_latency > 0 else 0)

        # 根据策略调整批大小
        if self.config.strategy == BatchStrategy.ADAPTIVE:
            self._adaptive_adjustment(avg_latency, avg_throughput, stability)
        elif self.config.strategy == BatchStrategy.DYNAMIC:
            self._dynamic_adjustment(avg_latency, avg_throughput, stability)
        elif self.config.strategy == BatchStrategy.LATENCY_OPTIMIZED:
            self._latency_optimized_adjustment(avg_latency)
        elif self.config.strategy == BatchStrategy.THROUGHPUT_OPTIMIZED:
            self._throughput_optimized_adjustment(avg_throughput)

    def _adaptive_adjustment(
        self, avg_latency: float, avg_throughput: float, stability: float
    ) -> None:
        """
        自适应调整策略

        综合考虑延迟、吞吐量和稳定性。
        """
        # 检查是否超过延迟约束
        if avg_latency > self.config.max_latency_ms:
            # 延迟过高,减小批大小
            new_size = int(self._current_batch_size / self.config.adjustment_factor)
            self._current_batch_size = max(new_size, self.config.min_batch_size)
            self.logger.debug(
                f"延迟过高({avg_latency:.2f}ms),减小批大小到 {self._current_batch_size}"
            )
            return

        # 检查稳定性
        if stability > self.config.stability_threshold:
            # 不稳定,保持当前批大小
            return

        # 检查吞吐量
        if avg_throughput < self.config.target_throughput:
            # 吞吐量不足,增加批大小
            new_size = int(self._current_batch_size * self.config.adjustment_factor)
            self._current_batch_size = min(new_size, self.config.max_batch_size)
            self.logger.debug(
                f"吞吐量不足({avg_throughput:.2f} req/s),增加批大小到 {self._current_batch_size}"
            )

    def _dynamic_adjustment(
        self, avg_latency: float, avg_throughput: float, stability: float
    ) -> None:
        """
        动态调整策略

        更激进地调整批大小,追求最优性能。
        """
        # 计算性能分数(0-1)
        latency_score = float(1.0 - min(avg_latency / self.config.max_latency_ms, 1.0))
        throughput_score = float(min(avg_throughput / self.config.target_throughput, 1.0))
        stability_score = float(1.0 - min(stability / self.config.stability_threshold, 1.0))

        # 综合分数
        overall_score = float(latency_score * 0.4 + throughput_score * 0.4 + stability_score * 0.2)

        # 根据分数调整
        if overall_score > 0.8:
            # 性能很好,大幅增加批大小
            factor = 2.0
        elif overall_score > 0.6:
            # 性能良好,适度增加
            factor = 1.5
        elif overall_score > 0.4:
            # 性能一般,小幅调整
            factor = 1.1
        else:
            # 性能较差,减小批大小
            factor = 0.8

        new_size = int(self._current_batch_size * factor)
        self._current_batch_size = max(
            min(new_size, self.config.max_batch_size), self.config.min_batch_size
        )

    def _latency_optimized_adjustment(self, avg_latency: float) -> None:
        """
        延迟优化调整策略

        优先保证低延迟,使用小批次。
        """
        if avg_latency > self.config.max_latency_ms * 0.8:
            # 接近延迟上限,大幅减小
            self._current_batch_size = max(
                int(self._current_batch_size * 0.7), self.config.min_batch_size
            )
        elif avg_latency < self.config.max_latency_ms * 0.5:
            # 延迟很低,可以适当增加
            self._current_batch_size = min(
                int(self._current_batch_size * 1.2),
                self.config.max_batch_size // 2,  # 限制为最大值的一半
            )

    def _throughput_optimized_adjustment(self, avg_throughput: float) -> None:
        """
        吞吐量优化调整策略

        优先保证高吞吐量,使用大批次。
        """
        if avg_throughput < self.config.target_throughput:
            # 吞吐量不足,增加批大小
            self._current_batch_size = min(
                int(self._current_batch_size * 1.5), self.config.max_batch_size
            )
        else:
            # 吞吐量足够,继续尝试增加以获得更高吞吐量
            self._current_batch_size = min(
                int(self._current_batch_size * 1.1), self.config.max_batch_size
            )

    def _update_stats(
        self, batch_size: int, processing_time_ms: float, waiting_time_ms: float, throughput: float
    ) -> None:
        """
        更新统计信息

        Args:
            batch_size: 批大小
            processing_time_ms: 处理时间
            waiting_time_ms: 等待时间
            throughput: 吞吐量
        """
        with self._stats_lock:
            self._stats.total_batches += 1
            self._stats.total_items += batch_size
            self._stats.total_time_ms += processing_time_ms + waiting_time_ms

            # 计算平均值
            self._stats.avg_batch_size = self._stats.total_items / self._stats.total_batches
            self._stats.avg_latency_ms = self._stats.total_time_ms / self._stats.total_items
            self._stats.avg_throughput = self._stats.total_items / (
                self._stats.total_time_ms / 1000.0
            )
            self._stats.current_batch_size = self._current_batch_size

    def get_stats(self) -> BatchStats:
        """
        获取统计信息

        Returns:
            统计信息对象
        """
        with self._stats_lock:
            return BatchStats(
                total_batches=self._stats.total_batches,
                total_items=self._stats.total_items,
                total_time_ms=self._stats.total_time_ms,
                avg_batch_size=self._stats.avg_batch_size,
                avg_latency_ms=self._stats.avg_latency_ms,
                avg_throughput=self._stats.avg_throughput,
                current_batch_size=self._stats.current_batch_size,
                cache_hit_rate=self._stats.cache_hit_rate,
                memory_usage_mb=self._stats.memory_usage_mb,
            )

    def reset_stats(self) -> None:
        """重置统计信息"""
        with self._stats_lock:
            self._stats = BatchStats()
            self._latencies.clear()
            self._batch_sizes.clear()
            self._throughputs.clear()

    def flush(self) -> None:
        """
        刷新队列

        强制处理队列中所有剩余项目。
        """
        max_iterations = 100  # 防止无限循环
        iteration = 0

        while self._queue and iteration < max_iterations:
            self._process_batch()
            iteration += 1

            # 短暂等待异步处理完成
            if self._is_processing:
                time.sleep(0.01)

    def shutdown(self) -> None:
        """
        关闭批处理器

        刷新队列并关闭线程池。
        """
        self.logger.info("关闭批处理器...")
        self.flush()
        self._executor.shutdown(wait=True)
        self.logger.info("批处理器已关闭")


# ========================================================================
# 批处理上下文管理器
# ========================================================================


class BatchProcessorManager:
    """
    批处理管理器

    管理多个批处理器实例。
    """

    _instances: dict[str, DynamicBatchProcessor] = {}

    @classmethod
    def register(cls, name: str, processor: DynamicBatchProcessor) -> None:
        """
        注册批处理器

        Args:
            name: 处理器名称
            processor: 批处理器实例
        """
        cls._instances[name] = processor

    @classmethod
    def get(cls, name: str) -> DynamicBatchProcessor | None:
        """
        获取批处理器

        Args:
            name: 处理器名称

        Returns:
            批处理器实例或None
        """
        return cls._instances.get(name)

    @classmethod
    def shutdown_all(cls) -> None:
        """关闭所有批处理器"""
        for processor in cls._instances.values():
            processor.shutdown()
        cls._instances.clear()


# ========================================================================
# 辅助函数
# ========================================================================


def create_batch_config(
    strategy: str = "adaptive", min_batch_size: int = 1, max_batch_size: int = 32, **kwargs: Any
) -> BatchConfig:
    """
    创建批处理配置

    Args:
        strategy: 策略名称
        min_batch_size: 最小批大小
        max_batch_size: 最大批大小
        **kwargs: 其他配置参数

    Returns:
        批处理配置对象
    """
    strategy_enum = BatchStrategy(strategy)

    return BatchConfig(
        strategy=strategy_enum,
        min_batch_size=min_batch_size,
        max_batch_size=max_batch_size,
        **kwargs,
    )


def estimate_optimal_batch_size(
    avg_text_length: int, model_complexity: float = 1.0, memory_constraint_mb: int = 2048
) -> int:
    """
    估算最优批大小

    Args:
        avg_text_length: 平均文本长度
        model_complexity: 模型复杂度因子
        memory_constraint_mb: 内存约束(MB)

    Returns:
        估算的最优批大小
    """
    # 基础批大小(基于文本长度)
    base_size = max(1, int(512 / max(avg_text_length, 50)))

    # 考虑模型复杂度
    adjusted_size = int(base_size / model_complexity)

    # 考虑内存约束(假设每个样本使用 memory_constraint_mb/批大小 MB)
    memory_limited_size = max(1, int(memory_constraint_mb / 100))

    # 返回较小值
    return min(adjusted_size, memory_limited_size, 32)


# ========================================================================
# 导出
# ========================================================================

__all__ = [
    "BatchConfig",
    "BatchItem",
    "BatchProcessorManager",
    "BatchResult",
    "BatchStats",
    "BatchStrategy",
    "DynamicBatchProcessor",
    "create_batch_config",
    "estimate_optimal_batch_size",
]
