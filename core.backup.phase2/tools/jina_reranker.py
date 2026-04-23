#!/usr/bin/env python3
"""
Jina Rerank工具 - 文档重排序，提高检索精度

功能：
1. 文档重排序 - 根据查询对文档进行相关性排序
2. 相关性评分 - 返回每个文档的相关性分数
3. Top-N选择 - 只返回最相关的N个文档
4. 批量处理 - 支持大规模文档重排序

技术方案：
- 使用8009端口的jina-reranker-v3-mlx模型
- 支持API密钥认证
- 返回相关性评分和排序结果

Author: Athena平台团队
Date: 2026-04-20
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import http.client
import json

from core.tools.decorators import tool
from core.logging_config import setup_logging

logger = setup_logging()


class JinaReranker:
    """Jina Reranker客户端"""

    def __init__(
        self,
        base_url: str = "127.0.0.1:8009",
        api_key: str = "xj781102@",
        model: str = "jina-reranker-v3-mlx"
    ):
        """
        初始化Jina Reranker

        Args:
            base_url: API服务地址
            api_key: API密钥
            model: 模型名称
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self._timeout = 30

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        重排序文档

        Args:
            query: 查询文本
            documents: 候选文档列表
            top_n: 返回前N个最相关的文档（None返回全部）
            model: 模型名称（默认使用初始化时的模型）

        Returns:
            重排序结果，包含：
            - success: 是否成功
            - results: 重排序后的文档列表
            - model: 使用的模型
            - usage: token使用情况
            - error: 错误信息（如果失败）
        """
        if not query or not query.strip():
            return {
                "success": False,
                "error": "查询文本为空",
                "results": []
            }

        if not documents or len(documents) == 0:
            return {
                "success": False,
                "error": "文档列表为空",
                "results": []
            }

        # 使用指定的模型或默认模型
        rerank_model = model or self.model

        try:
            # 构建请求
            payload = {
                "model": rerank_model,
                "query": query,
                "documents": documents,
                "top_n": top_n if top_n is not None else len(documents)
            }

            # 发送请求
            conn = http.client.HTTPConnection(
                self.base_url,
                timeout=self._timeout
            )

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            conn.request(
                "POST",
                "/v1/rerank",
                body=json.dumps(payload).encode("utf-8"),
                headers=headers
            )

            response = conn.getresponse()
            response_body = response.read().decode("utf-8")
            conn.close()

            if response.status != 200:
                return {
                    "success": False,
                    "error": f"API返回错误: {response.status} - {response_body}",
                    "results": []
                }

            # 解析响应
            result = json.loads(response_body)

            # 提取结果
            reranked_results = []
            for item in result.get("results", []):
                reranked_results.append({
                    "index": item.get("index"),
                    "document": item.get("document", {}).get("text", ""),
                    "relevance_score": item.get("relevance_score", 0.0),
                    "original_text": documents[item.get("index", 0)]
                })

            return {
                "success": True,
                "results": reranked_results,
                "model": result.get("model", rerank_model),
                "usage": result.get("usage", {}),
                "query": query
            }

        except Exception as e:
            logger.error(f"Rerank失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

    async def rerank_batch(
        self,
        queries: List[str],
        documents: List[str],
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        批量重排序

        Args:
            queries: 查询列表
            documents: 文档列表（所有查询共享相同的文档集）
            top_n: 返回前N个最相关的文档

        Returns:
            重排序结果列表
        """
        results = []
        for query in queries:
            result = await self.rerank(query, documents, top_n)
            results.append(result)

        return results


# 创建全局Reranker实例
_reranker_instance: Optional[JinaReranker] = None


def get_reranker() -> JinaReranker:
    """获取全局Reranker实例（单例模式）"""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = JinaReranker()
    return _reranker_instance


@tool(
    name="jina_reranker",
    description="文档重排序工具，使用Jina Reranker v3模型提高检索精度",
    category="semantic_search",
    tags=["rerank", "search", "ranking", "jina", "semantic"]
)
async def jina_reranker_handler(
    query: str,
    documents: List[str],
    top_n: Optional[int] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Jina Reranker工具handler

    Args:
        query: 查询文本
        documents: 候选文档列表
        top_n: 返回前N个最相关的文档（None返回全部）
        model: 模型名称（默认jina-reranker-v3-mlx）

    Returns:
        重排序结果字典，包含：
        - success: 是否成功
        - results: 重排序后的文档列表（包含相关性分数）
        - model: 使用的模型
        - usage: token使用情况
        - query: 查询文本
        - error: 错误信息（如果失败）
    """
    reranker = get_reranker()
    result = await reranker.rerank(query, documents, top_n, model)
    return result


@tool(
    name="jina_reranker_batch",
    description="批量文档重排序，支持多个查询同时重排序",
    category="semantic_search",
    tags=["rerank", "batch", "search", "ranking"]
)
async def jina_reranker_batch_handler(
    queries: List[str],
    documents: List[str],
    top_n: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    批量Jina Reranker工具handler

    Args:
        queries: 查询列表
        documents: 候选文档列表（所有查询共享）
        top_n: 返回前N个最相关的文档

    Returns:
        重排序结果列表
    """
    reranker = get_reranker()
    results = await reranker.rerank_batch(queries, documents, top_n)
    return results


# 导出
__all__ = [
    "JinaReranker",
    "get_reranker",
    "jina_reranker_handler",
    "jina_reranker_batch_handler"
]
