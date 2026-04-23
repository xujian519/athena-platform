#!/usr/bin/env python3
"""
专利相似度计算工具 - 计算两篇专利的相似度

功能：
1. 权利要求相似度 - 对比权利要求文本
2. 说明书相似度 - 对比说明书内容
3. 技术领域相似度 - 基于IPC分类
4. 综合相似度评分 - 加权综合评分
5. 相似度报告生成 - 详细的对比报告

技术方案：
- 向量相似度计算（使用BGE-M3嵌入）
- 文本相似度计算（Jaccard、余弦相似度）
- 结构化对比（权利要求逐项对比）
- 生成详细的相似度报告

Author: Athena平台团队
Date: 2026-04-20
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re

from core.tools.decorators import tool
from core.logging_config import setup_logging

logger = setup_logging()


class SimilarityLevel(Enum):
    """相似度等级"""
    VERY_HIGH = "极高相似"  # > 0.9
    HIGH = "高相似"  # 0.7 - 0.9
    MEDIUM = "中等相似"  # 0.5 - 0.7
    LOW = "低相似"  # 0.3 - 0.5
    VERY_LOW = "极低相似"  # < 0.3


@dataclass
class SimilarityResult:
    """相似度计算结果"""
    overall_similarity: float  # 综合相似度 (0-1)
    claims_similarity: float  # 权利要求相似度
    description_similarity: float  # 说明书相似度
    technical_field_similarity: float  # 技术领域相似度
    similarity_level: SimilarityLevel  # 相似度等级
    detailed_comparison: dict[str, Any]  # 详细对比


class PatentSimilarityCalculator:
    """专利相似度计算器"""

    def __init__(self):
        """初始化相似度计算器"""
        self._embedding_service = None

    def _get_embedding_service(self):
        """获取嵌入服务"""
        if self._embedding_service is None:
            try:
                from core.nlp.bge_embedding_service import get_bge_embedding_service
                self._embedding_service = get_bge_embedding_service()
            except Exception as e:
                logger.warning(f"⚠️ 无法加载嵌入服务: {e}")
                self._embedding_service = None
        return self._embedding_service

    async def calculate_similarity(
        self,
        patent1: dict[str, Any],
        patent2: dict[str, Any],
        weights: Optional[dict[str, float]] = None
    ) -> SimilarityResult:
        """
        计算两篇专利的相似度

        Args:
            patent1: 专利1数据
            patent2: 专利2数据
            weights: 权重配置（可选）

        Returns:
            相似度计算结果
        """
        # 默认权重
        if weights is None:
            weights = {
                "claims": 0.5,  # 权利要求权重50%
                "description": 0.3,  # 说明书权重30%
                "technical_field": 0.2  # 技术领域权重20%
            }

        # 1. 计算权利要求相似度
        claims_sim = await self._calculate_claims_similarity(
            patent1.get("claims", ""),
            patent2.get("claims", "")
        )

        # 2. 计算说明书相似度
        desc_sim = await self._calculate_description_similarity(
            patent1.get("description", ""),
            patent2.get("description", "")
        )

        # 3. 计算技术领域相似度
        field_sim = self._calculate_technical_field_similarity(
            patent1.get("ipc_classification", ""),
            patent2.get("ipc_classification", "")
        )

        # 4. 计算综合相似度
        overall_sim = (
            claims_sim * weights["claims"] +
            desc_sim * weights["description"] +
            field_sim * weights["technical_field"]
        )

        # 5. 确定相似度等级
        similarity_level = self._get_similarity_level(overall_sim)

        # 6. 生成详细对比
        detailed_comparison = {
            "patent1_id": patent1.get("patent_id", "Unknown"),
            "patent2_id": patent2.get("patent_id", "Unknown"),
            "weights_used": weights,
            "individual_similarities": {
                "claims": claims_sim,
                "description": desc_sim,
                "technical_field": field_sim
            },
            "key_differences": self._extract_key_differences(patent1, patent2)
        }

        return SimilarityResult(
            overall_similarity=overall_sim,
            claims_similarity=claims_sim,
            description_similarity=desc_sim,
            technical_field_similarity=field_sim,
            similarity_level=similarity_level,
            detailed_comparison=detailed_comparison
        )

    async def _calculate_claims_similarity(
        self,
        claims1: str,
        claims2: str
    ) -> float:
        """
        计算权利要求相似度

        Args:
            claims1: 专利1的权利要求
            claims2: 专利2的权利要求

        Returns:
            相似度 (0-1)
        """
        if not claims1 or not claims2:
            return 0.0

        # 方法1: 文本相似度（Jaccard）
        text_sim = self._jaccard_similarity(claims1, claims2)

        # 方法2: 向量相似度（如果有嵌入服务）
        vector_sim = 0.0
        embedding_service = self._get_embedding_service()
        if embedding_service:
            try:
                emb1 = await embedding_service.embed_text(claims1)
                emb2 = await embedding_service.embed_text(claims2)

                # 计算余弦相似度
                vector_sim = self._cosine_similarity(emb1, emb2)
            except Exception as e:
                logger.warning(f"⚠️ 向量相似度计算失败: {e}")

        # 综合两种方法（向量相似度权重更高）
        return text_sim * 0.3 + vector_sim * 0.7

    async def _calculate_description_similarity(
        self,
        desc1: str,
        desc2: str
    ) -> float:
        """
        计算说明书相似度

        Args:
            desc1: 专利1的说明书
            desc2: 专利2的说明书

        Returns:
            相似度 (0-1)
        """
        if not desc1 or not desc2:
            return 0.0

        # 文本相似度
        text_sim = self._jaccard_similarity(desc1, desc2)

        # 向量相似度
        vector_sim = 0.0
        embedding_service = self._get_embedding_service()
        if embedding_service:
            try:
                emb1 = await embedding_service.embed_text(desc1)
                emb2 = await embedding_service.embed_text(desc2)
                vector_sim = self._cosine_similarity(emb1, emb2)
            except Exception as e:
                logger.warning(f"⚠️ 向量相似度计算失败: {e}")

        return text_sim * 0.3 + vector_sim * 0.7

    def _calculate_technical_field_similarity(
        self,
        ipc1: str,
        ipc2: str
    ) -> float:
        """
        计算技术领域相似度（基于IPC分类）

        Args:
            ipc1: 专利1的IPC分类
            ipc2: 专利2的IPC分类

        Returns:
            相似度 (0-1)
        """
        if not ipc1 or not ipc2:
            return 0.0

        # IPC分类格式：部类(1字母) + 大类(2数字) + 小类(1字母) + ...
        # 例如：G06F 17/30

        # 提取部类和大类
        def extract_ipc_section(ipc: str) -> str:
            match = re.match(r"([A-H])\d+", ipc)
            return match.group(1) if match else ""

        section1 = extract_ipc_section(ipc1)
        section2 = extract_ipc_section(ipc2)

        # 相同部类 = 1.0，不同 = 0.0
        return 1.0 if section1 and section1 == section2 else 0.0

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        计算Jaccard相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度 (0-1)
        """
        # 分词（简单按字符分割，中文按词）
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _tokenize(self, text: str) -> list[str]:
        """
        分词

        Args:
            text: 文本

        Returns:
            词语列表
        """
        # 移除标点符号
        text = re.sub(r"[^\w\s]", "", text)

        # 简单分词（按空格）
        words = text.split()

        return words

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度 (0-1)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _get_similarity_level(self, similarity: float) -> SimilarityLevel:
        """
        根据相似度分数确定等级

        Args:
            similarity: 相似度分数

        Returns:
            相似度等级
        """
        if similarity >= 0.9:
            return SimilarityLevel.VERY_HIGH
        elif similarity >= 0.7:
            return SimilarityLevel.HIGH
        elif similarity >= 0.5:
            return SimilarityLevel.MEDIUM
        elif similarity >= 0.3:
            return SimilarityLevel.LOW
        else:
            return SimilarityLevel.VERY_LOW

    def _extract_key_differences(
        self,
        patent1: dict[str, Any],
        patent2: dict[str, Any]
    ) -> list[str]:
        """
        提取关键差异

        Args:
            patent1: 专利1
            patent2: 专利2

        Returns:
            关键差异列表
        """
        differences = []

        # 对比标题
        title1 = patent1.get("title", "")
        title2 = patent2.get("title", "")
        if title1 != title2:
            differences.append(f"标题不同: '{title1}' vs '{title2}'")

        # 对比IPC分类
        ipc1 = patent1.get("ipc_classification", "")
        ipc2 = patent2.get("ipc_classification", "")
        if ipc1 != ipc2:
            differences.append(f"IPC分类不同: '{ipc1}' vs '{ipc2}'")

        # 对比申请人
        applicant1 = patent1.get("applicant", "")
        applicant2 = patent2.get("applicant", "")
        if applicant1 and applicant2 and applicant1 != applicant2:
            differences.append(f"申请人不同: '{applicant1}' vs '{applicant2}'")

        return differences


