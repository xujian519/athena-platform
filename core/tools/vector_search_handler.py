#!/usr/bin/env python3
"""
向量搜索Handler（1024维度版本）
"""

from typing import Dict, Any
from core.tools.decorators import tool

@tool(
    name="vector_search",
    category="vector_search",
    description="向量语义搜索（基于BGE-M3模型，1024维）",
    priority="high",
    tags=["search", "vector", "semantic", "bge-m3", "1024dim"]
)
async def vector_search_handler(
    query: str,
    collection: str = "legal_main_1024",
    top_k: int = 10,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    向量语义搜索Handler（1024维版本）

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
        from core.vector.intelligent_vector_manager import IntelligentVectorManager
        from config.vector_config import validate_vector_dimension

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

        # 创建向量管理器
        manager = IntelligentVectorManager()

        # 执行搜索
        results = await manager.search_vector(
            query=query,
            collection_name=collection,
            limit=top_k,
            score_threshold=threshold
        )

        # 验证结果向量维度（如果有）
        for result in results:
            if "vector" in result:
                vector = result["vector"]
                if not validate_vector_dimension(vector):
                    return {
                        "success": False,
                        "error": f"结果向量维度错误: {len(vector)}（期望1024）"
                    }

        return {
            "success": True,
            "query": query,
            "collection": collection,
            "dimension": 1024,
            "total_results": len(results),
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "collection": collection
        }
