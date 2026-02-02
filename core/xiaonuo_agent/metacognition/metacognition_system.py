#!/usr/bin/env python3
"""
元认知系统 (Metacognition System)
关于认知的认知,实现自我监控、评估和调节

核心思想:
1. 自我监控:监控自身认知过程
2. 自我评估:评估自身能力和表现
3. 自我调节:调节认知策略
4. 元推理:关于推理的推理
5. 自我反思:反思过去的决策

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MetacognitiveProcess(Enum):
    """元认知过程类型"""

    MONITORING = "monitoring"  # 监控
    EVALUATING = "evaluating"  # 评估
    REGULATING = "regulating"  # 调节
    PLANNING = "planning"  # 计划
    REFLECTING = "reflecting"  # 反思


class ConfidenceLevel(Enum):
    """置信度等级"""

    VERY_LOW = "very_low"  # 非常低 (0.0-0.2)
    LOW = "low"  # 低 (0.2-0.4)
    MEDIUM = "medium"  # 中 (0.4-0.6)
    HIGH = "high"  # 高 (0.6-0.8)
    VERY_HIGH = "very_high"  # 非常高 (0.8-1.0)


@dataclass
class CognitiveState:
    """认知状态"""

    task_understanding: float  # 任务理解度 (0-1)
    solution_confidence: float  # 解决方案置信度 (0-1)
    resource_availability: float  # 资源可用性 (0-1)
    difficulty_estimate: float  # 难度估计 (0-1)
    progress_estimate: float  # 进度估计 (0-1)

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_understanding": round(self.task_understanding, 3),
            "solution_confidence": round(self.solution_confidence, 3),
            "resource_availability": round(self.resource_availability, 3),
            "difficulty_estimate": round(self.difficulty_estimate, 3),
            "progress_estimate": round(self.progress_estimate, 3),
            "timestamp": self.timestamp,
        }


@dataclass
class MetacognitiveJudgment:
    """元认知判断"""

    judgment_id: str
    process_type: MetacognitiveProcess
    target: str  # 判断目标(任务、推理、记忆等)
    judgment: str  # 判断内容
    confidence: float  # 判断置信度 (0-1)
    evidence: list[str]  # 支持证据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "judgment_id": self.judgment_id,
            "process_type": self.process_type.value,
            "target": self.target,
            "judgment": self.judgment,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }


@dataclass
class ReflectionEntry:
    """反思条目"""

    entry_id: str
    reflection_type: str  # 反思类型
    subject: str  # 反思主题
    content: str  # 反思内容
    lessons_learned: list[str]  # 学到的教训
    action_items: list[str]  # 行动项
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "entry_id": self.entry_id,
            "reflection_type": self.reflection_type,
            "subject": self.subject,
            "content": self.content,
            "lessons_learned": self.lessons_learned,
            "action_items": self.action_items,
            "timestamp": self.timestamp,
        }


@dataclass
class SelfAssessment:
    """自我评估"""

    assessment_id: str
    domain: str  # 评估领域(推理、记忆、学习等)
    score: float  # 自评分数 (0-1)
    strengths: list[str]  # 优势
    weaknesses: list[str]  # 劣势
    improvement_suggestions: list[str]  # 改进建议
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "assessment_id": self.assessment_id,
            "domain": self.domain,
            "score": round(self.score, 3),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "improvement_suggestions": self.improvement_suggestions,
            "timestamp": self.timestamp,
        }


class MetacognitionSystem:
    """
    元认知系统 - 关于认知的认知

    核心功能:
    1. 自我监控:实时监控认知过程
    2. 自我评估:评估自身能力和表现
    3. 自我调节:动态调节认知策略
    4. 元推理:对推理过程进行推理
    5. 自我反思:反思过去的决策和行动

    元认知层次:
    - 元认知知识:关于自己认知的知识
    - 元认知体验:在认知过程中的感受
    - 元认知监控:对认知过程的监控
    - 元认知调节:对认知过程的调节
    """

    def __init__(self):
        """初始化元认知系统"""
        # 当前认知状态
        self.current_state = CognitiveState(
            task_understanding=0.5,
            solution_confidence=0.5,
            resource_availability=1.0,
            difficulty_estimate=0.5,
            progress_estimate=0.0,
        )

        # 元认知判断历史
        self.judgments: list[MetacognitiveJudgment] = []

        # 反思日志
        self.reflections: list[ReflectionEntry] = []

        # 自我评估记录
        self.assessments: list[SelfAssessment] = []

        # 认知能力档案
        self.capability_profile = {
            "reasoning": 0.7,
            "memory": 0.8,
            "learning": 0.6,
            "planning": 0.7,
            "creativity": 0.5,
        }

        # 统计信息
        self.stats = {
            "total_judgments": 0,
            "total_reflections": 0,
            "total_assessments": 0,
            "average_confidence": 0.0,
            "self_awareness_score": 0.5,
        }

    async def monitor_cognitive_process(
        self, task: str, context: dict[str, Any] | None = None
    ) -> CognitiveState:
        """
        监控认知过程

        Args:
            task: 当前任务
            context: 上下文信息

        Returns:
            当前认知状态
        """
        context = context or {}

        # 更新认知状态
        # 1. 评估任务理解度
        self.current_state.task_understanding = await self._assess_understanding(task, context)

        # 2. 评估解决方案置信度
        self.current_state.solution_confidence = await self._assess_confidence(task, context)

        # 3. 评估资源可用性
        self.current_state.resource_availability = await self._assess_resources(context)

        # 4. 估计难度
        self.current_state.difficulty_estimate = await self._estimate_difficulty(task, context)

        # 5. 更新进度
        self.current_state.progress_estimate = context.get("progress", 0.0)

        self.current_state.timestamp = datetime.now().isoformat()

        # 生成监控判断
        await self._make_judgment(
            process_type=MetacognitiveProcess.MONITORING,
            target="cognitive_process",
            judgment=f"当前认知状态: 理解度={self.current_state.task_understanding:.2f}, "
            f"置信度={self.current_state.solution_confidence:.2f}",
            confidence=0.8,
            evidence=[f"任务: {task[:50]}..."],
        )

        logger.debug(
            f"👁️  认知监控: 理解={self.current_state.task_understanding:.2f}, "
            f"置信={self.current_state.solution_confidence:.2f}"
        )

        return self.current_state

    async def evaluate_performance(
        self, domain: str, recent_results: list[dict[str, Any]]
    ) -> SelfAssessment:
        """
        评估自身表现

        Args:
            domain: 评估领域
            recent_results: 最近的结果列表

        Returns:
            自我评估
        """
        # 计算成功率
        if recent_results:
            success_count = sum(1 for r in recent_results if r.get("success", False))
            score = success_count / len(recent_results)
        else:
            score = self.capability_profile.get(domain, 0.5)

        # 识别优势和劣势
        strengths = []
        weaknesses = []

        if score > 0.7:
            strengths.append(f"{domain}能力较强,成功率高")
        elif score < 0.4:
            weaknesses.append(f"{domain}能力需要提升")

        # 生成改进建议
        improvement_suggestions = []
        if score < 0.6:
            improvement_suggestions.append(f"加强{domain}方面的训练和练习")
            improvement_suggestions.append(f"分析{domain}失败案例,找出问题根源")

        # 创建评估
        assessment = SelfAssessment(
            assessment_id=f"assess_{domain}_{int(time.time())}",
            domain=domain,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=improvement_suggestions,
        )

        self.assessments.append(assessment)
        self.stats["total_assessments"] += 1

        # 更新能力档案
        self.capability_profile[domain] = (
            self.capability_profile.get(domain, 0.5) * 0.7 + score * 0.3
        )

        logger.info(f"📊 自我评估: {domain} = {score:.2f}")

        return assessment

    async def reflect_on_action(
        self, action: str, result: Any, context: dict[str, Any] | None = None
    ) -> ReflectionEntry:
        """
        对行动进行反思

        Args:
            action: 采取的行动
            result: 行动结果
            context: 上下文

        Returns:
            反思条目
        """
        context = context or {}
        success = result.get("success") if isinstance(result, dict) else True

        # 分析结果
        if success:
            reflection_type = "success_reflection"
            lessons = [f"行动'{action[:30]}...'取得了成功"]
            action_items = ["在类似情况下可重复此行动"]
        else:
            reflection_type = "failure_reflection"
            lessons = [f"行动'{action[:30]}...'未能达到预期"]
            action_items = ["分析失败原因,调整策略"]

        # 添加深度反思
        if isinstance(result, dict):
            if "error" in result:
                lessons.append(f"错误信息: {result['error']}")
            if "duration" in result:
                lessons.append(f"执行时间: {result['duration']:.2f}秒")

        # 创建反思条目
        reflection = ReflectionEntry(
            entry_id=f"reflect_{int(time.time())}",
            reflection_type=reflection_type,
            subject=action[:50],
            content=f"对行动的反思: {action[:100]}...",
            lessons_learned=lessons,
            action_items=action_items,
        )

        self.reflections.append(reflection)
        self.stats["total_reflections"] += 1

        logger.info(f"🤔 自我反思: {reflection_type} - {action[:30]}...")

        return reflection

    async def regulate_strategy(
        self, current_strategy: str, performance_feedback: dict[str, float]
    ) -> str:
        """
        调节认知策略

        Args:
            current_strategy: 当前策略
            performance_feedback: 性能反馈

        Returns:
            调节后的策略
        """
        # 分析性能反馈
        avg_performance = sum(performance_feedback.values()) / len(performance_feedback)

        if avg_performance > 0.7:
            # 性能良好,保持当前策略
            await self._make_judgment(
                process_type=MetacognitiveProcess.REGULATING,
                target="strategy",
                judgment=f"当前策略'{current_strategy}'表现良好,保持不变",
                confidence=0.8,
                evidence=[f"平均性能: {avg_performance:.2f}"],
            )
            return current_strategy

        else:
            # 性能不佳,需要调整策略
            new_strategy = await self._generate_alternative_strategy(
                current_strategy, performance_feedback
            )

            await self._make_judgment(
                process_type=MetacognitiveProcess.REGULATING,
                target="strategy",
                judgment=f"策略调整: '{current_strategy}' -> '{new_strategy}'",
                confidence=0.7,
                evidence=[f"原策略性能: {avg_performance:.2f}", "需要改进"],
            )

            logger.info(f"🎯 策略调节: {current_strategy} -> {new_strategy}")
            return new_strategy

    async def meta_reason(self, reasoning_trace: list[dict[str, Any]]) -> MetacognitiveJudgment:
        """
        元推理:对推理过程进行推理

        Args:
            reasoning_trace: 推理轨迹

        Returns:
            元认知判断
        """
        # 分析推理质量
        reasoning_depth = len(reasoning_trace)
        confidence_values = [r.get("confidence", 0.5) for r in reasoning_trace]
        avg_confidence = (
            sum(confidence_values) / len(confidence_values) if confidence_values else 0.5
        )

        # 评估推理特征
        has_planning = any("plan" in str(r).lower() for r in reasoning_trace)
        has_evidence = any("evidence" in r for r in reasoning_trace)
        has_alternatives = any("alternative" in str(r).lower() for r in reasoning_trace)

        # 生成元推理判断
        judgment = f"推理深度={reasoning_depth}, 平均置信度={avg_confidence:.2f}"

        evidence = []
        if has_planning:
            evidence.append("包含计划步骤")
        if has_evidence:
            evidence.append("有证据支持")
        if has_alternatives:
            evidence.append("考虑了替代方案")

        meta_judgment = await self._make_judgment(
            process_type=MetacognitiveProcess.EVALUATING,
            target="reasoning_process",
            judgment=judgment,
            confidence=avg_confidence,
            evidence=evidence,
        )

        logger.debug(f"🧠 元推理: {judgment}")

        return meta_judgment

    async def _assess_understanding(self, task: str, context: dict[str, Any]) -> float:
        """评估任务理解度"""
        # 简化实现:基于任务复杂度和上下文丰富度
        task_length = len(task)
        context_richness = len(context)

        # 任务越短、上下文越丰富,理解度越高
        understanding = min(1.0, 0.5 + (context_richness * 0.1) - (task_length * 0.001))
        return max(0.0, understanding)

    async def _assess_confidence(self, task: str, context: dict[str, Any]) -> float:
        """评估解决方案置信度"""
        # 基于历史成功率和当前状态
        base_confidence = self.capability_profile.get("reasoning", 0.5)

        # 调整因素
        if context.get("has_evidence"):
            base_confidence += 0.1
        if context.get("has_plan"):
            base_confidence += 0.1

        return min(1.0, max(0.0, base_confidence))

    async def _assess_resources(self, context: dict[str, Any]) -> float:
        """评估资源可用性"""
        # 简化实现
        return context.get("resource_availability", 1.0)

    async def _estimate_difficulty(self, task: str, context: dict[str, Any]) -> float:
        """估计任务难度"""
        # 基于任务长度和关键词
        difficulty_keywords = ["复杂", "困难", "挑战", "分析", "设计"]
        keyword_count = sum(1 for kw in difficulty_keywords if kw in task)

        difficulty = 0.3 + (len(task) * 0.0005) + (keyword_count * 0.1)
        return min(1.0, difficulty)

    async def _make_judgment(
        self,
        process_type: MetacognitiveProcess,
        target: str,
        judgment: str,
        confidence: float,
        evidence: list[str],
    ) -> MetacognitiveJudgment:
        """生成元认知判断"""
        judgment_obj = MetacognitiveJudgment(
            judgment_id=f"judgment_{int(time.time() * 1000)}",
            process_type=process_type,
            target=target,
            judgment=judgment,
            confidence=confidence,
            evidence=evidence,
        )

        self.judgments.append(judgment_obj)
        self.stats["total_judgments"] += 1

        # 更新平均置信度
        total_confidence = sum(j.confidence for j in self.judgments)
        self.stats["average_confidence"] = total_confidence / len(self.judgments)

        return judgment_obj

    async def _generate_alternative_strategy(
        self, current_strategy: str, feedback: dict[str, float]
    ) -> str:
        """生成替代策略"""
        # 简化实现:基于反馈生成新策略
        if "speed" in feedback and feedback["speed"] < 0.5:
            return f"{current_strategy}_optimized"
        elif "accuracy" in feedback and feedback["accuracy"] < 0.5:
            return f"{current_strategy}_careful"
        else:
            return f"{current_strategy}_adaptive"

    async def get_self_awareness_score(self) -> float:
        """获取自我觉察分数"""
        # 基于判断数量、反思深度、评估准确性
        judgment_factor = min(1.0, len(self.judgments) / 100)
        reflection_factor = min(1.0, len(self.reflections) / 50)
        assessment_factor = min(1.0, len(self.assessments) / 20)

        awareness = (judgment_factor + reflection_factor + assessment_factor) / 3
        self.stats["self_awareness_score"] = awareness

        return awareness

    async def get_metacognitive_report(self) -> dict[str, Any]:
        """获取元认知报告"""
        return {
            "current_state": self.current_state.to_dict(),
            "capability_profile": self.capability_profile,
            "recent_judgments": [j.to_dict() for j in self.judgments[-5:]],
            "recent_reflections": [r.to_dict() for r in self.reflections[-5:]],
            "recent_assessments": [a.to_dict() for a in self.assessments[-3:]],
            "self_awareness_score": await self.get_self_awareness_score(),
            "stats": self.stats,
        }

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "total_judgments": len(self.judgments),
            "total_reflections": len(self.reflections),
            "total_assessments": len(self.assessments),
            "capability_count": len(self.capability_profile),
        }


# 便捷函数
async def create_metacognition_system() -> MetacognitionSystem:
    """创建元认知系统"""
    return MetacognitionSystem()
