#!/usr/bin/env python3
"""
P0: 自主学习 - 性能监控系统
Autonomous Learning - Performance Monitoring System

实现系统级性能监控和自动优化:
1. 实时性能监控 (准确率、响应时间、置信度)
2. 异常检测 (性能下降)
3. 自动优化触发
4. 性能报告生成

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

from __future__ import annotations
import json
import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class PerformanceLevel(Enum):
    """性能等级"""
    EXCELLENT = "excellent"  # 优秀 (>90%)
    GOOD = "good"           # 良好 (80-90%)
    FAIR = "fair"           # 一般 (70-80%)
    POOR = "poor"           # 较差 (<70%)


class AlertType(Enum):
    """告警类型"""
    ACCURACY_DROP = "accuracy_drop"       # 准确率下降
    HIGH_LATENCY = "high_latency"         # 高延迟
    LOW_CONFIDENCE = "low_confidence"     # 低置信度
    MODEL_DRIFT = "model_drift"           # 模型漂移


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: datetime
    accuracy: float
    avg_response_time_ms: float
    avg_confidence: float
    total_predictions: int
    error_count: int
    level: PerformanceLevel


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    alert_type: AlertType
    severity: str  # info, warning, critical
    message: str
    timestamp: datetime
    metrics: dict[str, Any]
    suggested_actions: list[str] = field(default_factory=list)


class PerformanceMonitor:
    """
    性能监控器

    监控意图识别系统的性能指标，检测异常并触发优化
    """

    def __init__(
        self,
        window_size: int = 1000,  # 滑动窗口大小
        accuracy_threshold: float = 0.70,  # 准确率阈值
        latency_threshold_ms: float = 500.0,  # 延迟阈值
        confidence_threshold: float = 0.60,  # 置信度阈值
    ):
        """
        初始化性能监控器

        Args:
            window_size: 滑动窗口大小
            accuracy_threshold: 准确率阈值
            latency_threshold_ms: 延迟阈值 (毫秒)
            confidence_threshold: 置信度阈值
        """
        self.window_size = window_size
        self.accuracy_threshold = accuracy_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.confidence_threshold = confidence_threshold

        # 滑动窗口数据
        self.predictions: deque[dict[str, Any]] = deque(maxlen=window_size)

        # 历史快照
        self.snapshots: deque[PerformanceSnapshot] = deque(maxlen=100)

        # 告警列表
        self.alerts: deque[PerformanceAlert] = deque(maxlen=500)

        # 回调函数
        self.alert_callbacks: list[Callable] = []

        # 基线性能
        self.baseline_accuracy = 0.85
        self.baseline_latency_ms = 100.0

        logger.info(
            f"📊 性能监控器初始化: "
            f"窗口={window_size}, "
            f"准确率阈值={accuracy_threshold:.0%}, "
            f"延迟阈值={latency_threshold_ms}ms"
        )

    def record_prediction(
        self,
        query: str,
        predicted_intent: str,
        true_intent: str | None,
        confidence: float,
        response_time_ms: float,
    ) -> dict[str, Any]:
        """
        记录一次预测

        Args:
            query: 查询文本
            predicted_intent: 预测意图
            true_intent: 真实意图
            confidence: 置信度
            response_time_ms: 响应时间

        Returns:
            当前性能指标
        """
        # 判断是否正确
        correct = (true_intent is None) or (predicted_intent == true_intent)

        # 记录预测
        prediction = {
            "timestamp": datetime.now(),
            "query": query,
            "predicted_intent": predicted_intent,
            "true_intent": true_intent,
            "confidence": confidence,
            "response_time_ms": response_time_ms,
            "correct": correct,
        }

        self.predictions.append(prediction)

        # 计算当前性能
        metrics = self._calculate_metrics()

        # 检查是否需要告警
        self._check_and_alert(metrics)

        return metrics

    def _calculate_metrics(self) -> dict[str, Any]:
        """计算当前性能指标"""
        if not self.predictions:
            return {
                "accuracy": 0.0,
                "avg_response_time_ms": 0.0,
                "avg_confidence": 0.0,
                "total_predictions": 0,
                "error_count": 0,
                "level": PerformanceLevel.FAIR,
            }

        predictions_list = list(self.predictions)

        # 准确率
        correct_count = sum(1 for p in predictions_list if p["correct"])
        accuracy = correct_count / len(predictions_list)

        # 平均响应时间
        avg_response_time = np.mean([p["response_time_ms"] for p in predictions_list])

        # 平均置信度
        avg_confidence = np.mean([p["confidence"] for p in predictions_list])

        # 错误数量
        error_count = len(predictions_list) - correct_count

        # 性能等级
        if accuracy >= 0.90:
            level = PerformanceLevel.EXCELLENT
        elif accuracy >= 0.80:
            level = PerformanceLevel.GOOD
        elif accuracy >= 0.70:
            level = PerformanceLevel.FAIR
        else:
            level = PerformanceLevel.POOR

        # 创建快照
        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            accuracy=accuracy,
            avg_response_time_ms=avg_response_time,
            avg_confidence=avg_confidence,
            total_predictions=len(predictions_list),
            error_count=error_count,
            level=level,
        )

        self.snapshots.append(snapshot)

        return {
            "accuracy": accuracy,
            "avg_response_time_ms": avg_response_time,
            "avg_confidence": avg_confidence,
            "total_predictions": len(predictions_list),
            "error_count": error_count,
            "level": level,
        }

    def _check_and_alert(self, metrics: dict[str, Any]):
        """检查性能并生成告警"""
        accuracy = metrics["accuracy"]
        avg_latency = metrics["avg_response_time_ms"]
        avg_confidence = metrics["avg_confidence"]
        level = metrics["level"]

        # 1. 准确率下降告警
        if accuracy < self.accuracy_threshold:
            self._create_alert(
                AlertType.ACCURACY_DROP,
                "critical" if accuracy < 0.6 else "warning",
                f"准确率下降至 {accuracy:.1%}，低于阈值 {self.accuracy_threshold:.0%}",
                {
                    "current_accuracy": accuracy,
                    "threshold": self.accuracy_threshold,
                    "baseline": self.baseline_accuracy,
                },
                [
                    "检查训练数据质量",
                    "增加模型训练轮数",
                    "调整模型超参数",
                    "收集更多标注数据",
                ],
            )

        # 2. 高延迟告警
        if avg_latency > self.latency_threshold_ms:
            self._create_alert(
                AlertType.HIGH_LATENCY,
                "warning",
                f"平均响应时间 {avg_latency:.0f}ms，超过阈值 {self.latency_threshold_ms:.0f}ms",
                {
                    "current_latency_ms": avg_latency,
                    "threshold_ms": self.latency_threshold_ms,
                    "baseline_ms": self.baseline_latency_ms,
                },
                [
                    "优化模型推理速度",
                    "使用模型量化或剪枝",
                    "增加批处理大小",
                    "使用GPU加速",
                ],
            )

        # 3. 低置信度告警
        if avg_confidence < self.confidence_threshold:
            self._create_alert(
                AlertType.LOW_CONFIDENCE,
                "info",
                f"平均置信度 {avg_confidence:.1%}，低于阈值 {self.confidence_threshold:.0%}",
                {
                    "current_confidence": avg_confidence,
                    "threshold": self.confidence_threshold,
                },
                [
                    "模型可能需要重新训练",
                    "检查输入数据质量",
                    "调整置信度阈值",
                ],
            )

        # 4. 模型漂移检测 (与基线对比)
        if len(self.snapshots) >= 10:
            recent_snapshots = list(self.snapshots)[-10:]
            recent_accuracy = np.mean([s.accuracy for s in recent_snapshots])

            if recent_accuracy < self.baseline_accuracy - 0.1:  # 下降超过10%
                self._create_alert(
                    AlertType.MODEL_DRIFT,
                    "critical",
                    f"检测到模型漂移，准确率从 {self.baseline_accuracy:.1%} 下降至 {recent_accuracy:.1%}",
                    {
                        "baseline_accuracy": self.baseline_accuracy,
                        "recent_accuracy": recent_accuracy,
                        "drift_amount": self.baseline_accuracy - recent_accuracy,
                    },
                    [
                        "重新训练模型",
                        "更新训练数据",
                        "检查数据分布变化",
                        "启动在线学习",
                    ],
                )

    def _create_alert(
        self,
        alert_type: AlertType,
        severity: str,
        message: str,
        metrics: dict[str, Any],        suggested_actions: list[str],
    ):
        """创建告警"""
        # 避免重复告警 (5分钟内相同类型的告警只保留一个)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_alerts = [
            a for a in self.alerts
            if a.timestamp > cutoff_time and a.alert_type == alert_type
        ]

        if recent_alerts:
            return  # 已存在相同类型的告警

        alert = PerformanceAlert(
            alert_id=f"{alert_type.value}_{int(datetime.now().timestamp())}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            metrics=metrics,
            suggested_actions=suggested_actions,
        )

        self.alerts.append(alert)

        # 触发回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")

        # 记录日志
        log_level = {
            "critical": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
        }.get(severity, logging.INFO)

        logger.log(log_level, f"🚨 {alert_type.value.upper()}: {message}")

    def get_current_performance(self) -> dict[str, Any]:
        """获取当前性能"""
        if not self.snapshots:
            return {}

        latest = self.snapshots[-1]
        return {
            "timestamp": latest.timestamp.isoformat(),
            "accuracy": latest.accuracy,
            "avg_response_time_ms": latest.avg_response_time_ms,
            "avg_confidence": latest.avg_confidence,
            "total_predictions": latest.total_predictions,
            "error_count": latest.error_count,
            "level": latest.level.value,
            "baseline_accuracy": self.baseline_accuracy,
            "accuracy_delta": latest.accuracy - self.baseline_accuracy,
        }

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """获取活跃告警"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        active_alerts = [
            {
                "alert_id": a.alert_id,
                "type": a.alert_type.value,
                "severity": a.severity,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
                "metrics": a.metrics,
                "suggested_actions": a.suggested_actions,
            }
            for a in self.alerts
            if a.timestamp > cutoff_time
        ]

        return active_alerts

    def get_performance_trend(self, hours: int = 24) -> dict[str, Any]:
        """获取性能趋势"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        relevant_snapshots = [
            s for s in self.snapshots
            if s.timestamp > cutoff_time
        ]

        if not relevant_snapshots:
            return {}

        accuracies = [s.accuracy for s in relevant_snapshots]
        latencies = [s.avg_response_time_ms for s in relevant_snapshots]

        return {
            "period_hours": hours,
            "snapshots_count": len(relevant_snapshots),
            "accuracy": {
                "min": float(np.min(accuracies)),
                "max": float(np.max(accuracies)),
                "mean": float(np.mean(accuracies)),
                "std": float(np.std(accuracies)),
                "trend": "improving" if accuracies[-1] > accuracies[0] else "declining",
            },
            "latency_ms": {
                "min": float(np.min(latencies)),
                "max": float(np.max(latencies)),
                "mean": float(np.mean(latencies)),
                "std": float(np.std(latencies)),
            },
        }

    def generate_report(self, filepath: str | None = None) -> str:
        """生成性能报告"""
        if filepath is None:
            filepath = f"data/performance_report_{int(datetime.now().timestamp())}.json"

        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        report = {
            "report_time": datetime.now().isoformat(),
            "current_performance": self.get_current_performance(),
            "active_alerts": self.get_active_alerts(),
            "performance_trend": self.get_performance_trend(hours=24),
            "summary": {
                "total_predictions": len(self.predictions),
                "total_alerts": len(self.alerts),
                "performance_level": self.snapshots[-1].level.value if self.snapshots else "unknown",
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 性能报告已生成: {filepath}")
        return filepath

    def register_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """注册告警回调函数"""
        self.alert_callbacks.append(callback)

    def update_baseline(self, accuracy: float, latency_ms: float):
        """更新基线性能"""
        self.baseline_accuracy = accuracy
        self.baseline_latency_ms = latency_ms
        logger.info(
            f"📊 更新基线性能: "
            f"准确率={accuracy:.1%}, "
            f"延迟={latency_ms:.0f}ms"
        )
