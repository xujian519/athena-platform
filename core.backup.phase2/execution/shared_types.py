from __future__ import annotations
"""执行模块共享类型定义"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    CRITICAL = 1  # 关键任务
    HIGH = 2      # 高优先级
    NORMAL = 3    # 普通优先级
    LOW = 4       # 低优先级
    BACKGROUND = 5  # 后台任务
    # 兼容性别名
    URGENT = CRITICAL
    LOW_OLD = LOW


class ActionType(Enum):
    """动作类型枚举"""
    QUERY = "query"
    EXECUTE = "execute"
    TRANSFORM = "transform"
    VALIDATE = "validate"


class ExecutionError(Exception):
    """执行错误基类"""
    pass


class TaskExecutionError(ExecutionError):
    """任务执行错误"""
    pass


class TaskTimeoutError(ExecutionError):
    """任务超时错误"""
    pass


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class ResourceRequirement:
    """资源需求"""
    cpu_cores: int = 1
    memory_mb: float = 100.0
    timeout_seconds: int = 30


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_cores_used: float = 0.0
    memory_mb_used: float = 0.0
    duration_seconds: float = 0.0


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    name: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    action: Callable | None = None
    result: TaskResult | None = None


@dataclass
class TaskQueue:
    """任务队列"""
    tasks: list[Task] = field(default_factory=list)
    max_size: int = 1000

    def enqueue(self, task: Task) -> bool:
        """入队"""
        if len(self.tasks) >= self.max_size:
            return False
        self.tasks.append(task)
        return True

    def dequeue(self) -> Task | None:
        """出队（按优先级排序）"""
        if not self.tasks:
            return None
        self.tasks.sort(key=lambda t: t.priority.value)
        return self.tasks.pop(0)


@dataclass
class Workflow:
    """工作流"""
    workflow_id: str
    name: str
    tasks: list[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
