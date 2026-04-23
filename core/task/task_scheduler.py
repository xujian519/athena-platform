from __future__ import annotations
"""
TaskScheduler - 任务调度器
支持任务调度和优先级管理。
"""

import heapq
import logging
import threading
from collections.abc import Callable
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field

from core.agents.task_tool.background_task_manager import BackgroundTaskManager
from core.agents.task_tool.models import BackgroundTask, TaskStatus

logger = logging.getLogger(__name__)


@dataclass(order=True)
class ScheduledTask:
    """调度任务数据类"""

    priority: int  # 优先级，数字越大优先级越高
    task_id: str  # 任务ID（用于排序时的唯一标识）
    task: BackgroundTask  # 实际任务
    timeout: Optional[float] = None  # 超时时间（秒）
    created_at: float = field(default_factory=lambda: __import__("time").time())


class TaskScheduler:
    """任务调度器类

    负责管理任务的调度和优先级管理。
    """

    def __init__(
        self,
        background_manager: BackgroundTaskManager,
        max_concurrent: int = 10,
    ):
        """初始化TaskScheduler

        Args:
            background_manager: 后台任务管理器
            max_concurrent: 最大并发任务数
        """
        self._background_manager = background_manager
        self._max_concurrent = max_concurrent
        self._pending_queue: list[ScheduledTask] = []
        self._lock: threading.Lock = threading.Lock()
        self._scheduler_thread: threading.Thread | None = None
        self._running: bool = False

        logger.info("✅ TaskScheduler初始化完成")

    def schedule_task(
        self,
        func: Callable,
        priority: int = 5,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> BackgroundTask:
        """调度任务

        Args:
            func: 要执行的函数
            priority: 任务优先级 (1-10, 数字越大优先级越高)
            timeout: 超时时间（秒）
            **kwargs: 传递给BackgroundTaskManager.submit的参数

        Returns:
            BackgroundTask对象
        """
        # 提交任务到后台管理器
        task = self._background_manager.submit(func, **kwargs)

        # 创建调度任务
        scheduled_task = ScheduledTask(
            priority=priority,
            task_id=task.task_id,
            task=task,
            timeout=timeout,
        )

        # 添加到待处理队列（使用堆实现优先级队列）
        with self._lock:
            heapq.heappush(self._pending_queue, scheduled_task)

        logger.info(f"✅ 任务已调度: {task.task_id} (优先级: {priority}, 超时: {timeout}s)")

        return task

    def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        # 从待处理队列中移除
        with self._lock:
            for i, scheduled_task in enumerate(self._pending_queue):
                if scheduled_task.task_id == task_id:
                    # 从堆中移除（标记为已取消）
                    self._pending_queue[i].task.update_status(TaskStatus.CANCELLED)
                    logger.info(f"✅ 任务已取消: {task_id}")
                    return True

        # 尝试取消后台任务
        return self._background_manager.cancel(task_id)

    def get_pending_queue(self) -> list[BackgroundTask]:
        """获取待处理队列

        Returns:
            按优先级排序的待处理任务列表
        """
        with self._lock:
            # 创建副本并按优先级排序（从高到低）
            pending_tasks = [st.task for st in self._pending_queue]
            pending_tasks.sort(
                key=lambda t: next(
                    (st.priority for st in self._pending_queue if st.task_id == t.task_id),
                    0,
                ),
                reverse=True,
            )
            return pending_tasks

    def get_running_tasks(self) -> list[BackgroundTask]:
        """获取运行中的任务

        Returns:
            运行中的任务列表
        """
        return self._background_manager.get_running_tasks()

    def get_task(self, task_id: str) -> BackgroundTask | None:
        """获取任务

        Args:
            task_id: 任务ID

        Returns:
            BackgroundTask对象，如果不存在返回None
        """
        return self._background_manager.get_task(task_id)

    def start(self) -> None:
        """启动调度器"""
        if self._running:
            logger.warning("⚠️ 调度器已在运行")
            return

        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

        logger.info("✅ 调度器已启动")

    def stop(self) -> None:
        """停止调度器"""
        self._running = False

        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5.0)

        logger.info("⏹️ 调度器已停止")

    def _scheduler_loop(self) -> None:
        """调度器主循环"""
        while self._running:
            try:
                self._process_next_task()
            except Exception as e:
                logger.error(f"❌ 调度器循环错误: {e}", exc_info=True)

    def _process_next_task(self) -> None:
        """处理下一个待处理任务"""
        with self._lock:
            # 获取当前运行的任务数
            running_count = len(self.get_running_tasks())

            # 如果已达到最大并发数，等待
            if running_count >= self._max_concurrent:
                return

            # 检查是否有待处理任务
            if not self._pending_queue:
                return

            # 从优先级队列中取出最高优先级的任务
            scheduled_task = heapq.heappop(self._pending_queue)

            # 更新任务状态
            scheduled_task.task.update_status(TaskStatus.RUNNING)

        # 执行任务（在锁外）
        try:
            if scheduled_task.timeout:
                # 带超时的任务
                scheduled_task.task.future.result(timeout=scheduled_task.timeout)
                scheduled_task.task.update_status(TaskStatus.COMPLETED)
            else:
                # 不带超时的任务
                scheduled_task.task.future.result()
                scheduled_task.task.update_status(TaskStatus.COMPLETED)

            logger.info(f"✅ 任务完成: {scheduled_task.task_id}")
        except FutureTimeoutError:
            scheduled_task.task.update_status(TaskStatus.FAILED)
            logger.error(f"❌ 任务超时: {scheduled_task.task_id}")
        except Exception as e:
            scheduled_task.task.update_status(TaskStatus.FAILED)
            logger.error(f"❌ 任务失败: {scheduled_task.task_id} - {e}")


__all__ = ["TaskScheduler", "ScheduledTask"]
