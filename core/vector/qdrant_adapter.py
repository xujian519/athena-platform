#!/usr/bin/env python3
"""
Qdrant向量搜索适配器
Qdrant Vector Search Adapter

替换原有的NumPy向量搜索实现
"""

import logging
from typing import Any

from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class QdrantVectorAdapter:
    """Qdrant向量搜索适配器"""

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.collections = {
            "athena_memory": "athena_memory",
            "xiaonuo_memory": "xiaonuo_memory",
            "patents": "patents_professional",
            "legal": "legal_documents_unified",  # 更新为统一集合
            "technical": "technical_terms_unified",  # 更新为统一集合
            "patent_rules_1024": "patent_rules_1024",  # 专利规则向量库
            "patents_invalid_1024": "patents_invalid_1024",  # 专利无效向量库
            "legal_clauses_1024": "legal_clauses_1024",  # 法律条款向量库
            "technical_terms_1024": "technical_terms_1024",  # 技术术语向量库
        }

    async def search_vectors(
        self,
        collection_type: str,
        query_vector: list[float],
        limit: int = 10,
        threshold: float = 0.3,
    ) -> list[dict[str, Any]]:
        """搜索向量"""

        collection_name = self.collections.get(collection_type)
        if not collection_name:
            return []

        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=threshold,
                with_payload=True,
            )

            return [
                {"id": point.id, "score": point.score, "payload": point.payload}
                for point in results
            ]

        except Exception as e:
            logger.info(f"Qdrant搜索失败: {e}")
            return []

    async def add_vectors(self, collection_type: str, vectors: list[dict[str, Any]]) -> bool:
        """添加向量"""

        collection_name = self.collections.get(collection_type)
        if not collection_name:
            return False

        try:
            points = []
            for item in vectors:
                points.append(
                    {"id": item["id"], "vector": item["vector"], "payload": item["payload"]}
                )

            self.client.upsert(collection_name=collection_name, points=points)

            return True

        except Exception as e:
            logger.info(f"Qdrant添加向量失败: {e}")
            return False
