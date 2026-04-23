#!/usr/bin/env python3
from __future__ import annotations
"""
预测性错误检测器
Predictive Error Detector

增强错误预测能力:
1. 基于历史数据的错误预测
2. 实时风险评分
3. 早期预警系统
4. 模式识别与异常检测
5. 因果关系分析
6. 自动预防措施建议

作者: Athena平台团队
创建时间: 2025-12-27
版本: v2.0.0 "智能预测"
"""

import logging
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""

    NONE = "none"  # 无风险
    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


class ErrorPattern(Enum):
    """错误模式"""

    TIMEOUT = "timeout"  # 超时模式
    RATE_LIMIT = "rate_limit"  # 限流模式
    RESOURCE_EXHAUSTION = "resource"  # 资源耗尽
    DEPENDENCY_FAILURE = "dependency"  # 依赖失败
    INVALID_INPUT = "invalid_input"  # 无效输入
    CASCADE_FAILURE = "cascade"  # 级联失败
    PERFORMANCE_DEGRADATION = "performance"  # 性能下降


@dataclass
class ErrorPrediction:
    """错误预测结果"""

    error_type: ErrorPattern
    risk_level: RiskLevel
    probability: float  # 0-1
    confidence: float  # 0-1
    predicted_time: datetime | None = None
    factors: dict[str, float] = field(default_factory=dict)
    prevention_suggestions: list[str] = field(default_factory=list)
    estimated_impact: str = ""


@dataclass
class ErrorMetrics:
    """错误指标"""

    error_count: int = 0
    frequency: float = 0.0  # 错误频率(次/小时)
    avg_recovery_time: float = 0.0
    last_occurrence: datetime | None = None
    trend: str = "stable"  # increasing, decreasing, stable


