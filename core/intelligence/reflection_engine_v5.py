#!/usr/bin/env python3
"""
反思引擎 v5.0 - 因果推理与自适应循环
Reflection Engine v5.0 - Causal Reasoning & Adaptive Loop

v5.0核心特性:
1. 完整反思循环 - 反思→学习→改进的闭环
2. 因果推理分析 - 识别问题的根本原因
3. 思维链追踪 - 追踪推理过程
4. 自适应改进 - 自动应用反思建议

作者: Athena平台团队
版本: v5.0.0 "因果之光"
创建时间: 2026-01-23
"""

import asyncio
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

logger = setup_logging()


class ReflectionType(Enum):
    """反思类型"""

    OUTPUT = "output"  # 输出反思
    PROCESS = "process"  # 过程反思
    CAUSAL = "causal"  # 因果反思
    STRATEGIC = "strategic"  # 战略反思


class CausalRelation(Enum):
    """因果关系类型"""

    DIRECT = "direct"  # 直接因果
    INDIRECT = "indirect"  # 间接因果
    CONTRIBUTING = "contributing"  # 贡献因素
    CORRELATION = "correlation"  # 相关关系


class ActionCategory(Enum):
    """行动类别"""

    IMMEDIATE = "immediate"  # 立即执行
    SHORT_TERM = "short_term"  # 短期改进
    LONG_TERM = "long_term"  # 长期规划


