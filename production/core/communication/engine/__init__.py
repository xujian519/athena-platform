"""
通信引擎核心模块
Communication Engine Core Module
"""

from __future__ import annotations
from .dynamic_connection_pool import (
    ConnectionConfig,
    ConnectionStats,
    DynamicConnectionPool,
    PooledConnection,
)

__all__ = [
    "AsyncBatchProcessor",
    "BatchStats",
    "ConnectionConfig",
    "ConnectionStats",
    "DynamicConnectionPool",
    "PooledConnection",
]
