#!/usr/bin/env python3
from __future__ import annotations
"""
错误处理器
Error Handler

统一的错误处理和格式化工具

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import asyncio
import functools
import logging
import traceback
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from typing import Any, TypeVar

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

from ..exceptions import AthenaError, format_error

logger = logging.getLogger(__name__)

# 泛型类型定义
T = TypeVar("T")
P = ParamSpec("P")


class ErrorHandler:
    """
    统一错误处理器

    提供错误捕获、记录、格式化和恢复等功能
    """

    def __init__(self, component_name: str, raise_on_error: bool = False):
        """
        初始化错误处理器

        Args:
            component_name: 组件名称(用于日志)
            raise_on_error: 是否在处理后重新抛出异常
        """
        self.component_name = component_name
        self.raise_on_error = raise_on_error
        self.error_count = 0
        self.last_error: Exception | None = None
        self.last_error_time: datetime | None = None

    def handle_error(
        self, error: Exception, context: str = "", additional_info: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        处理错误并返回统一格式的错误响应

        Args:
            error: 异常对象
            context: 上下文信息
            additional_info: 额外信息

        Returns:
            Dict: 格式化的错误响应
        """
        self.error_count += 1
        self.last_error = error
        self.last_error_time = datetime.now()

        # 构建错误信息
        error_info = format_error(error)
        error_info["component"] = self.component_name
        error_info["context"] = context
        error_info["error_count"] = self.error_count

        if additional_info:
            error_info["additional_info"] = additional_info

        # 记录日志
        if isinstance(error, AthenaError):
            # Athena自定义异常使用WARNING级别
            logger.warning(
                f"⚠️ [{self.component_name}] {context}: {error}", extra={"error_info": error_info}
            )
        else:
            # 其他异常使用ERROR级别
            logger.error(
                f"❌ [{self.component_name}] {context}: {error}\n{traceback.format_exc()}",
                extra={"error_info": error_info},
            )

        # 如果需要重新抛出异常
        if self.raise_on_error:
            raise error

        return error_info

    @contextmanager
    def error_boundary(self, context: str = "") -> Any:
        """
        错误边界上下文管理器

        Args:
            context: 上下文信息

        Example:
            >>> with error_handler.error_boundary("处理用户请求"):
            ...     risky_operation()
        """
        try:
            yield
        except Exception as e:
            self.handle_error(e, context)

    def get_stats(self) -> dict[str, Any]:
        """
        获取错误统计信息

        Returns:
            Dict: 统计信息
        """
        # 格式化last_error,包含异常类型名
        last_error_str = None
        if self.last_error:
            error_type = type(self.last_error).__name__
            error_msg = str(self.last_error)
            last_error_str = f"{error_type}: {error_msg}" if error_msg else error_type

        return {
            "component": self.component_name,
            "total_errors": self.error_count,
            "last_error": last_error_str,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


def create_error_handler(component_name: str, raise_on_error: bool = False) -> ErrorHandler:
    """
    创建错误处理器

    Args:
        component_name: 组件名称
        raise_on_error: 是否重新抛出异常

    Returns:
        ErrorHandler: 错误处理器实例
    """
    return ErrorHandler(component_name, raise_on_error)


# ==================== 装饰器 ====================


def async_error_handler(
    context: str = "", raise_on_error: bool = False, component_name: str | None = None
):
    """
    异步错误处理装饰器

    Args:
        context: 上下文信息
        raise_on_error: 是否重新抛出异常
        component_name: 组件名称

    Example:
        >>> @async_error_handler("数据库查询")
        ... async def query_data():
        ...     ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 确定组件名称
                comp_name = component_name or func.__qualname__

                # 处理错误
                handler = create_error_handler(comp_name, raise_on_error)
                handler.handle_error(e, context or func.__name__)

                # 如果不重新抛出,返回错误响应
                if not raise_on_error:
                    # 根据函数返回类型决定返回值
                    # 这里返回None,实际使用中可能需要根据情况调整
                    return None  # type: ignore

                # 重新抛出异常
                raise

        return wrapper

    return decorator


def sync_error_handler(
    context: str = "", raise_on_error: bool = False, component_name: str | None = None
):
    """
    同步错误处理装饰器

    Args:
        context: 上下文信息
        raise_on_error: 是否重新抛出异常
        component_name: 组件名称

    Example:
        >>> @sync_error_handler("文件读取")
        ... def read_file(path):
        ...     ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 确定组件名称
                comp_name = component_name or func.__qualname__

                # 处理错误
                handler = create_error_handler(comp_name, raise_on_error)
                handler.handle_error(e, context or func.__name__)

                # 如果不重新抛出,返回错误响应
                if not raise_on_error:
                    return None  # type: ignore

                # 重新抛出异常
                raise

        return wrapper

    return decorator


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_on: tuple | None = None,
):
    """
    错误重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟(秒)
        backoff_factor: 退避因子
        retry_on: 需要重试的异常类型元组

    Example:
        >>> @retry_on_error(max_attempts=3, delay=1.0)
        ... async def fetch_data():
        ...     ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # 检查是否应该重试
                    if retry_on and not isinstance(e, retry_on):
                        raise

                    # 最后一次尝试失败,不再重试
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"❌ 重试失败: {func.__qualname__} "
                            f"({attempt + 1}/{max_attempts}次尝试)"
                        )
                        raise

                    # 记录重试
                    logger.warning(
                        f"⚠️ 重试: {func.__qualname__} "
                        f"({attempt + 1}/{max_attempts}次尝试) "
                        f"- {e}, {current_delay}秒后重试"
                    )

                    # 等待后重试
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor

            # 理论上不会到这里
            raise last_exception  # type: ignore

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            import time

            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # 检查是否应该重试
                    if retry_on and not isinstance(e, retry_on):
                        raise

                    # 最后一次尝试失败,不再重试
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"❌ 重试失败: {func.__qualname__} "
                            f"({attempt + 1}/{max_attempts}次尝试)"
                        )
                        raise

                    # 记录重试
                    logger.warning(
                        f"⚠️ 重试: {func.__qualname__} "
                        f"({attempt + 1}/{max_attempts}次尝试) "
                        f"- {e}, {current_delay}秒后重试"
                    )

                    # 等待后重试
                    time.sleep(current_delay)
                    current_delay *= backoff_factor

            # 理论上不会到这里
            raise last_exception  # type: ignore

        # 根据函数类型选择包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# ==================== 便捷函数 ====================


def log_error(
    error: Exception,
    context: str = "",
    level: str = "ERROR",
    extra: dict[str, Any] | None = None,
):
    """
    记录错误日志

    Args:
        error: 异常对象
        context: 上下文信息
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        extra: 额外信息
    """
    log_func = getattr(logger, level.lower(), logger.error)

    error_info = format_error(error)
    error_info["context"] = context

    if extra:
        error_info.update(extra)

    log_func(
        f"{'⚠️' if level == 'WARNING' else '❌'} {context}: {error}",
        extra={"error_info": error_info},
    )


def format_error_response(error: Exception, include_traceback: bool = False) -> dict[str, Any]:
    """
    格式化错误响应

    Args:
        error: 异常对象
        include_traceback: 是否包含堆栈跟踪

    Returns:
        Dict: 格式化的错误响应
    """
    response = format_error(error)

    if include_traceback:
        response["traceback"] = traceback.format_exc()

    return response


def safe_execute(
    func: Callable[..., T],
    *args: Any,
    default: Any = None,
    on_error: Callable[[Exception, Any]] | None = None,
    **kwargs: Any,
) -> Any:
    """
    安全执行函数

    Args:
        func: 要执行的函数
        *args: 位置参数
        default: 发生异常时的默认返回值
        on_error: 错误回调函数
        **kwargs: 关键字参数

    Returns:
        函数执行结果或默认值

    Example:
        >>> result = safe_execute(risky_function, arg1, arg2, default=None)
        >>> if result is None:
        ...     print("函数执行失败")
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(e, context=f"safe_execute({func.__name__})")

        if on_error:
            return on_error(e)

        return default


async def async_safe_execute(
    func: Callable[..., T],
    *args: Any,
    default: Any = None,
    on_error: Callable[[Exception, Any]] | None = None,
    **kwargs: Any,
) -> Any:
    """
    安全执行异步函数

    Args:
        func: 要执行的异步函数
        *args: 位置参数
        default: 发生异常时的默认返回值
        on_error: 错误回调函数
        **kwargs: 关键字参数

    Returns:
        函数执行结果或默认值
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        log_error(e, context=f"async_safe_execute({func.__name__})")

        if on_error:
            return on_error(e)

        return default


# 导出
__all__ = [
    "ErrorHandler",
    "async_error_handler",
    "async_safe_execute",
    "create_error_handler",
    "format_error_response",
    "log_error",
    "retry_on_error",
    "safe_execute",
    "sync_error_handler",
]
