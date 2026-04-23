#!/usr/bin/env python3

"""
多方案生成引擎
Multi-Plan Generator

功能:
1. 为同一意图生成多个可行方案
2. 支持不同策略的方案生成
3. 考虑资源约束和优先级

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .xiaonuo_planner_engine import ExecutionMode, ExecutionPlan, ExecutionStep, Intent

logger = logging.getLogger(__name__)


class PlanStrategy(Enum):
    """方案策略类型"""
    FAST = "fast"  # 快速执行策略（优先速度）
    RELIABLE = "reliable"  # 可靠执行策略（优先成功率）
    ECONOMICAL = "economical"  # 节约资源策略（优先资源利用率）
    BALANCED = "balanced"  # 平衡策略（综合考虑）


@dataclass
class PlanVariant:
    """方案变体"""
    strategy: PlanStrategy
    plan: ExecutionPlan
    score: float  # 方案评分 0-1
    advantages: list[str] = field(default_factory=list)
    disadvantages: list[str] = field(default_factory=list)


class MultiPlanGenerator:
    """
    多方案生成器

    核心功能:
    1. 为同一意图生成多个方案
    2. 不同策略导向的方案
    3. 方案评分和对比
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def generate(
        self,
        intent: Intent,
        context: dict[str, Any],
        strategies: Optional[list[PlanStrategy]] = None
    ) -> list[PlanVariant]:
        """
        生成多个执行方案

        Args:
            intent: 用户意图
            context: 上下文信息
            strategies: 要生成的策略列表（默认全部）

        Returns:
            List[PlanVariant]: 方案变体列表
        """
        self.logger.info(f"🎯 生成多方案: {intent.intent_type.value}")

        if strategies is None:
            strategies = [PlanStrategy.FAST, PlanStrategy.RELIABLE, PlanStrategy.BALANCED]

        variants = []

        for strategy in strategies:
            try:
                plan = await self._generate_plan_for_strategy(intent, context, strategy)

                # 评估方案
                score = self._score_plan(plan, strategy)
                advantages, disadvantages = self._analyze_plan(plan, strategy)

                variant = PlanVariant(
                    strategy=strategy,
                    plan=plan,
                    score=score,
                    advantages=advantages,
                    disadvantages=disadvantages,
                )

                variants.append(variant)
                self.logger.info(f"   ✅ {strategy.value} 方案生成完成 (评分: {score:.2f})")

            except Exception as e:
                self.logger.warning(f"   ⚠️ {strategy.value} 方案生成失败: {e}")

        # 按评分排序
        variants.sort(key=lambda v: v.score, reverse=True)

        return variants

    async def _generate_plan_for_strategy(
        self,
        intent: Intent,
        context: dict[str, Any],
        strategy: PlanStrategy
    ) -> ExecutionPlan:
        """为特定策略生成方案"""
        # 根据策略调整步骤
        base_steps = await self._generate_base_steps(intent, context)
        adjusted_steps = self._adjust_steps_for_strategy(base_steps, strategy)

        # 创建方案
        plan = ExecutionPlan(
            plan_id=f"plan_{strategy.value}_{int(__import__('time').time())}",
            intent=intent,
            steps=adjusted_steps,
            mode=self._select_mode_for_strategy(strategy),
            estimated_time=sum(s.estimated_time for s in adjusted_steps),
        )

        return plan

    async def _generate_base_steps(
        self,
        intent: Intent,
        context: dict[str, Any]]
    ) -> list[ExecutionStep]:
        """生成基础步骤"""
        from .task_decomposer import TaskDecomposer
        decomposer = TaskDecomposer()
        return await decomposer.decompose(intent, context)

    def _adjust_steps_for_strategy(
        self,
        steps: list[ExecutionStep],
        strategy: PlanStrategy
    ) -> list[ExecutionStep]:
        """根据策略调整步骤"""
        adjusted = []

        for step in steps:
            new_step = ExecutionStep(
                id=f"{strategy.value}_{step.id}",
                description=step.description,
                agent=step.agent,
                action=step.action,
                parameters=step.parameters.copy(),
                dependencies=step.dependencies.copy(),
                estimated_time=step.estimated_time,
                required_resources=step.required_resources.copy(),
            )

            # 根据策略调整时间估算
            if strategy == PlanStrategy.FAST:
                new_step.estimated_time = int(step.estimated_time * 0.7)  # 快速模式减少30%时间
            elif strategy == PlanStrategy.RELIABLE:
                new_step.estimated_time = int(step.estimated_time * 1.3)  # 可靠模式增加30%时间
            elif strategy == PlanStrategy.ECONOMICAL:
                # 节约模式增加10%时间（复用缓存）
                new_step.estimated_time = int(step.estimated_time * 1.1)

            adjusted.append(new_step)

        return adjusted

    def _select_mode_for_strategy(self, strategy: PlanStrategy) -> ExecutionMode:
        """为策略选择执行模式"""
        if strategy == PlanStrategy.FAST:
            return ExecutionMode.PARALLEL  # 快速模式：并行执行
        elif strategy == PlanStrategy.RELIABLE:
            return ExecutionMode.SEQUENTIAL  # 可靠模式：顺序执行
        else:
            return ExecutionMode.HYBRID  # 其他：混合模式

    def _score_plan(self, plan: ExecutionPlan, strategy: PlanStrategy) -> float:
        """方案评分"""
        score = 0.5  # 基础分

        # 根据策略类型评分
        if strategy == PlanStrategy.FAST:
            # 快速模式：时间越短越好
            time_score = max(0, 1 - plan.estimated_time / 600)  # 10分钟内满分
            score += 0.3 * time_score

        elif strategy == PlanStrategy.RELIABLE:
            # 可靠模式：步骤越少越稳定
            step_count_score = max(0, 1 - len(plan.steps) / 10)
            score += 0.3 * step_count_score

        elif strategy == PlanStrategy.ECONOMICAL:
            # 节约模式：资源需求越少越好
            resource_count = (
                len(plan.resource_requirements.services) +
                len(plan.resource_requirements.databases)
            )
            resource_score = max(0, 1 - resource_count / 10)
            score += 0.3 * resource_score

        else:  # BALANCED
            # 平衡模式：综合考虑
            score += 0.3 * (1 - plan.estimated_time / 900)
            score += 0.2 * max(0, 1 - len(plan.steps) / 10)

        return min(1.0, score)

    def _analyze_plan(
        self,
        plan: ExecutionPlan,
        strategy: PlanStrategy
    ) -> tuple[list[str], list[str]]:
        """分析方案优缺点"""
        advantages = []
        disadvantages = []

        if strategy == PlanStrategy.FAST:
            advantages.append("执行速度快")
            advantages.append("适合紧急任务")
            disadvantages.append("可能牺牲可靠性")
            disadvantages.append("资源消耗较高")

        elif strategy == PlanStrategy.RELIABLE:
            advantages.append("成功率高")
            advantages.append("容错能力强")
            disadvantages.append("执行时间较长")
            disadvantages.append("可能过度保守")

        elif strategy == PlanStrategy.ECONOMICAL:
            advantages.append("资源利用率高")
            advantages.append("成本较低")
            disadvantages.append("速度较慢")
            disadvantages.append("可能受缓存影响")

        else:  # BALANCED
            advantages.append("综合考虑各方因素")
            advantages.append("适用性广")
            disadvantages.append("可能在特定场景下不是最优")

        return advantages, disadvantages

    def get_generation_stats(self) -> dict[str, Any]:
        """获取生成统计"""
        return {
            "available_strategies": [s.value for s in PlanStrategy],
            "strategy_count": len(PlanStrategy),
        }

