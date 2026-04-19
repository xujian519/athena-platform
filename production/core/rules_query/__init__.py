#!/usr/bin/env python3
"""
规则查询模块
Rules Query Module - 三库联动规则查询系统

这个模块提供了专业任务所需的规则查询功能,包括:
- 向量数据库语义搜索(PostgreSQL pgvector + Qdrant)
- 知识图谱关系推理(NebulaGraph)
- 规则数据库精确查询(PostgreSQL规则库)
- 三库联动综合查询
- 领域优化的查询策略
- 查询缓存优化

作者: Athena平台团队
创建时间: 2026-01-20
版本: v2.0.0 "Real Integration"
"""

# 模拟实现(用于测试和开发)
# 真实实现(连接实际数据库)
from __future__ import annotations
from .real_database_query import (
    QueryCache,
    QueryResult,
    RealKnowledgeGraphQuerier,
    RealRuleDatabaseQuerier,
    RealThreeDatabaseQuery,
    RealVectorDBQuerier,
    clear_query_cache,
    get_cache_stats,
    query_rules_real,
)
from .three_database_query import (
    KnowledgeGraphQuerier,
    QuerySource,
    RuleDatabaseQuerier,
    RuleResult,
    ThreeDatabaseQuery,
    VectorDBQuerier,
    query_rules,
)
from .three_database_query import (
    QueryResult as MockQueryResult,
)

__all__ = [
    "KnowledgeGraphQuerier",
    # 模拟实现(用于测试)
    "MockQueryResult",
    # 真实实现(生产环境)
    "QueryCache",
    "QueryResult",
    # 基础类型
    "QuerySource",
    "RealKnowledgeGraphQuerier",
    "RealRuleDatabaseQuerier",
    "RealThreeDatabaseQuery",
    "RealVectorDBQuerier",
    "RuleDatabaseQuerier",
    "RuleResult",
    "ThreeDatabaseQuery",
    "VectorDBQuerier",
    "clear_query_cache",
    "get_cache_stats",
    "query_rules",
    "query_rules_real",
]
