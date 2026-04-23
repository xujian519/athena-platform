#!/usr/bin/env python3
"""
证据收集器

收集无效宣告所需的证据。
"""
import logging
from dataclasses import dataclass
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Evidence:
    """证据"""
    evidence_id: str
    patent_id: str
    title: str
    relevance_score: float
    challenge_points: list[str]
    publication_date: str

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "evidence_id": self.evidence_id,
            "patent_id": self.patent_id,
            "title": self.title,
            "relevance_score": self.relevance_score,
            "challenge_points": self.challenge_points,
            "publication_date": self.publication_date
        }


class EvidenceCollector:
    """证据收集器"""

    def __init__(self):
        """初始化收集器"""
        try:
            from enhanced_patent_search import EnhancedPatentRetriever
            self.retriever = EnhancedPatentRetriever()
            logger.info("✅ 证据收集器初始化成功（带检索功能）")
        except Exception as e:
            logger.warning(f"⚠️ 检索器初始化失败: {e}")
            self.retriever = None

    async def collect_evidence(
        self,
        target_patent_id: str,
        target_claims: list[str],
        invalidity_grounds: list[str],
        max_evidence: int = 10
    ) -> list[Evidence]:
        """
        收集证据

        Args:
            target_patent_id: 目标专利号
            target_claims: 目标权利要求
            invalidity_grounds: 无效理由
            max_evidence: 最大证据数量

        Returns:
            证据列表
        """
        logger.info(f"🔍 开始收集证据: {target_patent_id}")

        evidence_list = []

        try:
            # 1. 从目标专利中提取关键词
            keywords = self._extract_keywords(target_claims)

            # 2. 检索相关专利
            if self.retriever and keywords:
                for keyword in keywords[:3]:  # 最多检索3个关键词
                    try:
                        results = await self.retriever.search(
                            query=keyword,
                            search_fields=["title", "abstract"],
                            top_k=3
                        )

                        for result in results:
                            evidence = Evidence(
                                evidence_id=f"EVI_{len(evidence_list) + 1}",
                                patent_id=result.patent_id,
                                title=result.title,
                                relevance_score=result.score if hasattr(result, 'score') else 0.5,
                                challenge_points=self._identify_challenge_points(
                                    result,
                                    target_claims
                                ),
                                publication_date=result.publication_date if hasattr(result, 'publication_date') else ""
                            )
                            evidence_list.append(evidence)

                    except Exception as e:
                        logger.error(f"❌ 检索失败 {keyword}: {e}")

            # 3. 限制证据数量
            evidence_list = evidence_list[:max_evidence]

            logger.info(f"✅ 收集到 {len(evidence_list)} 份证据")
            return evidence_list

        except Exception as e:
            logger.error(f"❌ 证据收集失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_keywords(self, target_claims: list[str]) -> list[str]:
        """从权利要求中提取关键词"""
        import re

        keywords = []

        for claim in target_claims:
            # 提取技术术语
            pattern = r'([^\s，。]{4,12})(?:层|模块|单元|装置|方法|系统)'
            matches = re.findall(pattern, claim)
            keywords.extend(matches)

        # 去重
        return list(set(keywords))[:5]

    def _identify_challenge_points(
        self,
        evidence: Any,
        target_claims: list[str]
    ) -> list[str]:
        """识别挑战点"""
        challenge_points = []

        # 简化实现：基于关键词匹配
        f"{evidence.title} {evidence.abstract if hasattr(evidence, 'abstract') else ''}"

        for claim in target_claims[:2]:  # 只检查前2条权利要求
            if evidence.patent_id.lower() not in claim.lower():
                # 找到差异
                challenge_points.append(f"对比权利要求: {claim[:50]}...")

        return challenge_points[:3]
