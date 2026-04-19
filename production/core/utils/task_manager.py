#!/usr/bin/env python3
from __future__ import annotations
"""
任务管理器
Task Manager

管理后台任务的生命周期,防止任务泄漏和资源未释放

功能:
1. 创建并跟踪任务
2. 任务异常处理
3. 优雅关闭所有任务
4. 任务状态查询

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskInfo:
    """任务信息"""

    task_id: str
    coro: Callable
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    critical: bool = False  # 是否为关键任务
    task_ref: asyncio.Task | None = None


class TaskManager:
    """
    任务管理器

    管理后台任务的生命周期,确保任务:
    1. 被正确跟踪
    2. 异常被记录
    3. 在关闭时被取消
    4. 不会造成资源泄漏
    """

    def __init__(self, name: str):
        """
        初始化任务管理器

        Args:
            name: 任务管理器名称,用于日志标识
        """
        self.name = name
        self._tasks: dict[str, TaskInfo] = {}
        self._lock = asyncio.Lock()
        self._running = False

        logger.info(f"📋 任务管理器初始化: {name}")

    async def start(self):
        """启动任务管理器"""
        self._running = True
        logger.info(f"✅ 任务管理器已启动: {self.name}")

    async def stop(self):
        """停止任务管理器并取消所有任务"""
        self._running = False
        await self.cancel_all()
        logger.info(f"🛑 任务管理器已停止: {self.name}")

    async def create_task(
        self, coro: Coroutine, task_id: str, critical: bool = False
    ) -> asyncio.Task:
        """
        创建并跟踪任务

        Args:
            coro: 协程对象
            task_id: 任务ID
            critical: 是否为关键任务(关键任务失败时会重新抛出异常)

        Returns:
            asyncio.Task: 创建的任务对象

        Raises:
            ValueError: 如果任务ID已存在
        """
        if not self._running:
            raise RuntimeError(f"任务管理器未启动: {self.name}")

        async with self._lock:
            if task_id in self._tasks:
                raise ValueError(f"任务ID已存在: {task_id}")

            # 创建任务信息
            task_info = TaskInfo(task_id=task_id, coro=coro, critical=critical)

            # 创建包装协程
            wrapped = self._wrap_task(coro, task_info)

            # 创建任务
            task = asyncio.create_task(wrapped, name=task_id)
            task_info.task_ref = task
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.now()

            # 存储任务
            self._tasks[task_id] = task_info

            logger.info(f"✅ 任务已创建: {task_id} (critical={critical})")
            return task

    async def _wrap_task(self, coro: Coroutine, task_info: TaskInfo):
        """
        包装任务,添加异常处理和状态管理

        Args:
            coro: 原始协程
            task_info: 任务信息
        """
        try:
            await coro
            task_info.status = TaskStatus.COMPLETED
            logger.debug(f"✅ 任务已完成: {task_info.task_id}")
        except asyncio.CancelledError:
            task_info.status = TaskStatus.CANCELLED
            logger.info(f"🛑 任务已取消: {task_info.task_id}")
        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.error = str(e)
            logger.error(f"❌ 任务失败: {task_info.task_id} - {e}")

            # 如果是关键任务,重新抛出异常
            if task_info.critical:
                raise
        finally:
            task_info.completed_at = datetime.now()

            # 从活动任务中移除(但不删除记录,用于历史查询)
            async with self._lock:
                if task_info.task_id in self._tasks:
                    # 保留记录,但标记为非活动
                    pass

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消指定任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        async with self._lock:
            task_info = self._tasks.get(task_id)
            if not task_info:
                logger.warning(f"⚠️ 任务不存在: {task_id}")
                return False

            task = task_info.task_ref
            if not task or task.done():
                logger.warning(f"⚠️ 任务已完成或已取消: {task_id}")
                return False

            task.cancel()
            logger.info(f"🛑 任务取消请求已发送: {task_id}")
            return True

    async def cancel_all(self):
        """取消所有活动任务"""
        async with self._lock:
            active_tasks = [
                (task_id, task_info)
                for task_id, task_info in self._tasks.items()
                if task_info.task_ref and not task_info.task_ref.done()
            ]

            if not active_tasks:
                logger.info(f"✅ 没有需要取消的活动任务: {self.name}")
                return

            logger.info(f"🛑 开始取消 {len(active_tasks)} 个活动任务...")

            for task_id, task_info in active_tasks:
                task_info.task_ref.cancel()
                logger.info(f"  🛑 取消任务: {task_id}")

            # 等待所有任务完成取消
            tasks = [info.task_ref for _, info in active_tasks if info.task_ref]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"✅ 所有任务已取消: {self.name}")

    def get_task_info(self, task_id: str) -> TaskInfo | None:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            TaskInfo: 任务信息,不存在返回None
        """
        return self._tasks.get(task_id)

    def get_active_tasks(self) -> list[str]:
        """
        获取活动任务列表

        Returns:
            list[str]: 活动任务ID列表
        """
        return [
            task_id
            for task_id, task_info in self._tasks.items()
            if task_info.task_ref and not task_info.task_ref.done()
        ]

    def get_all_tasks(self) -> dict[str, TaskInfo]:
        """
        获取所有任务信息

        Returns:
            dict[str, TaskInfo]: 所有任务信息
        """
        return self._tasks.copy()

    def get_stats(self) -> dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            Dict: 统计信息
        """
        status_counts = dict.fromkeys(TaskStatus, 0)

        for task_info in self._tasks.values():
            status_counts[task_info.status] += 1

        active_count = len(self.get_active_tasks())

        return {
            "manager_name": self.name,
            "total_tasks": len(self._tasks),
            "active_tasks": active_count,
            "status_distribution": {s.value: c for s, c in status_counts.items()},
        }

    async def cleanup(self, max_history: int = 1000):
        """
        清理旧的任务记录

        Args:
            max_history: 保留的历史任务数量
        """
        async with self._lock:
            # 按完成时间排序
            completed_tasks = [
                (task_id, task_info)
                for task_id, task_info in self._tasks.items()
                if task_info.status
                in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task_info.completed_at is not None
            ]

            # 按时间排序,保留最近的任务
            completed_tasks.sort(key=lambda x: x[1].completed_at or datetime.min)

            # 删除超过限制的旧任务
            if len(completed_tasks) > max_history:
                to_remove = completed_tasks[:-max_history]
                for task_id, _ in to_remove:
                    del self._tasks[task_id]

                logger.info(f"🧹 已清理 {len(to_remove)} 个旧任务记录")

    def __repr__(self) -> str:
        stats = self.get_stats()
        return f"TaskManager(name={self.name}, active={stats['active_tasks']}, total={stats['total_tasks']})"


# 便捷函数
_managers: dict[str, TaskManager] = {}


def get_task_manager(name: str) -> TaskManager:
    """
    获取或创建任务管理器

    Args:
        name: 任务管理器名称

    Returns:
        TaskManager: 任务管理器实例
    """
    if name not in _managers:
        _managers[name] = TaskManager(name)
    return _managers[name]


async def shutdown_all_managers():
    """关闭所有任务管理器"""
    for name, manager in _managers.items():
        logger.info(f"🛑 关闭任务管理器: {name}")
        await manager.stop()
    _managers.clear()
