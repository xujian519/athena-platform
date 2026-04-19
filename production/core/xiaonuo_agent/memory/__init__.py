#!/usr/bin/env python3
"""
记忆模块 (Memory Module)
三层记忆系统

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

from __future__ import annotations
from core.xiaonuo_agent.memory.episodic_memory import (
    EpisodicMemory,
    EpisodicMemoryItem,
    ExperienceType,
    get_episodic_memory,
)
from core.xiaonuo_agent.memory.semantic_memory import (
    KnowledgeType,
    SemanticMemory,
    SemanticMemoryItem,
    get_semantic_memory,
)

__all__ = [
    # 情景记忆
    "EpisodicMemory",
    "EpisodicMemoryItem",
    "ExperienceType",
    "KnowledgeType",
    "MemoryItem",
    # 统一接口
    "MemorySystem",
    "MemoryType",
    # 语义记忆
    "SemanticMemory",
    "SemanticMemoryItem",
    # 工作记忆
    "WorkingMemory",
    "get_episodic_memory",
    "get_memory_system",
    "get_semantic_memory",
    "get_working_memory",
]
