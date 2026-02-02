#!/usr/bin/env python3
"""
并发控制机制
Concurrency Control Mechanisms

提供全面的并发控制能力,防止系统过载

作者: Athena AI Team
创建时间: 2026-01-11
版本: v1.0.0

特性:
- 信号量限流
- 任务队列管理
- 速率限制器
- 自适应节流
- 优先级调度
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar


logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class Priority(Enum):
    """任务优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ConcurrencyStats:
    """并发统计"""

    total_requests: int = 0
    concurrent_requests: int = 0
    peak_concurrent: int = 0
    rejected_requests: int = 0
    avg_wait_time_ms: float = 0.0
    total_wait_time_ms: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)


class ConcurrencyLimiter:
    """
    并发限制器

    使用信号量限制最大并发数

    使用示例:
        limiter = ConcurrencyLimiter(max_concurrent=100)

        async with limiter:
            # 最多100个并发执行
            await process_request()
    """

    def __init__(
        self,
        max_concurrent: int = 100,
        timeout: float | None = None,
        name: str = "ConcurrencyLimiter",
    ):
        """
        初始化并发限制器

        Args:
            max_concurrent: 最大并发数
            timeout: 获取许可的超时时间(秒)
            name: 限制器名称
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.name = name

        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = ConcurrencyStats()

        logger.info(f"✅ 并发限制器初始化: {name} (max={max_concurrent})")

    async def __aenter__(self):
        """进入上下文"""
        acquired = await self.acquire()
        if not acquired:
            raise RuntimeError(f"无法获取并发许可: {self.name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.release()

    async def acquire(self) -> bool:
        """获取并发许可"""
        start_time = time.time()

        try:
            if self.timeout:
                acquired = await asyncio.wait_for(self.semaphore.acquire(), timeout=self.timeout)
            else:
                acquired = await self.semaphore.acquire()

            if acquired:
                wait_time = (time.time() - start_time) * 1000
                self.stats.total_requests += 1
                self.stats.concurrent_requests += 1
                self.stats.peak_concurrent = max(
                    self.stats.peak_concurrent, self.stats.concurrent_requests
                )
                self.stats.total_wait_time_ms += wait_time
                self.stats.avg_wait_time_ms = (
                    self.stats.total_wait_time_ms / self.stats.total_requests
                )

                return True
            else:
                self.stats.rejected_requests += 1
                return False

        except asyncio.TimeoutError:
            self.stats.rejected_requests += 1
            logger.warning(f"获取并发许可超时: {self.name}")
            return False

    def release(self) -> Any:
        """释放并发许可"""
        self.semaphore.release()
        self.stats.concurrent_requests -= 1

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "current_concurrent": self.stats.concurrent_requests,
            "peak_concurrent": self.stats.peak_concurrent,
            "total_requests": self.stats.total_requests,
            "rejected_requests": self.stats.rejected_requests,
            "rejection_rate": (
                f"{self.stats.rejected_requests / max(self.stats.total_requests, 1):.2%}"
            ),
            "avg_wait_time_ms": round(self.stats.avg_wait_time_ms, 2),
            "utilization": (f"{self.stats.concurrent_requests / self.max_concurrent:.2%}"),
        }


class AsyncTaskQueue:
    """
    异步任务队列

    管理待处理的任务队列,控制并发执行

    使用示例:
        queue = AsyncTaskQueue(max_workers=50)

        # 添加任务
        result = await queue.submit(process_task, arg1, arg2)

        # 批量添加
        results = await queue.submit_batch([
            (process_task, arg1, arg2),
            (process_task, arg3, arg4),
        ])
    """

    def __init__(
        self, max_workers: int = 50, max_queue_size: int = 1000, name: str = "AsyncTaskQueue"
    ):
        """
        初始化任务队列

        Args:
            max_workers: 最大工作线程数
            max_queue_size: 队列最大长度
            name: 队列名称
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.name = name

        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.workers: list[asyncio.Task] = []
        self.running = False

        # 统计信息
        self.stats = {
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "rejected": 0,
        }

        logger.info(f"✅ 任务队列初始化: {name} (workers={max_workers})")

    async def start(self):
        """启动任务队列"""
        if self.running:
            logger.warning("任务队列已在运行")
            return

        self.running = True

        # 启动工作线程
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        logger.info(f"🚀 任务队列已启动: {self.name} ({self.max_workers} workers)")

    async def stop(self):
        """停止任务队列"""
        self.running = False

        # 取消所有工作线程
        for worker in self.workers:
            worker.cancel()

        # 等待所有工作线程结束
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

        logger.info(f"⏹️ 任务队列已停止: {self.name}")

    async def submit(self, func: Callable, *args, priority: int = 2, **kwargs) -> Any:
        """
        提交单个任务

        Args:
            func: 要执行的函数
            *args: 函数参数
            priority: 优先级
            **kwargs: 函数关键字参数

        Returns:
            任务执行结果
        """
        if not self.running:
            raise RuntimeError(f"任务队列未启动: {self.name}")

        # 创建任务
        task_item = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "priority": priority,
            "future": asyncio.Future(),
            "created_at": time.time(),
        }

        # 提交到队列
        try:
            self.queue.put_nowait(task_item)
            self.stats["submitted"] += 1
        except asyncio.QueueFull:
            self.stats["rejected"] += 1
            logger.error(f"任务队列已满: {self.name}")
            raise

        # 等待结果
        return await task_item["future"]

    async def submit_batch(self, tasks: list[tuple]) -> list[Any]:
        """
        批量提交任务

        Args:
            tasks: 任务列表,每个元素是 (func, *args, **kwargs)

        Returns:
            结果列表
        """
        if not self.running:
            raise RuntimeError(f"任务队列未启动: {self.name}")

        # 创建所有任务
        futures = []
        for task_tuple in tasks:
            if len(task_tuple) == 0:
                continue

            func = task_tuple[0]
            args = task_tuple[1] if len(task_tuple) > 1 else ()
            kwargs = task_tuple[2] if len(task_tuple) > 2 else {}

            future = asyncio.create_task(self.submit(func, *args, **kwargs))
            futures.append(future)

        # 等待所有任务完成
        results = await asyncio.gather(*futures, return_exceptions=True)

        return results

    async def _worker(self, worker_id: int):
        """工作线程"""
        logger.debug(f"工作线程启动: {self.name}-worker-{worker_id}")

        while self.running:
            try:
                # 获取任务
                task_item = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                # 执行任务
                try:
                    func = task_item["func"]
                    args = task_item["args"]
                    kwargs = task_item["kwargs"]

                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    task_item["future"].set_result(result)
                    self.stats["completed"] += 1

                except Exception as e:
                    task_item["future"].set_exception(e)
                    self.stats["failed"] += 1
                    logger.error(f"任务执行失败: {e}")

                finally:
                    self.queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程错误: {e}")
                await asyncio.sleep(0.1)

        logger.debug(f"工作线程停止: {self.name}-worker-{worker_id}")

    async def wait_for_completion(self):
        """等待所有任务完成"""
        await self.queue.join()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        queue_size = self.queue.qsize()

        return {
            "name": self.name,
            "max_workers": self.max_workers,
            "active_workers": len(self.workers),
            "queue_size": queue_size,
            "max_queue_size": self.max_queue_size,
            "queue_utilization": f"{queue_size / self.max_queue_size:.2%}",
            "submitted": self.stats["submitted"],
            "completed": self.stats["completed"],
            "failed": self.stats["failed"],
            "rejected": self.stats["rejected"],
            "success_rate": (
                f"{self.stats['completed'] / max(self.stats['submitted'] - self.stats['rejected'], 1):.2%}"
            ),
            "running": self.running,
        }


