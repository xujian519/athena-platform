#!/usr/bin/env python3
from __future__ import annotations

"""
任务管理器异常类
Task Manager Exceptions

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0
"""

from typing import Any


class TaskManagerError(Exception):
    """任务管理器基础异常类"""

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """初始化异常

        Args:
            message: 错误消息
            task_id: 关联的任务ID
            details: 错误详情
        """
        self.message = message
        self.task_id = task_id
        self.details = details or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        if self.task_id:
            return f"[Task {self.task_id}] {self.message}"
        return self.message


class TaskNotFoundError(TaskManagerError):
    """任务未找到异常"""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"任务不存在: {task_id}",
            task_id=task_id,
        )


class TaskDependencyError(TaskManagerError):
    """任务依赖异常"""

    def __init__(
        self,
        task_id: str,
        dependency_id: str | None = None,
        reason: str = "",
    ):
        super().__init__(
            message=f"依赖错误: {reason}" if reason else "任务依赖错误",
            task_id=task_id,
            details={"dependency_id": dependency_id} if dependency_id else None,
        )


class TaskValidationError(TaskManagerError):
    """任务验证异常"""

    def __init__(
        self,
        task_id: str | None = None,
        field: str | None = None,
        reason: str = "",
    ):
        super().__init__(
            message=f"验证失败: {reason}" if reason else "任务验证失败",
            task_id=task_id,
            details={"field": field} if field else None,
        )


class TaskExecutionError(TaskManagerError):
    """任务执行异常"""

    def __init__(
        self,
        task_id: str,
        executor: str | None = None,
        reason: str = "",
    ):
        super().__init__(
            message=f"执行失败: {reason}" if reason else "任务执行失败",
            task_id=task_id,
            details={"executor": executor} if executor else None,
        )


class TaskStorageError(TaskManagerError):
    """任务存储异常"""

    def __init__(
        self,
        operation: str,
        reason: str = "",
    ):
        super().__init__(
            message=f"存储操作失败 ({operation}): {reason}" if reason else f"存储操作失败: {operation}",
            details={"operation": operation},
        )


class TaskSchedulingError(TaskManagerError):
    """任务调度异常"""

    def __init__(
        self,
        task_id: str | None = None,
        reason: str = "",
    ):
        super().__init__(
            message=f"调度失败: {reason}" if reason else "任务调度失败",
            task_id=task_id,
        )
