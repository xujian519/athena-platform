#!/usr/bin/env python3
from __future__ import annotations
"""
Athena通信系统 - 后台任务管理器
Background Task Manager for Communication System

提供统一的后台任务管理功能,解决任务引用丢失和资源泄漏问题。

主要功能:
1. 任务创建和跟踪
2. 批量任务取消
3. 任务状态查询
4. 异常收集和报告
5. 超时处理

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TaskInfo:
    """任务信息"""

    task: asyncio.Task
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    error: Exception | None = None
    timeout: Optional[float] = None

    @property
    def is_done(self) -> bool:
        """任务是否完成"""
        return self.task.done()

    @property
    def is_cancelled(self) -> bool:
        """任务是否已取消"""
        return self.task.cancelled()

    @property
    def duration(self) -> float:
        """获取任务运行时长(秒)"""
        end_time = self.completed_at or datetime.now()
        return (end_time - self.created_at).total_seconds()


class BackgroundTaskManager:
    """
    后台任务管理器

    统一管理所有后台协程任务,确保:
    1. 所有任务引用都被保存
    2. 可以正确关闭所有任务
    3. 任务异常被正确收集
    4. 支持任务超时处理
    """

    def __init__(self, name: str = "BackgroundTaskManager"):
        """
        初始化任务管理器

        Args:
            name: 管理器名称,用于日志
        """
        self.name = name
        self._tasks: dict[str, TaskInfo] = {}
        self._task_counter = 0
        self._lock = asyncio.Lock()
        self._is_running = True

        logger.debug(f"{self.name} 初始化")

    def create_task(
        self,
        coro,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        callback: Callable[[asyncio.Task, Any], None] | None = None,
    ) -> asyncio.Task:
        """
        创建并跟踪后台任务

        Args:
            coro: 协程对象
            name: 任务名称(可选)
            timeout: 超时时间(秒),None表示无超时
            callback: 任务完成时的回调函数

        Returns:
            创建的asyncio.Task对象
        """
        if not self._is_running:
            logger.warning(f"{self.name} 已关闭,拒绝创建新任务")
            # 仍然创建任务,但不跟踪
            task = asyncio.create_task(coro, name=name)
            return task

        task_id = f"task_{self._task_counter}"
        self._task_counter += 1

        # 如果有超时,包装协程
        if timeout is not None:
            coro = self._with_timeout(coro, timeout)

        task = asyncio.create_task(coro, name=name or task_id)

        # 保存任务信息
        task_info = TaskInfo(task=task, name=name or task_id, timeout=timeout)

        # 添加完成回调
        task.add_done_callback(self._make_done_callback(task_id, callback))

        self._tasks[task_id] = task_info

        logger.debug(f"{self.name} 创建任务: {task_id} ({name})")
        return task

    def _with_timeout(self, coro, timeout: float) -> None:
        """为协程添加超时处理"""

        async def wrapper():
            try:
                async with asyncio.timeout(timeout):
                    return await coro
            except TimeoutError:
                logger.warning(f"任务超时: {timeout}秒")
                raise

        return wrapper()

    def _make_done_callback(self, task_id: str, callback: Callable[[asyncio.Task], Any] | None = None):
        """创建任务完成回调"""

        def done_callback(task: asyncio.Task) -> Any:
            try:
                # 记录完成时间
                if task_id in self._tasks:
                    self._tasks[task_id].completed_at = datetime.now()

                # 收集异常
                try:
                    task.result()
                except Exception as e:
                    if task_id in self._tasks:
                        self._tasks[task_id].error = e
                    logger.error(f"{self.name} 任务异常: {task_id} - {e}")

                # 调用用户回调
                if callback:
                    try:
                        callback(task)
                    except Exception as e:
                        logger.error(f"{self.name} 回调异常: {e}")

                logger.debug(f"{self.name} 任务完成: {task_id}")

            except Exception as e:
                logger.error(f"{self.name} 完成回调异常: {e}")

        return done_callback

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消指定任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        async with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"{self.name} 任务不存在: {task_id}")
                return False

            task_info = self._tasks[task_id]

            if task_info.is_done:
                logger.debug(f"{self.name} 任务已完成,无需取消: {task_id}")
                return False

            task_info.task.cancel()
            try:
                await task_info.task
            except asyncio.CancelledError:
                logger.info(f"{self.name} 任务已取消: {task_id}")
                return True

            return False

    async def cancel_all(self) -> int:
        """
        取消所有正在运行的任务

        Returns:
            取消的任务数量
        """
        if not self._is_running:
            return 0

        self._is_running = False

        # 收集需要取消的任务
        tasks_to_cancel = [
            (task_id, task_info)
            for task_id, task_info in self._tasks.items()
            if not task_info.is_done
        ]

        if not tasks_to_cancel:
            logger.debug(f"{self.name} 没有需要取消的任务")
            return 0

        logger.info(f"{self.name} 正在取消 {len(tasks_to_cancel)} 个任务...")

        # 取消所有任务
        for task_id, task_info in tasks_to_cancel:
            task_info.task.cancel()

        # 等待所有任务完成取消
        cancelled_count = 0
        for task_id, task_info in tasks_to_cancel:
            try:
                await task_info.task
                cancelled_count += 1
            except asyncio.CancelledError:
                cancelled_count += 1
            except Exception as e:
                logger.error(f"{self.name} 取消任务异常: {task_id} - {e}")

        logger.info(f"{self.name} 已取消 {cancelled_count} 个任务")
        return cancelled_count

    async def wait_all(
        self, timeout: Optional[float] = None, return_exceptions: bool = True
    ) -> dict[str, Any]:
        """
        等待所有任务完成

        Args:
            timeout: 超时时间(秒)
            return_exceptions: 是否返回异常

        Returns:
            完成统计信息
        """
        if not self._tasks:
            return {"total": 0, "completed": 0, "failed": 0, "cancelled": 0}

        # 收集所有未完成的任务
        tasks = [task_info.task for task_info in self._tasks.values() if not task_info.is_done]

        if not tasks:
            return self._get_statistics()

        logger.info(f"{self.name} 等待 {len(tasks)} 个任务完成...")

        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=return_exceptions), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"{self.name} 等待任务超时")
        except Exception as e:
            logger.error(f"{self.name} 等待任务异常: {e}")

        return self._get_statistics()

    def get_active_count(self) -> int:
        """获取活跃任务数量"""
        return sum(1 for task_info in self._tasks.values() if not task_info.is_done)

    def get_done_count(self) -> int:
        """获取已完成任务数量"""
        return sum(1 for task_info in self._tasks.values() if task_info.is_done)

    def get_failed_tasks(self) -> list[TaskInfo]:
        """获取失败的任务列表"""
        return [
            task_info
            for task_info in self._tasks.values()
            if task_info.is_done and task_info.error is not None
        ]

    def get_cancelled_tasks(self) -> list[TaskInfo]:
        """获取已取消的任务列表"""
        return [task_info for task_info in self._tasks.values() if task_info.is_cancelled]

    def get_task_info(self, task_id: str) -> TaskInfo | None:
        """获取指定任务的信息"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> dict[str, TaskInfo]:
        """获取所有任务信息"""
        return self._tasks.copy()

    def _get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total = len(self._tasks)
        completed = self.get_done_count()
        failed = len(self.get_failed_tasks())
        cancelled = len(self.get_cancelled_tasks())

        return {
            "total": total,
            "active": total - completed,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "success_rate": (completed - failed) / total if total > 0 else 1.0,
        }

    def get_statistics(self) -> dict[str, Any]:
        """获取任务统计信息"""
        stats = self._get_statistics()

        # 添加任务详情
        stats["tasks"] = {
            task_id: {
                "name": task_info.name,
                "done": task_info.is_done,
                "cancelled": task_info.is_cancelled,
                "error": str(task_info.error) if task_info.error else None,
                "duration": task_info.duration,
            }
            for task_id, task_info in self._tasks.items()
        }

        return stats

    def cleanup(self, max_age: float = 3600) -> int:
        """
        清理旧的任务记录

        Args:
            max_age: 任务完成后的保留时间(秒)

        Returns:
            清理的任务数量
        """
        now = datetime.now()
        to_remove = []

        for task_id, task_info in self._tasks.items():
            if task_info.is_done:
                if task_info.completed_at:
                    age = (now - task_info.completed_at).total_seconds()
                    if age > max_age:
                        to_remove.append(task_id)
                else:
                    # 没有完成时间的任务直接清理
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self._tasks[task_id]

        if to_remove:
            logger.debug(f"{self.name} 清理了 {len(to_remove)} 个旧任务记录")

        return len(to_remove)

    def is_running(self) -> bool:
        """检查管理器是否在运行"""
        return self._is_running

    def __len__(self) -> int:
        """返回任务总数"""
        return len(self._tasks)

    def __bool__(self) -> bool:
        """返回是否有活跃任务"""
        return self.get_active_count() > 0

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """异步上下文管理器退出"""
        await self.cancel_all()


