from __future__ import annotations

# pyright: ignore
"""
决策历史分析器
分析决策模式,提供改进建议
"""
import json
import logging
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """决策类型"""

    TASK_ASSIGNMENT = "task_assignment"
    RESOURCE_ALLOCATION = "resource_allocation"
    PRIORITY_ADJUSTMENT = "priority_adjustment"
    ERROR_HANDLING = "error_handling"
    OPTIMIZATION = "optimization"
    ROUTINE = "routine"


class DecisionOutcome(Enum):
    """决策结果"""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


@dataclass
class DecisionRecord:
    """决策记录"""

    decision_id: str
    decision_type: DecisionType
    context: dict[str, Any]
    decision_data: dict[str, Any]
    outcome: DecisionOutcome
    execution_time: float
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    impact_score: float = 0.0
    reasoning_trace: list[str] = field(default_factory=list)
    feedback: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionPattern:
    """决策模式"""

    pattern_id: str
    pattern_type: str
    frequency: int
    avg_confidence: float
    success_rate: float
    avg_execution_time: float
    contexts: list[dict[str, Any]]
    last_seen: datetime
    improvement_potential: float = 0.0


@dataclass
class TrendAnalysis:
    """趋势分析"""

    metric_name: str
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0-1
    current_value: float
    historical_values: list[tuple[datetime, float]]
    prediction: Optional[float] = None
    confidence_interval: tuple[float, float] | None = None