class RateLimiter:
    """
    速率限制器

    限制单位时间内的请求速率

    使用示例:
        limiter = RateLimiter(rate=100, per=60)  # 每分钟100次

        async with limiter:
            # 执行请求
            await api_call()
    """

    def __init__(
        self, rate: int, per: float = 1.0, burst: int | None = None, name: str = "RateLimiter"
    ):
        """
        初始化速率限制器

        Args:
            rate: 速率限制(次数)
            per: 时间窗口(秒)
            burst: 突发容量
            name: 限制器名称
        """
        self.rate = rate
        self.per = per
        self.burst = burst or rate
        self.name = name

        self.tokens = self.burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()

        logger.info(f"✅ 速率限制器初始化: {name} ({rate}/{per}s)")

    async def __aenter__(self):
        """进入上下文"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        pass

    async def acquire(self):
        """获取许可(等待速率限制)"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # 补充令牌
            tokens_to_add = elapsed * (self.rate / self.per)
            self.tokens = min(self.burst, self.tokens + tokens_to_add)
            self.last_update = now

            # 消耗令牌
            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                # 等待令牌补充
                wait_time = (1 - self.tokens) * (self.per / self.rate)
                await asyncio.sleep(wait_time)
                self.tokens = 0
                return

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "rate": f"{self.rate}/{self.per}s",
            "burst": self.burst,
            "available_tokens": round(self.tokens, 2),
            "utilization": f"{(self.burst - self.tokens) / self.burst:.2%}",
        }


