#!/usr/bin/env python3

"""
成本评估模块
Cost Evaluator

功能:
1. 评估方案的时间成本
2. 评估方案的计算资源成本
3. 评估方案的人力成本
4. 综合成本分析和对比

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from .xiaonuo_planner_engine import ExecutionPlan

logger = logging.getLogger(__name__)


@dataclass
class CostBreakdown:
    """成本明细"""
    time_cost: int  # 时间成本（秒）
    compute_cost: float  # 计算成本（估算单位）
    resource_cost: float  # 资源成本（估算单位）
    human_cost: float  # 人力成本（估算单位）
    total_cost: float  # 总成本（标准化单位）


@dataclass
class CostComparison:
    """成本对比"""
    plan_id: str
    breakdown: CostBreakdown
    rank: int  # 成本排名（1=最低）
    efficiency: float  # 成本效率评分 0-1


class CostEvaluator:
    """
    成本评估器

    核心功能:
    1. 多维度成本评估
    2. 成本对比分析
    3. 成本优化建议
    """

    # 成本权重配置
    TIME_WEIGHT = 0.4
    COMPUTE_WEIGHT = 0.3
    RESOURCE_WEIGHT = 0.2
    HUMAN_WEIGHT = 0.1

    # 资源单位成本（标准化）
    COST_PER_SECOND = 0.1  # 每秒时间成本
    COST_PER_RESOURCE = 10  # 每个资源成本
    COST_PER_STEP = 5  # 每步骤基础成本

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.evaluation_history: list[CostComparison] = []

    def evaluate(
        self,
        plan: ExecutionPlan,
        plans_for_comparison: Optional[list[ExecutionPlan]] = None
    ) -> CostComparison:
        """
        评估方案成本

        Args:
            plan: 要评估的方案
            plans_for_comparison: 用于对比的其他方案

        Returns:
            CostComparison: 成本对比结果
        """
        self.logger.info(f"💰 评估成本: {plan.plan_id}")

        # 1. 计算各项成本
        time_cost = plan.estimated_time
        compute_cost = self._calculate_compute_cost(plan)
        resource_cost = self._calculate_resource_cost(plan)
        human_cost = self._calculate_human_cost(plan)

        # 2. 计算总成本
        total_cost = (
            time_cost * self.COST_PER_SECOND +
            compute_cost * self.COMPUTE_WEIGHT +
            resource_cost * self.COST_PER_RESOURCE +
            human_cost * self.COST_PER_STEP
        )

        # 3. 创建成本明细
        breakdown = CostBreakdown(
            time_cost=time_cost,
            compute_cost=compute_cost,
            resource_cost=resource_cost,
            human_cost=human_cost,
            total_cost=total_cost,
        )

        # 4. 计算排名
        rank = 1
        efficiency = self._calculate_efficiency(breakdown)

        if plans_for_comparison:
            # 计算其他方案的成本
            other_costs = []
            for other_plan in plans_for_comparison:
                if other_plan.plan_id != plan.plan_id:
                    other_total = self._estimate_total_cost(other_plan)
                    other_costs.append(other_total)

            # 确定排名
            rank = sum(1 for c in other_costs if c < total_cost) + 1

        # 5. 创建对比结果
        comparison = CostComparison(
            plan_id=plan.plan_id,
            breakdown=breakdown,
            rank=rank,
            efficiency=efficiency,
        )

        # 6. 记录历史
        self.evaluation_history.append(comparison)

        self.logger.info(f"   ✅ 成本评估完成: 总成本={total_cost:.2f}, 排名={rank}")

        return comparison

    def _calculate_compute_cost(self, plan: ExecutionPlan) -> float:
        """计算计算成本"""
        # 基于步骤复杂度和数量估算
        base_cost = len(plan.steps) * self.COST_PER_STEP

        # 根据执行模式调整
        if plan.mode.value == "parallel":
            # 并行执行需要更多计算资源
            base_cost *= 1.2
        elif plan.mode.value == "hybrid":
            base_cost *= 1.1

        return base_cost

    def _calculate_resource_cost(self, plan: ExecutionPlan) -> float:
        """计算资源成本"""
        # 计算所需资源数量
        resource_count = (
            len(plan.resource_requirements.agents) * 2 +
            len(plan.resource_requirements.services) +
            len(plan.resource_requirements.databases) * 3
        )

        return resource_count * self.COST_PER_RESOURCE

    def _calculate_human_cost(self, plan: ExecutionPlan) -> float:
        """计算人力成本（用户等待和交互成本）"""
        # 基于步骤数量和预计交互次数估算
        interaction_steps = sum(
            1 for step in plan.steps
            if "chat" in step.action.lower() or "用户" in step.action.lower()
        )

        base_cost = len(plan.steps) * self.COST_PER_STEP
        interaction_cost = interaction_steps * 10  # 交互步骤成本更高

        return base_cost + interaction_cost

    def _calculate_efficiency(self, breakdown: CostBreakdown) -> float:
        """计算成本效率评分"""
        # 效率 = (价值/成本) 的归一化评分
        # 这里简化处理，实际应该根据方案价值计算

        # 时间效率（时间越短越好）
        time_efficiency = max(0, 1 - breakdown.time_cost / 1800)  # 30分钟内

        # 资源效率（资源越少越好）
        resource_efficiency = max(0, 1 - breakdown.resource_cost / 100)

        # 综合效率
        efficiency = (time_efficiency * 0.6 + resource_efficiency * 0.4)

        return efficiency

    def _estimate_total_cost(self, plan: ExecutionPlan) -> float:
        """估算总成本（简化版）"""
        return (
            plan.estimated_time * self.COST_PER_SECOND +
            len(plan.steps) * self.COST_PER_STEP +
            len(plan.resource_requirements.services) * self.COST_PER_RESOURCE
        )

    def compare_plans(
        self,
        plans: list[ExecutionPlan]
    ) -> list[CostComparison]:
        """对比多个方案的成本"""
        comparisons = []

        for plan in plans:
            comparison = self.evaluate(plan, plans)
            comparisons.append(comparison)

        # 按总成本排序
        comparisons.sort(key=lambda c: c.breakdown.total_cost)

        # 更新排名
        for i, comparison in enumerate(comparisons, 1):
            comparison.rank = i

        return comparisons

    def get_optimization_suggestions(
        self,
        comparison: CostComparison
    ) -> list[str]:
        """获取成本优化建议"""
        suggestions = []

        breakdown = comparison.breakdown

        # 时间成本优化
        if breakdown.time_cost > 300:  # 超过5分钟
            suggestions.append("考虑使用并行执行模式减少总时间")

        # 资源成本优化
        if breakdown.resource_cost > 50:
            suggestions.append("尝试复用缓存资源以降低资源成本")

        # 计算成本优化
        if breakdown.compute_cost > 30:
            suggestions.append("简化步骤或合并相似操作以降低计算成本")

        # 人力成本优化
        if breakdown.human_cost > 20:
            suggestions.append("减少用户交互环节以降低等待成本")

        return suggestions

    def get_evaluation_stats(self) -> dict[str, Any]:
        """获取评估统计"""
        if not self.evaluation_history:
            return {"total_evaluations": 0}

        total_costs = [c.breakdown.total_cost for c in self.evaluation_history]

        return {
            "total_evaluations": len(self.evaluation_history),
            "average_cost": sum(total_costs) / len(total_costs),
            "lowest_cost": min(total_costs),
            "highest_cost": max(total_costs),
        }

