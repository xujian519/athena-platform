from __future__ import annotations
"""
异步处理引擎 - Async Processing Engine

实现系统异步化处理功能:
1. BERT推理异步化
2. 数据库操作异步化
3. 外部API调用异步化
4. 任务队列管理
5. 并发控制和限流
"""

import asyncio
import functools
import logging
import queue
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AsyncTask:
    """异步任务"""

    task_id: str  # 任务ID
    name: str  # 任务名称
    func: Callable  # 执行函数
    args: tuple = field(default_factory=tuple)  # 位置参数
    kwargs: dict = field(default_factory=dict)  # 关键字参数
    priority: TaskPriority = TaskPriority.NORMAL  # 优先级
    status: TaskStatus = TaskStatus.PENDING  # 状态
    created_at: float = field(default_factory=time.time)  # 创建时间
    started_at: Optional[float] = None  # 开始时间
    completed_at: Optional[float] = None  # 完成时间
    result: Any = None  # 结果
    error: Optional[str] = None  # 错误
    retries: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数
    timeout: Optional[float] = None  # 超时时间(秒)
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    @property
    def duration(self) -> Optional[float]:
        """执行时长"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "result": str(self.result)[:100] if self.result else None,
            "error": self.error,
            "retries": self.retries,
            "metadata": self.metadata,
        }


class AsyncTaskQueue:
    """
    异步任务队列

    基于优先级的任务队列
    """

    def __init__(self, max_size: int = 10000):
        """
        初始化任务队列

        Args:
            max_size: 队列最大大小
        """
        self.max_size = max_size
        self._queue: list[AsyncTask] = []
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)

    def put(self, task: AsyncTask, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        添加任务到队列

        Args:
            task: 任务
            block: 是否阻塞
            timeout: 超时时间

        Returns:
            是否成功
        """
        with self._not_empty:
            # 检查队列是否已满
            if len(self._queue) >= self.max_size:
                if not block:
                    return False
                # 等待队列有空间
                self._not_empty.wait_for(lambda: len(self._queue) < self.max_size, timeout)

            # 按优先级插入(插入排序)
            inserted = False
            for i, existing_task in enumerate(self._queue):
                if task.priority.value > existing_task.priority.value:
                    self._queue.insert(i, task)
                    inserted = True
                    break

            if not inserted:
                self._queue.append(task)

            self._not_empty.notify()
            logger.debug(f"任务加入队列: {task.name} (优先级: {task.priority.name})")
            return True

    def get(self, block: bool = True, timeout: Optional[float] = None) -> AsyncTask | None:
        """
        从队列获取任务

        Args:
            block: 是否阻塞
            timeout: 超时时间

        Returns:
            任务或None
        """
        with self._not_empty:
            if not self._queue:
                if not block:
                    return None
                self._not_empty.wait_for(lambda: len(self._queue) > 0, timeout)

            if self._queue:
                task = self._queue.pop(0)
                return task

        return None

    def peek(self) -> AsyncTask | None:
        """查看队列头部的任务(不移除)"""
        with self._lock:
            return self._queue[0] if self._queue else None

    def qsize(self) -> int:
        """队列大小"""
        with self._lock:
            return len(self._queue)

    def empty(self) -> bool:
        """队列是否为空"""
        with self._lock:
            return len(self._queue) == 0

    def clear(self) -> None:
        """清空队列"""
        with self._lock:
            self._queue.clear()


