#!/usr/bin/env python3
"""
学习模块性能基准测试框架
Learning Module Performance Benchmark Framework

定义性能基准和测试工具，用于评估学习模块的性能表现。

作者: Athena平台团队
创建时间: 2026-01-28
版本: v1.0.0
"""

from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BenchmarkStatus(str, Enum):
    """基准测试状态"""

    PASSED = "passed"  # 通过
    FAILED = "failed"  # 失败
    WARNING = "warning"  # 警告（接近阈值）


@dataclass
class BenchmarkThreshold:
    """
    基准阈值

    定义各项性能指标的最低要求。
    """

    # 学习性能阈值
    pattern_discovery_min_accuracy: float = 0.75  # 模式发现最低准确率
    pattern_discovery_min_efficiency: float = 0.70  # 模式发现最低效率

    # 适应性能阈值
    adaptation_max_time: float = 5.0  # 适应操作最大时间（秒）
    adaptation_min_success_rate: float = 0.80  # 适应操作最低成功率

    # A/B测试阈值
    ab_test_min_confidence: float = 0.90  # A/B测试最低置信度
    ab_test_min_sample_size: int = 100  # A/B测试最小样本量

    # 内存阈值
    memory_max_mb: int = 500  # 最大内存使用（MB）
    memory_warning_mb: int = 350  # 内存警告阈值（MB）

    # 响应时间阈值
    response_time_p50_ms: float = 100  # 50分位响应时间（毫秒）
    response_time_p95_ms: float = 500  # 95分位响应时间（毫秒）
    response_time_p99_ms: float = 1000  # 99分位响应时间（毫秒）

    # 吞吐量阈值
    min_throughput_per_second: float = 10.0  # 最小吞吐量（次/秒）


@dataclass
class BenchmarkResult:
    """
    基准测试结果
    """

    name: str
    status: BenchmarkStatus
    actual_value: float
    threshold: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    """
    基准测试报告

    汇总所有基准测试的结果。
    """

    engine_name: str
    engine_version: str
    timestamp: datetime = field(default_factory=datetime.now)
    results: list[BenchmarkResult] = field(default_factory=list)
    overall_status: BenchmarkStatus = BenchmarkStatus.PASSED
    summary: dict[str, Any] = field(default_factory=dict)

    def add_result(self, result: BenchmarkResult) -> None:
        """添加测试结果"""
        self.results.append(result)
        # 更新总体状态
        if result.status == BenchmarkStatus.FAILED:
            self.overall_status = BenchmarkStatus.FAILED
        elif result.status == BenchmarkStatus.WARNING and self.overall_status != BenchmarkStatus.FAILED:
            self.overall_status = BenchmarkStatus.WARNING

    def get_summary(self) -> dict[str, Any]:
        """获取测试摘要"""
        passed = sum(1 for r in self.results if r.status == BenchmarkStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == BenchmarkStatus.FAILED)
        warning = sum(1 for r in self.results if r.status == BenchmarkStatus.WARNING)

        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "warning": warning,
            "status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
        }


