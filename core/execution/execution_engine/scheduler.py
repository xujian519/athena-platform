#!/usr/bin/env python3
from __future__ import annotations
"""
执行引擎 - 任务调度器
Execution Engine - Task Scheduler

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from ..types import Task, TaskPriority

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器

    负责管理和调度任务的执行。
    """

    def __init__(self, max_concurrent: int = 10):
        """初始化任务调度器

        Args:
            max_concurrent: 最大并发任务数
        """
        self.max_concurrent = max_concurrent
        self.running_tasks = set()
        self.pending_queue = asyncio.Queue()
        self.priority_queues = {priority: asyncio.Queue() for priority in TaskPriority}
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def schedule_task(self, task: Task):
        """调度任务

        Args:
            task: 要调度的任务
        """
        # 根据优先级放入相应队列
        if task.priority in self.priority_queues:
            await self.priority_queues[task.priority].put(task)
        else:
            await self.pending_queue.put(task)

    async def get_next_task(self) -> Task | None:
        """获取下一个任务

        Returns:
            下一个要执行的任务,如果没有则返回None
        """
        # 按优先级获取任务
        for priority in sorted(TaskPriority, key=lambda x: x.value, reverse=True):
            queue = self.priority_queues.get(priority)
            if queue and not queue.empty():
                return await queue.get()

        # 普通队列
        if not self.pending_queue.empty():
            return await self.pending_queue.get()

        return None

    @asynccontextmanager
    async def acquire_slot(self, task_id: str):
        """获取执行槽位

        Args:
            task_id: 任务ID
        """
        await self.semaphore.acquire()
        self.running_tasks.add(task_id)
        try:
            yield
        finally:
            self.running_tasks.discard(task_id)
            self.semaphore.release()

    def get_status(self) -> dict[str, Any]:
        """获取调度器状态

        Returns:
            调度器状态字典
        """
        return {
            "max_concurrent": self.max_concurrent,
            "running_tasks": len(self.running_tasks),
            "available_slots": self.semaphore._value,
            "pending_tasks": self.pending_queue.qsize(),
            "priority_queues": {
                priority.name: queue.qsize() for priority, queue in self.priority_queues.items()
            },
        }
