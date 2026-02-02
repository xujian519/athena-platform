#!/usr/bin/env python3
"""
NebulaGraph图数据库模块 (兼容层)
NebulaGraph Graph Database Module (Compatibility Layer)

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

此模块提供与NebulaGraph客户端兼容的接口，实际使用Neo4j作为后端。
所有类和函数都从 core.neo4j.neo4j_graph_client 重新导出。

迁移说明:
- NebulaGraphConfig -> Neo4jConfig
- Neo4jClient (nebula_graph_client.py) -> Neo4jClient (neo4j_graph_client.py)
- get_neo4j_client() -> get_neo4j_client()

作者: Athena平台团队
更新时间: 2026-01-25 (TD-001: 迁移到Neo4j)
"""

# 从Neo4j模块重新导出所有类和函数
from core.neo4j.neo4j_graph_client import (
    GraphClient,
    Neo4jClient,
    Neo4jConfig,
    get_graph_client,
    get_neo4j_client,
)

# 兼容层: NebulaGraphConfig = Neo4jConfig
NebulaGraphConfig = Neo4jConfig

__all__ = [
    # Neo4j原生导出
    "Neo4jClient",
    "Neo4jConfig",
    "get_neo4j_client",
    "get_graph_client",
    "GraphClient",
    # 兼容层导出
    "NebulaGraphConfig",
]

__version__ = "3.0.0 (TD-001: Neo4j)"
