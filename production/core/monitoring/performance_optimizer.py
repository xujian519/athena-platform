#!/usr/bin/env python3
"""
性能监控和参数调优系统
Performance Monitoring and Parameter Optimization System

持续监控模块性能，基于实际使用数据调优参数

作者: Athena平台团队
创建时间: 2025-12-31
版本: 1.0.0
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表盘
    HISTOGRAM = "histogram"  # 直方图
    SUMMARY = "summary"  # 摘要


class OptimizationAction(Enum):
    """优化动作"""
    INCREASE_THRESHOLD = "increase_threshold"
    DECREASE_THRESHOLD = "decrease_threshold"
    ADJUST_WEIGHT = "adjust_weight"
    EXPAND_KNOWLEDGE = "expand_knowledge"
    TUNE_PARAMETER = "tune_parameter"


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    module: str
    action: OptimizationAction
    parameter: str
    current_value: float
    suggested_value: float
    reason: str
    expected_improvement: str
    confidence: float


class PerformanceOptimizer:
    """
    性能监控和参数调优系统

    功能:
    1. 实时性能监控
    2. 指标收集和分析
    3. 异常检测
    4. 参数自动调优
    5. 优化建议生成
    """

    def __init__(self, storage_path: str | None = None):
        self.metrics_history: list[PerformanceMetric] = []
        self.baseline_metrics: dict[str, float] = {}
        self.thresholds: dict[str, dict[str, float]] = {}
        self.optimization_history: list[OptimizationSuggestion] = []
        self.storage_path = storage_path or "production/data/performance_metrics.json"

        # 模块参数配置
        self.module_parameters: dict[str, dict[str, Any]] = {
            "emotion_creative": {
                "creativity_threshold": 0.70,
                "practicality_weight": 0.50,
                "confidence_threshold": 0.75,
                "max_ideas_per_query": 5,
            },
            "semantic_fusion": {
                "similarity_threshold": 0.60,
                "novelty_threshold": 0.50,
                "fusion_depth_level": 3,
                "max_concept_mappings": 10,
            },
            "family_cocreation": {
                "decision_confidence_threshold": 0.80,
                "collaboration_weight_father": 0.40,
                "collaboration_weight_athena": 0.35,
                "collaboration_weight_xiaonuo": 0.25,
                "max_session_duration": 3600,
            },
        }

        # 性能基线
        self.performance_baselines = {
            "emotion_creative": {
                "average_practicality": 0.70,
                "average_confidence": 0.75,
                "response_time": 2.0,
                "success_rate": 0.90,
            },
            "semantic_fusion": {
                "average_novelty": 0.55,
                "average_utility": 0.75,
                "response_time": 3.0,
                "success_rate": 0.85,
            },
            "family_cocreation": {
                "average_quality": 0.85,
                "average_satisfaction": 0.85,
                "average_collaboration_efficiency": 0.80,
                "response_time": 5.0,
                "success_rate": 0.95,
            },
        }

    async def initialize(self):
        """初始化优化器"""
        logger.info("📊 初始化性能监控和参数调优系统...")

        # 加载历史数据
        await self._load_historical_data()

        # 设置阈值
        await self._set_thresholds()

        logger.info("✅ 性能监控和参数调优系统初始化完成")

    async def _load_historical_data(self):
        """加载历史数据"""
        try:
            path = Path(self.storage_path)
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    # 加载历史指标
                    for metric_data in data.get("metrics", []):
                        metric = PerformanceMetric(
                            name=metric_data["name"],
                            type=MetricType(metric_data["type"]),
                            value=metric_data["value"],
                            timestamp=datetime.fromisoformat(metric_data["timestamp"]),
                            labels=metric_data.get("labels", {}),
                            metadata=metric_data.get("metadata", {}),
                        )
                        self.metrics_history.append(metric)

                    # 加载基线
                    self.baseline_metrics = data.get("baselines", {})

                logger.info(f"📂 已加载 {len(self.metrics_history)} 条历史指标")
        except Exception as e:
            logger.warning(f"⚠️ 加载历史数据失败: {e}")

    async def _set_thresholds(self):
        """设置监控阈值"""
        self.thresholds = {
            "emotion_creative": {
                "practicality_min": 0.65,
                "confidence_min": 0.70,
                "response_time_max": 5.0,
                "success_rate_min": 0.85,
            },
            "semantic_fusion": {
                "novelty_min": 0.45,
                "utility_min": 0.70,
                "response_time_max": 8.0,
                "success_rate_min": 0.80,
            },
            "family_cocreation": {
                "quality_min": 0.80,
                "satisfaction_min": 0.80,
                "collaboration_efficiency_min": 0.75,
                "response_time_max": 15.0,
                "success_rate_min": 0.90,
            },
        }

    async def record_metric(
        self,
        module: str,
        metric_name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: dict[str, str] | None = None,
    ):
        """记录性能指标"""
        metric = PerformanceMetric(
            name=f"{module}.{metric_name}",
            type=metric_type,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metadata={"module": module},
        )

        self.metrics_history.append(metric)

        # 保持历史大小
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-5000:]

        # 检查是否需要优化
        await self._check_and_suggest_optimization(module, metric_name, value)

    async def _check_and_suggest_optimization(
        self, module: str, metric_name: str, value: float
    ):
        """检查并建议优化"""
        threshold_key = f"{module}.{metric_name}"

        # 获取阈值
        for mod, thresholds in self.thresholds.items():
            if mod == module:
                for key, threshold_value in thresholds.items():
                    if key in metric_name.lower():
                        # 检查是否违反阈值
                        if "min" in key and value < threshold_value:
                            await self._generate_optimization_suggestion(
                                module, metric_name, value, "below_threshold", threshold_value
                            )
                        elif "max" in key and value > threshold_value:
                            await self._generate_optimization_suggestion(
                                module, metric_name, value, "above_threshold", threshold_value
                            )

    async def _generate_optimization_suggestion(
        self,
        module: str,
        metric_name: str,
        current_value: float,
        issue_type: str,
        threshold_value: float,
    ):
        """生成优化建议"""
        # 根据问题类型生成建议
        if "practicality" in metric_name:
            if issue_type == "below_threshold":
                suggestion = OptimizationSuggestion(
                    module=module,
                    action=OptimizationAction.INCREASE_THRESHOLD,
                    parameter="creativity_filter",
                    current_value=current_value,
                    suggested_value=threshold_value + 0.05,
                    reason=f"实用性评分({current_value:.2f})低于阈值({threshold_value:.2f})",
                    expected_improvement="提高创意过滤标准，生成更实用的方案",
                    confidence=0.85,
                )
            else:
                suggestion = OptimizationSuggestion(
                    module=module,
                    action=OptimizationAction.TUNE_PARAMETER,
                    parameter="practicality_calculation",
                    current_value=current_value,
                    suggested_value=min(1.0, current_value * 1.05),
                    reason=f"实用性评分({current_value:.2f})表现优异",
                    expected_improvement="保持当前策略，微调计算参数",
                    confidence=0.75,
                )

        elif "confidence" in metric_name:
            if issue_type == "below_threshold":
                suggestion = OptimizationSuggestion(
                    module=module,
                    action=OptimizationAction.ADJUST_WEIGHT,
                    parameter="confidence_calculation_weights",
                    current_value=current_value,
                    suggested_value=threshold_value + 0.05,
                    reason=f"置信度({current_value:.2f})低于阈值({threshold_value:.2f})",
                    expected_improvement="调整置信度计算权重，提高可靠性",
                    confidence=0.80,
                )

        elif "response_time" in metric_name:
            if issue_type == "above_threshold":
                suggestion = OptimizationSuggestion(
                    module=module,
                    action=OptimizationAction.TUNE_PARAMETER,
                    parameter="max_processing_time",
                    current_value=current_value,
                    suggested_value=threshold_value * 0.8,
                    reason=f"响应时间({current_value:.2f}s)超过阈值({threshold_value:.2f}s)",
                    expected_improvement="优化处理流程，减少响应时间",
                    confidence=0.90,
                )

        else:
            # 通用建议
            suggestion = OptimizationSuggestion(
                module=module,
                action=OptimizationAction.TUNE_PARAMETER,
                parameter=metric_name,
                current_value=current_value,
                suggested_value=threshold_value,
                reason=f"指标{metric_name}({current_value:.2f})偏离正常范围",
                expected_improvement="调优参数以恢复性能",
                confidence=0.70,
            )

        self.optimization_history.append(suggestion)

        # 记录日志
        logger.warning(
            f"⚠️ 性能预警: {module}.{metric_name} = {current_value:.2f} "
            f"({issue_type} {threshold_value:.2f})"
        )
        logger.info(f"💡 优化建议: {suggestion.reason}")

    async def analyze_performance_trends(
        self, module: str, time_window_hours: int = 24
    ) -> dict[str, Any]:
        """分析性能趋势"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time and m.metadata.get("module") == module
        ]

        if not recent_metrics:
            return {"error": "没有足够的数据进行分析"}

        # 按指标名称分组
        metric_groups: dict[str, list[float]] = {}
        for metric in recent_metrics:
            key = metric.name.split(".")[-1]  # 获取指标名
            if key not in metric_groups:
                metric_groups[key] = []
            metric_groups[key].append(metric.value)

        # 计算统计信息
        analysis = {}
        for metric_name, values in metric_groups.items():
            if len(values) > 1:
                avg = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)

                # 计算趋势
                if len(values) >= 3:
                    first_half_avg = sum(values[: len(values) // 2]) / (len(values) // 2)
                    second_half_avg = sum(values[len(values) // 2 :]) / (
                        len(values) - len(values) // 2
                    )
                    trend = second_half_avg - first_half_avg
                    trend_direction = "↑" if trend > 0.01 else ("↓" if trend < -0.01 else "→")
                else:
                    trend = 0
                    trend_direction = "→"

                analysis[metric_name] = {
                    "average": avg,
                    "min": min_val,
                    "max": max_val,
                    "count": len(values),
                    "trend": trend,
                    "trend_direction": trend_direction,
                    "change_percent": (trend / avg * 100) if avg > 0 else 0,
                }

        return {
            "module": module,
            "time_window_hours": time_window_hours,
            "metrics_analyzed": len(analysis),
            "analysis": analysis,
            "overall_health": self._assess_overall_health(module, analysis),
        }

    def _assess_overall_health(
        self, module: str, analysis: dict[str, Any]
    ) -> str:
        """评估整体健康状况"""
        baseline = self.performance_baselines.get(module, {})

        if not baseline:
            return "unknown"

        # 计算健康得分
        health_scores = []
        for metric_name, stats in analysis.items():
            # 查找对应的基线
            for key, baseline_value in baseline.items():
                if key in metric_name.lower():
                    if stats["average"] >= baseline_value * 0.95:  # 95%基线
                        health_scores.append(1.0)
                    elif stats["average"] >= baseline_value * 0.85:  # 85%基线
                        health_scores.append(0.7)
                    else:
                        health_scores.append(0.4)
                    break

        if not health_scores:
            return "unknown"

        avg_health = sum(health_scores) / len(health_scores)

        if avg_health >= 0.85:
            return "excellent"
        elif avg_health >= 0.70:
            return "good"
        elif avg_health >= 0.55:
            return "fair"
        else:
            return "poor"

    async def auto_tune_parameters(self, module: str) -> dict[str, Any]:
        """自动调优参数"""
        logger.info(f"🔧 开始自动调优 {module} 模块...")

        # 分析性能趋势
        trends = await self.analyze_performance_trends(module, time_window_hours=48)

        if "error" in trends:
            return {"error": "无法分析性能趋势"}

        # 收集优化建议
        recent_suggestions = [
            s for s in self.optimization_history
            if s.module == module
            and (datetime.now() - s.timestamp).total_seconds() < 86400  # 最近24小时
        ]

        # 应用优化
        applied_optimizations = []

        for suggestion in recent_suggestions:
            if suggestion.confidence >= 0.80:
                # 应用高置信度的建议
                if module in self.module_parameters:
                    # 更新参数
                    if suggestion.action == OptimizationAction.INCREASE_THRESHOLD:
                        param = suggestion.parameter
                        if param in self.module_parameters[module]:
                            old_value = self.module_parameters[module][param]
                            self.module_parameters[module][param] = suggestion.suggested_value

                            applied_optimizations.append({
                                "parameter": param,
                                "old_value": old_value,
                                "new_value": suggestion.suggested_value,
                                "reason": suggestion.reason,
                            })

                            logger.info(
                                f"✅ 已应用优化: {module}.{param} "
                                f"{old_value:.2f} → {suggestion.suggested_value:.2f}"
                            )

        return {
            "module": module,
            "trend_analysis": trends,
            "optimizations_applied": applied_optimizations,
            "new_parameters": self.module_parameters.get(module, {}),
        }

    async def get_dashboard_data(self) -> dict[str, Any]:
        """获取监控仪表板数据"""
        dashboard = {
            "last_updated": datetime.now().isoformat(),
            "modules": {},
            "alerts": [],
        }

        for module in ["emotion_creative", "semantic_fusion", "family_cocreation"]:
            # 分析趋势
            trends = await self.analyze_performance_trends(module)

            # 获取最新指标
            recent_metrics = [
                m for m in self.metrics_history
                if m.metadata.get("module") == module
                and (datetime.now() - m.timestamp).total_seconds() < 3600  # 最近1小时
            ]

            dashboard["modules"][module] = {
                "health": trends.get("overall_health", "unknown"),
                "metrics_count": len(recent_metrics),
                "trend_analysis": trends.get("analysis", {}),
                "parameters": self.module_parameters.get(module, {}),
            }

            # 生成告警
            if trends.get("overall_health") in ["poor", "fair"]:
                dashboard["alerts"].append({
                    "module": module,
                    "severity": "high" if trends.get("overall_health") == "poor" else "medium",
                    "message": f"{module} 模块性能需要关注，建议执行参数调优",
                })

        return dashboard

    async def save_metrics(self):
        """保存指标数据"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "metrics": [
                    {
                        "name": m.name,
                        "type": m.type.value,
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "labels": m.labels,
                        "metadata": m.metadata,
                    }
                    for m in self.metrics_history[-1000:]  # 只保存最近1000条
                ],
                "baselines": self.baseline_metrics,
                "parameters": self.module_parameters,
            }

            path = Path(self.storage_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 已保存 {len(data['metrics'])} 条指标到 {self.storage_path}")

        except Exception as e:
            logger.error(f"❌ 保存指标失败: {e}")

    async def shutdown(self):
        """关闭优化器"""
        logger.info("🛑 关闭性能监控和参数调优系统...")
        await self.save_metrics()
        logger.info("✅ 性能监控和参数调优系统已关闭")


# 全局单例
_performance_optimizer: PerformanceOptimizer | None = None


async def get_performance_optimizer() -> PerformanceOptimizer:
    """获取性能优化器单例"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
        await _performance_optimizer.initialize()
    return _performance_optimizer
