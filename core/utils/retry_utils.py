#!/usr/bin/env python3
"""
重试工具模块
Retry Utilities

版本: 1.0.0
功能:
- 提供重试装饰器
- 支持指数退避
- 支持自定义异常类型
- 支持最大重试次数配置
"""

import asyncio
import functools
import logging
import random
from collections.abc import Callable
from typing import Any, Optional, Tuple, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryExhaustedError(Exception):
    """重试次数耗尽异常"""

    def __init__(self, func_name: str, attempts: int, last_exception: Exception):
        self.func_name = func_name
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"函数 {func_name} 在 {attempts} 次尝试后失败: {last_exception!s}")


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_range: float = 0.1,
    ):
        """
        初始化重试配置

        Args:
            max_attempts: 最大尝试次数(包括首次调用)
            base_delay: 基础延迟时间(秒)
            max_delay: 最大延迟时间(秒)
            exponential_base: 指数退避的底数
            jitter: 是否添加随机抖动
            jitter_range: 抖动范围(0-1之间)
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_range = jitter_range

    def get_delay(self, attempt: int) -> float:
        """
        计算第attempt次重试的延迟时间

        Args:
            attempt: 重试次数(从1开始)

        Returns:
            延迟时间(秒)
        """
        # 指数退避
        delay = min(self.base_delay * (self.exponential_base ** (attempt - 1)), self.max_delay)

        # 添加随机抖动
        if self.jitter:
            jitter_amount = delay * self.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)


def retry_on_exception(
    exceptions: tuple[type[Exception], ...] = (Exception,),
    config: RetryConfig | None = None,
    on_retry: Callable[[int, Exception, None]] | None = None,
):
    """
    同步函数重试装饰器

    Args:
        exceptions: 需要重试的异常类型元组
        config: 重试配置(None使用默认配置)
        on_retry: 每次重试前的回调函数

    Returns:
        装饰后的函数
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            func_name = func.__name__

            for attempt in range(1, config.max_attempts + 1):
                try:
                    if attempt > 1:
                        logger.info(f"🔄 重试 {func_name} (第{attempt}次)")
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    is_last_attempt = attempt == config.max_attempts

                    if is_last_attempt:
                        logger.error(
                            f"❌ {func_name} 重试失败 ({attempt}/{config.max_attempts}): {e}"
                        )
                        raise RetryExhaustedError(func_name, attempt, e) from e

                    # 计算延迟
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"⚠️ {func_name} 失败 ({attempt}/{config.max_attempts}): {e}, "
                        f"{delay:.1f}秒后重试..."
                    )

                    # 调用回调
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as cb_error:
                            logger.error(f"❌ 重试回调失败: {cb_error}")

                    # 等待
                    import time

                    time.sleep(delay)

            # 理论上不会到达这里
            raise RetryExhaustedError(func_name, config.max_attempts, last_exception)

        return wrapper

    return decorator


def async_retry_on_exception(
    exceptions: tuple[type[Exception], ...] = (Exception,),
    config: RetryConfig | None = None,
    on_retry: Callable[[int, Exception, None]] | None = None,
):
    """
    异步函数重试装饰器

    Args:
        exceptions: 需要重试的异常类型元组
        config: 重试配置(None使用默认配置)
        on_retry: 每次重试前的回调函数

    Returns:
        装饰后的异步函数
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            func_name = func.__name__

            for attempt in range(1, config.max_attempts + 1):
                try:
                    if attempt > 1:
                        logger.info(f"🔄 异步重试 {func_name} (第{attempt}次)")
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    is_last_attempt = attempt == config.max_attempts

                    if is_last_attempt:
                        logger.error(
                            f"❌ {func_name} 异步重试失败 ({attempt}/{config.max_attempts}): {e}"
                        )
                        raise RetryExhaustedError(func_name, attempt, e) from e

                    # 计算延迟
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"⚠️ {func_name} 失败 ({attempt}/{config.max_attempts}): {e}, "
                        f"{delay:.1f}秒后重试..."
                    )

                    # 调用回调
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as cb_error:
                            logger.error(f"❌ 重试回调失败: {cb_error}")

                    # 异步等待
                    await asyncio.sleep(delay)

            # 理论上不会到达这里
            raise RetryExhaustedError(func_name, config.max_attempts, last_exception)

        return wrapper

    return decorator


def safe_execute(
    func: Callable[..., T],
    *args,
    default_value: Any = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    log_error: bool = True,
    **kwargs,
) -> T | None:
    """
    安全执行函数,捕获异常并返回默认值

    Args:
        func: 要执行的函数
        *args: 位置参数
        default_value: 发生异常时的默认返回值
        exceptions: 要捕获的异常类型
        log_error: 是否记录错误日志
        **kwargs: 关键字参数

    Returns:
        函数结果或默认值
    """
    try:
        return func(*args, **kwargs)
    except exceptions as e:
        if log_error:
            logger.error(f"❌ {func.__name__} 执行失败: {e}")
        return default_value


async def async_safe_execute(
    func: Callable[..., T],
    *args,
    default_value: Any = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    log_error: bool = True,
    **kwargs,
) -> T | None:
    """
    安全执行异步函数,捕获异常并返回默认值

    Args:
        func: 要执行的异步函数
        *args: 位置参数
        default_value: 发生异常时的默认返回值
        exceptions: 要捕获的异常类型
        log_error: 是否记录错误日志
        **kwargs: 关键字参数

    Returns:
        函数结果或默认值
    """
    try:
        return await func(*args, **kwargs)
    except exceptions as e:
        if log_error:
            logger.error(f"❌ {func.__name__} 异步执行失败: {e}")
        return default_value


# 预定义的重试配置
RETRY_CONFIG_FAST = RetryConfig(max_attempts=2, base_delay=0.5, max_delay=5.0)
RETRY_CONFIG_NORMAL = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=30.0)
RETRY_CONFIG_SLOW = RetryConfig(max_attempts=5, base_delay=2.0, max_delay=60.0)
RETRY_CONFIG_DATABASE = RetryConfig(
    max_attempts=3, base_delay=0.5, max_delay=10.0, jitter_range=0.2
)
RETRY_CONFIG_NETWORK = RetryConfig(
    max_attempts=4, base_delay=1.0, max_delay=30.0, exponential_base=2.5
)
