#!/usr/bin/env python3
from __future__ import annotations
"""
协作模式实现
Collaboration Patterns Implementation

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0

导出所有协作模式实现。
"""

from .consensus import ConsensusCollaborationPattern
from .hierarchical import HierarchicalCollaborationPattern
from .parallel import ParallelCollaborationPattern
from .sequential import SequentialCollaborationPattern

__all__ = [
    "SequentialCollaborationPattern",
    "ParallelCollaborationPattern",
    "HierarchicalCollaborationPattern",
    "ConsensusCollaborationPattern",
]