# =============================================================================
# 便捷函数
# =============================================================================


def get_task_manager(name: str = "BackgroundTaskManager") -> BackgroundTaskManager:
    """获取后台任务管理器实例"""
    return BackgroundTaskManager(name)


# =============================================================================
# 使用示例
# =============================================================================


async def example_usage():
    """使用示例"""

    # 创建任务管理器
    async with BackgroundTaskManager("示例管理器") as manager:
        # 创建多个后台任务
        async def task1():
            await asyncio.sleep(1)
            return "任务1完成"

        async def task2():
            await asyncio.sleep(2)
            return "任务2完成"

        manager.create_task(task1(), name="任务1")
        manager.create_task(task2(), name="任务2", timeout=5)

        # 查看统计
        print(f"活跃任务: {manager.get_active_count()}")
        print(f"已完成: {manager.get_done_count()}")

        # 等待所有任务完成
        stats = await manager.wait_all(timeout=10)
        print(f"最终统计: {stats}")

    # 管理器自动关闭所有任务


if __name__ == "__main__":
    asyncio.run(example_usage())


# =============================================================================
# 导出
# =============================================================================

# 为保持兼容性，提供 TaskManager 作为别名
TaskManager = BackgroundTaskManager


__all__ = [
    "BackgroundTaskManager",
    "TaskManager",  # 别名
    "TaskInfo",
    "get_task_manager",
]
