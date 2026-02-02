#!/usr/bin/env python3
"""
执行模块 - 统一类型定义
Execution Module - Unified Type Definitions

这是执行模块的唯一类型定义来源，所有其他文件都应从此文件导入类型定义。

作者: Athena AI系统
创建时间: 2026-01-27
版本: 2.0.0
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# =============================================================================
# 枚举定义 - 所有枚举都使用一致的值体系
# =============================================================================


class ActionType(Enum):
    """动作类型 - 支持的所有动作类型"""

    COMMAND = "command"  # Shell命令执行
    FUNCTION = "function"  # 函数调用
    API_CALL = "api_call"  # API调用
    FILE_OPERATION = "file_operation"  # 文件操作
    DATABASE = "database"  # 数据库操作
    HTTP_REQUEST = "http_request"  # HTTP请求
    WORKFLOW = "workflow"  # 工作流执行
    CUSTOM = "custom"  # 自定义动作


class TaskStatus(Enum):
    """任务状态 - 任务生命周期的所有可能状态"""

    PENDING = "pending"  # 等待执行
    QUEUED = "queued"  # 已排队，等待调度
    RUNNING = "running"  # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 执行超时
    PAUSED = "paused"  # 已暂停


class TaskPriority(Enum):
    """任务优先级 - 数值越小优先级越高（用于优先队列排序）

    注意: 这是统一的优先级定义，所有模块都使用这个定义。
    优先级队列会使用枚举值进行排序，值越小优先级越高。
    """

    CRITICAL = 1  # 关键任务，最高优先级
    HIGH = 2  # 高优先级
    NORMAL = 3  # 普通优先级（默认）
    LOW = 4  # 低优先级
    BACKGROUND = 5  # 后台任务，最低优先级


class ResourceType(Enum):
    """资源类型 - 系统资源的分类"""

    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK = "network"
    GPU = "gpu"


# =============================================================================
# 基础任务类型定义
# =============================================================================


@dataclass
class Task:
    """统一任务定义

    这是所有任务类型的基础类，包含任务的核心属性。
    设计为兼容两种使用方式:
    1. 基于动作的任务（使用 action_type 和 action_data）
    2. 基于函数的任务（使用 function, args, kwargs）
    """

    # 基础标识信息
    task_id: str
    name: str

    # 优先级和状态
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING

    # 超时和重试配置
    timeout: float | None = None  # 超时时间（秒）
    max_retries: int = 0  # 最大重试次数
    retry_count: int = 0  # 当前重试次数

    # 依赖关系
    dependencies: list[str] = field(default_factory=list)  # 依赖的任务ID列表

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # 执行结果
    result: Any = None
    error: str | None = None
    progress: float = 0.0  # 0.0 到 1.0

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    # ========================================
    # 方式1: 基于动作的任务（用于 ExecutionEngine）
    # ========================================
    action_type: str | ActionType = ActionType.CUSTOM
    action_data: dict[str, Any] = field(default_factory=dict)

    # ========================================
    # 方式2: 基于函数的任务（用于 OptimizedExecutionModule）
    # ========================================
    function: Callable | None = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)

    # ========================================
    # 资源预估（用于智能调度）
    # ========================================
    estimated_cpu_usage: float = 0.1  # 预估CPU使用率（0.0-1.0）
    estimated_memory_usage: float = 0.1  # 预估内存使用率（0.0-1.0）
    tags: list[str] = field(default_factory=list)  # 任务标签

    # 兼容性属性 - description 字段
    description: str = ""

    def can_start(self, completed_tasks: dict[str, Any]) -> bool:
        """检查任务是否可以开始执行（依赖是否满足）

        Args:
            completed_tasks: 已完成的任务字典 {task_id: task}

        Returns:
            bool: 是否可以开始执行
        """
        for dep_id in self.dependencies:
            if dep_id not in completed_tasks:
                return False
            dep_task = completed_tasks[dep_id]
            if hasattr(dep_task, "status"):
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
        return True

    def start(self) -> None:
        """标记任务开始执行"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def complete(
        self, success: bool, data: Any | None = None, error: str | None = None
    ) -> None:
        """标记任务完成

        Args:
            success: 是否成功
            data: 结果数据
            error: 错误信息
        """
        self.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.result = data
        self.error = error
        self.completed_at = datetime.now()

        # 计算执行时间
        if self.started_at:
            execution_time = (self.completed_at - self.started_at).total_seconds()
            self.metadata["execution_time"] = execution_time

    def retry(self) -> bool:
        """尝试重试任务

        Returns:
            bool: 是否可以重试
        """
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = TaskStatus.PENDING
            return True
        return False