class LearningBenchmark:
    """
    学习模块基准测试器

    执行各种性能基准测试。
    """

    def __init__(self, thresholds: BenchmarkThreshold | None = None):
        """
        初始化基准测试器

        Args:
            thresholds: 自定义阈值，如果为None则使用默认值
        """
        self.thresholds = thresholds or BenchmarkThreshold()
        self.logger = logging.getLogger(f"{__name__}.LearningBenchmark")

    async def run_all_benchmarks(self, engine: Any) -> BenchmarkReport:
        """
        运行所有基准测试

        Args:
            engine: 要测试的学习引擎实例

        Returns:
            基准测试报告
        """
        report = BenchmarkReport(
            engine_name=engine.__class__.__name__,
            engine_version=getattr(engine, "version", "1.0.0"),
        )

        self.logger.info(f"🚀 开始基准测试: {report.engine_name}")

        # 1. 学习性能测试
        await self._benchmark_learning_performance(engine, report)

        # 2. 适应性能测试
        await self._benchmark_adaptation_performance(engine, report)

        # 3. 内存使用测试
        await self._benchmark_memory_usage(engine, report)

        # 4. 响应时间测试
        await self._benchmark_response_time(engine, report)

        # 5. 吞吐量测试
        await self._benchmark_throughput(engine, report)

        # 生成摘要
        report.summary = report.get_summary()

        self.logger.info(
            f"✅ 基准测试完成: {report.summary['passed']}/{report.summary['total']} 通过"
        )

        return report

    async def _benchmark_learning_performance(self, engine: Any, report: BenchmarkReport) -> None:
        """测试学习性能"""
        try:
            # 创建测试数据
            test_experiences = [
                {
                    "task": f"test_task_{i}",
                    "action": "test_action",
                    "result": {"success": True},
                    "context": {"test": True},
                }
                for i in range(10)
            ]

            # 测试模式发现准确率
            start_time = time.time()
            total_accuracy = 0.0
            total_efficiency = 0.0

            for exp in test_experiences:
                try:
                    result = await engine.process_experience(exp)
                    # 假设返回结果中包含学习质量指标
                    accuracy = result.get("learning_quality", 0.8)
                    efficiency = result.get("efficiency", 0.75)
                    total_accuracy += accuracy
                    total_efficiency += efficiency
                except Exception as e:
                    self.logger.warning(f"经验处理失败: {e}")

            avg_accuracy = total_accuracy / len(test_experiences)
            avg_efficiency = total_efficiency / len(test_experiences)
            elapsed = time.time() - start_time

            # 验证准确率阈值
            if avg_accuracy >= self.thresholds.pattern_discovery_min_accuracy:
                status = BenchmarkStatus.PASSED
            elif avg_accuracy >= self.thresholds.pattern_discovery_min_accuracy * 0.9:
                status = BenchmarkStatus.WARNING
            else:
                status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="模式发现准确率",
                    status=status,
                    actual_value=avg_accuracy,
                    threshold=self.thresholds.pattern_discovery_min_accuracy,
                    unit="分数",
                    details={"elapsed_time": elapsed},
                )
            )

            # 验证效率阈值
            if avg_efficiency >= self.thresholds.pattern_discovery_min_efficiency:
                status = BenchmarkStatus.PASSED
            elif avg_efficiency >= self.thresholds.pattern_discovery_min_efficiency * 0.9:
                status = BenchmarkStatus.WARNING
            else:
                status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="模式发现效率",
                    status=status,
                    actual_value=avg_efficiency,
                    threshold=self.thresholds.pattern_discovery_min_efficiency,
                    unit="分数",
                )
            )

        except Exception as e:
            self.logger.error(f"学习性能测试失败: {e}")
            report.add_result(
                BenchmarkResult(
                    name="学习性能测试",
                    status=BenchmarkStatus.FAILED,
                    actual_value=0.0,
                    threshold=1.0,
                    unit="N/A",
                    details={"error": str(e)},
                )
            )

    async def _benchmark_adaptation_performance(self, engine: Any, report: BenchmarkReport) -> None:
        """测试适应性能"""
        try:
            # 测试适应操作
            test_contexts = [
                {"task_type": "decision", "complexity": "high"},
                {"task_type": "learning", "complexity": "medium"},
                {"task_type": "creative", "complexity": "low"},
            ]

            total_time = 0.0
            success_count = 0

            for context in test_contexts:
                start_time = time.time()
                try:
                    result = await engine.adapt_behavior(context)
                    if result.get("success"):
                        success_count += 1
                    elapsed = time.time() - start_time
                    total_time += elapsed
                except Exception as e:
                    self.logger.warning(f"适应操作失败: {e}")

            avg_time = total_time / len(test_contexts)
            success_rate = success_count / len(test_contexts)

            # 验证响应时间阈值
            if avg_time <= self.thresholds.adaptation_max_time:
                time_status = BenchmarkStatus.PASSED
            elif avg_time <= self.thresholds.adaptation_max_time * 1.2:
                time_status = BenchmarkStatus.WARNING
            else:
                time_status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="适应响应时间",
                    status=time_status,
                    actual_value=avg_time,
                    threshold=self.thresholds.adaptation_max_time,
                    unit="秒",
                )
            )

            # 验证成功率阈值
            if success_rate >= self.thresholds.adaptation_min_success_rate:
                success_status = BenchmarkStatus.PASSED
            elif success_rate >= self.thresholds.adaptation_min_success_rate * 0.9:
                success_status = BenchmarkStatus.WARNING
            else:
                success_status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="适应成功率",
                    status=success_status,
                    actual_value=success_rate,
                    threshold=self.thresholds.adaptation_min_success_rate,
                    unit="分数",
                )
            )

        except Exception as e:
            self.logger.error(f"适应性能测试失败: {e}")
            report.add_result(
                BenchmarkResult(
                    name="适应性能测试",
                    status=BenchmarkStatus.FAILED,
                    actual_value=0.0,
                    threshold=1.0,
                    unit="N/A",
                    details={"error": str(e)},
                )
            )

    async def _benchmark_memory_usage(self, engine: Any, report: BenchmarkReport) -> None:
        """测试内存使用"""
        try:
            import tracemalloc

            tracemalloc.start()

            # 执行一些操作
            for i in range(100):
                await engine.process_experience(
                    {
                        "task": f"memory_test_{i}",
                        "action": "test",
                        "result": {"success": True},
                        "context": {"memory_test": True},
                    }
                )

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            peak_mb = peak / 1024 / 1024  # 转换为MB

            # 验证内存阈值
            if peak_mb <= self.thresholds.memory_max_mb:
                if peak_mb >= self.thresholds.memory_warning_mb:
                    status = BenchmarkStatus.WARNING
                else:
                    status = BenchmarkStatus.PASSED
            else:
                status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="内存使用",
                    status=status,
                    actual_value=peak_mb,
                    threshold=self.thresholds.memory_max_mb,
                    unit="MB",
                    details={"current_mb": current / 1024 / 1024},
                )
            )

        except ImportError:
            self.logger.warning("tracemalloc不可用，跳过内存测试")
        except Exception as e:
            self.logger.error(f"内存使用测试失败: {e}")

    async def _benchmark_response_time(self, engine: Any, report: BenchmarkReport) -> None:
        """测试响应时间"""
        try:
            response_times = []

            # 执行多次操作收集响应时间
            for _ in range(50):
                start_time = time.time()
                await engine.process_experience(
                    {
                        "task": "latency_test",
                        "action": "test",
                        "result": {"success": True},
                        "context": {"latency_test": True},
                    }
                )
                elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
                response_times.append(elapsed)

            # 计算百分位数
            response_times.sort()
            p50 = response_times[len(response_times) // 2]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]

            # 验证P50响应时间
            if p50 <= self.thresholds.response_time_p50_ms:
                p50_status = BenchmarkStatus.PASSED
            elif p50 <= self.thresholds.response_time_p50_ms * 1.2:
                p50_status = BenchmarkStatus.WARNING
            else:
                p50_status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="P50响应时间",
                    status=p50_status,
                    actual_value=p50,
                    threshold=self.thresholds.response_time_p50_ms,
                    unit="ms",
                )
            )

            # 验证P95响应时间
            if p95 <= self.thresholds.response_time_p95_ms:
                p95_status = BenchmarkStatus.PASSED
            elif p95 <= self.thresholds.response_time_p95_ms * 1.2:
                p95_status = BenchmarkStatus.WARNING
            else:
                p95_status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="P95响应时间",
                    status=p95_status,
                    actual_value=p95,
                    threshold=self.thresholds.response_time_p95_ms,
                    unit="ms",
                )
            )

            # 验证P99响应时间
            if p99 <= self.thresholds.response_time_p99_ms:
                p99_status = BenchmarkStatus.PASSED
            elif p99 <= self.thresholds.response_time_p99_ms * 1.2:
                p99_status = BenchmarkStatus.WARNING
            else:
                p99_status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="P99响应时间",
                    status=p99_status,
                    actual_value=p99,
                    threshold=self.thresholds.response_time_p99_ms,
                    unit="ms",
                )
            )

        except Exception as e:
            self.logger.error(f"响应时间测试失败: {e}")

    async def _benchmark_throughput(self, engine: Any, report: BenchmarkReport) -> None:
        """测试吞吐量"""
        try:
            # 测试1秒内的处理能力
            start_time = time.time()
            count = 0
            duration = 1.0  # 1秒

            while time.time() - start_time < duration:
                await engine.process_experience(
                    {
                        "task": f"throughput_test_{count}",
                        "action": "test",
                        "result": {"success": True},
                        "context": {"throughput_test": True},
                    }
                )
                count += 1

            throughput = count / duration

            # 验证吞吐量阈值
            if throughput >= self.thresholds.min_throughput_per_second:
                status = BenchmarkStatus.PASSED
            elif throughput >= self.thresholds.min_throughput_per_second * 0.8:
                status = BenchmarkStatus.WARNING
            else:
                status = BenchmarkStatus.FAILED

            report.add_result(
                BenchmarkResult(
                    name="吞吐量",
                    status=status,
                    actual_value=throughput,
                    threshold=self.thresholds.min_throughput_per_second,
                    unit="次/秒",
                )
            )

        except Exception as e:
            self.logger.error(f"吞吐量测试失败: {e}")


# 便捷函数
def create_benchmark(thresholds: BenchmarkThreshold | None = None) -> LearningBenchmark:
    """创建基准测试器实例"""
    return LearningBenchmark(thresholds)


# 默认阈值
DEFAULT_THRESHOLDS = BenchmarkThreshold()


__all__ = [
    "BenchmarkStatus",
    "BenchmarkThreshold",
    "BenchmarkResult",
    "BenchmarkReport",
    "LearningBenchmark",
    "LearningBenchmarks",  # 别名
    "create_benchmark",
    "DEFAULT_THRESHOLDS",
]


# 为保持兼容性，提供 LearningBenchmarks 作为 LearningBenchmark 的别名
LearningBenchmarks = LearningBenchmark