class AdaptiveConcurrencyController:
    """
    自适应并发控制器

    根据系统性能动态调整并发数

    使用示例:
        controller = AdaptiveConcurrencyController(
            min_concurrent=10,
            max_concurrent=200,
            target_latency_ms=100
        )

        async with controller:
            result = await process_request()
    """

    def __init__(
        self,
        min_concurrent: int = 10,
        max_concurrent: int = 200,
        target_latency_ms: float = 100,
        adjustment_rate: float = 0.1,
        name: str = "AdaptiveController",
    ):
        """
        初始化自适应控制器

        Args:
            min_concurrent: 最小并发数
            max_concurrent: 最大并发数
            target_latency_ms: 目标延迟(毫秒)
            adjustment_rate: 调整速率
            name: 控制器名称
        """
        self.min_concurrent = min_concurrent
        self.max_concurrent = max_concurrent
        self.target_latency_ms = target_latency_ms
        self.adjustment_rate = adjustment_rate
        self.name = name

        self.current_concurrent = min_concurrent
        self.semaphore = asyncio.Semaphore(min_concurrent)

        # 性能历史
        self.latency_history = deque(maxlen=100)
        self.concurrency_history = deque(maxlen=100)

        logger.info(
            f"✅ 自适应控制器初始化: {name} "
            f"(min={min_concurrent}, max={max_concurrent}, target={target_latency_ms}ms)"
        )

    async def __aenter__(self):
        """进入上下文"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.release()

    async def acquire(self):
        """获取许可"""
        await self.semaphore.acquire()

    def release(self, latency_ms: float | None = None) -> Any:
        """释放许可并记录性能"""
        self.semaphore.release()

        if latency_ms is not None:
            self._record_latency(latency_ms)
            self._adjust_concurrency()

    def _record_latency(self, latency_ms: float) -> Any:
        """记录延迟"""
        self.latency_history.append(latency_ms)
        self.concurrency_history.append(self.current_concurrent)

    def _adjust_concurrency(self) -> Any:
        """调整并发数"""
        if len(self.latency_history) < 10:
            return

        # 计算平均延迟
        avg_latency = sum(self.latency_history) / len(self.latency_history)

        # 延迟过高,减少并发
        if avg_latency > self.target_latency_ms * 1.2:
            old_concurrent = self.current_concurrent
            self.current_concurrent = max(
                self.min_concurrent, int(self.current_concurrent * (1 - self.adjustment_rate))
            )
            if self.current_concurrent != old_concurrent:
                # 更新信号量
                self._update_semaphore()
                logger.debug(
                    f"延迟过高({avg_latency:.1f}ms), "
                    f"减少并发: {old_concurrent} → {self.current_concurrent}"
                )

        # 延迟较低,增加并发
        elif avg_latency < self.target_latency_ms * 0.8:
            old_concurrent = self.current_concurrent
            self.current_concurrent = min(
                self.max_concurrent, int(self.current_concurrent * (1 + self.adjustment_rate))
            )
            if self.current_concurrent != old_concurrent:
                # 更新信号量
                self._update_semaphore()
                logger.debug(
                    f"延迟较低({avg_latency:.1f}ms), "
                    f"增加并发: {old_concurrent} → {self.current_concurrent}"
                )

    def _update_semaphore(self) -> Any:
        """更新信号量容量"""
        # 创建新信号量
        new_semaphore = asyncio.Semaphore(self.current_concurrent)
        # 替换旧信号量(在下一次acquire时生效)
        self.semaphore = new_semaphore

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        avg_latency = (
            sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0
        )

        return {
            "name": self.name,
            "current_concurrent": self.current_concurrent,
            "min_concurrent": self.min_concurrent,
            "max_concurrent": self.max_concurrent,
            "target_latency_ms": self.target_latency_ms,
            "avg_latency_ms": round(avg_latency, 2),
            "latency_ratio": f"{avg_latency / self.target_latency_ms:.2%}",
            "samples": len(self.latency_history),
        }


# =============================================================================
# 全局实例和便捷函数
# =============================================================================

_limiters: dict[str, ConcurrencyLimiter] = {}
_queues: dict[str, AsyncTaskQueue] = {}
_rate_limiters: dict[str, RateLimiter] = {}


def get_limiter(name: str, max_concurrent: int = 100, **kwargs) -> ConcurrencyLimiter:
    """获取或创建并发限制器"""
    if name not in _limiters:
        _limiters[name] = ConcurrencyLimiter(max_concurrent, name=name, **kwargs)
    return _limiters[name]


def get_task_queue(name: str, max_workers: int = 50, **kwargs) -> AsyncTaskQueue:
    """获取或创建任务队列"""
    if name not in _queues:
        _queues[name] = AsyncTaskQueue(max_workers, name=name, **kwargs)
    return _queues[name]


def get_rate_limiter(name: str, rate: int, per: float = 1.0, **kwargs) -> RateLimiter:
    """获取或创建速率限制器"""
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter(rate, per, name=name, **kwargs)
    return _rate_limiters[name]


# =============================================================================
# 使用示例
# =============================================================================


async def example_usage():
    """并发控制使用示例"""

    # 1. 并发限制器
    print("=== 并发限制器示例 ===")
    limiter = ConcurrencyLimiter(max_concurrent=5)

    async def task_with_limit(n):
        async with limiter:
            print(f"任务 {n} 开始执行")
            await asyncio.sleep(1)
            print(f"任务 {n} 完成")
            return n

    # 并发执行10个任务,但最多5个并发
    results = await asyncio.gather(*[task_with_limit(i) for i in range(10)])
    print(f"结果: {results}")
    print(f"统计: {limiter.get_stats()}")

    # 2. 任务队列
    print("\n=== 任务队列示例 ===")
    queue = AsyncTaskQueue(max_workers=3)
    await queue.start()

    async def task_func(n):
        await asyncio.sleep(0.5)
        return n * 2

    # 提交任务
    results = await queue.submit_batch([(task_func, i) for i in range(10)])
    print(f"结果: {results}")
    print(f"统计: {queue.get_stats()}")

    await queue.stop()

    # 3. 速率限制器
    print("\n=== 速率限制器示例 ===")
    rate_limiter = RateLimiter(rate=5, per=1)  # 每秒5次

    start_time = time.time()
    for i in range(10):
        async with rate_limiter:
            print(f"请求 {i+1} 在 {time.time() - start_time:.2f}s")

    print(f"统计: {rate_limiter.get_stats()}")


if __name__ == "__main__":
    asyncio.run(example_usage())


# 全局辅助函数
def get_limiters_status() -> dict[str, Any]:
    """获取所有限制器的状态"""
    status = {}

    for name, limiter in _limiters.items():
        if isinstance(limiter, ConcurrencyLimiter):
            status[name] = {"type": "concurrency_limiter", "stats": limiter.get_stats()}
        elif isinstance(limiter, RateLimiter):
            status[name] = {"type": "rate_limiter", "stats": limiter.get_stats()}
        elif isinstance(limiter, AsyncTaskQueue):
            status[name] = {"type": "task_queue", "stats": limiter.get_stats()}

    return status
