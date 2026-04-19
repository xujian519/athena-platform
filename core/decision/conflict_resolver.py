#!/usr/bin/env python3
from __future__ import annotations
"""
冲突仲裁器
Conflict Resolver

当智能体之间意见冲突时,进行仲裁和协调。
基于规则和证据强度,帮助达成共识或明确分歧。

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .integrated_decision_engine import AgentOpinion, ConflictAnalysis

logger = logging.getLogger(__name__)


class ArbitrationResult(Enum):
    """仲裁结果类型"""

    CONSENSUS_REACHED = "达成共识"
    COMPROMISE_FOUND = "找到折中"
    DIVERGENCE_IDENTIFIED = "明确分歧"
    FURTHER_DISCUSSION = "需要进一步讨论"


@dataclass
class ArbitrationDecision:
    """仲裁决策"""

    result: ArbitrationResult
    resolution: str
    adjusted_opinions: list[AgentOpinion]
    reasoning: str
    confidence: float


class ConflictResolver:
    """
    冲突仲裁器

    当智能体意见冲突时,基于规则进行仲裁
    """

    def __init__(self):
        """初始化冲突仲裁器"""
        self.name = "冲突仲裁器"
        self.arbitration_rules = self._init_arbitration_rules()
        logger.info("⚖️ 冲突仲裁器初始化完成")

    def _init_arbitration_rules(self) -> dict[str, Any]:
        """初始化仲裁规则"""
        return {
            "evidence_weight": 0.4,
            "expertise_weight": 0.3,
            "confidence_weight": 0.3,
            "consensus_threshold": 0.7,
            "compromise_threshold": 0.5,
        }

    async def resolve(
        self,
        opinions: list[AgentOpinion],
        conflict: ConflictAnalysis,
        context: dict[str, Any] | None = None,
    ) -> ArbitrationDecision:
        """
        仲裁冲突

        Args:
            opinions: 各智能体意见
            conflict: 冲突分析结果
            context: 上下文信息

        Returns:
            ArbitrationDecision: 仲裁决策
        """
        logger.info("⚖️ 启动冲突仲裁")
        logger.info(f"   冲突方: {conflict.conflicting_parties}")

        # 计算各方得分
        scores = self._calculate_scores(opinions)

        # 判断是否可以达成共识
        if self._can_reach_consensus(scores):
            result = ArbitrationResult.CONSENSUS_REACHED
            resolution = self._form_consensus_resolution(opinions, scores)
            adjusted_opinions = self._adjust_opinions_toward_consensus(opinions, resolution)
            confidence = 0.85

        elif self._can_find_compromise(scores):
            result = ArbitrationResult.COMPROMISE_FOUND
            resolution = self._form_compromise(opinions, scores)
            adjusted_opinions = self._adjust_opinions_for_compromise(opinions, resolution)
            confidence = 0.70

        else:
            result = ArbitrationResult.DIVERGENCE_IDENTIFIED
            resolution = self._identify_divergence(opinions, conflict)
            adjusted_opinions = opinions  # 保持原意见
            confidence = 0.60

        reasoning = f"""基于证据强度({self.arbitration_rules['evidence_weight']})、
专业匹配度({self.arbitration_rules['expertise_weight']})和置信度({self.arbitration_rules['confidence_weight']})进行仲裁。
"""

        logger.info(f"   仲裁结果: {result.value}")
        logger.info(f"   解决方案: {resolution[:100]}...")

        return ArbitrationDecision(
            result=result,
            resolution=resolution,
            adjusted_opinions=adjusted_opinions,
            reasoning=reasoning,
            confidence=confidence,
        )

    def _calculate_scores(self, opinions: list[AgentOpinion]) -> dict[str, float]:
        """计算各方得分"""
        scores = {}

        for opinion in opinions:
            # 证据得分
            evidence_score = len(opinion.evidence) * 0.1

            # 置信度得分
            confidence_score = opinion.confidence

            # 综合得分
            total_score = (
                evidence_score * self.arbitration_rules["evidence_weight"]
                + confidence_score * self.arbitration_rules["confidence_weight"]
            )

            scores[opinion.agent_name] = total_score

        return scores

    def _can_reach_consensus(self, scores: dict[str, float]) -> bool:
        """判断是否能达成共识"""
        if not scores:
            return False
        max_score = max(scores.values())
        return max_score >= self.arbitration_rules["consensus_threshold"]

    def _can_find_compromise(self, scores: dict[str, float]) -> bool:
        """判断是否能找到折中方案"""
        if not scores:
            return False
        avg_score = sum(scores.values()) / len(scores)
        return avg_score >= self.arbitration_rules["compromise_threshold"]

    def _form_consensus_resolution(
        self, opinions: list[AgentOpinion], scores: dict[str, float]
    ) -> str:
        """形成共识解决方案"""
        # 找到得分最高的意见
        best_agent = max(scores.keys(), key=lambda k: scores[k])
        best_opinion = next(op for op in opinions if op.agent_name == best_agent)

        return f"""采纳{best_agent}的建议。
理由:该方在证据强度和置信度综合评估中表现最优。
具体建议:{best_opinion.opinion}
"""

    def _form_compromise(self, opinions: list[AgentOpinion], scores: dict[str, float]) -> str:
        """形成折中方案"""
        all_suggestions = [op.opinion for op in opinions]
        return f"""综合各方意见,建议采取折中方案。
各方观点包括:
{chr(10).join(f'  - {s}' for s in all_suggestions)}

折中建议:在考虑各方关切的基础上,平衡多方面因素。
"""

    def _identify_divergence(self, opinions: list[AgentOpinion], conflict: ConflictAnalysis) -> str:
        """识别分歧"""
        divergence_desc = "、".join(conflict.conflict_points)
        return f"""各方在"{divergence_desc}"问题上存在根本分歧。
这种分歧可能源于:
1. 专业视角不同
2. 价值取向差异
3. 信息不对称

建议:提交给爸爸做最终判断。
"""

    def _adjust_opinions_toward_consensus(
        self, opinions: list[AgentOpinion], resolution: str
    ) -> list[AgentOpinion]:
        """调整意见以达成共识"""
        adjusted = []
        for op in opinions:
            adjusted_op = AgentOpinion(
                agent_name=op.agent_name,
                opinion=op.opinion + f" [经仲裁调整: {resolution[:50]}...]",
                confidence=min(op.confidence + 0.05, 1.0),
                evidence=op.evidence,
                reasoning=op.reasoning + " 接受仲裁结果。",
            )
            adjusted.append(adjusted_op)
        return adjusted

    def _adjust_opinions_for_compromise(
        self, opinions: list[AgentOpinion], resolution: str
    ) -> list[AgentOpinion]:
        """调整意见以接受折中"""
        adjusted = []
        for op in opinions:
            adjusted_op = AgentOpinion(
                agent_name=op.agent_name,
                opinion=op.opinion + " [接受折中方案]",
                confidence=op.confidence,
                evidence=op.evidence,
                reasoning=op.reasoning + " 为了达成共识,接受折中。",
            )
            adjusted.append(adjusted_op)
        return adjusted
