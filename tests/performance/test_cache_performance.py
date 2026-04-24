#!/usr/bin/env python3
"""
多级缓存性能基准测试 - Phase 2.2架构优化

Multi-Level Cache Performance Benchmark

性能指标:
- 吞吐量（OPS）
- 平均延迟（P50, P95, P99）
- 缓存命中率
- 内存占用

运行:
    pytest tests/performance/test_cache_performance.py -v -s
    python tests/performance/test_cache_performance.py

作者: Athena平台团队
创建时间: 2026-04-24
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path
from statistics import mean

import pytest

# 导入被测试模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.context_management.cache import CacheConfig, MultiLevelCacheManager


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self, name: str):
        self.name = name
        self.latencies: list[float] = []
        self.errors = 0
        self.start_time = 0
        self.end_time = 0

    def record(self, latency_ms: float, success: bool = True):
        """记录一次操作"""
        if success:
            self.latencies.append(latency_ms)
        else:
            self.errors += 1

    @property
    def total_operations(self) -> int:
        return len(self.latencies) + self.errors

    @property
    def success_rate(self) -> float:
        if self.total_operations == 0:
            return 0.0
        return len(self.latencies) / self.total_operations

    @property
    def throughput_ops(self) -> float:
        """吞吐量（操作/秒）"""
        duration = self.end_time - self.start_time
        if duration == 0:
            return 0.0
        return self.total_operations / duration

    @property
    def avg_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return mean(self.latencies)

    @property
    def p50_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        return sorted_latencies[len(sorted_latencies) // 2]

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    def report(self) -> str:
        """生成性能报告"""
        return f"""
{self.name} 性能报告:
  总操作数: {self.total_operations}
  成功率: {self.success_rate:.2%}
  吞吐量: {self.throughput_ops:.2f} OPS
  平均延迟: {self.avg_latency_ms:.4f} ms
  P50延迟: {self.p50_latency_ms:.4f} ms
  P95延迟: {self.p95_latency_ms:.4f} ms
  P99延迟: {self.p99_latency_ms:.4f} ms
  错误数: {self.errors}
