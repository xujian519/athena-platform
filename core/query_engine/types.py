#!/usr/bin/env python3
from __future__ import annotations
"""
Query Engine类型定义
Query Engine Type Definitions

定义查询引擎系统的核心数据类型

作者: Athena平台团队
版本: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DataSourceType(Enum):
    """数据源类型枚举"""

    POSTGRESQL = "postgresql"
    REDIS = "redis"
    QDRANT = "qdrant"
    NEO4J = "neo4j"


class QueryStatus(Enum):
    """查询状态枚举"""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class QueryStats:
    """查询统计信息"""

    execution_time: float = 0.0  # 执行时间（秒）
    rows_affected: int = 0  # 影响行数
    rows_returned: int = 0  # 返回行数
    cache_hit: bool = False  # 缓存命中
    data_source: DataSourceType | None = None  # 数据源类型
    query_complexity: int = 0  # 查询复杂度评分
    memory_used: int = 0  # 内存使用（字节）
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "execution_time": self.execution_time,
            "rows_affected": self.rows_affected,
            "rows_returned": self.rows_returned,
            "cache_hit": self.cache_hit,
            "data_source": self.data_source.value if self.data_source else None,
            "query_complexity": self.query_complexity,
            "memory_used": self.memory_used,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class QueryResult:
    """查询结果"""

    data: list[dict[str, Any]]  # 结果数据
    status: QueryStatus  # 查询状态
    stats: QueryStats  # 统计信息
    error: Optional[str] = None  # 错误信息
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "data": self.data,
            "status": self.status.value,
            "stats": self.stats.to_dict(),
            "error": self.error,
            "metadata": self.metadata,
        }

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status in (QueryStatus.COMPLETED, QueryStatus.CACHED)

    @property
    def row_count(self) -> int:
        """结果行数"""
        return len(self.data)


@dataclass
class CacheKey:
    """缓存键"""

    data_source: DataSourceType
    query: str
    parameters: tuple[Any, ...] = ()
    hash_value: Optional[str] = None

    def __post_init__(self):
        """生成缓存键哈希值"""
        if self.hash_value is None:
            import hashlib

            key_str = f"{self.data_source.value}:{self.query}:{self.parameters}"
            self.hash_value = hashlib.sha256(key_str.encode()).hexdigest()

    def __str__(self) -> str:
        return self.hash_value or ""


@dataclass
class QueryPlan:
    """查询执行计划"""

    steps: list[str]  # 执行步骤
    estimated_cost: float  # 预估成本
    data_sources: list[DataSourceType]  # 涉及的数据源
    parallelizable: bool = False  # 是否可并行执行
    cache_strategy: Optional[str] = None  # 缓存策略

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "steps": self.steps,
            "estimated_cost": self.estimated_cost,
            "data_sources": [ds.value for ds in self.data_sources],
            "parallelizable": self.parallelizable,
            "cache_strategy": self.cache_strategy,
        }