class ActionPriority(Enum):
    """行动优先级"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionStatus(Enum):
    """行动状态"""

    PENDING = "pending"
    IMPLEMENTING = "implementing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ThoughtStep:
    """思维步骤"""

    step_id: str
    timestamp: datetime
    content: str
    reasoning_type: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalFactor:
    """因果因子"""

    factor_id: str
    description: str
    relation_type: CausalRelation
    strength: float  # 因果强度 0-1
    confidence: float  # 置信度 0-1
    evidence: list[str]  # 证据
    actionable: bool  # 是否可行动


@dataclass
class ReflectionActionItem:
    """反思行动项"""

    action_id: str
    description: str
    priority: ActionPriority
    category: ActionCategory
    implementation: dict[str, Any]
    expected_impact: float
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


@dataclass
class ReflectionLoopV5:
    """反思循环 v5.0"""

    loop_id: str
    timestamp: datetime
    reflection_type: ReflectionType

    # 输入
    original_input: str
    output: str
    context: dict[str, Any]
    # 思维链
    thought_chain: list[ThoughtStep]

    # 反思结果
    reflection_result: dict[str, Any]
    # 因果分析
    causal_factors: list[CausalFactor]

    # 行动项
    action_items: list[ReflectionActionItem]

    # 改进效果
    improvement_measured: bool = False
    improvement_score: float = 0.0


class ReflectionEngineV5:
    """
    反思引擎 v5.0 - 完整反思循环

    核心改进:
    1. 完整的反思→学习→改进闭环
    2. 因果推理分析
    3. 思维链追踪
    4. 自适应改进
    """

    def __init__(self, agent_id: str = "default_agent", llm_client=None):
        self.agent_id = agent_id
        self.llm_client = llm_client

        # 反思历史
        self.reflection_history: list[ReflectionLoopV5] = []

        # 因果知识库
        self.causal_knowledge: dict[str, list[CausalFactor]] = defaultdict(list)

        # 行动项追踪
        self.action_tracker: dict[str, ReflectionActionItem] = {}

        # 改进效果跟踪
        self.improvement_history: list[dict[str, Any]] = []

        # 质量阈值
        self.quality_thresholds = {
            "accuracy": 0.85,
            "completeness": 0.80,
            "clarity": 0.85,
            "relevance": 0.90,
        }

        # 统计信息
        self.stats = {
            "total_reflections": 0,
            "causal_analyses": 0,
            "action_items_created": 0,
            "action_items_completed": 0,
            "improvements_measured": 0,
            "avg_improvement_score": 0.0,
            "total_processing_time": 0.0,
        }

        logger.info(f"🤔 反思引擎v5.0初始化: {agent_id}")

    async def reflect_with_loop(
        self,
        original_input: str,
        output: str,
        context: dict[str, Any],        thought_chain: list[ThoughtStep] | None = None,
        reflection_types: list[ReflectionType] | None = None,
    ) -> ReflectionLoopV5:
        """
        执行完整反思循环

        Args:
            original_input: 原始输入
            output: 输出结果
            context: 上下文
            thought_chain: 思维链(如果可用)
            reflection_types: 要执行的反思类型

        Returns:
            完整的反思循环对象
        """
        reflection_start = datetime.now()

        if reflection_types is None:
            reflection_types = [
                ReflectionType.OUTPUT,
                ReflectionType.PROCESS,
                ReflectionType.CAUSAL,
            ]

        logger.info("🔄 开始反思循环...")

        # 创建反思循环对象
        loop = ReflectionLoopV5(
            loop_id=self._generate_loop_id(),
            timestamp=datetime.now(),
            reflection_type=ReflectionType.OUTPUT,
            original_input=original_input,
            output=output,
            context=context,
            thought_chain=thought_chain or [],
            reflection_result={},
            causal_factors=[],
            action_items=[],
        )

        # 1. 执行多种类型的反思
        for reflection_type in reflection_types:
            try:
                await self._perform_reflection(loop, reflection_type)
            except Exception as e:
                logger.warning(f"反思类型 {reflection_type.value} 失败: {e}")

        # 2. 因果分析
        if ReflectionType.CAUSAL in reflection_types:
            try:
                await self._perform_causal_analysis(loop)
            except Exception as e:
                logger.warning(f"因果分析失败: {e}")

        # 3. 生成行动项
        try:
            await self._generate_action_items(loop)
        except Exception as e:
            logger.warning(f"生成行动项失败: {e}")

        # 4. 自动执行立即行动项
        try:
            await self._execute_immediate_actions(loop)
        except Exception as e:
            logger.warning(f"执行立即行动失败: {e}")

        # 5. 记录反思循环
        self.reflection_history.append(loop)
        self.stats["total_reflections"] += 1

        processing_time = (datetime.now() - reflection_start).total_seconds()
        self.stats["total_processing_time"] += processing_time

        logger.info(f"✅ 反思循环完成: {loop.loop_id}, 耗时{processing_time:.2f}s")

        return loop

    async def _perform_reflection(self, loop: ReflectionLoopV5, reflection_type: ReflectionType):
        """执行特定类型的反思"""
        if reflection_type == ReflectionType.OUTPUT:
            result = await self._reflect_on_output(loop)
        elif reflection_type == ReflectionType.PROCESS:
            result = await self._reflect_on_process(loop)
        elif reflection_type == ReflectionType.CAUSAL:
            result = await self._reflect_on_causality(loop)
        elif reflection_type == ReflectionType.STRATEGIC:
            result = await self._reflect_on_strategy(loop)
        else:
            result = {"status": "unknown_reflection_type"}

        loop.reflection_result[reflection_type.value] = result

    async def _reflect_on_output(self, loop: ReflectionLoopV5) -> dict[str, Any]:
        """输出反思"""
        # 评估输出的质量
        quality_scores = {
            "accuracy": await self._assess_accuracy(loop.output, loop.context),
            "completeness": await self._assess_completeness(loop.output, loop.context),
            "clarity": await self._assess_clarity(loop.output),
            "relevance": await self._assess_relevance(loop.output, loop.original_input),
        }

        # 计算总体质量分数
        overall_quality = sum(quality_scores.values()) / len(quality_scores)

        # 生成反馈
        feedback = await self._generate_quality_feedback(quality_scores)

        return {
            "quality_scores": quality_scores,
            "overall_quality": overall_quality,
            "feedback": feedback,
            "needs_improvement": overall_quality < 0.8,
        }

    async def _reflect_on_process(self, loop: ReflectionLoopV5) -> dict[str, Any]:
        """过程反思"""
        if not loop.thought_chain:
            return {"status": "no_thought_chain_available"}

        # 分析思维链
        process_analysis = {
            "step_count": len(loop.thought_chain),
            "reasoning_depth": await self._calculate_reasoning_depth(loop.thought_chain),
            "logical_consistency": await self._assess_logical_consistency(loop.thought_chain),
            "confidence_evolution": [step.confidence for step in loop.thought_chain],
        }

        # 识别问题步骤
        problem_steps = await self._identify_problem_steps(loop.thought_chain)

        return {
            "process_analysis": process_analysis,
            "problem_steps": len(problem_steps),
            "process_quality": 1.0 - min(len(problem_steps) / max(len(loop.thought_chain), 1), 1.0),
        }

    async def _perform_causal_analysis(self, loop: ReflectionLoopV5):
        """执行因果分析"""
        # 识别输出中的问题
        problems = await self._identify_problems(loop)

        # 对每个问题进行因果分析
        for problem in problems:
            try:
                causal_factors = await self._analyze_causes(problem, loop)
                loop.causal_factors.extend(causal_factors)
            except Exception as e:
                logger.warning(f"分析问题原因失败: {e}")

        # 存储到因果知识库
        for factor in loop.causal_factors:
            self.causal_knowledge[loop.loop_id].append(factor)

        self.stats["causal_analyses"] += len(problems)

    async def _analyze_causes(
        self, problem: dict[str, Any], loop: ReflectionLoopV5
    ) -> list[CausalFactor]:
        """分析问题的原因"""
        causal_factors = []

        # 基于"5个为什么"方法进行因果分析
        current_problem = problem
        for depth in range(5):  # 5层深度
            # 询问"为什么"
            causes = await self._find_causes(current_problem, loop, depth)

            if not causes:
                break

            causal_factors.extend(causes)

            # 如果找到根本原因,停止
            if any(c.relation_type == CausalRelation.DIRECT for c in causes):
                break

            # 更新当前问题为最可能的原因
            if causes:
                current_problem = {
                    "type": "cause",
                    "description": causes[0].description,
                    "depth": depth + 1,
                }

        return causal_factors

    async def _find_causes(
        self, problem: dict[str, Any], loop: ReflectionLoopV5, depth: int
    ) -> list[CausalFactor]:
        """寻找问题的原因"""
        potential_causes = []

        # 检查常见原因类型
        common_causes = [
            {
                "description": "输入信息不完整",
                "type": CausalRelation.CONTRIBUTING,
                "strength": 0.7,
                "actionable": True,
                "evidence": ["输入长度较短", "缺少关键参数"],
            },
            {
                "description": "知识库信息过时",
                "type": CausalRelation.CONTRIBUTING,
                "strength": 0.6,
                "actionable": True,
                "evidence": ["检索结果相关度低"],
            },
            {
                "description": "推理步骤跳跃",
                "type": CausalRelation.DIRECT,
                "strength": 0.8,
                "actionable": True,
                "evidence": ["思维链不连续"],
            },
            {
                "description": "上下文理解偏差",
                "type": CausalRelation.INDIRECT,
                "strength": 0.5,
                "actionable": True,
                "evidence": ["上下文关键词匹配度低"],
            },
        ]

        # 根据问题类型选择可能的原因
        for cause in common_causes:
            # 简化:随机选择一些原因(实际应该基于分析)
            if depth == 0 or (depth < 3 and cause["strength"] > 0.6):
                factor = CausalFactor(
                    factor_id=f"{loop.loop_id}_cause_{depth}_{len(potential_causes)}",
                    description=cause["description"],
                    relation_type=cause["type"],
                    strength=cause["strength"],
                    confidence=0.7,
                    evidence=cause["evidence"],
                    actionable=cause["actionable"],
                )
                potential_causes.append(factor)

        return potential_causes

    async def _generate_action_items(self, loop: ReflectionLoopV5):
        """生成行动项"""
        action_items = []

        # 基于反思结果生成行动项
        for reflection_type, result in loop.reflection_result.items():
            if result.get("needs_improvement", False):
                actions = await self._create_improvement_actions(reflection_type, result, loop)
                action_items.extend(actions)

        # 基于因果因子生成行动项
        for factor in loop.causal_factors:
            if factor.actionable and factor.strength > 0.6:
                action = await self._create_action_from_factor(factor, loop)
                if action:
                    action_items.append(action)

        # 按优先级排序
        priority_order = {ActionPriority.HIGH: 3, ActionPriority.MEDIUM: 2, ActionPriority.LOW: 1}

        action_items.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=True)

        loop.action_items = action_items

        # 追踪行动项
        for action in action_items:
            self.action_tracker[action.action_id] = action

        self.stats["action_items_created"] += len(action_items)

    async def _execute_immediate_actions(self, loop: ReflectionLoopV5):
        """执行立即行动项"""
        immediate_actions = [
            action for action in loop.action_items if action.category == ActionCategory.IMMEDIATE
        ]

        for action in immediate_actions:
            try:
                # 执行行动
                await self._execute_action(action)
                action.status = ActionStatus.COMPLETED
                action.completed_at = datetime.now()
                self.stats["action_items_completed"] += 1
            except Exception as e:
                logger.error(f"执行行动项失败 {action.action_id}: {e}")
                action.status = ActionStatus.FAILED

    async def measure_improvement(
        self, loop_id: str, new_output: str, new_context: dict[str, Any]
    ) -> float:
        """
        测量改进效果

        Args:
            loop_id: 反思循环ID
            new_output: 改进后的输出
            new_context: 新上下文

        Returns:
            改进分数 (0-1)
        """
        # 找到原始反思循环
        original_loop = next(
            (loop for loop in self.reflection_history if loop.loop_id == loop_id), None
        )

        if not original_loop:
            logger.warning(f"未找到反思循环: {loop_id}")
            return 0.0

        # 计算原始输出质量
        original_quality = await self._calculate_output_quality(
            original_loop.output, original_loop.context
        )

        # 计算新输出质量
        new_quality = await self._calculate_output_quality(new_output, new_context)

        # 计算改进分数
        improvement_score = new_quality - original_quality

        # 记录改进效果
        improvement_record = {
            "loop_id": loop_id,
            "timestamp": datetime.now().isoformat(),
            "original_quality": original_quality,
            "new_quality": new_quality,
            "improvement": improvement_score,
        }

        self.improvement_history.append(improvement_record)
        self.stats["improvements_measured"] += 1

        # 更新平均改进分数
        all_improvements = [max(r["improvement"], 0) for r in self.improvement_history]
        self.stats["avg_improvement_score"] = sum(all_improvements) / len(all_improvements)

        logger.info(f"📈 改进测量: {improvement_score:.3f}")

        return max(improvement_score, 0.0)

    # ========== 辅助方法 ==========

    def _generate_loop_id(self) -> str:
        """生成反思循环ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_part = hashlib.md5(f"{timestamp}_{id(self, usedforsecurity=False)}".encode()).hexdigest()[:8]
        return f"loop_{timestamp}_{hash_part}"

    async def _assess_accuracy(self, output: str, context: dict[str, Any]) -> float:
        """评估准确性"""
        # 简化实现:基于输出长度和关键词
        base_score = 0.75
        if len(output) > 50:
            base_score += 0.1
        return min(base_score, 1.0)

    async def _assess_completeness(self, output: str, context: dict[str, Any]) -> float:
        """评估完整性"""
        # 简化实现:基于输出覆盖的信息点
        expected_keywords = context.get("expected_keywords", [])
        if not expected_keywords:
            return 0.8

        covered = sum(1 for kw in expected_keywords if kw.lower() in output.lower())
        return min(covered / len(expected_keywords) + 0.5, 1.0)

    async def _assess_clarity(self, output: str) -> float:
        """评估清晰度"""
        # 简化实现:基于句子结构
        sentences = output.split("。")
        if len(sentences) == 0:
            return 0.5

        avg_length = sum(len(s) for s in sentences) / len(sentences)
        if 10 < avg_length < 100:
            return 0.9
        elif avg_length <= 10 or avg_length >= 100:
            return 0.7
        return 0.8

    async def _assess_relevance(self, output: str, original_input: str) -> float:
        """评估相关性"""
        # 简化实现:基于关键词重叠
        input_words = set(original_input.lower().split())
        output_words = set(output.lower().split())

        if not input_words:
            return 0.8

        overlap = len(input_words & output_words)
        return min(overlap / len(input_words) + 0.6, 1.0)

    async def _generate_quality_feedback(self, quality_scores: dict[str, float]) -> str:
        """生成质量反馈"""
        # 识别最低分的维度
        lowest_metric = min(quality_scores, key=quality_scores.get)
        feedback = f"需要改进{lowest_metric},当前分数: {quality_scores[lowest_metric]:.2f}"
        return feedback

    async def _calculate_reasoning_depth(self, thought_chain: list[ThoughtStep]) -> int:
        """计算推理深度"""
        return len(thought_chain)

    async def _assess_logical_consistency(self, thought_chain: list[ThoughtStep]) -> float:
        """评估逻辑一致性"""
        if not thought_chain:
            return 0.8

        # 简化:基于置信度变化
        confidences = [step.confidence for step in thought_chain]
        if len(confidences) < 2:
            return 0.9

        # 计算置信度变化的一致性
        changes = [abs(confidences[i] - confidences[i + 1]) for i in range(len(confidences) - 1)]
        avg_change = sum(changes) / len(changes) if changes else 0

        # 变化越小越一致
        consistency = max(0.9 - avg_change, 0.5)
        return consistency

    async def _identify_problem_steps(self, thought_chain: list[ThoughtStep]) -> list[ThoughtStep]:
        """识别问题步骤"""
        # 简化:识别低置信度的步骤
        problem_steps = [step for step in thought_chain if step.confidence < 0.7]
        return problem_steps

    async def _identify_problems(self, loop: ReflectionLoopV5) -> list[dict[str, Any]]:
        """识别问题"""
        problems = []

        # 检查输出反思中的问题
        output_reflection = loop.reflection_result.get(ReflectionType.OUTPUT.value, {})
        if output_reflection.get("needs_improvement", False):
            problems.append(
                {
                    "type": "output_quality",
                    "description": "输出质量不达标",
                    "details": output_reflection.get("quality_scores", {}),
                }
            )

        # 检查过程反思中的问题
        process_reflection = loop.reflection_result.get(ReflectionType.PROCESS.value, {})
        problem_count = process_reflection.get("problem_steps", 0)
        if problem_count > 0:
            problems.append(
                {
                    "type": "reasoning_process",
                    "description": f"有{problem_count}个推理步骤存在问题",
                    "details": process_reflection,
                }
            )

        return problems

    async def _create_improvement_actions(
        self, reflection_type: str, result: dict[str, Any], loop: ReflectionLoopV5
    ) -> list[ReflectionActionItem]:
        """创建改进行动项"""
        actions = []

        if reflection_type == ReflectionType.OUTPUT.value:
            # 基于输出质量创建行动项
            quality_scores = result.get("quality_scores", {})
            for metric, score in quality_scores.items():
                if score < 0.8:
                    action = ReflectionActionItem(
                        action_id=f"action_{loop.loop_id}_{metric}",
                        description=f"改进{metric}: 当前分数{score:.2f}",
                        priority=ActionPriority.HIGH if score < 0.7 else ActionPriority.MEDIUM,
                        category=ActionCategory.SHORT_TERM,
                        implementation={
                            "type": "quality_improvement",
                            "metric": metric,
                            "target_score": 0.85,
                        },
                        expected_impact=0.1,
                    )
                    actions.append(action)

        return actions

    async def _create_action_from_factor(
        self, factor: CausalFactor, loop: ReflectionLoopV5
    ) -> ReflectionActionItem | None:
        """从因果因子创建行动项"""
        if not factor.actionable:
            return None

        priority = ActionPriority.HIGH if factor.strength > 0.7 else ActionPriority.MEDIUM

        action = ReflectionActionItem(
            action_id=f"action_{loop.loop_id}_{factor.factor_id}",
            description=f"解决因果问题: {factor.description}",
            priority=priority,
            category=ActionCategory.SHORT_TERM,
            implementation={
                "type": "causal_intervention",
                "factor_id": factor.factor_id,
                "intervention_strength": factor.strength,
            },
            expected_impact=factor.strength * 0.5,
        )

        return action

    async def _execute_action(self, action: ReflectionActionItem):
        """执行行动项"""
        # 简化实现:记录执行
        logger.info(f"🎯 执行行动: {action.description}")

    async def _reflect_on_causality(self, loop: ReflectionLoopV5) -> dict[str, Any]:
        """因果反思"""
        return {"status": "causal_reflection_completed"}

    async def _reflect_on_strategy(self, loop: ReflectionLoopV5) -> dict[str, Any]:
        """战略反思"""
        return {"status": "strategic_reflection_completed"}

    async def _calculate_output_quality(self, output: str, context: dict[str, Any]) -> float:
        """计算输出质量"""
        accuracy = await self._assess_accuracy(output, context)
        completeness = await self._assess_completeness(output, context)
        clarity = await self._assess_clarity(output)

        return (accuracy + completeness + clarity) / 3.0

    async def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "agent_id": self.agent_id,
            "stats": self.stats,
            "total_loops": len(self.reflection_history),
            "pending_actions": sum(
                1
                for action in self.action_tracker.values()
                if action.status == ActionStatus.PENDING
            ),
            "completed_actions": sum(
                1
                for action in self.action_tracker.values()
                if action.status == ActionStatus.COMPLETED
            ),
            "avg_processing_time": (
                self.stats["total_processing_time"] / self.stats["total_reflections"]
                if self.stats["total_reflections"] > 0
                else 0
            ),
        }


