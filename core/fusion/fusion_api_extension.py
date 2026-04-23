#!/usr/bin/env python3
from __future__ import annotations
"""
向量-图融合API扩展
Fusion API Extension for Memory System

为现有记忆API添加向量-图融合能力

作者: 小诺·双鱼公主
创建时间: 2025-12-28
"""

import logging
from typing import Any

from pydantic import BaseModel, Field

from .vector_graph_fusion_service import (
    QueryStrategy,
    VectorGraphFusionService,
    get_fusion_service,
)

logger = logging.getLogger(__name__)


# 请求/响应模型
class FusionStoreRequest(BaseModel):
    """融合存储请求"""

    agent_id: str
    content: str
    memory_type: str = "conversation"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = []
    metadata: dict[str, Any] = {}


class FusionSearchRequest(BaseModel):
    """融合搜索请求"""

    query: str
    agent_id: Optional[str] = None
    memory_type: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    strategy: str = Field(default="fusion_both")


class FusionSearchResponse(BaseModel):
    """融合搜索响应"""

    results: list[dict]
    total_count: int
    strategy_used: str
    query_time_ms: float


class FusionStatsResponse(BaseModel):
    """融合统计响应"""

    total_agent_memories: int
    total_episodic_memories: int
    total_mappings: int
    coverage_rate: float
    sync_rate: float


class FusionAPIExtension:
    """融合API扩展"""

    def __init__(self, service: VectorGraphFusionService = None):
        """初始化API扩展"""
        self.service = service
        self._initialized = False

    async def initialize(self):
        """初始化扩展"""
        if self._initialized:
            return

        if self.service is None:
            self.service = await get_fusion_service()

        self._initialized = True
        logger.info("✅ 融合API扩展已初始化")

    async def store_memory(self, request: FusionStoreRequest) -> dict:
        """存储记忆"""
        if not self._initialized:
            await self.initialize()

        memory_id = await self.service.store_memory(
            agent_id=request.agent_id,
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            tags=request.tags,
            metadata=request.metadata,
        )

        return {"success": True, "memory_id": memory_id, "message": "记忆已存储到向量-图融合系统"}

    async def search_memories(self, request: FusionSearchRequest) -> FusionSearchResponse:
        """搜索记忆"""
        if not self._initialized:
            await self.initialize()

        import time

        start_time = time.time()

        # 解析策略
        try:
            strategy = QueryStrategy(request.strategy)
        except ValueError:
            strategy = QueryStrategy.FUSION_BOTH

        results = await self.service.search_memories(
            query=request.query,
            agent_id=request.agent_id,
            memory_type=request.memory_type,
            limit=request.limit,
            strategy=strategy,
        )

        query_time = (time.time() - start_time) * 1000

        return FusionSearchResponse(
            results=[
                {
                    "entity_id": r.entity_id,
                    "entity_type": r.entity_type,
                    "business_key": r.business_key,
                    "content": r.content,
                    "vector_score": r.vector_score,
                    "graph_centrality": r.graph_centrality,
                    "combined_score": r.combined_score,
                    "metadata": r.metadata,
                }
                for r in results
            ],
            total_count=len(results),
            strategy_used=strategy.value,
            query_time_ms=query_time,
        )

    async def get_memory(self, memory_id: str) -> dict | None:
        """获取单个记忆"""
        if not self._initialized:
            await self.initialize()

        return await self.service.get_memory_by_id(memory_id)

    async def get_statistics(self) -> FusionStatsResponse:
        """获取统计信息"""
        if not self._initialized:
            await self.initialize()

        stats = await self.service.get_statistics()

        return FusionStatsResponse(
            total_agent_memories=stats["total_agent_memories"],
            total_episodic_memories=stats["total_episodic_memories"],
            total_mappings=stats["total_mappings"],
            coverage_rate=stats["coverage_rate"],
            sync_rate=stats["sync_rate"],
        )

    async def health_check(self) -> dict:
        """健康检查"""
        return {
            "status": "healthy" if self._initialized else "initializing",
            "service_initialized": self._initialized,
            "vector_dimension": self.service.config.vector_dimension if self.service else None,
            "embedding_model": self.service.config.embedding_model if self.service else None,
        }


# 全局单例
_fusion_api: FusionAPIExtension = None


def get_fusion_api() -> FusionAPIExtension:
    """获取融合API单例"""
    global _fusion_api
    if _fusion_api is None:
        _fusion_api = FusionAPIExtension()
    return _fusion_api
