#!/usr/bin/env python3
"""
统一工具注册表性能基准测试
Performance Benchmark for Unified Tool Registry

测试统一工具注册表的性能表现，并与旧注册表对比。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.base import ToolCategory, ToolDefinition, get_global_registry
from core.tools.unified_registry import get_unified_registry


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    total_time: float
    iterations: int
    avg_time: float
    throughput: float  # 每秒操作数


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        self.results: list[BenchmarkResult] = []
        self.unified_registry = get_unified_registry()
        self.old_registry = get_global_registry()

    def benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 1000,
        warmup: int = 10,
    ) -> BenchmarkResult:
        """
        执行基准测试

        Args:
            name: 测试名称
            func: 测试函数
            iterations: 迭代次数
            warmup: 预热次数

        Returns:
            BenchmarkResult: 测试结果
        """
        print(f"\n🔬 测试: {name}")
        print(f"   迭代次数: {iterations}")
        print(f"   预热次数: {warmup}")

        # 预热
        for _ in range(warmup):
            func()

        # 正式测试
        start_time = time.perf_counter()
        for _ in range(iterations):
            func()
        end_time = time.perf_counter()

        # 计算结果
        total_time = end_time - start_time
        avg_time = total_time / iterations
        throughput = iterations / total_time

        result = BenchmarkResult(
            name=name,
            total_time=total_time,
            iterations=iterations,
            avg_time=avg_time,
            throughput=throughput,
        )

        self.results.append(result)

        # 打印结果
        print(f"   总时间: {total_time:.4f}秒")
        print(f"   平均时间: {avg_time*1000:.4f}毫秒")
        print(f"   吞吐量: {throughput:.2f} ops/sec")

        return result

    def compare_results(self, result1: BenchmarkResult, result2: BenchmarkResult):
        """
        对比两个测试结果

        Args:
            result1: 结果1
            result2: 结果2
        """
        speedup = result2.avg_time / result1.avg_time
        improvement = (1 - speedup) * 100

        print(f"\n📊 对比: {result1.name} vs {result2.name}")
        print(f"   加速比: {speedup:.2f}x")
        print(f"   性能提升: {improvement:+.1f}%")

        if improvement > 0:
            print("   ✅ 性能提升")
        elif improvement < 0:
            print("   ⚠️ 性能下降")
        else:
            print("   ➡️ 性能持平")

    def test_register_performance(self, count: int = 1000):
        """测试注册性能"""
        print("\n" + "="*60)
        print("📝 工具注册性能测试")
        print("="*60)

        # 测试新注册表
        def register_unified():
            for i in range(count):
                tool = ToolDefinition(
                    tool_id=f"perf_tool_{i}",
                    name=f"性能测试工具{i}",
                    description="性能测试",
                    category=ToolCategory.PATENT_SEARCH,
                )
                self.unified_registry.register(tool)

        result_unified = self.benchmark(
            name="统一注册表-注册工具",
            func=register_unified,
            iterations=10,
        )

        # 测试旧注册表
        def register_old():
            for i in range(count):
                tool = ToolDefinition(
                    tool_id=f"old_perf_tool_{i}",
                    name=f"旧性能测试工具{i}",
                    description="旧性能测试",
                    category=ToolCategory.PATENT_SEARCH,
                )
                self.old_registry.register(tool)

        result_old = self.benchmark(
            name="旧注册表-注册工具",
            func=register_old,
            iterations=10,
        )

        # 对比结果
        self.compare_results(result_unified, result_old)

    def test_query_performance(self, count: int = 1000):
        """测试查询性能"""
        print("\n" + "="*60)
        print("🔍 工具查询性能测试")
        print("="*60)

        # 预先注册工具
        for i in range(count):
            tool = ToolDefinition(
                tool_id=f"query_tool_{i}",
                name=f"查询工具{i}",
                description="查询测试",
                category=ToolCategory.PATENT_SEARCH,
            )
            self.unified_registry.register(tool)
            self.old_registry.register(tool)

        # 测试新注册表
        def query_unified():
            for i in range(count):
                self.unified_registry.get(f"query_tool_{i}")

        result_unified = self.benchmark(
            name="统一注册表-查询工具",
            func=query_unified,
            iterations=100,
        )

        # 测试旧注册表
        def query_old():
            for i in range(count):
                self.old_registry.get(f"query_tool_{i}")

        result_old = self.benchmark(
            name="旧注册表-查询工具",
            func=query_old,
            iterations=100,
        )

        # 对比结果
        self.compare_results(result_unified, result_old)

    def test_lazy_load_performance(self, count: int = 100):
        """测试懒加载性能"""
        print("\n" + "="*60)
        print("⏳ 懒加载性能测试")
        print("="*60)

        # 注册懒加载工具
        for i in range(count):
            self.unified_registry.register_lazy(
                tool_id=f"lazy_tool_{i}",
                import_path="os.path",
                function_name="join",
                metadata={},
            )

        # 测试首次加载（无缓存）
        def load_first_time():
            for i in range(count):
                self.unified_registry.get(f"lazy_tool_{i}")

        result_first = self.benchmark(
            name="懒加载-首次加载",
            func=load_first_time,
            iterations=10,
        )

        # 测试缓存加载（有缓存）
        def load_cached():
            for i in range(count):
                self.unified_registry.get(f"lazy_tool_{i}")

        result_cached = self.benchmark(
            name="懒加载-缓存加载",
            func=load_cached,
            iterations=100,
        )

        # 对比结果
        self.compare_results(result_first, result_cached)

    def test_concurrent_performance(self, thread_count: int = 10):
        """测试并发性能"""
        print("\n" + "="*60)
        print("🔄 并发性能测试")
        print("="*60)

        import threading

        # 预先注册工具
        count = 1000
        for i in range(count):
            tool = ToolDefinition(
                tool_id=f"concurrent_tool_{i}",
                name=f"并发工具{i}",
                description="并发测试",
                category=ToolCategory.PATENT_SEARCH,
            )
            self.unified_registry.register(tool)

        errors = []
        query_count = 0

        def query_worker():
            nonlocal query_count
            try:
                for i in range(1000):
                    tool_id = f"concurrent_tool_{i % count}"
                    tool = self.unified_registry.get(tool_id)
                    if tool is None:
                        errors.append(f"工具未找到: {tool_id}")
                    query_count += 1
            except Exception as e:
                errors.append(str(e))

        # 执行并发测试
        start_time = time.perf_counter()
        threads = []
        for _ in range(thread_count):
            t = threading.Thread(target=query_worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
        end_time = time.perf_counter()

        # 计算结果
        total_time = end_time - start_time
        total_queries = thread_count * 1000
        throughput = total_queries / total_time

        print("\n🔬 测试: 并发查询")
        print(f"   线程数: {thread_count}")
        print(f"   总查询数: {total_queries}")
        print(f"   总时间: {total_time:.4f}秒")
        print(f"   吞吐量: {throughput:.2f} queries/sec")
        print(f"   错误数: {len(errors)}")

        if len(errors) == 0:
            print("   ✅ 并发安全")
        else:
            print("   ❌ 并发错误:")
            for error in errors[:10]:  # 只显示前10个错误
                print(f"      - {error}")

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("📊 性能测试摘要")
        print("="*60)

        print(f"\n测试项目数: {len(self.results)}")
        print("\n详细结果:")

        for result in self.results:
            print(f"\n  {result.name}:")
            print(f"    总时间: {result.total_time:.4f}秒")
            print(f"    平均时间: {result.avg_time*1000:.4f}毫秒")
            print(f"    吞吐量: {result.throughput:.2f} ops/sec")

        print("\n" + "="*60)


def main():
    """主函数"""
    print("🚀 统一工具注册表性能基准测试")
    print("="*60)

    # 创建基准测试实例
    benchmark = PerformanceBenchmark()

    # 执行测试
    try:
        # 1. 注册性能测试
        benchmark.test_register_performance(count=1000)

        # 2. 查询性能测试
        benchmark.test_query_performance(count=1000)

        # 3. 懒加载性能测试
        benchmark.test_lazy_load_performance(count=100)

        # 4. 并发性能测试
        benchmark.test_concurrent_performance(thread_count=10)

        # 打印摘要
        benchmark.print_summary()

        print("\n✅ 性能测试完成")
        return 0

    except Exception as e:
        print(f"\n❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
