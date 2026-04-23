#!/usr/bin/env python3
"""
Athena平台性能基准测试套件
Performance Benchmark Test Suite

建立关键系统组件的性能基准，包括:
1. Agent执行性能
2. LLM调用性能
3. 数据库查询性能
4. 缓存系统性能
5. 工具调用性能

作者: Athena平台团队
创建时间: 2026-04-21
版本: v1.0.0
"""

import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class BenchmarkResult:
    """性能基准测试结果"""

    name: str  # 测试名称
    iterations: int  # 迭代次数
    total_time: float  # 总耗时(秒)
    avg_time: float  # 平均耗时(秒)
    min_time: float  # 最小耗时(秒)
    max_time: float  # 最大耗时(秒)
    median_time: float  # 中位数耗时(秒)
    std_dev: float  # 标准差
    throughput: float  # 吞吐量(操作/秒)

    # 性能目标
    target_p95: float | None = field(default=None)  # P95目标(秒)
    target_avg: float | None = field(default=None)  # 平均目标(秒)
    p95_actual: float | None = field(default=None)  # 实际P95值

    def meets_target(self) -> bool:
        """是否达到性能目标"""
        if self.target_p95 and self.p95_actual:
            return self.p95_actual <= self.target_p95
        if self.target_avg:
            return self.avg_time <= self.target_avg
        return True

    def __str__(self) -> str:
        status = "✅ PASS" if self.meets_target() else "❌ FAIL"
        target_avg_ms = f"{self.target_avg*1000:.2f}ms" if self.target_avg else "N/A"
        target_p95_ms = f"{self.target_p95*1000:.2f}ms" if self.target_p95 else "N/A"
        p95_actual_ms = f"{self.p95_actual*1000:.2f}ms" if self.p95_actual else "0ms"

        return (
            f"{status} | {self.name}\n"
            f"  平均耗时: {self.avg_time*1000:.2f}ms "
            f"(目标: {target_avg_ms})\n"
            f"  P95耗时: {p95_actual_ms} "
            f"(目标: {target_p95_ms})\n"
            f"  吞吐量: {self.throughput:.2f} ops/sec\n"
            f"  标准差: {self.std_dev*1000:.2f}ms"
        )


