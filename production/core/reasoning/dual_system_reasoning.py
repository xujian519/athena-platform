#!/usr/bin/env python3
"""
双系统推理引擎

Dual System Reasoning Engine

基于Daniel Kahneman的双系统理论实现:
- System 1: 快速、直觉、自动、情感驱动
- System 2: 慢速、分析、理性、逻辑驱动

结合最新认知科学研究,实现智能的双系统协同推理。
"""

from __future__ import annotations
import asyncio
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .enhanced_reasoning_base import (
    BaseReasoner,
    ReasoningChain,
    ReasoningContext,
    ReasoningResult,
    ReasoningStep,
    ReasoningType,
)


@dataclass
class System1Profile:
    """System 1 直觉推理特征配置"""

    response_time_threshold: float = 0.5  # 响应时间阈值(秒)
    confidence_bias: float = 0.1  # 置信度偏差(过度自信)
    pattern_matching_weight: float = 0.8  # 模式匹配权重
    emotional_influence: float = 0.3  # 情感影响权重
    heuristic_usage: list[str] = field(
        default_factory=lambda: [
            "availability",  # 可得性启发式
            "representativeness",  # 代表性启发式
            "anchoring",  # 锚定启发式
            "affect_heuristic",  # 情感启发式
        ]
    )
    cognitive_biases: list[str] = field(
        default_factory=lambda: [
            "confirmation_bias",  # 确认偏误
            "availability_cascade",  # 可得性级联
            "attentional_bias",  # 注意力偏误
        ]
    )


@dataclass
class System2Profile:
    """System 2 分析推理特征配置"""

    response_time_threshold: float = 3.0  # 响应时间阈值(秒)
    analytical_depth: int = 3  # 分析深度
    logical_rigor: float = 0.9  # 逻辑严格性
    evidence_threshold: float = 0.7  # 证据阈值
    verification_steps: int = 2  # 验证步骤数
    deliberation_weight: float = 0.8  # 审慎权重
    formal_reasoning: bool = True  # 形式推理启用


@dataclass
class DualSystemInteraction:
    """双系统交互配置"""

    arbitration_strategy: str = "confidence_based"  # 仲裁策略
    system1_priority_threshold: float = 0.6  # System1优先阈值
    system2_override_threshold: float = 0.8  # System2覆盖阈值
    consensus_threshold: float = 0.7  # 共识阈值
    conflict_resolution: str = "system2_wins"  # 冲突解决策略
    learning_enabled: bool = True  # 学习启用


