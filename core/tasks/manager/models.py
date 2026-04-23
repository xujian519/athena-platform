#!/usr/bin/env python3
from __future__ import annotations

"""
任务管理器数据模型
Task Manager Data Models

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待执行
    READY = "ready"  # 准备就绪（依赖已满足）
    ASSIGNED = "assigned"  # 已分配
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消
    BLOCKED = "blocked"  # 阻塞（依赖未满足）
    TIMEOUT = "timeout"  # 超时


class TaskPriority(Enum):
    """任务优先级枚举"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class TaskDependencyType(Enum):
    """任务依赖类型枚举"""

    FINISH_TO_START = "fts"  # 前置任务完成后开始
    START_TO_START = "sts"  # 前置任务开始后开始
    FINISH_TO_FINISH = "ftf"  # 前置任务完成后完成
    START_TO_FINISH = "stf"  # 前置任务开始后完成


@dataclass
class TaskDependency:
    """任务依赖关系"""

    task_id: str  # 依赖的任务ID
    dependency_type: TaskDependencyType = TaskDependencyType.FINISH_TO_START
    required: bool = True  # 是否必须依赖


@dataclass
class TaskResult:
    """任务执行结果"""

    success: bool  # 是否成功
    data: Optional[dict[str, Any]] = None  # 结果数据
    error: Optional[str] = None  # 错误信息
    execution_time: float = 0.0  # 执行时间（秒）
    token_usage: int = 0  # Token使用量
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class TaskMetrics:
    """任务指标"""

    total_tasks: int = 0  # 总任务数
    pending_tasks: int = 0  # 等待中的任务
    running_tasks: int = 0  # 运行中的任务
    completed_tasks: int = 0  # 已完成的任务
    failed_tasks: int = 0  # 失败的任务
    blocked_tasks: int = 0  # 阻塞的任务
    average_execution_time: float = 0.0  # 平均执行时间
    total_token_usage: int = 0  # 总Token使用量


@dataclass
class Task:
    """任务对象"""

    id: str  # 任务唯一标识
    title: str  # 任务标题
    description: str = ""  # 任务描述
    status: TaskStatus = TaskStatus.PENDING  # 任务状态
    priority: TaskPriority = TaskPriority.NORMAL  # 任务优先级
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    started_at: datetime | None = None  # 开始时间
    completed_at: datetime | None = None  # 完成时间
    deadline: datetime | None = None  # 截止时间
    assigned_to: Optional[str] = None  # 分配给的Agent ID
    created_by: Optional[str] = None  # 创建者ID
    session_id: Optional[str] = None  # 关联的会话ID
    skill_id: Optional[str] = None  # 关联的技能ID
    dependencies: list[TaskDependency] = field(default_factory=list)  # 任务依赖
    dependents: list[str] = field(default_factory=list)  # 依赖此任务的其他任务ID
    result: TaskResult | None = None  # 执行结果
    progress: float = 0.0  # 进度 (0.0 - 1.0)
    tags: list[str] = field(default_factory=list)  # 标签
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据
    retry_count: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数
    timeout_seconds: Optional[int] = None  # 超时时间（秒）

    def can_start(self, completed_tasks: set[str]) -> bool:
        """检查任务是否可以开始

        Args:
            completed_tasks: 已完成的任务ID集合

        Returns:
            bool: 是否可以开始
        """
        if self.status not in [TaskStatus.PENDING, TaskStatus.BLOCKED]:
            return False

        # 检查所有必需的依赖是否已完成
        for dep in self.dependencies:
            if dep.required and dep.task_id not in completed_tasks:
                return False

        return True

    def add_dependency(self, task_id: str, dependency_type: TaskDependencyType = TaskDependencyType.FINISH_TO_START) -> None:
        """添加任务依赖

        Args:
            task_id: 依赖的任务ID
            dependency_type: 依赖类型
        """
        dependency = TaskDependency(
            task_id=task_id,
            dependency_type=dependency_type,
        )
        if not any(d.task_id == task_id for d in self.dependencies):
            self.dependencies.append(dependency)
            self.updated_at = datetime.now()

    def assign_to(self, agent_id: str) -> None:
        """分配任务给Agent

        Args:
            agent_id: Agent ID
        """
        self.assigned_to = agent_id
        self.status = TaskStatus.ASSIGNED
        self.updated_at = datetime.now()

    def start(self) -> None:
        """开始执行任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.updated_at = datetime.now()

    def complete(self, result: TaskResult) -> None:
        """完成任务

        Args:
            result: 任务结果
        """
        self.result = result
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.progress = 1.0 if result.success else self.progress
        self.updated_at = datetime.now()

    def fail(self, error: str) -> None:
        """标记任务失败

        Args:
            error: 错误信息
        """
        self.result = TaskResult(success=False, error=error)
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.now()

    def update_progress(self, progress: float) -> None:
        """更新任务进度

        Args:
            progress: 进度值 (0.0 - 1.0)
        """
        self.progress = max(0.0, min(1.0, progress))
        self.updated_at = datetime.now()

    def is_overdue(self) -> bool:
        """检查任务是否过期

        Returns:
            bool: 是否过期
        """
        if not self.deadline:
            return False
        if self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False
        return datetime.now() > self.deadline

    def can_retry(self) -> bool:
        """检查任务是否可以重试

        Returns:
            bool: 是否可以重试
        """
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """增加重试次数"""
        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            dict: 任务字典表示
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "assigned_to": self.assigned_to,
            "created_by": self.created_by,
            "session_id": self.session_id,
            "skill_id": self.skill_id,
            "dependencies": [
                {
                    "task_id": d.task_id,
                    "dependency_type": d.dependency_type.value,
                    "required": d.required,
                }
                for d in self.dependencies
            ],
            "dependents": self.dependents,
            "result": {
                "success": self.result.success,
                "data": self.result.data,
                "error": self.result.error,
                "execution_time": self.result.execution_time,
                "token_usage": self.result.token_usage,
                "metadata": self.result.metadata,
            }
            if self.result
            else None,
            "progress": self.progress,
            "tags": self.tags,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """从字典创建任务

        Args:
            data: 任务字典

        Returns:
            Task: 任务对象
        """
        dependencies = [
            TaskDependency(
                task_id=d["task_id"],
                dependency_type=TaskDependencyType(d.get("dependency_type", "fts")),
                required=d.get("required", True),
            )
            for d in data.get("dependencies", [])
        ]

        result_data = data.get("result")
        result = (
            TaskResult(
                success=result_data["success"],
                data=result_data.get("data"),
                error=result_data.get("error"),
                execution_time=result_data.get("execution_time", 0.0),
                token_usage=result_data.get("token_usage", 0),
                metadata=result_data.get("metadata", {}),
            )
            if result_data
            else None
        )

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", 2)),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            assigned_to=data.get("assigned_to"),
            created_by=data.get("created_by"),
            session_id=data.get("session_id"),
            skill_id=data.get("skill_id"),
            dependencies=dependencies,
            dependents=data.get("dependents", []),
            result=result,
            progress=data.get("progress", 0.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds"),
        )
