"""
性能回归测试框架

目标: 建立自动化性能测试，防止性能退化

功能:
1. 自动化性能测试
2. 性能基线管理
3. 回归检测和告警
4. CI/CD集成
5. 性能报告生成

Author: Athena Team
Date: 2026-04-24
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import statistics


@dataclass
class PerformanceBaseline:
    """性能基线"""
    name: str
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "metrics": self.metrics,
        }


@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    actual_value: float
    baseline_value: float
    threshold_percent: float
    deviation_percent: float
    message: str = ""
    timestamp: float = field(default_factory=time.time)


class PerformanceThreshold:
    """性能阈值"""

    def __init__(
        self,
        metric_name: str,
        max_degradation_percent: float = 10.0,
        min_improvement_percent: float = 0.0,
        absolute_threshold: Optional[float] = None
    ):
        self.metric_name = metric_name
        self.max_degradation_percent = max_degradation_percent
        self.min_improvement_percent = min_improvement_percent
        self.absolute_threshold = absolute_threshold

    def check(self, actual: float, baseline: float) -> TestResult:
        """检查是否通过阈值"""
        if baseline == 0:
            deviation = 0
        else:
            deviation = ((actual - baseline) / baseline) * 100

        # 检查是否超过最大退化阈值
        if deviation > self.max_degradation_percent:
            return TestResult(
                name=self.metric_name,
                passed=False,
                actual_value=actual,
                baseline_value=baseline,
                threshold_percent=self.max_degradation_percent,
                deviation_percent=deviation,
                message=f"性能退化{deviation:.1f}%，超过阈值{self.max_degradation_percent}%",
            )

        # 检查是否满足最小改进要求
        if deviation < -self.min_improvement_percent:
            improvement = -deviation
            return TestResult(
                name=self.metric_name,
                passed=True,
                actual_value=actual,
                baseline_value=baseline,
                threshold_percent=self.max_degradation_percent,
                deviation_percent=deviation,
                message=f"性能改进{improvement:.1f}%，超过要求{self.min_improvement_percent}%",
            )

        # 检查绝对阈值
        if self.absolute_threshold and actual > self.absolute_threshold:
            return TestResult(
                name=self.metric_name,
                passed=False,
                actual_value=actual,
                baseline_value=baseline,
                threshold_percent=self.max_degradation_percent,
                deviation_percent=deviation,
                message=f"实际值{actual}超过绝对阈值{self.absolute_threshold}",
            )

        return TestResult(
            name=self.metric_name,
            passed=True,
            actual_value=actual,
            baseline_value=baseline,
            threshold_percent=self.max_degradation_percent,
            deviation_percent=deviation,
            message=f"性能在可接受范围内（偏差{deviation:.1f}%）",
        )


class PerformanceRegressionTester:
    """性能回归测试器"""

    def __init__(self, baseline_path: str = "data/performance_baseline.json"):
        self.baseline_path = Path(baseline_path)
        self.baseline: Optional[PerformanceBaseline] = None
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.test_history: List[TestResult] = []

    def load_baseline(self) -> Optional[PerformanceBaseline]:
        """加载性能基线"""
        if not self.baseline_path.exists():
            return None

        with open(self.baseline_path, 'r') as f:
            data = json.load(f)

        self.baseline = PerformanceBaseline(
            name=data.get("name", "baseline"),
            timestamp=data.get("timestamp", time.time()),
            metrics=data.get("metrics", {})
        )

        return self.baseline

    def save_baseline(self, baseline: PerformanceBaseline):
        """保存性能基线"""
        self.baseline = baseline

        # 确保目录存在
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.baseline_path, 'w') as f:
            json.dump(baseline.to_dict(), f, indent=2)

    def set_threshold(self, threshold: PerformanceThreshold):
        """设置性能阈值"""
        self.thresholds[threshold.metric_name] = threshold

    def add_threshold(
        self,
        metric_name: str,
        max_degradation_percent: float = 10.0,
        absolute_threshold: Optional[float] = None
    ):
        """添加性能阈值"""
        threshold = PerformanceThreshold(
            metric_name=metric_name,
            max_degradation_percent=max_degradation_percent,
            absolute_threshold=absolute_threshold
        )
        self.set_threshold(threshold)

    async def run_test(
        self,
        test_name: str,
        test_func: Callable,
        metric_name: Optional[str] = None
    ) -> TestResult:
        """运行单个性能测试"""
        # 加载基线
        if self.baseline is None:
            self.load_baseline()

        # 执行测试
        start_time = time.time()
        result = await test_func()
        duration = (time.time() - start_time) * 1000  # ms

        # 确定指标名称
        if metric_name is None:
            metric_name = test_name

        # 获取基线值
        baseline_value = 0
        if self.baseline and metric_name in self.baseline.metrics:
            baseline_value = self.baseline.metrics[metric_name]

        # 检查阈值
        if metric_name in self.thresholds:
            test_result = self.thresholds[metric_name].check(duration, baseline_value)
        else:
            # 默认阈值：最多10%退化
            default_threshold = PerformanceThreshold(metric_name, max_degradation_percent=10.0)
            test_result = default_threshold.check(duration, baseline_value)

        self.test_history.append(test_result)

        return test_result

    async def run_test_suite(
        self,
        tests: Dict[str, Callable]
    ) -> Dict[str, TestResult]:
        """运行测试套件"""
        results = {}

        for test_name, test_func in tests.items():
            try:
                result = await self.run_test(test_name, test_func)
                results[test_name] = result
            except Exception as e:
                results[test_name] = TestResult(
                    name=test_name,
                    passed=False,
                    actual_value=0,
                    baseline_value=0,
                    threshold_percent=0,
                    deviation_percent=0,
                    message=f"测试执行失败: {str(e)}",
                )

        return results

    def generate_report(self, results: Dict[str, TestResult]) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.passed)
        failed_tests = total_tests - passed_tests

        # 按测试分组
        passed = {k: v for k, v in results.items() if v.passed}
        failed = {k: v for k, v in results.items() if not v.passed}

        return {
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            },
            "passed_tests": passed,
            "failed_tests": failed,
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "timestamp": datetime.now().isoformat(),
        }

    def save_report(self, report: Dict[str, Any], output_path: str):
        """保存测试报告"""
        report_path = Path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def update_baseline(self, metrics: Dict[str, float]):
        """更新性能基线"""
        baseline = PerformanceBaseline(
            name=f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            metrics=metrics
        )
        self.save_baseline(baseline)


# 预定义的测试套件
async def test_api_latency() -> float:
    """测试API延迟"""
    # 模拟API调用
    await asyncio.sleep(0.1)  # 100ms
    return 100.0  # 返回延迟（ms）


async def test_vector_search_latency() -> float:
    """测试向量检索延迟"""
    # 模拟向量检索
    await asyncio.sleep(0.05)  # 50ms
    return 50.0


async def test_throughput() -> float:
    """测试吞吐量"""
    # 模拟吞吐量测试
    start = time.time()
    requests = 0

    for _ in range(10):
        await asyncio.sleep(0.01)  # 10ms per request
        requests += 1

    duration = time.time() - start
    qps = requests / duration

    return qps


async def run_regression_tests():
    """运行完整的回归测试套件"""

    tester = PerformanceRegressionTester()

    # 设置阈值
    tester.add_threshold("test_api_latency", max_degradation_percent=15, absolute_threshold=120)
    tester.add_threshold("test_vector_search_latency", max_degradation_percent=20, absolute_threshold=60)
    tester.add_threshold("test_throughput", max_degradation_percent=5)  # QPS不应该下降太多

    # 定义测试套件
    tests = {
        "test_api_latency": test_api_latency,
        "test_vector_search_latency": test_vector_search_latency,
        "test_throughput": test_throughput,
    }

    # 运行测试
    print("🧪 运行性能回归测试...")
    results = await tester.run_test_suite(tests)

    # 生成报告
    report = tester.generate_report(results)

    # 输出结果
    print(f"\n{'='*60}")
    print(f"性能回归测试报告")
    print(f"{'='*60}")
    print(f"总测试数: {report['summary']['total']}")
    print(f"通过: {report['summary']['passed']} ✅")
    print(f"失败: {report['summary']['failed']} ❌")
    print(f"通过率: {report['summary']['pass_rate']*100:.1f}%")

    if report['failed_tests']:
        print(f"\n❌ 失败的测试:")
        for name, result in report['failed_tests'].items():
            print(f"  - {name}: {result.message}")
    else:
        print(f"\n✅ 所有测试通过！")

    # 保存报告
    tester.save_report(report, "data/performance_regression_report.json")
    print(f"\n📄 报告已保存到: data/performance_regression_report.json")

    return report


if __name__ == "__main__":
    # 运行回归测试
    asyncio.run(run_regression_tests())
