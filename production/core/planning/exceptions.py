#!/usr/bin/env python3
from __future__ import annotations
"""
规划系统异常定义
Planning System Exceptions

定义规划系统使用的各种异常类型,提供更精确的错误处理。

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.1.0 "Phase 2 Enhanced"
"""

from typing import Any

# ============================================================================
# 基础异常类
# ============================================================================


class PlanningError(Exception):
    """
    规划系统基础异常类

    所有规划系统异常的基类,提供统一的错误处理接口。
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码(可选)
            details: 额外的错误详情(可选)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def __str__(self) -> str:
        """返回异常的字符串表示"""
        if self.details:
            return f"[{self.error_code}] {self.message} - {self.details}"
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """将异常转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================================
# 任务相关异常
# ============================================================================


class TaskError(PlanningError):
    """任务相关的异常基类"""

    pass


class TaskValidationError(TaskError):
    """
    任务验证失败异常

    当任务输入不符合要求时抛出。
    """

    def __init__(self, message: str, field: str | None = None, value: Any | None = None):
        """
        初始化异常

        Args:
            message: 错误消息
            field: 验证失败的字段名
            value: 验证失败的值
        """
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(message, details=details)


class TaskNotFoundError(TaskError):
    """
    任务未找到异常

    当尝试访问不存在的任务时抛出。
    """

    def __init__(self, task_id: str):
        """
        初始化异常

        Args:
            task_id: 未找到的任务ID
        """
        super().__init__(message=f"任务未找到: {task_id}", details={"task_id": task_id})
        self.task_id = task_id


class TaskExecutionError(TaskError):
    """
    任务执行异常

    当任务执行过程中发生错误时抛出。
    """

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        step: int | None = None,
        cause: Exception | None = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            task_id: 任务ID
            step: 失败的步骤
            cause: 原始异常
        """
        details = {}
        if task_id:
            details["task_id"] = task_id
        if step is not None:
            details["step"] = step
        if cause:
            details["cause"] = str(cause)

        super().__init__(message, details=details)
        self.task_id = task_id
        self.step = step
        self.cause = cause


# ============================================================================
# 复杂度分析异常
# ============================================================================


class ComplexityAnalysisError(PlanningError):
    """
    复杂度分析异常

    当复杂度分析失败时抛出。
    """

    def __init__(
        self, message: str, task_id: str | None = None, analysis_stage: str | None = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            task_id: 任务ID
            analysis_stage: 分析阶段
        """
        details = {}
        if task_id:
            details["task_id"] = task_id
        if analysis_stage:
            details["analysis_stage"] = analysis_stage

        super().__init__(message, details=details)


# ============================================================================
# 策略相关异常
# ============================================================================


class StrategyError(PlanningError):
    """策略相关的异常基类"""

    pass


class StrategyNotFoundError(StrategyError):
    """
    策略未找到异常

    当请求的策略不存在时抛出。
    """

    def __init__(self, strategy_name: str):
        """
        初始化异常

        Args:
            strategy_name: 未找到的策略名称
        """
        super().__init__(
            message=f"策略未找到: {strategy_name}", details={"strategy": strategy_name}
        )
        self.strategy_name = strategy_name


class StrategyExecutionError(StrategyError):
    """
    策略执行异常

    当策略执行失败时抛出。
    """

    def __init__(
        self, message: str, strategy: str | None = None, cause: Exception | None = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            strategy: 策略名称
            cause: 原始异常
        """
        details = {}
        if strategy:
            details["strategy"] = strategy
        if cause:
            details["cause"] = str(cause)

        super().__init__(message, details=details)
        self.strategy = strategy
        self.cause = cause


class StrategySelectionError(StrategyError):
    """
    策略选择异常

    当无法为任务选择合适的策略时抛出。
    """

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        available_strategies: list | None = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            task_id: 任务ID
            available_strategies: 可用策略列表
        """
        details = {}
        if task_id:
            details["task_id"] = task_id
        if available_strategies:
            details["available_strategies"] = available_strategies

        super().__init__(message, details=details)


# ============================================================================
# 工作流相关异常
# ============================================================================


class WorkflowError(PlanningError):
    """工作流相关的异常基类"""

    pass


class WorkflowNotFoundError(WorkflowError):
    """
    工作流未找到异常

    当请求的工作流不存在时抛出。
    """

    def __init__(self, workflow_id: str):
        """
        初始化异常

        Args:
            workflow_id: 未找到的工作流ID
        """
        super().__init__(
            message=f"工作流未找到: {workflow_id}", details={"workflow_id": workflow_id}
        )
        self.workflow_id = workflow_id


class WorkflowValidationError(WorkflowError):
    """
    工作流验证异常

    当工作流验证失败时抛出。
    """

    def __init__(
        self,
        message: str,
        workflow_id: str | None = None,
        validation_errors: list | None = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            workflow_id: 工作流ID
            validation_errors: 验证错误列表
        """
        details = {}
        if workflow_id:
            details["workflow_id"] = workflow_id
        if validation_errors:
            details["validation_errors"] = validation_errors

        super().__init__(message, details=details)


class WorkflowExecutionError(WorkflowError):
    """
    工作流执行异常

    当工作流执行失败时抛出。
    """

    def __init__(
        self,
        message: str,
        workflow_id: str | None = None,
        failed_step: int | None = None,
        cause: Exception | None = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            workflow_id: 工作流ID
            failed_step: 失败的步骤
            cause: 原始异常
        """
        details = {}
        if workflow_id:
            details["workflow_id"] = workflow_id
        if failed_step is not None:
            details["failed_step"] = failed_step
        if cause:
            details["cause"] = str(cause)

        super().__init__(message, details=details)
        self.workflow_id = workflow_id
        self.failed_step = failed_step
        self.cause = cause


# ============================================================================
# 性能跟踪异常
# ============================================================================


class PerformanceTrackingError(PlanningError):
    """
    性能跟踪异常

    当性能跟踪操作失败时抛出。
    """

    def __init__(
        self, message: str, metric_name: str | None = None, operation: str | None = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            metric_name: 指标名称
            operation: 操作类型
        """
        details = {}
        if metric_name:
            details["metric_name"] = metric_name
        if operation:
            details["operation"] = operation

        super().__init__(message, details=details)


# ============================================================================
# 配置异常
# ============================================================================


class ConfigurationError(PlanningError):
    """
    配置错误异常

    当规划系统配置不正确时抛出。
    """

    def __init__(
        self, message: str, config_key: str | None = None, config_value: Any | None = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            config_key: 配置键
            config_value: 配置值
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)

        super().__init__(message, details=details)


# ============================================================================
# 导出所有异常类
# ============================================================================

__all__ = [
    # 复杂度分析
    "ComplexityAnalysisError",
    # 配置
    "ConfigurationError",
    # 性能跟踪
    "PerformanceTrackingError",
    # 基础异常
    "PlanningError",
    # 策略相关
    "StrategyError",
    "StrategyExecutionError",
    "StrategyNotFoundError",
    "StrategySelectionError",
    # 任务相关
    "TaskError",
    "TaskExecutionError",
    "TaskNotFoundError",
    "TaskValidationError",
    # 工作流相关
    "WorkflowError",
    "WorkflowExecutionError",
    "WorkflowNotFoundError",
    "WorkflowValidationError",
]
