#!/usr/bin/env python3
"""
BGE专利搜索增强器
BGE Enhanced Patent Search

使用BGE Large ZH v1.5增强专利搜索功能

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""

import logging
from dataclasses import dataclass
from typing import Any

from core.nlp.bge_embedding_service import get_bge_service

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""

    patent_id: str
    title: str
    abstract: str
    score: float
    similarity: float
    highlights: list[str]


class BGEPatentSearch:
    """BGE专利搜索增强器"""

    def __init__(self):
        self.name = "BGE专利搜索"
        self.version = "1.0.0"
        self.bge_service = None
        self.logger = logging.getLogger(self.name)

    async def initialize(self):
        """初始化"""
        if not self.bge_service:
            self.bge_service = await get_bge_service()
            self.logger.info("BGE专利搜索初始化完成")

    async def search_patents(
        self, query: str, top_k: int = 10, similarity_threshold: float = 0.7
    ) -> list[SearchResult]:
        """
        使用BGE搜索专利

        Args:
            query: 查询文本
            top_k: 返回结果数
            similarity_threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        await self.initialize()

        try:
            # 生成查询向量
            query_embedding = await self.bge_service.encode(query, task_type="patent_search")

            # 获取查询向量
            if isinstance(query_embedding.embeddings, list):
                query_vector = (
                    query_embedding.embeddings[0]
                    if len(query_embedding.embeddings) == 1
                    else query_embedding.embeddings
                )
            else:
                query_vector = query_embedding.embeddings

            # 执行向量搜索
            results = await self._vector_search(query_vector, top_k, similarity_threshold)

            return results

        except Exception as e:
            self.logger.error(f"BGE专利搜索失败: {e}")
            return []

    async def _vector_search(
        self, query_vector: list[float], top_k: int, threshold: float
    ) -> list[SearchResult]:
        """执行向量搜索"""
        # TODO: 集成Qdrant向量数据库
        # 这里返回模拟结果
        mock_results = [
            SearchResult(
                patent_id=f"CN{1000 + i}A",
                title=f"专利技术方案 {i}",
                abstract="这是一项关于专利技术的创新方案...",
                score=0.9 - i * 0.05,
                similarity=0.9 - i * 0.05,
                highlights=[f"匹配的关键词{i}"],
            )
            for i in range(min(top_k, 5))
        ]

        # 过滤低于阈值的结果
        return [r for r in mock_results if r.similarity >= threshold]

    async def batch_encode_patents(self, patents: list[dict[str, Any]]) -> list[list[float]]:
        """
        批量编码专利文本

        Args:
            patents: 专利列表,每个包含title和abstract

        Returns:
            嵌入向量列表
        """
        await self.initialize()

        # 组合标题和摘要
        texts = []
        for patent in patents:
            title = patent.get("title", "")
            abstract = patent.get("abstract", "")
            combined = f"标题: {title}\n摘要: {abstract}"
            texts.append(combined)

        # 批量编码
        result = await self.bge_service.encode(texts, task_type="patent_analysis")

        return result.embeddings if isinstance(result.embeddings, list) else [result.embeddings]

    async def find_similar_patents(self, patent_text: str, top_k: int = 5) -> list[SearchResult]:
        """
        查找相似专利

        Args:
            patent_text: 专利文本
            top_k: 返回数量

        Returns:
            相似专利列表
        """
        await self.initialize()

        # 生成专利向量
        patent_embedding = await self.bge_service.encode(patent_text, task_type="patent_analysis")

        # 搜索相似专利
        patent_vector = (
            patent_embedding.embeddings[0]
            if isinstance(patent_embedding.embeddings, list)
            else patent_embedding.embeddings
        )

        return await self._vector_search(patent_vector, top_k, 0.75)

    def get_statistics(self) -> dict[str, Any]:
        """获取搜索统计"""
        if self.bge_service:
            return self.bge_service.get_statistics()
        return {"status": "not_initialized"}


# 导出
__all__ = ["BGEPatentSearch", "SearchResult"]
