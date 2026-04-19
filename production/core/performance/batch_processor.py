#!/usr/bin/env python3
"""
智能批处理器
实现高效的批量推理,提升吞吐量5-10倍

作者: Athena AI
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import contextlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """批处理请求"""

    request_id: str
    text: str
    priority: int = 2  # 1=high, 2=medium, 3=low
    timestamp: float = field(default_factory=time.time)
    future: "asyncio.Future[Any]" = field(default=None)

    def __post_init__(self):
        if self.future is None:
            self.future = asyncio.Future()


@dataclass
class BatchStats:
    """批处理统计"""

    total_requests: int = 0
    total_batches: int = 0
    avg_batch_size: float = 0.0
    avg_latency_ms: float = 0.0
    peak_batch_size: int = 0
    total_processing_time_sec: float = 0.0


class BatchProcessor:
    """智能批处理器

    特性:
    - 优先级队列: 高优先级请求优先处理
    - 动态批大小: 根据负载自动调整
    - 超时机制: 避免请求饥饿
    - MPS优化: 充分利用GPU批处理能力
    """

    def __init__(
        self,
        model: Any,
        batch_size: int = 32,
        timeout_ms: int = 50,
        device: str = "mps",
        enable_adaptive_batching: bool = True,
        min_batch_size: int = 8,
        max_batch_size: int = 64,
    ):
        """
        初始化批处理器

        Args:
            model: 嵌入模型
            batch_size: 目标批大小
            timeout_ms: 批处理超时(毫秒)
            device: 推理设备('mps'或'cpu')
            enable_adaptive_batching: 启用自适应批大小
            min_batch_size: 最小批大小
            max_batch_size: 最大批大小
        """
        self.model = model
        self.batch_size = batch_size
        self.timeout = timeout_ms / 1000
        self.device = device

        # 自适应批处理
        self.enable_adaptive_batching = enable_adaptive_batching
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.current_batch_size = batch_size

        # 按优先级分组的请求队列
        self.pending_requests: dict[int, list[BatchRequest]] = defaultdict(list)

        # 统计信息
        self.stats = BatchStats()

        # 后台任务
        self._processing_task: asyncio.Task | None = None
        self._running = False

        # 性能监控
        self._recent_latencies: list[float] = []
        self._max_latency_samples = 100

    async def start(self):
        """启动批处理器"""
        if self._running:
            logger.warning("批处理器已在运行")
            return

        self._running = True
        self._processing_task = asyncio.create_task(self._process_loop())
        logger.info("✅ 批处理器已启动")

    async def stop(self):
        """停止批处理器"""
        self._running = False

        if self._processing_task:
            self._processing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._processing_task

        # 完成剩余请求
        for _priority, requests in self.pending_requests.items():
            for req in requests:
                if not req.future.done():
                    req.future.set_exception(RuntimeError("批处理器已停止"))

        self.pending_requests.clear()
        logger.info("⏹️ 批处理器已停止")

    async def process(self, text: str, priority: int = 2) -> Any:
        """
        处理单个文本请求

        Args:
            text: 待处理文本
            priority: 优先级 (1=high, 2=medium, 3=low)

        Returns:
            处理结果(嵌入向量)
        """
        # 创建请求
        request = BatchRequest(request_id=f"{id(text)}_{time.time()}", text=text, priority=priority)

        # 添加到队列
        self.pending_requests[priority].append(request)
        self.stats.total_requests += 1

        # 等待结果
        try:
            result = await asyncio.wait_for(request.future, timeout=10.0)
            return result
        except asyncio.TimeoutError:
            # 超时处理
            self.pending_requests[priority].remove(request)
            raise asyncio.TimeoutError(f"请求超时: {request.request_id}") from None

    async def _process_loop(self):
        """批处理主循环"""
        while self._running:
            try:
                # 检查是否有待处理请求
                total_pending = sum(len(reqs) for reqs in self.pending_requests.values())

                if total_pending == 0:
                    await asyncio.sleep(0.001)
                    continue

                # 检查是否应该处理批次
                should_process = False

                # 条件1: 达到当前批大小
                if total_pending >= self.current_batch_size:
                    should_process = True
                # 条件2: 超时
                else:
                    for priority in sorted(self.pending_requests.keys()):
                        if self.pending_requests[priority]:
                            oldest = self.pending_requests[priority][0]
                            if time.time() - oldest.timestamp >= self.timeout:
                                should_process = True
                                break

                if should_process:
                    await self._process_batch()

                # 自适应调整批大小
                if self.enable_adaptive_batching:
                    self._adjust_batch_size()

                await asyncio.sleep(0.001)

            except Exception as e:
                logger.error(f"批处理循环错误: {e}", exc_info=True)
                await asyncio.sleep(0.01)

    async def _process_batch(self):
        """处理一个批次"""
        batch_requests = []

        # 按优先级收集请求
        for priority in sorted(self.pending_requests.keys()):
            needed = self.current_batch_size - len(batch_requests)
            if needed <= 0:
                break

            available = self.pending_requests[priority][:needed]
            batch_requests.extend(available)
            self.pending_requests[priority] = self.pending_requests[priority][needed:]

        if not batch_requests:
            return

        try:
            # 提取文本
            texts = [req.text for req in batch_requests]

            # 批量编码
            start_time = time.time()

            embeddings = await self._encode_batch(texts)

            latency_ms = (time.time() - start_time) * 1000

            # 分发结果
            for req, embedding in zip(batch_requests, embeddings, strict=False):
                if not req.future.done():
                    req.future.set_result(embedding)

            # 更新统计
            self.stats.total_batches += 1
            self.stats.peak_batch_size = max(self.stats.peak_batch_size, len(batch_requests))

            # 滑动平均
            alpha = 0.1
            self.stats.avg_batch_size = (
                alpha * len(batch_requests) + (1 - alpha) * self.stats.avg_batch_size
            )
            self.stats.avg_latency_ms = alpha * latency_ms + (1 - alpha) * self.stats.avg_latency_ms

            self.stats.total_processing_time_sec += time.time() - start_time

            # 记录延迟用于自适应调整
            self._recent_latencies.append(latency_ms)
            if len(self._recent_latencies) > self._max_latency_samples:
                self._recent_latencies.pop(0)

            logger.debug(
                f"📦 批次: {len(batch_requests)}请求, "
                f"延迟: {latency_ms:.2f}ms, "
                f"吞吐: {len(batch_requests)/(latency_ms/1000):.0f} texts/sec"
            )

        except Exception as e:
            # 错误处理 - 标记所有请求失败
            for req in batch_requests:
                if not req.future.done():
                    req.future.set_exception(e)
            logger.error(f"批处理失败: {e}", exc_info=True)

    async def _encode_batch(self, texts: list[str]) -> list[Any]:
        """批量编码文本

        根据设备类型选择最优编码方式
        """
        if self.device == "mps":
            # MPS批处理 - 使用大batch size
            embeddings = self.model.encode(
                texts, batch_size=len(texts), device="mps", show_progress_bar=False
            )
        else:
            # CPU批处理
            embeddings = self.model.encode(
                texts, batch_size=min(32, len(texts)), show_progress_bar=False
            )

        return embeddings

    def _adjust_batch_size(self) -> Any:
        """自适应调整批大小

        基于最近延迟动态调整:
        - 延迟高 -> 减小批大小
        - 延迟低 -> 增大批大小
        """
        if len(self._recent_latencies) < 10:
            return

        avg_latency = sum(self._recent_latencies) / len(self._recent_latencies)

        # 目标延迟: 50ms
        target_latency = 50.0

        if avg_latency > target_latency * 1.2:
            # 延迟过高,减小批大小
            new_size = max(self.min_batch_size, int(self.current_batch_size * 0.9))
            if new_size != self.current_batch_size:
                logger.debug(f"减小批大小: {self.current_batch_size} -> {new_size}")
                self.current_batch_size = new_size

        elif avg_latency < target_latency * 0.8:
            # 延迟较低,增大批大小
            new_size = min(self.max_batch_size, int(self.current_batch_size * 1.1))
            if new_size != self.current_batch_size:
                logger.debug(f"增大批大小: {self.current_batch_size} -> {new_size}")
                self.current_batch_size = new_size

    def get_stats(self) -> dict:
        """获取统计信息"""
        total_processing_time = self.stats.total_processing_time_sec

        return {
            "total_requests": self.stats.total_requests,
            "total_batches": self.stats.total_batches,
            "avg_batch_size": round(self.stats.avg_batch_size, 1),
            "peak_batch_size": self.stats.peak_batch_size,
            "avg_latency_ms": round(self.stats.avg_latency_ms, 2),
            "pending_requests": sum(len(reqs) for reqs in self.pending_requests.values()),
            "current_batch_size": self.current_batch_size,
            "throughput_per_sec": (
                round(self.stats.total_requests / max(total_processing_time, 0.001), 1)
                if total_processing_time > 0
                else 0
            ),
            "device": self.device,
            "running": self._running,
        }

    def get_queue_status(self) -> dict:
        """获取队列状态"""
        return {
            "high_priority": len(self.pending_requests.get(1, [])),
            "medium_priority": len(self.pending_requests.get(2, [])),
            "low_priority": len(self.pending_requests.get(3, [])),
            "total_pending": sum(len(reqs) for reqs in self.pending_requests.values()),
        }

    def reset_stats(self) -> Any:
        """重置统计信息"""
        self.stats = BatchStats()
        self._recent_latencies.clear()
        logger.info("统计信息已重置")


# 便捷函数
_batch_processors: dict[str, BatchProcessor] = {}


def get_batch_processor(model_name: str, model: Any = None, **kwargs) -> BatchProcessor:
    """获取或创建批处理器实例"""
    if model_name not in _batch_processors:
        if model is None:
            raise ValueError("首次调用需要提供model参数")

        _batch_processors[model_name] = BatchProcessor(model, **kwargs)

    return _batch_processors[model_name]


async def shutdown_all_batch_processors():
    """关闭所有批处理器"""
    for processor in _batch_processors.values():
        await processor.stop()
    _batch_processors.clear()
