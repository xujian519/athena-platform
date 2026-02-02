#!/usr/bin/env python3
"""
Athena执行系统 - 日志工具和装饰器
Logging Utilities and Decorators for Execution System

提供统一的日志记录功能,包括:
1. 日志装饰器 - 自动记录函数执行
2. 性能监控装饰器 - 记录执行时间
3. 异常捕获装饰器 - 统一异常处理
4. 结构化日志支持

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import functools
import inspect
import logging
import time
from collections.abc import Callable
from typing import Any, ParamSpec

# Python 3.12+ 类型签名支持
P = ParamSpec("P")


# =============================================================================
# 日志装饰器
# =============================================================================


def log_execution(
    logger_name: str | None = None,
    level: int = logging.INFO,
    log_args: bool = True,
    log_result: bool = False,
    log_exception: bool = True,
) -> Callable:
    """
    日志记录装饰器

    自动记录函数的调用、参数、执行时间和结果/异常。

    Args:
        logger_name: 日志记录器名称,默认使用模块名
        level: 日志级别
        log_args: 是否记录参数
        log_result: 是否记录返回值
        log_exception: 是否记录异常

    Example:
        @log_execution(level=logging.DEBUG)
        async def my_function(x, y):
            return x + y
    """

    def decorator(func: Callable) -> Callable:
        # 获取日志记录器
        logger = logging.getLogger(logger_name or func.__module__)

        # 判断是否是异步函数
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                func_name = f"{func.__module__}.{func.__qualname__}"
                start_time = time.time()

                # 记录函数调用
                msg_parts = [f"开始 {func_name}"]
                if log_args and (args or kwargs):
                    args_str = ", ".join(repr(a) for a in args)
                    kwargs_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
                    params = ", ".join(filter(None, [args_str, kwargs_str]))
                    msg_parts.append(f"参数: ({params})")

                logger.log(level, " | ".join(msg_parts))

                try:
                    # 执行函数
                    result = await func(*args, **kwargs)

                    # 计算执行时间
                    duration = time.time() - start_time

                    # 记录成功结果
                    msg_parts = [f"完成 {func_name}", f"耗时: {duration:.3f}s"]
                    if log_result:
                        msg_parts.append(f"返回值: {result!r}")

                    logger.log(level, " | ".join(msg_parts))
                    return result

                except Exception as e:
                    # 计算执行时间
                    duration = time.time() - start_time

                    # 记录异常
                    if log_exception:
                        logger.error(
                            f"异常 {func_name} | 耗时: {duration:.3f}s | "
                            f"错误: {type(e).__name__}: {e}",
                            exc_info=True,
                        )
                    raise

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                func_name = f"{func.__module__}.{func.__qualname__}"
                start_time = time.time()

                # 记录函数调用
                msg_parts = [f"开始 {func_name}"]
                if log_args and (args or kwargs):
                    args_str = ", ".join(repr(a) for a in args)
                    kwargs_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
                    params = ", ".join(filter(None, [args_str, kwargs_str]))
                    msg_parts.append(f"参数: ({params})")

                logger.log(level, " | ".join(msg_parts))

                try:
                    # 执行函数
                    result = func(*args, **kwargs)

                    # 计算执行时间
                    duration = time.time() - start_time

                    # 记录成功结果
                    msg_parts = [f"完成 {func_name}", f"耗时: {duration:.3f}s"]
                    if log_result:
                        msg_parts.append(f"返回值: {result!r}")

                    logger.log(level, " | ".join(msg_parts))
                    return result

                except Exception as e:
                    # 计算执行时间
                    duration = time.time() - start_time

                    # 记录异常
                    if log_exception:
                        logger.error(
                            f"异常 {func_name} | 耗时: {duration:.3f}s | "
                            f"错误: {type(e).__name__}: {e}",
                            exc_info=True,
                        )
                    raise

            return sync_wrapper

    return decorator


def log_performance(logger_name: str | None = None, threshold_ms: float = 100.0) -> Callable:
    """
    性能监控装饰器

    记录函数执行时间,当执行时间超过阈值时发出警告。

    Args:
        logger_name: 日志记录器名称
        threshold_ms: 性能警告阈值(毫秒)

    Example:
        @log_performance(threshold_ms=50)
        async def fast_function():
            pass
    """

    def decorator(func: Callable) -> Callable:
        logger = logging.getLogger(logger_name or func.__module__)
        is_async = inspect.iscoroutinefunction(func)  # 使用 inspect.iscoroutinefunction

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                func_name = f"{func.__module__}.{func.__qualname__}"
                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)
                    return result

                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000

                    if duration_ms > threshold_ms:
                        logger.warning(
                            f"⚠️ 性能警告: {func_name} 执行时间 {duration_ms:.2f}ms "
                            f"超过阈值 {threshold_ms}ms"
                        )
                    else:
                        logger.debug(f"✓ {func_name} 执行时间 {duration_ms:.2f}ms")

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                func_name = f"{func.__module__}.{func.__qualname__}"
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    return result

                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000

                    if duration_ms > threshold_ms:
                        logger.warning(
                            f"⚠️ 性能警告: {func_name} 执行时间 {duration_ms:.2f}ms "
                            f"超过阈值 {threshold_ms}ms"
                        )
                    else:
                        logger.debug(f"✓ {func_name} 执行时间 {duration_ms:.2f}ms")

            return sync_wrapper

    return decorator


def log_exceptions(
    logger_name: str | None = None, reraise: bool = True, default_return: Any = None
) -> Callable:
    """
    异常捕获装饰器

    统一捕获和处理函数异常。

    Args:
        logger_name: 日志记录器名称
        reraise: 是否重新抛出异常
        default_return: 异常时的默认返回值

    Example:
        @log_exceptions(reraise=False, default_return=None)
        async def safe_function():
            pass
    """

    def decorator(func: Callable) -> Callable:
        logger = logging.getLogger(logger_name or func.__module__)
        is_async = inspect.iscoroutinefunction(func)  # 使用 inspect.iscoroutinefunction

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                func_name = f"{func.__module__}.{func.__qualname__}"

                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    logger.error(
                        f"❌ 异常捕获: {func_name} | " f"类型: {type(e).__name__} | 消息: {e}",
                        exc_info=True,
                    )

                    if reraise:
                        raise
                    else:
                        return default_return

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                func_name = f"{func.__module__}.{func.__qualname__}"

                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    logger.error(
                        f"❌ 异常捕获: {func_name} | " f"类型: {type(e).__name__} | 消息: {e}",
                        exc_info=True,
                    )

                    if reraise:
                        raise
                    else:
                        return default_return

            return sync_wrapper

    return decorator


# =============================================================================
# 结构化日志支持
# =============================================================================


class StructuredLogger:
    """
    结构化日志记录器

    提供结构化的日志记录格式,便于日志解析和分析。
    """

    def __init__(self, name: str, component: str | None = None):
        """
        初始化结构化日志记录器

        Args:
            name: 日志记录器名称
            component: 组件名称
        """
        self.logger = logging.getLogger(name)
        self.component = component or name

    def _format_message(self, message: str, **kwargs) -> str:
        """格式化结构化消息"""
        parts = [f"[{self.component}]", message]

        # 添加额外字段
        for key, value in kwargs.items():
            parts.append(f"{key}={value}")

        return " | ".join(parts)

    def info(self, message: str, **kwargs) -> Any:
        """记录INFO级别日志"""
        self.logger.info(self._format_message(message, **kwargs))

    def debug(self, message: str, **kwargs) -> Any:
        """记录DEBUG级别日志"""
        self.logger.debug(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs) -> Any:
        """记录WARNING级别日志"""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs) -> Any:
        """记录ERROR级别日志"""
        self.logger.error(self._format_message(message, **kwargs))

    def critical(self, message: str, **kwargs) -> Any:
        """记录CRITICAL级别日志"""
        self.logger.critical(self._format_message(message, **kwargs))

    def exception(self, message: str, **kwargs) -> Any:
        """记录异常日志"""
        self.logger.error(self._format_message(message, **kwargs), exc_info=True)


# =============================================================================
# 便捷函数
# =============================================================================


def get_structured_logger(name: str, component: str | None = None) -> StructuredLogger:
    """
    获取结构化日志记录器

    Args:
        name: 日志记录器名称
        component: 组件名称

    Returns:
        StructuredLogger实例
    """
    return StructuredLogger(name, component)


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "StructuredLogger",
    "get_structured_logger",
    "log_exceptions",
    "log_execution",
    "log_performance",

