#!/usr/bin/env python3
"""
优化记忆系统 - 向后兼容重定向
Optimized Memory System - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.memory.optimized_memory

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0-refactored

--- 迁移指南 ---

旧导入:
  from core.memory.optimized_memory_system import OptimizedMemorySystem

新导入:
  from core.memory.optimized_memory import OptimizedMemorySystem
  # 或
  from core.memory.optimized_memory.core import OptimizedMemorySystem

--- 文件结构 ---

core/memory/optimized_memory/
├── __init__.py              # 公共接口导出
├── types.py                 # 数据模型 (70行)
├── tier_managers.py         # 分层管理器 (183行)
├── migration.py             # 迁移执行器 (37行)
├── vector_index.py          # 向量索引 (174行)
├── tier_coordinator.py      # 分层协调器 (172行)
└── core.py                  # 核心模块 (548行)

总计: ~1184行 (原文件: 1209行)

--- 使用示例 ---

# 推荐导入方式
from core.memory.optimized_memory import (
    OptimizedMemorySystem,
    MemoryTier,
    DataAccessPattern,
    MemoryData,
    VectorIndexConfig,
    IntelligentTierManager,
    OptimizedVectorIndex,
)

# 或单独导入
from core.memory.optimized_memory import OptimizedMemorySystem

"""

import logging
import warnings

logger = logging.getLogger(__name__)

# 向后兼容重定向
from core.memory.optimized_memory import (  # type: ignore
    ColdTierManager,
    DataAccessPattern,
    HotTierManager,
    IntelligentTierManager,
    MemoryData,
    MemoryTier,
    MigrationExecutor,
    OptimizedMemorySystem,
    OptimizedVectorIndex,
    VectorIndexConfig,
    WarmTierManager,
)

# 发出迁移警告
warnings.warn(
    "optimized_memory_system 已重构，请使用新导入路径: "
    "from core.memory.optimized_memory import OptimizedMemorySystem",
    DeprecationWarning,
    stacklevel=2,
)

logger.info("⚠️  使用已重构的optimized_memory_system，建议更新导入路径")

# 导出所有公共接口以保持向后兼容
__all__ = [
    "OptimizedMemorySystem",
    "MemoryTier",
    "DataAccessPattern",
    "MemoryData",
    "VectorIndexConfig",
    "IntelligentTierManager",
    "OptimizedVectorIndex",
    "HotTierManager",
    "WarmTierManager",
    "ColdTierManager",
    "MigrationExecutor",
]
