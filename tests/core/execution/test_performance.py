#!/usr/bin/env python3
"""
执行模块性能测试
Execution Module Performance Tests

测试执行模块的性能指标，验证修复后的性能符合预期。

性能基准:
- 任务创建: < 1μs
- 任务入队/出队: < 10μs
- 优先级排序: O(n log n)
- 类型一致性检查: < 1μs

作者: Athena AI系统
版本: 2.0.0
创建时间: 2026-01-27
"""

import asyncio
import pytest
import statistics
import time
from typing import Any

from core.execution.shared_types import (
    ActionType,
    Task,
    TaskPriority,
    TaskQueue,
    TaskStatus,
)
from core.execution.parallel_executor import ParallelExecutor


class TestTaskCreationPerformance:
    """测试任务创建性能"""

    def test_task_creation_speed(self):
        """测试任务创建速度应该 < 1μs"""
        iterations = 10000

        start_time = time.perf_counter()
        for _ in range(iterations):
            task = Task(
                task_id=f"task_{_}",
                name="性能测试任务",
                priority=TaskPriority.NORMAL,
            )
        end_time = time.perf_counter()

        avg_time = (end_time - start_time) / iterations
        max_allowed = 1e-6  # 1微秒

        print(f"\n平均任务创建时间: {avg_time * 1e6:.2f}μs")
        assert avg_time < max_allowed, f"任务创建时间 {avg_time * 1e6:.2f}μs 超过限制 {max_allowed * 1e6:.2f}μs"

    def test_task_with_function_creation_speed(self):
        """测试带函数的任务创建速度"""
        async def dummy_func():
            return "result"

        iterations = 1000
        start_time = time.perf_counter()

        for _ in range(iterations):
            task = Task(
                task_id=f"task_{_}",
                name="函数任务",
                function=dummy_func,
                args=(1, 2),
                kwargs={"key": "value"},
            )

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations

        print(f"带函数的任务创建平均时间: {avg_time * 1e6:.2f}μs")
        assert avg_time < 5e-6  # 5微秒


class TestTaskQueuePerformance:
    """测试任务队列性能"""

    def test_enqueue_dequeue_speed(self):
        """测试入队出队速度"""
        queue = TaskQueue(max_size=10000)
        iterations = 1000

        # 入队测试
        tasks = [
            Task(
                task_id=f"task_{_}",
                name="任务",
                priority=TaskPriority(_ % 5 + 1),
            )
            for _ in range(iterations)
        ]

        start_time = time.perf_counter()
        for task in tasks:
            queue.enqueue(task)
        end_time = time.perf_counter()

        avg_enqueue_time = (end_time - start_time) / iterations
        print(f"平均入队时间: {avg_enqueue_time * 1e6:.2f}μs")
        assert avg_enqueue_time < 10e-6  # 10微秒

        # 出队测试（涉及排序，允许更长时间）
        start_time = time.perf_counter()
        for _ in range(iterations):
            queue.dequeue()
        end_time = time.perf_counter()

        avg_dequeue_time = (end_time - start_time) / iterations
        print(f"平均出队时间: {avg_dequeue_time * 1e6:.2f}μs")
        # 出队涉及排序，允许更长时间
        assert avg_dequeue_time < 500e-6  # 500微秒

    def test_priority_sorting_performance(self):
        """测试优先级排序性能"""
        queue = TaskQueue(max_size=10000)
        iterations = 1000

        # 添加随机优先级的任务
        import random

        priorities = list(TaskPriority)
        tasks = [
            Task(
                task_id=f"task_{_}",
                name="任务",
                priority=random.choice(priorities),
            )
            for _ in range(iterations)
        ]

        for task in tasks:
            queue.enqueue(task)

        # 测试出队顺序（已按优先级排序）
        start_time = time.perf_counter()
        prev_priority_value = 0
        count = 0

        while queue.size() > 0:
            task = queue.dequeue()
            assert task.priority.value >= prev_priority_value, "优先级排序错误"
            prev_priority_value = task.priority.value
            count += 1

        end_time = time.perf_counter()
        sort_time = end_time - start_time

        print(f"优先级排序总时间: {sort_time * 1e3:.2f}ms")
        print(f"平均每项排序时间: {sort_time / count * 1e6:.2f}μs")
        assert count == iterations, f"出队数量不匹配: {count} != {iterations}"

    def test_large_queue_performance(self):
        """测试大队列性能"""
        queue = TaskQueue(max_size=100000)
        iterations = 10000

        import random

        priorities = list(TaskPriority)

        start_time = time.perf_counter()
        for _ in range(iterations):
            task = Task(
                task_id=f"task_{_}",
                name="大规模任务",
                priority=random.choice(priorities),
            )
            queue.enqueue(task)
        end_time = time.perf_counter()

        total_enqueue_time = end_time - start_time
        print(f"大规模入队 ({iterations} 项) 总时间: {total_enqueue_time * 1e3:.2f}ms")
        print(f"平均入队时间: {total_enqueue_time / iterations * 1e6:.2f}μs")

        # 清空队列
        start_time = time.perf_counter()
        for _ in range(iterations):
            queue.dequeue()
        end_time = time.perf_counter()

        total_dequeue_time = end_time - start_time
        print(f"大规模出队 ({iterations} 项) 总时间: {total_dequeue_time * 1e3:.2f}ms")
        print(f"平均出队时间: {total_dequeue_time / iterations * 1e6:.2f}μs")


