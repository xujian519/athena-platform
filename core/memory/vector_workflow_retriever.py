#!/usr/bin/env python3
from __future__ import annotations
"""
向量workflow检索器

使用Qdrant向量数据库实现高性能O(log n)向量相似度检索。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import logging

import numpy as np

from core.memory.type_utils import safe_domain_getter
from core.memory.workflow_pattern import WorkflowPattern
from core.memory.workflow_retriever import RetrievalResult

logger = logging.getLogger(__name__)


class VectorWorkflowRetriever:
    """
    基于向量数据库的Workflow检索器

    使用Qdrant实现高性能向量相似度检索。
    当模式数量较大时（>1000），性能显著优于内存遍历。
    """

    COLLECTION_NAME = "workflow_patterns"

    def __init__(
        self,
        qdrant_url: str = "localhost:6333",
        vector_size: int = 768,
        similarity_threshold: float = 0.75
    ):
        """
        初始化向量检索器

        Args:
            qdrant_url: Qdrant服务地址
            vector_size: 向量维度
            similarity_threshold: 相似度阈值
        """
        self.qdrant_url = qdrant_url
        self.vector_size = vector_size
        self.similarity_threshold = similarity_threshold
        self._client = None
        self._enabled = False

        # 尝试连接Qdrant
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self._client = QdrantClient(url=qdrant_url)

            # 确保collection存在
            self._ensure_collection_exists()

            self._enabled = True
            logger.info(
                f"🔍 VectorWorkflowRetriever初始化完成 "
                f"(Qdrant: {qdrant_url}, 维度: {vector_size})"
            )
        except ImportError:
            logger.warning(
                "⚠️ qdrant-client未安装，向量检索功能不可用。"
                "安装命令: pip install qdrant-client"
            )
        except Exception:
            logger.warning("💡 启动Qdrant: docker run -p 6333:6333 qdrant/qdrant")

    def _ensure_collection_exists(self):
        """确保collection存在"""
        if not self._client:
            return

        from qdrant_client.models import Distance, VectorParams

        try:
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.COLLECTION_NAME not in collection_names:
                logger.info(f"📦 创建collection: {self.COLLECTION_NAME}")
                self._client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
            else:
                logger.debug(f"✅ Collection已存在: {self.COLLECTION_NAME}")
        except Exception:
            logger.error("操作失败: e", exc_info=True)
            raise

    @property
    def enabled(self) -> bool:
        """检查向量检索是否启用"""
        return self._enabled and self._client is not None

    async def index_pattern(self, pattern: WorkflowPattern) -> bool:
        """
        将模式索引到向量数据库

        Args:
            pattern: WorkflowPattern对象

        Returns:
            是否索引成功
        """
        if not self.enabled:
            return False

        if pattern.embedding is None:
            logger.debug(f"⏭️ 模式无embedding，跳过索引: {pattern.pattern_id}")
            return False

        try:
            from qdrant_client.models import PointStruct

            # 使用类型工具统一处理domain
            domain_value = safe_domain_getter(pattern.domain)

            point = PointStruct(
                id=pattern.pattern_id,
                vector=pattern.embedding.tolist(),
                payload={
                    "name": pattern.name,
                    "description": pattern.description,
                    "task_type": pattern.task_type,
                    "domain": domain_value,
                    "success_rate": pattern.success_rate,
                    "usage_count": pattern.usage_count,
                    "created_at": pattern.created_at.isoformat()
                }
            )

            self._client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[point]
            )

            logger.debug(f"📇 模式已索引: {pattern.pattern_id}")
            return True

        except Exception:
            return False

    async def retrieve_similar_workflows(
        self,
        task_embedding: np.ndarray,
        limit: int = 10,
        min_score: Optional[float] = None
    ) -> list[RetrievalResult]:
        """
        检索相似的workflow模式

        Args:
            task_embedding: 任务向量
            limit: 返回结果数量
            min_score: 最小相似度分数（可选）

        Returns:
            按相似度排序的检索结果列表
        """
        if not self.enabled:
            logger.debug("⏭️ 向量检索未启用")
            return []

        min_score = min_score or self.similarity_threshold

        logger.debug(f"🔍 向量检索: limit={limit}, min_score={min_score}")

        try:
            # 执行向量搜索
            search_results = self._client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=task_embedding.tolist(),
                limit=limit,
                score_threshold=min_score
            )

            # 转换为RetrievalResult
            results = []
            for result in search_results:
                # 从payload重建pattern
                pattern = self._payload_to_pattern(result.payload)
                if pattern:
                    results.append(RetrievalResult(
                        pattern=pattern,
                        similarity=result.score,
                        relevance_score=result.score,
                        match_reason=f"向量相似度: {result.score:.3f}"
                    ))

            logger.info(
                f"✅ 向量检索完成: 找到{len(results)}个相似模式 "
                f"(阈值: {min_score})"
            )

            return results

        except Exception:
            return []

    def _payload_to_pattern(self, payload: dict) -> WorkflowPattern | None:
        """从payload构建WorkflowPattern"""
        try:
            from datetime import datetime

            return WorkflowPattern(
                pattern_id=payload.get("name", "unknown"),
                name=payload["name"],
                description=payload["description"],
                task_type=payload["task_type"],
                domain=payload["domain"],
                steps=[],  # 向量检索不返回完整steps
                success_rate=payload["success_rate"],
                usage_count=payload["usage_count"],
                created_at=datetime.fromisoformat(payload["created_at"])
            )
        except Exception:
            return None

    async def delete_pattern(self, pattern_id: str) -> bool:
        """
        删除模式索引

        Args:
            pattern_id: 模式ID

        Returns:
            是否删除成功
        """
        if not self.enabled:
            return False

        try:
            self._client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=[pattern_id]
            )
            logger.debug(f"🗑️ 模式索引已删除: {pattern_id}")
            return True
        except Exception:
            return False

    async def get_collection_info(self) -> dict | None:
        """
        获取collection信息

        Returns:
            Collection信息字典
        """
        if not self.enabled:
            return None

        try:
            info = self._client.get_collection(self.COLLECTION_NAME)
            return {
                "name": info.config.params.vectors.size,
                "vector_size": info.config.params.vectors.size,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count
            }
        except Exception:
            return None


__all__ = ['VectorWorkflowRetriever']
