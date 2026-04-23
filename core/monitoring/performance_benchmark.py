#!/usr/bin/env python3
from __future__ import annotations
"""
持续性能基准测试系统 - 阶段5优化
自动化基准测试、性能回归检测、优化建议生成

作者: 小诺·双鱼公主 🌊✨
创建时间: 2025-12-27
版本: v1.0.0
"""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class BenchmarkResult:
    """基准测试结果"""

    name: str
    timestamp: float
    duration_ms: float
    throughput: float  # 吞吐量
    metrics: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkConfig:
    """基准测试配置"""

    # 测试配置
    num_iterations: int = 100
    warmup_iterations: int = 10
    timeout_seconds: float = 300.0

    # 回归检测
    enable_regression_detection: bool = True
    regression_threshold: float = 0.10  # 10%性能下降视为回归
    baseline_window: int = 7  # 基准窗口(天)

    # 结果存储
    results_dir: str = "/Users/xujian/Athena工作平台/logs/benchmarks"

    # 对比配置
    compare_with_baseline: bool = True
    generate_recommendations: bool = True


class ContinuousPerformanceBenchmark:
    """持续性能基准测试系统"""

    def __init__(self, config: BenchmarkConfig = None):
        self.config = config or BenchmarkConfig()

        # 创建结果目录
        Path(self.config.results_dir).mkdir(parents=True, exist_ok=True)

        # 结果存储
        self.results: dict[str, list[BenchmarkResult]] = {}

        # 加载历史结果
        self._load_historical_results()

        logger.info("📊 持续性能基准测试系统初始化完成")
        logger.info(f"📁 结果目录: {self.config.results_dir}")

    def _load_historical_results(self) -> Any:
        """加载历史结果"""
        results_dir = Path(self.config.results_dir)

        for result_file in results_dir.glob("*.json"):
            try:
                with open(result_file, encoding="utf-8") as f:
                    data = json.load(f)

                    for benchmark_name, results in data.items():
                        if benchmark_name not in self.results:
                            self.results[benchmark_name] = []

                        for result_data in results:
                            result = BenchmarkResult(
                                name=benchmark_name,
                                timestamp=result_data["timestamp"],
                                duration_ms=result_data["duration_ms"],
                                throughput=result_data["throughput"],
                                metrics=result_data["metrics"],
                                metadata=result_data.get("metadata", {}),
                            )
                            self.results[benchmark_name].append(result)

            except Exception as e:
                logger.warning(f"⚠️ 加载{result_file}失败: {e}")

        total_results = sum(len(results) for results in self.results.values())
        logger.info(f"📂 已加载{total_results}条历史结果")

    def run_benchmark(
        self, name: str, benchmark_func: Callable, metadata: Optional[dict[str, Any]] = None
    ) -> BenchmarkResult:
        """
        运行基准测试

        Args:
            name: 基准测试名称
            benchmark_func: 测试函数,接受迭代次数参数
            metadata: 元数据(可选)

        Returns:
            测试结果
        """
        logger.info(f"🔬 运行基准测试: {name}")
        start_time = time.time()

        # 预热
        logger.info(f"🔥 预热 ({self.config.warmup_iterations}次)...")
        try:
            benchmark_func(self.config.warmup_iterations)
        except Exception as e:
            logger.warning(f"⚠️ 预热失败: {e}")

        # 正式测试
        logger.info(f"📊 测试 ({self.config.num_iterations}次)...")
        test_start = time.time()

        try:
            benchmark_func(self.config.num_iterations)
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            raise

        test_duration = (time.time() - test_start) * 1000  # ms

        # 计算吞吐量
        throughput = self.config.num_iterations / (test_duration / 1000)

        # 收集指标
        metrics = self._collect_metrics()

        # 创建结果
        result = BenchmarkResult(
            name=name,
            timestamp=time.time(),
            duration_ms=test_duration,
            throughput=throughput,
            metrics=metrics,
            metadata=metadata or {},
        )

        # 存储结果
        if name not in self.results:
            self.results[name] = []
        self.results[name].append(result)

        time.time() - start_time
        logger.info(f"✅ {name}完成: {test_duration:.2f}ms, 吞吐量: {throughput:.2f} 次/秒")

        # 保存结果
        self._save_results()

        # 回归检测
        if self.config.enable_regression_detection:
            self._detect_regression(name, result)

        # 生成报告
        self._generate_benchmark_report(result)

        return result

    def _collect_metrics(self) -> dict[str, Any]:
        """收集系统指标"""
        import psutil

        # GPU指标
        gpu_metrics = {}
        if torch.backends.mps.is_available():
            if hasattr(torch.mps, "current_allocated_memory"):
                gpu_metrics["memory_used_mb"] = torch.mps.current_allocated_memory() / (1024 * 1024)
                gpu_metrics["device"] = "mps"
        elif torch.cuda.is_available():
            gpu_metrics["memory_used_mb"] = torch.cuda.memory_allocated() / (1024 * 1024)
            gpu_metrics["device"] = "cuda"

        # 系统指标
        memory = psutil.virtual_memory()
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_used_gb": memory.used / (1024**3),
            "memory_percent": memory.percent,
        }

        return {"gpu": gpu_metrics, "system": system_metrics, "pytorch_version": torch.__version__}

    def _detect_regression(self, name: str, current_result: BenchmarkResult) -> Any:
        """检测性能回归"""
        if name not in self.results or len(self.results[name]) < 2:
            return

        # 获取基准窗口内的结果
        cutoff_time = time.time() - (self.config.baseline_window * 24 * 3600)
        baseline_results = [
            r
            for r in self.results[name]
            if r.timestamp < current_result.timestamp and r.timestamp >= cutoff_time
        ]

        if not baseline_results:
            return

        # 计算基准平均值
        baseline_avg_throughput = np.mean([r.throughput for r in baseline_results])
        baseline_std_throughput = np.std([r.throughput for r in baseline_results])

        # 检测回归
        performance_change = (
            current_result.throughput - baseline_avg_throughput
        ) / baseline_avg_throughput

        if performance_change < -self.config.regression_threshold:
            logger.warning(f"⚠️ 性能回归检测: {name}")
            logger.warning(
                f"  基准吞吐量: {baseline_avg_throughput:.2f} ± {baseline_std_throughput:.2f}"
            )
            logger.warning(f"  当前吞吐量: {current_result.throughput:.2f}")
            logger.warning(f"  性能下降: {abs(performance_change)*100:.1f}%")

        elif performance_change > self.config.regression_threshold:
            logger.info(f"✅ 性能提升: {name}")
            logger.info(f"  基准吞吐量: {baseline_avg_throughput:.2f}")
            logger.info(f"  当前吞吐量: {current_result.throughput:.2f}")
            logger.info(f"  性能提升: {performance_change*100:.1f}%")

    def _generate_benchmark_report(self, result: BenchmarkResult) -> Any:
        """生成基准测试报告"""
        report = [
            "=" * 60,
            f"📊 基准测试报告: {result.name}",
            "=" * 60,
            f"时间: {datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "🎯 性能指标:",
            f"  耗时: {result.duration_ms:.2f}ms",
            f"  吞吐量: {result.throughput:.2f} 次/秒",
            "",
            "📊 系统指标:",
        ]

        # GPU指标
        if "gpu" in result.metrics:
            gpu = result.metrics["gpu"]
            if "device" in gpu:
                report.append(f"  设备: {gpu['device']}")
            if "memory_used_mb" in gpu:
                report.append(f"  GPU内存: {gpu['memory_used_mb']:.0f}MB")

        # 系统指标
        if "system" in result.metrics:
            sys = result.metrics["system"]
            report.append(f"  CPU: {sys.get('cpu_percent', 0):.1f}%")
            report.append(f"  内存: {sys.get('memory_percent', 0):.1f}%")

        # 对比历史
        if result.name in self.results and len(self.results[result.name]) > 1:
            history = self.results[result.name]
            avg_throughput = np.mean([r.throughput for r in history[:-1]])
            std_throughput = np.std([r.throughput for r in history[:-1]])

            report.append("")
            report.append("📈 历史对比:")
            report.append(f"  历史平均: {avg_throughput:.2f} ± {std_throughput:.2f} 次/秒")
            report.append(f"  当前性能: {result.throughput:.2f} 次/秒")

            performance_change = (result.throughput - avg_throughput) / avg_throughput * 100
            if performance_change > 0:
                report.append(f"  性能变化: +{performance_change:.1f}% ✅")
            else:
                report.append(f"  性能变化: {performance_change:.1f}% ⚠️")

        report.append("=" * 60)

        logger.info("\n" + "\n".join(report))

    def _save_results(self) -> Any:
        """保存结果到文件"""
        # 转换为可序列化格式
        serializable_results = {}
        for name, results in self.results.items():
            serializable_results[name] = [
                {
                    "timestamp": r.timestamp,
                    "duration_ms": r.duration_ms,
                    "throughput": r.throughput,
                    "metrics": r.metrics,
                    "metadata": r.metadata,
                }
                for r in results
            ]

        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        filepath = Path(self.config.results_dir) / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        logger.debug(f"💾 结果已保存: {filepath}")

    def get_benchmark_summary(self, name: Optional[str] = None) -> dict[str, Any]:
        """获取基准测试摘要"""
        if name:
            if name not in self.results:
                return {}

            results = self.results[name]
        else:
            # 所有测试的汇总
            results = []
            for benchmark_results in self.results.values():
                results.extend(benchmark_results)

        if not results:
            return {}

        throughputs = [r.throughput for r in results]
        durations = [r.duration_ms for r in results]

        return {
            "name": name or "all",
            "count": len(results),
            "avg_throughput": np.mean(throughputs),
            "std_throughput": np.std(throughputs),
            "min_throughput": np.min(throughputs),
            "max_throughput": np.max(throughputs),
            "avg_duration_ms": np.mean(durations),
            "first_run": datetime.fromtimestamp(min(r.timestamp for r in results)).isoformat(),
            "last_run": datetime.fromtimestamp(max(r.timestamp for r in results)).isoformat(),
        }

    def compare_benchmarks(self, baseline_name: str, target_name: str) -> dict[str, Any]:
        """对比两个基准测试"""
        if baseline_name not in self.results or target_name not in self.results:
            return {}

        baseline = self.results[baseline_name]
        target = self.results[target_name]

        baseline_avg = np.mean([r.throughput for r in baseline])
        target_avg = np.mean([r.throughput for r in target])

        speedup = target_avg / baseline_avg if baseline_avg > 0 else 0

        return {
            "baseline_name": baseline_name,
            "target_name": target_name,
            "baseline_throughput": baseline_avg,
            "target_throughput": target_avg,
            "speedup": speedup,
            "improvement_percent": (speedup - 1) * 100,
        }

    def get_recommendations(self) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 分析最近的测试结果
        for name, results in self.results.items():
            if len(results) < 3:
                continue

            recent = results[-5:]
            throughputs = [r.throughput for r in recent]

            # 性能波动
            std = np.std(throughputs)
            mean = np.mean(throughputs)
            cv = std / mean if mean > 0 else 0  # 变异系数

            if cv > 0.15:
                recommendations.append(
                    f"⚠️ {name}: 性能波动较大(CV={cv:.2f}),建议检查系统负载和后台进程"
                )

            # 性能趋势
            if len(recent) >= 5:
                recent_half = throughputs[-3:]
                earlier_half = throughputs[:-3]

                if np.mean(recent_half) < np.mean(earlier_half) * 0.9:
                    recommendations.append(f"⚠️ {name}: 最近性能下降,建议检查是否有系统变更")

        return recommendations


