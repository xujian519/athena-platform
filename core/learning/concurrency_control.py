#!/usr/bin/env python3
from __future__ import annotations
"""
学习引擎并发控制模块
Concurrency Control for Learning Engines

提供并发控制机制，防止资源竞争和过载：
1. 信号量控制：限制同时执行的学习任务数量
2. 速率限制：控制学习操作频率
3. 资源池管理：管理学习资源的使用

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyConfig:
    """并发控制配置"""

    max_concurrent_tasks: int = 10  # 最大并发任务数
    max_operations_per_second: int = 100  # 每秒最大操作数
    max_queue_size: int = 1000  # 最大队列大小
    task_timeout: float = 30.0  # 任务超时时间（秒）


class RateLimiter:
    """
    速率限制器

    使用令牌桶算法限制操作频率。
    """

    def __init__(self, max_rate: int, window: float = 1.0):
        """
        初始化速率限制器

        Args:
            max_rate: 最大速率（操作数/秒）
            window: 时间窗口（秒）
        """
        self.max_rate = max_rate
        self.window = window
        self.tokens: float = float(max_rate)  # 使用float以支持小数令牌
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """获取令牌"""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # 补充令牌
            self.tokens = min(
                self.max_rate, self.tokens + elapsed * self.max_rate / self.window
            )
            self.last_update = now

            # 检查是否有可用令牌
            if self.tokens >= 1:
                self.tokens -= 1
                return True

            return False

    async def wait_for_token(self) -> None:
        """等待获取令牌"""
        while not await self.acquire():
            # 计算等待时间
            wait_time = self.window / self.max_rate
            await asyncio.sleep(wait_time)


class AsyncSemaphore:
    """
    异步信号量包装器

    提供超时和统计功能的信号量。
    """

    def __init__(self, max_concurrent: int):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.current_count = 0
        self.total_acquired = 0
        self.total_released = 0
        self.total_timeouts = 0

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取信号量

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否获取成功
        """
        try:
            if timeout is None:
                await self._semaphore.acquire()
            else:
                await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout)

            self.current_count += 1
            self.total_acquired += 1
            return True

        except asyncio.TimeoutError:
            self.total_timeouts += 1
            logger.warning(f"信号量获取超时: {timeout}秒")
            return False

    def release(self) -> None:
        """释放信号量"""
        if self.current_count > 0:
            self.current_count -= 1
            self.total_released += 1
            self._semaphore.release()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "max_concurrent": self.max_concurrent,
            "current_count": self.current_count,
            "total_acquired": self.total_acquired,
            "total_released": self.total_released,
            "total_timeouts": self.total_timeouts,
            "utilization": self.current_count / self.max_concurrent
            if self.max_concurrent > 0
            else 0,
        }

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()


