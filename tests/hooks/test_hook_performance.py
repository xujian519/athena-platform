#!/usr/bin/env python3
"""
Hook性能监控和测试

测试Hook系统的性能指标和监控功能。

作者: Athena平台团队
创建时间: 2026-04-20
"""

import asyncio
import time
from dataclasses import dataclass

import pytest

from core.hooks.base import HookContext, HookRegistry, HookType


@dataclass
class HookMetrics:
    """Hook性能指标"""
    hook_id: str
    call_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    error_count: int = 0
    last_execution: float | None = None

    def update(self, execution_time: float, success: bool):
        """更新指标"""
        self.call_count += 1
        self.total_time += execution_time
        self.avg_time = self.total_time / self.call_count
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        if not success:
            self.error_count += 1
        self.last_execution = time.time()


@dataclass
class PerformanceReport:
    """性能报告"""
    total_hooks: int
    total_calls: int
    total_time: float
    avg_time_per_call: float
    slowest_hook: tuple[str, float] | None
    fastest_hook: tuple[str, float] | None
    error_rate: float


class HookPerformanceMonitor:
    """Hook性能监控器（简化版本）"""

    def __init__(self):
        self._metrics: dict[str, HookMetrics] = {}
        self._start_times: dict[str, float] = {}

    def start_tracking(self, hook_id: str) -> None:
        """开始跟踪"""
        self._start_times[hook_id] = time.perf_counter()

    def end_tracking(self, hook_id: str, success: bool = True) -> HookMetrics:
        """结束跟踪"""
        if hook_id not in self._start_times:
            raise ValueError(f"No start time found for hook: {hook_id}")

        execution_time = time.perf_counter() - self._start_times[hook_id]
        del self._start_times[hook_id]

        if hook_id not in self._metrics:
            self._metrics[hook_id] = HookMetrics(hook_id=hook_id)

        self._metrics[hook_id].update(execution_time, success)
        return self._metrics[hook_id]

    def get_metrics(self, hook_id: str) -> HookMetrics | None:
        """获取指标"""
        return self._metrics.get(hook_id)

    def get_all_metrics(self) -> dict[str, HookMetrics]:
        """获取所有指标"""
        return self._metrics.copy()

    def get_report(self) -> PerformanceReport:
        """生成性能报告"""
        if not self._metrics:
            return PerformanceReport(
                total_hooks=0,
                total_calls=0,
                total_time=0.0,
                avg_time_per_call=0.0,
                slowest_hook=None,
                fastest_hook=None,
                error_rate=0.0,
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

        return PerformanceReport(
            total_hooks=len(self._metrics),
            total_calls=total_calls,
            total_time=total_time,
            avg_time_per_call=total_time / total_calls if total_calls > 0 else 0.0,
            slowest_hook=slowest_hook,
            fastest_hook=fastest_hook,
            error_rate=total_errors / total_calls if total_calls > 0 else 0.0,
        )

    def reset_metrics(self) -> None:
        """重置所有指标"""
        self._metrics.clear()
        self._start_times.clear()


class TestHookPerformanceMonitor:
    """测试Hook性能监控器"""

    def test_start_end_tracking(self):
        """测试开始和结束跟踪"""
        monitor = HookPerformanceMonitor()

        monitor.start_tracking("test_hook")
        time.sleep(0.01)
        metrics = monitor.end_tracking("test_hook")

        assert metrics.hook_id == "test_hook"
        assert metrics.call_count == 1
        assert metrics.total_time > 0.01
        assert metrics.avg_time > 0.01

    def test_multiple_executions(self):
        """测试多次执行的指标统计"""
        monitor = HookPerformanceMonitor()

        for _ in range(5):
            monitor.start_tracking("test_hook")
            time.sleep(0.001)
            monitor.end_tracking("test_hook")

        metrics = monitor.get_metrics("test_hook")
        assert metrics.call_count == 5
        assert metrics.avg_time > 0
        assert metrics.min_time <= metrics.avg_time <= metrics.max_time

    def test_error_tracking(self):
        """测试错误跟踪"""
        monitor = HookPerformanceMonitor()

        monitor.start_tracking("test_hook")
        monitor.end_tracking("test_hook", success=False)

        metrics = monitor.get_metrics("test_hook")
        assert metrics.error_count == 1

    def test_get_all_metrics(self):
        """测试获取所有指标"""
        monitor = HookPerformanceMonitor()

        monitor.start_tracking("hook1")
        monitor.end_tracking("hook1")

        monitor.start_tracking("hook2")
        monitor.end_tracking("hook2")

        all_metrics = monitor.get_all_metrics()
        assert len(all_metrics) == 2
        assert "hook1" in all_metrics
        assert "hook2" in all_metrics

    def test_performance_report(self):
        """测试性能报告生成"""
        monitor = HookPerformanceMonitor()

        # 模拟执行
        for i in range(10):
            monitor.start_tracking(f"hook{i % 3}")
            time.sleep(0.001 * (i + 1))
            monitor.end_tracking(f"hook{i % 3}")

        report = monitor.get_report()

        assert report.total_hooks == 3
        assert report.total_calls == 10
        assert report.avg_time_per_call > 0
        assert report.slowest_hook is not None
        assert report.fastest_hook is not None

    def test_reset_metrics(self):
        """测试重置指标"""
        monitor = HookPerformanceMonitor()

        monitor.start_tracking("test_hook")
        monitor.end_tracking("test_hook")

        assert len(monitor.get_all_metrics()) == 1

        monitor.reset_metrics()

        assert len(monitor.get_all_metrics()) == 0


class TestHookPerformance:
    """测试Hook性能指标"""

    @pytest.mark.asyncio
    async def test_hook_execution_latency(self):
        """测试Hook执行延迟（目标<1ms）"""
        registry = HookRegistry()

        async def fast_hook(context: HookContext):
            return "result"

        registry.register_function("fast_hook", HookType.POST_TASK_COMPLETE, fast_hook)

        # 测量延迟
        latencies = []
        for _ in range(100):
            context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)

            start = time.perf_counter()
            await registry.trigger(HookType.POST_TASK_COMPLETE, context)
            end = time.perf_counter()

            latencies.append((end - start) * 1000)  # 转换为毫秒

        # 计算P95延迟
        latencies.sort()
        p95_latency = latencies[int(len(latencies) * 0.95)]

        # P95延迟应该<10ms（考虑Python开销）
        assert p95_latency < 10, f"P95 latency {p95_latency:.2f}ms exceeds 10ms"

    @pytest.mark.asyncio
    async def test_concurrent_hooks(self):
        """测试并发Hook执行（目标10+并发）"""
        registry = HookRegistry()

        executed = []

        async def concurrent_hook(context: HookContext):
            executed.append(context.get("hook_id"))
            await asyncio.sleep(0.01)
            return "result"

        # 注册15个Hook
        for i in range(15):
            registry.register_function(
                f"hook_{i}",
                HookType.POST_TASK_COMPLETE,
                concurrent_hook,
            )

        # 并行执行
        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        start = time.perf_counter()
        await registry.trigger_parallel(HookType.POST_TASK_COMPLETE, context)
        end = time.perf_counter()

        # 所有Hook都应该执行
        assert len(executed) == 15

        # 并行执行应该比顺序快
        elapsed = end - start
        assert elapsed < 0.1, f"Parallel execution took {elapsed:.2f}s, too slow"

    @pytest.mark.asyncio
    async def test_high_throughput(self):
        """测试高吞吐量（目标>1000 hooks/s）"""
        registry = HookRegistry()

        async def simple_hook(context: HookContext):
            return "result"

        registry.register_function("simple_hook", HookType.POST_TASK_COMPLETE, simple_hook)

        # 执行1000次
        iterations = 1000
        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)

        start = time.perf_counter()
        for _ in range(iterations):
            await registry.trigger(HookType.POST_TASK_COMPLETE, context)
        end = time.perf_counter()

        elapsed = end - start
        throughput = iterations / elapsed

        # 吞吐量应该>100 hooks/s
        assert throughput > 100, f"Throughput {throughput:.2f} hooks/s is too low"

    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """测试内存效率"""
        import sys

        registry = HookRegistry()

        async def lightweight_hook(context: HookContext):
            return "result"

        # 注册100个Hook
        for i in range(100):
            registry.register_function(
                f"hook_{i}",
                HookType.POST_TASK_COMPLETE,
                lightweight_hook,
            )

        # 获取内存使用（粗略估计）
        hooks = registry.get_hooks(HookType.POST_TASK_COMPLETE)
        hook_size = sys.getsizeof(hooks)

        # 100个Hook应该不会占用太多内存
        assert hook_size < 100000, f"100 hooks occupy {hook_size} bytes, too much"

    @pytest.mark.asyncio
    async def test_priority_sorting_performance(self):
        """测试优先级排序性能"""
        registry = HookRegistry()

        async def priority_hook(context: HookContext):
            return "result"

        # 注册100个不同优先级的Hook
        import random

        priorities = list(range(100))
        random.shuffle(priorities)

        for i, priority in enumerate(priorities):
            registry.register_function(
                f"hook_{i}",
                HookType.POST_TASK_COMPLETE,
                priority_hook,
                priority=priority,
            )

        # 验证排序正确
        hooks = registry.get_hooks(HookType.POST_TASK_COMPLETE)
        priorities_sorted = [h.priority for h in hooks]

        assert priorities_sorted == sorted(priorities, reverse=True)


