#!/usr/bin/env python3
"""
Athena 感知模块 - 性能基准跟踪系统
跟踪性能指标变化，检测性能回归
最后更新: 2026-01-26
"""

from __future__ import annotations
import asyncio
import json
import logging
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标"""
    timestamp: str
    test_name: str
    metric_name: str
    value: float
    unit: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBaseline:
    """性能基准"""
    test_name: str
    metric_name: str
    baseline_value: float
    unit: str
    created_at: str
    samples: list[float] = field(default_factory=list)
    threshold_percent: float = 20.0  # 回归阈值百分比


@dataclass
class PerformanceRegression:
    """性能回归报告"""
    timestamp: str
    test_name: str
    metric_name: str
    current_value: float
    baseline_value: float
    percent_change: float
    is_regression: bool
    severity: str  # "critical", "warning", "info"


class PerformanceTracker:
    """
    性能基准跟踪系统

    功能：
    1. 记录性能指标
    2. 与基准对比
    3. 检测性能回归
    4. 生成趋势报告
    5. 导出/导入基准数据
    """

    def __init__(self, baseline_dir: str = "/tmp/performance_baselines"):
        """
        初始化性能跟踪器

        Args:
            baseline_dir: 基准数据存储目录
        """
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

        self.metrics: list[PerformanceMetric] = []
        self.baselines: dict[str, PerformanceBaseline] = {}

        logger.info(f"✓ 性能跟踪器已初始化 (基准目录: {baseline_dir})")

    def record_metric(
        self,
        test_name: str,
        metric_name: str,
        value: float,
        unit: str,
        metadata: dict[str, Any] | None | None = None
    ):
        """
        记录性能指标

        Args:
            test_name: 测试名称
            metric_name: 指标名称
            value: 指标值
            unit: 单位
            metadata: 额外元数据
        """
        metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            test_name=test_name,
            metric_name=metric_name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )

        self.metrics.append(metric)
        logger.info(f"✓ 指标已记录: {test_name}.{metric_name} = {value}{unit}")

    def set_baseline(
        self,
        test_name: str,
        metric_name: str,
        baseline_value: float,
        unit: str,
        samples: list[float] | None | None = None,
        threshold_percent: float = 20.0
    ):
        """
        设置性能基准

        Args:
            test_name: 测试名称
            metric_name: 指标名称
            baseline_value: 基准值
            unit: 单位
            samples: 样本数据
            threshold_percent: 回归阈值百分比
        """
        baseline_key = f"{test_name}.{metric_name}"

        baseline = PerformanceBaseline(
            test_name=test_name,
            metric_name=metric_name,
            baseline_value=baseline_value,
            unit=unit,
            created_at=datetime.now().isoformat(),
            samples=samples or [],
            threshold_percent=threshold_percent
        )

        self.baselines[baseline_key] = baseline
        self._save_baseline(baseline_key, baseline)

        logger.info(
            f"✓ 基准已设置: {baseline_key} = {baseline_value}{unit} "
            f"(阈值: ±{threshold_percent}%)"
        )

    def check_regressions(
        self,
        threshold_percent: float | None = None
    ) -> list[PerformanceRegression]:
        """
        检测性能回归

        Args:
            threshold_percent: 覆盖默认阈值

        Returns:
            回归报告列表
        """
        regressions = []

        # 获取最新的指标
        latest_metrics = {}
        for metric in self.metrics:
            key = f"{metric.test_name}.{metric.metric_name}"
            if key not in latest_metrics:
                latest_metrics[key] = metric

        # 与基准对比
        for baseline_key, baseline in self.baselines.items():
            if baseline_key not in latest_metrics:
                continue

            current_metric = latest_metrics[baseline_key]
            current_value = current_metric.value
            baseline_value = baseline.baseline_value

            # 计算变化百分比
            if baseline_value == 0:
                percent_change = 0
            else:
                percent_change = ((current_value - baseline_value) / baseline_value) * 100

            # 判断是否为回归（性能变差）
            threshold = threshold_percent or baseline.threshold_percent
            is_regression = abs(percent_change) > threshold

            # 确定严重程度
            if abs(percent_change) > threshold * 2:
                severity = "critical"
            elif abs(percent_change) > threshold:
                severity = "warning"
            else:
                severity = "info"

            regression = PerformanceRegression(
                timestamp=datetime.now().isoformat(),
                test_name=baseline.test_name,
                metric_name=baseline.metric_name,
                current_value=current_value,
                baseline_value=baseline_value,
                percent_change=percent_change,
                is_regression=is_regression,
                severity=severity
            )

            regressions.append(regression)

            if is_regression:
                direction = "上升" if percent_change > 0 else "下降"
                logger.warning(
                    f"⚠️ 性能{'回归' if percent_change > 0 else '改善'}: "
                    f"{baseline_key} {direction} {abs(percent_change):.1f}% "
                    f"({baseline_value}{baseline.unit} → {current_value}{baseline.unit})"
                )

        return regressions

    def calculate_baseline_from_samples(
        self,
        test_name: str,
        metric_name: str,
        samples: list[float],
        unit: str,
        threshold_percent: float = 20.0
    ):
        """
        从样本计算基准值

        Args:
            test_name: 测试名称
            metric_name: 指标名称
            samples: 样本数据
            unit: 单位
            threshold_percent: 回归阈值百分比
        """
        if not samples:
            logger.warning(f"无法计算基准: {test_name}.{metric_name} - 没有样本数据")
            return

        # 使用中位数作为基准（更稳健）
        baseline_value = statistics.median(samples)

        self.set_baseline(
            test_name=test_name,
            metric_name=metric_name,
            baseline_value=baseline_value,
            unit=unit,
            samples=samples,
            threshold_percent=threshold_percent
        )

        logger.info(
            f"✓ 基准已从{len(samples)}个样本计算: "
            f"{test_name}.{metric_name} = {baseline_value}{unit} "
            f"(平均: {statistics.mean(samples):.4f}, "
            f"标准差: {statistics.stdev(samples) if len(samples) > 1 else 0:.4f})"
        )

    def get_trend(
        self,
        test_name: str,
        metric_name: str,
        days: int = 7
    ) -> dict[str, Any]:
        """
        获取性能趋势

        Args:
            test_name: 测试名称
            metric_name: 指标名称
            days: 天数

        Returns:
            趋势数据
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        # 筛选指标
        filtered_metrics = [
            m for m in self.metrics
            if m.test_name == test_name
            and m.metric_name == metric_name
            and datetime.fromisoformat(m.timestamp) > cutoff_time
        ]

        if not filtered_metrics:
            return {"error": "没有足够的历史数据"}

        values = [m.value for m in filtered_metrics]

        return {
            "test_name": test_name,
            "metric_name": metric_name,
            "period_days": days,
            "samples_count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "trend": "improving" if len(values) > 1 and values[-1] < values[0] else "stable"
        }

    def generate_report(self) -> str:
        """生成性能报告"""
        lines = []
        lines.append("# 性能基准跟踪报告")
        lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 回归检测
        regressions = self.check_regressions()
        if regressions:
            lines.append("## 性能回归检测结果\n")
            lines.append("| 测试 | 指标 | 当前值 | 基准值 | 变化 | 严重程度 |")
            lines.append("|------|------|--------|--------|------|----------|")

            for reg in regressions:
                change_str = f"{reg.percent_change:+.1f}%"
                severity_icon = "🔴" if reg.severity == "critical" else "⚠️" if reg.severity == "warning" else "✅"
                lines.append(
                    f"| {reg.test_name} | {reg.metric_name} | "
                    f"{reg.current_value:.4f}{reg.current_value > 0 and '单位' or ''} | "
                    f"{reg.baseline_value:.4f} | {change_str} | {severity_icon} {reg.severity} |"
                )

            lines.append("")
        else:
            lines.append("## ✅ 未检测到性能回归\n")

        # 趋势分析
        lines.append("## 性能趋势\n")

        for baseline_key in self.baselines.keys():
            test_name, metric_name = baseline_key.split(".", 1)
            trend = self.get_trend(test_name, metric_name)

            if "error" not in trend:
                lines.append(f"### {baseline_key}")
                lines.append(f"- 样本数: {trend['samples_count']}")
                lines.append(f"- 平均值: {trend['mean']:.4f}")
                lines.append(f"- 中位数: {trend['median']:.4f}")
                lines.append(f"- 标准差: {trend['std_dev']:.4f}")
                lines.append(f"- 趋势: {trend['trend']}\n")

        # 基准列表
        lines.append("## 当前基准\n")
        lines.append("| 测试 | 指标 | 基准值 | 单位 | 创建时间 |")
        lines.append("|------|------|--------|------|----------|")

        for baseline_key, baseline in self.baselines.items():
            created_time = datetime.fromisoformat(baseline.created_at).strftime('%Y-%m-%d %H:%M')
            lines.append(
                f"| {baseline.test_name} | {baseline.metric_name} | "
                f"{baseline.baseline_value:.4f} | {baseline.unit} | {created_time} |"
            )

        return "\n".join(lines)

    def save_baselines(self, filepath: str | None = None):
        """
        保存所有基准到文件

        Args:
            filepath: 文件路径，默认使用时间戳
        """
        if filepath is None:
            filepath = self.baseline_dir / f"baselines_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            "generated_at": datetime.now().isoformat(),
            "baselines": {
                key: asdict(baseline)
                for key, baseline in self.baselines.items()
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 基准已保存: {filepath}")

    def load_baselines(self, filepath: str):
        """
        从文件加载基准

        Args:
            filepath: 文件路径
        """
        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)

            for key, baseline_data in data.get("baselines", {}).items():
                baseline = PerformanceBaseline(**baseline_data)
                self.baselines[key] = baseline

            logger.info(f"✓ 基准已加载: {filepath} ({len(self.baselines)}个基准)")

        except Exception as e:
            logger.error(f"加载基准失败: {e}")

    def _save_baseline(self, key: str, baseline: PerformanceBaseline):
        """保存单个基准"""
        filepath = self.baseline_dir / f"{key.replace('.', '_')}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(baseline), f, ensure_ascii=False, indent=2)

    def load_all_baselines(self):
        """加载基准目录中的所有基准"""
        for filepath in self.baseline_dir.glob("*.json"):
            try:
                with open(filepath, encoding='utf-8') as f:
                    baseline_data = json.load(f)

                # 跳过汇总文件
                if "baselines" in baseline_data:
                    continue

                baseline = PerformanceBaseline(**baseline_data)
                key = f"{baseline.test_name}.{baseline.metric_name}"
                self.baselines[key] = baseline

            except Exception as e:
                logger.warning(f"加载基准失败 {filepath}: {e}")

        logger.info(f"✓ 已加载{len(self.baselines)}个基准")


# 使用示例
if __name__ == "__main__":
    async def main():
        tracker = PerformanceTracker()

        # 加载现有基准
        tracker.load_all_baselines()

        # 模拟性能测试数据
        print("\n模拟性能测试...")

        # OCR性能测试
        ocr_times = [0.108, 0.109, 0.107, 0.110, 0.108]
        for time_val in ocr_times:
            tracker.record_metric("ocr", "response_time", time_val, "秒")

        # 设置基准（如果是第一次运行）
        if "ocr.response_time" not in tracker.baselines:
            tracker.calculate_baseline_from_samples(
                "ocr", "response_time", ocr_times, "秒", threshold_percent=10
            )

        # 检测回归
        print("\n检测性能回归...")
        regressions = tracker.check_regressions()

        if not regressions:
            print("✅ 未检测到性能回归")
        else:
            print(f"⚠️ 检测到{len(regressions)}个性能问题")

        # 生成报告
        print("\n" + "="*60)
        print(tracker.generate_report())
        print("="*60 + "\n")

        # 保存基准
        tracker.save_baselines()

    asyncio.run(main())