class ConcurrencyController:
    """
    并发控制器

    综合的并发控制解决方案，结合信号量、速率限制和任务队列。
    """

    def __init__(self, config: ConcurrencyConfig | None = None):
        self.config = config or ConcurrencyConfig()
        self.semaphore = AsyncSemaphore(self.config.max_concurrent_tasks)
        self.rate_limiter = RateLimiter(self.config.max_operations_per_second)
        self.task_queue: deque[asyncio.Task] = deque(maxlen=self.config.max_queue_size)
        self.active_tasks: set[asyncio.Task] = set()
        self.completed_tasks: int = 0
        self.failed_tasks: int = 0
        self.total_tasks: int = 0

    async def submit_task(
        self,
        coro: Callable[[], Any],
        priority: int = 0,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        提交任务到并发控制器

        Args:
            coro: 协程函数
            priority: 优先级（数值越大优先级越高）
            timeout: 任务超时时间

        Returns:
            任务结果

        Raises:
            asyncio.TimeoutError: 任务超时
            RuntimeError: 任务队列已满
        """
        # 检查队列大小
        if len(self.task_queue) >= self.config.max_queue_size:
            raise RuntimeError("任务队列已满")

        # 等待速率限制
        await self.rate_limiter.wait_for_token()

        # 等待信号量
        if not await self.semaphore.acquire(timeout=timeout):
            raise RuntimeError(f"无法获取信号量（超时: {timeout}秒）")

        task = None
        try:
            # 创建任务
            self.total_tasks += 1
            task = asyncio.create_task(coro())
            self.active_tasks.add(task)

            # 执行任务（带超时）
            if timeout is not None:
                result = await asyncio.wait_for(task, timeout=timeout)
            else:
                result = await task

            self.completed_tasks += 1
            return result

        except asyncio.TimeoutError:
            self.failed_tasks += 1
            logger.error(f"任务执行超时: {timeout}秒")
            raise

        except Exception as e:
            self.failed_tasks += 1
            logger.error(f"任务执行失败: {e}")
            raise

        finally:
            if task is not None:
                self.active_tasks.discard(task)
            self.semaphore.release()

    async def submit_batch(
        self, coros: list[Callable[[], Any]], timeout: Optional[float] = None
    ) -> list[Any]:
        """
        批量提交任务

        Args:
            coros: 协程函数列表
            timeout: 每个任务的超时时间

        Returns:
            结果列表
        """
        tasks = []
        for coro in coros:
            task = self.submit_task(coro, timeout=timeout)
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查异常
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量任务[{i}]失败: {result}")

        return results

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "config": {
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "max_operations_per_second": self.config.max_operations_per_second,
                "max_queue_size": self.config.max_queue_size,
                "task_timeout": self.config.task_timeout,
            },
            "semaphore": self.semaphore.get_stats(),
            "tasks": {
                "total": self.total_tasks,
                "active": len(self.active_tasks),
                "queued": len(self.task_queue),
                "completed": self.completed_tasks,
                "failed": self.failed_tasks,
                "success_rate": self.completed_tasks / max(self.total_tasks, 1),
            },
        }

    async def shutdown(self) -> None:
        """关闭并发控制器，等待所有活动任务完成"""
        logger.info("关闭并发控制器...")

        # 等待所有活动任务完成
        if self.active_tasks:
            logger.info(f"等待 {len(self.active_tasks)} 个活动任务完成...")
            await asyncio.gather(*self.active_tasks, return_exceptions=True)

        logger.info("并发控制器已关闭")


class LearningEngineConcurrencyMixin:
    """
    学习引擎并发控制混入类

    为学习引擎提供并发控制能力。
    """

    def __init__(self, *args, concurrency_config: ConcurrencyConfig | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.concurrency_config = concurrency_config or ConcurrencyConfig()
        self.concurrency_controller = ConcurrencyController(self.concurrency_config)

    async def process_experience_safe(
        self, experience_data: dict[str, Any], timeout: float = 30.0
    ) -> dict[str, Any]:
        """
        安全地处理学习经验（带并发控制）

        Args:
            experience_data: 经验数据
            timeout: 超时时间

        Returns:
            处理结果
        """
        async def _process():
            return await super().process_experience(experience_data)  # type: ignore

        result = await self.concurrency_controller.submit_task(
            _process, timeout=timeout
        )

        return result  # type: ignore[no-any-return]

    async def batch_process_experiences(
        self, experiences: list[dict[str, Any]], timeout: float = 30.0
    ) -> list[dict[str, Any]]:
        """
        批量处理学习经验（带并发控制）

        Args:
            experiences: 经验数据列表
            timeout: 每个任务的超时时间

        Returns:
            处理结果列表
        """
        async def _make_process_task(exp: dict[str, Any]):
            return await super().process_experience(exp)  # type: ignore

        # 创建协程工厂列表（使用闭包捕获exp值）
        # 定义一个工厂函数来创建闭包，确保每个exp被正确捕获
        def create_task_factory(e: dict[str, Any]) -> Callable[[], Any]:
            async def task_factory() -> Any:
                return await _make_process_task(e)
            return task_factory

        task_factories = [create_task_factory(exp) for exp in experiences]
        return await self.concurrency_controller.submit_batch(task_factories, timeout=timeout)

    def get_concurrency_stats(self) -> dict[str, Any]:
        """获取并发统计信息"""
        return self.concurrency_controller.get_statistics()

    async def shutdown_concurrency(self) -> None:
        """关闭并发控制器"""
        await self.concurrency_controller.shutdown()


# 全局单例
_global_concurrency_controller: ConcurrencyController | None = None


def get_global_concurrency_controller(
    config: ConcurrencyConfig | None = None,
) -> ConcurrencyController:
    """获取全局并发控制器"""
    global _global_concurrency_controller

    if _global_concurrency_controller is None:
        _global_concurrency_controller = ConcurrencyController(config)

    return _global_concurrency_controller


__all__ = [
    "ConcurrencyConfig",
    "RateLimiter",
    "AsyncSemaphore",
    "ConcurrencyController",
    "LearningEngineConcurrencyMixin",
    "get_global_concurrency_controller",
]
