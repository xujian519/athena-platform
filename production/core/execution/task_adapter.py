#!/usr/bin/env python3
"""
任务模型适配器
Task Model Adapter

将执行引擎的任务模型适配到标准化任务模型

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

from __future__ import annotations
from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..task_models import Task, TaskPriority, TaskResult, TaskStatus, TaskType
from .types import ActionType
from .types import Task as ExecutionTask
from .types import TaskPriority as ExecutionTaskPriority
from .types import TaskStatus as ExecutionTaskStatus


class TaskAdapter:
    """任务模型适配器"""

    @staticmethod
    def to_standard_task(execution_task: ExecutionTask) -> Task:
        """
        将执行引擎任务转换为标准任务

        Args:
            execution_task: 执行引擎任务对象

        Returns:
            Task: 标准任务对象
        """
        # 转换任务类型(action_type 现在是 str,不是 ActionType)
        task_type = TaskAdapter._convert_action_type_str(execution_task.action_type)

        # 转换优先级
        priority = TaskAdapter._convert_priority(execution_task.priority)

        # 转换状态
        status = (
            TaskAdapter._convert_status(execution_task.status)
            if hasattr(execution_task, "status")
            else TaskStatus.PENDING
        )

        # 创建标准任务
        standard_task = Task(
            id=execution_task.task_id,
            name=execution_task.name,
            task_type=task_type,
            action=execution_task.action_type if hasattr(execution_task, "action_type") else "",
            action_data=execution_task.action_data,
            priority=priority,
            status=status,
            agent_id=execution_task.metadata.get("agent_id", ""),
            retry_count=execution_task.retry_count,
            max_retries=execution_task.max_retries,
            dependencies=[
                TaskAdapter._create_dependency(dep) for dep in execution_task.dependencies
            ],
            metadata=execution_task.metadata,
            created_at=execution_task.created_at,
            due_at=getattr(execution_task, "scheduled_at", None),  # 安全访问 scheduled_at
        )

        return standard_task

    @staticmethod
    def from_standard_task(standard_task: Task) -> ExecutionTask:
        """
        将标准任务转换为执行引擎任务

        Args:
            standard_task: 标准任务对象

        Returns:
            ExecutionTask: 执行引擎任务对象
        """
        # 转换动作类型(TaskType -> str)
        action_type_str = TaskAdapter._convert_task_type_to_str(standard_task.task_type)

        # 转换优先级
        priority = TaskAdapter._convert_task_priority(standard_task.priority)

        # 创建执行引擎任务
        execution_task = ExecutionTask(
            task_id=standard_task.id,
            name=standard_task.name,
            action_type=action_type_str,
            action_data=standard_task.action_data,
            priority=priority,
            timeout=standard_task.metadata.get("timeout"),
            retry_count=standard_task.retry_count,
            max_retries=standard_task.max_retries,
            dependencies=[dep.task_id for dep in standard_task.dependencies],
            metadata={
                **standard_task.metadata,
                "agent_id": standard_task.agent_id,
                "task_type": standard_task.task_type.value,
            },
            # 注意:ExecutionTask (types.py) 没有 scheduled_at 参数
        )

        return execution_task

    @staticmethod
    def _convert_action_type_str(action_type_str: str) -> TaskType:
        """转换动作类型字符串到任务类型"""
        # action_type_str 现在是字符串,映射到 TaskType
        mapping = {
            "function": TaskType.FUNCTION_CALL,
            "api_call": TaskType.API_CALL,
            "workflow": TaskType.WORKFLOW,
            "command": TaskType.FUNCTION_CALL,
            "file_operation": TaskType.FUNCTION_CALL,
            "database": TaskType.FUNCTION_CALL,
            "http_request": TaskType.API_CALL,
            "custom": TaskType.FUNCTION_CALL,
        }
        return mapping.get(action_type_str, TaskType.FUNCTION_CALL)

    @staticmethod
    def _convert_task_type_to_str(task_type: TaskType) -> str:
        """转换任务类型到动作类型字符串"""
        mapping = {
            TaskType.FUNCTION_CALL: "function",
            TaskType.API_CALL: "api_call",
            TaskType.WORKFLOW: "workflow",
            TaskType.BATCH: "custom",
            TaskType.SCHEDULED: "custom",
            TaskType.REAL_TIME: "function",
        }
        return mapping.get(task_type, "function")

    @staticmethod
    def _convert_action_type(action_type: ActionType) -> TaskType:
        """转换动作类型到任务类型"""
        mapping = {
            ActionType.FUNCTION: TaskType.FUNCTION_CALL,
            ActionType.API_CALL: TaskType.API_CALL,
            ActionType.WORKFLOW: TaskType.WORKFLOW,
            ActionType.COMMAND: TaskType.FUNCTION_CALL,
            ActionType.FILE_OPERATION: TaskType.FUNCTION_CALL,
            ActionType.DATABASE: TaskType.FUNCTION_CALL,
            ActionType.HTTP_REQUEST: TaskType.API_CALL,
            ActionType.CUSTOM: TaskType.FUNCTION_CALL,
        }
        return mapping.get(action_type, TaskType.FUNCTION_CALL)

    @staticmethod
    def _convert_task_type(task_type: TaskType) -> ActionType:
        """转换任务类型到动作类型"""
        mapping = {
            TaskType.FUNCTION_CALL: ActionType.FUNCTION,
            TaskType.API_CALL: ActionType.API_CALL,
            TaskType.WORKFLOW: ActionType.WORKFLOW,
            TaskType.BATCH: ActionType.CUSTOM,
            TaskType.SCHEDULED: ActionType.CUSTOM,
            TaskType.REAL_TIME: ActionType.FUNCTION,
        }
        return mapping.get(task_type, ActionType.FUNCTION)

    @staticmethod
    def _convert_priority(priority: ExecutionTaskPriority) -> TaskPriority:
        """转换优先级"""
        # ExecutionTaskPriority 没有 URGENT,使用 CRITICAL 代替
        mapping = {
            ExecutionTaskPriority.LOW: TaskPriority.LOW,
            ExecutionTaskPriority.NORMAL: TaskPriority.NORMAL,
            ExecutionTaskPriority.HIGH: TaskPriority.HIGH,
            # ExecutionTaskPriority 没有 URGENT,映射到 CRITICAL
            ExecutionTaskPriority.CRITICAL: TaskPriority.CRITICAL,
        }
        return mapping.get(priority, TaskPriority.NORMAL)

    @staticmethod
    def _convert_task_priority(priority: TaskPriority) -> ExecutionTaskPriority:
        """转换任务优先级到执行引擎优先级"""
        # TaskPriority 有 URGENT,但 ExecutionTaskPriority 没有,映射到 CRITICAL
        mapping = {
            TaskPriority.LOW: ExecutionTaskPriority.LOW,
            TaskPriority.NORMAL: ExecutionTaskPriority.NORMAL,
            TaskPriority.HIGH: ExecutionTaskPriority.HIGH,
            # TaskPriority.URGENT 映射到 CRITICAL(ExecutionTaskPriority 没有 URGENT)
            TaskPriority.URGENT: ExecutionTaskPriority.CRITICAL,
            TaskPriority.CRITICAL: ExecutionTaskPriority.CRITICAL,
        }
        return mapping.get(priority, ExecutionTaskPriority.NORMAL)

    @staticmethod
    def _convert_status(status: ExecutionTaskStatus) -> TaskStatus:
        """转换状态"""
        # ExecutionTaskStatus 没有 RETRYING,映射到 PENDING
        mapping = {
            ExecutionTaskStatus.PENDING: TaskStatus.PENDING,
            ExecutionTaskStatus.RUNNING: TaskStatus.RUNNING,
            ExecutionTaskStatus.COMPLETED: TaskStatus.COMPLETED,
            ExecutionTaskStatus.FAILED: TaskStatus.FAILED,
            ExecutionTaskStatus.CANCELLED: TaskStatus.CANCELLED,
            ExecutionTaskStatus.TIMEOUT: TaskStatus.TIMEOUT,
            # ExecutionTaskStatus 没有 RETRYING,但 TaskStatus 有
            # 如果需要 RETRYING 状态,需要在调用方处理
        }
        return mapping.get(status, TaskStatus.PENDING)

    @staticmethod
    def _create_dependency(task_id: str) -> Any:
        """创建依赖对象"""
        from ..task_models import TaskDependency

        return TaskDependency(task_id=task_id)

    @staticmethod
    def convert_result(execution_result, task_id: str) -> TaskResult:
        """
        转换执行结果到标准结果

        Args:
            execution_result: 执行引擎结果
            task_id: 任务ID

        Returns:
            TaskResult: 标准任务结果
        """
        if hasattr(execution_result, "status") and hasattr(execution_result, "result"):
            # 执行引擎结果对象
            status = TaskAdapter._convert_status(execution_result.status)
            success = status == TaskStatus.COMPLETED

            return TaskResult(
                success=success,
                data=execution_result.result,
                error=execution_result.error,
                execution_time=execution_result.duration or 0.0,
                metrics=execution_result.metrics if hasattr(execution_result, "metrics") else {},
                timestamp=execution_result.end_time or datetime.now(),
            )
        else:
            # 直接返回结果
            return TaskResult(
                success=True, data=execution_result, execution_time=0.0, timestamp=datetime.now()
            )


# 兼容性装饰器
def ensure_standard_task(func: Callable) -> Callable:
    """
    确保任务参数是标准任务模型的装饰器
    """

    def wrapper(*args, **kwargs) -> Any:
        # 查找任务参数
        if args:
            # 第一个参数通常是self,跳过
            for i, arg in enumerate(args[1:], 1):
                if isinstance(arg, ExecutionTask):
                    # 转换为标准任务
                    args = list(args)
                    args[i] = TaskAdapter.to_standard_task(arg)
                    args = tuple(args)
                    break

        # 检查kwargs中的任务参数
        for key, value in kwargs.items():
            if isinstance(value, ExecutionTask):
                kwargs[key] = TaskAdapter.to_standard_task(value)

        return func(*args, **kwargs)

    return wrapper
