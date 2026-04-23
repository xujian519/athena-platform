#!/usr/bin/env python3
from __future__ import annotations

"""
任务管理器
Task Manager

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

任务管理器是P1阶段的核心模块，整合P0系统的Skills、Plugins和会话记忆系统，
提供统一的任务管理接口。
"""

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .exceptions import TaskManagerError
from .models import Task, TaskMetrics, TaskPriority, TaskResult, TaskStatus
from .scheduler import TaskScheduler
from .storage import FileTaskStorage, TaskStorage

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器

    整合P0系统的Skills、Plugins和会话记忆系统，提供统一的任务管理接口。

    核心功能:
    - 任务生命周期管理（创建、分配、执行、完成）
    - 优先级队列和调度
    - 任务依赖关系处理
    - 状态持久化和恢复
    - 任务监控和报告
    """

    def __init__(
        self,
        storage: TaskStorage | None = None,
        enable_auto_cleanup: bool = True,
        cleanup_interval: int = 3600,
    ):
        """初始化任务管理器

        Args:
            storage: 任务存储实例
            enable_auto_cleanup: 是否启用自动清理
            cleanup_interval: 清理间隔（秒）
        """
        self.storage = storage or FileTaskStorage()
        self.scheduler = TaskScheduler(storage=self.storage)
        self._lock = threading.RLock()
        self._observers: list[Callable[[Task, str], None]] = []
        self._auto_cleanup_enabled = enable_auto_cleanup
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread: threading.Thread | None = None
        self._running = False

        logger.info("任务管理器初始化完成")

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
        task = self.scheduler.create_task(
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            created_by=created_by,
            session_id=session_id,
            skill_id=skill_id,
            deadline=deadline,
            dependencies=dependencies,
            tags=tags,
            metadata=metadata,
        )

        self._notify_observers(task, "created")
        logger.info(f"创建任务: {task.id} - {task.title}")

        return task

    def get_task(self, task_id: str) -> Task | None:
        """获取任务

        Args:
            task_id: 任务ID

        Returns:
            Task | None: 任务对象
        """
        return self.scheduler.get_task(task_id)

    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """分配任务给Agent

        Args:
            task_id: 任务ID
            agent_id: Agent ID

        Returns:
            bool: 是否成功分配
        """
        task = self.scheduler.get_task(task_id)
        if not task:
            raise TaskManagerError(f"任务不存在: {task_id}", task_id=task_id)

        task.assign_to(agent_id)
        self.storage.save(task)
        self._notify_observers(task, "assigned")

        logger.info(f"任务 {task_id} 分配给 {agent_id}")
        return True

    def start_task(self, task_id: str) -> bool:
        """开始执行任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功开始
        """
        task = self.scheduler.get_task(task_id)
        if not task:
            raise TaskManagerError(f"任务不存在: {task_id}", task_id=task_id)

        if not task.assigned_to:
            raise TaskManagerError(
                f"任务未分配，无法开始: {task_id}",
                task_id=task_id,
            )

        result = self.scheduler.start_task(task_id, task.assigned_to)
        if result:
            self._notify_observers(task, "started")

        return result

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
        result = self.scheduler.complete_task(task_id, result)

        task = self.scheduler.get_task(task_id)
        if task:
            self._notify_observers(task, "completed")

        return result

    def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败

        Args:
            task_id: 任务ID
            error: 错误信息

        Returns:
            bool: 是否成功标记
        """
        result = self.scheduler.fail_task(task_id, error)

        task = self.scheduler.get_task(task_id)
        if task:
            self._notify_observers(task, "failed")

        return result

    def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        result = self.scheduler.cancel_task(task_id)

        task = self.scheduler.get_task(task_id)
        if task and result:
            self._notify_observers(task, "cancelled")

        return result

    def get_next_task(self, agent_id: Optional[str] = None) -> Task | None:
        """获取下一个可执行的任务

        Args:
            agent_id: 可选的Agent ID，用于过滤分配给该Agent的任务

        Returns:
            Task | None: 下一个任务
        """
        task = self.scheduler.get_next_task()

        # 如果指定了Agent，过滤任务
        if agent_id and task:
            if task.assigned_to and task.assigned_to != agent_id:
                # 尝试获取该Agent的任务
                agent_tasks = self.scheduler.get_tasks_by_agent(agent_id)
                ready_tasks = [t for t in agent_tasks if t.status == TaskStatus.READY]
                if ready_tasks:
                    # 按优先级排序
                    ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
                    return ready_tasks[0]
                return None

        return task

    def get_metrics(self) -> TaskMetrics:
        """获取任务指标

        Returns:
            TaskMetrics: 任务指标
        """
        return self.scheduler.get_metrics()

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """按状态获取任务

        Args:
            status: 任务状态

        Returns:
            list: 任务列表
        """
        return self.scheduler.storage.load_by_status(status)

    def get_tasks_by_agent(self, agent_id: str) -> list[Task]:
        """按Agent获取任务

        Args:
            agent_id: Agent ID

        Returns:
            list: 任务列表
        """
        return self.scheduler.get_tasks_by_agent(agent_id)

    def get_tasks_by_session(self, session_id: str) -> list[Task]:
        """按会话获取任务

        Args:
            session_id: 会话ID

        Returns:
            list: 任务列表
        """
        return self.scheduler.get_tasks_by_session(session_id)

    def get_ready_tasks(self) -> list[Task]:
        """获取所有准备就绪的任务

        Returns:
            list: 任务列表
        """
        return self.scheduler.get_ready_tasks()

    def get_blocked_tasks(self) -> list[Task]:
        """获取所有被阻塞的任务

        Returns:
            list: 任务列表
        """
        return self.scheduler.get_blocked_tasks()

    def get_overdue_tasks(self) -> list[Task]:
        """获取所有过期任务

        Returns:
            list: 任务列表
        """
        return self.scheduler.get_overdue_tasks()

    def add_observer(self, observer: Callable[[Task, str], None]) -> None:
        """添加任务状态观察者

        Args:
            observer: 观察者函数，接收(task, event)参数
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Callable[[Task, str], None]) -> None:
        """移除任务状态观察者

        Args:
            observer: 观察者函数
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, task: Task, event: str) -> None:
        """通知观察者

        Args:
            task: 任务对象
            event: 事件类型
        """
        for observer in self._observers:
            try:
                observer(task, event)
            except Exception as e:
                logger.error(f"观察者通知失败: {e}")

    def cleanup_completed(self, keep_days: int = 7) -> int:
        """清理已完成的任务

        Args:
            keep_days: 保留天数

        Returns:
            int: 清理的任务数量
        """
        return self.scheduler.cleanup_completed(keep_days=keep_days)

    def start_auto_cleanup(self) -> None:
        """启动自动清理"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            logger.warning("自动清理已在运行")
            return

        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info("自动清理已启动")

    def stop_auto_cleanup(self) -> None:
        """停止自动清理"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        logger.info("自动清理已停止")

    def _cleanup_loop(self) -> None:
        """自动清理循环"""
        while self._running:
            try:
                time.sleep(self._cleanup_interval)
                if self._running:
                    count = self.cleanup_completed(keep_days=7)
                    if count > 0:
                        logger.info(f"自动清理了 {count} 个已完成的任务")
            except Exception as e:
                logger.error(f"自动清理失败: {e}")

    def get_pending_count(self) -> int:
        """获取等待中的任务数量

        Returns:
            int: 任务数量
        """
        return self.scheduler.get_pending_count()

    def is_empty(self) -> bool:
        """检查队列是否为空

        Returns:
            bool: 是否为空
        """
        return self.scheduler.is_empty()

    def shutdown(self) -> None:
        """关闭任务管理器"""
        self.stop_auto_cleanup()
        logger.info("任务管理器已关闭")


# 全局任务管理器实例
_global_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例

    Returns:
        TaskManager: 任务管理器实例
    """
    global _global_task_manager
    if _global_task_manager is None:
        _global_task_manager = TaskManager()
    return _global_task_manager


def create_task(
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
    """创建任务（快捷函数）

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
    manager = get_task_manager()
    return manager.create_task(
        title=title,
        description=description,
        priority=priority,
        assigned_to=assigned_to,
        created_by=created_by,
        session_id=session_id,
        skill_id=skill_id,
        deadline=deadline,
        dependencies=dependencies,
        tags=tags,
        metadata=metadata,
    )