class DecisionHistoryAnalyzer:
    """决策历史分析器"""

    def __init__(self, max_history: int = 10000):
        self.decision_history = deque(maxlen=max_history)
        self.patterns = {}
        self.trends = {}
        self.insights = []
        self.cache = {}
        self.last_analysis = None
        self.analysis_interval = timedelta(hours=1)

    async def record_decision(self, decision_record: DecisionRecord):
        """记录决策"""
        # 添加到历史记录
        self.decision_history.append(decision_record)

        # 更新模式
        await self._update_patterns(decision_record)

        # 清理过期缓存
        await self._cleanup_cache()

    async def _update_patterns(self, decision: DecisionRecord):
        """更新决策模式"""
        # 生成模式键
        pattern_key = self._generate_pattern_key(decision)

        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = DecisionPattern(
                pattern_id=f"pattern_{len(self.patterns)}",
                pattern_type=decision.decision_type.value,
                frequency=0,
                avg_confidence=0.0,
                success_rate=0.0,
                avg_execution_time=0.0,
                contexts=[],
                last_seen=decision.timestamp,
            )

        # 更新模式统计
        pattern = self.patterns[pattern_key]
        pattern.frequency += 1
        pattern.last_seen = decision.timestamp

        # 更新平均置信度
        pattern.avg_confidence = (
            pattern.avg_confidence * (pattern.frequency - 1) + decision.confidence
        ) / pattern.frequency

        # 更新成功率
        success_count = sum(
            1
            for d in self.decision_history
            if self._generate_pattern_key(d) == pattern_key and d.outcome == DecisionOutcome.SUCCESS
        )
        pattern.success_rate = success_count / pattern.frequency

        # 更新平均执行时间
        pattern.avg_execution_time = (
            pattern.avg_execution_time * (pattern.frequency - 1) + decision.execution_time
        ) / pattern.frequency

        # 保存上下文(限制数量)
        if len(pattern.contexts) < 10:
            pattern.contexts.append(decision.context.copy())

        # 计算改进潜力
        pattern.improvement_potential = self._calculate_improvement_potential(pattern)

    def _generate_pattern_key(self, decision: DecisionRecord) -> str:
        """生成模式键"""
        # 基于决策类型和关键上下文特征
        key_features = [
            decision.decision_type.value,
        ]

        # 添加上下文特征
        if "task_type" in decision.context:
            key_features.append(f"task:{decision.context['task_type']}")
        if "priority" in decision.context:
            key_features.append(f"priority:{decision.context['priority']}")
        if "error_type" in decision.context:
            key_features.append(f"error:{decision.context['error_type']}")

        return "|".join(key_features)

    def _calculate_improvement_potential(self, pattern: DecisionPattern) -> float:
        """计算改进潜力"""
        # 基于成功率和执行时间的改进潜力
        success_potential = 1.0 - pattern.success_rate
        time_potential = min(pattern.avg_execution_time / 10.0, 1.0)
        confidence_potential = 1.0 - pattern.avg_confidence

        # 加权平均
        return success_potential * 0.5 + time_potential * 0.3 + confidence_potential * 0.2

    async def analyze_patterns(self) -> list[DecisionPattern]:
        """分析决策模式"""
        if not self.decision_history:
            return []

        # 按改进潜力排序
        sorted_patterns = sorted(
            self.patterns.values(), key=lambda p: p.improvement_potential, reverse=True  # type: ignore
        )

        return sorted_patterns[:10]  # 返回前10个最有改进潜力的模式

    async def analyze_trends(self, days: int = 30) -> dict[str, TrendAnalysis]:
        """分析决策趋势"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_decisions = [d for d in self.decision_history if d.timestamp >= cutoff_date]

        if not recent_decisions:
            return {}

        trends = {}

        # 分析成功率趋势
        success_trend = await self._analyze_success_trend(recent_decisions)
        if success_trend:
            trends["success_rate"] = success_trend

        # 分析执行时间趋势
        time_trend = await self._analyze_execution_time_trend(recent_decisions)
        if time_trend:
            trends["execution_time"] = time_trend

        # 分析置信度趋势
        confidence_trend = await self._analyze_confidence_trend(recent_decisions)
        if confidence_trend:
            trends["confidence"] = confidence_trend

        # 分析决策频率趋势
        frequency_trend = await self._analyze_frequency_trend(recent_decisions)
        if frequency_trend:
            trends["frequency"] = frequency_trend

        self.trends = trends
        return trends

    async def _analyze_success_trend(
        self, decisions: list[DecisionRecord]
    ) -> TrendAnalysis | None:
        """分析成功率趋势"""
        # 按天分组计算成功率
        daily_success = defaultdict(list)
        for decision in decisions:
            date_key = decision.timestamp.date()
            daily_success[date_key].append(decision.outcome == DecisionOutcome.SUCCESS)

        if len(daily_success) < 3:
            return None

        # 计算每日成功率
        success_rates = []
        for date in sorted(daily_success.keys()):
            rate = sum(daily_success[date]) / len(daily_success[date])
            success_rates.append((datetime.combine(date, datetime.min.time()), rate))

        # 趋势分析
        return self._calculate_trend("success_rate", success_rates)

    async def _analyze_execution_time_trend(
        self, decisions: list[DecisionRecord]
    ) -> TrendAnalysis | None:
        """分析执行时间趋势"""
        # 按天分组计算平均执行时间
        daily_times = defaultdict(list)
        for decision in decisions:
            date_key = decision.timestamp.date()
            daily_times[date_key].append(decision.execution_time)

        if len(daily_times) < 3:
            return None

        # 计算每日平均执行时间
        avg_times = []
        for date in sorted(daily_times.keys()):
            avg = np.mean(daily_times[date])
            avg_times.append((datetime.combine(date, datetime.min.time()), avg))

        # 趋势分析
        return self._calculate_trend("execution_time", avg_times)

    async def _analyze_confidence_trend(
        self, decisions: list[DecisionRecord]
    ) -> TrendAnalysis | None:
        """分析置信度趋势"""
        # 按天分组计算平均置信度
        daily_confidence = defaultdict(list)
        for decision in decisions:
            date_key = decision.timestamp.date()
            daily_confidence[date_key].append(decision.confidence)

        if len(daily_confidence) < 3:
            return None

        # 计算每日平均置信度
        avg_confidence = []
        for date in sorted(daily_confidence.keys()):
            avg = np.mean(daily_confidence[date])
            avg_confidence.append((datetime.combine(date, datetime.min.time()), avg))

        # 趋势分析
        return self._calculate_trend("confidence", avg_confidence)

    async def _analyze_frequency_trend(
        self, decisions: list[DecisionRecord]
    ) -> TrendAnalysis | None:
        """分析决策频率趋势"""
        # 按天分组计算决策数量
        daily_count = defaultdict(int)
        for decision in decisions:
            date_key = decision.timestamp.date()
            daily_count[date_key] += 1

        if len(daily_count) < 3:
            return None

        # 计算每日决策频率
        frequencies = []
        for date in sorted(daily_count.keys()):
            frequencies.append((datetime.combine(date, datetime.min.time()), daily_count[date]))

        # 趋势分析
        return self._calculate_trend("frequency", frequencies)

    def _calculate_trend(
        self, metric_name: str, values: list[tuple[datetime, float]]
    ) -> TrendAnalysis:
        """计算趋势"""
        if len(values) < 2:
            return None

        # 提取时间序列
        times = [v[0].timestamp() for v in values]
        metric_values = [v[1] for v in values]

        # 线性回归计算趋势
        times_array = np.array(times)
        values_array = np.array(metric_values)

        # 归一化时间
        times_norm = (times_array - times_array[0]) / (times_array[-1] - times_array[0] + 1e-6)

        # 计算斜率
        coeffs = np.polyfit(times_norm, values_array, 1)
        slope = coeffs[0]

        # 确定趋势方向
        if slope > 0.05:
            trend_direction = "improving" if metric_name == "success_rate" else "increasing"
        elif slope < -0.05:
            trend_direction = "declining" if metric_name == "success_rate" else "decreasing"
        else:
            trend_direction = "stable"

        # 计算趋势强度
        trend_strength = min(abs(slope) * 10, 1.0)

        # 预测下一个值
        next_time_norm = 1.1  # 比最后时间点稍远
        prediction = np.polyval(coeffs, next_time_norm)

        # 计算置信区间
        residuals = values_array - np.polyval(coeffs, times_norm)
        std_error = np.std(residuals)
        confidence_interval = (prediction - 2 * std_error, prediction + 2 * std_error)

        return TrendAnalysis(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            current_value=metric_values[-1],
            historical_values=values,
            prediction=prediction,
            confidence_interval=confidence_interval,
        )

    async def generate_insights(self) -> list[dict[str, Any]]:
        """生成洞察"""
        insights = []

        # 分析模式
        patterns = await self.analyze_patterns()
        for pattern in patterns[:5]:  # 前5个最有改进潜力的模式
            if pattern.improvement_potential > 0.3:
                insight = {
                    "type": "pattern_improvement",
                    "title": f"改进 {pattern.pattern_type} 决策模式",
                    "description": f"该模式出现 {pattern.frequency} 次,成功率 {pattern.success_rate:.1%}",
                    "recommendation": await self._generate_pattern_recommendation(pattern),
                    "priority": "high" if pattern.improvement_potential > 0.5 else "medium",
                    "potential_impact": pattern.improvement_potential,
                }
                insights.append(insight)

        # 分析趋势
        trends = await self.analyze_trends()
        for trend_name, trend in trends.items():
            if trend.trend_direction == "declining" and trend.trend_strength > 0.3:
                insight = {
                    "type": "trend_warning",
                    "title": f"{trend_name} 呈下降趋势",
                    "description": f"当前值: {trend.current_value:.3f}, 趋势强度: {trend.trend_strength:.2f}",
                    "recommendation": await self._generate_trend_recommendation(trend),
                    "priority": "high" if trend.trend_strength > 0.5 else "medium",
                    "potential_impact": trend.trend_strength,
                }
                insights.append(insight)

        # 分析异常
        anomalies = await self._detect_anomalies()
        for anomaly in anomalies:
            insight = {
                "type": "anomaly_detection",
                "title": "检测到异常决策",
                "description": f"决策 {anomaly['decision_id']} 在 {anomaly['metric']} 上表现异常",
                "recommendation": "检查决策上下文和执行过程",
                "priority": "high",
                "potential_impact": 0.8,
            }
            insights.append(insight)

        self.insights = insights
        return insights

    async def _generate_pattern_recommendation(self, pattern: DecisionPattern) -> str:
        """生成模式改进建议"""
        if pattern.success_rate < 0.7:
            return f"建议审查 {pattern.pattern_type} 决策的逻辑,考虑添加额外的验证步骤"
        elif pattern.avg_execution_time > 5.0:
            return f"建议优化 {pattern.pattern_type} 决策的执行流程,减少处理时间"
        elif pattern.avg_confidence < 0.7:
            return f"建议提高 {pattern.pattern_type} 决策的信息收集质量,提升置信度"
        else:
            return f"继续监控 {pattern.pattern_type} 决策模式的表现"

    async def _generate_trend_recommendation(self, trend: TrendAnalysis) -> str:
        """生成趋势改进建议"""
        if trend.metric_name == "success_rate":
            return "成功率呈下降趋势,建议审查决策质量和执行过程"
        elif trend.metric_name == "execution_time":
            return "执行时间呈上升趋势,建议优化性能瓶颈"
        elif trend.metric_name == "confidence":
            return "置信度呈下降趋势,建议改进信息收集和分析方法"
        elif trend.metric_name == "frequency":
            return "决策频率呈上升趋势,建议检查是否存在决策过度"
        else:
            return "持续监控该指标的变化"

    async def _detect_anomalies(self) -> list[dict[str, Any]]:
        """检测异常决策"""
        if len(self.decision_history) < 10:
            return []

        anomalies = []

        # 计算各指标的统计值
        execution_times = [d.execution_time for d in self.decision_history]
        confidences = [d.confidence for d in self.decision_history]

        # 使用IQR方法检测异常
        def detect_outliers(values, multiplier=1.5) -> None:  # type: ignore
            q75, q25 = np.percentile(values, [75, 25])
            iqr = q75 - q25
            lower_bound = q25 - multiplier * iqr
            upper_bound = q75 + multiplier * iqr
            return lower_bound, upper_bound

        _exec_lower, exec_upper = detect_outliers(execution_times)
        conf_lower, _conf_upper = detect_outliers(confidences)

        # 检测执行时间异常
        for decision in self.decision_history:
            if decision.execution_time > exec_upper:
                anomalies.append(
                    {
                        "decision_id": decision.decision_id,
                        "metric": "execution_time",
                        "value": decision.execution_time,
                        "threshold": exec_upper,
                    }
                )

            if decision.confidence < conf_lower:
                anomalies.append(
                    {
                        "decision_id": decision.decision_id,
                        "metric": "confidence",
                        "value": decision.confidence,
                        "threshold": conf_lower,
                    }
                )

        return anomalies

    async def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = [
            key
            for key, value in self.cache.items()
            if current_time - value.get("timestamp", datetime.min) > timedelta(hours=24)
        ]
        for key in expired_keys:
            del self.cache[key]

    async def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.decision_history:
            return {}

        # 基本统计
        total_decisions = len(self.decision_history)
        success_decisions = sum(
            1 for d in self.decision_history if d.outcome == DecisionOutcome.SUCCESS
        )

        # 按类型统计
        type_stats = defaultdict(int)
        for decision in self.decision_history:
            type_stats[decision.decision_type.value] += 1

        # 时间统计
        recent_decisions = [
            d for d in self.decision_history if d.timestamp >= datetime.now() - timedelta(days=7)
        ]

        return {
            "total_decisions": total_decisions,
            "success_rate": success_decisions / total_decisions,
            "avg_execution_time": np.mean([d.execution_time for d in self.decision_history]),
            "avg_confidence": np.mean([d.confidence for d in self.decision_history]),
            "decisions_last_week": len(recent_decisions),
            "decision_types": dict(type_stats),
            "patterns_count": len(self.patterns),
            "last_analysis": self.last_analysis.isoformat() if self.last_analysis else None,
        }

    async def export_analysis(self, filepath: str):
        """导出分析结果"""
        analysis_data = {
            "timestamp": datetime.now().isoformat(),
            "statistics": await self.get_statistics(),
            "patterns": [asdict(p) for p in (await self.analyze_patterns())],
            "trends": {k: asdict(v) for k, v in (await self.analyze_trends()).items()},
            "insights": await self.generate_insights(),
            "recent_decisions": [asdict(d) for d in list(self.decision_history)[-100:]],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)


# 全局决策历史分析器实例
decision_history_analyzer = DecisionHistoryAnalyzer()


# 便捷函数
async def record_decision(
    decision_id: str,
    decision_type: str,
    context: dict[str, Any],    decision_data: dict[str, Any],    outcome: str,
    execution_time: float,
    confidence: float,
):
    """记录决策"""
    record = DecisionRecord(
        decision_id=decision_id,
        decision_type=DecisionType(decision_type),
        context=context,
        decision_data=decision_data,
        outcome=DecisionOutcome(outcome),
        execution_time=execution_time,
        confidence=confidence,
    )
    await decision_history_analyzer.record_decision(record)


async def get_decision_insights() -> list[dict[str, Any]]:
    """获取决策洞察"""
    return await decision_history_analyzer.generate_insights()


async def get_decision_patterns() -> list[DecisionPattern]:
    """获取决策模式"""
    return await decision_history_analyzer.analyze_patterns()


async def get_decision_trends() -> dict[str, TrendAnalysis]:
    """获取决策趋势"""
    return await decision_history_analyzer.analyze_trends()