class PredictiveErrorDetector:
    """
    预测性错误检测器

    核心能力:
    1. 基于历史数据预测错误
    2. 实时风险评估
    3. 早期预警
    4. 模式识别
    5. 自动预防建议
    """

    def __init__(self, window_size: int = 1000):
        # 错误历史
        self.error_history: deque = deque(maxlen=window_size)

        # 错误模式统计
        self.error_patterns: dict[ErrorPattern, ErrorMetrics] = defaultdict(lambda: ErrorMetrics())

        # 风险阈值
        self.risk_thresholds = {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.9,
        }

        # 预测模型(简化版)
        self.prediction_models: dict[ErrorPattern, dict] = {}

        # 系统状态监控
        self.system_metrics: deque = deque(maxlen=100)

        # 预警规则
        self.alert_rules: list[Callable] = []

        logger.info("🔮 预测性错误检测器初始化完成")

    async def predict_errors(
        self, current_context: dict[str, Any], time_horizon: timedelta = timedelta(minutes=10)
    ) -> list[ErrorPrediction]:
        """
        预测未来可能发生的错误

        Args:
            current_context: 当前上下文
            time_horizon: 预测时间范围

        Returns:
            错误预测列表
        """
        predictions = []

        # 更新系统指标
        await self._update_system_metrics(current_context)

        # 对每种错误模式进行预测
        for error_pattern in ErrorPattern:
            prediction = await self._predict_error_pattern(
                error_pattern, current_context, time_horizon
            )

            if prediction.probability > self.risk_thresholds[RiskLevel.LOW]:
                predictions.append(prediction)

        # 按风险等级排序
        predictions.sort(key=lambda p: p.probability, reverse=True)

        return predictions

    async def _predict_error_pattern(
        self, error_pattern: ErrorPattern, context: dict[str, Any], time_horizon: timedelta
    ) -> ErrorPrediction:
        """预测特定错误模式"""
        metrics = self.error_patterns[error_pattern]

        # 基础概率(基于历史频率)
        base_probability = min(1.0, metrics.frequency * 0.1)

        # 调整因子
        factors = {}

        # 1. 趋势因子
        trend_factor = await self._compute_trend_factor(error_pattern)
        factors["trend"] = trend_factor

        # 2. 时间因子(距离上次错误的时间)
        time_factor = await self._compute_time_factor(metrics)
        factors["time_since_last"] = time_factor

        # 3. 上下文因子
        context_factor = await self._compute_context_factor(error_pattern, context)
        factors["context"] = context_factor

        # 4. 系统状态因子
        system_factor = await self._compute_system_factor(error_pattern)
        factors["system"] = system_factor

        # 综合概率
        probability = (
            base_probability
            * (1.0 + trend_factor + time_factor + context_factor + system_factor)
            / 5.0
        )
        probability = min(1.0, max(0.0, probability))

        # 风险等级
        risk_level = self._compute_risk_level(probability)

        # 置信度(基于数据量)
        confidence = min(1.0, metrics.error_count / 100)

        # 预测时间
        predicted_time = None
        if probability > 0.5:
            predicted_time = datetime.now() + time_horizon * (1.0 - probability)

        # 预防建议
        prevention = await self._generate_prevention_suggestions(
            error_pattern, probability, context
        )

        # 预估影响
        impact = await self._estimate_impact(error_pattern, probability)

        return ErrorPrediction(
            error_type=error_pattern,
            risk_level=risk_level,
            probability=probability,
            confidence=confidence,
            predicted_time=predicted_time,
            factors=factors,
            prevention_suggestions=prevention,
            estimated_impact=impact,
        )

    async def _compute_trend_factor(self, error_pattern: ErrorPattern) -> float:
        """计算趋势因子"""
        metrics = self.error_patterns[error_pattern]

        if metrics.trend == "increasing":
            return 0.3
        elif metrics.trend == "decreasing":
            return -0.3
        else:
            return 0.0

    async def _compute_time_factor(self, metrics: ErrorMetrics) -> float:
        """计算时间因子"""
        if metrics.last_occurrence is None:
            return 0.0

        time_since_last = (datetime.now() - metrics.last_occurrence).total_seconds()

        # 如果最近发生过错误,因子较高
        if time_since_last < 300:  # 5分钟内
            return 0.4
        elif time_since_last < 3600:  # 1小时内
            return 0.2
        else:
            return 0.0

    async def _compute_context_factor(
        self, error_pattern: ErrorPattern, context: dict[str, Any]
    ) -> float:
        """计算上下文因子"""
        factor = 0.0

        # 根据错误模式检查上下文
        if error_pattern == ErrorPattern.TIMEOUT:
            # 检查是否有大量并发请求
            concurrent_requests = context.get("concurrent_requests", 0)
            if concurrent_requests > 100:
                factor += 0.3

        elif error_pattern == ErrorPattern.RATE_LIMIT:
            # 检查请求频率
            request_rate = context.get("request_rate", 0)
            if request_rate > 1000:  # 每分钟1000次
                factor += 0.4

        elif error_pattern == ErrorPattern.RESOURCE_EXHAUSTION:
            # 检查资源使用率
            cpu_usage = context.get("cpu_usage", 0)
            memory_usage = context.get("memory_usage", 0)

            if cpu_usage > 80:
                factor += 0.3
            if memory_usage > 80:
                factor += 0.3

        return min(1.0, factor)

    async def _compute_system_factor(self, error_pattern: ErrorPattern) -> float:
        """计算系统状态因子"""
        if not self.system_metrics:
            return 0.0

        # 分析最近的系统指标
        recent_metrics = list(self.system_metrics)[-10:]

        # 计算异常程度
        anomalies = 0
        for metric in recent_metrics:
            if metric.get("anomaly", False):
                anomalies += 1

        anomaly_ratio = anomalies / len(recent_metrics)

        # 异常越多,因子越高
        return anomaly_ratio * 0.5

    def _compute_risk_level(self, probability: float) -> RiskLevel:
        """计算风险等级"""
        if probability >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif probability >= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif probability >= self.risk_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        elif probability >= self.risk_thresholds[RiskLevel.LOW]:
            return RiskLevel.LOW
        else:
            return RiskLevel.NONE

    async def _generate_prevention_suggestions(
        self, error_pattern: ErrorPattern, probability: float, context: dict[str, Any]
    ) -> list[str]:
        """生成预防建议"""
        suggestions = []

        if error_pattern == ErrorPattern.TIMEOUT:
            suggestions.extend(
                ["增加超时时间设置", "优化请求参数大小", "考虑分批处理", "检查网络连接状态"]
            )

        elif error_pattern == ErrorPattern.RATE_LIMIT:
            suggestions.extend(
                ["实施请求限流", "添加请求队列", "使用指数退避重试", "考虑升级服务套餐"]
            )

        elif error_pattern == ErrorPattern.RESOURCE_EXHAUSTION:
            suggestions.extend(["优化资源使用", "清理临时文件", "增加系统资源", "实施负载均衡"])

        elif error_pattern == ErrorPattern.DEPENDENCY_FAILURE:
            suggestions.extend(["检查依赖服务状态", "实现降级方案", "添加本地缓存", "配置备用服务"])

        elif error_pattern == ErrorPattern.INVALID_INPUT:
            suggestions.extend(["增强输入验证", "提供输入示例", "添加格式提示", "实现自动纠错"])

        elif error_pattern == ErrorPattern.CASCADE_FAILURE:
            suggestions.extend(["实施断路器模式", "设置超时和重试", "隔离关键服务", "建立监控告警"])

        elif error_pattern == ErrorPattern.PERFORMANCE_DEGRADATION:
            suggestions.extend(
                ["性能剖析和优化", "缓存热点数据", "异步处理耗时操作", "升级硬件配置"]
            )

        # 根据概率筛选建议
        if probability > 0.7:
            return suggestions[:4]  # 高风险:所有建议
        elif probability > 0.5:
            return suggestions[:3]  # 中风险:主要建议
        else:
            return suggestions[:2]  # 低风险:关键建议

    async def _estimate_impact(self, error_pattern: ErrorPattern, probability: float) -> str:
        """预估错误影响"""
        if probability > 0.8:
            return f"严重:{error_pattern.value} 可能导致服务完全中断"
        elif probability > 0.6:
            return f"显著:{error_pattern.value} 可能影响大部分功能"
        elif probability > 0.4:
            return f"中等:{error_pattern.value} 可能影响部分功能"
        else:
            return f"轻微:{error_pattern.value} 影响有限"

    async def record_error(
        self,
        error_pattern: ErrorPattern,
        context: Optional[dict[str, Any]] = None,
        recovery_time: Optional[float] = None,
    ):
        """记录错误发生"""
        metrics = self.error_patterns[error_pattern]

        # 更新计数
        metrics.error_count += 1

        # 更新最后发生时间
        metrics.last_occurrence = datetime.now()

        # 更新恢复时间
        if recovery_time is not None:
            if metrics.avg_recovery_time == 0:
                metrics.avg_recovery_time = recovery_time
            else:
                metrics.avg_recovery_time = metrics.avg_recovery_time * 0.9 + recovery_time * 0.1

        # 计算频率
        await self._update_frequency(error_pattern)

        # 记录到历史
        self.error_history.append(
            {"pattern": error_pattern, "timestamp": datetime.now(), "context": context or {}}
        )

        logger.info(f"📊 错误已记录: {error_pattern.value} (总计: {metrics.error_count})")

    async def _update_frequency(self, error_pattern: ErrorPattern):
        """更新错误频率"""
        metrics = self.error_patterns[error_pattern]

        # 计算最近1小时的错误数
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = [
            e
            for e in self.error_history
            if e["pattern"] == error_pattern and e["timestamp"] > one_hour_ago
        ]

        metrics.frequency = len(recent_errors)

        # 更新趋势
        await self._update_trend(error_pattern)

    async def _update_trend(self, error_pattern: ErrorPattern):
        """更新错误趋势"""
        metrics = self.error_patterns[error_pattern]

        # 比较最近30分钟和前30分钟
        now = datetime.now()
        recent_30 = [
            e
            for e in self.error_history
            if e["pattern"] == error_pattern and now - timedelta(minutes=30) < e["timestamp"] <= now
        ]

        previous_30 = [
            e
            for e in self.error_history
            if e["pattern"] == error_pattern
            and now - timedelta(minutes=60) < e["timestamp"] <= now - timedelta(minutes=30)
        ]

        recent_count = len(recent_30)
        previous_count = len(previous_30)

        if recent_count > previous_count * 1.5:
            metrics.trend = "increasing"
        elif recent_count < previous_count * 0.5:
            metrics.trend = "decreasing"
        else:
            metrics.trend = "stable"

    async def _update_system_metrics(self, context: dict[str, Any]):
        """更新系统指标"""
        # 提取系统指标
        metrics = {
            "timestamp": datetime.now(),
            "cpu_usage": context.get("cpu_usage", 0),
            "memory_usage": context.get("memory_usage", 0),
            "request_rate": context.get("request_rate", 0),
            "concurrent_requests": context.get("concurrent_requests", 0),
            "anomaly": False,  # 可以添加异常检测逻辑
        }

        # 简单的异常检测
        if self.system_metrics:
            last_metrics = self.system_metrics[-1]

            # 检查CPU突然升高
            if metrics["cpu_usage"] > last_metrics.get("cpu_usage", 0) + 20:
                metrics["anomaly"] = True

            # 检查内存突然升高
            if metrics["memory_usage"] > last_metrics.get("memory_usage", 0) + 20:
                metrics["anomaly"] = True

        self.system_metrics.append(metrics)

    async def get_risk_assessment(self) -> dict[str, Any]:
        """获取综合风险评估"""
        # 预测未来错误
        predictions = await self.predict_errors({})

        # 计算整体风险
        if not predictions:
            overall_risk = RiskLevel.NONE
        else:
            max_prob = max(p.probability for p in predictions)
            overall_risk = self._compute_risk_level(max_prob)

        # 统计各风险等级的错误数
        risk_distribution = defaultdict(int)
        for pred in predictions:
            risk_distribution[pred.risk_level] += 1

        return {
            "overall_risk": overall_risk.value,
            "total_predictions": len(predictions),
            "risk_distribution": dict(risk_distribution),
            "high_risk_errors": [
                p.error_type.value
                for p in predictions
                if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            ],
            "recommendations": [
                suggestion
                for p in predictions
                if p.probability > 0.5
                for suggestion in p.prevention_suggestions
            ][:5],
        }

    async def detect_anomalies(self) -> list[dict[str, Any]]:
        """检测系统异常"""
        anomalies = []

        if len(self.system_metrics) < 10:
            return anomalies

        # 提取最近的指标
        recent_metrics = list(self.system_metrics)[-10:]

        # 检测CPU异常
        cpu_values = [m["cpu_usage"] for m in recent_metrics]
        cpu_mean = np.mean(cpu_values)
        cpu_std = np.std(cpu_values)

        for _i, metric in enumerate(recent_metrics):
            z_score = abs((metric["cpu_usage"] - cpu_mean) / (cpu_std + 1e-8))
            if z_score > 2:  # 2个标准差之外
                anomalies.append(
                    {
                        "type": "cpu_spike",
                        "timestamp": metric["timestamp"],
                        "value": metric["cpu_usage"],
                        "z_score": z_score,
                    }
                )

        # 检测内存异常
        memory_values = [m["memory_usage"] for m in recent_metrics]
        memory_mean = np.mean(memory_values)
        memory_std = np.std(memory_values)

        for _i, metric in enumerate(recent_metrics):
            z_score = abs((metric["memory_usage"] - memory_mean) / (memory_std + 1e-8))
            if z_score > 2:
                anomalies.append(
                    {
                        "type": "memory_spike",
                        "timestamp": metric["timestamp"],
                        "value": metric["memory_usage"],
                        "z_score": z_score,
                    }
                )

        return anomalies

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_errors": sum(m.error_count for m in self.error_patterns.values()),
            "patterns_detected": len(self.error_patterns),
            "avg_recovery_time": (
                np.mean(
                    [
                        m.avg_recovery_time
                        for m in self.error_patterns.values()
                        if m.avg_recovery_time > 0
                    ]
                )
                if any(m.avg_recovery_time > 0 for m in self.error_patterns.values())
                else 0
            ),
            "most_frequent_error": (
                max(
                    self.error_patterns.items(),
                    key=lambda x: x[1].error_count,
                    default=(None, ErrorMetrics()),
                )[0].value
                if self.error_patterns
                else None
            ),
        }


# 导出便捷函数
_detector: PredictiveErrorDetector | None = None


def get_predictive_detector() -> PredictiveErrorDetector:
    """获取预测性错误检测器单例"""
    global _detector
    if _detector is None:
        _detector = PredictiveErrorDetector()
    return _detector
