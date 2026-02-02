#!/usr/bin/env python3
"""
任务模型标准化
Task Models Standardization

定义统一的任务对象、状态和优先级,确保所有模块使用相同的任务模型

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 初始化logger
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"  # 等待中
    QUEUED = "queued"  # 已排队
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 超时
    RETRYING = "retrying"  # 重试中


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 1  # 低优先级
    NORMAL = 2  # 普通优先级
    HIGH = 3  # 高优先级
    URGENT = 4  # 紧急优先级
    CRITICAL = 5  # 关键优先级


class TaskType(Enum):
    """任务类型"""

    FUNCTION_CALL = "function_call"  # 函数调用
    API_CALL = "api_call"  # API调用
    WORKFLOW = "workflow"  # 工作流
    BATCH = "batch"  # 批处理
    SCHEDULED = "scheduled"  # 定时任务
    REAL_TIME = "real_time"  # 实时任务


@dataclass
class TaskResult:
    """任务结果"""

    success: bool
    data: Any = None
    error: str | None = None
    execution_time: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TaskDependency:
    """任务依赖"""

    task_id: str
    dependency_type: str = "success"  # success, completion, custom
    condition: Callable | None = None


@dataclass
class Task:
    """
    标准化任务对象

    统一的任务定义,包含所有必要属性和方法
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.FUNCTION_CALL

    # 任务内容
    action: str = ""
    action_data: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)

    # 状态管理
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    due_at: datetime | None = None

    # 执行信息
    agent_id: str = ""
    executor_id: str | None = None
    worker_id: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    # 结果信息
    result: TaskResult | None = None

    # 依赖关系
    dependencies: list[TaskDependency] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)

    # 元数据
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # 回调函数
    on_success: Callable | None = None
    on_failure: Callable | None = None
    on_complete: Callable | None = None

    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            self.name = f"Task_{self.id[:8]}"

    def start(self) -> bool:
        """开始任务"""
        if self.status not in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RETRYING]:
            return False

        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        return True

    def complete(
        self, success: bool, data: Any = None, error: str = None, execution_time: float = 0.0
    ) -> Any:
        """完成任务"""
        self.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.completed_at = datetime.now()

        # 创建结果对象
        self.result = TaskResult(
            success=success,
            data=data,
            error=error,
            execution_time=execution_time,
            metrics={"retry_count": self.retry_count, "total_time": self.get_total_time()},
        )

        # 执行回调
        if success and self.on_success:
            if asyncio.iscoroutinefunction(self.on_success):
                # 异步回调需要在事件循环中执行
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.on_success(self))
                    else:
                        loop.run_until_complete(self.on_success(self))
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[task_models] Exception: {e}")
            else:
                try:
                    self.on_success(self)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[task_models] Exception: {e}")
        elif not success and self.on_failure:
            if asyncio.iscoroutinefunction(self.on_failure):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.on_failure(self))
                    else:
                        loop.run_until_complete(self.on_failure(self))
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[task_models] Exception: {e}")
            else:
                try:
                    self.on_failure(self)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[task_models] Exception: {e}")

        # 通用完成回调
        if self.on_complete:
            if asyncio.iscoroutinefunction(self.on_complete):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.on_complete(self))
                    else:
                        loop.run_until_complete(self.on_complete(self))
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[task_models] Exception: {e}")
            else:
                try:
                    self.on_complete(self)
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[task_models] Exception: {e}")

    def cancel(self) -> Any:
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()

    def timeout(self) -> Any:
        """任务超时"""
        self.status = TaskStatus.TIMEOUT
        self.completed_at = datetime.now()

    def retry(self) -> bool:
        """重试任务"""
        if self.retry_count >= self.max_retries:
            return False

        self.retry_count += 1
        self.status = TaskStatus.RETRYING
        self.started_at = None
        self.completed_at = None
        self.result = None
        return True

    def add_dependency(self, task_id: str, dependency_type: str = "success") -> None:
        """添加依赖"""
        dependency = TaskDependency(task_id=task_id, dependency_type=dependency_type)
        self.dependencies.append(dependency)

    def can_start(self, completed_tasks: dict[str, "Task"]) -> bool:
        """检查是否可以开始"""
        if self.status != TaskStatus.PENDING:
            return False

        # 检查所有依赖是否满足
        for dep in self.dependencies:
            if dep.task_id not in completed_tasks:
                return False

            dep_task = completed_tasks[dep.task_id]

            if (dep.dependency_type == "success" and not dep_task.is_success()) or (dep.dependency_type == "completion" and not dep_task.is_completed()) or (dep.dependency_type == "custom" and dep.condition and not dep.condition(dep_task)):
                return False

        return True

    def is_success(self) -> bool:
        """是否成功"""
        return self.status == TaskStatus.COMPLETED and self.result and self.result.success

    def is_failed(self) -> bool:
        """是否失败"""
        return self.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED]

    def is_completed(self) -> bool:
        """是否完成"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.TIMEOUT,
            TaskStatus.CANCELLED,
        ]

    def is_running(self) -> bool:
        """是否正在运行"""
        return self.status == TaskStatus.RUNNING

    def get_total_time(self) -> float:
        """获取总耗时"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    def get_wait_time(self) -> float:
        """获取等待时间"""
        end_time = self.started_at or self.completed_at or datetime.now()
        return (end_time - self.created_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "action": self.action,
            "action_data": self.action_data,
            "parameters": self.parameters,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "agent_id": self.agent_id,
            "executor_id": self.executor_id,
            "worker_id": self.worker_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "result": self.result.to_dict() if self.result else None,
            "dependencies": [
                {"task_id": dep.task_id, "type": dep.dependency_type} for dep in self.dependencies
            ],
            "dependents": self.dependents,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """从字典创建任务"""
        # 处理特殊字段
        task_type = TaskType(data.get("task_type", TaskType.FUNCTION_CALL.value))
        status = TaskStatus(data.get("status", TaskStatus.PENDING.value))
        priority = TaskPriority(data.get("priority", TaskPriority.NORMAL.value))

        # 处理时间字段
        created_at = (
            datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )
        started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        completed_at = (
            datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )
        due_at = datetime.fromisoformat(data["due_at"]) if data.get("due_at") else None

        # 处理结果
        result_data = data.get("result")
        result = None
        if result_data:
            result = TaskResult(
                success=result_data["success"],
                data=result_data.get("data"),
                error=result_data.get("error"),
                execution_time=result_data.get("execution_time", 0.0),
                metrics=result_data.get("metrics", {}),
                timestamp=datetime.fromisoformat(result_data["timestamp"]),
            )

        # 处理依赖
        dependencies = []
        for dep_data in data.get("dependencies", []):
            dependencies.append(
                TaskDependency(
                    task_id=dep_data["task_id"], dependency_type=dep_data.get("type", "success")
                )
            )

        # 创建任务
        task = cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            task_type=task_type,
            action=data.get("action", ""),
            action_data=data.get("action_data", {}),
            parameters=data.get("parameters", {}),
            status=status,
            priority=priority,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            due_at=due_at,
            agent_id=data.get("agent_id", ""),
            executor_id=data.get("executor_id"),
            worker_id=data.get("worker_id"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            result=result,
            dependencies=dependencies,
            dependents=data.get("dependents", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

        return task

    @classmethod
    def from_json(cls, json_str: str) -> "Task":
        """从JSON字符串创建任务"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def copy(self) -> "Task":
        """创建任务副本"""
        return Task.from_dict(self.to_dict())

    def __str__(self) -> str:
        """字符串表示"""
        return f"Task(id={self.id[:8]}..., name={self.name}, status={self.status.value}, priority={self.priority.name})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()


# 工具函数
def create_function_task(
    name: str,
    func_name: str,
    args: list | None = None,
    kwargs: dict | None = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    agent_id: str = "",
) -> Task:
    """创建函数调用任务"""
    return Task(
        name=name,
        task_type=TaskType.FUNCTION_CALL,
        action=func_name,
        action_data={"args": args or [], "kwargs": kwargs or {}},
        priority=priority,
        agent_id=agent_id,
    )


def create_api_task(
    name: str,
    url: str,
    method: str = "GET",
    data: dict | None = None,
    headers: dict | None = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    agent_id: str = "",
) -> Task:
    """创建API调用任务"""
    return Task(
        name=name,
        task_type=TaskType.API_CALL,
        action="api_call",
        action_data={"url": url, "method": method, "data": data or {}, "headers": headers or {}},
        priority=priority,
        agent_id=agent_id,
    )


def create_workflow_task(
    name: str, steps: list[dict], priority: TaskPriority = TaskPriority.NORMAL, agent_id: str = ""
) -> Task:
    """创建工作流任务"""
    return Task(
        name=name,
        task_type=TaskType.WORKFLOW,
        action="workflow",
        action_data={"steps": steps},
        priority=priority,
        agent_id=agent_id,
    )


# 任务工厂
class TaskFactory:
    """任务工厂"""

    @staticmethod
    def create_task(task_type: TaskType, **kwargs) -> Task:
        """创建任务"""
        if task_type == TaskType.FUNCTION_CALL:
            return create_function_task(**kwargs)
        elif task_type == TaskType.API_CALL:
            return create_api_task(**kwargs)
        elif task_type == TaskType.WORKFLOW:
            return create_workflow_task(**kwargs)
        else:
            return Task(task_type=task_type, **kwargs)


# 任务队列管理器
class TaskQueue:
    """任务队列"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue: list[Task] = []
        self._task_index: dict[str, Task] = {}

    def enqueue(self, task: Task) -> bool:
        """入队"""
        if len(self._queue) >= self.max_size:
            return False

        if task.id in self._task_index:
            return False

        # 按优先级插入
        insert_pos = 0
        for i, existing_task in enumerate(self._queue):
            if task.priority.value > existing_task.priority.value:
                insert_pos = i
                break
            insert_pos = i + 1

        self._queue.insert(insert_pos, task)
        self._task_index[task.id] = task

        # 更新状态
        task.status = TaskStatus.QUEUED

        return True

    def dequeue(self) -> Task | None:
        """出队"""
        if not self._queue:
            return None

        task = self._queue.pop(0)
        del self._task_index[task.id]

        return task

    def peek(self) -> Task | None:
        """查看队首任务"""
        return self._queue[0] if self._queue else None

    def get_task(self, task_id: str) -> Task | None:
        """获取任务"""
        return self._task_index.get(task_id)

    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id not in self._task_index:
            return False

        task = self._task_index[task_id]
        self._queue.remove(task)
        del self._task_index[task_id]

        return True

    def size(self) -> int:
        """队列大小"""
        return len(self._queue)

    def is_empty(self) -> bool:
        """是否为空"""
        return len(self._queue) == 0

    def is_full(self) -> bool:
        """是否已满"""
        return len(self._queue) >= self.max_size

    def clear(self) -> Any:
        """清空队列"""
        self._queue.clear()
        self._task_index.clear()

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """按状态获取任务"""
        return [task for task in self._queue if task.status == status]

    def get_tasks_by_priority(self, priority: TaskPriority) -> list[Task]:
        """按优先级获取任务"""
        return [task for task in self._queue if task.priority == priority]

    def get_summary(self) -> dict[str, Any]:
        """获取队列摘要"""
        status_counts = {}
        priority_counts = {}

        for task in self._queue:
            # 统计状态
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # 统计优先级
            priority = task.priority.name
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        return {
            "size": len(self._queue),
            "max_size": self.max_size,
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "oldest_task": self._queue[0].created_at.isoformat() if self._queue else None,
            "newest_task": self._queue[-1].created_at.isoformat() if self._queue else None,
        }