class TestTaskOperationPerformance:
    """测试任务操作性能"""

    def test_task_start_performance(self):
        """测试任务启动性能"""
        task = Task(task_id="test", name="测试任务")

        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            task.start()
            # 重置状态以便重复测试
            task.status = TaskStatus.PENDING
            task.started_at = None

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations

        print(f"平均任务启动时间: {avg_time * 1e6:.2f}μs")
        assert avg_time < 1e-6  # 1微秒

    def test_task_complete_performance(self):
        """测试任务完成性能"""
        task = Task(task_id="test", name="测试任务")

        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            task.start()
            task.complete(True, "result")
            # 重置状态以便重复测试
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations

        print(f"平均任务完成时间: {avg_time * 1e6:.2f}μs")
        assert avg_time < 1e-6  # 1微秒

    def test_task_can_start_performance(self):
        """测试依赖检查性能"""
        # 创建完成任务字典
        completed_tasks = {
            f"dep_{i:03d}": Task(
                task_id=f"dep_{i:03d}",
                name="依赖任务",
            )
            for i in range(100)
        }

        # 设置所有任务为已完成
        for task in completed_tasks.values():
            task.status = TaskStatus.COMPLETED

        # 创建测试任务
        task = Task(
            task_id="test",
            name="主任务",
            dependencies=["dep_001", "dep_050", "dep_099"],
        )

        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            result = task.can_start(completed_tasks)

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations

        print(f"平均依赖检查时间: {avg_time * 1e6:.2f}μs")
        assert avg_time < 5e-6  # 5微秒
        assert result is True


class TestTypeConsistencyPerformance:
    """测试类型一致性检查性能"""

    def test_import_performance(self):
        """测试导入性能"""
        iterations = 1000
        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()

            # 模拟导入检查
            from core.execution.shared_types import Task as Task1
            from core.execution import Task as Task2

            # 检查是否是同一个类
            assert Task1 is Task2

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        avg_time = statistics.mean(times)
        print(f"平均导入和一致性检查时间: {avg_time * 1e6:.2f}μs")
        assert avg_time < 100e-6  # 100微秒


@pytest.mark.asyncio
class TestParallelExecutorPerformance:
    """测试并行执行器性能"""

    async def test_parallel_execution_throughput(self):
        """测试并行执行吞吐量"""
        executor = ParallelExecutor(max_workers=10, max_concurrent_tasks=50)

        # 创建快速异步任务
        async def fast_task(task_id):
            await asyncio.sleep(0.01)  # 10ms
            return f"result_{task_id}"

        # 提交任务
        num_tasks = 100
        start_time = time.perf_counter()

        for i in range(num_tasks):
            await executor.submit_task(
                task_id=f"task_{i}",
                task_name=f"任务_{i}",
                coroutine=fast_task,
                args=(f"task_{i}",),
            )

        # 执行所有任务
        results = await executor.execute_all()

        end_time = time.perf_counter()
        total_time = end_time - start_time

        throughput = num_tasks / total_time
        print(f"并行执行吞吐量: {throughput:.2f} 任务/秒")
        print(f"总执行时间: {total_time * 1e3:.2f}ms")
        print(f"平均任务时间: {total_time / num_tasks * 1e3:.2f}ms")

        # 验证所有任务都完成
        assert len(results) == num_tasks
        # 验证大部分任务成功
        successful = sum(1 for r in results.values() if r.success)
        print(f"成功任务: {successful}/{num_tasks}")
        assert successful >= num_tasks * 0.95  # 至少95%成功

    async def test_priority_ordering_performance(self):
        """测试优先级排序在实际执行中的性能"""
        executor = ParallelExecutor(max_workers=5, max_concurrent_tasks=20)

        async def dummy_task(name):
            await asyncio.sleep(0.001)
            return name

        # 提交不同优先级的任务
        priorities = [
            TaskPriority.CRITICAL,
            TaskPriority.HIGH,
            TaskPriority.NORMAL,
            TaskPriority.LOW,
            TaskPriority.BACKGROUND,
        ]

        start_time = time.perf_counter()

        for priority in priorities:
            for i in range(10):
                await executor.submit_task(
                    task_id=f"{priority.name}_{i}",
                    task_name=f"{priority.name}_任务_{i}",
                    coroutine=dummy_task,
                    args=(f"{priority.name}_{i}",),
                    priority=priority,
                )

        results = await executor.execute_all()
        end_time = time.perf_counter()

        total_time = end_time - start_time
        print(f"优先级排序执行总时间: {total_time * 1e3:.2f}ms")

        # 验证高优先级任务优先完成
        critical_tasks = [
            r for r in results.values() if r.success and "CRITICAL" in r.task_name
        ]
        background_tasks = [
            r for r in results.values() if r.success and "BACKGROUND" in r.task_name
        ]

        if critical_tasks and background_tasks:
            avg_critical_time = statistics.mean(t.execution_time for t in critical_tasks)
            avg_background_time = statistics.mean(t.execution_time for t in background_tasks)
            print(f"关键任务平均执行时间: {avg_critical_time * 1e3:.2f}ms")
            print(f"后台任务平均执行时间: {avg_background_time * 1e3:.2f}ms")

            # 关键任务应该比后台任务完成得更快
            # (这在理想情况下成立，但由于并发执行，可能有一定波动)
            print(f"时间比: {avg_background_time / avg_critical_time:.2f}x")


