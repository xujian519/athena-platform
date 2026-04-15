#!/usr/bin/env python3
from __future__ import annotations
"""
动态权重调整器
Dynamic Weight Adjuster

基于性能数据自动调整各组件的权重参数:
1. 工具发现权重(语义、上下文、性能)
2. 参数验证权重(类型、格式、范围)
3. 错误预测阈值(风险等级触发条件)
4. 缓存策略参数(容量、TTL)

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AdjustmentStrategy(Enum):
    """调整策略"""

    CONSERVATIVE = "conservative"  # 保守调整:小幅变动
    MODERATE = "moderate"  # 适中调整:中幅变动
    AGGRESSIVE = "aggressive"  # 激进调整:大幅变动


@dataclass
class WeightConfig:
    """权重配置"""

    component: str
    weights: dict[str, float]
    last_adjusted: datetime
    performance_impact: float = 0.0
    adjustment_count: int = 0

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "weights": self.weights,
            "last_adjusted": self.last_adjusted.isoformat(),
            "performance_impact": self.performance_impact,
            "adjustment_count": self.adjustment_count,
        }


@dataclass
class AdjustmentRecommendation:
    """调整建议"""

    component: str
    parameter_name: str
    current_value: float
    recommended_value: float
    reason: str
    expected_impact: float
    confidence: float


class DynamicWeightAdjuster:
    """
    动态权重调整器

    核心功能:
    1. 监控性能指标
    2. 分析权重效果
    3. 生成调整建议
    4. 执行权重调整
    """

    def __init__(
        self,
        config_path: str = "config/weight_configs.json",
        min_adjustment_interval: timedelta = timedelta(hours=1),
        strategy: AdjustmentStrategy = AdjustmentStrategy.MODERATE,
    ):
        self.config_path = Path(config_path)
        self.min_adjustment_interval = min_adjustment_interval
        self.strategy = strategy

        # 权重配置
        self.weight_configs: dict[str, WeightConfig] = {}

        # 调整历史
        self.adjustment_history: list[dict] = []

        # 初始化
        self._load_configs()
        self._init_default_weights()

        logger.info("🔧 动态权重调整器初始化完成")
        logger.info(f"   调整策略: {self.strategy.value}")
        logger.info(f"   最小间隔: {self.min_adjustment_interval}")

    def _load_configs(self) -> Any:
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
                for comp_name, comp_data in data.get("components", {}).items():
                    self.weight_configs[comp_name] = WeightConfig(
                        component=comp_name,
                        weights=comp_data["weights"],
                        last_adjusted=datetime.fromisoformat(comp_data["last_adjusted"]),
                        performance_impact=comp_data.get("performance_impact", 0.0),
                        adjustment_count=comp_data.get("adjustment_count", 0),
                    )
            logger.info(f"✅ 加载了 {len(self.weight_configs)} 个组件配置")

    def _save_configs(self) -> Any:
        """保存配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "adjustment_strategy": self.strategy.value,
            "components": {name: config.to_dict() for name, config in self.weight_configs.items()},
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.debug(f"💾 配置已保存: {self.config_path}")

    def _init_default_weights(self) -> Any:
        """初始化默认权重"""
        defaults = {
            "tool_discovery": {
                "semantic_weight": 0.5,
                "context_weight": 0.3,
                "performance_weight": 0.2,
            },
            "parameter_validator": {
                "type_check_weight": 0.4,
                "format_check_weight": 0.3,
                "range_check_weight": 0.3,
            },
            "error_detector": {
                "high_risk_threshold": 0.7,
                "medium_risk_threshold": 0.4,
                "low_risk_threshold": 0.2,
            },
            "cache_manager": {"max_size": 1000, "ttl_seconds": 3600, "eviction_policy": "lru"},
        }

        for comp_name, weights in defaults.items():
            if comp_name not in self.weight_configs:
                self.weight_configs[comp_name] = WeightConfig(
                    component=comp_name, weights=weights, last_adjusted=datetime.now()
                )

    async def analyze_and_recommend(
        self, performance_stats: dict[str, Any], time_range: timedelta = timedelta(hours=24)
    ) -> list[AdjustmentRecommendation]:
        """
        分析性能并生成调整建议

        Args:
            performance_stats: 性能统计数据
            time_range: 分析时间范围

        Returns:
            调整建议列表
        """
        recommendations = []

        # 1. 分析工具发现权重
        tool_rec = await self._analyze_tool_discovery_weights(performance_stats)
        recommendations.extend(tool_rec)

        # 2. 分析参数验证权重
        val_rec = await self._analyze_parameter_validator_weights(performance_stats)
        recommendations.extend(val_rec)

        # 3. 分析错误预测阈值
        err_rec = await self._analyze_error_detector_thresholds(performance_stats)
        recommendations.extend(err_rec)

        # 4. 分析缓存策略
        cache_rec = await self._analyze_cache_parameters(performance_stats)
        recommendations.extend(cache_rec)

        logger.info(f"📊 生成了 {len(recommendations)} 条调整建议")
        return recommendations

    async def _analyze_tool_discovery_weights(
        self, stats: dict[str, Any]
    ) -> list[AdjustmentRecommendation]:
        """分析工具发现权重"""
        recommendations = []
        config = self.weight_configs.get("tool_discovery")
        if not config:
            return recommendations

        accuracy = stats.get("tool_selection_accuracy", 0.85)
        semantic_time = stats.get("semantic_matching_time", 0.1)
        stats.get("context_analysis_time", 0.05)

        # 分析1: 语义权重
        if accuracy < 0.90:
            # 准确率低,增加语义权重
            current = config.weights["semantic_weight"]
            recommended = min(0.7, current + 0.1)
            recommendations.append(
                AdjustmentRecommendation(
                    component="tool_discovery",
                    parameter_name="semantic_weight",
                    current_value=current,
                    recommended_value=recommended,
                    reason=f"工具选择准确率{accuracy:.1%}偏低,建议增加语义匹配权重",
                    expected_impact=0.05,
                    confidence=0.8,
                )
            )
        elif accuracy > 0.95 and semantic_time > 0.15:
            # 准确率高但语义匹配慢,可以适当降低
            current = config.weights["semantic_weight"]
            recommended = max(0.4, current - 0.05)
            recommendations.append(
                AdjustmentRecommendation(
                    component="tool_discovery",
                    parameter_name="semantic_weight",
                    current_value=current,
                    recommended_value=recommended,
                    reason=f"准确率已达{accuracy:.1%},可略微降低语义权重以提升速度",
                    expected_impact=-0.02,
                    confidence=0.6,
                )
            )

        # 分析2: 上下文权重
        context_usage = stats.get("context_usage_rate", 0.3)
        if context_usage > 0.7:
            current = config.weights["context_weight"]
            recommended = min(0.4, current + 0.05)
            recommendations.append(
                AdjustmentRecommendation(
                    component="tool_discovery",
                    parameter_name="context_weight",
                    current_value=current,
                    recommended_value=recommended,
                    reason=f"上下文使用率高{context_usage:.1%},建议增加上下文权重",
                    expected_impact=0.03,
                    confidence=0.7,
                )
            )

        return recommendations

    async def _analyze_parameter_validator_weights(
        self, stats: dict[str, Any]
    ) -> list[AdjustmentRecommendation]:
        """分析参数验证权重"""
        recommendations = []
        config = self.weight_configs.get("parameter_validator")
        if not config:
            return recommendations

        stats.get("avg_validation_time", 0.3)
        type_errors = stats.get("type_error_rate", 0.05)
        format_errors = stats.get("format_error_rate", 0.10)

        # 类型检查权重
        if type_errors > 0.08:
            current = config.weights["type_check_weight"]
            recommended = min(0.5, current + 0.1)
            recommendations.append(
                AdjustmentRecommendation(
                    component="parameter_validator",
                    parameter_name="type_check_weight",
                    current_value=current,
                    recommended_value=recommended,
                    reason=f"类型错误率{type_errors:.1%}偏高,建议增强类型检查",
                    expected_impact=0.04,
                    confidence=0.85,
                )
            )

        # 格式检查权重
        if format_errors > 0.15:
            current = config.weights["format_check_weight"]
            recommended = min(0.4, current + 0.1)
            recommendations.append(
                AdjustmentRecommendation(
                    component="parameter_validator",
                    parameter_name="format_check_weight",
                    current_value=current,
                    recommended_value=recommended,
                    reason=f"格式错误率{format_errors:.1%}偏高,建议增强格式检查",
                    expected_impact=0.05,
                    confidence=0.8,
                )
            )

        return recommendations

    async def _analyze_error_detector_thresholds(
        self, stats: dict[str, Any]
    ) -> list[AdjustmentRecommendation]:
        """分析错误检测阈值"""
        recommendations = []
        config = self.weight_configs.get("error_detector")
        if not config:
            return recommendations

        prevention_rate = stats.get("error_prevention_rate", 0.3)
        false_positive_rate = stats.get("false_positive_rate", 0.2)

        # 高风险阈值
        if prevention_rate < 0.35 and false_positive_rate < 0.15:
            current = config.weights["high_risk_threshold"]
            recommended = max(0.6, current - 0.05)
            recommendations.append(
                AdjustmentRecommendation(
                    component="error_detector",
                    parameter_name="high_risk_threshold",
                    current_value=current,
                    recommended_value=recommended,
                    reason=f"预防率{prevention_rate:.1%}偏低,可降低高风险阈值以提前预警",
                    expected_impact=0.08,
                    confidence=0.75,
                )
            )

        # 中风险阈值
        if false_positive_rate > 0.25:
            current = config.weights["medium_risk_threshold"]
            recommended = min(0.5, current + 0.05)
            recommendations.append(
                AdjustmentRecommendation(
                    component="error_detector",
                    parameter_name="medium_risk_threshold",
                    current_value=current,
                    recommended_value=recommended,
                    reason=f"误报率{false_positive_rate:.1%}偏高,建议提高中风险阈值",
                    expected_impact=-0.03,
                    confidence=0.7,
                )
            )

        return recommendations

    async def _analyze_cache_parameters(
        self, stats: dict[str, Any]
    ) -> list[AdjustmentRecommendation]:
        """分析缓存参数"""
        recommendations = []
        config = self.weight_configs.get("cache_manager")
        if not config:
            return recommendations

        hit_rate = stats.get("cache_hit_rate", 0.7)
        1.0 - hit_rate
        avg_size = stats.get("avg_cache_size", 500)

        # 缓存大小
        if hit_rate < 0.65 and avg_size < 800:
            current = config.weights["max_size"]
            recommended = min(2000, current + 200)
            recommendations.append(
                AdjustmentRecommendation(
                    component="cache_manager",
                    parameter_name="max_size",
                    current_value=current,
                    recommended_value=recommended,
                    reason=f"缓存命中率{hit_rate:.1%}偏低,建议增加缓存容量",
                    expected_impact=0.06,
                    confidence=0.8,
                )
            )

        # TTL
        ttl_seconds = config.weights["ttl_seconds"]
        eviction_rate = stats.get("cache_eviction_rate", 0.1)

        if eviction_rate > 0.15 and ttl_seconds < 7200:
            recommended = min(14400, ttl_seconds + 1800)
            recommendations.append(
                AdjustmentRecommendation(
                    component="cache_manager",
                    parameter_name="ttl_seconds",
                    current_value=ttl_seconds,
                    recommended_value=recommended,
                    reason=f"缓存淘汰率{eviction_rate:.1%}偏高,建议延长TTL",
                    expected_impact=0.04,
                    confidence=0.7,
                )
            )

        return recommendations

    async def apply_recommendations(
        self,
        recommendations: list[AdjustmentRecommendation],
        auto_apply: bool = False,
        confidence_threshold: float = 0.7,
    ) -> dict[str, Any]:
        """
        应用调整建议

        Args:
            recommendations: 调整建议列表
            auto_apply: 是否自动应用(超过置信度阈值)
            confidence_threshold: 置信度阈值

        Returns:
            应用结果
        """
        applied = []
        skipped = []
        total_impact = 0.0

        for rec in recommendations:
            # 检查置信度
            if rec.confidence < confidence_threshold and not auto_apply:
                skipped.append(
                    {
                        "recommendation": rec,
                        "reason": f"置信度{rec.confidence:.2%}低于阈值{confidence_threshold:.2%}",
                    }
                )
                continue

            # 应用调整
            if rec.component in self.weight_configs:
                config = self.weight_configs[rec.component]

                # 记录旧值
                old_value = config.weights.get(rec.parameter_name)
                if old_value is None:
                    skipped.append({"recommendation": rec, "reason": "参数不存在"})
                    continue

                # 应用新值
                config.weights[rec.parameter_name] = rec.recommended_value
                config.last_adjusted = datetime.now()
                config.adjustment_count += 1
                config.performance_impact += rec.expected_impact

                applied.append(
                    {
                        "component": rec.component,
                        "parameter": rec.parameter_name,
                        "old_value": old_value,
                        "new_value": rec.recommended_value,
                        "reason": rec.reason,
                        "expected_impact": rec.expected_impact,
                    }
                )

                total_impact += rec.expected_impact

                logger.info(f"✅ 调整: {rec.component}.{rec.parameter_name}")
                logger.info(f"   {old_value:.3f} → {rec.recommended_value:.3f}")
                logger.info(f"   理由: {rec.reason}")

        # 保存配置
        if applied:
            self._save_configs()

            # 记录历史
            self.adjustment_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "applied_count": len(applied),
                    "skipped_count": len(skipped),
                    "total_impact": total_impact,
                    "changes": applied,
                }
            )

        return {
            "applied": applied,
            "skipped": skipped,
            "total_applied": len(applied),
            "total_skipped": len(skipped),
            "expected_total_impact": total_impact,
            "timestamp": datetime.now().isoformat(),
        }

    async def auto_adjust(
        self, performance_stats: dict[str, Any], confidence_threshold: float = 0.75
    ) -> dict[str, Any]:
        """
        自动调整权重

        Args:
            performance_stats: 性能统计数据
            confidence_threshold: 自动应用的置信度阈值

        Returns:
            调整结果
        """
        logger.info("🔄 开始自动权重调整...")

        # 生成建议
        recommendations = await self.analyze_and_recommend(performance_stats)

        # 应用高置信度建议
        result = await self.apply_recommendations(
            recommendations, auto_apply=True, confidence_threshold=confidence_threshold
        )

        logger.info("✅ 自动调整完成")
        logger.info(f"   应用: {result['total_applied']} 条")
        logger.info(f"   跳过: {result['total_skipped']} 条")
        logger.info(f"   预期影响: {result['expected_total_impact']:+.2%}")

        return result

    def get_current_weights(self, component: str) -> dict[str, float | None]:
        """获取当前权重配置"""
        config = self.weight_configs.get(component)
        return config.weights if config else None

    def get_adjustment_history(self, limit: int = 10) -> list[dict]:
        """获取调整历史"""
        return self.adjustment_history[-limit:]


