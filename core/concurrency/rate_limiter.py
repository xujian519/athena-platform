#!/usr/bin/env python3
"""
并发控制和资源管理模块
Concurrency Control and Resource Management Module

提供并发限制、资源池管理、请求节流等功能

作者: Athena AI系统
创建时间: 2025-12-19
版本: 1.0.0
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ConcurrencyStats:
    """并发统计信息"""

    active_requests: int = 0
    total_requests: int = 0
    rejected_requests: int = 0
    peak_concurrency: int = 0
    average_wait_time: float = 0.0
    total_wait_time: float = 0.0
    completed_requests: int = 0


class AsyncConcurrencyLimiter:
    """异步并发限制器"""

    def __init__(
        self,
        max_concurrent: int = 10,
        queue_size: int = 100,
        timeout: float = 30.0,
    ):
        """
        初始化并发限制器

        Args:
            max_concurrent: 最大并发数
            queue_size: 队列大小
            timeout: 请求超时时间(秒)
        """
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        self.timeout = timeout

        # 信号量用于控制并发
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # 队列用于跟踪等待的请求
        self._queue: deque = deque()

        # 统计信息
        self._stats = ConcurrencyStats()
        self._lock = asyncio.Lock()

        logger.info(
            f"✅ 并发限制器初始化完成 "
            f"(最大并发: {max_concurrent}, 队列大小: {queue_size}, 超时: {timeout}s)"
        )

    @asynccontextmanager
    async def acquire(self):
        """
        获取并发许可(上下文管理器)

        Yields:
            None

        Raises:
            asyncio.TimeoutError: 获取许可超时
        """
        start_time = time.time()
        acquired = False

        try:
            # 尝试获取许可
            acquired = await asyncio.wait_for(self._semaphore.acquire(), timeout=self.timeout)

            # 更新统计信息
            async with self._lock:
                self._stats.active_requests += 1
                self._stats.total_requests += 1
                wait_time = time.time() - start_time
                self._stats.total_wait_time += wait_time
                self._stats.peak_concurrency = max(
                    self._stats.peak_concurrency, self._stats.active_requests
                )

            logger.debug(
                f"🔓 获取并发许可 (活跃请求: {self._stats.active_requests}/{self.max_concurrent})"
            )

            yield

        except asyncio.TimeoutError:
            async with self._lock:
                self._stats.rejected_requests += 1
            logger.warning(f"⚠️ 获取并发许可超时 ({self.timeout}s)")
            raise

        finally:
            if acquired:
                # 释放许可
                self._semaphore.release()

                async with self._lock:
                    self._stats.active_requests -= 1
                    self._stats.completed_requests += 1
                    self._stats.average_wait_time = (
                        self._stats.total_wait_time / self._stats.completed_requests
                        if self._stats.completed_requests > 0
                        else 0.0
                    )

                logger.debug(
                    f"🔒 释放并发许可 (活跃请求: {self._stats.active_requests}/{self.max_concurrent})"
                )

    async def run(self, coro: Awaitable[T]) -> T:
        """
        在并发限制下运行协程

        Args:
            coro: 要运行的协程

        Returns:
            协程的结果

        Raises:
            asyncio.TimeoutError: 获取许可超时
            Exception: 协程抛出的异常
        """
        async with self.acquire():
            return await coro

    def get_stats(self) -> dict[str, Any]:
        """
        获取并发统计信息

        Returns:
            统计信息字典
        """
        return {
            "active_requests": self._stats.active_requests,
            "total_requests": self._stats.total_requests,
            "rejected_requests": self._stats.rejected_requests,
            "peak_concurrency": self._stats.peak_concurrency,
            "average_wait_time": self._stats.average_wait_time,
            "max_concurrent": self.max_concurrent,
            "queue_size": self.queue_size,
            "utilization": (
                self._stats.active_requests / self.max_concurrent if self.max_concurrent > 0 else 0
            ),
        }

    def reset_stats(self) -> Any:
        """重置统计信息"""
        self._stats = ConcurrencyStats()
        logger.info("📊 并发统计信息已重置")


class ResourcePool:
    """资源池管理器"""

    def __init__(
        self,
        resource_factory: Callable[[], Awaitable[Any]],
        max_size: int = 10,
        idle_timeout: float = 300.0,
    ):
        """
        初始化资源池

        Args:
            resource_factory: 资源工厂函数(异步)
            max_size: 最大资源数量
            idle_timeout: 空闲资源超时时间(秒)
        """
        self.resource_factory = resource_factory
        self.max_size = max_size
        self.idle_timeout = idle_timeout

        # 资源池
        self._pool: list[Any] = []

        # 资源状态
        self._in_use: set[int] = set()
        self._created_count = 0
        self._lock = asyncio.Lock()

        logger.info(f"✅ 资源池初始化完成 (最大容量: {max_size}, 空闲超时: {idle_timeout}s)")

    @asynccontextmanager
    async def acquire(self):
        """
        从资源池获取资源(上下文管理器)

        Yields:
            资源对象
        """
        resource = None
        resource_id = None

        try:
            # 尝试从池中获取资源
            async with self._lock:
                if self._pool:
                    resource = self._pool.pop()
                    # 生成简单的资源ID
                    resource_id = id(resource)
                    self._in_use.add(resource_id)
                else:
                    # 创建新资源
                    if self._created_count < self.max_size:
                        resource = await self.resource_factory()
                        resource_id = id(resource)
                        self._in_use.add(resource_id)
                        self._created_count += 1
                        logger.debug(
                            f"🔨 创建新资源 (ID: {resource_id}, 总计: {self._created_count})"
                        )
                    else:
                        # 资源池已满,等待
                        pass

            if resource is None:
                # 等待其他请求释放资源
                logger.warning("⏳ 资源池已满,等待资源释放...")
                await asyncio.sleep(0.1)
                # 递归重试(简化实现,生产环境应使用条件变量)
                async with self.acquire() as res:
                    yield res
                    return

            logger.debug(f"✅ 获取资源 (ID: {resource_id})")
            yield resource

        finally:
            if resource is not None and resource_id is not None:
                # 将资源返回池中
                async with self._lock:
                    self._in_use.discard(resource_id)
                    self._pool.append(resource)
                logger.debug(f"↩️ 返回资源 (ID: {resource_id})")

    def get_stats(self) -> dict[str, Any]:
        """
        获取资源池统计信息

        Returns:
            统计信息字典
        """
        return {
            "pool_size": len(self._pool),
            "in_use": len(self._in_use),
            "created_total": self._created_count,
            "max_size": self.max_size,
            "utilization": (len(self._in_use) / self.max_size if self.max_size > 0 else 0),
        }

    async def cleanup_idle(self):
        """清理空闲资源"""
        async with self._lock:
            # 简化实现:移除所有空闲资源
            # 生产环境应跟踪每个资源的最后使用时间
            removed_count = len(self._pool)
            self._pool.clear()

            if removed_count > 0:
                logger.info(f"🧹 清理了 {removed_count} 个空闲资源")


class RequestThrottler:
    """请求节流器(控制请求速率)"""

    def __init__(self, rate: float = 10.0, burst: int = 5):
        """
        初始化请求节流器

        Args:
            rate: 请求速率(请求/秒)
            burst: 突发容量
        """
        self.rate = rate
        self.burst = burst

        # 令牌桶
        self._tokens = float(burst)
        self._last_update = time.time()

        self._lock = asyncio.Lock()

        logger.info(f"✅ 请求节流器初始化完成 (速率: {rate}/s, 突发: {burst})")

    async def acquire(self) -> bool:
        """
        获取许可(节流)

        Returns:
            是否成功获取许可
        """
        async with self._lock:
            current_time = time.time()

            # 计算需要添加的令牌数
            elapsed = current_time - self._last_update
            tokens_to_add = elapsed * self.rate

            # 更新令牌桶
            self._tokens = min(self._tokens + tokens_to_add, self.burst)
            self._last_update = current_time

            # 检查是否有足够的令牌
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            else:
                return False

    async def wait_for_token(self, timeout: float = 10.0) -> bool:
        """
        等待直到有可用令牌

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否成功获取令牌
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)

        return False

    def get_stats(self) -> dict[str, Any]:
        """
        获取节流器统计信息

        Returns:
            统计信息字典
        """
        return {
            "rate": self.rate,
            "burst": self.burst,
            "available_tokens": self._tokens,
        }


# 全局实例
_concurrency_limiter: AsyncConcurrencyLimiter | None = None


def get_concurrency_limiter(
    max_concurrent: int = 10, queue_size: int = 100, timeout: float = 30.0
) -> AsyncConcurrencyLimiter:
    """
    获取全局并发限制器实例

    Args:
        max_concurrent: 最大并发数
        queue_size: 队列大小
        timeout: 请求超时时间(秒)

    Returns:
        并发限制器实例
    """
    global _concurrency_limiter

    if _concurrency_limiter is None:
        _concurrency_limiter = AsyncConcurrencyLimiter(
            max_concurrent=max_concurrent,
            queue_size=queue_size,
            timeout=timeout,
        )

    return _concurrency_limiter


# 导出
__all__ = [
    "AsyncConcurrencyLimiter",
    "ConcurrencyStats",
    "RequestThrottler",
    "ResourcePool",
    "get_concurrency_limiter",
]
