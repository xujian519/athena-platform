#!/usr/bin/env python3

"""
方案对比选择器
Plan Selector

功能:
1. 对比多个执行方案
2. 基于多维度评估选择最优方案
3. 提供方案推荐理由
4. 支持用户偏好配置

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from .cost_evaluator import CostComparison
from .multi_plan_generator import PlanStrategy, PlanVariant
from .risk_predictor import RiskAssessment, RiskLevel
from .xiaonuo_planner_engine import ExecutionPlan, PlanConfidence

logger = logging.getLogger(__name__)


class SelectionCriteria(Enum):
    """选择标准"""
    FASTEST = "fastest"  # 最快执行
    MOST_RELIABLE = "most_reliable"  # 最可靠
    LOWEST_COST = "lowest_cost"  # 最低成本
    BALANCED = "balanced"  # 平衡方案


@dataclass
class SelectionResult:
    """选择结果"""
    selected_plan: ExecutionPlan
    strategy: PlanStrategy
    reason: str
    comparison: list[dict[str, Any]  # 方案对比信息
    confidence: float  # 选择置信度


class PlanSelector:
    """
    方案选择器

    核心功能:
    1. 多维度方案对比
    2. 基于用户偏好选择
    3. 智能推荐引擎
    """

    # 评估权重配置
    CONFIDENCE_WEIGHT = 0.3
    COST_WEIGHT = 0.3
    RISK_WEIGHT = 0.2
    TIME_WEIGHT = 0.2

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.selection_history: list[SelectionResult] = []

    async def select(
        self,
        variants: list[PlanVariant],
        cost_comparisons: list[CostComparison],
        risk_assessments: list[RiskAssessment],
        criteria: Optional[SelectionCriteria] = None,
        user_preferences: Optional[dict[str, Any]] = None
    ) -> SelectionResult:
        """
        选择最优方案

        Args:
            variants: 方案变体列表
            cost_comparisons: 成本对比结果
            risk_assessments: 风险评估结果
            criteria: 选择标准（默认为BALANCED）
            user_preferences: 用户偏好配置

        Returns:
            SelectionResult: 选择结果
        """
        self.logger.info(f"🎯 选择最优方案: {len(variants)} 个方案候选")

        if not variants:
            raise ValueError("没有可用的方案")

        # 1. 确定选择标准
        if criteria is None:
            criteria = self._infer_criteria_from_preferences(user_preferences)

        # 2. 评估每个方案
        scores = []
        for variant in variants:
            # 查找对应的成本和风险评估
            cost_comp = next(
                (c for c in cost_comparisons if c.plan_id == variant.plan.plan_id),
                None
            )
            risk_assess = next(
                (r for r in risk_assessments if r.plan_id == variant.plan.plan_id),
                None
            )

            # 计算综合得分
            score = self._calculate_comprehensive_score(
                variant, cost_comp, risk_assess, criteria
            )

            scores.append({
                "variant": variant,
                "score": score,
                "cost": cost_comp,
                "risk": risk_assess,
            })

        # 3. 选择最高分方案
        best = max(scores, key=lambda x: x["score"])
        selected_variant = best["variant"]

        # 4. 生成选择理由
        reason = self._generate_selection_reason(
            selected_variant,
            best["cost"],
            best["risk"],
            criteria
        )

        # 5. 生成对比信息
        comparison = self._generate_comparison_info(scores)

        # 6. 创建选择结果
        result = SelectionResult(
            selected_plan=selected_variant.plan,
            strategy=selected_variant.strategy,
            reason=reason,
            comparison=comparison,
            confidence=selected_variant.plan.confidence == PlanConfidence.HIGH,
        )

        # 7. 记录历史
        self.selection_history.append(result)

        self.logger.info(f"   ✅ 方案选择完成: {selected_variant.strategy.value} (得分: {best['score']:.2f})")

        return result

    def _infer_criteria_from_preferences(
        self,
        preferences: Optional[dict[str, Any]]
    ) -> SelectionCriteria:
        """从用户偏好推断选择标准"""
        if not preferences:
            return SelectionCriteria.BALANCED

        priority = preferences.get("priority", "").lower()

        if "fast" in priority or "speed" in priority or "quick" in priority:
            return SelectionCriteria.FASTEST
        elif "reliable" in priority or "safe" in priority or "stable" in priority:
            return SelectionCriteria.MOST_RELIABLE
        elif "cost" in priority or "cheap" in priority or "economic" in priority:
            return SelectionCriteria.LOWEST_COST
        else:
            return SelectionCriteria.BALANCED

    def _calculate_comprehensive_score(
        self,
        variant: PlanVariant,
        cost_comparison: Optional[CostComparison],
        risk_assessment: Optional[RiskAssessment],
        criteria: SelectionCriteria
    ) -> float:
        """计算综合得分"""
        score = 0.0

        # 1. 基础分（方案置信度）
        confidence_score = (
            1.0 if variant.plan.confidence == PlanConfidence.HIGH else
            0.7 if variant.plan.confidence == PlanConfidence.MEDIUM else 0.4
        )
        score += confidence_score * self.CONFIDENCE_WEIGHT

        # 2. 成本分（根据标准调整）
        if cost_comparison:
            cost_score = self._normalize_cost_score(cost_comparison, criteria)
            score += cost_score * self.COST_WEIGHT

        # 3. 风险分（根据标准调整）
        if risk_assessment:
            risk_score = self._normalize_risk_score(risk_assessment, criteria)
            score += risk_score * self.RISK_WEIGHT

        # 4. 时间分（根据标准调整）
        time_score = self._normalize_time_score(variant.plan, criteria)
        score += time_score * self.TIME_WEIGHT

        # 5. 策略适配加分
        strategy_bonus = self._get_strategy_bonus(variant.strategy, criteria)
        score += strategy_bonus * 0.1

        return min(1.0, score)

    def _normalize_cost_score(
        self,
        comparison: CostComparison,
        criteria: SelectionCriteria
    ) -> float:
        """标准化成本得分"""
        if not comparison:
            return 0.5

        # 成本越低越好
        # 使用排名来标准化（假设最多10个方案）
        rank_score = 1.0 - (comparison.rank - 1) / 10.0

        # 根据选择标准调整
        if criteria == SelectionCriteria.LOWEST_COST:
            return rank_score  # 成本优先：直接使用排名
        elif criteria == SelectionCriteria.FASTEST:
            return 0.5  # 速度优先：成本权重降低
        elif criteria == SelectionCriteria.MOST_RELIABLE:
            return 0.6  # 可靠优先：稍微考虑成本
        else:
            return rank_score * 0.8  # 平衡：降低成本权重

    def _normalize_risk_score(
        self,
        assessment: RiskAssessment,
        criteria: SelectionCriteria
    ) -> float:
        """标准化风险得分"""
        if not assessment:
            return 0.5

        # 风险越低越好
        risk_score_map = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 0.7,
            RiskLevel.HIGH: 0.4,
            RiskLevel.CRITICAL: 0.1,
        }

        base_score = risk_score_map.get(assessment.overall_risk, 0.5)

        # 根据选择标准调整
        if criteria == SelectionCriteria.MOST_RELIABLE:
            return base_score  # 可靠优先：直接使用风险得分
        elif criteria == SelectionCriteria.FASTEST:
            return 0.7  # 速度优先：降低风险权重
        elif criteria == SelectionCriteria.LOWEST_COST:
            return 0.6  # 成本优先：稍微考虑风险
        else:
            return base_score * 0.9

    def _normalize_time_score(
        self,
        plan: ExecutionPlan,
        criteria: SelectionCriteria
    ) -> float:
        """标准化时间得分"""
        if not plan:
            return 0.5

        # 时间越短越好
        time_score = max(0, 1 - plan.estimated_time / 1800)  # 30分钟内

        # 根据选择标准调整
        if criteria == SelectionCriteria.FASTEST:
            return time_score  # 速度优先：直接使用时间得分
        elif criteria == SelectionCriteria.MOST_RELIABLE:
            return 0.7  # 可靠优先：降低时间权重
        elif criteria == SelectionCriteria.LOWEST_COST:
            return 0.6  # 成本优先：降低时间权重
        else:
            return time_score * 0.8

    def _get_strategy_bonus(
        self,
        strategy: PlanStrategy,
        criteria: SelectionCriteria
    ) -> float:
        """获取策略适配加分"""
        # 策略与标准的匹配度
        matching = {
            (PlanStrategy.FAST, SelectionCriteria.FASTEST): 0.3,
            (PlanStrategy.RELIABLE, SelectionCriteria.MOST_RELIABLE): 0.3,
            (PlanStrategy.ECONOMICAL, SelectionCriteria.LOWEST_COST): 0.3,
            (PlanStrategy.BALANCED, SelectionCriteria.BALANCED): 0.3,
        }

        return matching.get((strategy, criteria), 0.0)

    def _generate_selection_reason(
        self,
        variant: PlanVariant,
        cost_comparison: Optional[CostComparison],
        risk_assessment: Optional[RiskAssessment],
        criteria: SelectionCriteria
    ) -> str:
        """生成选择理由"""
        reasons = []

        # 策略优势
        reasons.append(f"采用{variant.strategy.value}策略")

        # 优势列表
        if variant.advantages:
            advantages = "、".join(variant.advantages[:3])  # 最多显示3个
            reasons.append(f"优势: {advantages}")

        # 成本优势
        if cost_comparison and cost_comparison.rank == 1:
            reasons.append("成本最低")

        # 风险优势
        if risk_assessment and risk_assessment.overall_risk == RiskLevel.LOW:
            reasons.append("风险最低")

        # 置信度优势
        if variant.plan.confidence == PlanConfidence.HIGH:
            reasons.append("置信度高")

        # 添加标准相关理由
        if criteria == SelectionCriteria.FASTEST:
            reasons.append("执行速度快")
        elif criteria == SelectionCriteria.MOST_RELIABLE:
            reasons.append("成功率高")
        elif criteria == SelectionCriteria.LOWEST_COST:
            reasons.append("资源消耗少")

        return "；".join(reasons)

    def _generate_comparison_info(
        self,
        scores: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成对比信息"""
        comparison = []

        for item in scores:
            variant = item["variant"]
            cost = item["cost"]
            risk = item["risk"]

            comparison.append({
                "strategy": variant.strategy.value,
                "score": item["score"],
                "confidence": variant.plan.confidence.value,
                "estimated_time": variant.plan.estimated_time,
                "steps_count": len(variant.plan.steps),
                "cost_rank": cost.rank if cost else None,
                "risk_level": risk.overall_risk.value if risk else None,
            })

        return comparison

    def get_selection_stats(self) -> dict[str, Any]:
        """获取选择统计"""
        if not self.selection_history:
            return {"total_selections": 0}

        strategy_distribution = {}
        for result in self.selection_history:
            strategy = result.strategy.value
            strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1

        return {
            "total_selections": len(self.selection_history),
            "strategy_distribution": strategy_distribution,
            "confidence_selection_rate": sum(
                1 for r in self.selection_history if r.confidence
            ) / len(self.selection_history),
        }

