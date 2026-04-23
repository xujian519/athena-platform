"""
任务调度器实现

负责任务的优先级调度和队列管理。
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from collections import deque
import logging
import heapq
from datetime import datetime

from .types import TaskInfo, TaskPriority, AgentInfo, SchedulingResult


logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    任务调度器

    实现基于优先级的任务调度和队列管理。
    """

    def __init__(self):
        """初始化调度器"""
        self._queue: List[Tuple[int, TaskInfo]] = []  # 优先级队列
        self._task_map: Dict[str, TaskInfo] = {}  # 任务映射
        self._priority_map = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }
        self._counter = 0  # 用于保持FIFO顺序的计数器

    async def submit(self, task: TaskInfo) -> bool:
        """
        提交任务到队列

        Args:
            task: 任务信息

        Returns:
            是否成功提交
        """
        if task.task_id in self._task_map:
            logger.warning(f"Task {task.task_id} already in queue")
            return False

        priority = self._priority_map[task.priority]
        # 使用计数器确保相同优先级的任务按FIFO顺序处理
        heapq.heappush(self._queue, (priority, self._counter, task))
        self._counter += 1
        self._task_map[task.task_id] = task

        logger.info(f"Task {task.task_id} added to queue with priority {task.priority}")
        return True

    async def get_next_task(self) -> Optional[TaskInfo]:
        """
        获取下一个待处理任务

        Returns:
            任务信息，如果队列为空则返回None
        """
        if not self._queue:
            return None

        priority, counter, task = heapq.heappop(self._queue)
        if task.task_id in self._task_map:
            del self._task_map[task.task_id]
            logger.info(f"Task {task.task_id} retrieved from queue")
            return task

        return None

    async def peek_next_task(self) -> Optional[TaskInfo]:
        """
        查看下一个待处理任务（不移除）

        Returns:
            任务信息，如果队列为空则返回None
        """
        if not self._queue:
            return None

        return self._queue[0][2]

    async def remove_task(self, task_id: str) -> bool:
        """
        从队列中移除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功移除
        """
        if task_id not in self._task_map:
            return False

        # 标记为已删除，实际从队列中移除在get_next_task时处理
        del self._task_map[task_id]
        logger.info(f"Task {task_id} removed from queue")
        return True

    async def get_queue_size(self) -> int:
        """获取队列大小"""
        return len(self._queue)

    async def get_queue_status(self) -> Dict[str, int]:
        """获取队列状态"""
        # 统计各优先级的任务数量
        priority_counts = {p: 0 for p in TaskPriority}
        for task in self._task_map.values():
            priority_counts[task.priority] += 1

        return {
            "total_pending": len(self._queue),
            "critical": priority_counts[TaskPriority.CRITICAL],
            "high": priority_counts[TaskPriority.HIGH],
            "medium": priority_counts[TaskPriority.MEDIUM],
            "low": priority_counts[TaskPriority.LOW],
        }

    async def has_pending_tasks(self) -> bool:
        """检查是否有待处理任务"""
        return len(self._queue) > 0
