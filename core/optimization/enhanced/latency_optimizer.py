#!/usr/bin/env python3
"""
P99延迟优化器 (P99 Latency Optimizer)
专注于减少长尾延迟,优化P99性能指标

作者: 小诺·双鱼公主
版本: v2.0.0
优化目标: P99延迟 250ms → 175ms
"""

import asyncio
import heapq
import logging
import statistics
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PriorityLevel(str, Enum):
    """优先级级别"""

    CRITICAL = "critical"  # 关键请求,最高优先级
    HIGH = "high"  # 高优先级
    NORMAL = "normal"  # 正常优先级
    LOW = "low"  # 低优先级,可延后处理


class RequestType(str, Enum):
    """请求类型"""

    REALTIME = "realtime"  # 实时请求
    BATCH = "batch"  # 批量请求
    BACKGROUND = "background"  # 后台任务
    STREAMING = "streaming"  # 流式请求


@dataclass(order=True)
class PriorityRequest:
    """优先级请求"""

    priority: int  # 用于堆排序(越小优先级越高)
    request_id: str = field(compare=False)
    request_type: RequestType = field(compare=False)
    payload: dict[str, Any] = field(compare=False)
    created_at: datetime = field(compare=False)
    timeout_ms: int = field(compare=False, default=5000)
    metadata: dict[str, Any] = field(compare=False, default_factory=dict)

    def __post_init__(self):
        """创建后初始化优先级"""
        if self.priority == 0:
            # 根据请求类型设置默认优先级
            priority_map = {
                RequestType.REALTIME: 1,
                RequestType.STREAMING: 2,
                RequestType.BATCH: 5,
                RequestType.BACKGROUND: 10,
            }
            self.priority = priority_map.get(self.request_type, 5)


@dataclass
class LatencyMetric:
    """延迟指标"""

    p50: float  # 中位数延迟
    p75: float  # 75分位延迟
    p90: float  # 90分位延迟
    p95: float  # 95分位延迟
    p99: float  # 99分位延迟
    avg: float  # 平均延迟
    min: float  # 最小延迟
    max: float  # 最大延迟
    count: int  # 样本数量


@dataclass
class OptimizationResult:
    """优化结果"""

    request_id: str
    original_latency_ms: float
    optimized_latency_ms: float
    improvement_pct: float
    optimization_techniques: list[str]
    timestamp: datetime


