#!/usr/bin/env python3
from __future__ import annotations
"""
评估引擎 - 反思引擎
Evaluation Engine - Reflection Engine

作者: Athena平台团队
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.0.0

提供评估结果的反思和洞察提取功能。
"""

import logging
import statistics
import uuid
from collections import deque
from typing import Any

from .types import EvaluationResult, EvaluationType, ReflectionRecord, ReflectionType

logger = logging.getLogger(__name__)


class ReflectionEngine:
    """反思引擎"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.reflection_history = deque(maxlen=1000)
        self.patterns = []

    async def generate_reflection(
        self, evaluation_result: EvaluationResult, context: Optional[dict[str, Any]] = None
    ) -> ReflectionRecord:
        """生成反思"""
        reflection_id = str(uuid.uuid4())
        context = context or {}

        # 生成观察
        observations = await self._generate_observations(evaluation_result)

        # 进行分析
        analysis = await self._perform_analysis(evaluation_result, observations)

        # 提取见解
        insights = await self._extract_insights(evaluation_result, analysis)

        # 生成行动项
        action_items = await self._generate_action_items(evaluation_result, insights)

        # 总结经验教训
        lessons_learned = await self._summarize_lessons(evaluation_result, insights)

        reflection = ReflectionRecord(
            id=reflection_id,
            evaluator_id=self.agent_id,
            target_evaluation_id=evaluation_result.id,
            reflection_type=ReflectionType.SELF_REFLECTION,
            context=context,
            observations=observations,
            analysis=analysis,
            insights=insights,
            action_items=action_items,
            lessons_learned=lessons_learned,
        )

        self.reflection_history.append(reflection)
        return reflection

    async def _generate_observations(self, evaluation_result: EvaluationResult) -> str:
        """生成观察"""
        observations = []

        # 基于分数的观察
        if evaluation_result.overall_score < 70:
            observations.append("整体表现低于期望水平")
        elif evaluation_result.overall_score > 85:
            observations.append("整体表现优秀")

        # 基于强项的观察
        if evaluation_result.strengths:
            observations.append(f"识别出{len(evaluation_result.strengths)}个强项")

        # 基于弱项的观察
        if evaluation_result.weaknesses:
            observations.append(f"发现{len(evaluation_result.weaknesses)}个需要改进的方面")

        return "; ".join(observations) if observations else "无明显特征"

    async def _perform_analysis(
        self, evaluation_result: EvaluationResult, observations: str
    ) -> str:
        """进行分析"""
        analysis_parts = []

        # 分析评分分布
        scores = [result.get("score", 0) for result in evaluation_result.criteria_results.values()]
        if scores:
            avg_score = statistics.mean(scores)
            min_score = min(scores)
            max_score = max(scores)

            analysis_parts.append(f"平均得分为{avg_score:.1f},最低{min_score},最高{max_score}")

            # 分析得分差异
            if max_score - min_score > 40:
                analysis_parts.append("各标准得分差异较大,存在明显的优劣势")
            elif max_score - min_score < 10:
                analysis_parts.append("各标准得分较为均衡")

        # 分析改进建议
        if evaluation_result.recommendations:
            analysis_parts.append(f"提出了{len(evaluation_result.recommendations)}项改进建议")

        return "; ".join(analysis_parts) if analysis_parts else "需要进一步分析"

    async def _extract_insights(
        self, evaluation_result: EvaluationResult, analysis: str
    ) -> list[str]:
        """提取见解"""
        insights = []

        # 从分数中提取见解
        if evaluation_result.overall_score < 60:
            insights.append("当前表现需要立即关注和改进")
        elif 60 <= evaluation_result.overall_score < 80:
            insights.append("有明确的改进空间和发展潜力")
        else:
            insights.append("表现良好,可考虑进一步提升到卓越水平")

        # 从弱项中提取见解
        if evaluation_result.weaknesses:
            insights.append("弱项集中表明需要系统性的改进方案")

        # 从强项中提取见解
        if evaluation_result.strengths:
            insights.append("强项可以作为其他领域的改进参考")

        return insights

    async def _generate_action_items(
        self, evaluation_result: EvaluationResult, insights: list[str]
    ) -> list[str]:
        """生成行动项"""
        action_items = []

        # 基于弱项生成行动项
        for weakness in evaluation_result.weaknesses:
            action_items.append(f"制定计划改进: {weakness}")

        # 基于建议生成行动项
        for recommendation in evaluation_result.recommendations[:3]:  # 限制数量
            action_items.append(f"实施改进措施: {recommendation}")

        # 基于见解生成行动项
        for insight in insights[:2]:  # 限制数量
            action_items.append(f"深入探索: {insight}")

        # 确保有行动项
        if not action_items:
            action_items.append("制定全面的改进计划")

        return action_items

    async def _summarize_lessons(
        self, evaluation_result: EvaluationResult, insights: list[str]
    ) -> list[str]:
        """总结经验教训"""
        lessons = []

        # 基于评估结果总结
        if evaluation_result.overall_score < 70:
            lessons.append("识别并解决核心问题是提升表现的关键")
        else:
            lessons.append("保持优势同时持续寻找改进机会")

        # 基于评估类型总结
        if evaluation_result.evaluation_type == EvaluationType.PERFORMANCE:
            lessons.append("性能优化需要持续监控和调整")
        elif evaluation_result.evaluation_type == EvaluationType.QUALITY:
            lessons.append("质量保证需要制度化、标准化")

        # 基于置信度总结
        if evaluation_result.confidence < 0.7:
            lessons.append("提高评估的置信度需要更多证据支持")

        return lessons if lessons else ["持续学习和改进是永恒的主题"]