# 创建全局计算器实例
_calculator_instance: Optional[PatentSimilarityCalculator] = None


def get_similarity_calculator() -> PatentSimilarityCalculator:
    """获取全局相似度计算器实例（单例模式）"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = PatentSimilarityCalculator()
    return _calculator_instance


@tool(
    name="patent_similarity",
    description="专利相似度计算工具，计算两篇专利的综合相似度",
    category="patent_analysis",
    tags=["patent", "similarity", "comparison", "analysis"]
)
async def patent_similarity_handler(
    patent1: dict[str, Any],
    patent2: dict[str, Any],
    weights: Optional[dict[str, float]] = None
) -> dict[str, Any]:
    """
    专利相似度计算工具handler

    Args:
        patent1: 专利1数据，包含：
            - patent_id: 专利号
            - title: 标题
            - claims: 权利要求
            - description: 说明书
            - ipc_classification: IPC分类
            - applicant: 申请人（可选）
        patent2: 专利2数据（结构同patent1）
        weights: 权重配置（可选）：
            - claims: 权利要求权重（默认0.5）
            - description: 说明书权重（默认0.3）
            - technical_field: 技术领域权重（默认0.2）

    Returns:
        相似度计算结果，包含：
        - success: 是否成功
        - overall_similarity: 综合相似度 (0-1)
        - claims_similarity: 权利要求相似度
        - description_similarity: 说明书相似度
        - technical_field_similarity: 技术领域相似度
        - similarity_level: 相似度等级
        - detailed_comparison: 详细对比
        - error: 错误信息（如果失败）
    """
    try:
        calculator = get_similarity_calculator()
        result = await calculator.calculate_similarity(patent1, patent2, weights)

        return {
            "success": True,
            "overall_similarity": result.overall_similarity,
            "claims_similarity": result.claims_similarity,
            "description_similarity": result.description_similarity,
            "technical_field_similarity": result.technical_field_similarity,
            "similarity_level": result.similarity_level.value,
            "detailed_comparison": result.detailed_comparison
        }

    except Exception as e:
        logger.error(f"相似度计算失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "overall_similarity": 0.0
        }


# 导出
__all__ = [
    "PatentSimilarityCalculator",
    "get_similarity_calculator",
    "patent_similarity_handler",
    "SimilarityLevel",
    "SimilarityResult"
]