class P99LatencyOptimizer:
    """
    P99延迟优化器

    功能:
    1. 优先级队列调度
    2. 请求批处理
    3. 快速路径优化
    4. 模型预热
    5. 超时控制
    6. 延迟监控和预测
    """

    def __init__(self, p99_target_ms: float = 175.0):
        self.name = "P99延迟优化器"
        self.version = "2.0.0"
        self.p99_target_ms = p99_target_ms

        # 优先级队列
        self.priority_queue: list[PriorityRequest] = []
        self.queue_lock = asyncio.Lock()

        # 延迟历史(用于监控和分析)
        self.latency_history: deque = deque(maxlen=1000)

        # 请求批处理缓冲区
        self.batch_buffer: dict[RequestType, list[PriorityRequest]] = defaultdict(list)

        # 模型预热状态
        self.prewarmed_models: dict[str, datetime] = {}

        # 快速路径缓存
        self.fast_path_cache: dict[str, tuple[Any, datetime]] = {}

        # 优化结果历史
        self.optimization_history: list[OptimizationResult] = []

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "fast_path_hits": 0,
            "batch_processed": 0,
            "timeouts": 0,
            "p99_before": 250.0,
            "p99_after": 0.0,
            "improvement_rate": 0.0,
        }

        logger.info(f"✅ {self.name} 初始化完成 (目标P99: {p99_target_ms}ms)")

    async def process_request(
        self,
        request_id: str,
        handler: Callable,
        request_type: RequestType = RequestType.BATCH,
        priority: PriorityLevel = PriorityLevel.NORMAL,
        **kwargs,
    ) -> dict[str, Any]:
        """
        处理请求(应用延迟优化)

        Args:
            request_id: 请求ID
            handler: 处理函数
            request_type: 请求类型
            priority: 优先级
            **kwargs: 请求参数

        Returns:
            处理结果
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        # 1. 尝试快速路径
        fast_path_result = await self._try_fast_path(request_id, kwargs)
        if fast_path_result is not None:
            self.stats["fast_path_hits"] += 1
            latency_ms = (time.time() - start_time) * 1000
            self._record_latency(latency_ms)
            return fast_path_result

        # 2. 检查是否可以批处理
        if request_type in [RequestType.BATCH, RequestType.BACKGROUND]:
            batch_result = await self._try_batch_processing(
                request_id, handler, request_type, kwargs
            )
            if batch_result is not None:
                self.stats["batch_processed"] += 1
                latency_ms = (time.time() - start_time) * 1000
                self._record_latency(latency_ms)
                return batch_result

        # 3. 正常处理路径(带超时控制)
        timeout_ms = kwargs.get("timeout_ms", 5000)
        result = await self._execute_with_timeout(handler, timeout_ms / 1000, **kwargs)

        latency_ms = (time.time() - start_time) * 1000
        self._record_latency(latency_ms)

        # 4. 如果结果可缓存,更新快速路径缓存
        if self._is_cacheable(kwargs):
            self._update_fast_path_cache(request_id, result)

        return result

    async def _try_fast_path(
        self, request_id: str, params: dict[str, Any]
    ) -> dict[str, Any] | None:
        """尝试快速路径(缓存命中)"""
        cache_key = self._generate_cache_key(params)

        if cache_key in self.fast_path_cache:
            result, cached_at = self.fast_path_cache[cache_key]
            cache_age = (datetime.now() - cached_at).total_seconds()

            # 缓存有效期5分钟
            if cache_age < 300:
                logger.debug(f"✨ 快速路径命中: {cache_key}")
                return result
            else:
                # 缓存过期,删除
                del self.fast_path_cache[cache_key]

        return None

    async def _try_batch_processing(
        self, request_id: str, handler: Callable, request_type: RequestType, params: dict[str, Any]
    ) -> dict[str, Any] | None:
        """尝试批处理"""
        # 添加到批处理缓冲区
        self.batch_buffer[request_type].append(
            PriorityRequest(
                priority=0,
                request_id=request_id,
                request_type=request_type,
                payload=params,
                created_at=datetime.now(),
            )
        )

        # 批次大小阈值
        batch_size = len(self.batch_buffer[request_type])
        if batch_size >= 10:  # 10个请求一批
            # 执行批处理
            batch_requests = self.batch_buffer[request_type]
            self.batch_buffer[request_type].clear()

            logger.info(f"🔄 批处理 {batch_size} 个 {request_type} 请求")

            # 并发执行
            tasks = [handler(req.payload) for req in batch_requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 返回当前请求的结果
            for i, req in enumerate(batch_requests):
                if req.request_id == request_id:
                    if isinstance(results[i], Exception):
                        raise results[i]
                    return results[i]

        return None

    async def _execute_with_timeout(
        self, handler: Callable, timeout_seconds: float, **kwargs
    ) -> dict[str, Any]:
        """执行处理函数(带超时控制)"""
        try:
            async with asyncio.timeout(timeout_seconds):
                if asyncio.iscoroutinefunction(handler):
                    return await handler(**kwargs)
                else:
                    return handler(**kwargs)
        except asyncio.TimeoutError:
            self.stats["timeouts"] += 1
            logger.warning(f"⏱️ 请求超时 ({timeout_seconds}s)")
            raise

    def _generate_cache_key(self, params: dict[str, Any]) -> str:
        """生成缓存键"""
        # 简化版:基于参数生成键
        key_parts = []
        for k in sorted(params.keys()):
            key_parts.append(f"{k}={params[k]}")
        return "|".join(key_parts)

    def _is_cacheable(self, params: dict[str, Any]) -> bool:
        """判断请求是否可缓存"""
        # 只缓存只读操作
        operation = params.get("operation", "")
        return operation in ["query", "search", "get", "list"]

    def _update_fast_path_cache(self, request_id: str, result: Any) -> Any:
        """更新快速路径缓存"""
        # 简化版:直接使用request_id作为键
        self.fast_path_cache[request_id] = (result, datetime.now())

    def _record_latency(self, latency_ms: float) -> Any:
        """记录延迟"""
        self.latency_history.append(latency_ms)

    async def prewarm_models(self, model_ids: list[str]):
        """
        预热模型

        预热可以减少首次请求的延迟,改善P99性能
        """
        logger.info(f"🔥 预热 {len(model_ids)} 个模型...")

        for model_id in model_ids:
            # 模拟预热过程
            await asyncio.sleep(0.1)
            self.prewarmed_models[model_id] = datetime.now()
            logger.debug(f"  ✅ {model_id} 已预热")

        logger.info("✅ 模型预热完成")

    async def prioritize_request(
        self,
        request_id: str,
        request_type: RequestType,
        priority: PriorityLevel,
        payload: dict[str, Any],    ):
        """
        将请求加入优先级队列

        Args:
            request_id: 请求ID
            request_type: 请求类型
            priority: 优先级
            payload: 请求负载
        """
        priority_value = {
            PriorityLevel.CRITICAL: 1,
            PriorityLevel.HIGH: 3,
            PriorityLevel.NORMAL: 5,
            PriorityLevel.LOW: 10,
        }[priority]

        request = PriorityRequest(
            priority=priority_value,
            request_id=request_id,
            request_type=request_type,
            payload=payload,
            created_at=datetime.now(),
        )

        async with self.queue_lock:
            heapq.heappush(self.priority_queue, request)

        logger.debug(f"📤 请求加入队列: {request_id} (优先级: {priority.value})")

    async def process_next_priority_request(self) -> dict[str, Any] | None:
        """处理下一个高优先级请求"""
        async with self.queue_lock:
            if not self.priority_queue:
                return None

            request = heapq.heappop(self.priority_queue)

        logger.info(f"📥 处理优先级请求: {request.request_id}")

        # 返回请求信息供上层处理
        return {
            "request_id": request.request_id,
            "type": request.request_type,
            "payload": request.payload,
        }

    def get_latency_metrics(self) -> LatencyMetric:
        """获取延迟指标"""
        if not self.latency_history:
            return LatencyMetric(0, 0, 0, 0, 0, 0, 0, 0, 0)

        latencies = list(self.latency_history)
        sorted_latencies = sorted(latencies)

        n = len(sorted_latencies)

        return LatencyMetric(
            p50=sorted_latencies[int(n * 0.5)],
            p75=sorted_latencies[int(n * 0.75)],
            p90=sorted_latencies[int(n * 0.9)],
            p95=sorted_latencies[int(n * 0.95)],
            p99=sorted_latencies[min(int(n * 0.99), n - 1)],
            avg=statistics.mean(latencies),
            min=min(latencies),
            max=max(latencies),
            count=n,
        )

    def is_p99_target_met(self) -> bool:
        """检查P99目标是否达成"""
        metrics = self.get_latency_metrics()
        return metrics.p99 <= self.p99_target_ms

    def get_improvement_rate(self) -> float:
        """获取改进率"""
        metrics = self.get_latency_metrics()
        if metrics.p99 > 0:
            return (self.stats["p99_before"] - metrics.p99) / self.stats["p99_before"] * 100
        return 0.0

    def get_optimization_report(self) -> dict[str, Any]:
        """获取优化报告"""
        metrics = self.get_latency_metrics()
        improvement_rate = self.get_improvement_rate()

        # 计算目标达成度
        target_progress = (
            (self.stats["p99_before"] - metrics.p99)
            / (self.stats["p99_before"] - self.p99_target_ms)
            * 100
        )

        return {
            "name": self.name,
            "version": self.version,
            "target": {
                "p99_before_ms": self.stats["p99_before"],
                "p99_target_ms": self.p99_target_ms,
                "p99_current_ms": metrics.p99,
            },
            "metrics": {
                "p50_ms": metrics.p50,
                "p75_ms": metrics.p75,
                "p90_ms": metrics.p90,
                "p95_ms": metrics.p95,
                "p99_ms": metrics.p99,
                "avg_ms": metrics.avg,
            },
            "progress": {
                "improvement_rate_pct": improvement_rate,
                "target_progress_pct": min(100, target_progress),
                "target_met": self.is_p99_target_met(),
            },
            "optimization_techniques": {
                "fast_path_hits": self.stats["fast_path_hits"],
                "batch_processed": self.stats["batch_processed"],
                "prewarmed_models": len(self.prewarmed_models),
                "cache_size": len(self.fast_path_cache),
                "queue_size": len(self.priority_queue),
            },
            "stats": self.stats,
        }


# 全局单例
_latency_optimizer_instance: P99LatencyOptimizer | None = None


def get_p99_latency_optimizer() -> P99LatencyOptimizer:
    """获取P99延迟优化器实例"""
    global _latency_optimizer_instance
    if _latency_optimizer_instance is None:
        _latency_optimizer_instance = P99LatencyOptimizer()
    return _latency_optimizer_instance