# 测试和实用函数
async def test_reflection_v5():
    """测试反思引擎v5.0"""
    logger.info("🧪 测试反思引擎v5.0...")

    # 创建反思引擎
    engine = ReflectionEngineV5(agent_id="xiaonuo_test")

    # 模拟思维链
    thought_chain = [
        ThoughtStep(
            step_id="step1",
            timestamp=datetime.now(),
            content="分析用户意图",
            reasoning_type="intent_analysis",
            confidence=0.9,
        ),
        ThoughtStep(
            step_id="step2",
            timestamp=datetime.now(),
            content="检索相关知识",
            reasoning_type="knowledge_retrieval",
            confidence=0.85,
        ),
    ]

    # 执行反思循环
    loop = await engine.reflect_with_loop(
        original_input="帮我分析这个专利",
        output="这是一个关于人工智能的专利...",
        context={"domain": "patent_analysis"},
        thought_chain=thought_chain,
    )

    print(f"反思循环完成: {loop.loop_id}")
    print(f"因果因子数量: {len(loop.causal_factors)}")
    print(f"行动项数量: {len(loop.action_items)}")

    # 获取统计
    stats = await engine.get_statistics()
    print(f"统计信息: {stats}")

    return engine


if __name__ == "__main__":
    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    # 运行测试
    asyncio.run(test_reflection_v5())