class System1Reasoner(BaseReasoner):
    """System 1 快速直觉推理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.profile = System1Profile(**config.get("system1_profile", {}))
        self.patterns: dict[str, list[dict[str, Any]]] = {}
        self.heuristics_cache: dict[str, Any] = {}

    def _get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.SYSTEM1_INTUITIVE

    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """System 1 快速推理"""
        start_time = time.time()
        reasoning_chain = ReasoningChain(reasoning_type=ReasoningType.SYSTEM1_INTUITIVE)

        # 第1步:快速模式匹配
        pattern_match_step = await self._pattern_matching(context)
        reasoning_chain.add_step(pattern_match_step)

        # 第2步:启发式推理
        heuristic_step = await self._heuristic_reasoning(context, pattern_match_step.output_state)
        reasoning_chain.add_step(heuristic_step)

        # 第3步:直觉判断
        intuition_step = await self._intuitive_judgment(context, heuristic_step.output_state)
        reasoning_chain.add_step(intuition_step)

        # 计算执行时间
        execution_time = time.time() - start_time
        reasoning_chain.total_time = execution_time
        reasoning_chain.completed_at = time.time()

        # 创建推理结果
        result = ReasoningResult(
            conclusion=intuition_step.output_state.get("conclusion", ""),
            reasoning_chain=reasoning_chain,
            confidence=intuition_step.confidence,
            reasoning_type=ReasoningType.SYSTEM1_INTUITIVE,
            performance_metrics={
                "execution_time": execution_time,
                "steps_count": len(reasoning_chain.steps),
                "system_type": "system1",
                "response_time": execution_time,
            },
        )

        # 添加支持证据
        for step in reasoning_chain.steps:
            for evidence in step.evidence:
                result.add_supporting_evidence(evidence)

        return result

    async def _pattern_matching(self, context: ReasoningContext) -> ReasoningStep:
        """快速模式匹配"""
        start_time = time.time()
        input_text = str(context.input_data.get("query", ""))

        # 使用简单的关键词模式匹配
        matched_patterns = []
        pattern_confidence = 0.0

        # 检查常见模式
        common_patterns = {
            "question_pattern": ["?", "什么", "为什么", "如何", "怎么", "what", "why", "how"],
            "problem_pattern": ["问题", "困难", "挑战", "problem", "issue", "challenge"],
            "decision_pattern": ["选择", "决定", "还是", "whether", "choose", "decide"],
            "comparison_pattern": ["比较", "对比", "difference", "compare", "versus", "vs"],
        }

        for pattern_name, keywords in common_patterns.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in input_text.lower())
            if matches > 0:
                matched_patterns.append((pattern_name, matches))
                pattern_confidence += matches * self.profile.pattern_matching_weight

        # 标准化置信度
        pattern_confidence = (
            min(pattern_confidence / len(keywords), 1.0) if matched_patterns else 0.1
        )

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.SYSTEM1_INTUITIVE,
            operation="pattern_matching",
            input_state={"input_text": input_text},
            output_state={
                "matched_patterns": matched_patterns,
                "pattern_type": matched_patterns[0][0] if matched_patterns else "unknown",
                "confidence": pattern_confidence,
            },
            confidence=pattern_confidence,
            computation_time=computation_time,
            justification=f"基于关键词快速匹配,找到 {len(matched_patterns)} 个模式",
        )

    async def _heuristic_reasoning(
        self, context: ReasoningContext, previous_output: dict[str, Any]
    ) -> ReasoningStep:
        """启发式推理"""
        start_time = time.time()

        # 可得性启发式:基于记忆中容易获得的信息
        availability_score = self._availability_heuristic(context)

        # 代表性启发式:基于相似性判断
        representativeness_score = self._representativeness_heuristic(context)

        # 锚定启发式:基于初始锚定值
        anchoring_score = self._anchoring_heuristic(context)

        # 综合启发式评分
        heuristic_score = (availability_score + representativeness_score + anchoring_score) / 3

        # 添加认知偏误影响
        heuristic_score += self.profile.confidence_bias
        heuristic_score = min(max(heuristic_score, 0.0), 1.0)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.SYSTEM1_INTUITIVE,
            operation="heuristic_reasoning",
            input_state=previous_output,
            output_state={
                "heuristic_score": heuristic_score,
                "availability_score": availability_score,
                "representativeness_score": representativeness_score,
                "anchoring_score": anchoring_score,
                "dominant_heuristic": self._get_dominant_heuristic(
                    availability_score, representativeness_score, anchoring_score
                ),
            },
            confidence=heuristic_score,
            computation_time=computation_time,
            justification=f"使用启发式推理,综合评分为 {heuristic_score:.2f}",
        )

    async def _intuitive_judgment(
        self, context: ReasoningContext, previous_output: dict[str, Any]
    ) -> ReasoningStep:
        """直觉判断"""
        start_time = time.time()

        heuristic_score = previous_output.get("heuristic_score", 0.5)
        pattern_type = previous_output.get("pattern_type", "unknown")

        # 基于模式类型和启发式评分生成直觉判断
        intuition_templates = {
            "question_pattern": self._generate_question_intuition(context, heuristic_score),
            "problem_pattern": self._generate_problem_intuition(context, heuristic_score),
            "decision_pattern": self._generate_decision_intuition(context, heuristic_score),
            "comparison_pattern": self._generate_comparison_intuition(context, heuristic_score),
            "unknown": self._generate_general_intuition(context, heuristic_score),
        }

        conclusion, confidence = intuition_templates.get(
            pattern_type, intuition_templates["unknown"]
        )

        # 添加情感影响
        emotional_adjustment = self._calculate_emotional_influence(context)
        confidence += emotional_adjustment * self.profile.emotional_influence
        confidence = min(max(confidence, 0.0), 1.0)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.SYSTEM1_INTUITIVE,
            operation="intuitive_judgment",
            input_state=previous_output,
            output_state={
                "conclusion": conclusion,
                "confidence": confidence,
                "emotional_adjustment": emotional_adjustment,
                "intuition_type": pattern_type,
            },
            confidence=confidence,
            computation_time=computation_time,
            justification=f"基于 {pattern_type} 的直觉判断,考虑了情感因素",
        )

    def _availability_heuristic(self, context: ReasoningContext) -> float:
        """可得性启发式:基于工作记忆中容易获得的信息"""
        if not context.working_memory:
            return 0.5

        # 模拟可得性评分
        working_memory_size = len(context.working_memory)
        availability_score = min(working_memory_size / 5.0, 1.0)  # 归一化到[0,1]

        return availability_score

    def _representativeness_heuristic(self, context: ReasoningContext) -> float:
        """代表性启发式:基于相似性判断"""
        # 简化的代表性启发式实现
        domain_familiarity = 0.7 if context.domain in self.patterns else 0.4
        complexity_penalty = max(0, 1.0 - context.complexity.value * 0.1)

        return domain_familiarity * complexity_penalty

    def _anchoring_heuristic(self, context: ReasoningContext) -> float:
        """锚定启发式:基于初始锚定值"""
        # 使用背景知识作为锚定
        background_size = len(context.background_knowledge)
        anchor_strength = min(background_size / 10.0, 1.0)

        return anchor_strength * 0.8 + 0.2  # 添加基础锚定

    def _get_dominant_heuristic(
        self, availability: float, representativeness: float, anchoring: float
    ) -> str:
        """获取主导启发式"""
        heuristics = {
            "availability": availability,
            "representativeness": representativeness,
            "anchoring": anchoring,
        }
        return max(heuristics, key=heuristics.get)

    def _calculate_emotional_influence(self, context: ReasoningContext) -> float:
        """计算情感影响"""
        # 简化的情感影响计算
        emotional_keywords = [
            "重要",
            "紧急",
            "危险",
            "安全",
            "喜欢",
            "讨厌",
            "important",
            "urgent",
            "dangerous",
        ]
        input_text = str(context.input_data.get("query", "")).lower()

        emotion_count = sum(1 for keyword in emotional_keywords if keyword in input_text)
        return (emotion_count * 0.1) - 0.05  # 归一化到小范围

    def _generate_question_intuition(
        self, context: ReasoningContext, score: float
    ) -> tuple[str, float]:
        """生成问题相关的直觉判断"""
        if score > 0.7:
            return "这是一个需要深入思考的问题,应该仔细分析", score
        elif score > 0.4:
            return "这是一个常规问题,可以基于常识回答", score
        else:
            return "这个问题需要更多信息才能准确回答", score

    def _generate_problem_intuition(
        self, context: ReasoningContext, score: float
    ) -> tuple[str, float]:
        """生成问题相关的直觉判断"""
        if score > 0.7:
            return "这是一个复杂问题,需要系统性分析", score
        elif score > 0.4:
            return "这个问题有标准解决方案", score
        else:
            return "这个问题比较简单,可以快速处理", score

    def _generate_decision_intuition(
        self, context: ReasoningContext, score: float
    ) -> tuple[str, float]:
        """生成决策相关的直觉判断"""
        if score > 0.7:
            return "这是一个重要决策,需要慎重考虑", score
        elif score > 0.4:
            return "这是一个常规决策,可以基于经验判断", score
        else:
            return "这是一个简单决策,可以快速决定", score

    def _generate_comparison_intuition(
        self, context: ReasoningContext, score: float
    ) -> tuple[str, float]:
        """生成比较相关的直觉判断"""
        if score > 0.7:
            return "两者有显著差异,需要详细分析", score
        elif score > 0.4:
            return "两者有一定差异,但各有优势", score
        else:
            return "两者基本相似,选择影响不大", score

    def _generate_general_intuition(
        self, context: ReasoningContext, score: float
    ) -> tuple[str, float]:
        """生成一般直觉判断"""
        if score > 0.7:
            return "基于直觉,这个情况值得深入分析", score
        elif score > 0.4:
            return "基于直觉,这个情况比较正常", score
        else:
            return "基于直觉,这个情况需要更多信息", score


class System2Reasoner(BaseReasoner):
    """System 2 慢速分析推理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.profile = System2Profile(**config.get("system2_profile", {}))
        self.logical_rules: dict[str, Callable] = {}
        self.verification_methods: list[str] = [
            "consistency_check",
            "logical_validation",
            "evidence_evaluation",
        ]

    def _get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.SYSTEM2_ANALYTICAL

    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """System 2 深度分析推理"""
        start_time = time.time()
        reasoning_chain = ReasoningChain(reasoning_type=ReasoningType.SYSTEM2_ANALYTICAL)

        # 第1步:问题分析
        analysis_step = await self._analyze_problem(context)
        reasoning_chain.add_step(analysis_step)

        # 第2步:逻辑推理
        logic_step = await self._logical_reasoning(context, analysis_step.output_state)
        reasoning_chain.add_step(logic_step)

        # 第3步:证据评估
        evidence_step = await self._evaluate_evidence(context, logic_step.output_state)
        reasoning_chain.add_step(evidence_step)

        # 第4步:多重验证
        verification_step = await self._verify_conclusion(context, evidence_step.output_state)
        reasoning_chain.add_step(verification_step)

        # 第5步:元认知反思
        reflection_step = await self._metacognitive_reflection(context, reasoning_chain)
        reasoning_chain.add_step(reflection_step)

        # 计算执行时间
        execution_time = time.time() - start_time
        reasoning_chain.total_time = execution_time
        reasoning_chain.completed_at = time.time()

        # 创建推理结果
        result = ReasoningResult(
            conclusion=reflection_step.output_state.get("final_conclusion", ""),
            reasoning_chain=reasoning_chain,
            confidence=reflection_step.confidence,
            reasoning_type=ReasoningType.SYSTEM2_ANALYTICAL,
            performance_metrics={
                "execution_time": execution_time,
                "steps_count": len(reasoning_chain.steps),
                "system_type": "system2",
                "logical_rigor": self.profile.logical_rigor,
                "verification_count": self.profile.verification_steps,
            },
        )

        # 添加支持证据和备选结论
        for step in reasoning_chain.steps:
            for evidence in step.evidence:
                result.add_supporting_evidence(evidence)

        # 添加备选结论
        alternative_conclusions = self._generate_alternatives(context, reasoning_chain)
        for alt_conclusion, alt_confidence in alternative_conclusions:
            result.add_alternative_conclusion(alt_conclusion, alt_confidence)

        return result

    async def _analyze_problem(self, context: ReasoningContext) -> ReasoningStep:
        """深度问题分析"""
        start_time = time.time()

        # 分析问题结构
        query = str(context.input_data.get("query", ""))

        # 识别问题类型
        problem_type = self._identify_problem_type(query)

        # 分析复杂度
        complexity_assessment = self._assess_complexity(query, context)

        # 识别关键要素
        key_elements = self._extract_key_elements(query)

        # 分析约束条件
        constraint_analysis = self._analyze_constraints(context.constraints)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.SYSTEM2_ANALYTICAL,
            operation="problem_analysis",
            input_state={"query": query},
            output_state={
                "problem_type": problem_type,
                "complexity_assessment": complexity_assessment,
                "key_elements": key_elements,
                "constraint_analysis": constraint_analysis,
                "analysis_confidence": 0.8,
            },
            confidence=0.8,
            computation_time=computation_time,
            justification="系统性分析问题结构、类型、复杂度和关键要素",
        )

    async def _logical_reasoning(
        self, context: ReasoningContext, previous_output: dict[str, Any]
    ) -> ReasoningStep:
        """逻辑推理"""
        start_time = time.time()

        problem_type = previous_output.get("problem_type", "unknown")
        key_elements = previous_output.get("key_elements", [])

        # 根据问题类型选择逻辑推理方法
        if problem_type == "deductive":
            logical_result = self._deductive_reasoning(context, key_elements)
        elif problem_type == "inductive":
            logical_result = self._inductive_reasoning(context, key_elements)
        elif problem_type == "causal":
            logical_result = self._causal_reasoning(context, key_elements)
        else:
            logical_result = self._general_reasoning(context, key_elements)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.SYSTEM2_ANALYTICAL,
            operation="logical_reasoning",
            input_state=previous_output,
            output_state={
                "logical_conclusion": logical_result.get("conclusion"),
                "logical_steps": logical_result.get("steps"),
                "logical_confidence": logical_result.get("confidence"),
                "reasoning_method": logical_result.get("method"),
            },
            confidence=logical_result.get("confidence"),
            computation_time=computation_time,
            justification=f"使用 {logical_result.get('method')} 进行逻辑推理",
        )

    async def _evaluate_evidence(
        self, context: ReasoningContext, previous_output: dict[str, Any]
    ) -> ReasoningStep:
        """证据评估"""
        start_time = time.time()

        logical_conclusion = previous_output.get("logical_conclusion", "")

        # 收集证据
        evidence_sources = [
            ("background_knowledge", context.background_knowledge),
            ("working_memory", context.working_memory),
            ("input_data", context.input_data),
        ]

        evaluated_evidence = []
        total_evidence_strength = 0.0

        for source_name, source_data in evidence_sources:
            evidence_strength = self._evaluate_evidence_strength(source_data, logical_conclusion)
            evaluated_evidence.append(
                {
                    "source": source_name,
                    "strength": evidence_strength,
                    "relevance": self._calculate_relevance(source_data, logical_conclusion),
                }
            )
            total_evidence_strength += evidence_strength

        # 计算整体证据支持度
        overall_evidence_support = (
            total_evidence_strength / len(evidence_sources) if evidence_sources else 0.0
        )

        # 应用证据阈值
        evidence_confidence = (
            overall_evidence_support
            if overall_evidence_support >= self.profile.evidence_threshold
            else 0.3
        )

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.SYSTEM2_ANALYTICAL,
            operation="evidence_evaluation",
            input_state=previous_output,
            output_state={
                "evaluated_evidence": evaluated_evidence,
                "overall_evidence_support": overall_evidence_support,
                "evidence_confidence": evidence_confidence,
                "evidence_threshold_met": overall_evidence_support
                >= self.profile.evidence_threshold,
            },
            confidence=evidence_confidence,
            computation_time=computation_time,
            justification=f"评估了 {len(evidence_sources)} 个证据源,整体支持度为 {overall_evidence_support:.2f}",
        )

    async def _verify_conclusion(
        self, context: ReasoningContext, previous_output: dict[str, Any]
    ) -> ReasoningStep:
        """结论验证"""
        start_time = time.time()

        logical_conclusion = previous_output.get("logical_conclusion", "")
        evidence_confidence = previous_output.get("evidence_confidence", 0.0)

        verification_results = []
        total_verification_score = 0.0

        # 执行多种验证方法
        for method in self.verification_methods[: self.profile.verification_steps]:
            verification_score = self._perform_verification(method, logical_conclusion, context)
            verification_results.append(
                {"method": method, "score": verification_score, "passed": verification_score >= 0.6}
            )
            total_verification_score += verification_score

        # 计算平均验证分数
        average_verification_score = total_verification_score / len(verification_results)

        # 调整置信度
        verified_confidence = evidence_confidence * average_verification_score

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.SYSTEM2_ANALYTICAL,
            operation="conclusion_verification",
            input_state=previous_output,
            output_state={
                "verification_results": verification_results,
                "average_verification_score": average_verification_score,
                "verified_confidence": verified_confidence,
                "all_verifications_passed": all(r["passed"] for r in verification_results),
            },
            confidence=verified_confidence,
            computation_time=computation_time,
            justification=f"执行了 {len(verification_results)} 种验证方法,平均分数 {average_verification_score:.2f}",
        )

    async def _metacognitive_reflection(
        self, context: ReasoningContext, reasoning_chain: ReasoningChain
    ) -> ReasoningStep:
        """元认知反思"""
        start_time = time.time()

        # 分析推理链质量
        chain_quality = self._analyze_reasoning_chain_quality(reasoning_chain)

        # 检查认知一致性
        consistency_score = self._check_cognitive_consistency(reasoning_chain)

        # 评估推理充分性
        sufficiency_score = self._assess_reasoning_sufficiency(context, reasoning_chain)

        # 反思性调整
        reflection_adjustment = self._calculate_reflection_adjustment(
            chain_quality, consistency_score, sufficiency_score
        )

        # 生成最终结论
        last_step = reasoning_chain.steps[-1] if reasoning_chain.steps else None
        base_conclusion = last_step.output_state.get("logical_conclusion", "") if last_step else ""
        final_conclusion = self._refine_conclusion(base_conclusion, reflection_adjustment)

        # 计算最终置信度
        base_confidence = last_step.confidence if last_step else 0.5
        final_confidence = base_confidence * reflection_adjustment
        final_confidence = min(max(final_confidence, 0.0), 1.0)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.SYSTEM2_ANALYTICAL,
            operation="metacognitive_reflection",
            input_state={"reasoning_chain": reasoning_chain},
            output_state={
                "final_conclusion": final_conclusion,
                "final_confidence": final_confidence,
                "chain_quality": chain_quality,
                "consistency_score": consistency_score,
                "sufficiency_score": sufficiency_score,
                "reflection_adjustment": reflection_adjustment,
            },
            confidence=final_confidence,
            computation_time=computation_time,
            justification="通过元认知反思调整和优化推理结论",
        )

    # 辅助方法实现
    def _identify_problem_type(self, query: str) -> str:
        """识别问题类型"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["如果", "假如", "那么", "if", "then", "therefore"]):
            return "deductive"
        elif any(
            word in query_lower for word in ["模式", "规律", "pattern", "trend", "regularity"]
        ):
            return "inductive"
        elif any(
            word in query_lower for word in ["原因", "为什么", "导致", "cause", "why", "lead to"]
        ):
            return "causal"
        else:
            return "general"

    def _assess_complexity(self, query: str, context: ReasoningContext) -> dict[str, Any]:
        """评估复杂度"""
        return {
            "lexical_complexity": len(query.split()),
            "structural_complexity": len(context.constraints),
            "knowledge_complexity": len(context.background_knowledge),
            "overall_complexity": context.complexity.value,
        }

    def _extract_key_elements(self, query: str) -> list[str]:
        """提取关键要素"""
        # 简化的关键要素提取
        words = query.split()
        # 过滤停用词并提取关键词
        key_words = [word for word in words if len(word) > 3 and word.isalpha()]
        return key_words[:10]  # 限制数量

    def _analyze_constraints(self, constraints: list[str]) -> dict[str, Any]:
        """分析约束条件"""
        return {
            "constraint_count": len(constraints),
            "constraint_types": ["temporal", "logical", "resource"] if constraints else [],
            "constraint_stringency": min(len(constraints) / 5.0, 1.0),
        }

    def _deductive_reasoning(
        self, context: ReasoningContext, elements: list[str]
    ) -> dict[str, Any]:
        """演绎推理"""
        return {
            "conclusion": f"基于元素 {', '.join(elements[:3])} 的演绎推理结论",
            "steps": ["前提分析", "逻辑推导", "结论验证"],
            "confidence": 0.85,
            "method": "deductive",
        }

    def _inductive_reasoning(
        self, context: ReasoningContext, elements: list[str]
    ) -> dict[str, Any]:
        """归纳推理"""
        return {
            "conclusion": f"基于元素 {', '.join(elements[:3])} 的归纳推理结论",
            "steps": ["案例收集", "模式识别", "一般化"],
            "confidence": 0.75,
            "method": "inductive",
        }

    def _causal_reasoning(self, context: ReasoningContext, elements: list[str]) -> dict[str, Any]:
        """因果推理"""
        return {
            "conclusion": f"基于元素 {', '.join(elements[:3])} 的因果推理结论",
            "steps": ["因果识别", "关系验证", "因果推断"],
            "confidence": 0.80,
            "method": "causal",
        }

    def _general_reasoning(self, context: ReasoningContext, elements: list[str]) -> dict[str, Any]:
        """一般推理"""
        return {
            "conclusion": f"基于元素 {', '.join(elements[:3])} 的一般推理结论",
            "steps": ["信息整合", "逻辑分析", "结论形成"],
            "confidence": 0.70,
            "method": "general",
        }

    def _evaluate_evidence_strength(self, evidence_data: Any, conclusion: str) -> float:
        """评估证据强度"""
        if not evidence_data:
            return 0.0

        # 简化的证据强度评估
        evidence_size = len(str(evidence_data))
        relevance_score = 0.5  # 简化的相关性评分

        return min(evidence_size / 100.0, 1.0) * relevance_score

    def _calculate_relevance(self, evidence_data: Any, conclusion: str) -> float:
        """计算相关性"""
        # 简化的相关性计算
        conclusion_words = set(conclusion.lower().split())
        evidence_words = set(str(evidence_data).lower().split())

        if not conclusion_words:
            return 0.0

        intersection = conclusion_words.intersection(evidence_words)
        return len(intersection) / len(conclusion_words)

    def _perform_verification(
        self, method: str, conclusion: str, context: ReasoningContext
    ) -> float:
        """执行验证方法"""
        # 简化的验证实现
        verification_scores = {
            "consistency_check": 0.8,
            "logical_validation": 0.85,
            "evidence_evaluation": 0.75,
        }
        return verification_scores.get(method, 0.7)

    def _analyze_reasoning_chain_quality(self, chain: ReasoningChain) -> float:
        """分析推理链质量"""
        if not chain.steps:
            return 0.0

        # 基于步骤数量和平均置信度计算质量
        avg_confidence = sum(step.confidence for step in chain.steps) / len(chain.steps)
        depth_factor = min(len(chain.steps) / 5.0, 1.0)

        return avg_confidence * depth_factor

    def _check_cognitive_consistency(self, chain: ReasoningChain) -> float:
        """检查认知一致性"""
        if len(chain.steps) < 2:
            return 1.0

        # 简化的一致性检查
        confidences = [step.confidence for step in chain.steps]
        variance = np.var(confidences) if confidences else 0

        # 方差越小,一致性越高
        consistency = 1.0 - min(variance, 1.0)
        return consistency

    def _assess_reasoning_sufficiency(
        self, context: ReasoningContext, chain: ReasoningChain
    ) -> float:
        """评估推理充分性"""
        # 基于推理步骤数量和复杂度评估充分性
        step_count = len(chain.steps)
        complexity_factor = context.complexity.value

        required_steps = {
            1: 2,  # SIMPLE
            2: 3,  # MODERATE
            3: 4,  # COMPLEX
            4: 5,  # VERY_COMPLEX
            5: 6,  # EXPERT
        }.get(complexity_factor, 3)

        sufficiency = min(step_count / required_steps, 1.0)
        return sufficiency

    def _calculate_reflection_adjustment(
        self, quality: float, consistency: float, sufficiency: float
    ) -> float:
        """计算反思调整因子"""
        # 综合质量、一致性和充分性
        adjustment = (quality + consistency + sufficiency) / 3.0
        return adjustment

    def _refine_conclusion(self, base_conclusion: str, adjustment: float) -> str:
        """优化结论"""
        if adjustment > 0.8:
            return f"[高置信度] {base_conclusion}"
        elif adjustment > 0.6:
            return f"[中等置信度] {base_conclusion}"
        elif adjustment > 0.4:
            return f"[需要验证] {base_conclusion}"
        else:
            return f"[不确定性高] {base_conclusion}"

    def _generate_alternatives(
        self, context: ReasoningContext, chain: ReasoningChain
    ) -> list[tuple[str, float]]:
        """生成备选结论"""
        # 简化的备选结论生成
        alternatives = [
            ("需要更多信息来确定结论", 0.3),
            ("可能存在其他解释", 0.4),
            ("结论可能依赖于特定假设", 0.5),
        ]
        return alternatives[:2]  # 返回前2个备选


class DualSystemReasoner(BaseReasoner):
    """双系统协同推理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.system1 = System1Reasoner(config)
        self.system2 = System2Reasoner(config)
        self.interaction = DualSystemInteraction(**config.get("interaction", {}))
        self.coordination_history: list[dict[str, Any]] = []

    def _get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.DUAL_PROCESS

    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """双系统协同推理"""
        start_time = time.time()

        # 并行执行双系统推理
        system1_task = self.system1.reason(context)
        system2_task = self.system2.reason(context)

        # 等待两个系统完成
        system1_result, system2_result = await asyncio.gather(system1_task, system2_task)

        # 协调和整合结果
        final_result = await self._coordinate_systems(system1_result, system2_result, context)

        # 记录协调历史
        coordination_record = {
            "timestamp": time.time(),
            "system1_confidence": system1_result.confidence,
            "system2_confidence": system2_result.confidence,
            "final_confidence": final_result.confidence,
            "coordination_strategy": self.interaction.arbitration_strategy,
            "execution_time": time.time() - start_time,
        }
        self.coordination_history.append(coordination_record)

        return final_result

    async def _coordinate_systems(
        self,
        system1_result: ReasoningResult,
        system2_result: ReasoningResult,
        context: ReasoningContext,
    ) -> ReasoningResult:
        """协调双系统结果"""

        # 根据仲裁策略选择结果
        if self.interaction.arbitration_strategy == "confidence_based":
            return self._confidence_based_arbitration(system1_result, system2_result)
        elif self.interaction.arbitration_strategy == "system2_priority":
            return self._system2_priority_arbitration(system1_result, system2_result)
        elif self.interaction.arbitration_strategy == "consensus":
            return self._consensus_arbitration(system1_result, system2_result)
        else:
            return self._hybrid_arbitration(system1_result, system2_result, context)

    def _confidence_based_arbitration(
        self, system1_result: ReasoningResult, system2_result: ReasoningResult
    ) -> ReasoningResult:
        """基于置信度的仲裁"""
        if system1_result.confidence > self.interaction.system1_priority_threshold:
            return system1_result
        elif system2_result.confidence > self.interaction.system2_override_threshold:
            return system2_result
        else:
            # 混合结果
            return self._blend_results(system1_result, system2_result, 0.4)

    def _system2_priority_arbitration(
        self, system1_result: ReasoningResult, system2_result: ReasoningResult
    ) -> ReasoningResult:
        """System 2 优先仲裁"""
        # 总是给予System 2 更高权重,除非System 1 置信度极高
        if system1_result.confidence > 0.9:
            return system1_result
        else:
            return self._blend_results(system1_result, system2_result, 0.7)

    def _consensus_arbitration(
        self, system1_result: ReasoningResult, system2_result: ReasoningResult
    ) -> ReasoningResult:
        """共识仲裁"""
        # 检查结论是否相似
        similarity = self._calculate_conclusion_similarity(
            system1_result.conclusion, system2_result.conclusion
        )

        if similarity > self.interaction.consensus_threshold:
            # 结论相似,使用高置信度结果
            return (
                system1_result
                if system1_result.confidence > system2_result.confidence
                else system2_result
            )
        else:
            # 结论不同,标记为需要人工决策
            blended_result = self._blend_results(system1_result, system2_result, 0.5)
            blended_result.metadata["requires_human_decision"] = True
            blended_result.metadata["conclusion_conflict"] = True
            return blended_result

    def _hybrid_arbitration(
        self,
        system1_result: ReasoningResult,
        system2_result: ReasoningResult,
        context: ReasoningContext,
    ) -> ReasoningResult:
        """混合仲裁策略"""
        # 根据任务复杂度和时间限制动态调整权重
        complexity_weight = context.complexity.value / 5.0
        time_pressure = 1.0 if (context.time_limit and context.time_limit < 2.0) else 0.0

        # 计算System 1 权重
        system1_weight = (0.3 * time_pressure) + (0.2 * (1 - complexity_weight))
        system2_weight = 1.0 - system1_weight

        return self._blend_results(system1_result, system2_result, system2_weight)

    def _blend_results(
        self,
        system1_result: ReasoningResult,
        system2_result: ReasoningResult,
        system2_weight: float,
    ) -> ReasoningResult:
        """混合两个系统的结果"""
        system1_weight = 1.0 - system2_weight

        # 创建混合推理链
        blended_chain = ReasoningChain(
            reasoning_type=ReasoningType.DUAL_PROCESS,
            steps=system1_result.reasoning_chain.steps + system2_result.reasoning_chain.steps,
        )

        # 混合结论
        if system1_weight > system2_weight:
            primary_conclusion = system1_result.conclusion
        else:
            primary_conclusion = system2_result.conclusion

        blended_conclusion = f"[双系统综合] {primary_conclusion}"

        # 计算混合置信度
        blended_confidence = (
            system1_result.confidence * system1_weight + system2_result.confidence * system2_weight
        )

        # 混合支持证据
        blended_evidence = system1_result.supporting_evidence + system2_result.supporting_evidence

        # 混合性能指标
        blended_metrics = {
            "system1_confidence": system1_result.confidence,
            "system2_confidence": system2_result.confidence,
            "system1_time": system1_result.performance_metrics.get("execution_time", 0),
            "system2_time": system2_result.performance_metrics.get("execution_time", 0),
            "blending_weight_system2": system2_weight,
            "total_steps": len(blended_chain.steps),
        }

        return ReasoningResult(
            result_id=str(uuid.uuid4()),
            conclusion=blended_conclusion,
            reasoning_chain=blended_chain,
            confidence=blended_confidence,
            supporting_evidence=blended_evidence,
            reasoning_type=ReasoningType.DUAL_PROCESS,
            performance_metrics=blended_metrics,
            metadata={
                "system1_weight": system1_weight,
                "system2_weight": system2_weight,
                "primary_system": "system1" if system1_weight > system2_weight else "system2",
            },
        )

    def _calculate_conclusion_similarity(self, conclusion1: str, conclusion2: str) -> float:
        """计算结论相似度"""
        if not conclusion1 or not conclusion2:
            return 0.0

        # 简化的相似度计算(基于词汇重叠)
        words1 = set(conclusion1.lower().split())
        words2 = set(conclusion2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def get_coordination_statistics(self) -> dict[str, Any]:
        """获取协调统计信息"""
        if not self.coordination_history:
            return {}

        recent_records = self.coordination_history[-100:]  # 最近100次

        avg_s1_conf = sum(r["system1_confidence"] for r in recent_records) / len(recent_records)
        avg_s2_conf = sum(r["system2_confidence"] for r in recent_records) / len(recent_records)
        avg_final_conf = sum(r["final_confidence"] for r in recent_records) / len(recent_records)
        avg_time = sum(r["execution_time"] for r in recent_records) / len(recent_records)

        return {
            "total_coordinations": len(self.coordination_history),
            "average_system1_confidence": avg_s1_conf,
            "average_system2_confidence": avg_s2_conf,
            "average_final_confidence": avg_final_conf,
            "average_execution_time": avg_time,
            "coordination_strategy": self.interaction.arbitration_strategy,
        }


# 导出的主要接口
__all__ = [
    "DualSystemInteraction",
    "DualSystemReasoner",
    "System1Profile",
    "System1Reasoner",
    "System2Profile",
    "System2Reasoner",
]
