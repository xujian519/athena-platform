#!/usr/bin/env python3
from __future__ import annotations
"""
Athena自动进化系统
Athena Auto-Evolution System

实现系统的自动进化和优化功能:
- Phase 1: 基础进化 - 参数自动调优
- Phase 2: 智能进化 - 演化算法集成
- Phase 3: 自主进化 - 完全自主运行

作者: Athena平台团队
创建时间: 2026-02-06
版本: v1.0.0
"""

from .evolution_coordinator import EvolutionCoordinator, get_evolution_coordinator
from .types import (
    EvolutionConfig,
    EvolutionPhase,
    EvolutionResult,
    EvolutionStatus,
    EvolutionStrategy,
    MutationType,
)

__all__ = [
    "EvolutionCoordinator",
    "get_evolution_coordinator",
    "EvolutionConfig",
    "EvolutionResult",
    "EvolutionPhase",
    "EvolutionStatus",
    "MutationType",
    "EvolutionStrategy",
]
