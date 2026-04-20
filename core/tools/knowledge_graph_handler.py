#!/usr/bin/env python3
"""
知识图谱搜索工具处理器

提供基于Neo4j的知识图谱搜索和推理功能。

Author: Athena平台团队
Created: 2026-04-19
Version: 1.0.0
"""

import json
import logging
from typing import Any

# Type hints for type checkers
from typing import Dict, List

logger = logging.getLogger(__name__)


async def knowledge_graph_search_handler(
    query: str,
    query_type: str = "cypher",
    top_k: int = 10,
    return_format: str = "json"
) -> Dict[str, Any]:
    """
    知识图谱搜索处理器

    功能:
    1. 执行Cypher查询（Neo4j查询语言）
    2. 图谱推理（节点关系遍历）
    3. 路径查找（最短路径、所有路径）
    4. 邻居查询（节点邻居发现）
    5. 统计信息（节点数、边数、标签类型）

    Args:
        query: 查询内容
            - Cypher查询: 完整的Cypher语句
            - 自然语言: 需要转换为Cypher（待实现）
        query_type: 查询类型
            - "cypher": Cypher查询（默认）
            - "natural": 自然语言查询（需要LLM转换）
            - "path": 路径查询
            - "neighbors": 邻居查询
            - "stats": 统计信息
        top_k: 返回结果数量限制（默认10）
        return_format: 返回格式
            - "json": JSON格式（默认）
            - "dict": Python字典
            - "raw": 原始Neo4j结果

    Returns:
        Dict[str, Any]: 查询结果
        {
            "success": bool,  # 是否成功
            "results": list,  # 查询结果列表
            "count": int,  # 结果数量
            "execution_time": float,  # 执行时间（秒）
            "query_type": str,  # 查询类型
            "error": str | None  # 错误信息（如果失败）
        }

    Examples:
        # 1. Cypher查询示例
        >>> result = await knowledge_graph_search_handler(
        ...     query="MATCH (n:Patent) RETURN n LIMIT 10",
        ...     query_type="cypher"
        ... )

        # 2. 获取统计信息
        >>> result = await knowledge_graph_search_handler(
        ...     query="",
        ...     query_type="stats"
        ... )

        # 3. 邻居查询
        >>> result = await knowledge_graph_search_handler(
        ...     query="MATCH (n:Patent {id: 'CN123456'}) RETURN n",
        ...     query_type="neighbors"
        ... )
    """
    import time
    from core.knowledge.unified_knowledge_graph import get_knowledge_graph

    start_time = time.time()

    try:
        # 获取知识图谱实例
        kg = await get_knowledge_graph()

        # 根据查询类型执行不同操作
        if query_type == "stats":
            # 获取统计信息
            stats = await kg.get_statistics()

            result = {
                "success": True,
                "results": [
                    {
                        "backend": stats.backend.value,
                        "node_count": stats.node_count,
                        "edge_count": stats.edge_count,
                        "tag_types": stats.tag_types or [],
                        "edge_types": stats.edge_types or [],
                        "is_available": stats.is_available
                    }
                ],
                "count": 1,
                "execution_time": time.time() - start_time,
                "query_type": query_type,
                "error": None
            }

        elif query_type == "cypher":
            # 执行Cypher查询
            if not query:
                raise ValueError("Cypher查询不能为空")

            # 添加LIMIT子句（如果未提供）
            if "LIMIT" not in query.upper() and top_k > 0:
                query = f"{query} LIMIT {top_k}"

            # 执行查询
            results = await kg.execute_query(query)

            # 转换结果为可序列化格式
            serializable_results = []
            for record in results:
                # 将Neo4j Record对象转换为字典
                if hasattr(record, "data"):
                    serializable_results.append(record.data())
                elif isinstance(record, dict):
                    serializable_results.append(record)
                else:
                    # 其他类型，尝试直接序列化
                    serializable_results.append(record)

            result = {
                "success": True,
                "results": serializable_results,
                "count": len(serializable_results),
                "execution_time": time.time() - start_time,
                "query_type": query_type,
                "error": None
            }

        elif query_type == "path":
            # 路径查询（最短路径）
            # 示例: MATCH path = shortestPath((start:Patent {id: 'A'})-[*]-(end:Patent {id: 'B'})) RETURN path
            if not query:
                raise ValueError("路径查询不能为空")

            results = await kg.execute_query(query)

            serializable_results = []
            for record in results:
                if hasattr(record, "data"):
                    serializable_results.append(record.data())
                elif isinstance(record, dict):
                    serializable_results.append(record)
                else:
                    serializable_results.append(record)

            result = {
                "success": True,
                "results": serializable_results,
                "count": len(serializable_results),
                "execution_time": time.time() - start_time,
                "query_type": query_type,
                "error": None
            }

        elif query_type == "neighbors":
            # 邻居查询
            # 先获取目标节点，然后查询其邻居
            if not query:
                raise ValueError("邻居查询不能为空")

            # 构建邻居查询Cypher
            # 假设query是获取目标节点的查询
            neighbor_query = f"""
            WITH ({query}) as target
            MATCH (target)-[r]-(neighbor)
            RETURN DISTINCT neighbor, type(r) as relationship_type, r
            LIMIT {top_k}
            """

            results = await kg.execute_query(neighbor_query)

            serializable_results = []
            for record in results:
                if hasattr(record, "data"):
                    serializable_results.append(record.data())
                elif isinstance(record, dict):
                    serializable_results.append(record)
                else:
                    serializable_results.append(record)

            result = {
                "success": True,
                "results": serializable_results,
                "count": len(serializable_results),
                "execution_time": time.time() - start_time,
                "query_type": query_type,
                "error": None
            }

        elif query_type == "natural":
            # 自然语言查询（需要LLM转换为Cypher）
            raise NotImplementedError(
                "自然语言查询功能尚未实现，请使用Cypher查询。"
                "提示: 可以使用query_type='cypher'直接编写Cypher查询。"
            )

        else:
            raise ValueError(f"不支持的查询类型: {query_type}")

        # 关闭连接
        await kg.close()

        # 根据返回格式返回
        if return_format == "dict":
            return result
        elif return_format == "raw":
            return result["results"]
        else:  # json
            # 确保所有结果都是JSON可序列化的
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            return json.loads(json_str)

    except Exception as e:
        logger.error(f"知识图谱查询失败: {e}", exc_info=True)

        return {
            "success": False,
            "results": [],
            "count": 0,
            "execution_time": time.time() - start_time,
            "query_type": query_type,
            "error": str(e)
        }