"""


async def benchmark_single_get(
    manager: MultiLevelCacheManager, key: str
) -> tuple[float, bool]:
    """单次GET操作基准测试"""
    start = time.time()
    try:
        await manager.get(key)
        latency = (time.time() - start) * 1000  # 转换为毫秒
        return latency, True
    except Exception:
        return (time.time() - start) * 1000, False


async def benchmark_single_set(
    manager: MultiLevelCacheManager, key: str, value
) -> tuple[float, bool]:
    """单次SET操作基准测试"""
    start = time.time()
    try:
        await manager.set(key, value)
        latency = (time.time() - start) * 1000
        return latency, True
    except Exception:
        return (time.time() - start) * 1000, False


@pytest.mark.asyncio
async def test_read_performance():
    """读取性能测试"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        config = CacheConfig(
            l1_capacity=1000,
            l2_enabled=False,
            l3_db_path=db_path,
        )
        manager = MultiLevelCacheManager(config=config)

        # 预热缓存
        print("\n预热缓存...")
        warmup_data = {f"key_{i}": f"value_{i}" for i in range(100)}
        await manager.warm_up(warmup_data)

        # L1命中测试
        print("\n测试L1缓存命中性能...")
        l1_metrics = PerformanceMetrics("L1缓存命中")
        l1_metrics.start_time = time.time()

        for _ in range(10000):
            key = f"key_{_ % 100}"
            latency, success = await benchmark_single_get(manager, key)
            l1_metrics.record(latency, success)

        l1_metrics.end_time = time.time()

        # 获取统计信息
        stats = await manager.get_full_statistics()
        l1_hit_rate = stats["manager"]["l1_hit_rate"]

        print(l1_metrics.report())
        print(f"L1命中率: {l1_hit_rate:.2%}")

        # 清理
        await manager.close()

        # 验证目标
        assert l1_hit_rate > 0.7, f"L1命中率应>70%，实际: {l1_hit_rate:.2%}"
        assert l1_metrics.avg_latency_ms < 1.0, f"平均延迟应<1ms，实际: {l1_metrics.avg_latency_ms:.4f}ms"

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_write_performance():
    """写入性能测试"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        config = CacheConfig(
            l1_capacity=10000,
            l2_enabled=False,
            l3_db_path=db_path,
        )
        manager = MultiLevelCacheManager(config=config)

        print("\n测试写入性能...")
        write_metrics = PerformanceMetrics("写入操作")
        write_metrics.start_time = time.time()

        for i in range(1000):
            key = f"key_{i}"
            value = {"data": f"value_{i}", "index": i}
            latency, success = await benchmark_single_set(manager, key, value)
            write_metrics.record(latency, success)

        write_metrics.end_time = time.time()

        print(write_metrics.report())

        # 清理
        await manager.close()

        # 验证目标
        assert write_metrics.success_rate > 0.99, f"成功率应>99%，实际: {write_metrics.success_rate:.2%}"

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_mixed_workload():
    """混合工作负载测试"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        config = CacheConfig(
            l1_capacity=1000,
            l2_enabled=False,
            l3_db_path=db_path,
        )
        manager = MultiLevelCacheManager(config=config)

        print("\n测试混合工作负载（80%读，20%写）...")

        # 预热
        warmup_data = {f"key_{i}": f"value_{i}" for i in range(100)}
        await manager.warm_up(warmup_data)

        metrics = PerformanceMetrics("混合工作负载")
        metrics.start_time = time.time()

        for i in range(10000):
            if i % 5 == 0:  # 20%写入
                key = f"key_{i % 200}"
                value = f"updated_value_{i}"
                latency, success = await benchmark_single_set(manager, key, value)
            else:  # 80%读取
                key = f"key_{i % 100}"
                latency, success = await benchmark_single_get(manager, key)
            metrics.record(latency, success)

        metrics.end_time = time.time()

        print(metrics.report())

        # 最终统计
        final_stats = await manager.get_full_statistics()
        print(f"\n最终缓存统计:")
        print(f"  总命中率: {final_stats['manager']['overall_hit_rate']:.2%}")
        print(f"  L1命中: {final_stats['manager']['l1_hits']}")
        print(f"  L3命中: {final_stats['manager']['l3_hits']}")
        print(f"  未命中: {final_stats['manager']['misses']}")

        # 清理
        await manager.close()

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_cache_hit_rate():
    """缓存命中率测试"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        config = CacheConfig(
            l1_capacity=500,
            l2_enabled=False,
            l3_db_path=db_path,
        )
        manager = MultiLevelCacheManager(config=config)

        print("\n测试缓存命中率...")

        # 预热一部分数据
        warmup_keys = 100
        warmup_data = {f"key_{i}": f"value_{i}" for i in range(warmup_keys)}
        await manager.warm_up(warmup_data)

        # 执行混合访问（80%热数据，20%冷数据）
        total_requests = 10000
        hot_data_ratio = 0.8

        for i in range(total_requests):
            if i < total_requests * hot_data_ratio:
                # 访问热数据（在缓存中）
                key = f"key_{i % warmup_keys}"
            else:
                # 访问冷数据（不在缓存中）
                key = f"cold_key_{i % 1000}"

            await manager.get(key)

        stats = await manager.get_full_statistics()
        hit_rate = stats["manager"]["overall_hit_rate"]

        print(f"\n缓存命中率测试结果:")
        print(f"  总请求数: {total_requests}")
        print(f"  热数据比例: {hot_data_ratio:.0%}")
        print(f"  实际命中率: {hit_rate:.2%}")
        print(f"  L1命中率: {stats['manager']['l1_hit_rate']:.2%}")
        print(f"  L3命中率: {stats['manager']['l3_hit_rate']:.2%}")

        # 清理
        await manager.close()

        # 目标验证
        assert hit_rate > 0.7, f"命中率应>70%，实际: {hit_rate:.2%}"

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_concurrent_access():
    """并发访问测试"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        config = CacheConfig(
            l1_capacity=1000,
            l2_enabled=False,
            l3_db_path=db_path,
        )
        manager = MultiLevelCacheManager(config=config)

        print("\n测试并发访问性能...")

        # 预热
        warmup_data = {f"key_{i}": f"value_{i}" for i in range(100)}
        await manager.warm_up(warmup_data)

        # 并发读取任务
        async def concurrent_reader(task_id: int, operations: int):
            """并发读取任务"""
            latencies = []
            for i in range(operations):
                start = time.time()
                await manager.get(f"key_{i % 100}")
                latencies.append((time.time() - start) * 1000)
            return latencies

        # 启动10个并发任务
        num_tasks = 10
        operations_per_task = 1000

        start = time.time()
        tasks = [
            concurrent_reader(i, operations_per_task) for i in range(num_tasks)
        ]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start

        # 统计
        all_latencies = [lat for latencies in results for lat in latencies]
        avg_latency = mean(all_latencies)
        total_ops = num_tasks * operations_per_task
        throughput = total_ops / total_time

        print(f"\n并发访问测试结果:")
        print(f"  并发任务数: {num_tasks}")
        print(f"  每任务操作数: {operations_per_task}")
        print(f"  总操作数: {total_ops}")
        print(f"  总耗时: {total_time:.4f}秒")
        print(f"  吞吐量: {throughput:.2f} OPS")
        print(f"  平均延迟: {avg_latency:.4f} ms")

        # 清理
        await manager.close()

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


async def run_all_benchmarks():
    """运行所有基准测试"""
    print("=" * 60)
    print("多级缓存系统性能基准测试")
    print("=" * 60)

    await test_read_performance()
    await test_write_performance()
    await test_mixed_workload()
    await test_cache_hit_rate()
    await test_concurrent_access()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
