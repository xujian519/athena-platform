#!/usr/bin/env python3
"""
重试机制工具

为关键操作提供自动重试功能，提升系统可靠性。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import asyncio
import logging
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

# 类型变量
P = ParamSpec('P')
T = TypeVar('T')


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        初始化重试配置

        Args:
            max_attempts: 最大尝试次数（包括第一次）
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            exponential_base: 指数退避基数
            jitter: 是否添加随机抖动
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        计算第attempt次重试的延迟时间

        Args:
            attempt: 重试次数（从0开始）

        Returns:
            延迟时间（秒）
        """
        # 指数退避
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        # 添加随机抖动（避免雷群效应）
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay


class RetryError(Exception):
    """重试失败异常"""

    def __init__(
        self,
        message: str,
        last_exception: Exception | None = None,
        attempts: int = 0
    ):
        """
        初始化重试失败异常

        Args:
            message: 错误消息
            last_exception: 最后一次异常
            attempts: 尝试次数
        """
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


def retry(
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
    config: RetryConfig | None = None,
    on_retry: Callable[[Exception, int, None]] | None = None
):
    """
    同步函数重试装饰器

    Args:
        exceptions: 需要重试的异常类型
        config: 重试配置
        on_retry: 重试时的回调函数

    Examples:
        >>> @retry(exceptions=(ConnectionError, TimeoutError), max_attempts=3)
        >>> def fetch_data():
        ...     # 可能失败的网络操作
        ...     pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:

                    # 如果是最后一次尝试，不再重试
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"❌ 重试失败: {func.__name__} "
                            f"({config.max_attempts}次尝试后放弃)"
                        )
                        raise RetryError(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts",
                            last_exception=e,
                            attempts=config.max_attempts
                        ) from e

                    # 计算延迟时间
                    delay = config.get_delay(attempt)

                    logger.warning(
                        f"⚠️ {func.__name__} 失败 (尝试 {attempt + 1}/{config.max_attempts}), "
                        f"{delay:.2f}秒后重试. 错误: {e}"
                    )

                    # 调用回调
                    if on_retry:
                        on_retry(e, attempt + 1)

                    # 等待后重试
                    time.sleep(delay)

            # 不应该到达这里
            raise RuntimeError("Unexpected state in retry decorator")

        return wrapper
    return decorator


def async_retry(
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
    config: RetryConfig | None = None,
    on_retry: Callable[[Exception, int, None]] | None = None
):
    """
    异步函数重试装饰器

    Args:
        exceptions: 需要重试的异常类型
        config: 重试配置
        on_retry: 重试时的回调函数

    Examples:
        >>> @async_retry(exceptions=(ConnectionError, TimeoutError), max_attempts=3)
        >>> async def fetch_data_async():
        ...     # 可能失败的异步网络操作
        ...     pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:

                    # 如果是最后一次尝试，不再重试
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"❌ 异步重试失败: {func.__name__} "
                            f"({config.max_attempts}次尝试后放弃)"
                        )
                        raise RetryError(
                            f"Async function {func.__name__} failed after {config.max_attempts} attempts",
                            last_exception=e,
                            attempts=config.max_attempts
                        ) from e

                    # 计算延迟时间
                    delay = config.get_delay(attempt)

                    logger.warning(
                        f"⚠️ {func.__name__} 失败 (尝试 {attempt + 1}/{config.max_attempts}), "
                        f"{delay:.2f}秒后重试. 错误: {e}"
                    )

                    # 调用回调
                    if on_retry:
                        on_retry(e, attempt + 1)

                    # 等待后重试
                    await asyncio.sleep(delay)

            # 不应该到达这里
            raise RuntimeError("Unexpected state in async retry decorator")

        return wrapper
    return decorator


def retry_context(
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
    config: RetryConfig | None = None
):
    """
    重试上下文管理器

    用于代码块级别的重试控制。

    Args:
        exceptions: 需要重试的异常类型
        config: 重试配置

    Examples:
        >>> with retry_context(exceptions=ConnectionError, max_attempts=3):
        ...     # 可能失败的代码块
        ...     response = requests.get(url)
    """
    if config is None:
        config = RetryConfig()

    class RetryContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                return True

            if not isinstance(exc_val, exceptions):
                return False

            # 在with块中发生异常，需要重试
            # 这需要使用循环来实现，这里仅提供框架
            return False

    return RetryContext()


__all__ = [
    'RetryConfig',
    'RetryError',
    'async_retry',
    'retry',
    'retry_context'
]