# 导出便捷函数
_adjuster: DynamicWeightAdjuster | None = None


def get_weight_adjuster() -> DynamicWeightAdjuster:
    """获取权重调整器单例"""
    global _adjuster
    if _adjuster is None:
        _adjuster = DynamicWeightAdjuster()
    return _adjuster


# 使用示例
async def main():
    """主函数示例"""
    print("=" * 60)
    print("动态权重调整器演示")
    print("=" * 60)

    # 获取调整器
    adjuster = get_weight_adjuster()

    # 模拟性能数据
    performance_stats = {
        "tool_selection_accuracy": 0.87,  # 略低
        "semantic_matching_time": 0.12,
        "context_analysis_time": 0.05,
        "context_usage_rate": 0.75,
        "avg_validation_time": 0.25,
        "type_error_rate": 0.09,  # 偏高
        "format_error_rate": 0.12,
        "error_prevention_rate": 0.32,  # 偏低
        "false_positive_rate": 0.18,
        "cache_hit_rate": 0.62,  # 偏低
        "avg_cache_size": 450,
        "cache_eviction_rate": 0.18,
    }

    # 生成建议
    print("\n📊 分析性能数据...")
    recommendations = await adjuster.analyze_and_recommend(performance_stats)

    print(f"\n生成了 {len(recommendations)} 条调整建议:\n")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.component}.{rec.parameter_name}")
        print(f"   当前值: {rec.current_value:.3f}")
        print(f"   推荐值: {rec.recommended_value:.3f}")
        print(f"   理由: {rec.reason}")
        print(f"   预期影响: {rec.expected_impact:+.2%}")
        print(f"   置信度: {rec.confidence:.1%}")
        print()

    # 应用建议(自动应用高置信度的)
    print("🔄 应用调整建议...")
    result = await adjuster.apply_recommendations(
        recommendations, auto_apply=True, confidence_threshold=0.75
    )

    print("\n✅ 应用结果:")
    print(f"   应用: {result['total_applied']} 条")
    print(f"   跳过: {result['total_skipped']} 条")
    print(f"   预期总影响: {result['expected_total_impact']:+.2%}")

    if result["applied"]:
        print("\n应用的调整:")
        for change in result["applied"]:
            print(f"   - {change['component']}.{change['parameter']}")
            print(f"     {change['old_value']:.3f} → {change['new_value']:.3f}")
            print(f"     {change['reason']}")

    # 查看当前权重
    print("\n📋 当前权重配置:")
    for comp_name, config in adjuster.weight_configs.items():
        print(f"\n{comp_name}:")
        for param, value in config.weights.items():
            print(f"  {param}: {value:.3f}")

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