class AsyncProcessor:
    """
    异步处理器

    执行异步任务的工作线程池
    """

    def __init__(self, max_workers: int = 10, task_queue: AsyncTaskQueue | None = None):
        """
        初始化异步处理器

        Args:
            max_workers: 最大工作线程数
            task_queue: 任务队列
        """
        self.max_workers = max_workers
        self.task_queue = task_queue or AsyncTaskQueue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
        self._worker_thread: threading.Thread | None = None

        # 任务追踪
        self._active_tasks: dict[str, AsyncTask] = {}
        self._completed_tasks: list[AsyncTask] = []
        self._max_completed_history = 1000

        # 统计信息
        self._stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
        }

        self._lock = threading.RLock()

        logger.info(f"✅ 异步处理器初始化完成: {max_workers} 工作线程")

    def start(self) -> None:
        """启动异步处理器"""
        if self._running:
            logger.warning("异步处理器已经在运行")
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("🚀 异步处理器已启动")

    def stop(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """
        停止异步处理器

        Args:
            wait: 是否等待任务完成
            timeout: 超时时间
        """
        self._running = False

        if wait:
            start_time = time.time()
            while self._active_tasks and (timeout is None or time.time() - start_time < timeout):
                time.sleep(0.1)

        self.executor.shutdown(wait=wait)
        logger.info("🛑 异步处理器已停止")

    def submit(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        name: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        提交任务

        Args:
            func: 执行函数
            args: 位置参数
            kwargs: 关键字参数
            name: 任务名称
            priority: 优先级
            timeout: 超时时间
            max_retries: 最大重试次数
            metadata: 元数据

        Returns:
            任务ID
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        task = AsyncTask(
            task_id=task_id,
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            metadata=metadata or {},
        )

        # 加入队列
        if self.task_queue.put(task):
            with self._lock:
                self._stats["total_submitted"] += 1

            logger.info(f"提交任务: {task.name} ({task_id})")
            return task_id
        else:
            logger.error(f"任务队列已满,无法提交任务: {task.name}")
            raise queue.Full("任务队列已满")

    def get_task_status(self, task_id: str) -> Optional[dict[str, Any]]:
        """获取任务状态"""
        with self._lock:
            # 检查活动任务
            if task_id in self._active_tasks:
                return self._active_tasks[task_id].to_dict()

            # 检查已完成任务
            for task in self._completed_tasks:
                if task.task_id == task_id:
                    return task.to_dict()

        return None

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        with self._lock:
            # 尝试从队列中移除
            # 注意:这里简化实现,实际应该从队列中精确查找并移除
            for task in list(self.task_queue._queue):
                if task.task_id == task_id and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    self._stats["total_cancelled"] += 1
                    logger.info(f"任务已取消: {task_id}")
                    return True

            # 尝试取消活动任务(这通常很困难,因为可能已经在执行)
            if task_id in self._active_tasks:
                logger.warning(f"任务正在执行,无法取消: {task_id}")
                return False

        return False

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                **self._stats,
                "active_tasks": len(self._active_tasks),
                "queued_tasks": self.task_queue.qsize(),
                "completed_tasks": len(self._completed_tasks),
                "success_rate": (
                    self._stats["total_completed"] / self._stats["total_submitted"]
                    if self._stats["total_submitted"] > 0
                    else 0
                ),
            }

    def _worker_loop(self) -> None:
        """工作线程循环"""
        logger.info("工作线程循环已启动")

        while self._running:
            try:
                # 从队列获取任务
                task = self.task_queue.get(block=True, timeout=0.5)
                if task is None:
                    continue

                # 提交到线程池执行
                self.executor.submit(self._execute_task, task)

                # 存储活动任务
                with self._lock:
                    self._active_tasks[task.task_id] = task

            except Exception as e:
                logger.error(f"工作线程异常: {e}")

        logger.info("工作线程循环已退出")

    def _execute_task(self, task: AsyncTask) -> None:
        """
        执行任务

        Args:
            task: 任务
        """
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()

        logger.info(f"开始执行任务: {task.name} ({task.task_id})")

        try:
            # 执行任务
            if task.timeout:
                # 带超时执行(需要asyncio支持,这里简化处理)
                result = task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()

            with self._lock:
                self._stats["total_completed"] += 1

            logger.info(f"任务完成: {task.name} " f"耗时: {task.duration:.2f}s")

        except Exception as e:
            task.error = str(e)
            task.retries += 1

            # 检查是否需要重试
            if task.retries < task.max_retries:
                logger.warning(
                    f"任务失败,准备重试 ({task.retries}/{task.max_retries}): {task.name}, 错误: {e}"
                )
                task.status = TaskStatus.PENDING
                task.started_at = None
                # 重新加入队列
                self.task_queue.put(task)
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = time.time()

                with self._lock:
                    self._stats["total_failed"] += 1

                logger.error(f"任务失败(已达最大重试次数): {task.name}, 错误: {e}")

        finally:
            # 从活动任务移除
            with self._lock:
                if task.task_id in self._active_tasks:
                    del self._active_tasks[task.task_id]

                # 加入已完成任务
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    self._completed_tasks.append(task)
                    # 清理旧记录
                    while len(self._completed_tasks) > self._max_completed_history:
                        self._completed_tasks.pop(0)


class AsyncDatabase:
    """
    异步数据库包装器

    为数据库操作提供异步接口
    """

    def __init__(self, db_path: str):
        """
        初始化异步数据库

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.processor = AsyncProcessor(max_workers=5)
        self.processor.start()

        logger.info(f"✅ 异步数据库初始化完成: {db_path}")

    async def execute(self, query: str, params: tuple = (), fetch: bool = False) -> Any:
        """
        异步执行SQL查询

        Args:
            query: SQL查询
            params: 参数
            fetch: 是否获取结果

        Returns:
            查询结果
        """
        import sqlite3

        def _execute() -> Any:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)

            if fetch:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount

            conn.close()
            return result

        # 在线程池中执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute)

    async def execute_many(self, query: str, params_list: list[tuple]) -> int:
        """
        批量执行SQL

        Args:
            query: SQL查询
            params_list: 参数列表

        Returns:
            影响的行数
        """
        import sqlite3

        def _execute_many() -> Any:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            rowcount = cursor.rowcount
            conn.close()
            return rowcount

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute_many)

    def close(self) -> None:
        """关闭数据库连接"""
        self.processor.stop()


class AsyncBERTClassifier:
    """
    异步BERT分类器

    为BERT推理提供异步接口
    """

    def __init__(self, model_path: str):
        """
        初始化异步BERT分类器

        Args:
            model_path: 模型路径
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.processor = AsyncProcessor(max_workers=2)  # BERT推理比较重,减少并发
        self._load_model()

        logger.info(f"✅ 异步BERT分类器初始化完成: {model_path}")

    def _load_model(self) -> None:
        """加载模型(延迟加载)"""
        # 实际实现中,这里应该加载BERT模型和tokenizer
        # 这里只是占位符
        logger.info("BERT模型加载完成(占位符)")

    async def predict(self, text: str, top_k: int = 1) -> list[dict[str, Any]]:
        """
        异步预测

        Args:
            text: 输入文本
            top_k: 返回top-k结果

        Returns:
            预测结果列表
        """

        def _predict() -> Any:
            # 这里应该是实际的BERT推理
            # 占位符实现
            return [
                {"label": "patent_search", "confidence": 0.95},
                {"label": "patent_analysis", "confidence": 0.05},
            ][:top_k]

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _predict)

    async def predict_batch(self, texts: list[str], top_k: int = 1) -> list[list[dict[str, Any]]]:
        """
        批量异步预测

        Args:
            texts: 输入文本列表
            top_k: 返回top-k结果

        Returns:
            预测结果列表
        """
        tasks = [self.predict(text, top_k) for text in texts]
        return await asyncio.gather(*tasks)

    def close(self) -> None:
        """关闭分类器"""
        self.processor.stop()


