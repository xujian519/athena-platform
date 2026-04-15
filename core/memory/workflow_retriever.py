from __future__ import annotations
import numpy as np

#!/usr/bin/env python3
"""
工作流模式检索器

基于向量相似度检索相关的workflow模式。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import logging
from dataclasses import dataclass
from typing import Any

from core.memory.workflow_pattern import WorkflowPattern

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""

    pattern: WorkflowPattern
    similarity: float
    relevance_score: float
    match_reason: str


class WorkflowRetriever:
    """
    工作流模式检索器

    基于多种策略检索相似的历史workflow模式:
    1. 向量相似度检索
    2. 任务类型匹配
    3. 关键词匹配
    """

    def __init__(
        self, similarity_threshold: float = 0.75, top_k: int = 5, enable_hybrid_search: bool = True
    ):
        """
        初始化检索器

        Args:
            similarity_threshold: 相似度阈值
            top_k: 返回结果数量
            enable_hybrid_search: 是否启用混合检索
        """
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.enable_hybrid_search = enable_hybrid_search

        logger.info(
            f"🔍 WorkflowRetriever初始化 " f"(阈值: {similarity_threshold}, Top-K: {top_k})"
        )

    async def retrieve_similar_workflows(
        self,
        task: Any,
        patterns: list[WorkflowPattern],
        task_embedding: np.ndarray | None = None,
    ) -> list[RetrievalResult]:
        """
        检索相似的workflow模式

        Args:
            task: 当前任务
            patterns: 候选模式列表
            task_embedding: 任务向量表示(可选)

        Returns:
            按相似度排序的检索结果列表
        """
        logger.info(f"🔍 检索相似workflow (候选模式: {len(patterns)})")

        if not patterns:
            return []

        # 策略1: 向量相似度检索
        if task_embedding is not None:
            vector_results = await self._vector_similarity_search(task_embedding, patterns)
        else:
            vector_results = []

        # 策略2: 任务类型匹配
        type_results = await self._type_based_search(task, patterns)

        # 策略3: 关键词匹配
        keyword_results = await self._keyword_based_search(task, patterns)

        # 混合检索
        if self.enable_hybrid_search:
            results = await self._hybrid_search(vector_results, type_results, keyword_results)
        else:
            results = vector_results or type_results

        # 过滤低相似度结果
        filtered_results = [r for r in results if r.similarity >= self.similarity_threshold]

        # 按相关性分数排序并返回Top-K
        sorted_results = sorted(filtered_results, key=lambda r: r.relevance_score, reverse=True)[
            : self.top_k
        ]

        logger.info(
            f"✅ 检索完成: 返回{len(sorted_results)}个结果 " f"(阈值: {self.similarity_threshold})"
        )

        return sorted_results

    async def _vector_similarity_search(
        self, task_embedding: np.ndarray, patterns: list[WorkflowPattern]
    ) -> list[RetrievalResult]:
        """向量相似度搜索"""

        results = []

        for pattern in patterns:
            if pattern.embedding is None:
                continue

            # 计算余弦相似度
            similarity = self._cosine_similarity(task_embedding, pattern.embedding)

            results.append(
                RetrievalResult(
                    pattern=pattern,
                    similarity=similarity,
                    relevance_score=similarity,
                    match_reason=f"向量相似度: {similarity:.3f}",
                )
            )

        return results

    async def _type_based_search(
        self, task: Any, patterns: list[WorkflowPattern]
    ) -> list[RetrievalResult]:
        """基于任务类型的搜索"""

        results = []
        task_type = getattr(task, "type", None)
        task_domain = getattr(task, "domain", None)

        for pattern in patterns:
            similarity = 0.0
            match_reasons = []

            # 任务类型完全匹配
            if task_type and pattern.task_type == task_type:
                similarity += 0.4
                match_reasons.append(f"任务类型匹配: {task_type}")

            # 领域匹配
            if task_domain and pattern.domain == task_domain:
                similarity += 0.3
                match_reasons.append(f"领域匹配: {task_domain}")

            # 成功率权重
            similarity += 0.3 * pattern.success_rate
            match_reasons.append(f"成功率: {pattern.success_rate:.2f}")

            if similarity > 0:
                results.append(
                    RetrievalResult(
                        pattern=pattern,
                        similarity=similarity,
                        relevance_score=similarity,
                        match_reason=", ".join(match_reasons),
                    )
                )

        return results

    async def _keyword_based_search(
        self, task: Any, patterns: list[WorkflowPattern]
    ) -> list[RetrievalResult]:
        """基于关键词的搜索"""

        results = []
        task_description = getattr(task, "description", "").lower()

        # 提取关键词
        task_keywords = self._extract_keywords(task_description)

        for pattern in patterns:
            pattern_desc = pattern.description.lower()
            pattern_name = pattern.name.lower()

            # 计算关键词匹配度
            matches = sum(1 for kw in task_keywords if kw in pattern_desc or kw in pattern_name)

            if matches > 0:
                similarity = min(1.0, matches / len(task_keywords)) * 0.8

                results.append(
                    RetrievalResult(
                        pattern=pattern,
                        similarity=similarity,
                        relevance_score=similarity,
                        match_reason=f"关键词匹配: {matches}/{len(task_keywords)}",
                    )
                )

        return results

    async def _hybrid_search(
        self,
        vector_results: list[RetrievalResult],
        type_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """混合检索,融合多种策略的结果"""

        # 聚合所有结果
        all_results: dict[str, RetrievalResult] = {}

        # 向量结果 (权重: 0.5)
        for result in vector_results:
            pattern_id = result.pattern.pattern_id
            if pattern_id not in all_results:
                all_results[pattern_id] = result
            else:
                # 累加相关性分数
                all_results[pattern_id].relevance_score += 0.5 * result.similarity

        # 类型匹配结果 (权重: 0.3)
        for result in type_results:
            pattern_id = result.pattern.pattern_id
            if pattern_id not in all_results:
                all_results[pattern_id] = result
                all_results[pattern_id].relevance_score = 0.3 * result.similarity
            else:
                all_results[pattern_id].relevance_score += 0.3 * result.similarity

        # 关键词结果 (权重: 0.2)
        for result in keyword_results:
            pattern_id = result.pattern.pattern_id
            if pattern_id not in all_results:
                all_results[pattern_id] = result
                all_results[pattern_id].relevance_score = 0.2 * result.similarity
            else:
                all_results[pattern_id].relevance_score += 0.2 * result.similarity

        return list(all_results.values())

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(vec1, vec2) / (norm1 * norm2)

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""

        # 简单实现: 基于常见关键词列表
        common_keywords = [
            "专利",
            "分析",
            "检索",
            "审查",
            "新颖性",
            "创造性",
            "patent",
            "analysis",
            "search",
            "review",
            "novelty",
            "法律",
            "案例",
            "判决",
            "法规",
            "商标",
            "版权",
            "侵权",
            "答复",
            "意见",
            "陈述",
        ]

        keywords = []
        text_lower = text.lower()

        for kw in common_keywords:
            if kw.lower() in text_lower:
                keywords.append(kw)

        return keywords


__all__ = ["RetrievalResult", "WorkflowRetriever"]
