"""
Coordinator模式 - 数据类型定义

定义协调器系统使用的所有数据类型。
"""

from typing import Protocol, Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


class AgentStatus(str, Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConflictType(str, Enum):
    """冲突类型枚举"""
    RESOURCE = "resource"  # 资源冲突
    TIMING = "timing"  # 时序冲突
    DEPENDENCY = "dependency"  # 依赖冲突
    CAPACITY = "capacity"  # 容量冲突


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    name: str
    status: AgentStatus = AgentStatus.IDLE
    capabilities: list[str] = field(default_factory=list)
    current_tasks: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return self.status == AgentStatus.IDLE

    def can_handle_task(self, task_type: str) -> bool:
        """检查Agent是否能处理指定类型的任务"""
        return task_type in self.capabilities or "*" in self.capabilities


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    task_type: str
    priority: TaskPriority = TaskPriority.MEDIUM
    payload: dict[str, Any] = field(default_factory=dict)
    required_capabilities: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    timeout: int = 300  # 超时时间（秒）
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    status: str = "pending"

    def is_ready(self, completed_tasks: set[str]) -> bool:
        """检查任务是否就绪（所有依赖已完成）"""
        return all(dep in completed_tasks for dep in self.dependencies)


@dataclass
class ConflictInfo:
    """冲突信息"""
    conflict_id: str
    conflict_type: ConflictType
    agents_involved: list[str]
    tasks_involved: list[str]
    description: str
    severity: str = "medium"  # low, medium, high, critical
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class SchedulingResult:
    """调度结果"""
    success: bool
    task_id: str
    assigned_agent: Optional[str] = None
    reason: str = ""
    conflicts: list[ConflictInfo] = field(default_factory=list)
    scheduled_at: datetime = field(default_factory=datetime.now)


# 协议定义
class AgentProtocol(Protocol):
    """Agent协议接口"""

    agent_id: str
    status: AgentStatus
    capabilities: list[str]

    async def execute_task(self, task: TaskInfo) -> Any:
        """执行任务"""
        ...

    async def get_status(self) -> AgentStatus:
        """获取状态"""
        ...


class SchedulerProtocol(Protocol):
    """调度器协议接口"""

    async def schedule(self, task: TaskInfo, available_agents: list[AgentInfo]) -> SchedulingResult:
        """调度任务"""
        ...

    async def get_queue_status(self) -> dict[str, int]:
        """获取队列状态"""
        ...