class AsyncAPIClient:
    """
    异步API客户端

    为外部API调用提供异步接口
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        初始化异步API客户端

        Args:
            base_url: 基础URL
            timeout: 超时时间
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = None

        logger.info(f"✅ 异步API客户端初始化完成: {base_url}")

    async def _get_session(self):
        """获取或创建aiohttp会话"""
        if self.session is None:
            import aiohttp

            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self.session

    async def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        异步GET请求

        Args:
            endpoint: 端点
            params: 查询参数
            headers: 请求头

        Returns:
            响应数据
        """
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        异步POST请求

        Args:
            endpoint: 端点
            data: 表单数据
            json: JSON数据
            headers: 请求头

        Returns:
            响应数据
        """
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with session.post(url, data=data, json=json, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def close(self) -> None:
        """关闭客户端"""
        if self.session:
            await self.session.close()


# 便捷装饰器
def async_task(
    name: str = "",
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: Optional[float] = None,
    max_retries: int = 3,
):
    """
    异步任务装饰器

    Usage:
        @async_task(name="数据处理", priority=TaskPriority.HIGH)
        def process_data(data):
            # 处理数据
            return result
    """

    def decorator(func) -> None:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            processor = get_async_processor()
            task_id = processor.submit(
                func=func,
                args=args,
                kwargs=kwargs,
                name=name or func.__name__,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
            )
            return task_id

        return wrapper

    return decorator


# 全局单例
_async_processor: AsyncProcessor | None = None


def get_async_processor() -> AsyncProcessor:
    """获取全局异步处理器"""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncProcessor()
        _async_processor.start()
    return _async_processor


# 便捷函数
async def run_in_executor(func: Callable, *args, **kwargs) -> Any:
    """
    在线程池中运行函数

    Args:
        func: 函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数结果
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


async def gather_with_concurrency(*coroutines_or_tasks, concurrency: int = 10) -> list[Any]:
    """
    并发执行协程(限制并发数)

    Args:
        *coroutines_or_tasks: 协程或任务列表
        concurrency: 最大并发数

    Returns:
        结果列表
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def run_with_limit(coro):
        async with semaphore:
            return await coro

    tasks = [run_with_limit(coro) for coro in coroutines_or_tasks]
    return await asyncio.gather(*tasks)
