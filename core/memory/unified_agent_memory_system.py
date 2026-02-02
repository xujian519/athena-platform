#!/usr/bin/env python3
"""
统一Agent记忆系统 - 向后兼容重定向
Unified Agent Memory System - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.memory.unified_memory

作者: Athena平台团队
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0-refactored

--- 迁移指南 ---

旧导入:
  from core.memory.unified_agent_memory_system import UnifiedAgentMemorySystem

新导入:
  from core.memory.unified_memory import UnifiedAgentMemorySystem
  # 或
  from core.memory.unified_memory import (
      UnifiedAgentMemorySystem,
      MemoryType,
      AgentType,
      MemoryTier,
  )

--- 文件结构 ---

core/memory/unified_memory/
├── __init__.py              # 公共接口导出 (62行)
├── types.py                 # 数据类型定义 (175行)
├── utils.py                 # 工具函数 (204行)
└── core.py                  # 核心实现 (1880行)

总计: ~2321行 (原文件: 2350行)

--- 使用示例 ---

# 推荐导入方式
from core.memory.unified_memory import (
    UnifiedAgentMemorySystem,
    MemoryType,
    AgentType,
)

# 初始化记忆系统
memory_system = UnifiedAgentMemorySystem()

# 存储记忆
await memory_system.store_memory(
    agent_id="xiaonuo_pisces",
    content="用户询问了专利检索相关的问题",
    memory_type=MemoryType.CONVERSATION
)

# 检索记忆
memories = await memory_system.retrieve_memories(
    agent_id="xiaonuo_pisces",
    query="专利检索",
    limit=5
)

"""

import logging
import warnings

logger = logging.getLogger(__name__)

# 向后兼容重定向
from core.memory.unified_memory import (  # type: ignore
    AGENT_REGISTRY,
    AgentIdentity,
    AgentType,
    CacheStatistics,
    MemoryItem,
    MemoryTier,
    MemoryType,
    UnifiedAgentMemorySystem,
)

# 发出迁移警告
warnings.warn(
    "unified_agent_memory_system.py 已重构，请使用新导入路径: "
    "from core.memory.unified_memory import UnifiedAgentMemorySystem",
    DeprecationWarning,
    stacklevel=2,
)

logger.info("⚠️  使用已重构的unified_agent_memory_system.py，建议更新导入路径")

# 导出所有公共接口以保持向后兼容
__all__ = [
    # 核心类
    "UnifiedAgentMemorySystem",
    # 数据模型
    "AgentType",
    "MemoryType",
    "MemoryTier",
    "AgentIdentity",
    "MemoryItem",
    "CacheStatistics",
    "AGENT_REGISTRY",
]
