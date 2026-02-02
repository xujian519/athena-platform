#!/usr/bin/env python3
"""
优化记忆系统 - 公共接口
Optimized Memory System - Public Interface

提供智能分层存储和向量索引优化的记忆管理系统

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

# 数据模型
# 核心系统
from core.memory.optimized_memory.core import OptimizedMemorySystem

# 迁移执行器
from core.memory.optimized_memory.migration import MigrationExecutor

# 分层协调器
from core.memory.optimized_memory.tier_coordinator import IntelligentTierManager

# 分层管理器
from core.memory.optimized_memory.tier_managers import (
    ColdTierManager,
    HotTierManager,
    WarmTierManager,
)
from core.memory.optimized_memory.types import (
    DataAccessPattern,
    MemoryData,
    MemoryTier,
    VectorIndexConfig,
)

# 向量索引
from core.memory.optimized_memory.vector_index import OptimizedVectorIndex

__all__ = [
    # 数据模型
    "MemoryTier",
    "DataAccessPattern",
    "MemoryData",
    "VectorIndexConfig",
    # 分层管理器
    "HotTierManager",
    "WarmTierManager",
    "ColdTierManager",
    # 迁移执行器
    "MigrationExecutor",
    # 向量索引
    "OptimizedVectorIndex",
    # 分层协调器
    "IntelligentTierManager",
    # 核心系统
    "OptimizedMemorySystem",
]

__version__ = "2.1.0"
__author__ = "Athena AI System"
