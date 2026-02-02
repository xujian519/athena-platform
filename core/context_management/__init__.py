#!/usr/bin/env python3
"""
上下文管理模块
Context Management Module - 任务上下文的持久化和恢复

这个模块提供了任务执行过程中的上下文管理功能,包括:
- 任务上下文的创建和保存
- 步骤级别的上下文追踪
- 全局变量的持久化
- 任务中断后的恢复

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

from .task_context_manager import (
    ContextStatus,
    StepContext,
    TaskContext,
    TaskContextManager,
    create_task_context,
    resume_task_context,
)

__all__ = [
    "ContextStatus",
    "StepContext",
    "TaskContext",
    "TaskContextManager",
    "create_task_context",
    "resume_task_context",
]
