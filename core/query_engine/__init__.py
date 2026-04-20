#!/usr/bin/env python3
from __future__ import annotations
"""
Query Engine - 查询引擎系统
Query Engine System

提供统一的跨数据源查询能力，支持PostgreSQL、Redis、Qdrant、Neo4j

作者: Athena平台团队
版本: 1.0.0
"""

from core.query_engine.base import (
    QueryResult,
    QueryStats,
    DataSourceType,
    BaseAdapter,
)
from core.query_engine.types import QueryStatus
from core.query_engine.engine import QueryEngine, QueryOptimizer
from core.query_engine.exceptions import (
    QueryEngineError,
    AdapterNotFoundError,
    QueryExecutionError,
    InvalidQueryError,
)

__all__ = [
    # 核心类
    "QueryEngine",
    "QueryOptimizer",
    "QueryResult",
    "QueryStats",
    "QueryStatus",
    "DataSourceType",
    "BaseAdapter",
    # 异常
    "QueryEngineError",
    "AdapterNotFoundError",
    "QueryExecutionError",
    "InvalidQueryError",
]
