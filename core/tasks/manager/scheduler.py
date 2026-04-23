#!/usr/bin/env python3
from __future__ import annotations

"""
任务调度器
Task Scheduler

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0
"""

import heapq
import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .exceptions import TaskDependencyError, TaskManagerError
from .models import Task, TaskMetrics, TaskPriority, TaskResult, TaskStatus
from .storage import FileTaskStorage, TaskStorage

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PriorityTask:
    """优先级任务包装器（用于堆）"""

    priority: int  # 优先级（数值越小优先级越高）
    created_at: datetime  # 创建时间（用于同优先级排序）
    task: Task = field(compare=False)  # 实际任务


class TaskScheduler:
    """任务调度器

    负责任务的调度、优先级管理和依赖处理。
    """

    def __init__(self, storage: TaskStorage | None = None):
        """初始化任务调度器

        Args:
            storage: 任务存储实例
        """
        self.storage = storage or FileTaskStorage()
        self._lock = threading.RLock()
        self._priority_queue: list[PriorityTask] = []
        self._task_index: dict[str, Task] = {}
        self._completed_tasks: set[str] = set()
        self._running_tasks: set[str] = set()
        self._metrics = TaskMetrics()
        self._execution_times: dict[str, float] = {}

        # 加载现有任务
        self._load_existing_tasks()

    def _load_existing_tasks(self) -> None:
        """加载现有任务"""
        try:
            all_tasks = self.storage.load_all()
            for task_id, task in all_tasks.items():
                self._task_index[task_id] = task

                if task.status == TaskStatus.COMPLETED:
                    self._completed_tasks.add(task_id)
                elif task.status == TaskStatus.RUNNING:
                    self._running_tasks.add(task_id)
                    # 将运行中的任务放回队列（可能需要重新调度）
                    self._add_to_queue(task)

            self._update_metrics()
            logger.info(f"已加载 {len(self._task_index)} 个任务")
        except Exception as e:
            logger.error(f"加载现有任务失败: {e}")

    def _add_to_queue(self, task: Task) -> None:
        """添加任务到优先级队列

        Args:
            task: 任务对象
        """
        # 优先级转换：CRITICAL=1, URGENT=2, HIGH=3, NORMAL=4, LOW=5
        priority_value = 6 - task.priority.value
        priority_task = PriorityTask(
            priority=priority_value,
            created_at=task.created_at,
            task=task,
        )
        heapq.heappush(self._priority_queue, priority_task)

    def _update_metrics(self) -> None:
        """更新任务指标"""
        total = len(self._task_index)
        # PENDING和READY都算作等待中的任务
        pending = sum(1 for t in self._task_index.values() if t.status in [TaskStatus.PENDING, TaskStatus.READY])
        running = len(self._running_tasks)
        completed = len(self._completed_tasks)
        failed = sum(1 for t in self._task_index.values() if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in self._task_index.values() if t.status == TaskStatus.BLOCKED)

        avg_time = 0.0
        if self._execution_times:
            avg_time = sum(self._execution_times.values()) / len(self._execution_times)

        self._metrics = TaskMetrics(
            total_tasks=total,
            pending_tasks=pending,
            running_tasks=running,
            completed_tasks=completed,
            failed_tasks=failed,
            blocked_tasks=blocked,
            average_execution_time=avg_time,
        )

    def schedule_task(self, task: Task) -> bool:
        """调度任务

        Args:
            task: 任务对象

        Returns:
            bool: 是否成功调度
        """
        with self._lock:
            try:
                # 检查任务是否已存在
                if task.id in self._task_index:
                    logger.warning(f"任务 {task.id} 已存在，将更新")
                    existing_task = self._task_index[task.id]
                    # 更新现有任务
                    existing_task.title = task.title
                    existing_task.description = task.description
                    existing_task.priority = task.priority
                    existing_task.updated_at = datetime.now()
                    task = existing_task
                else:
                    self._task_index[task.id] = task

                # 检查依赖是否满足
                # 暂时重置为PENDING以进行依赖检查
                if task.status not in [TaskStatus.PENDING, TaskStatus.BLOCKED]:
                    task.status = TaskStatus.PENDING

                if not task.can_start(self._completed_tasks):
                    task.status = TaskStatus.BLOCKED
                    logger.info(f"任务 {task.id} 被阻塞，等待依赖完成")
                else:
                    task.status = TaskStatus.READY
                    self._add_to_queue(task)

                # 保存到存储
                self.storage.save(task)
                self._update_metrics()

                logger.info(f"任务 {task.id} 已调度，状态: {task.status.value}")
                return True

            except Exception as e:
                logger.error(f"调度任务 {task.id} 失败: {e}")
                raise TaskManagerError(f"调度任务失败: {e}", task_id=task.id) from e

    def get_next_task(self) -> Task | None:
        """获取下一个可执行的任务

        Returns:
            Task | None: 下一个任务，如果没有可执行任务则返回None
        """
        with self._lock:
            while self._priority_queue:
                priority_task = heapq.heappop(self._priority_queue)
                task = priority_task.task

                # 跳过已完成或取消的任务
                if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    continue

                # 检查任务是否可以执行
                if task.status == TaskStatus.READY:
                    return task

                # 检查依赖是否已满足
                if task.can_start(self._completed_tasks):
                    task.status = TaskStatus.READY
                    return task

                # 依赖未满足，重新入队
                task.status = TaskStatus.BLOCKED
                heapq.heappush(self._priority_queue, priority_task)

            return None

    def start_task(self, task_id: str, agent_id: Optional[str] = None) -> bool:
        """开始执行任务

        Args:
            task_id: 任务ID
            agent_id: 执行任务的Agent ID

        Returns:
            bool: 是否成功开始
        """
        with self._lock:
            task = self._task_index.get(task_id)
            if not task:
                raise TaskManagerError(f"任务不存在: {task_id}", task_id=task_id)

            # 检查任务是否准备好（READY状态表示依赖已满足）
            if task.status != TaskStatus.READY:
                # 检查依赖是否满足
                if task.dependencies and not all(dep.task_id in self._completed_tasks for dep in task.dependencies if dep.required):
                    raise TaskDependencyError(
                        task_id=task_id,
                        reason="依赖未满足",
                    )

            # 先分配Agent（如果有）
            if agent_id:
                task.assigned_to = agent_id

            # 然后开始任务
            task.start()

            self._running_tasks.add(task_id)
            self.storage.save(task)
            self._update_metrics()

            logger.info(f"任务 {task_id} 开始执行，由 {agent_id} 执行")
            return True

    def complete_task(
        self,
        task_id: str,
        result: TaskResult,
    ) -> bool:
        """完成任务

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            bool: 是否成功完成
        """
        with self._lock:
            task = self._task_index.get(task_id)
            if not task:
                raise TaskManagerError(f"任务不存在: {task_id}", task_id=task_id)

            task.complete(result)

            if task_id in self._running_tasks:
                self._running_tasks.remove(task_id)

            if result.success:
                self._completed_tasks.add(task_id)
                self._execution_times[task_id] = result.execution_time

                # 检查并解除依赖此任务的其他任务的阻塞
                self._unblock_dependents(task_id)

            self.storage.save(task)
            self._update_metrics()

            logger.info(f"任务 {task_id} 已完成，结果: {'成功' if result.success else '失败'}")
            return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败

        Args:
            task_id: 任务ID
            error: 错误信息

        Returns:
            bool: 是否成功标记
        """
        with self._lock:
            task = self._task_index.get(task_id)
            if not task:
                raise TaskManagerError(f"任务不存在: {task_id}", task_id=task_id)

            task.fail(error)

            if task_id in self._running_tasks:
                self._running_tasks.remove(task_id)

            # 检查是否可以重试
            if task.can_retry():
                task.increment_retry()
                # 重置状态为PENDING，然后重新调度
                task.status = TaskStatus.PENDING
                # 检查依赖是否满足，如果满足则设为READY
                if task.can_start(self._completed_tasks):
                    task.status = TaskStatus.READY
                    self._add_to_queue(task)
                else:
                    task.status = TaskStatus.BLOCKED
                logger.info(f"任务 {task_id} 将重试 ({task.retry_count}/{task.max_retries})")
            else:
                logger.error(f"任务 {task_id} 失败: {error}")

            self.storage.save(task)
            self._update_metrics()
            return True

    def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        with self._lock:
            task = self._task_index.get(task_id)
            if not task:
                raise TaskManagerError(f"任务不存在: {task_id}", task_id=task_id)

            # 已完成或已取消的任务不能取消
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                logger.warning(f"任务 {task_id} 已完成或已取消，无法取消")
                return False

            task.cancel()

            if task_id in self._running_tasks:
                self._running_tasks.remove(task_id)

            self.storage.save(task)
            self._update_metrics()

            logger.info(f"任务 {task_id} 已取消")
            return True

    def _unblock_dependents(self, completed_task_id: str) -> None:
        """解除依赖任务

        Args:
            completed_task_id: 已完成的任务ID
        """
        for task_id, task in self._task_index.items():
            if task.status == TaskStatus.BLOCKED:
                # 检查是否依赖刚完成的任务
                if any(dep.task_id == completed_task_id for dep in task.dependencies):
                    # 检查是否所有依赖都已满足（暂时设置为PENDING进行检查）
                    original_status = task.status
                    task.status = TaskStatus.PENDING

                    if task.can_start(self._completed_tasks):
                        task.status = TaskStatus.READY
                        self._add_to_queue(task)
                        logger.info(f"任务 {task_id} 解除阻塞")
                    else:
                        # 恢复原状态
                        task.status = original_status

    def get_task(self, task_id: str) -> Task | None:
        """获取任务

        Args:
            task_id: 任务ID

        Returns:
            Task | None: 任务对象
        """
        with self._lock:
            return self._task_index.get(task_id)

    def get_metrics(self) -> TaskMetrics:
        """获取任务指标

        Returns:
            TaskMetrics: 任务指标
        """
        with self._lock:
            self._update_metrics()
            return self._metrics

    def get_ready_tasks(self) -> list[Task]:
        """获取所有准备就绪的任务

        Returns:
            list: 准备就绪的任务列表
        """
        with self._lock:
            return [
                task
                for task in self._task_index.values()
                if task.status == TaskStatus.READY
            ]

    def get_blocked_tasks(self) -> list[Task]:
        """获取所有被阻塞的任务

        Returns:
            list: 被阻塞的任务列表
        """
        with self._lock:
            return [
                task
                for task in self._task_index.values()
                if task.status == TaskStatus.BLOCKED
            ]

    def get_overdue_tasks(self) -> list[Task]:
        """获取所有过期任务

        Returns:
            list: 过期任务列表
        """
        with self._lock:
            now = datetime.now()
            return [
                task
                for task in self._task_index.values()
                if task.is_overdue()
            ]

    def cleanup_completed(self, keep_days: int = 7) -> int:
        """清理已完成的任务

        Args:
            keep_days: 保留天数

        Returns:
            int: 清理的任务数量
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            to_remove = []

            for task_id, task in self._task_index.items():
                if (
                    task.status == TaskStatus.COMPLETED
                    and task.completed_at
                    and task.completed_at < cutoff_time
                ):
                    to_remove.append(task_id)

            for task_id in to_remove:
                del self._task_index[task_id]
                self._completed_tasks.discard(task_id)
                self.storage.delete(task_id)

            self._update_metrics()
            logger.info(f"清理了 {len(to_remove)} 个已完成的任务")
            return len(to_remove)

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        session_id: Optional[str] = None,
        skill_id: Optional[str] = None,
        deadline: datetime | None = None,
        dependencies: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Task:
        """创建新任务

        Args:
            title: 任务标题
            description: 任务描述
            priority: 任务优先级
            assigned_to: 分配给的Agent ID
            created_by: 创建者ID
            session_id: 关联的会话ID
            skill_id: 关联的技能ID
            deadline: 截止时间
            dependencies: 依赖的任务ID列表
            tags: 标签列表
            metadata: 元数据

        Returns:
            Task: 创建的任务对象
        """
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            created_by=created_by,
            session_id=session_id,
            skill_id=skill_id,
            deadline=deadline,
            tags=tags or [],
            metadata=metadata or {},
        )

        # 添加依赖
        if dependencies:
            for dep_id in dependencies:
                task.add_dependency(dep_id)

        # 调度任务
        self.schedule_task(task)

        return task

    def get_tasks_by_agent(self, agent_id: str) -> list[Task]:
        """获取Agent的所有任务

        Args:
            agent_id: Agent ID

        Returns:
            list: 任务列表
        """
        with self._lock:
            return [
                task
                for task in self._task_index.values()
                if task.assigned_to == agent_id
            ]

    def get_tasks_by_session(self, session_id: str) -> list[Task]:
        """获取会话的所有任务

        Args:
            session_id: 会话ID

        Returns:
            list: 任务列表
        """
        with self._lock:
            return [
                task
                for task in self._task_index.values()
                if task.session_id == session_id
            ]

    def get_pending_count(self) -> int:
        """获取等待中的任务数量

        Returns:
            int: 任务数量
        """
        with self._lock:
            return sum(
                1 for task in self._task_index.values()
                if task.status in [TaskStatus.PENDING, TaskStatus.READY]
            )

    def is_empty(self) -> bool:
        """检查队列是否为空

        Returns:
            bool: 是否为空
        """
        with self._lock:
            return len(self._priority_queue) == 0
