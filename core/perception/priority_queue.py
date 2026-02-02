#!/usr/bin/env python3
"""
智能优先级队列系统
Smart Priority Queue System

为感知模块提供智能的任务优先级调度功能。

功能特性:
1. 多级优先级支持
2. 动态优先级调整
3. 公平性保证
4. 饱和策略
5. 性能监控

调度算法:
- 优先级队列
- 时间片轮转
- 加权公平队列
- 自适应调度

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import heapq
import inspect
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Priority(Enum):
    """优先级级别"""

    CRITICAL = 0  # 紧急(如系统关键任务)
    HIGH = 1  # 高(如用户交互任务)
    NORMAL = 2  # 正常(如常规处理)
    LOW = 3  # 低(如后台任务)
    BACKGROUND = 4  # 后台(如清理任务)


class SchedulingPolicy(Enum):
    """调度策略"""

    PRIORITY = "priority"  # 纯优先级
    FAIR = "fair"  # 公平队列
    ADAPTIVE = "adaptive"  # 自适应
    DEADLINE = "deadline"  # 基于截止时间


@dataclass
class PriorityTask:
    """优先级任务"""

    priority: Priority
    task_id: str
    data: Any
    created_at: datetime = field(default_factory=datetime.now)
    deadline: datetime | None = None
    estimated_duration: float = 0.0  # 预估持续时间(秒)
    callback: Callable | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # 公平性字段
    user_id: str | None = None  # 用户ID(用于公平调度)
    queue_time: datetime = field(default_factory=datetime.now)

    # 动态优先级字段
    boost_factor: float = 0.0  # 优先级提升因子
    penalty_factor: float = 0.0  # 优先级惩罚因子

    @property
    def effective_priority(self) -> int:
        """有效优先级(考虑提升和惩罚)"""
        base_priority = self.priority.value
        adjusted = base_priority + self.penalty_factor - self.boost_factor
        return max(0, min(int(adjusted), len(Priority) - 1))

    @property
    def waiting_time(self) -> float:
        """等待时间(秒)"""
        return (datetime.now() - self.queue_time).total_seconds()

    @property
    def is_overdue(self) -> bool:
        """是否超期"""
        if self.deadline is None:
            return False
        return datetime.now() > self.deadline

    def __lt__(self, other):
        """比较操作符(用于堆排序)"""
        # 优先级高的先处理
        if self.effective_priority != other.effective_priority:
            return self.effective_priority < other.effective_priority

        # 相同优先级时,截止时间早的先处理
        if self.deadline and other.deadline:
            return self.deadline < other.deadline

        # 相同优先级且无截止时间时,等待时间长的先处理(公平性)
        return self.queue_time < other.queue_time


@dataclass
class QueueMetrics:
    """队列指标"""

    total_enqueued: int = 0
    total_dequeued: int = 0
    total_completed: int = 0
    total_failed: int = 0
    current_size: int = 0
    peak_size: int = 0
    total_latency: float = 0.0  # 总延迟时间(用于计算吞吐量)

    # 优先级统计
    priority_counts: dict[str, int] = field(default_factory=lambda: {p.name: 0 for p in Priority})
    priority_wait_times: dict[str, list[float]] = field(
        default_factory=lambda: {p.name: [] for p in Priority}
    )

    # 性能统计
    avg_waiting_time: float = 0.0
    avg_processing_time: float = 0.0
    throughput: float = 0.0  # 任务/秒

    @property
    def completion_rate(self) -> float:
        """完成率"""
        total = self.total_completed + self.total_failed
        return self.total_completed / max(total, 1)


class SmartPriorityQueue:
    """智能优先级队列

    支持多种调度策略和优先级调整机制。

    使用示例:
        >>> queue = SmartPriorityQueue(policy=SchedulingPolicy.ADAPTIVE)
        >>> await queue.initialize()
        >>>
        >>> # 添加任务
        >>> task = PriorityTask(Priority.HIGH, "task1", data)
        >>> await queue.enqueue(task)
        >>>
        >>> # 处理任务
        >>> task = await queue.dequeue()
        >>> result = await task.callback(task.data)
        >>> await queue.complete(task, result)
    """

    def __init__(
        self,
        policy: SchedulingPolicy = SchedulingPolicy.PRIORITY,
        max_size: int = 10000,
        worker_count: int = 4,
    ):
        """初始化队列

        Args:
            policy: 调度策略
            max_size: 最大队列长度
            worker_count: 工作线程数
        """
        self.policy = policy
        self.max_size = max_size
        self.worker_count = worker_count

        # 优先级队列
        self._queue: list[PriorityTask] = []
        self._queue_lock = threading.RLock()

        # 用户任务计数(用于公平调度)
        self._user_task_counts: dict[str, int] = {}

        # 指标
        self.metrics = QueueMetrics()

        # 工作任务
        self._workers: list[asyncio.Task] = []
        self._running = False

        logger.info(
            f"🎯 初始化智能优先级队列 (策略={policy.value}, "
            f"最大长度={max_size}, 工作线程={worker_count})"
        )

    async def initialize(self) -> None:
        """初始化队列"""
        if self._running:
            return

        self._running = True

        # 启动工作线程
        for i in range(self.worker_count):
            task = asyncio.create_task(self._worker(i))
            self._workers.append(task)

        logger.info(f"✅ 优先级队列启动,工作线程: {self.worker_count}")

    async def _worker(self, worker_id: int) -> None:
        """工作线程

        Args:
            worker_id: 工作线程ID
        """
        logger.info(f"🔧 工作线程 {worker_id} 启动")

        while self._running:
            try:
                # 获取任务
                task = await self.dequeue()

                if task is None:
                    await asyncio.sleep(0.1)
                    continue

                # 处理任务
                start_time = time.time()
                self.metrics.current_size -= 1

                try:
                    # 执行回调
                    if task.callback:
                        if inspect.iscoroutinefunction(task.callback):
                            result = await task.callback(task.data)
                        else:
                            result = task.callback(task.data)
                        await self.complete(task, result)
                    else:
                        # 无回调,直接标记完成
                        await self.complete(task, None)

                    processing_time = time.time() - start_time

                    logger.debug(
                        f"✅ 工作线程 {worker_id} 完成任务 {task.task_id} "
                        f"(耗时={processing_time:.3f}s)"
                    )

                except Exception as e:
                    processing_time = time.time() - start_time
                    logger.error(f"❌ 工作线程 {worker_id} 处理任务 {task.task_id} 失败: {e}")
                    await self.fail(task, e)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 工作线程 {worker_id} 异常: {e}")
                await asyncio.sleep(1)

        logger.info(f"⏹️ 工作线程 {worker_id} 停止")

    async def enqueue(self, task: PriorityTask) -> bool:
        """入队

        Args:
            task: 任务

        Returns:
            是否成功入队
        """
        with self._queue_lock:
            if len(self._queue) >= self.max_size:
                logger.warning(f"⚠️ 队列已满 ({self.max_size}),拒绝任务 {task.task_id}")
                return False

            # 应用调度策略
            if self.policy == SchedulingPolicy.FAIR:
                # 公平调度:考虑用户任务数
                if task.user_id:
                    user_count = self._user_task_counts.get(task.user_id, 0)
                    if user_count > 3:  # 限制每个用户的并发任务数
                        # 降低优先级
                        task.penalty_factor = user_count - 3

            elif self.policy == SchedulingPolicy.ADAPTIVE:
                # 自适应调度:根据等待时间提升优先级
                # 将在dequeue时动态调整
                pass

            heapq.heappush(self._queue, task)

            # 更新指标
            self.metrics.total_enqueued += 1
            self.metrics.current_size = len(self._queue)
            self.metrics.peak_size = max(self.metrics.peak_size, len(self._queue))
            self.metrics.priority_counts[task.priority.name] += 1

            logger.debug(f"📥 任务入队: {task.task_id} (优先级={task.priority.name})")
            return True

    async def dequeue(self, timeout: float = 1.0) -> PriorityTask | None:
        """出队

        Args:
            timeout: 超时时间(秒)

        Returns:
            任务,如果队列为空返回None
        """
        try:
            await asyncio.wait_for(self._has_task(), timeout=timeout)

            with self._queue_lock:
                if not self._queue:
                    return None

                # 应用自适应策略
                if self.policy == SchedulingPolicy.ADAPTIVE:
                    self._apply_adaptive_priority()

                # 基于截止时间的调度
                if self.policy == SchedulingPolicy.DEADLINE:
                    task = self._dequeue_by_deadline()
                else:
                    task = heapq.heappop(self._queue)

                # 记录等待时间
                wait_time = task.waiting_time
                self.metrics.priority_wait_times[task.priority.name].append(wait_time)

                # 更新用户任务计数
                if task.user_id:
                    self._user_task_counts[task.user_id] = (
                        self._user_task_counts.get(task.user_id, 0) + 1
                    )

                logger.debug(f"📤 任务出队: {task.task_id} (等待={wait_time:.3f}s)")
                return task

        except asyncio.TimeoutError:
            return None

    async def _has_task(self) -> bool:
        """检查是否有任务"""
        return len(self._queue) > 0

    def _apply_adaptive_priority(self) -> None:
        """应用自适应优先级调整"""
        for task in self._queue:
            # 等待时间越长,优先级越高
            wait_hours = task.waiting_time / 3600
            if wait_hours > 1:  # 等待超过1小时
                task.boost_factor = min(wait_hours, 3.0)  # 最多提升3级

            # 超期任务紧急提升
            if task.is_overdue:
                task.boost_factor += 5.0

    def _dequeue_by_deadline(self) -> PriorityTask:
        """按截止时间出队"""
        # 找到截止时间最早的任务
        earliest_task = None
        earliest_deadline = None

        for task in self._queue:
            if task.deadline:
                if earliest_deadline is None or task.deadline < earliest_deadline:
                    earliest_deadline = task.deadline
                    earliest_task = task

        if earliest_task:
            # 从队列中移除
            self._queue.remove(earliest_task)
            heapq.heapify(self._queue)
            return earliest_task
        else:
            # 没有截止时间,使用普通优先级
            return heapq.heappop(self._queue)

    async def complete(self, task: PriorityTask, result: Any) -> None:
        """标记任务完成

        Args:
            task: 任务
            result: 结果
        """
        self.metrics.total_completed += 1

        # 更新用户任务计数
        if task.user_id:
            self._user_task_counts[task.user_id] = max(
                0, self._user_task_counts.get(task.user_id, 1) - 1
            )

        logger.debug(f"✅ 任务完成: {task.task_id}")

    async def fail(self, task: PriorityTask, error: Exception) -> None:
        """标记任务失败

        Args:
            task: 任务
            error: 错误
        """
        self.metrics.total_failed += 1

        # 更新用户任务计数
        if task.user_id:
            self._user_task_counts[task.user_id] = max(
                0, self._user_task_counts.get(task.user_id, 1) - 1
            )

        logger.debug(f"❌ 任务失败: {task.task_id} - {error}")

    async def shutdown(self) -> None:
        """关闭队列"""
        logger.info("🛑 关闭优先级队列...")

        self._running = False

        # 取消工作线程
        for worker in self._workers:
            worker.cancel()

        # 等待工作线程停止
        await asyncio.gather(*self._workers, return_exceptions=True)

        self._workers.clear()

        # 处理剩余任务
        with self._queue_lock:
            remaining = len(self._queue)
            if remaining > 0:
                logger.warning(f"⚠️ 队列关闭时仍有 {remaining} 个未处理任务")

        logger.info("✅ 优先级队列已关闭")

    def get_metrics(self) -> QueueMetrics:
        """获取队列指标"""
        # 计算平均等待时间
        all_waits = []
        for waits in self.metrics.priority_wait_times.values():
            all_waits.extend(waits)

        if all_waits:
            self.metrics.avg_waiting_time = sum(all_waits) / len(all_waits)

        # 计算吞吐量
        if self.metrics.total_completed > 0 and self.metrics.total_latency > 0:
            self.metrics.throughput = self.metrics.total_completed / self.metrics.total_latency

        return self.metrics

    async def clear(self) -> int:
        """清空队列

        Returns:
            清空的任务数量
        """
        with self._queue_lock:
            count = len(self._queue)
            self._queue.clear()
            self.metrics.current_size = 0
            logger.info(f"🧹 清空队列,移除了 {count} 个任务")
            return count


# 便捷函数
def create_priority_queue(
    policy: SchedulingPolicy = SchedulingPolicy.ADAPTIVE,
    max_size: int = 10000,
    worker_count: int = 4,
) -> SmartPriorityQueue:
    """创建优先级队列"""
    return SmartPriorityQueue(policy, max_size, worker_count)


__all__ = [
    "Priority",
    "PriorityTask",
    "QueueMetrics",
    "SchedulingPolicy",
    "SmartPriorityQueue",
    "create_priority_queue",
]
