"""
状态持久化模块
State Persistence Module

提供自动状态持久化能力:
1. StateModule - 状态模块基类
2. StatePersistenceManager - 持久化管理器
3. CheckpointManager - 检查点管理器

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""


from __future__ import annotations
__all__ = ["CheckpointManager", "PersistenceStrategy", "StateModule", "StatePersistenceManager"]

__version__ = "1.0.0"
