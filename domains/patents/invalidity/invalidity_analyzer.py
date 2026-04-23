#!/usr/bin/env python3
"""
无效理由分析器

分析专利的无效理由。
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvalidityGround(Enum):
    """无效理由类型"""
    NOVELTY = "novelty"  # 新颖性
    INVENTIVENESS = "inventiveness"  # 创造性
    CLARITY = "clarity"  # 清晰度
    SUPPORT = "support"  # 说明书支持
    DIVISIONAL = "divisional"  # 分案申请


@dataclass
class InvalidityAnalysis:
    """无效理由分析结果"""
    target_patent_id: str
    invalidity_grounds: list[InvalidityGround]
    claims_to_challenge: list[int]  # 挑战的权利要求
    analysis_details: dict[str, Any]
    confidence_scores: dict[str, float]
    recommended_strategy: str

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "target_patent_id": self.target_patent_id,
            "invalidity_grounds": [g.value for g in self.invalidity_grounds],
            "claims_to_challenge": self.claims_to_challenge,
            "analysis_details": self.analysis_details,
            "confidence_scores": self.confidence_scores,
            "recommended_strategy": self.recommended_strategy
        }


class InvalidityAnalyzer:
    """无效理由分析器"""

    def __init__(self):
        """初始化分析器"""
        logger.info("✅ 无效理由分析器初始化成功")

    async def analyze_invalidity(
        self,
        target_patent_id: str,
        target_claims: list[str],
        prior_art_references: list[str] | None = None,
        analysis_options: dict[str, Any] | None = None
    ) -> InvalidityAnalysis:
        """
        分析无效理由

        Args:
            target_patent_id: 目标专利号
            target_claims: 目标权利要求
            prior_art_references: 现有技术参考
            analysis_options: 分析选项

        Returns:
            InvalidityAnalysis对象
        """
        logger.info(f"🔍 开始分析无效理由: {target_patent_id}")

        try:
            # 1. 确定无效理由类型
            invalidity_grounds = self._determine_grounds(target_claims)

            # 2. 确定挑战的权利要求
            claims_to_challenge = list(range(1, len(target_claims) + 1))

            # 3. 分析细节
            analysis_details = {
                "total_claims": len(target_claims),
                "independent_claims": len([c for c in target_claims if c.startswith("1.")]),
                "prior_art_count": len(prior_art_references) if prior_art_references else 0,
                "analysis_date": "2026-04-20"
            }

            # 4. 计算置信度
            confidence_scores = self._calculate_confidence(
                invalidity_grounds,
                prior_art_references
            )

            # 5. 推荐策略
            recommended_strategy = self._recommend_strategy(
                invalidity_grounds,
                confidence_scores
            )

            logger.info("✅ 无效理由分析完成")

            return InvalidityAnalysis(
                target_patent_id=target_patent_id,
                invalidity_grounds=invalidity_grounds,
                claims_to_challenge=claims_to_challenge,
                analysis_details=analysis_details,
                confidence_scores=confidence_scores,
                recommended_strategy=recommended_strategy
            )

        except Exception as e:
            logger.error(f"❌ 无效理由分析失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _determine_grounds(self, target_claims: list[str]) -> list[InvalidityGround]:
        """确定无效理由类型"""
        grounds = []

        # 默认基于新颖性和创造性
        grounds.append(InvalidityGround.NOVELTY)
        grounds.append(InvalidityGround.INVENTIVENESS)

        # 检查是否有清晰度问题
        for claim in target_claims:
            if "?" in claim or "约" in claim or "左右" in claim:
                if InvalidityGround.CLARITY not in grounds:
                    grounds.append(InvalidityGround.CLARITY)

        return grounds

    def _calculate_confidence(
        self,
        grounds: list[InvalidityGround],
        prior_art_references: list[str] | None
    ) -> dict[str, float]:
        """计算置信度"""
        confidence_scores = {}

        # 基于现有技术数量调整
        base_confidence = 0.6
        if prior_art_references:
            base_confidence += min(len(prior_art_references) * 0.1, 0.3)

        for ground in grounds:
            if ground == InvalidityGround.NOVELTY:
                confidence_scores["novelty"] = base_confidence + 0.1
            elif ground == InvalidityGround.INVENTIVENESS:
                confidence_scores["inventiveness"] = base_confidence

        return confidence_scores

    def _recommend_strategy(
        self,
        grounds: list[InvalidityGround],
        confidence_scores: dict[str, float]
    ) -> str:
        """推荐策略"""
        if InvalidityGround.NOVELTY in grounds:
            return "基于现有技术挑战新颖性"
        elif InvalidityGround.INVENTIVENESS in grounds:
            return "基于现有技术挑战创造性"
        else:
            return "综合多理由挑战"