class PerformanceBenchmark:
    """性能基准测试运行器"""

    def __init__(self, warmup_iterations: int = 3):
        """
        初始化基准测试运行器

        Args:
            warmup_iterations: 预热迭代次数
        """
        self.warmup_iterations = warmup_iterations
        self.results: list[BenchmarkResult] = []

    async def benchmark_async(
        self,
        name: str,
        func: Callable,
        iterations: int = 10,
        target_p95: float | None = None,
        target_avg: float | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> BenchmarkResult:
        """
        异步函数性能基准测试

        Args:
            name: 测试名称
            func: 被测试的异步函数
            iterations: 迭代次数
            target_p95: P95目标时间(秒)
            target_avg: 平均目标时间(秒)
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            基准测试结果
        """
        print(f"\n🔬 基准测试: {name}")
        print(f"   迭代次数: {iterations}")

        # 预热
        if self.warmup_iterations > 0:
            print(f"   预热 {self.warmup_iterations} 次...")
            for _ in range(self.warmup_iterations):
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    print(f"   ⚠️ 预热失败: {e}")

        # 正式测试
        times = []
        print("   开始测试...")
        for i in range(iterations):
            start = time.perf_counter()
            try:
                await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            except Exception as e:
                print(f"   ❌ 第{i+1}次迭代失败: {e}")

        if not times:
            raise RuntimeError(f"基准测试失败: {name}, 所有迭代都失败了")

        # 计算统计数据
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = iterations / total_time if total_time > 0 else 0.0

        # 计算P95
        sorted_times = sorted(times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_actual = sorted_times[min(p95_index, len(sorted_times) - 1)]

        # 创建结果
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput,
            target_p95=target_p95,
            target_avg=target_avg,
            p95_actual=p95_actual,
        )

        self.results.append(result)
        print(f"   ✅ 完成: {result}")

        return result

    def benchmark_sync(
        self,
        name: str,
        func: Callable,
        iterations: int = 10,
        target_p95: float | None = None,
        target_avg: float | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> BenchmarkResult:
        """
        同步函数性能基准测试

        Args:
            name: 测试名称
            func: 被测试的同步函数
            iterations: 迭代次数
            target_p95: P95目标时间(秒)
            target_avg: 平均目标时间(秒)
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            基准测试结果
        """
        print(f"\n🔬 基准测试: {name}")
        print(f"   迭代次数: {iterations}")

        # 预热
        if self.warmup_iterations > 0:
            print(f"   预热 {self.warmup_iterations} 次...")
            for _ in range(self.warmup_iterations):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"   ⚠️ 预热失败: {e}")

        # 正式测试
        times = []
        print("   开始测试...")
        for i in range(iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            except Exception as e:
                print(f"   ❌ 第{i+1}次迭代失败: {e}")

        if not times:
            raise RuntimeError(f"基准测试失败: {name}, 所有迭代都失败了")

        # 计算统计数据
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = iterations / total_time if total_time > 0 else 0.0

        # 计算P95
        sorted_times = sorted(times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_actual = sorted_times[min(p95_index, len(sorted_times) - 1)]

        # 创建结果
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput,
            target_p95=target_p95,
            target_avg=target_avg,
            p95_actual=p95_actual,
        )

        self.results.append(result)
        print(f"   ✅ 完成: {result}")

        return result

    def print_summary(self) -> None:
        """打印测试结果摘要"""
        print("\n" + "=" * 80)
        print("📊 性能基准测试摘要")
        print("=" * 80)

        passed = sum(1 for r in self.results if r.meets_target())
        failed = len(self.results) - passed

        for result in self.results:
            print(result)
            print()

        print("-" * 80)
        print(f"总计: {len(self.results)} 个测试")
        print(f"通过: {passed} 个 ✅")
        print(f"失败: {failed} 个 ❌")
        print(f"成功率: {passed/len(self.results)*100:.1f}%")
        print("=" * 80)

    def save_report(self, filepath: str) -> None:
        """
        保存性能报告到文件

        Args:
            filepath: 报告文件路径
        """
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Athena平台性能基准测试报告\n\n")
            f.write(f"> **生成时间**: {datetime.now().isoformat()}\n")
            f.write(f"> **测试数量**: {len(self.results)}\n\n")

            f.write("## 测试结果\n\n")

            for i, result in enumerate(self.results, 1):
                f.write(f"### {i}. {result.name}\n\n")
                f.write(f"- **平均耗时**: {result.avg_time*1000:.2f}ms\n")
                f.write(f"- **P95耗时**: {result.p95_actual*1000 if result.p95_actual else 0:.2f}ms\n")
                f.write(f"- **最小耗时**: {result.min_time*1000:.2f}ms\n")
                f.write(f"- **最大耗时**: {result.max_time*1000:.2f}ms\n")
                f.write(f"- **吞吐量**: {result.throughput:.2f} ops/sec\n")
                f.write(f"- **标准差**: {result.std_dev*1000:.2f}ms\n")

                if result.meets_target():
                    f.write("- **状态**: ✅ PASS\n\n")
                else:
                    f.write("- **状态**: ❌ FAIL\n\n")

        print(f"✅ 性能报告已保存: {filepath}")


# 全局基准测试运行器
_benchmark_runner: PerformanceBenchmark | None = None


def get_benchmark_runner() -> PerformanceBenchmark:
    """
    获取全局基准测试运行器

    Returns:
        性能基准测试运行器
    """
    global _benchmark_runner
    if _benchmark_runner is None:
        _benchmark_runner = PerformanceBenchmark()
    return _benchmark_runner

