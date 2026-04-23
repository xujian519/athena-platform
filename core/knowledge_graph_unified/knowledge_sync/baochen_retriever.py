#!/usr/bin/env python3

"""
宝宸知识库检索器
Bao Chen Knowledge Retriever for Athena Platform

从 Qdrant 的 baochen_wiki collection 中检索知识，
支持按分类过滤（等价于 patent_agent 的 KB_FILTERS 模式）。
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

COLLECTION_NAME = "baochen_wiki"

# 场景模式到知识库分类的映射（移植自 patent_agent/prompts.py）
KB_FILTERS: Optional[dict[str, list[str] = {
    "法律咨询": ["法律法规", "审查指南", "复审无效"],
    "审查意见": ["审查指南", "复审无效", "专利实务", "法律法规"],
    "侵权分析": ["专利侵权", "专利判决", "法律法规"],
    "检索": None,  # None = 不做分类过滤，搜索全部分类
}


@dataclass
class BaoChenSearchResult:
    """检索结果"""

    source_file: str
    kb_category: str
    page_title: str
    section_title: str
    chunk_text: str
    score: float
    wiki_links: list[str] = field(default_factory=list)
    source_book: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaoChenKnowledgeRetriever:
    """宝宸知识库检索器"""

    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.qdrant_url = qdrant_url.rstrip("/")
        self.session = requests.Session()
        self._embedding_service = None

    async def search(
        self,
        query: str,
        mode: str = "检索",
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> list[BaoChenSearchResult]:
        """
        搜索宝宸知识库

        Args:
            query: 查询文本
            mode: 场景模式（法律咨询/审查意见/侵权分析/检索）
            top_k: 返回结果数量
            score_threshold: 最低相似度阈值

        Returns:
            检索结果列表
        """
        # 1. 嵌入查询
        query_vector = await self._embed_query(query)
        if not query_vector:
            return []

        # 2. 构建 Qdrant 搜索请求
        kb_filter = KB_FILTERS.get(mode, None)

        # 使用 over-fetch-then-filter 策略
        fetch_k = top_k * 4 if kb_filter else top_k

        search_payload: dict[str, Any] = {
            "vector": query_vector,
            "limit": fetch_k,
            "with_payload": True,
            "score_threshold": score_threshold,
        }

        # 添加分类过滤
        if kb_filter:
            search_payload["filter"]] = {
                "should": [
                    {"key": "kb_category", "match": {"value": cat}}
                    for cat in kb_filter
                ],
                "min_should": 1,
            }

        # 3. 执行搜索
        try:
            url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}/points/search"
            resp = self.session.post(url, json=search_payload, timeout=10)

            if resp.status_code != 200:
                logger.error(f"搜索失败: {resp.text}")
                return []

            raw_results = resp.json().get("result", [])

        except Exception as e:
            logger.error(f"搜索异常: {e}")
            return []

        # 4. 转换结果
        results: list[BaoChenSearchResult] = []
        for item in raw_results[:top_k]:
            payload = item.get("payload", {})
            results.append(
                BaoChenSearchResult(
                    source_file=payload.get("source_file", ""),
                    kb_category=payload.get("kb_category", ""),
                    page_title=payload.get("page_title", ""),
                    section_title=payload.get("section_title", ""),
                    chunk_text=payload.get("chunk_text", ""),
                    score=item.get("score", 0.0),
                    wiki_links=payload.get("wiki_links", []),
                    source_book=payload.get("source_book"),
                    metadata={
                        "kb_subcategory": payload.get("kb_subcategory", ""),
                        "char_count": payload.get("char_count", 0),
                        "content_hash": payload.get("content_hash", ""),
                    },
                )
            )

        logger.info(f"检索 '{query[:30]}...' → {len(results)} 个结果 (模式: {mode})")
        return results

    async def search_by_categories(
        self,
        query: str,
        categories: list[str],
        top_k: int = 5,
    ) -> list[BaoChenSearchResult]:
        """
        按指定分类搜索

        Args:
            query: 查询文本
            categories: 要搜索的知识库分类列表
            top_k: 返回结果数量
        """
        query_vector = await self._embed_query(query)
        if not query_vector:
            return []

        search_payload: dict[str, Any] = {
            "vector": query_vector,
            "limit": top_k,
            "with_payload": True,
            "filter": {
                "should": [
                    {"key": "kb_category", "match": {"value": cat}}
                    for cat in categories
                ],
                "min_should": 1,
            },
        }

        try:
            url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}/points/search"
            resp = self.session.post(url, json=search_payload, timeout=10)
            if resp.status_code != 200:
                return []

            results = []
            for item in resp.json().get("result", []):
                payload = item.get("payload", {})
                results.append(
                    BaoChenSearchResult(
                        source_file=payload.get("source_file", ""),
                        kb_category=payload.get("kb_category", ""),
                        page_title=payload.get("page_title", ""),
                        section_title=payload.get("section_title", ""),
                        chunk_text=payload.get("chunk_text", ""),
                        score=item.get("score", 0.0),
                        wiki_links=payload.get("wiki_links", []),
                        source_book=payload.get("source_book"),
                    )
                )
            return results

        except Exception as e:
            logger.error(f"分类搜索异常: {e}")
            return []

    @staticmethod
    def get_kb_filter(mode: str) -> Optional[list[str]]:
        """获取指定模式的知识库过滤列表"""
        return KB_FILTERS.get(mode, None)

    @staticmethod
    def get_available_modes() -> list[str]:
        """获取可用的场景模式列表"""
        return list(KB_FILTERS.keys())

    async def _embed_query(self, text: str) -> list[float]:
        """嵌入查询文本"""
        try:
            service = await self._get_embedding_service()
            result = await service.encode(text, self._module_type.LEGAL_ANALYSIS)
            embedding = result["embeddings"]
            # 确保返回 list[float]
            if isinstance(embedding, list) and embedding and isinstance(embedding[0], list):
                return embedding[0]
            return embedding if isinstance(embedding, list) else []
        except Exception as e:
            logger.error(f"嵌入查询失败: {e}")
            return []

    async def _get_embedding_service(self):
        """获取嵌入服务"""
        if self._embedding_service is None:
            from core.ai.embedding.unified_embedding_service import (
                ModuleType,
                UnifiedEmbeddingService,
            )

            self._embedding_service = UnifiedEmbeddingService()
            await self._embedding_service.initialize()
            self._module_type = ModuleType
        return self._embedding_service

