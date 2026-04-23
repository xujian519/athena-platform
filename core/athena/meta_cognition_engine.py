#!/usr/bin/env python3
from __future__ import annotations
"""
Athena元认知引擎
Meta-Cognition Engine for Athena

实现"关于认知的认知",让Athena能够:
1. 监控自身思考过程
2. 评估认知策略有效性
3. 动态调整认知方法
4. 预测和规划认知任务
5. 自我反思和改进

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "元认知之光"
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class CognitiveStrategy(Enum):
    """认知策略"""

    ANALYTICAL = "analytical"  # 分析型 - 逐步推理
    INTUITIVE = "intuitive"  # 直觉型 - 快速判断
    SYSTEMATIC = "systematic"  # 系统型 - 结构化分析
    CREATIVE = "creative"  # 创造型 - 发散思维
    CRITICAL = "critical"  # 批判型 - 质疑验证
    COLLABORATIVE = "collaborative"  # 协作型 - 集体智慧
    META = "meta"  # 元认知 - 思考思考本身


class CognitiveLoad(Enum):
    """认知负荷"""

    MINIMAL = "minimal"  # 最小 - 熟悉任务
    LIGHT = "light"  # 轻度 - 简单任务
    MODERATE = "moderate"  # 中度 - 需要思考
    HEAVY = "heavy"  # 重度 - 复杂任务
    OVERLOAD = "overload"  # 超载 - 需要分解


class ThinkingPhase(Enum):
    """思考阶段"""

    PREPARATION = "preparation"  # 准备阶段
    GENERATION = "generation"  # 生成阶段
    EVALUATION = "evaluation"  # 评估阶段
    DECISION = "decision"  # 决策阶段
    REFLECTION = "reflection"  # 反思阶段
    META = "meta"  # 元认知阶段


@dataclass
class CognitiveState:
    """认知状态"""

    current_strategy: CognitiveStrategy = CognitiveStrategy.ANALYTICAL
    cognitive_load: CognitiveLoad = CognitiveLoad.MODERATE
    thinking_phase: ThinkingPhase = ThinkingPhase.PREPARATION
    focus_level: float = 0.8  # 专注度 0-1
    confidence_level: float = 0.7  # 置信度 0-1
    mental_energy: float = 1.0  # 精神能量 0-1
    working_memory_usage: float = 0.3  # 工作记忆使用率 0-1
    reasoning_depth: int = 3  # 推理深度


@dataclass
class ThinkingProcess:
    """思考过程记录"""

    process_id: str
    task: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    cognitive_state: CognitiveState = field(default_factory=CognitiveState)
    thought_steps: list[dict[str, Any]] = field(default_factory=list)
    strategy_changes: list[dict[str, Any]] = field(default_factory=list)
    meta_observations: list[str] = field(default_factory=list)
    effectiveness_score: Optional[float] = None


class MetaCognitionEngine:
    """
    元认知引擎

    核心能力:
    1. 自我监控 - 实时监控思考过程
    2. 策略选择 - 动态选择最优认知策略
    3. 负荷管理 - 平衡认知负荷
    4. 效果评估 - 评估思考质量
    5. 自我调节 - 调整认知方法
    """

    def __init__(self, agent_id: str = "athena"):
        self.agent_id = agent_id

        # 当前认知状态
        self.current_state = CognitiveState()

        # 思考过程历史
        self.thinking_history: deque[ThinkingProcess] = deque(maxlen=1000)
        self.current_process: ThinkingProcess | None = None

        # 策略效果统计
        self.strategy_performance: dict[CognitiveStrategy, dict[str, float]] = defaultdict(
            lambda: {
                "usage_count": 0,
                "avg_effectiveness": 0.7,
                "avg_time": 0.0,
                "success_rate": 0.8,
            }
        )

        # 元认知模式
        self.meta_patterns = {
            "task_complexity_mapping": {},  # 任务复杂度 -> 最佳策略
            "load_thresholds": {},  # 负荷阈值
            "strategy_combinations": {},  # 策略组合
        }

        # 自我反思记录
        self.reflection_insights: deque[dict[str, Any]] = deque(maxlen=100)

        logger.info(f"🧠 Athena元认知引擎初始化完成 - {self.agent_id}")

    async def start_thinking(
        self, task: str, initial_strategy: CognitiveStrategy | None = None
    ) -> ThinkingProcess:
        """开始一个思考过程"""
        process_id = f"thinking_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # 智能选择初始策略
        if initial_strategy is None:
            initial_strategy = await self._select_optimal_strategy(task)

        # 创建思考过程
        process = ThinkingProcess(
            process_id=process_id,
            task=task,
            cognitive_state=CognitiveState(current_strategy=initial_strategy),
        )

        self.current_process = process

        # 记录元观察
        await self._observe_thinking_start(task, initial_strategy)

        logger.info(f"💭 开始思考过程: {task[:50]}...")
        return process

    async def think_step(
        self, thought: str, reasoning: str, confidence: float = 0.7
    ) -> dict[str, Any]:
        """执行一个思考步骤"""
        if self.current_process is None:
            raise RuntimeError("没有活跃的思考过程")

        step = {
            "step_number": len(self.current_process.thought_steps) + 1,
            "thought": thought,
            "reasoning": reasoning,
            "confidence": confidence,
            "strategy": self.current_process.cognitive_state.current_strategy.value,
            "phase": self.current_process.cognitive_state.thinking_phase.value,
            "timestamp": datetime.now().isoformat(),
            "cognitive_load": self.current_process.cognitive_state.cognitive_load.value,
        }

        self.current_process.thought_steps.append(step)

        # 更新认知状态
        await self._update_cognitive_state_after_step(step)

        logger.debug(f"  思考步骤 {step['step_number']}: {thought[:50]}...")

        return step

    async def change_strategy(self, new_strategy: CognitiveStrategy, reason: str) -> dict[str, Any]:
        """改变认知策略"""
        if self.current_process is None:
            raise RuntimeError("没有活跃的思考过程")

        old_strategy = self.current_process.cognitive_state.current_strategy

        change_record = {
            "from_strategy": old_strategy.value,
            "to_strategy": new_strategy.value,
            "reason": reason,
            "step_number": len(self.current_process.thought_steps) + 1,
            "timestamp": datetime.now().isoformat(),
        }

        self.current_process.strategy_changes.append(change_record)
        self.current_process.cognitive_state.current_strategy = new_strategy

        # 元观察:记录策略变更原因
        await self._observe_strategy_change(old_strategy, new_strategy, reason)

        logger.info(f"🔄 策略变更: {old_strategy.value} -> {new_strategy.value} ({reason})")

        return change_record

    async def evaluate_thinking_quality(self) -> dict[str, Any]:
        """评估当前思考质量"""
        if self.current_process is None:
            raise RuntimeError("没有活跃的思考过程")

        process = self.current_process

        # 多维度评估
        metrics = {
            "depth_score": self._evaluate_reasoning_depth(process),
            "coherence_score": self._evaluate_coherence(process),
            "adaptability_score": self._evaluate_adaptability(process),
            "efficiency_score": self._evaluate_efficiency(process),
            "meta_awareness_score": self._evaluate_meta_awareness(process),
        }

        # 综合得分
        overall_score = np.mean(list(metrics.values()))
        process.effectiveness_score = overall_score

        evaluation = {
            "overall_score": overall_score,
            "metrics": metrics,
            "strengths": [k for k, v in metrics.items() if v > 0.8],
            "weaknesses": [k for k, v in metrics.items() if v < 0.6],
            "recommendations": await self._generate_improvement_recommendations(metrics),
            "timestamp": datetime.now().isoformat(),
        }

        return evaluation

    async def finish_thinking(self, outcome: str, success: bool) -> ThinkingProcess:
        """完成思考过程"""
        if self.current_process is None:
            raise RuntimeError("没有活跃的思考过程")

        process = self.current_process
        process.end_time = datetime.now()

        # 最终评估
        evaluation = await self.evaluate_thinking_quality()

        # 更新策略性能统计
        strategy = process.cognitive_state.current_strategy
        self.strategy_performance[strategy]["usage_count"] += 1
        self.strategy_performance[strategy]["success_rate"] = (
            self.strategy_performance[strategy]["success_rate"] * 0.9
            + (1.0 if success else 0.0) * 0.1
        )
        self.strategy_performance[strategy]["avg_effectiveness"] = (
            self.strategy_performance[strategy]["avg_effectiveness"] * 0.8
            + evaluation["overall_score"] * 0.2
        )

        # 计算思考时长
        duration = (process.end_time - process.start_time).total_seconds()
        self.strategy_performance[strategy]["avg_time"] = (
            self.strategy_performance[strategy]["avg_time"] * 0.9 + duration * 0.1
        )

        # 记录到历史
        self.thinking_history.append(process)

        # 生成元认知洞察
        insight = await self._generate_meta_insight(process, evaluation, outcome)
        self.reflection_insights.append(insight)

        logger.info(
            f"✅ 思考完成: {process.task[:50]}... (效果: {evaluation['overall_score']:.2f})"
        )

        self.current_process = None
        return process

    async def _select_optimal_strategy(self, task: str) -> CognitiveStrategy:
        """智能选择最优认知策略"""
        # 分析任务特征
        task_complexity = await self._estimate_task_complexity(task)
        has_uncertainty = "?" in task or "可能" in task or "如何" in task
        is_creative = "创造" in task or "设计" in task or "新" in task
        is_critical = "评估" in task or "验证" in task or "检查" in task

        # 根据特征选择策略
        if task_complexity > 0.8:
            return CognitiveStrategy.SYSTEMATIC
        elif is_creative:
            return CognitiveStrategy.CREATIVE
        elif is_critical:
            return CognitiveStrategy.CRITICAL
        elif has_uncertainty:
            return CognitiveStrategy.ANALYTICAL
        else:
            return CognitiveStrategy.INTUITIVE

    async def _estimate_task_complexity(self, task: str) -> float:
        """估算任务复杂度"""
        complexity_factors = {
            "length": min(len(task) / 500, 1.0),
            "keywords": sum(
                [
                    "复杂" in task,
                    "分析" in task,
                    "系统" in task,
                    "设计" in task,
                    "优化" in task,
                    "综合" in task,
                ]
            )
            / 6,
            "questions": task.count("?") / 10,
            "subtasks": len([s for s in task.split(",") if len(s) > 5]) / 10,
        }

        return np.mean(list(complexity_factors.values()))

    async def _observe_thinking_start(self, task: str, strategy: CognitiveStrategy):
        """观察思考开始时的元认知信息"""
        observation = {
            "observation_type": "thinking_start",
            "task_complexity": await self._estimate_task_complexity(task),
            "chosen_strategy": strategy.value,
            "initial_cognitive_load": self.current_state.cognitive_load.value,
            "mental_energy": self.current_state.mental_energy,
            "timestamp": datetime.now().isoformat(),
        }

        if self.current_process:
            self.current_process.meta_observations.append(str(observation))

    async def _observe_strategy_change(
        self, old_strategy: CognitiveStrategy, new_strategy: CognitiveStrategy, reason: str
    ):
        """观察策略变更"""
        observation = {
            "observation_type": "strategy_change",
            "trigger": reason,
            "old_strategy_effectiveness": self.strategy_performance[old_strategy][
                "avg_effectiveness"
            ],
            "timestamp": datetime.now().isoformat(),
        }

        if self.current_process:
            self.current_process.meta_observations.append(str(observation))

    async def _update_cognitive_state_after_step(self, step: dict[str, Any]):
        """在思考步骤后更新认知状态"""
        if self.current_process is None:
            return

        # 增加工作记忆使用
        self.current_process.cognitive_state.working_memory_usage = min(
            self.current_process.cognitive_state.working_memory_usage + 0.05, 1.0
        )

        # 更新推理深度
        self.current_process.cognitive_state.reasoning_depth += 1

        # 如果步骤过多,增加认知负荷
        if self.current_process.cognitive_state.reasoning_depth > 5:
            load_levels = list(CognitiveLoad)
            current_idx = load_levels.index(self.current_process.cognitive_state.cognitive_load)
            if current_idx < len(load_levels) - 1:
                self.current_process.cognitive_state.cognitive_load = load_levels[current_idx + 1]

    def _evaluate_reasoning_depth(self, process: ThinkingProcess) -> float:
        """评估推理深度"""
        step_count = len(process.thought_steps)
        # 理想深度:3-7步
        if 3 <= step_count <= 7:
            return 1.0
        elif step_count < 3:
            return 0.5
        else:
            return max(0.6, 1.0 - (step_count - 7) * 0.05)

    def _evaluate_coherence(self, process: ThinkingProcess) -> float:
        """评估推理连贯性"""
        if len(process.thought_steps) < 2:
            return 1.0

        # 检查策略变更频率(过多变更降低连贯性)
        strategy_changes = len(process.strategy_changes)
        total_steps = len(process.thought_steps)

        if strategy_changes == 0:
            change_score = 1.0
        elif strategy_changes / total_steps < 0.3:
            change_score = 0.8
        else:
            change_score = 0.5

        return change_score

    def _evaluate_adaptability(self, process: ThinkingProcess) -> float:
        """评估适应性"""
        # 有策略变更说明有适应性
        if len(process.strategy_changes) > 0:
            # 但不能太多
            if len(process.strategy_changes) <= 2:
                return 1.0
            else:
                return 0.7
        return 0.5

    def _evaluate_efficiency(self, process: ThinkingProcess) -> float:
        """评估效率"""
        if process.end_time is None:
            return 0.7

        duration = (process.end_time - process.start_time).total_seconds()
        step_count = len(process.thought_steps)

        # 每步平均时间(理想:5-15秒)
        avg_time_per_step = duration / max(step_count, 1)

        if 5 <= avg_time_per_step <= 15:
            return 1.0
        elif avg_time_per_step < 5:
            return 0.8  # 可能太匆忙
        else:
            return max(0.5, 1.0 - (avg_time_per_step - 15) * 0.02)

    def _evaluate_meta_awareness(self, process: ThinkingProcess) -> float:
        """评估元认知意识"""
        # 有元观察记录说明有元认知意识
        observation_count = len(process.meta_observations)

        if observation_count >= 3:
            return 1.0
        elif observation_count >= 1:
            return 0.7
        else:
            return 0.4

    async def _generate_improvement_recommendations(self, metrics: dict[str, float]) -> list[str]:
        """生成改进建议"""
        recommendations = []

        if metrics["depth_score"] < 0.6:
            recommendations.append("建议增加推理深度,探索更多可能性")

        if metrics["coherence_score"] < 0.6:
            recommendations.append("建议减少不必要的策略变更,保持思维连贯")

        if metrics["adaptability_score"] < 0.6:
            recommendations.append("建议根据任务进展灵活调整认知策略")

        if metrics["efficiency_score"] < 0.6:
            recommendations.append("建议优化思考流程,提高效率")

        if metrics["meta_awareness_score"] < 0.6:
            recommendations.append("建议增强对自身思考过程的监控和反思")

        return recommendations

    async def _generate_meta_insight(
        self, process: ThinkingProcess, evaluation: dict[str, Any], outcome: str
    ) -> dict[str, Any]:
        """生成元认知洞察"""
        insight = {
            "process_id": process.process_id,
            "task": process.task,
            "strategy_used": process.cognitive_state.current_strategy.value,
            "effectiveness": evaluation["overall_score"],
            "key_learnings": {
                "best_performing_strategy": max(
                    self.strategy_performance.items(), key=lambda x: x[1]["avg_effectiveness"]
                )[0].value,
                "areas_for_improvement": evaluation["weaknesses"],
                "successful_patterns": evaluation["strengths"],
            },
            "timestamp": datetime.now().isoformat(),
        }

        return insight

    async def get_meta_report(self) -> dict[str, Any]:
        """获取元认知报告"""
        return {
            "agent_id": self.agent_id,
            "current_state": {
                "strategy": self.current_state.current_strategy.value,
                "cognitive_load": self.current_state.cognitive_load.value,
                "mental_energy": self.current_state.mental_energy,
                "focus_level": self.current_state.focus_level,
            },
            "strategy_performance": {
                strategy.value: perf for strategy, perf in self.strategy_performance.items()
            },
            "recent_insights": list(self.reflection_insights)[-5:],
            "total_thinking_processes": len(self.thinking_history),
            "avg_effectiveness": (
                np.mean(
                    [
                        p.effectiveness_score
                        for p in self.thinking_history
                        if p.effectiveness_score is not None
                    ]
                )
                if self.thinking_history
                else 0.0
            ),
        }


# 导出便捷函数
_athena_meta_engine: MetaCognitionEngine | None = None


def get_meta_cognition_engine() -> MetaCognitionEngine:
    """获取Athena元认知引擎单例"""
    global _athena_meta_engine
    if _athena_meta_engine is None:
        _athena_meta_engine = MetaCognitionEngine()
    return _athena_meta_engine
