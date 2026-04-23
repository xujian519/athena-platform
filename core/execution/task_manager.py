#!/usr/bin/env python3
from __future__ import annotations
"""
任务管理器 - 兼容性实现
Task Manager - Compatibility Implementation

为优化后的系统提供任务管理功能的兼容性接口。
使用统一的类型定义(从 shared_types.py 导入)。

作者: Athena AI系统
创建时间: 2025-12-11
版本: 2.0.0
更新时间: 2026-01-27
"""

import asyncio
import inspect
import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

# 从统一的 shared_types.py 导入类型定义
from .shared_types import Task, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器 - 使用统一的Task类型"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.tasks: dict[str, Task] = {}
        self.task_queue = asyncio.Queue()
        self.running_tasks: dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 10)
        self.default_timeout = self.config.get("default_timeout", timedelta(minutes=5))
        self.initialized = False
        self.running = False

    async def initialize(self):
        """初始化任务管理器"""
        if self.initialized:
            return

        try:
            self.running = True

            # 启动任务执行器
            for _ in range(self.max_concurrent_tasks):
                asyncio.create_task(self._task_executor())

            self.initialized = True
            logger.info("✅ 任务管理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 任务管理器初始化失败: {e}")
            raise

    async def shutdown(self):
        """关闭任务管理器"""
        self.running = False

        # 取消所有运行中的任务
        for task_id, task in self.running_tasks.items():
            task.cancel()
            logger.info(f"取消任务: {task_id}")

        self.running_tasks.clear()
        logger.info("任务管理器已关闭")

    async def create_task(
        self,
        name: str,
        function: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        description: str = "",
        timeout: timedelta | None = None,
        max_retries: int = 0,
    ) -> str:
        """
        创建新任务

        Args:
            name: 任务名称
            function: 任务函数
            args: 位置参数
            kwargs: 关键字参数
            priority: 优先级
            description: 任务描述
            timeout: 超时时间
            max_retries: 最大重试次数

        Returns:
            任务ID
        """
        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 处理 timeout 参数 - 转换为秒数
        timeout_seconds = timeout.total_seconds() if timeout else None
        default_timeout_seconds = (
            self.default_timeout.total_seconds() if self.default_timeout else None
        )

        task = Task(
            task_id=task_id,
            name=name,
            description=description,
            function=function,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            timeout=timeout_seconds or default_timeout_seconds,
            max_retries=max_retries,
        )

        self.tasks[task.task_id] = task
        await self.task_queue.put(task)

        logger.info(f"创建任务: {name} (ID: {task.task_id})")
        return task.task_id

    async def get_task(self, task_id: str) -> Task | None:
        """获取任务"""
        return self.tasks.get(task_id)

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """获取任务状态"""
        task = await self.get_task(task_id)
        return task.status if task else None

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = await self.get_task(task_id)
        if not task:
            return False

        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]

        task.status = TaskStatus.CANCELLED
        logger.info(f"任务已取消: {task_id}")
        return True

    async def wait_for_task(self, task_id: str, timeout: timedelta | None = None) -> Any:
        """等待任务完成"""
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        start_time = datetime.now()
        check_interval = 0.1

        while True:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if task.status == TaskStatus.COMPLETED:
                    return task.result
                elif task.status == TaskStatus.FAILED:
                    raise Exception(task.error or "任务执行失败")
                else:
                    raise Exception("任务已取消")

            if timeout and (datetime.now() - start_time) > timeout:
                raise asyncio.TimeoutError(f"任务超时: {task_id}")

            await asyncio.sleep(check_interval)

    async def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        """列出任务"""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    async def clear_completed_tasks(self, older_than: timedelta = timedelta(hours=1)):
        """清理已完成的任务"""
        cutoff_time = datetime.now() - older_than
        tasks_to_remove = []

        for task_id, task in self.tasks.items():
            if (
                task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at
                and task.completed_at < cutoff_time
            ):
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.tasks[task_id]

        logger.info(f"清理了 {len(tasks_to_remove)} 个已完成的任务")

    async def _task_executor(self):
        """任务执行器"""
        while self.running:
            try:
                # 获取任务
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                # 执行任务
                await self._execute_task(task)

            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"任务执行器异常: {e}")

    async def _execute_task(self, task: Task):
        """执行单个任务"""
        task_id = task.task_id

        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            logger.info(f"开始执行任务: {task.name}")

            # 创建执行任务
            execute_coro = self._run_task_function(task)
            if task.timeout:
                execute_coro = asyncio.wait_for(execute_coro, timeout=task.timeout)

            # 启动执行
            execution_task = asyncio.create_task(execute_coro)
            self.running_tasks[task_id] = execution_task

            try:
                result = await execution_task
                task.complete(True, result)
                logger.info(f"任务完成: {task.name}")

            except TimeoutError:
                task.complete(False, error="任务执行超时")
                logger.error(f"任务超时: {task.name}")

            except Exception as e:
                task.complete(False, error=str(e))
                logger.error(f"任务执行失败: {task.name} - {e}")

                # 重试逻辑
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.PENDING
                    await self.task_queue.put(task)
                    logger.info(f"任务重试 ({task.retry_count}/{task.max_retries}): {task.name}")

            finally:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

        except Exception as e:
            logger.error(f"任务执行异常: {task_id} - {e}")
            task.complete(False, error=str(e))

    async def _run_task_function(self, task: Task) -> Any:
        """运行任务函数"""
        if task.function is None:
            raise RuntimeError(f"任务 {task.task_id} 没有可执行的函数")

        if inspect.iscoroutinefunction(task.function):
            return await task.function(*task.args, **task.kwargs)
        else:
            # 在线程池中运行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, task.function, *task.args, **task.kwargs)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_tasks = len(self.tasks)
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(1 for t in self.tasks.values() if t.status == status)

        return {
            "total_tasks": total_tasks,
            "running_tasks": len(self.running_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "status_distribution": status_counts,
            "max_concurrent": self.max_concurrent_tasks,
        }


# 兼容性函数
def create_task_manager(config: Optional[dict[str, Any]] = None) -> TaskManager:
    """创建任务管理器实例"""
    return TaskManager(config if config is not None else {})
