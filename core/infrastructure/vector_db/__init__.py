#!/usr/bin/env python3

"""
Neo4j图数据库模块
Neo4j Graph Database Module

提供统一的Neo4j客户端接口

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

from core.neo4j.neo4j_graph_client import (
    GraphClient,
    Neo4jClient,
    Neo4jConfig,
    get_graph_client,
    get_neo4j_client,
)

__all__ = ["GraphClient", "Neo4jClient", "Neo4jConfig", "get_graph_client", "get_neo4j_client"]

__version__ = "2.0.0"

