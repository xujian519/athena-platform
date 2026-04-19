#!/usr/bin/env python3
"""
重试处理器
Retry Handler

作者: Athena平台团队
版本: v1.0
创建: 2025-12-30

功能:
- 指数退避重试
- 智能错误判断
- 重试日志记录
"""

from __future__ import annotations
import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from .error_classifier import ErrorClassifier

logger = logging.getLogger("RetryHandler")

T = TypeVar("T")


class RetryHandler:
    """重试处理器"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """
        初始化重试处理器

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟秒数
            max_delay: 最大延迟秒数
            exponential_base: 指数退避基数
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    async def execute_with_retry(
        self, func: Callable, *args, error_context: str = "", **kwargs
    ) -> Any:
        """
        执行函数并在失败时重试

        Args:
            func: 要执行的异步函数
            *args: 位置参数
            error_context: 错误上下文描述
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 重试次数用尽后仍失败
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"🔄 第{attempt + 1}次尝试...")

                return await func(*args, **kwargs)

            except Exception as e:
                last_error = e
                severity, category = ErrorClassifier.classify(e)

                # 检查是否应该重试
                if not ErrorClassifier.should_retry(e):
                    logger.warning(f"❌ 错误不可重试 ({category.value}): {e}")
                    raise

                # 最后一次尝试失败
                if attempt >= self.max_retries:
                    logger.error(f"❌ 重试次数已达上限 ({self.max_retries}次): {e}")
                    raise

                # 计算延迟
                delay = self._calculate_delay(attempt, e)

                # 记录日志
                context_str = f"[{error_context}] " if error_context else ""
                logger.warning(
                    f"{context_str}⚠️ 第{attempt + 1}次尝试失败 "
                    f"({severity.value}/{category.value}): {e}, "
                    f"{delay:.1f}秒后重试..."
                )

                # 等待后重试
                await asyncio.sleep(delay)

        # 应该不会到达这里
        raise last_error

    def _calculate_delay(self, attempt: int, error: Exception) -> float:
        """
        计算重试延迟

        Args:
            attempt: 当前尝试次数
            error: 异常对象

        Returns:
            延迟秒数
        """
        # 使用错误分类器的建议延迟
        base_delay = ErrorClassifier.get_retry_delay(attempt, error)

        # 应用配置的倍数
        delay = base_delay * self.base_delay

        # 限制最大延迟
        return min(delay, self.max_delay)

    def sync_execute_with_retry(
        self, func: Callable, *args, error_context: str = "", **kwargs
    ) -> Any:
        """
        同步版本的带重试执行

        Args:
            func: 要执行的同步函数
            *args: 位置参数
            error_context: 错误上下文描述
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 重试次数用尽后仍失败
        """
        import time

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"🔄 第{attempt + 1}次尝试...")

                return func(*args, **kwargs)

            except Exception as e:
                last_error = e
                severity, category = ErrorClassifier.classify(e)

                # 检查是否应该重试
                if not ErrorClassifier.should_retry(e):
                    logger.warning(f"❌ 错误不可重试 ({category.value}): {e}")
                    raise

                # 最后一次尝试失败
                if attempt >= self.max_retries:
                    logger.error(f"❌ 重试次数已达上限 ({self.max_retries}次): {e}")
                    raise

                # 计算延迟
                delay = self._calculate_delay(attempt, e)

                # 记录日志
                context_str = f"[{error_context}] " if error_context else ""
                logger.warning(
                    f"{context_str}⚠️ 第{attempt + 1}次尝试失败 "
                    f"({severity.value}/{category.value}): {e}, "
                    f"{delay:.1f}秒后重试..."
                )

                # 等待后重试
                time.sleep(delay)

        # 应该不会到达这里
        raise last_error


# 全局默认重试处理器
_default_retry_handler = RetryHandler()


def retry_with_backoff(
    max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0, error_context: str = ""
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟秒数
        max_delay: 最大延迟秒数
        error_context: 错误上下文描述

    Returns:
        装饰器函数

    示例:
        @retry_with_backoff(max_retries=3, error_context="调用API")
        async def my_function():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = RetryHandler(
                max_retries=max_retries, base_delay=base_delay, max_delay=max_delay
            )
            return await handler.execute_with_retry(
                func, *args, error_context=error_context, **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            handler = RetryHandler(
                max_retries=max_retries, base_delay=base_delay, max_delay=max_delay
            )
            return handler.sync_execute_with_retry(
                func, *args, error_context=error_context, **kwargs
            )

        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def retry_async(
    func: Callable, *args, max_retries: int = 3, error_context: str = "", **kwargs
) -> Any:
    """
    便捷的异步重试函数

    Args:
        func: 异步函数
        *args: 位置参数
        max_retries: 最大重试次数
        error_context: 错误上下文
        **kwargs: 关键字参数

    Returns:
        函数执行结果

    示例:
        result = await retry_async(my_func, arg1, arg2, max_retries=2)
    """
    handler = RetryHandler(max_retries=max_retries)
    return await handler.execute_with_retry(func, *args, error_context=error_context, **kwargs)


def retry_sync(
    func: Callable, *args, max_retries: int = 3, error_context: str = "", **kwargs
) -> Any:
    """
    便捷的同步重试函数

    Args:
        func: 同步函数
        *args: 位置参数
        max_retries: 最大重试次数
        error_context: 错误上下文
        **kwargs: 关键字参数

    Returns:
        函数执行结果

    示例:
        result = retry_sync(my_func, arg1, arg2, max_retries=2)
    """
    handler = RetryHandler(max_retries=max_retries)
    return handler.sync_execute_with_retry(func, *args, error_context=error_context, **kwargs)
