#!/usr/bin/env python3
from __future__ import annotations
"""
Athena 感知模块 - 异步任务队列
支持任务优先级、并发控制、状态跟踪
最后更新: 2026-01-26
"""

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """任务数据类"""
    id: str
    func: Callable[..., Awaitable[Any]]
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration(self) -> float | None:
        """获取任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AsyncTaskQueue:
    """
    异步任务队列

    功能：
    - 任务优先级管理
    - 并发控制
    - 任务状态跟踪
    - 任务结果存储
    - 自动重试
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        max_queue_size: int = 1000
    ):
        """
        初始化任务队列

        Args:
            max_concurrent_tasks: 最大并发任务数
            max_queue_size: 最大队列长度
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_queue_size = max_queue_size

        # 任务队列（按优先级排序）
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)

        # 任务存储
        self._tasks: dict[str, Task] = {}

        # 并发控制
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # 工作任务
        self._worker_tasks: list[asyncio.Task] = []

        # 队列状态
        self._running = False
        self._paused = False

        # 统计信息
        self.stats = {
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "total_duration": 0.0
        }

        logger.info(f"✓ 异步任务队列已初始化 (最大并发: {max_concurrent_tasks})")

    async def start(self, num_workers: int = None):
        """
        启动任务队列

        Args:
            num_workers: 工作协程数量，默认等于max_concurrent_tasks
        """
        if self._running:
            logger.warning("任务队列已在运行中")
            return

        num_workers = num_workers or self.max_concurrent_tasks
        self._running = True
        self._paused = False

        # 创建工作协程
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)

        logger.info(f"✓ 任务队列已启动 ({num_workers}个工作协程)")

    async def stop(self, wait_for_completion: bool = True):
        """
        停止任务队列

        Args:
            wait_for_completion: 是否等待当前任务完成
        """
        if not self._running:
            return

        self._running = False

        # 取消所有工作协程
        for worker_task in self._worker_tasks:
            if wait_for_completion:
                await worker_task
            else:
                worker_task.cancel()

        self._worker_tasks.clear()
        logger.info("✓ 任务队列已停止")

    async def pause(self):
        """暂停任务队列"""
        self._paused = True
        logger.info("✓ 任务队列已暂停")

    async def resume(self):
        """恢复任务队列"""
        self._paused = False
        logger.info("✓ 任务队列已恢复")

    async def submit(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs
    ) -> str:
        """
        提交任务到队列

        Args:
            func: 异步函数
            *args: 函数参数
            priority: 任务优先级
            **kwargs: 函数关键字参数

        Returns:
            任务ID
        """
        if not self._running:
            raise RuntimeError("任务队列未启动")

        task_id = str(uuid.uuid4())

        # 创建任务对象
        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )

        # 存储任务
        self._tasks[task_id] = task

        # 添加到队列（使用优先级的负值作为排序键，使高优先级先执行）
        try:
            await self._queue.put((-priority.value, task_id))
            self.stats["submitted"] += 1
            logger.debug(f"✓ 任务已提交: {task_id} (优先级: {priority.name})")
            return task_id
        except asyncio.QueueFull:
            del self._tasks[task_id]
            raise RuntimeError("任务队列已满") from None

    async def get_task(self, task_id: str) -> Task | None:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务对象，不存在返回None
        """
        return self._tasks.get(task_id)

    async def get_task_result(
        self,
        task_id: str,
        timeout: float | None = None
    ) -> Any:
        """
        等待任务完成并获取结果

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            任务结果

        Raises:
            TimeoutError: 等待超时
            RuntimeError: 任务失败
        """
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 等待任务完成
        start_time = datetime.now()
        while task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"等待任务超时: {task_id}")
            await asyncio.sleep(0.1)

        # 检查任务状态
        if task.status == TaskStatus.COMPLETED:
            return task.result
        elif task.status == TaskStatus.FAILED:
            raise RuntimeError(f"任务失败: {task.error}")
        else:
            raise RuntimeError(f"任务被取消: {task_id}")

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status == TaskStatus.RUNNING:
            # 正在运行的任务无法取消
            logger.warning(f"无法取消正在运行的任务: {task_id}")
            return False

        task.status = TaskStatus.CANCELLED
        self.stats["cancelled"] += 1
        logger.info(f"✓ 任务已取消: {task_id}")
        return True

    async def clear(self):
        """清空队列"""
        # 清空优先队列
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # 清空任务存储（只删除未开始的任务）
        to_delete = [
            task_id for task_id, task in self._tasks.items()
            if task.status == TaskStatus.PENDING
        ]
        for task_id in to_delete:
            del self._tasks[task_id]

        logger.info(f"✓ 队列已清空 (删除了{len(to_delete)}个待处理任务)")

    async def _worker(self, worker_name: str):
        """
        工作协程

        Args:
            worker_name: 工作协程名称
        """
        logger.info(f"✓ 工作协程启动: {worker_name}")

        while self._running:
            try:
                # 检查是否暂停
                if self._paused:
                    await asyncio.sleep(0.5)
                    continue

                # 获取任务（带超时，避免永久阻塞）
                try:
                    _, task_id = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                task = self._tasks.get(task_id)
                if not task:
                    continue

                # 执行任务
                await self._execute_task(task, worker_name)

            except Exception as e:
                logger.error(f"❌ 工作协程错误 ({worker_name}): {e}")

        logger.info(f"✓ 工作协程停止: {worker_name}")

    async def _execute_task(self, task: Task, worker_name: str):
        """
        执行任务

        Args:
            task: 任务对象
            worker_name: 工作协程名称
        """
        # 使用信号量控制并发
        async with self._semaphore:
            try:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()

                logger.debug(f"[{worker_name}] 开始执行任务: {task.id}")

                # 执行任务函数
                result = await task.func(*task.args, **task.kwargs)

                # 任务完成
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now()

                self.stats["completed"] += 1
                self.stats["total_duration"] += task.duration or 0

                logger.debug(f"[{worker_name}] 任务完成: {task.id} (耗时: {task.duration:.2f}s)")

            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                self.stats["cancelled"] += 1
                logger.info(f"[{worker_name}] 任务被取消: {task.id}")

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                self.stats["failed"] += 1
                logger.error(f"[{worker_name}] 任务失败: {task.id} - {e}")

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        # 统计各状态任务数量
        status_counts = {}
        for status in TaskStatus:
            count = sum(
                1 for task in self._tasks.values()
                if task.status == status
            )
            status_counts[status.value] = count

        # 计算平均执行时间
        avg_duration = 0
        if self.stats["completed"] > 0:
            avg_duration = self.stats["total_duration"] / self.stats["completed"]

        return {
            "running": self._running,
            "paused": self._paused,
            "queue_size": self._queue.qsize(),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_workers": len(self._worker_tasks),
            "task_counts": status_counts,
            "total_submitted": self.stats["submitted"],
            "total_completed": self.stats["completed"],
            "total_failed": self.stats["failed"],
            "total_cancelled": self.stats["cancelled"],
            "avg_duration": avg_duration,
            "success_rate": (
                self.stats["completed"] / self.stats["submitted"]
                if self.stats["submitted"] > 0 else 0
            )
        }

    def get_queue_info(self) -> list[dict[str, Any]]:
        """
        获取队列信息

        Returns:
            任务信息列表
        """
        tasks_info = []
        for task in self._tasks.values():
            tasks_info.append({
                "id": task.id,
                "status": task.status.value,
                "priority": task.priority.name,
                "created_at": task.created_at.isoformat(),
                "duration": task.duration
            })

        # 按创建时间排序
        tasks_info.sort(key=lambda x: x["created_at"])

        return tasks_info


# 使用示例
if __name__ == "__main__":
    async def sample_task(name: str, duration: float) -> str:
        """示例任务"""
        print(f"任务 {name} 开始执行")
        await asyncio.sleep(duration)
        print(f"任务 {name} 执行完成")
        return f"任务 {name} 的结果"

    async def test():
        # 创建任务队列
        queue = AsyncTaskQueue(max_concurrent_tasks=3)

        # 启动队列
        await queue.start(num_workers=2)

        # 提交任务
        task_ids = []
        for i in range(5):
            priority = (
                TaskPriority.HIGH if i == 0 else
                TaskPriority.URGENT if i == 1 else
                TaskPriority.NORMAL
            )
            task_id = await queue.submit(
                sample_task,
                f"task-{i}",
                1.0,
                priority=priority
            )
            task_ids.append(task_id)

        # 等待所有任务完成
        results = []
        for task_id in task_ids:
            result = await queue.get_task_result(task_id, timeout=30)
            results.append(result)
            print(f"任务结果: {result}")

        # 显示统计信息
        print("\n=== 队列统计 ===")
        stats = queue.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        # 停止队列
        await queue.stop()

    asyncio.run(test())