# 全局单例
_benchmark_system: ContinuousPerformanceBenchmark | None = None


def get_benchmark_system() -> ContinuousPerformanceBenchmark:
    """获取全局基准测试系统实例"""
    global _benchmark_system
    if _benchmark_system is None:
        _benchmark_system = ContinuousPerformanceBenchmark()
    return _benchmark_system


# 便捷函数
def run_benchmark(
    name: str, benchmark_func: Callable, metadata: Optional[dict[str, Any]] = None
) -> BenchmarkResult:
    """运行基准测试"""
    system = get_benchmark_system()
    return system.run_benchmark(name, benchmark_func, metadata)


if __name__ == "__main__":
    # 测试基准测试系统
    # setup_logging()  # 日志配置已移至模块导入

    print("=" * 60)
    print("🧪 测试持续性能基准测试系统")
    print("=" * 60)

    system = ContinuousPerformanceBenchmark()

    # 定义测试函数
    def matrix_multiply_benchmark(iterations: int) -> Any:
        """矩阵乘法基准测试"""
        size = 1024
        for _ in range(iterations):
            a = torch.randn(size, size)
            b = torch.randn(size, size)
            torch.matmul(a, b)

    def embedding_benchmark(iterations: int) -> Any:
        """嵌入基准测试"""
        for _ in range(iterations):
            ids = torch.randint(0, 10000, (32, 128))
            embedding = torch.nn.Embedding(10000, 768)
            embedding(ids)

    # 运行测试
    print("\n📊 运行矩阵乘法基准测试...")
    result1 = system.run_benchmark(
        "matrix_multiply", matrix_multiply_benchmark, metadata={"size": 1024}
    )

    print("\n📊 运行嵌入基准测试...")
    result2 = system.run_benchmark(
        "embedding", embedding_benchmark, metadata={"vocab_size": 10000, "embed_dim": 768}
    )

    # 获取摘要
    print("\n📊 基准测试摘要:")
    summary = system.get_benchmark_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # 获取建议
    print("\n💡 优化建议:")
    for rec in system.get_recommendations():
        print(f"  {rec}")
