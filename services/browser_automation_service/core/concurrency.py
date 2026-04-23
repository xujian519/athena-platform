#!/usr/bin/env python3
"""
并发控制模块
Concurrency Control Module for Browser Automation Service

提供并发限制、速率限制和资源管理功能

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import asyncio
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

from config.settings import logger, settings

from core.exceptions import ConcurrentLimitExceededError


class RateLimiter:
    """
    速率限制器

    使用滑动窗口算法实现速率限制
    """

    def __init__(self, rate: int, per: int = 60):
        """
        初始化速率限制器

        Args:
            rate: 限制数量
            per: 时间窗口（秒）
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """
        获取一个许可

        Returns:
            bool: 是否获取成功
        """
        async with self._lock:
            current = time.monotonic()
            time_passed = current - self.last_check
            self.last_check = current

            # 恢复许可
            self.allowance += time_passed * (self.rate / self.per)

            if self.allowance > self.rate:
                self.allowance = self.rate

            if self.allowance < 1.0:
                return False

            self.allowance -= 1.0
            return True

    async def wait(self) -> None:
        """等待获取许可"""
        while not await self.acquire():
            wait_time = self.per / self.rate
            logger.debug(f"⏳ 速率限制，等待 {wait_time:.2f} 秒")
            await asyncio.sleep(wait_time)


class SemaphoreManager:
    """
    信号量管理器

    提供并发控制功能
    """

    def __init__(self, max_concurrent: int, name: str = "semaphore"):
        """
        初始化信号量管理器

        Args:
            max_concurrent: 最大并发数
            name: 名称（用于日志）
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.name = name
        self.active_count = 0
        self.total_requests = 0
        self.total_wait_time = 0.0

    @property
    def available(self) -> int:
        """获取可用许可数"""
        return self.semaphore._value

    @property
    def usage_percent(self) -> float:
        """获取使用率百分比"""
        if self.max_concurrent == 0:
            return 0.0
        return (self.active_count / self.max_concurrent) * 100

    @asynccontextmanager
    async def acquire(self, timeout: float | None = None):
        """
        获取信号量

        Args:
            timeout: 超时时间（秒）

        Yields:
            None

        Raises:
            ConcurrentLimitExceededError: 获取超时
        """
        start_time = time.monotonic()
        self.total_requests += 1

        try:
            # 尝试获取信号量
            acquired = False
            if timeout:
                acquired = await asyncio.wait_for(
                    self.semaphore.acquire(),
                    timeout=timeout,
                )
            else:
                await self.semaphore.acquire()
                acquired = True

            wait_time = time.monotonic() - start_time
            self.total_wait_time += wait_time
            self.active_count += 1

            if wait_time > 0.1:  # 等待超过100ms记录日志
                logger.debug(
                    f"🔒 {self.name}: 等待 {wait_time:.2f}s "
                    f"(活跃: {self.active_count}/{self.max_concurrent})"
                )

            yield

        except TimeoutError:
            logger.warning(
                f"⚠️ {self.name}: 获取信号量超时 ({timeout}s)"
            )
            raise ConcurrentLimitExceededError(
                message=f"并发控制: 获取{self.name}超时",
                limit=self.max_concurrent,
                details={
                    "active": self.active_count,
                    "max": self.max_concurrent,
                    "wait_time": timeout,
                },
            ) from None

        finally:
            # 释放信号量
            if acquired or self.semaphore._value < self.max_concurrent:
                self.semaphore.release()
                self.active_count -= 1

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            dict: 统计信息
        """
        avg_wait = (
            self.total_wait_time / self.total_requests
            if self.total_requests > 0
            else 0
        )

        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "active_count": self.active_count,
            "available": self.available,
            "usage_percent": round(self.usage_percent, 2),
            "total_requests": self.total_requests,
            "avg_wait_time": round(avg_wait, 3),
        }


