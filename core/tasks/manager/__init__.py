#!/usr/bin/env python3
from __future__ import annotations

"""
任务管理器系统 - P1阶段核心模块
Task Manager System - P1 Phase Core Module

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

此模块提供统一的任务管理接口，集成P0系统的Skills、Plugins和会话记忆系统。
"""

from .exceptions import (
    TaskDependencyError,
    TaskManagerError,
    TaskNotFoundError,
    TaskValidationError,
)
from .manager import TaskManager, create_task, get_task_manager
from .models import (
    Task,
    TaskDependency,
    TaskMetrics,
    TaskPriority,
    TaskResult,
    TaskStatus,
)
from .scheduler import TaskScheduler
from .storage import FileTaskStorage, TaskStorage

__all__ = [
    "TaskManager",
    "get_task_manager",
    "create_task",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskDependency",
    "TaskResult",
    "TaskMetrics",
    "TaskScheduler",
    "TaskStorage",
    "FileTaskStorage",
    "TaskManagerError",
    "TaskNotFoundError",
    "TaskDependencyError",
    "TaskValidationError",
]

__version__ = "1.0.0"
