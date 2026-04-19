#!/usr/bin/env python3
from __future__ import annotations
"""
统一Agent记忆系统 - 统一接口
Unified Agent Memory System - Unified Interface

提供统一的记忆管理功能

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0

使用示例:
    from core.memory.unified_memory import UnifiedAgentMemorySystem

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

# 数据模型
# 核心类
from .core import UnifiedAgentMemorySystem
from .types import (
    AGENT_REGISTRY,
    AgentIdentity,
    AgentType,
    CacheStatistics,
    MemoryItem,
    MemoryTier,
    MemoryType,
)

__all__ = [
    # 数据模型
    "AgentType",
    "MemoryType",
    "MemoryTier",
    "AgentIdentity",
    "MemoryItem",
    "CacheStatistics",
    "AGENT_REGISTRY",
    # 核心类
    "UnifiedAgentMemorySystem",
]

__version__ = "2.1.0"
