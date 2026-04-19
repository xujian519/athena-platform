#!/usr/bin/env python3
from __future__ import annotations
"""
学习效果评估器
Learning Effectiveness Evaluator

评估在线学习系统的学习效果
生成学习报告和改进建议
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.async_main import async_main

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""

    ACCURACY = "accuracy"  # 准确率
    LATENCY = "latency"  # 延迟
    SUCCESS_RATE = "success_rate"  # 成功率
    ERROR_RATE = "error_rate"  # 错误率
    THROUGHPUT = "throughput"  # 吞吐量
    CUSTOM = "custom"  # 自定义


class TrendDirection(Enum):
    """趋势方向"""

    IMPROVING = "improving"  # 改善
    DECLINING = "declining"  # 下降
    STABLE = "stable"  # 稳定
    UNKNOWN = "unknown"  # 未知


@dataclass
class MetricData:
    """指标数据"""

    name: str
    value: float
    baseline: float
    target: float
    unit: str = ""
    history: list[float] = field(default_factory=list)


@dataclass
class TrendAnalysis:
    """趋势分析"""

    metric_name: str
    direction: TrendDirection
    change_rate: float
    confidence: float
    significant: bool


@dataclass
class LearningReport:
    """学习报告"""

    report_id: str
    timestamp: datetime
    overall_score: float  # 总体评分(0-100)
    metrics: dict[str, MetricData]
    trends: dict[str, TrendAnalysis]
    recommendations: list[str]
    summary: str


class LearningEvaluator:
    """
    学习效果评估器

    核心功能:
    1. 指标跟踪
    2. 趋势分析
    3. 学习报告生成
    4. 改进建议
    """

    def __init__(self):
        """初始化评估器"""
        self.name = "学习效果评估器 v1.0"
        self.version = "1.0.0"

        # 指标数据
        self.metrics: dict[str, MetricData] = {}

        # 历史数据
        self.history: list[dict[str, float]] = []
        self.max_history_size = 1000

        # 报告历史
        self.reports: list[LearningReport] = []

        # 基线和目标
        self.baselines: dict[str, float] = {
            "intent_accuracy": 0.97,
            "tool_selection_accuracy": 0.89,
            "parameter_extraction_accuracy": 0.75,
            "avg_latency_ms": 200,
            "success_rate": 0.70,
        }

        self.targets: dict[str, float] = {
            "intent_accuracy": 0.985,
            "tool_selection_accuracy": 0.95,
            "parameter_extraction_accuracy": 0.85,
            "avg_latency_ms": 150,
            "success_rate": 0.80,
        }

    def record_metric(self, name: str, value: float, unit: str = ""):
        """
        记录指标

        Args:
            name: 指标名称
            value: 指标值
            unit: 单位
        """
        if name not in self.metrics:
            baseline = self.baselines.get(name, 0.0)
            target = self.targets.get(name, 0.0)
            self.metrics[name] = MetricData(
                name=name, value=value, baseline=baseline, target=target, unit=unit, history=[]
            )

        # 更新当前值
        self.metrics[name].value = value
        self.metrics[name].history.append(value)

        # 限制历史大小
        if len(self.metrics[name].history) > 1000:
            self.metrics[name].history = self.metrics[name].history[-1000:]

    def analyze_trend(self, metric_name: str, window: int = 10) -> TrendAnalysis:
        """
        分析指标趋势

        Args:
            metric_name: 指标名称
            window: 分析窗口大小

        Returns:
            TrendAnalysis: 趋势分析
        """
        if metric_name not in self.metrics:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.UNKNOWN,
                change_rate=0.0,
                confidence=0.0,
                significant=False,
            )

        metric = self.metrics[metric_name]
        history = metric.history[-window:] if len(metric.history) >= window else metric.history

        if len(history) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.UNKNOWN,
                change_rate=0.0,
                confidence=0.0,
                significant=False,
            )

        # 计算变化率
        first_value = history[0]
        last_value = history[-1]
        change_rate = (last_value - first_value) / first_value if first_value != 0 else 0

        # 判断方向
        if abs(change_rate) < 0.01:  # 小于1%变化视为稳定
            direction = TrendDirection.STABLE
        elif change_rate > 0:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.DECLINING

        # 计算置信度(基于历史数据的稳定性)
        if len(history) >= 3:
            variance = sum((x - sum(history) / len(history)) ** 2 for x in history) / len(history)
            mean = sum(history) / len(history)
            coefficient_of_variation = (variance**0.5) / mean if mean != 0 else 0
            confidence = max(0, 1 - coefficient_of_variation)
        else:
            confidence = 0.5

        # 判断是否显著
        significant = abs(change_rate) > 0.05 and confidence > 0.7

        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            change_rate=change_rate,
            confidence=confidence,
            significant=significant,
        )

    def generate_report(self) -> LearningReport:
        """
        生成学习报告

        Returns:
            LearningReport: 学习报告
        """
        report_id = f"report_{int(datetime.now().timestamp())}"
        timestamp = datetime.now()

        # 分析所有指标趋势
        trends = {}
        for metric_name in self.metrics:
            trends[metric_name] = self.analyze_trend(metric_name)

        # 计算总体评分
        overall_score = self._calculate_overall_score()

        # 生成建议
        recommendations = self._generate_recommendations(trends)

        # 生成摘要
        summary = self._generate_summary(overall_score, trends)

        report = LearningReport(
            report_id=report_id,
            timestamp=timestamp,
            overall_score=overall_score,
            metrics=self.metrics.copy(),
            trends=trends,
            recommendations=recommendations,
            summary=summary,
        )

        self.reports.append(report)
        return report

    def _calculate_overall_score(self) -> float:
        """计算总体评分"""
        if not self.metrics:
            return 0.0

        scores = []
        for metric in self.metrics.values():
            # 计算达到目标的百分比
            if metric.target > 0:
                score = min(100, (metric.value / metric.target) * 100)
                scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _generate_recommendations(self, trends: dict[str, TrendAnalysis]) -> list[str]:
        """生成改进建议"""
        recommendations = []

        for metric_name, trend in trends.items():
            if trend.direction == TrendDirection.DECLINING and trend.significant:
                recommendations.append(
                    f"⚠️ {metric_name} 呈现下降趋势 ({trend.change_rate:.1%}), "
                    f"建议检查相关配置和数据处理流程"
                )
            elif trend.direction == TrendDirection.IMPROVING and trend.significant:
                recommendations.append(
                    f"✅ {metric_name} 持续改善 ({trend.change_rate:.1%}), "
                    f"当前策略有效,建议继续保持"
                )
            elif trend.direction == TrendDirection.STABLE:
                metric = self.metrics.get(metric_name)
                if metric and metric.value < metric.target:
                    recommendations.append(
                        f"ℹ️ {metric_name} 保持稳定但未达目标 "
                        f"(当前: {metric.value:.2%}, 目标: {metric.target:.2%}), "
                        f"建议尝试新的优化策略"
                    )

        return recommendations[:10]  # 最多10条建议

    def _generate_summary(self, overall_score: float, trends: dict[str, TrendAnalysis]) -> str:
        """生成摘要"""
        improving_count = sum(1 for t in trends.values() if t.direction == TrendDirection.IMPROVING)
        declining_count = sum(1 for t in trends.values() if t.direction == TrendDirection.DECLINING)
        stable_count = sum(1 for t in trends.values() if t.direction == TrendDirection.STABLE)

        summary = "学习效果评估报告\n"
        summary += f"总体评分: {overall_score:.1f}/100\n"
        summary += (
            f"趋势概览: 改善({improving_count}), 下降({declining_count}), 稳定({stable_count})\n"
        )

        if overall_score >= 90:
            summary += "整体表现优秀,继续保持!"
        elif overall_score >= 80:
            summary += "整体表现良好,仍有优化空间。"
        elif overall_score >= 70:
            summary += "整体表现一般,需要重点优化下降指标。"
        else:
            summary += "整体表现较差,需要全面审查学习系统。"

        return summary

    def export_report_json(self, report: LearningReport) -> str:
        """导出报告为JSON"""
        data = {
            "report_id": report.report_id,
            "timestamp": report.timestamp.isoformat(),
            "overall_score": report.overall_score,
            "metrics": {
                name: {"value": m.value, "baseline": m.baseline, "target": m.target, "unit": m.unit}
                for name, m in report.metrics.items()
            },
            "trends": {
                name: {
                    "direction": t.direction.value,
                    "change_rate": t.change_rate,
                    "confidence": t.confidence,
                    "significant": t.significant,
                }
                for name, t in report.trends.items()
            },
            "recommendations": report.recommendations,
            "summary": report.summary,
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_latest_report(self) -> LearningReport | None:
        """获取最新报告"""
        return self.reports[-1] if self.reports else None

    def get_all_reports(self) -> list[LearningReport]:
        """获取所有报告"""
        return self.reports.copy()


# 单例实例
_evaluator_instance: LearningEvaluator | None = None


def get_learning_evaluator() -> LearningEvaluator:
    """获取学习效果评估器单例"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = LearningEvaluator()
        logger.info("学习效果评估器已初始化")
    return _evaluator_instance


@async_main
async def main():
    """测试主函数"""
    evaluator = get_learning_evaluator()

    print("=== 学习效果评估测试 ===\n")

    # 记录一些指标
    print("记录指标...")
    evaluator.record_metric("intent_accuracy", 0.97, "")
    evaluator.record_metric("tool_selection_accuracy", 0.91, "")
    evaluator.record_metric("parameter_extraction_accuracy", 0.78, "")
    evaluator.record_metric("avg_latency_ms", 180, "ms")
    evaluator.record_metric("success_rate", 0.75, "")

    # 模拟历史数据
    for i in range(20):
        evaluator.record_metric("intent_accuracy", 0.95 + i * 0.001)
        evaluator.record_metric("tool_selection_accuracy", 0.88 + i * 0.0015)

    # 生成报告
    print("\n生成学习报告...")
    report = evaluator.generate_report()

    print(f"\n=== {report.summary} ===")

    print("\n推荐建议:")
    for rec in report.recommendations:
        print(f"  {rec}")

    # 导出JSON
    json_report = evaluator.export_report_json(report)
    print(f"\nJSON报告:\n{json_report}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
