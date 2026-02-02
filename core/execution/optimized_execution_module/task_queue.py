#!/usr/bin/env python3
"""
优化版执行模块 - 任务优先级队列
Optimized Execution Module - Task Priority Queue

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import heapq
import threading
from typing import Any

from .types import Task


class TaskPriorityQueue:
    """任务优先级队列 - 线程安全的优先级队列实现"""

    def __init__(self):
        """初始化优先级队列"""
        self._queue = []
        self._tasks = {}
        self._lock = threading.RLock()
        self._counter = 0  # 用于相同优先级的FIFO排序

    def put(self, task: Task) -> Any:
        """添加任务到队列

        Args:
            task: 要添加的任务对象

        Returns:
            入队操作的结果
        """
        with self._lock:
            # 优先级越小,优先级越高
            priority_value = task.priority.value
            heapq.heappush(self._queue, (priority_value, self._counter, task.task_id))
            self._tasks[task.task_id] = task
            self._counter += 1

    def get(self) -> Task | None:
        """从队列获取最高优先级任务

        Returns:
            最高优先级任务,如果队列为空则返回None
        """
        with self._lock:
            while self._queue:
                _, _, task_id = heapq.heappop(self._queue)
                if task_id in self._tasks:
                    task = self._tasks.pop(task_id)
                    return task
            return None

    def peek(self) -> Task | None:
        """查看最高优先级任务但不移除

        Returns:
            最高优先级任务,如果队列为空则返回None
        """
        with self._lock:
            while self._queue:
                _, _, task_id = self._queue[0]
                if task_id in self._tasks:
                    return self._tasks[task_id]
                heapq.heappop(self._queue)
            return None

    def remove(self, task_id: str) -> bool:
        """从队列移除指定任务

        Args:
            task_id: 要移除的任务ID

        Returns:
            是否成功移除
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    def size(self) -> int:
        """获取队列大小

        Returns:
            队列中的任务数量
        """
        with self._lock:
            return len(self._queue)

    def is_empty(self) -> bool:
        """检查队列是否为空

        Returns:
            队列是否为空
        """
        with self._lock:
            return len(self._queue) == 0
