#!/usr/bin/env python3
"""
增强的异常处理和超时控制工具
Enhanced Exception Handling and Timeout Control Utilities

提供更健壮的异常处理和超时控制机制

功能:
1. 自定义异常类
2. 超时控制装饰器
3. 上下文管理器
4. 异常链支持

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v1.0.0
"""

import asyncio
import functools
import inspect
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

from core.logging_config import setup_logging

logger = setup_logging()

T = TypeVar("T")


# ==================== 自定义异常类 ====================

class OAResponseBaseError(Exception):
    """OA答复系统基础异常"""

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN",
        context: Optional[dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp,
        }


class PromptGenerationError(OAResponseBaseError):
    """提示词生成错误"""

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="PROMPT_GENERATION_ERROR",
            context=context,
        )


class KnowledgeGraphError(OAResponseBaseError):
    """知识图谱错误"""

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="KNOWLEDGE_GRAPH_ERROR",
            context=context,
        )


class WorkflowRecordError(OAResponseBaseError):
    """工作流记录错误"""

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="WORKFLOW_RECORD_ERROR",
            context=context,
        )


class PatternExtractionError(OAResponseBaseError):
    """模式提取错误"""

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="PATTERN_EXTRACTION_ERROR",
            context=context,
        )


class ConfigurationError(OAResponseBaseError):
    """配置错误"""

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context,
        )


class TimeoutErrorCustom(OAResponseBaseError):
    """超时错误"""

    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        context: Optional[dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            context={** (context or {}), "timeout_seconds": timeout_seconds},
        )


# ==================== 超时控制装饰器 ====================

def timeout(seconds: float, reraise: bool = True):
    """
    异步超时控制装饰器

    Args:
        seconds: 超时时间（秒）
        reraise: 是否重新抛出TimeoutErrorCustom

    Returns:
        装饰器函数

    示例:
        @timeout(seconds=5.0)
        async def my_async_function():
            await some_operation()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds,
                )
            except asyncio.TimeoutError:
                func_name = func.__name__
                logger.error(f"操作超时: {func_name} ({seconds}秒)")

                if reraise:
                    raise TimeoutErrorCustom(
                        message=f"操作超时: {func_name}",
                        timeout_seconds=seconds,
                        context={"function": func_name},
                    )
                return None  # type: ignore

        return wrapper
    return decorator


# ==================== 异常处理上下文管理器 ====================

@contextmanager
def handle_errors(
    error_types: tuple[type[Exception], ...] = (Exception,),
    default_return: Any = None,
    reraise: bool = False,
    context: Optional[dict[str, Any] | None = None,
):
    """
    异常处理上下文管理器

    Args:
        error_types: 要捕获的异常类型
        default_return: 发生异常时的默认返回值
        reraise: 是否重新抛出异常
        context: 额外的上下文信息

    示例:
        with handle_errors(error_types=(ValueError, TypeError), default_return=[]):
            result = some_function()
    """

    try:
        yield
    except error_types as e:
        logger.error(f"捕获异常: {type(e).__name__}: {e}", exc_info=True)

        if context:
            logger.error(f"上下文: {context}")

        if reraise:
            raise
        return default_return


# ==================== 安全执行包装器 ====================

def safe_execute(
    func: Callable[..., T],
    error_message: str = "操作失败",
    default_return: Any = None,
    log_level: str = "error",
) -> Callable[..., T]:
    """
    安全执行包装器

    Args:
        func: 要包装的函数
        error_message: 错误消息
        default_return: 默认返回值
        log_level: 日志级别

    Returns:
        包装后的函数
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_func = getattr(logger, log_level, logger.error)
            log_func(f"{error_message}: {e}")
            return default_return

    return wrapper


# ==================== 重试装饰器 ====================

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    失败重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟（秒）
        backoff_factor: 退避因子
        exceptions: 要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} 在 {max_attempts} 次尝试后仍然失败"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} 第 {attempt} 次尝试失败: {e}，"
                        f"{current_delay:.1f}秒后重试..."
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            import time

            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} 在 {max_attempts} 次尝试后仍然失败"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} 第 {attempt} 次尝试失败: {e}，"
                        f"{current_delay:.1f}秒后重试..."
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff_factor

        # 根据函数类型返回相应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==================== 日志记录装饰器 ====================

def log_execution(
    log_args: bool = True,
    log_result: bool = True,
    log_exceptions: bool = True,
):
    """
    日志记录装饰器

    Args:
        log_args: 是否记录参数
        log_result: 是否记录结果
        log_exceptions: 是否记录异常

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            func_name = func.__name__
            logger.info(f"→ 开始执行: {func_name}")

            if log_args:
                logger.debug(f"  参数: args={args}, kwargs={kwargs}")

            try:
                result = await func(*args, **kwargs)

                if log_result:
                    logger.debug(f"  结果: {result}")

                logger.info(f"✓ 完成: {func_name}")
                return result

            except Exception as e:
                if log_exceptions:
                    logger.error(
                        f"✗ 失败: {func_name} - {type(e).__name__}: {e}",
                        exc_info=True,
                    )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            func_name = func.__name__
            logger.info(f"→ 开始执行: {func_name}")

            if log_args:
                logger.debug(f"  参数: args={args}, kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)

                if log_result:
                    logger.debug(f"  结果: {result}")

                logger.info(f"✓ 完成: {func_name}")
                return result

            except Exception as e:
                if log_exceptions:
                    logger.error(
                        f"✗ 失败: {func_name} - {type(e).__name__}: {e}",
                        exc_info=True,
                    )
                raise

        # 根据函数类型返回相应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==================== 示例和测试 ====================

async def example_timeout_usage():
    """超时控制使用示例"""

    @timeout(seconds=2.0)
    async def slow_operation():
        await asyncio.sleep(1.0)
        return "完成"

    result = await slow_operation()
    print(f"结果: {result}")


async def example_retry_usage():
    """重试机制使用示例"""

    @retry_on_failure(max_attempts=3, exceptions=(ValueError,))
    async def unreliable_operation():
        import random

        if random.random() < 0.7:  # 70%失败率
            raise ValueError("随机失败")
        return "成功"

    try:
        result = await unreliable_operation()
        print(f"结果: {result}")
    except Exception as e:
        print(f"最终失败: {e}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_timeout_usage())
    asyncio.run(example_retry_usage())
