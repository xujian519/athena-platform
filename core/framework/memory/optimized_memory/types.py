#!/usr/bin/env python3

"""
优化记忆系统 - 数据模型
Optimized Memory System - Data Models

定义内存分层和向量索引的数据结构

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np


class MemoryTier(Enum):
    """内存层级"""

    HOT = "hot"  # L1: 热点数据 - 快速访问，内存中
    WARM = "warm"  # L2: 温数据 - Redis缓存
    COLD = "cold"  # L3: 冷数据 - 持久化存储
    ARCHIVE = "archive"  # L4: 归档数据 - 长期存储


class DataAccessPattern(Enum):
    """数据访问模式"""

    SEQUENTIAL = "sequential"  # 顺序访问
    RANDOM = "random"  # 随机访问
    TEMPORAL = "temporal"  # 时间相关访问
    FREQUENT = "frequent"  # 频繁访问
    RARE = "rare"  # 稀少访问


@dataclass
class MemoryData:
    """内存数据项"""

    data_id: str
    content: Any
    metadata: dict[str, Any]
    access_pattern: DataAccessPattern
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    tier: MemoryTier = MemoryTier.COLD
    vector_embedding: np.Optional[ndarray] = None
    related_entities: list[str] = field(default_factory=list)
    access_frequency: float = 0.0  # 每分钟访问次数
    decay_factor: float = 0.95  # 衰减因子


@dataclass
class VectorIndexConfig:
    """向量索引配置"""

    index_type: str = "hnsw"  # hnsw, ivf, brute_force
    dimension: int = 1024
    ef_construction: int = 200
    ef_search: int = 50
    max_connections: int = 32
    space: str = "cosine"  # cosine, l2, inner_product