class CircuitBreaker:
    """
    熔断器

    防止级联故障
    """

    # 状态枚举
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 半开

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        half_open_attempts: int = 3,
        name: str = "circuit_breaker",
    ):
        """
        初始化熔断器

        Args:
            failure_threshold: 失败阈值
            timeout: 熔断超时时间（秒）
            half_open_attempts: 半开状态尝试次数
            name: 名称
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts
        self.name = name

        self.state = self.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.half_open_success_count = 0

        self._lock = asyncio.Lock()

    async def call(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 函数返回值

        Raises:
            Exception: 熔断器打开或函数执行失败
        """
        async with self._lock:
            # 检查是否应该尝试恢复
            if self.state == self.OPEN:
                if time.monotonic() - self.last_failure_time > self.timeout:
                    logger.info(f"🔄 {self.name}: 熔断器进入半开状态")
                    self.state = self.HALF_OPEN
                    self.half_open_success_count = 0
                else:
                    raise Exception(f"{self.name}: 熔断器打开，拒绝请求")

        # 执行函数
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 成功
            async with self._lock:
                if self.state == self.HALF_OPEN:
                    self.half_open_success_count += 1
                    if self.half_open_success_count >= self.half_open_attempts:
                        logger.info(f"✅ {self.name}: 熔断器恢复到关闭状态")
                        self.state = self.CLOSED
                        self.failure_count = 0

                self.failure_count = 0

            return result

        except Exception:
            # 失败
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.monotonic()

                if self.failure_count >= self.failure_threshold:
                    if self.state != self.OPEN:
                        logger.warning(
                            f"⚠️ {self.name}: 熔断器打开 "
                            f"(失败数: {self.failure_count})"
                        )
                        self.state = self.OPEN

            raise

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "time_until_retry": max(
                0,
                self.timeout - (time.monotonic() - self.last_failure_time),
            ),
        }


# =============================================================================
# 全局并发控制管理器
# =============================================================================


class ConcurrencyManager:
    """
    并发控制管理器

    集中管理所有并发控制资源
    """

    def __init__(self):
        """初始化并发控制管理器"""
        # 导航操作信号量
        self.navigate_semaphore = SemaphoreManager(
            max_concurrent=5,
            name="navigate_semaphore",
        )

        # 点击操作信号量
        self.click_semaphore = SemaphoreManager(
            max_concurrent=10,
            name="click_semaphore",
        )

        # 填充操作信号量
        self.fill_semaphore = SemaphoreManager(
            max_concurrent=10,
            name="fill_semaphore",
        )

        # 截图操作信号量
        self.screenshot_semaphore = SemaphoreManager(
            max_concurrent=3,
            name="screenshot_semaphore",
        )

        # JavaScript执行信号量
        self.js_semaphore = SemaphoreManager(
            max_concurrent=5,
            name="js_semaphore",
        )

        # 任务执行信号量
        self.task_semaphore = SemaphoreManager(
            max_concurrent=settings.MAX_CONCURRENT_TASKS,
            name="task_semaphore",
        )

        # 速率限制器
        self.rate_limiter = RateLimiter(
            rate=settings.RATE_LIMIT_PER_MINUTE,
            per=60,
        )

    async def check_rate_limit(self) -> bool:
        """
        检查速率限制

        Returns:
            bool: 是否允许请求
        """
        return await self.rate_limiter.acquire()

    def get_all_stats(self) -> dict[str, Any]:
        """
        获取所有统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "semaphores": {
                "navigate": self.navigate_semaphore.get_stats(),
                "click": self.click_semaphore.get_stats(),
                "fill": self.fill_semaphore.get_stats(),
                "screenshot": self.screenshot_semaphore.get_stats(),
                "js": self.js_semaphore.get_stats(),
                "task": self.task_semaphore.get_stats(),
            },
            "rate_limit": {
                "rate": self.rate_limiter.rate,
                "per": self.rate_limiter.per,
                "allowance": self.rate_limiter.allowance,
            },
        }


# 全局并发控制管理器实例
_concurrency_manager: ConcurrencyManager | None = None


def get_concurrency_manager() -> ConcurrencyManager:
    """获取全局并发控制管理器实例"""
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager()
    return _concurrency_manager


# 导出
__all__ = [
    "RateLimiter",
    "SemaphoreManager",
    "CircuitBreaker",
    "ConcurrencyManager",
    "get_concurrency_manager",
]
