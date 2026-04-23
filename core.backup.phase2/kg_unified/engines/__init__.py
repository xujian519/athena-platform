#!/usr/bin/env python3
"""
Knowledge Graph Engines
知识图谱引擎模块

统一的图数据库引擎接口（仅Neo4j）

作者: Athena平台团队
版本: v1.1.0
更新: 2026-04-21 - 移除ArangoDB支持
"""

from .neo4j_engine import (
    # 核心引擎
    Neo4jEngine,
    # 配置
    Neo4jConfig,
    # 枚举类型
    GraphType,
    JudgmentNodeType,
    # 数据类
    GraphNode,
    GraphEdge,
    # 兼容层
    GraphClient,
    NebulaGraphClient,
    Neo4jJudgmentClient,
    # 便捷函数
    get_neo4j_engine,
    get_neo4j_client,
    get_graph_client,
    get_judgment_client,
    get_nebula_client,
    # 全局实例
    graph_engine as neo4j_graph_engine,
)

__all__ = [
    # Neo4j引擎
    "Neo4jEngine",
    "Neo4jConfig",
    "GraphType",
    "JudgmentNodeType",
    "GraphNode",
    "GraphEdge",
    "GraphClient",
    "NebulaGraphClient",
    "Neo4jJudgmentClient",
    "get_neo4j_engine",
    "get_neo4j_client",
    "get_graph_client",
    "get_judgment_client",
    "get_nebula_client",
    "neo4j_graph_engine",
]