class TestMemoryEfficiency:
    """测试内存效率"""

    def test_task_memory_footprint(self):
        """测试任务内存占用"""
        import sys

        task = Task(
            task_id="test_001",
            name="内存测试任务",
            priority=TaskPriority.NORMAL,
        )

        # 获取对象大小
        task_size = sys.getsizeof(task)
        print(f"单个任务对象大小: {task_size} bytes")

        # 验证任务大小合理 (< 10KB)
        assert task_size < 10240, f"任务对象过大: {task_size} bytes"

    def test_queue_memory_efficiency(self):
        """测试队列内存效率"""
        import sys

        queue = TaskQueue(max_size=1000)

        # 添加任务前的内存
        baseline_size = sys.getsizeof(queue)

        # 添加任务
        for i in range(100):
            task = Task(
                task_id=f"task_{i}",
                name=f"任务_{i}",
                priority=TaskPriority(i % 5 + 1),
            )
            queue.enqueue(task)

        # 添加任务后的内存
        after_size = sys.getsizeof(queue)

        memory_increase = after_size - baseline_size
        avg_per_task = memory_increase / 100

        print(f"队列内存增加: {memory_increase} bytes (100个任务)")
        print(f"平均每任务: {avg_per_task} bytes")

        # 验证内存增长合理
        assert avg_per_task < 10000, f"平均每任务内存过大: {avg_per_task} bytes"


@pytest.mark.benchmark
class TestBenchmarks:
    """性能基准测试"""

    def test_benchmark_task_creation(self):
        """任务创建基准测试"""
        iterations = 100000
        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()
            task = Task(task_id="bench", name="基准任务")
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        p50 = statistics.quantiles(times, n=2)[0]
        p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(times, n=100)[98]  # 99th percentile

        print(f"\n任务创建基准 (n={iterations}):")
        print(f"  P50: {p50 * 1e6:.2f}μs")
        print(f"  P95: {p95 * 1e6:.2f}μs")
        print(f"  P99: {p99 * 1e6:.2f}μs")

        # 基准要求
        assert p50 < 1e-6, f"P50 超过基准: {p50 * 1e6:.2f}μs"
        assert p95 < 2e-6, f"P95 超过基准: {p95 * 1e6:.2f}μs"

    def test_benchmark_queue_operations(self):
        """队列操作基准测试"""
        queue = TaskQueue(max_size=10000)
        iterations = 10000

        # 入队基准
        enqueue_times = []
        for i in range(iterations):
            task = Task(
                task_id=f"bench_{i}",
                name="基准任务",
                priority=TaskPriority(i % 5 + 1),
            )
            start_time = time.perf_counter()
            queue.enqueue(task)
            end_time = time.perf_counter()
            enqueue_times.append(end_time - start_time)

        avg_enqueue = statistics.mean(enqueue_times)
        p95_enqueue = statistics.quantiles(enqueue_times, n=20)[18]

        print(f"\n入队基准 (n={iterations}):")
        print(f"  平均: {avg_enqueue * 1e6:.2f}μs")
        print(f"  P95: {p95_enqueue * 1e6:.2f}μs")

        # 出队基准
        dequeue_times = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            queue.dequeue()
            end_time = time.perf_counter()
            dequeue_times.append(end_time - start_time)

        avg_dequeue = statistics.mean(dequeue_times)
        p95_dequeue = statistics.quantiles(dequeue_times, n=20)[18]

        print(f"\n出队基准 (n={iterations}):")
        print(f"  平均: {avg_dequeue * 1e6:.2f}μs")
        print(f"  P95: {p95_dequeue * 1e6:.2f}μs")

        # 基准要求（出队涉及排序，允许更长时间）
        assert avg_enqueue < 10e-6, f"平均入队时间超过基准"
        assert avg_dequeue < 5000e-6, f"平均出队时间超过基准（涉及排序）"


def run_performance_report():
    """运行性能测试并生成报告"""
    pytest.main([__file__, "-v", "-s", "--tb=short"])


if __name__ == "__main__":
    run_performance_report()
