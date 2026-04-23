from __future__ import annotations
"""
BackgroundTaskManager - 后台任务管理器

支持异步任务执行、取消和状态管理。
"""

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from core.framework.agents.task_tool.models import BackgroundTask, TaskInput, TaskStatus


class BackgroundTaskManager:
    """后台任务管理器类

    负责管理后台执行的任务，支持：
    - 任务提交和异步执行
    - 任务取消
    - 任务状态查询
    - 并发控制（使用信号量）
    - 优雅关闭
    """

    def __init__(self, max_workers: int = 10):
        """初始化BackgroundTaskManager

        Args:
            max_workers: 最大并发任务数，默认为10
        """
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Optional[dict[str, BackgroundTask] = {}
        self._lock: threading.Lock = threading.Lock()
        self._max_workers: int = max_workers
        self._is_shutdown: bool = False

    def submit(
        self,
        func: Callable,
        args: Optional[tuple[Any, ...]] = None,]

        kwargs: Optional[dict[str, Any]],]

        agent_id: Optional[str] = None,
        input_data: Optional[TaskInput ] = None,
    ) -> str:
        """提交后台任务

        Args:
            func: 要执行的函数
            args: 函数位置参数
            kwargs: 函数关键字参数
            agent_id: 代理ID
            input_data: 任务输入数据

        Returns:
            BackgroundTask对象

        Raises:
            RuntimeError: 如果管理器已关闭
        """
        if self._is_shutdown:
            raise RuntimeError("BackgroundTaskManager has been shut down")

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 准备任务参数
        task_args = args if args is not None else ()
        task_kwargs = kwargs if kwargs is not None else {}

        # 提交任务到线程池
        future = self._executor.submit(self._execute_task, func, task_args, task_kwargs, task_id)

        # 创建BackgroundTask对象
        task = BackgroundTask(
            task_id=task_id,
            status=TaskStatus.PENDING,
            future=future,
            agent_id=agent_id or "unknown",
            input_data=input_data,
        )

        # 存储任务
        with self._lock:
            self._tasks[task_id] = task

        return task

    def _execute_task(
        self,
        func: Callable,
        args: Optional[tuple[Any, ...],]

        kwargs: Optional[dict[str, Any],]

        task_id: str,
    ) -> str:
        """执行任务的包装函数

        Args:
            func: 要执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
            task_id: 任务ID

        Returns:
            任务执行结果
        """
        # 更新任务状态为运行中
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].update_status(TaskStatus.RUNNING)

        try:
            # 执行任务
            result = func(*args, **_kwargs  # noqa: ARG001)

            # 更新任务状态为完成
            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].update_status(TaskStatus.COMPLETED)

            return result
        except Exception as e:
            # 更新任务状态为失败
            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].update_status(TaskStatus.FAILED)

            raise e

    def get_task(self, task_id: str) -> BackgroundTask :
        """获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            BackgroundTask对象，如果任务不存在则返回None
        """
        with self._lock:
            return self._tasks.get(task_id)

    def wait_get_task(
        self, task_id: str, timeout: Optional[float] = None
    ) -> BackgroundTask :
        """等待任务完成并返回结果

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            BackgroundTask对象，如果任务不存在则返回None

        Raises:
            TimeoutError: 如果任务超时
        """
        task = self.get_task(task_id)
        if task is None:
            return None

        try:
            task.future.result(timeout=timeout)
            return self.get_task(task_id)
        except TimeoutError:
            raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
        except Exception:
            # 任务执行出错，返回任务对象
            return self.get_task(task_id)

    def cancel(self, task_id: str) -> str:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            True如果任务被成功取消，False如果任务不存在或无法取消
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False

            # 尝试取消Future
            cancelled = task.future.cancel()

            if cancelled:
                task.update_status(TaskStatus.CANCELLED)

            return cancelled

    def get_all_tasks(self) -> list[BackgroundTask]:
        """获取所有任务

        Returns:
            所有任务列表
        """
        with self._lock:
            return list(self._tasks.values())

    def get_running_tasks(self) -> list[BackgroundTask]:
        """获取运行中的任务

        Returns:
            运行中的任务列表
        """
        with self._lock:
            return [task for task in self._tasks.values() if task.status == TaskStatus.RUNNING]

    def shutdown(self, wait: bool = True) -> str:
        """关闭管理器

        Args:
            wait: 是否等待所有任务完成
        """
        self._is_shutdown = True
        self._executor.shutdown(wait=wait)

    def __enter__(self):
        """支持上下文管理器协议"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器协议"""
        self.shutdown()
