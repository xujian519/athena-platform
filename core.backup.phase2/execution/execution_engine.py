#!/usr/bin/env python3
from __future__ import annotations
"""
执行引擎 - 向后兼容重定向
Execution Engine - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.execution.execution_engine (模块化目录)
"""

import warnings

from .execution_engine import (
    ActionExecutor,
    ActionType,
    ExecutionEngine,
    Task,
    TaskPriority,
    TaskResult,
    TaskScheduler,
    TaskStatus,
    Workflow,
    WorkflowEngine,
)

warnings.warn(
    "execution_engine.py 已重构为模块化目录 core.execution.execution_engine/。",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "ActionExecutor",
    "ActionType",
    "ExecutionEngine",
    "Task",
    "TaskPriority",
    "TaskResult",
    "TaskScheduler",
    "TaskStatus",
    "Workflow",
    "WorkflowEngine",
]
