#!/usruj/bin/env python3
"""
Hook性能监控器

监控和跟踪Hook的性能指标。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

import asyncio
import logging
import statistics
import time
from typing import Any

from .types import BenchmarkResult, HookMetrics, PerformanceReport

logger = logging.getLogger(__name__)


class HookPerformanceMonitor:
    """Hook性能监控器

    跟踪Hook的执行时间和性能指标。
    """

    def __init__(self):
        """初始化性能监控器"""
        self._metrics: dict[str, HookMetrics] = {}
        self._start_times: dict[str, float] = {}
        self._lock = asyncio.Lock()

        logger.info("📊 HookPerformanceMonitor初始化完成")

    async def start_tracking(self, hook_id: str) -> None:
        """开始跟踪Hook性能

        Args:
            hook_id: Hook ID
        """
        async with self._lock:
            self._start_times[hook_id] = time.perf_counter()

    async def end_tracking(
        self, hook_id: str, success: bool = True
    ) -> HookMetrics | None:
        """结束跟踪并返回指标

        Args:
            hook_id: Hook ID
            success: 是否成功

        Returns:
            HookMetrics | None: 性能指标
        """
        async with self._lock:
            if hook_id not in self._start_times:
                logger.warning(f"⚠️ 未找到开始时间: {hook_id}")
                return None

            execution_time = time.perf_counter() - self._start_times[hook_id]
            del self._start_times[hook_id]

            if hook_id not in self._metrics:
                self._metrics[hook_id] = HookMetrics(hook_id=hook_id)

            self._metrics[hook_id].update(execution_time, success)
            return self._metrics[hook_id]

    async def get_metrics(self, hook_id: str) -> HookMetrics | None:
        """获取Hook性能指标

        Args:
            hook_id: Hook ID

        Returns:
            HookMetrics | None: 性能指标
        """
        async with self._lock:
            return self._metrics.get(hook_id)

    async def get_all_metrics(self) -> dict[str, HookMetrics]:
        """获取所有Hook的性能指标

        Returns:
            dict[str, HookMetrics]: Hook ID到指标的映射
        """
        async with self._lock:
            return self._metrics.copy()

    async def get_report(self) -> PerformanceReport:
        """生成性能报告

        Returns:
            PerformanceReport: 性能报告
        """
        async with self._lock:
            if not self._metrics:
                return PerformanceReport(
                    total_hooks=0,
                    total_calls=0,
                    total_time=0.0,
                    avg_time_per_call=0.0,
                    slowest_hook=None,
                    fastest_hook=None,
                    error_rate=0.0,
                    throughput=0.0,
                )

            total_calls = sum(m.call_count for m in self._metrics.values())
            total_time = sum(m.total_time for m in self._metrics.values())
            total_errors = sum(m.error_count for m in self._metrics.values())

            # 找出最慢和最快的Hook
            slowest_hook = None
            fastest_hook = None

            for hook_id, metrics in self._metrics.items():
                if metrics.call_count > 0:
                    if slowest_hook is None or metrics.max_time > slowest_hook[1]:
                        slowest_hook = (hook_id, metrics.max_time)
                    if fastest_hook is None or metrics.min_time < fastest_hook[1]:
                        fastest_hook = (hook_id, metrics.min_time)

            # 计算吞吐量
            throughput = total_calls / total_time if total_time > 0 else 0.0

            return PerformanceReport(
                total_hooks=len(self._metrics),
                total_calls=total_calls,
                total_time=total_time,
                avg_time_per_call=total_time / total_calls if total_calls > 0 else 0.0,
                slowest_hook=slowest_hook,
                fastest_hook=fastest_hook,
                error_rate=total_errors / total_calls if total_calls > 0 else 0.0,
                throughput=throughput,
            )

    async def reset_metrics(self, hook_id: str | None = None) -> None:
        """重置性能指标

        Args:
            hook_id: Hook ID，None表示重置所有
        """
        async with self._lock:
            if hook_id:
                self._metrics.pop(hook_id, None)
                logger.info(f"🔄 Hook指标已重置: {hook_id}")
            else:
                self._metrics.clear()
                self._start_times.clear()
                logger.info("🔄 所有Hook指标已重置")

    async def benchmark(
        self,
        hook_id: str,
        hook_func,
        iterations: int = 1000,
        warmup: int = 100,
    ) -> BenchmarkResult:
        """性能基准测试

        Args:
            hook_id: Hook ID
            hook_func: Hook函数
            iterations: 迭代次数
            warmup: 预热次数

        Returns:
            BenchmarkResult: 基准测试结果
        """
        logger.info(f"🚀 开始基准测试: {hook_id} ({iterations}次迭代)")

        # 预热
        for _ in range(warmup):
            if asyncio.iscoroutinefunction(hook_func):
                await hook_func()
            else:
                hook_func()

        # 正式测试
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            if asyncio.iscoroutinefunction(hook_func):
                await hook_func()
            else:
                hook_func()

            end = time.perf_counter()
            times.append(end - start)

        # 计算统计指标
        total_time = sum(times)
        avg_time = total_time / iterations
        min_time = min(times)
        max_time = max(times)

        sorted_times = sorted(times)
        p50_time = sorted_times[int(len(times) * 0.5)]
        p95_time = sorted_times[int(len(times) * 0.95)]
        p99_time = sorted_times[int(len(times) * 0.99)]

        throughput = iterations / total_time if total_time > 0 else 0.0

        result = BenchmarkResult(
            hook_id=hook_id,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            p50_time=p50_time,
            p95_time=p95_time,
            p99_time=p99_time,
            throughput=throughput,
        )

        logger.info(
            f"✅ 基准测试完成: {hook_id} - "
            f"平均{avg_time*1000:.3f}ms, "
            f"P95{p95_time*1000:.3f}ms, "
            f"吞吐量{throughput:.2f}ops/s"
        )

        return result


__all__ = [
    "HookPerformanceMonitor",
]
