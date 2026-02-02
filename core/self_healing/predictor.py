#!/usr/bin/env python3
"""
故障预测器 (Failure Predictor)
基于系统指标进行预测性故障检测

作者: 小诺·双鱼公主
版本: v1.0.0
"""

import logging
import statistics
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """预测结果"""

    will_fail: bool
    probability: float  # 0-1
    predicted_time: datetime | None = None
    time_to_failure: str | None = None  # "5-10分钟"
    confidence: str = "low"  # low, medium, high
    factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class MetricBaseline:
    """指标基线"""

    metric_name: str
    mean: float
    std_dev: float
    min_value: float
    max_value: float
    sample_size: int
    last_updated: datetime


class FailurePredictor:
    """
    故障预测器

    功能:
    1. 收集系统指标历史数据
    2. 建立指标基线
    3. 检测异常模式
    4. 预测潜在故障
    """

    def __init__(
        self,
        window_size: int = 100,
        anomaly_threshold: float = 2.5,
        prediction_horizon_minutes: int = 10,
    ):
        self.name = "故障预测器"
        self.version = "1.0.0"
        self.window_size = window_size
        self.anomaly_threshold = anomaly_threshold
        self.prediction_horizon = timedelta(minutes=prediction_horizon_minutes)

        # 历史数据存储
        self.metrics_history: dict[str, deque] = {}
        self.baselines: dict[str, MetricBaseline] = {}

        # 预测统计
        self.predictions_made = 0
        self.correct_predictions = 0
        self.false_alarms = 0

        logger.info(
            f"✅ {self.name} 初始化完成 (窗口大小={window_size}, 阈值={anomaly_threshold}σ)"
        )

    async def collect_metrics(self, metrics: dict[str, float]) -> None:
        """
        收集系统指标

        Args:
            metrics: 指标字典,如 {"cpu_usage": 75.5, "memory_usage": 82.3}
        """
        timestamp = datetime.now()

        for metric_name, value in metrics.items():
            # 初始化deque
            if metric_name not in self.metrics_history:
                self.metrics_history[metric_name] = deque(maxlen=self.window_size)

            # 添加数据点
            self.metrics_history[metric_name].append({"value": value, "timestamp": timestamp})

            # 更新基线
            await self._update_baseline(metric_name)

    async def _update_baseline(self, metric_name: str) -> None:
        """更新指标基线"""
        history = self.metrics_history.get(metric_name)
        if not history or len(history) < 10:
            return

        values = [point["value"] for point in history]

        self.baselines[metric_name] = MetricBaseline(
            metric_name=metric_name,
            mean=statistics.mean(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0,
            min_value=min(values),
            max_value=max(values),
            sample_size=len(values),
            last_updated=datetime.now(),
        )

    async def predict_failure(self, metric_name: str | None = None) -> PredictionResult:
        """
        预测故障

        Args:
            metric_name: 指定要预测的指标,None表示综合预测

        Returns:
            预测结果
        """
        if metric_name:
            return await self._predict_single_metric(metric_name)
        else:
            return await self._predict_comprehensive()

    async def _predict_single_metric(self, metric_name: str) -> PredictionResult:
        """预测单个指标的故障"""
        history = self.metrics_history.get(metric_name)
        baseline = self.baselines.get(metric_name)

        if not history or len(history) < 10:
            return PredictionResult(
                will_fail=False, probability=0.0, confidence="low", factors=["数据不足"]
            )

        # 检测异常
        latest_value = history[-1]["value"]
        z_score = 0
        if baseline and baseline.std_dev > 0:
            z_score = abs(latest_value - baseline.mean) / baseline.std_dev

        # 分析趋势
        trend = self._analyze_trend(list(history))

        # 计算故障概率
        probability = 0.0
        factors = []
        recommendations = []

        # 异常检测
        if z_score > self.anomaly_threshold:
            probability += 0.4
            factors.append(f"{metric_name} 异常 (z-score={z_score:.2f})")
            recommendations.append(f"检查 {metric_name} 相关服务")

        # 趋势分析
        if trend == "degrading":
            probability += 0.3
            factors.append(f"{metric_name} 呈恶化趋势")
            recommendations.append(f"优化 {metric_name} 使用")
        elif trend == "improving":
            probability -= 0.1

        # 临界值检测
        if baseline and latest_value > baseline.max_value * 0.95:
            probability += 0.2
            factors.append(f"{metric_name} 接近历史最大值")

        probability = max(0, min(1, probability))

        # 置信度评估
        confidence = "low"
        if len(history) > 50:
            confidence = "medium"
        if len(history) > 80 and baseline.std_dev > 0:
            confidence = "high"

        # 预测故障时间
        predicted_time = None
        time_to_failure = None

        if probability > 0.6:
            predicted_time = datetime.now() + self.prediction_horizon
            time_to_failure = f"{self.prediction_horizon.seconds // 60}分钟内"

        self.predictions_made += 1

        return PredictionResult(
            will_fail=probability > 0.5,
            probability=probability,
            predicted_time=predicted_time,
            time_to_failure=time_to_failure,
            confidence=confidence,
            factors=factors,
            recommendations=recommendations,
        )

    async def _predict_comprehensive(self) -> PredictionResult:
        """综合预测所有指标"""
        if not self.metrics_history:
            return PredictionResult(
                will_fail=False, probability=0.0, confidence="low", factors=["无指标数据"]
            )

        # 预测各个指标
        all_predictions = []
        all_factors = []
        all_recommendations = []

        for metric_name in self.metrics_history:
            prediction = await self._predict_single_metric(metric_name)
            all_predictions.append(prediction)
            all_factors.extend(prediction.factors)
            all_recommendations.extend(prediction.recommendations)

        if not all_predictions:
            return PredictionResult(will_fail=False, probability=0.0, confidence="low")

        # 综合概率(加权平均)
        total_prob = sum(p.probability for p in all_predictions)
        avg_prob = total_prob / len(all_predictions)

        # 最严重的预测时间
        predicted_times = [p.predicted_time for p in all_predictions if p.predicted_time]
        predicted_time = min(predicted_times) if predicted_times else None

        # 置信度(取最高)
        confidence_order = {"low": 0, "medium": 1, "high": 2}
        max_confidence = max(all_predictions, key=lambda p: confidence_order[p.confidence])
        confidence = max_confidence.confidence

        return PredictionResult(
            will_fail=avg_prob > 0.5,
            probability=avg_prob,
            predicted_time=predicted_time,
            time_to_failure=(
                f"{self.prediction_horizon.seconds // 60}分钟内" if predicted_time else None
            ),
            confidence=confidence,
            factors=list(set(all_factors)),
            recommendations=list(set(all_recommendations)),
        )

    def _analyze_trend(self, history: list[dict]) -> str:
        """
        分析指标趋势

        Returns:
            "improving", "stable", 或 "degrading"
        """
        if len(history) < 5:
            return "stable"

        # 取最近10个点
        recent = history[-10:] if len(history) >= 10 else history
        values = [point["value"] for point in recent]

        # 计算线性回归斜率
        n = len(values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        if n * sum_x2 - sum_x**2 == 0:
            return "stable"

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)

        # 归一化斜率
        avg_value = sum_y / n if n > 0 else 1
        normalized_slope = slope / avg_value if avg_value != 0 else 0

        # 判断趋势
        if normalized_slope > 0.05:  # 增长超过5%
            return "degrading"
        elif normalized_slope < -0.05:  # 下降超过5%
            return "improving"
        else:
            return "stable"

    def get_metrics_status(self) -> dict[str, Any]:
        """获取指标状态"""
        return {
            "name": self.name,
            "version": self.version,
            "metrics_tracked": len(self.metrics_history),
            "baselines_established": len(self.baselines),
            "prediction_accuracy": (
                self.correct_predictions / self.predictions_made if self.predictions_made > 0 else 0
            ),
            "predictions_made": self.predictions_made,
            "false_alarm_rate": (
                self.false_alarms / self.predictions_made if self.predictions_made > 0 else 0
            ),
            "metrics": {
                name: {
                    "samples": len(history),
                    "latest": history[-1]["value"] if history else None,
                    "baseline": (
                        {
                            "mean": baseline.mean,
                            "std_dev": baseline.std_dev,
                            "min": baseline.min_value,
                            "max": baseline.max_value,
                        }
                        if baseline
                        else None
                    ),
                }
                for name, history in self.metrics_history.items()
                for baseline in [self.baselines.get(name)]
            },
        }


# 全局单例
_predictor_instance: FailurePredictor | None = None


def get_failure_predictor() -> FailurePredictor:
    """获取故障预测器实例"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = FailurePredictor()
    return _predictor_instance