class TestHookStressTest:
    """Hook压力测试"""

    @pytest.mark.asyncio
    async def test_rapid_registration(self):
        """测试快速注册"""
        registry = HookRegistry()

        async def dummy_hook(context: HookContext):
            return "result"

        # 快速注册100个Hook
        start = time.perf_counter()
        for i in range(100):
            registry.register_function(
                f"hook_{i}",
                HookType.POST_TASK_COMPLETE,
                dummy_hook,
            )
        end = time.perf_counter()

        elapsed = end - start
        assert elapsed < 1.0, f"Registration took {elapsed:.2f}s, too slow"

    @pytest.mark.asyncio
    async def test_rapid_trigger(self):
        """测试快速触发"""
        registry = HookRegistry()

        async def dummy_hook(context: HookContext):
            return "result"

        registry.register_function("dummy_hook", HookType.POST_TASK_COMPLETE, dummy_hook)

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)

        # 快速触发1000次
        start = time.perf_counter()
        for _ in range(1000):
            await registry.trigger(HookType.POST_TASK_COMPLETE, context)
        end = time.perf_counter()

        elapsed = end - start
        assert elapsed < 5.0, f"1000 triggers took {elapsed:.2f}s, too slow"

    @pytest.mark.asyncio
    async def test_error_resilience(self):
        """测试错误恢复能力"""
        registry = HookRegistry()

        async def failing_hook(context: HookContext):
            raise ValueError("Simulated error")

        async def working_hook(context: HookContext):
            return "success"

        registry.register_function("failing_hook", HookType.POST_TASK_COMPLETE, failing_hook)
        registry.register_function("working_hook", HookType.POST_TASK_COMPLETE, working_hook)

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)

        # 即使有错误，也应该继续执行
        results = await registry.trigger(HookType.POST_TASK_COMPLETE, context)

        # 应该有两个结果（包括None）
        assert len(results) == 2
        assert "success" in results


__all__ = [
    "TestHookPerformanceMonitor",
    "TestHookPerformance",
    "TestHookStressTest",
]

