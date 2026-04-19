#!/usr/bin/env python3
from __future__ import annotations
"""
协作模式实现 - 公共接口
Collaboration Patterns Implementation - Public Interface

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0

此模块提供协作模式的公共接口导出。
"""

# 导入基础类
from .base import CollaborationPattern

# 导入工厂类
from .factory import CollaborationPatternFactory

# 导入具体模式实现
from .patterns import (
    ConsensusCollaborationPattern,
    HierarchicalCollaborationPattern,
    ParallelCollaborationPattern,
    SequentialCollaborationPattern,
)

# 导出公共接口
__all__ = [
    # 基础类
    "CollaborationPattern",
    # 具体模式
    "SequentialCollaborationPattern",
    "ParallelCollaborationPattern",
    "HierarchicalCollaborationPattern",
    "ConsensusCollaborationPattern",
    # 工厂类
    "CollaborationPatternFactory",
]