# 便捷函数：常用查询模板
async def get_graph_statistics() -> Dict[str, Any]:
    """
    获取知识图谱统计信息

    Returns:
        统计信息字典
    """
    return await knowledge_graph_search_handler(
        query="",
        query_type="stats"
    )


async def search_patents_by_keyword(
    keyword: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    按关键词搜索专利节点

    Args:
        keyword: 关键词
        limit: 返回数量限制

    Returns:
        搜索结果
    """
    cypher = f"""
    MATCH (n:Patent)
    WHERE n.title CONTAINS '{keyword}'
       OR n.abstract CONTAINS '{keyword}'
       OR n.id CONTAINS '{keyword}'
    RETURN n
    LIMIT {limit}
    """

    return await knowledge_graph_search_handler(
        query=cypher,
        query_type="cypher"
    )


async def find_related_patents(
    patent_id: str,
    relationship_type: str | None = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    查找与指定专利相关的专利

    Args:
        patent_id: 专利ID
        relationship_type: 关系类型（可选，如"CITES"、"SIMILAR_TO"）
        limit: 返回数量限制

    Returns:
        相关专利列表
    """
    if relationship_type:
        cypher = f"""
        MATCH (p1:Patent {{id: '{patent_id}'}})-[r:{relationship_type}]-(p2:Patent)
        RETURN p2, type(r) as relationship_type
        LIMIT {limit}
        """
    else:
        cypher = f"""
        MATCH (p1:Patent {{id: '{patent_id}'}})-[r]-(p2:Patent)
        RETURN p2, type(r) as relationship_type
        LIMIT {limit}
        """

    return await knowledge_graph_search_handler(
        query=cypher,
        query_type="cypher"
    )


async def find_shortest_path(
    start_id: str,
    end_id: str,
    max_depth: int = 5
) -> Dict[str, Any]:
    """
    查找两个节点之间的最短路径

    Args:
        start_id: 起始节点ID
        end_id: 结束节点ID
        max_depth: 最大搜索深度

    Returns:
        路径信息
    """
    cypher = f"""
    MATCH path = shortestPath(
        (start {{id: '{start_id}'}})-[*..{max_depth}]-(end {{id: '{end_id}'}})
    )
    RETURN path, length(path) as path_length
    """

    return await knowledge_graph_search_handler(
        query=cypher,
        query_type="path"
    )


if __name__ == "__main__":
    import asyncio

    async def test():
        """测试知识图谱搜索工具"""
        print("=" * 80)
        print("知识图谱搜索工具测试")
        print("=" * 80)

        # 测试1: 获取统计信息
        print("\n【测试1】获取知识图谱统计信息")
        stats = await get_graph_statistics()
        print(f"后端: {stats['results'][0]['backend']}")
        print(f"节点数: {stats['results'][0]['node_count']}")
        print(f"边数: {stats['results'][0]['edge_count']}")
        print(f"标签类型: {stats['results'][0]['tag_types']}")

        # 测试2: 查询所有节点（限制5个）
        print("\n【测试2】查询前5个节点")
        result = await knowledge_graph_search_handler(
            query="MATCH (n) RETURN n LIMIT 5",
            query_type="cypher"
        )
        print(f"成功: {result['success']}")
        print(f"结果数量: {result['count']}")
        print(f"执行时间: {result['execution_time']:.3f}秒")

        if result['success'] and result['count'] > 0:
            print(f"第一个结果: {result['results'][0]}")

        # 测试3: 搜索专利（假设有Patent标签）
        print("\n【测试3】搜索专利（关键词：AI）")
        result = await search_patents_by_keyword("AI", limit=3)
        print(f"成功: {result['success']}")
        print(f"结果数量: {result['count']}")

    asyncio.run(test())
