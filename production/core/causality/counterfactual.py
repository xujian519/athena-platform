#!/usr/bin/env python3
"""
反事实解释器 (Counterfactual Explainer)
生成"如果...会怎样"的解释

作者: 小诺·双鱼公主
版本: v1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ExplanationType(str, Enum):
    """解释类型"""

    WHY = "why"  # 为什么会发生
    WHY_NOT = "why_not"  # 为什么没有发生
    WHAT_IF = "what_if"  # 如果...会怎样
    HOW_TO = "how_to"  # 如何实现


@dataclass
class CounterfactualExplanation:
    """反事实解释"""

    explanation_id: str
    original_outcome: Any
    counterfactual_outcome: Any
    changed_factors: list[dict[str, Any]]
    explanation_text: str
    confidence: float = 0.0
    validity: str = "unknown"  # valid, invalid, unknown


@dataclass
class Intervention:
    """干预动作"""

    variable: str
    original_value: Any
    counterfactual_value: Any
    effect_size: float = 0.0
    feasibility: str = "medium"  # high, medium, low


class CounterfactualExplainer:
    """
    反事实解释器

    功能:
    1. 生成反事实解释
    2. 分析"如果...会怎样"场景
    3. 提供可操作的建议
    """

    def __init__(self):
        self.name = "反事实解释器"
        self.version = "1.0.0"
        self.explanations_generated = 0

        logger.info(f"✅ {self.name} 初始化完成")

    async def explain_why(
        self, outcome: Any, context: dict[str, Any], causal_graph: Any | None = None
    ) -> CounterfactualExplanation:
        """
        解释为什么发生某个结果

        Args:
            outcome: 实际结果
            context: 上下文信息
            causal_graph: 因果图(可选)

        Returns:
            反事实解释
        """
        explanation_id = f"why_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 识别关键因素
        key_factors = self._identify_key_factors(outcome, context)

        # 生成解释文本
        explanation_text = self._generate_why_text(outcome, key_factors)

        self.explanations_generated += 1

        return CounterfactualExplanation(
            explanation_id=explanation_id,
            original_outcome=outcome,
            counterfactual_outcome=None,
            changed_factors=key_factors,
            explanation_text=explanation_text,
            confidence=0.75,
            validity="unknown",
        )

    async def explain_why_not(
        self,
        desired_outcome: Any,
        actual_outcome: Any,
        context: dict[str, Any],        causal_graph: Any | None = None,
    ) -> CounterfactualExplanation:
        """
        解释为什么没有发生某个结果

        Args:
            desired_outcome: 期望结果
            actual_outcome: 实际结果
            context: 上下文信息
            causal_graph: 因果图(可选)

        Returns:
            反事实解释
        """
        explanation_id = f"why_not_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 分析差异
        gaps = self._analyze_outcome_gaps(desired_outcome, actual_outcome, context)

        # 生成解释
        explanation_text = self._generate_why_not_text(desired_outcome, gaps)

        # 建议干预
        interventions = self._suggest_interventions(gaps)

        self.explanations_generated += 1

        return CounterfactualExplanation(
            explanation_id=explanation_id,
            original_outcome=actual_outcome,
            counterfactual_outcome=desired_outcome,
            changed_factors=interventions,
            explanation_text=explanation_text,
            confidence=0.70,
            validity="unknown",
        )

    async def what_if(
        self,
        scenario: dict[str, Any],        interventions: list[Intervention],
        causal_graph: Any | None = None,
    ) -> CounterfactualExplanation:
        """
        分析"如果...会怎样"场景

        Args:
            scenario: 当前场景
            interventions: 干预列表
            causal_graph: 因果图(可选)

        Returns:
            反事实解释
        """
        explanation_id = f"what_if_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 应用干预
        counterfactual_scenario = self._apply_interventions(scenario, interventions)

        # 预测结果
        predicted_outcome = self._predict_counterfactual_outcome(
            scenario, counterfactual_scenario, interventions
        )

        # 生成解释
        explanation_text = self._generate_what_if_text(interventions, predicted_outcome)

        self.explanations_generated += 1

        return CounterfactualExplanation(
            explanation_id=explanation_id,
            original_outcome=scenario,
            counterfactual_outcome=predicted_outcome,
            changed_factors=[
                {
                    "variable": i.variable,
                    "from": i.original_value,
                    "to": i.counterfactual_value,
                    "effect": i.effect_size,
                }
                for i in interventions
            ],
            explanation_text=explanation_text,
            confidence=0.65,
            validity="unknown",
        )

    async def how_to_achieve(
        self,
        target_outcome: Any,
        current_context: dict[str, Any],        causal_graph: Any | None = None,
    ) -> CounterfactualExplanation:
        """
        解释如何实现某个目标

        Args:
            target_outcome: 目标结果
            current_context: 当前上下文
            causal_graph: 因果图(可选)

        Returns:
            反事实解释(包含行动计划)
        """
        explanation_id = f"how_to_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 识别需要的改变
        required_changes = self._identify_required_changes(target_outcome, current_context)

        # 生成行动计划
        action_plan = self._generate_action_plan(required_changes)

        # 生成解释
        explanation_text = self._generate_how_to_text(target_outcome, action_plan)

        self.explanations_generated += 1

        return CounterfactualExplanation(
            explanation_id=explanation_id,
            original_outcome=current_context,
            counterfactual_outcome=target_outcome,
            changed_factors=action_plan,
            explanation_text=explanation_text,
            confidence=0.70,
            validity="unknown",
        )

    def _identify_key_factors(self, outcome: Any, context: dict[str, Any]) -> list[dict[str, Any]]:
        """识别关键因素"""
        # 简化版实现
        factors = []

        for key, value in context.items():
            if isinstance(value, (int, float)):
                factors.append(
                    {
                        "factor": key,
                        "value": value,
                        "impact": "high" if abs(value) > 0.5 else "medium",
                    }
                )

        # 按影响排序
        factors.sort(key=lambda x: x["value"], reverse=True)
        return factors[:5]

    def _generate_why_text(self, outcome: Any, factors: list[dict[str, Any]]) -> str:
        """生成"为什么"解释文本"""
        if not factors:
            return f"由于当前条件,发生了 {outcome}"

        top_factors = factors[:3]
        factor_descriptions = [f"{f['factor']} (值: {f['value']})" for f in top_factors]

        return (
            f"发生 {outcome} 的主要原因可能是:\n"
            f"1. {factor_descriptions[0] if len(factor_descriptions) > 0 else ''}\n"
            f"2. {factor_descriptions[1] if len(factor_descriptions) > 1 else ''}\n"
            f"3. {factor_descriptions[2] if len(factor_descriptions) > 2 else ''}"
        )

    def _analyze_outcome_gaps(
        self, desired: Any, actual: Any, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """分析结果差距"""
        gaps = []

        # 简化版实现
        if isinstance(desired, (int, float)) and isinstance(actual, (int, float)):
            gap = desired - actual
            gaps.append(
                {
                    "type": "value_gap",
                    "desired": desired,
                    "actual": actual,
                    "gap": gap,
                    "priority": "high" if abs(gap) > 0.5 else "medium",
                }
            )

        return gaps

    def _generate_why_not_text(self, desired: Any, gaps: list[dict[str, Any]]) -> str:
        """生成"为什么不"解释文本"""
        if not gaps:
            return f"无法实现 {desired} 的具体原因不明确"

        return f"没有实现 {desired} 可能是因为:\n" + "\n".join(
            [f"- {gap['type']}: 差距为 {gap.get('gap', 'N/A')}" for gap in gaps]
        )

    def _suggest_interventions(self, gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """建议干预措施"""
        interventions = []

        for gap in gaps:
            if gap["type"] == "value_gap":
                interventions.append(
                    {
                        "variable": "context_variable",
                        "action": "increase",
                        "magnitude": abs(gap.get("gap", 0)),
                        "feasibility": "medium",
                    }
                )

        return interventions

    def _apply_interventions(
        self, scenario: dict[str, Any], interventions: list[Intervention]
    ) -> dict[str, Any]:
        """应用干预措施"""
        counterfactual = scenario.copy()

        for intervention in interventions:
            counterfactual[intervention.variable] = intervention.counterfactual_value

        return counterfactual

    def _predict_counterfactual_outcome(
        self,
        original: dict[str, Any],        counterfactual: dict[str, Any],        interventions: list[Intervention],
    ) -> dict[str, Any]:
        """预测反事实结果"""
        # 简化版实现:线性模型
        outcome_change = sum(i.effect_size for i in interventions)

        return {
            "predicted_change": outcome_change,
            "confidence": "medium",
            "affected_variables": [i.variable for i in interventions],
        }

    def _generate_what_if_text(
        self, interventions: list[Intervention], outcome: dict[str, Any]
    ) -> str:
        """生成"如果...会怎样"解释文本"""
        changes = [
            f"将 {i.variable} 从 {i.original_value} 改为 {i.counterfactual_value}"
            for i in interventions
        ]

        return (
            "如果进行以下干预:\n"
            + "\n".join([f"- {change}" for change in changes])
            + f"\n\n预测结果:变化量约为 {outcome.get('predicted_change', 'N/A')}"
        )

    def _identify_required_changes(
        self, target: Any, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """识别需要的改变"""
        # 简化版实现
        changes = []

        for key, value in context.items():
            if isinstance(value, (int, float)) and value < 0.5:
                changes.append(
                    {
                        "variable": key,
                        "current_value": value,
                        "target_value": value * 1.5,
                        "priority": "high",
                    }
                )

        return changes

    def _generate_action_plan(self, changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """生成行动计划"""
        plan = []

        for change in changes:
            plan.append(
                {
                    "action": "increase",
                    "target": change["variable"],
                    "from": change["current_value"],
                    "to": change["target_value"],
                    "priority": change["priority"],
                }
            )

        return plan

    def _generate_how_to_text(self, target: Any, plan: list[dict[str, Any]]) -> str:
        """生成"如何实现"解释文本"""
        steps = [
            f"{i + 1}. {step['action'].upper()} {step['target']} "
            f"从 {step['from']} 到 {step['to']}"
            for i, step in enumerate(plan)
        ]

        return f"要实现 {target},建议按以下步骤操作:\n\n" + "\n".join(steps)

    def get_status(self) -> dict[str, Any]:
        """获取解释器状态"""
        return {
            "name": self.name,
            "version": self.version,
            "explanations_generated": self.explanations_generated,
            "supported_types": [t.value for t in ExplanationType],
        }


# 全局单例
_explainer_instance: CounterfactualExplainer | None = None


def get_counterfactual_explainer() -> CounterfactualExplainer:
    """获取反事实解释器实例"""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = CounterfactualExplainer()
    return _explainer_instance
