#!/usr/bin/env python3
"""
双层级架构模块
Dual-Layer Architecture Module - Work Level + Task Level两层架构

这个模块实现了JoyAgent的双层级架构设计:
- Work Level (工作层): 高层规划、任务分解、资源分配、Agent协调
- Task Level (任务层): 低层执行、工具调用、数据处理、结果生成

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

from __future__ import annotations
from .architecture import (
    DualLayerCoordinator,
    LayerType,
    TaskLevelExecution,
    TaskLevelExecutor,
    WorkLevelOrchestrator,
    WorkLevelPlan,
    execute_dual_layer_task,
)

__all__ = [
    "DualLayerCoordinator",
    "LayerType",
    "TaskLevelExecution",
    "TaskLevelExecutor",
    "WorkLevelOrchestrator",
    "WorkLevelPlan",
    "execute_dual_layer_task",
]
