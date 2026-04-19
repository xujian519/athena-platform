#!/usr/bin/env python3
from __future__ import annotations
"""
RAG能力适配器 - 将RAG管理器包装为能力调用接口
RAG Capability Adapter - Wrap RAG Manager as Capability Invocation Interface

功能:
1. 将RAG管理器的检索方法适配为能力调用接口
2. 支持向量检索、知识图谱查询等能力
3. 提供统一的结果格式

作者: Claude Code
版本: 1.0.0
日期: 2026-01-23
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RAGCapabilityAdapter:
    """
    RAG能力适配器

    将RAG管理器包装为能力调用接口,供动态提示词系统使用
    """

    def __init__(self, rag_manager=None):
        """
        初始化RAG能力适配器

        Args:
            rag_manager: RAG管理器实例
        """
        self.rag_manager = rag_manager
        logger.info("✅ RAG能力适配器初始化完成")

    async def invoke_vector_search(
        self,
        query_text: str,
        collections: list[str] | None = None,
        limit: int = 5,
        threshold: float = 0.3,
        task_type: str = "default",
    ) -> dict[str, Any]:
        """
        向量检索能力

        Args:
            query_text: 查询文本
            collections: 要检索的集合列表(为空则使用任务类型默认集合)
            limit: 返回结果数
            threshold: 相似度阈值
            task_type: 任务类型(用于选择检索策略)

        Returns:
            检索结果字典
        """
        if not self.rag_manager:
            logger.warning("⚠️ RAG管理器未初始化,返回空结果")
            return self._empty_vector_result(query_text)

        try:
            # 使用RAG管理器执行检索
            rag_context = await self.rag_manager.retrieve(
                query=query_text,
                task_type=task_type,
                context={"collections": collections} if collections else None,
            )

            # 转换为能力调用格式
            results = []
            for retrieval_result in rag_context.retrieval_results:
                results.append(
                    {
                        "id": str(retrieval_result.metadata.get("id", "")),
                        "title": retrieval_result.source,
                        "content": retrieval_result.content,
                        "similarity": retrieval_result.score,
                        "metadata": retrieval_result.metadata,
                    }
                )

            logger.info(
                f"✅ 向量检索完成: {len(results)}条结果, 数据源: {rag_context.data_sources_used}"
            )

            return {
                "results": results,
                "query": query_text,
                "data_sources": rag_context.data_sources_used,
                "total_results": len(results),
                "processing_time": rag_context.processing_time,
            }

        except Exception as e:
            logger.error(f"❌ 向量检索失败: {e}")
            return self._empty_vector_result(query_text)

    async def invoke_kg_query(
        self, query_text: str, query_type: str = "semantic", limit: int = 10
    ) -> dict[str, Any]:
        """
        知识图谱查询能力

        Args:
            query_text: 查询文本
            query_type: 查询类型(semantic/path/entity)
            limit: 返回结果数

        Returns:
            查询结果字典
        """
        # TODO: 集成Neo4j知识图谱查询
        logger.warning("⚠️ 知识图谱查询暂未实现,返回模拟数据")

        return {
            "nodes": [
                {"id": "1", "label": "专利", "name": "示例专利", "properties": {}},
                {"id": "2", "label": "概念", "name": "创造性", "properties": {}},
            ],
            "relationships": [{"from": "1", "to": "2", "type": "RELATED_TO", "properties": {}}],
            "query": query_text,
            "query_type": query_type,
            "total_nodes": 2,
            "total_relationships": 1,
        }

    async def invoke_hybrid_search(
        self,
        query_text: str,
        task_type: str = "patent_search",
        vector_weight: float = 0.7,
        kg_weight: float = 0.3,
    ) -> dict[str, Any]:
        """
        混合检索能力(向量+知识图谱)

        Args:
            query_text: 查询文本
            task_type: 任务类型
            vector_weight: 向量检索权重
            kg_weight: 知识图谱权重

        Returns:
            混合检索结果
        """
        # 执行向量检索
        vector_result = await self.invoke_vector_search(query_text=query_text, task_type=task_type)

        # 执行知识图谱查询
        kg_result = await self.invoke_kg_query(query_text=query_text)

        # 合并结果(简单实现)
        return {
            "vector_results": vector_result.get("results", []),
            "kg_results": kg_result,
            "query": query_text,
            "weights": {"vector": vector_weight, "kg": kg_weight},
        }

    def _empty_vector_result(self, query: str) -> dict[str, Any]:
        """返回空的向量检索结果"""
        return {
            "results": [],
            "query": query,
            "data_sources": [],
            "total_results": 0,
            "processing_time": 0.0,
        }


# 全局单例
_rag_capability_adapter: RAGCapabilityAdapter | None = None


def get_rag_capability_adapter(rag_manager=None) -> RAGCapabilityAdapter:
    """
    获取RAG能力适配器单例

    Args:
        rag_manager: RAG管理器实例

    Returns:
        RAG能力适配器实例
    """
    global _rag_capability_adapter

    if _rag_capability_adapter is None and rag_manager is not None:
        _rag_capability_adapter = RAGCapabilityAdapter(rag_manager)

    return _rag_capability_adapter
