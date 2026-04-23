#!/usr/bin/env python3
# 启用延迟类型注解评估，支持|联合类型语法
from __future__ import annotations

"""
Athena执行系统 - 统一类型定义
Unified Type Definitions for Execution System

这个模块提供了执行系统中所有核心数据类型的统一定义,
避免在多个文件中重复定义相同类型,确保类型一致性。

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.2.0
更新时间: 2026-01-24 - 新增ActionType、ActionExecutor相关类型
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

if False:
    pass


# =============================================================================
# 任务状态和优先级枚举
# =============================================================================


class TaskStatus(Enum):
    """任务状态枚举 - 统一定义"""

    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 超时
    PAUSED = "paused"  # 暂停


class TaskPriority(Enum):
    """任务优先级枚举 - 统一定义"""

    CRITICAL = 1  # 关键任务,最高优先级
    HIGH = 2  # 高优先级
    NORMAL = 3  # 普通优先级
    LOW = 4  # 低优先级
    BACKGROUND = 5  # 后台任务,最低优先级


class TaskType(Enum):
    """任务类型枚举 - 统一定义"""

    FUNCTION_CALL = "function_call"
    API_CALL = "api_call"
    WORKFLOW = "workflow"
    COMMAND = "command"
    FILE_OPERATION = "file_operation"
    CUSTOM = "custom"


# 兼容性别名
Priority = TaskPriority  # 向后兼容


# =============================================================================
# 任务队列和依赖
# =============================================================================

from collections import deque


class TaskQueue:
    """任务队列 - 简单实现"""

    def __init__(self, max_size: int = 10000):
        """
        初始化任务队列

        Args:
            max_size: 队列最大大小
        """
        self._queue: deque = deque()
        self._max_size = max_size

    def enqueue(self, task: Task) -> bool:
        """入队"""
        if len(self._queue) >= self._max_size:
            return False
        self._queue.append(task)
        return True

    def dequeue(self) -> Task | None:
        """出队"""
        return self._queue.popleft() if self._queue else None

    def size(self) -> int:
        """获取队列大小"""
        return len(self._queue)

    def clear(self) -> None:
        """清空队列"""
        self._queue.clear()

    def get_task(self, task_id: str) -> Task | None:
        """根据ID获取任务"""
        for task in self._queue:
            if task.task_id == task_id:
                return task
        return None

    def get_summary(self) -> dict[str, Any]:
        """获取队列摘要"""
        return {
            "size": len(self._queue),
            "max_size": self._max_size,
            "utilization": len(self._queue) / self._max_size if self._max_size > 0 else 0,
        }


@dataclass
class TaskDependency:
    """任务依赖关系"""

    task_id: str
    depends_on: str  # 依赖的任务ID
    dependency_type: str = "hard"  # hard 或 soft 依赖


# =============================================================================
# 任务定义
# =============================================================================


@dataclass
class Task:
    """
    统一的任务定义

    这个类定义了执行系统中所有任务的基本结构,
    提供了任务ID、优先级、状态、依赖关系等核心属性。

    兼容性说明:
    - task_id: 主要字段名,id 属性作为别名提供兼容性
    - timeout: 支持秒数(float)或 timedelta 对象
    """

    task_id: str
    name: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING

    # 执行相关
    function: Callable[..., Any] | None = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    # 依赖和约束
    dependencies: list[str] = field(default_factory=list)
    timeout: Optional[float] = None  # 秒数
    retry_count: int = 0
    max_retries: int = 3

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # 结果和错误
    result: Any = None
    error: Optional[str] = None

    # 进度和元数据
    progress: float = 0.0
    estimated_cpu_usage: float = 0.1
    estimated_memory_usage: float = 0.1
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # 兼容性字段(可选)
    description: str = ""
    action_type: str = "function"  # 用于 execution_engine.py 兼容
    action_data: dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""  # 智能体ID
    action: str = ""  # 动作名称
    parameters: dict[str, Any] = field(default_factory=dict)  # 动作参数
    task_type: str = "function_call"  # 任务类型

    def __post_init__(self):
        """初始化后处理,确保字段类型正确"""
        # 确保 timeout 是 float 类型
        if isinstance(self.timeout, timedelta):
            self.timeout = self.timeout.total_seconds()

    @property
    def id(self) -> str:
        """id 属性别名,用于向后兼容"""
        return self.task_id

    @id.setter
    def id(self, value: str):
        """id 设置器,用于向后兼容"""
        self.task_id = value

    # 兼容 enhanced_execution_engine.py 的方法
    def start(self) -> None:
        """标记任务开始"""
        self.status = TaskStatus.RUNNING
        if self.started_at is None:
            self.started_at = datetime.now()

    def complete(
        self, success: bool, data: Any | None = None, error: Optional[str] = None, execution_time: float = 0.0
    ) -> None:
        """
        标记任务完成

        Args:
            success: 是否成功
            data: 结果数据
            error: 错误信息
            execution_time: 执行时间(秒)
        """
        self.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.result = data
        self.error = error
        self.completed_at = datetime.now()

    def can_start(self, completed_tasks: dict[str, Any]) -> bool:
        """
        检查任务是否可以开始(依赖是否满足)

        Args:
            completed_tasks: 已完成的任务字典

        Returns:
            是否可以开始
        """
        return all(dep_id in completed_tasks for dep_id in self.dependencies)

    def retry(self) -> bool:
        """
        增加重试计数并检查是否可以重试

        Returns:
            是否可以重试
        """
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = TaskStatus.PENDING
            return True
        return False

    def add_dependency(self, task_id: str) -> None:
        """
        添加任务依赖

        Args:
            task_id: 依赖的任务ID
        """
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def remove_dependency(self, task_id: str) -> bool:
        """
        移除任务依赖

        Args:
            task_id: 要移除的依赖任务ID

        Returns:
            是否成功移除
        """
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "priority": self.priority.value,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "tags": self.tags,
            "metadata": self.metadata,
            "error": self.error,
        }


# =============================================================================
# 执行结果定义
# =============================================================================


@dataclass
class ExecutionResult:
    """
    统一的执行结果定义

    封装任务执行的结果信息,包括成功/失败状态、
    返回值、错误信息、执行时间等。
    """

    task_id: str
    task_name: str
    success: bool
    result: Any = None
    error: Exception | Optional[str] = None
    execution_time: float = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "success": self.success,
            "result": str(self.result) if self.result is not None else None,
            "error": str(self.error) if self.error is not None else None,
            "execution_time": self.execution_time,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "metadata": self.metadata,
        }


# =============================================================================
# 并发控制相关
# =============================================================================


class ConcurrencyLevel(Enum):
    """并发级别枚举"""

    TASK = "task"  # 任务级
    RESOURCE = "resource"  # 资源级
    OPERATION = "operation"  # 操作级
    CRITICAL_SECTION = "critical_section"  # 临界区


class LockType(Enum):
    """锁类型枚举"""

    READ = "read"  # 读锁(共享)
    WRITE = "write"  # 写锁(排他)
    UPDATE = "update"  # 更新锁(意向)
    INTENT_SHARED = "is"  # 意向共享
    INTENT_EXCLUSIVE = "ix"  # 意向排他


@dataclass
class ResourceRequirement:
    """
    资源需求定义

    定义任务执行所需的各类资源数量。
    """

    cpu_cores: float = 1.0
    memory_mb: float = 512.0
    disk_io_mb_s: float = 10.0
    network_mbps: float = 1.0
    gpu_memory_mb: float = 0.0


@dataclass
class ResourceUsage:
    """
    资源使用情况定义

    记录当前系统资源的实际使用情况。
    """

    cpu_cores: float = 0.0
    memory_mb: float = 0.0
    disk_io_mb_s: float = 0.0
    network_mbps: float = 0.0
    gpu_memory_mb: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# 工作流相关
# =============================================================================


class WorkflowStatus(Enum):
    """工作流状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ExecutionMode(Enum):
    """执行模式枚举"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    CONDITIONAL = "conditional"  # 条件执行


# =============================================================================
# 统计信息相关
# =============================================================================


@dataclass
class ExecutionStatistics:
    """
    执行统计信息

    记录系统执行过程中的各种统计数据。
    """

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0

    avg_wait_time: float = 0.0
    avg_execution_time: float = 0.0

    active_tasks: int = 0
    queued_tasks: int = 0

    total_execution_time: float = 0.0
    parallel_efficiency: float = 0.0

    throughput_per_second: float = 0.0

    resource_usage: dict[str, float] = field(default_factory=dict)
    lock_contentions: int = 0
    deadlocks_detected: int = 0
    starvations_detected: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "cancelled_tasks": self.cancelled_tasks,
            "avg_wait_time": self.avg_wait_time,
            "avg_execution_time": self.avg_execution_time,
            "active_tasks": self.active_tasks,
            "queued_tasks": self.queued_tasks,
            "total_execution_time": self.total_execution_time,
            "parallel_efficiency": self.parallel_efficiency,
            "throughput_per_second": self.throughput_per_second,
            "resource_usage": self.resource_usage,
            "lock_contentions": self.lock_contentions,
            "deadlocks_detected": self.deadlocks_detected,
            "starvations_detected": self.starvations_detected,
        }


# =============================================================================
# 异常定义
# =============================================================================


class ExecutionError(Exception):
    """执行错误基类"""

    pass


class TaskTimeoutError(ExecutionError):
    """任务超时错误"""

    pass


class TaskExecutionError(ExecutionError):
    """任务执行错误"""

    pass


class ResourceUnavailableError(ExecutionError):
    """资源不可用错误"""

    pass


class DeadlockDetectedError(ExecutionError):
    """死锁检测错误"""

    pass


class DependencyCycleError(ExecutionError):
    """依赖循环错误"""

    pass


# =============================================================================
# 动作类型枚举
# =============================================================================


class ActionType(Enum):
    """动作类型枚举 - 支持多种执行模式"""

    COMMAND = "command"  # 命令执行
    FUNCTION = "function"  # 函数调用
    API_CALL = "api_call"  # API调用
    FILE_OPERATION = "file_operation"  # 文件操作
    DATABASE = "database"  # 数据库操作
    HTTP_REQUEST = "http_request"  # HTTP请求
    WORKFLOW = "workflow"  # 工作流
    CUSTOM = "custom"  # 自定义动作


# =============================================================================
# 任务结果扩展
# =============================================================================


@dataclass
class TaskResult:
    """
    任务执行结果

    封装任务执行的结果信息,包括成功/失败状态、
    返回值、错误信息、执行时间等。
    """

    task_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 导出所有类型
# =============================================================================

__all__ = [
    "ActionType",
    "ConcurrencyLevel",
    "DeadlockDetectedError",
    "DependencyCycleError",
    # 异常
    "ExecutionError",
    "ExecutionMode",
    "ExecutionResult",
    "ExecutionStatistics",
    "LockType",
    "Priority",  # 别名
    "ResourceRequirement",
    "ResourceUnavailableError",
    "ResourceUsage",
    # 数据类
    "Task",
    "TaskDependency",  # 新增
    "TaskExecutionError",
    "TaskPriority",
    "TaskQueue",  # 新增
    "TaskResult",
    # 枚举
    "TaskStatus",
    "TaskTimeoutError",
    "TaskType",  # 新增
    "WorkflowStatus",
]