# =============================================================================
# 资源管理类型
# =============================================================================


@dataclass
class ResourceRequirement:
    """资源需求 - 任务执行所需的资源"""

    cpu_cores: float = 1.0
    memory_mb: float = 512.0
    disk_io_mb_s: float = 10.0
    network_mbps: float = 1.0
    gpu_memory_mb: float = 0.0


@dataclass
class ResourceUsage:
    """资源使用情况 - 当前系统的资源使用情况"""

    cpu_cores: float = 0.0
    memory_mb: float = 0.0
    disk_io_mb_s: float = 0.0
    network_mbps: float = 0.0
    gpu_memory_mb: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# 任务队列和结果类型
# =============================================================================


class TaskQueue:
    """任务队列 - 简单的任务队列实现"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._tasks: dict[str, Task] = {}

    def enqueue(self, task: Task) -> bool:
        """入队"""
        if len(self._tasks) >= self.max_size:
            return False
        self._tasks[task.task_id] = task
        return True

    def dequeue(self) -> Task | None:
        """出队 - 按优先级排序"""
        if not self._tasks:
            return None

        # 按优先级排序（priority值越小越优先）
        sorted_tasks = sorted(
            self._tasks.values(),
            key=lambda t: (t.priority.value, t.created_at.timestamp()),
        )
        task = sorted_tasks[0]
        del self._tasks[task.task_id]
        return task

    def get_task(self, task_id: str) -> Task | None:
        """获取任务"""
        return self._tasks.get(task_id)

    def size(self) -> int:
        """队列大小"""
        return len(self._tasks)

    def clear(self) -> None:
        """清空队列"""
        self._tasks.clear()

    def get_summary(self) -> dict[str, Any]:
        """获取队列摘要"""
        return {
            "size": len(self._tasks),
            "max_size": self.max_size,
            "priority_distribution": {
                priority.name: sum(1 for t in self._tasks.values() if t.priority == priority)
                for priority in TaskPriority
            },
        }


@dataclass
class TaskResult:
    """任务执行结果"""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: str | None = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

    # 兼容性字段
    task_name: str = ""
    execution_time: float = 0.0

    def __post_init__(self):
        """初始化后处理"""
        if not self.task_name:
            self.task_name = self.task_id


@dataclass
class TaskType:
    """任务类型枚举（兼容旧代码）"""

    FUNCTION_CALL = "function_call"
    API_CALL = "api_call"
    COMMAND = "command"
    WORKFLOW = "workflow"
    CUSTOM = "custom"


# =============================================================================
# 工作流类型
# =============================================================================


@dataclass
class Workflow:
    """工作流定义"""

    id: str
    name: str
    tasks: list[Task] = field(default_factory=list)
    parallel: bool = False
    max_concurrent: int = 5
    timeout: float | None = None
    created_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# 异常类型
# =============================================================================


class ExecutionError(Exception):
    """执行错误基类"""

    pass


class TaskExecutionError(ExecutionError):
    """任务执行错误"""

    pass


class TaskTimeoutError(ExecutionError):
    """任务超时错误"""

    pass


class DeadlockDetectedError(ExecutionError):
    """死锁检测错误"""

    pass


class DependencyCycleError(ExecutionError):
    """依赖循环错误"""

    pass


class TaskValidationError(ExecutionError):
    """任务验证错误"""

    pass


# =============================================================================
# 导出所有公共类型
# =============================================================================


__all__ = [
    # 枚举
    "ActionType",
    "TaskStatus",
    "TaskPriority",
    "ResourceType",
    # 核心数据类
    "Task",
    "TaskResult",
    "TaskQueue",
    "TaskType",
    "ResourceRequirement",
    "ResourceUsage",
    "Workflow",
    # 异常
    "ExecutionError",
    "TaskExecutionError",
    "TaskTimeoutError",
    "DeadlockDetectedError",
    "DependencyCycleError",
    "TaskValidationError",
]
