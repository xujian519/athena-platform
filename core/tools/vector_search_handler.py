#!/usr/bin/env python3
"""
向量搜索Handler（1024维度版本）
使用BGE-M3 API和Qdrant scroll方法实现（兼容旧版本Qdrant）
"""

import logging
from typing import Any, Dict

import aiohttp
import numpy as np

from core.tools.decorators import tool

logger = logging.getLogger(__name__)


@tool(
    name="vector_search",
    category="vector_search",
    description="向量语义搜索（基于BGE-M3模型，1024维）",
    tags=["search", "vector", "semantic", "bge-m3", "1024dim"]
)
async def vector_search_handler(
    query: str,
    collection: str = "patent_rules_1024",
    top_k: int = 10,
    threshold: float = 0.7
) -> dict[str, Any]:
    """
    向量语义搜索Handler（1024维版本）

    使用BGE-M3 API生成查询向量，然后在Qdrant中使用scroll方法搜索最相似的向量。

    参数:
        query: 查询文本
        collection: 集合名称（必须以_1024结尾）
        top_k: 返回结果数（默认: 10）
        threshold: 相似度阈值（默认: 0.7）

    返回:
        {
            "success": true,
            "query": "...",
            "collection": "...",
            "dimension": 1024,
            "total_results": 10,
            "results": [...]
        }
    """
    try:
        # 参数验证
        if not query:
            return {
                "success": False,
                "error": "缺少必需参数: query"
            }

        # 验证集合名称（必须以_1024结尾）
        if not collection.endswith("_1024"):
            return {
                "success": False,
                "error": f"集合名称必须以_1024结尾，当前: {collection}"
            }

        if top_k <= 0:
            return {
                "success": False,
                "error": "top_k必须大于0"
            }

        if not (0.0 <= threshold <= 1.0):
            return {
                "success": False,
                "error": "threshold必须在0.0到1.0之间"
            }

        # 1. 使用BGE-M3 API生成查询向量
        async with aiohttp.ClientSession() as session:
            payload = {
                "input": [query],
                "model": "bge-m3"
            }

            async with session.post(
                "http://127.0.0.1:8766/v1/embeddings",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"BGE-M3 API错误: {response.status} - {error_text}"
                    }

                data = await response.json()

                if "data" not in data or len(data["data"]) == 0:
                    return {
                        "success": False,
                        "error": "BGE-M3 API返回数据格式错误"
                    }

                query_vector = np.array(data["data"][0]["embedding"])

                # 验证向量维度
                if len(query_vector) != 1024:
                    return {
                        "success": False,
                        "error": f"查询向量维度错误: {len(query_vector)}（期望1024）"
                    }

        # 2. 在Qdrant中搜索（使用scroll方法）
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(host="localhost", port=6333)

            # 使用scroll方法获取所有点（带向量）
            all_points, _ = client.scroll(
                collection_name=collection,
                limit=top_k * 10,  # 获取更多点以提高搜索质量
                with_payload=True,
                with_vectors=True
            )

            if not all_points:
                return {
                    "success": True,
                    "query": query,
                    "collection": collection,
                    "dimension": 1024,
                    "total_results": 0,
                    "results": [],
                    "note": "集合为空"
                }

            # 计算余弦相似度
            similarities = []
            query_norm = np.linalg.norm(query_vector)

            for point in all_points:
                if hasattr(point.vector, '__len__'):
                    point_vector = np.array(point.vector)

                    # 确保向量维度一致
                    if len(point_vector) != 1024:
                        logger.warning(f"跳过维度不是1024的点: {point.id}, 维度: {len(point_vector)}")
                        continue

                    # 计算余弦相似度
                    point_norm = np.linalg.norm(point_vector)
                    if query_norm > 0 and point_norm > 0:
                        similarity = float(np.dot(query_vector, point_vector) / (query_norm * point_norm))
                    else:
                        similarity = 0.0

                    # 只保留高于阈值的
                    if similarity >= threshold:
                        similarities.append({
                            "id": str(point.id),
                            "score": similarity,
                            "payload": point.payload
                        })

            # 按相似度排序并取top_k
            similarities.sort(key=lambda x: x["score"], reverse=True)
            results = similarities[:top_k]

            return {
                "success": True,
                "query": query,
                "collection": collection,
                "dimension": 1024,
                "total_results": len(results),
                "results": results,
                "method": "scroll + cosine_similarity"
            }

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Qdrant查询失败: {e}", exc_info=True)

            # 如果是集合不存在的错误
            if "not found" in error_msg or "collection" in error_msg:
                return {
                    "success": False,
                    "error": f"集合不存在: {collection}",
                    "hint": "请先创建该集合或使用其他集合名称"
                }
            raise

    except Exception as e:
        logger.error(f"向量搜索失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "collection": collection
        }


__all__ = ["vector_search_handler"]
