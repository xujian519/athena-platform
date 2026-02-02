#!/usr/bin/env python3
"""
错误处理和重试机制
Error Handling and Retry Mechanism

提供统一的错误处理、重试策略和异常管理
"""

import logging
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Type

logger = logging.getLogger(__name__)


# =============================================================================
# 错误类型枚举
# =============================================================================


class ErrorType(str, Enum):
    """错误类型分类"""

    # 网络相关
    NETWORK_ERROR = "network_error"
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"

    # 数据库相关
    DATABASE_ERROR = "database_error"
    QUERY_ERROR = "query_error"

    # 业务逻辑相关
    VALIDATION_ERROR = "validation_error"
    BUSINESS_ERROR = "business_error"
    NOT_FOUND_ERROR = "not_found_error"

    # 认证授权相关
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"

    # 系统相关
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_ERROR = "configuration_error"

    # 外部服务相关
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    RATE_LIMIT_ERROR = "rate_limit_error"

    # 通用错误
    UNKNOWN_ERROR = "unknown_error"


# =============================================================================
# 自定义异常
# =============================================================================


class AthenaError(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            error_type: 错误类型
            details: 详细信息
            original_error: 原始异常
        """
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = time.time()

        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


# =============================================================================
# 特定异常类
# =============================================================================


class ValidationError(AthenaError):
    """验证错误"""

    def __init__(self, message: str, field: str | None = None, value: Any | None = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(message=message, error_type=ErrorType.VALIDATION_ERROR, details=details)


class NotFoundError(AthenaError):
    """资源未找到错误"""

    def __init__(self, message: str, resource_type: str, resource_id: str):
        super().__init__(
            message=message,
            error_type=ErrorType.NOT_FOUND_ERROR,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class AuthenticationError(AthenaError):
    """认证错误"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message=message, error_type=ErrorType.AUTHENTICATION_ERROR)


class AuthorizationError(AthenaError):
    """授权错误"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message=message, error_type=ErrorType.AUTHORIZATION_ERROR)


class ExternalServiceError(AthenaError):
    """外部服务错误"""

    def __init__(self, message: str, service_name: str, status_code: int | None = None):
        details = {"service_name": service_name}
        if status_code:
            details["status_code"] = status_code

        super().__init__(
            message=message, error_type=ErrorType.EXTERNAL_SERVICE_ERROR, details=details
        )


class RateLimitError(AthenaError):
    """速率限制错误"""

    def __init__(self, message: str = "请求过于频繁", retry_after: int | None = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(message=message, error_type=ErrorType.RATE_LIMIT_ERROR, details=details)


# =============================================================================
# 重试策略配置
# =============================================================================


@dataclass
class RetryConfig:
    """重试配置"""

    max_attempts: int = 3  # 最大重试次数
    base_delay: float = 1.0  # 基础延迟(秒)
    max_delay: float = 60.0  # 最大延迟(秒)
    exponential_base: float = 2.0  # 指数退避基数
    jitter: bool = True  # 是否添加随机抖动
    retry_on: tuple[type[Exception], ...] = (Exception,)  # 可重试的异常类型


# =============================================================================
# 重试机制
# =============================================================================


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: tuple[type[Exception, ...]] | None = None,
):
    """
    重试装饰器(指数退避)

    Args:
        max_attempts: 最大重试次数
        base_delay: 基础延迟(秒)
        max_delay: 最大延迟(秒)
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动
        retry_on: 可重试的异常类型

    Returns:
        装饰器函数

    Examples:
        >>> @retry(max_attempts=3, base_delay=1.0)
        >>> def unstable_function():
        >>>     # 可能失败的操作
        >>>     pass
    """
    if retry_on is None:
        retry_on = (Exception,)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except retry_on as e:
                    last_exception = e

                    # 最后一次尝试失败,不再重试
                    if attempt == max_attempts - 1:
                        logger.error(f"函数 {func.__name__} 重试 {max_attempts} 次后仍失败")
                        raise

                    # 计算延迟时间
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    # 添加随机抖动
                    if jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"函数 {func.__name__} 执行失败 "
                        f"(尝试 {attempt + 1}/{max_attempts}): {e}, "
                        f"{delay:.2f}秒后重试"
                    )

                    time.sleep(delay)

            # 不应该到达这里
            raise last_exception

        return wrapper

    return decorator


class RetryManager:
    """
    重试管理器

    提供更灵活的重试控制

    Examples:
        >>> manager = RetryManager(config)
        >>>
        >>> result = manager.execute(unstable_operation)
    """

    def __init__(self, config: RetryConfig | None = None):
        """
        初始化重试管理器

        Args:
            config: 重试配置
        """
        self.config = config or RetryConfig()

    def execute(
        self,
        func: Callable,
        *args: Any,
        on_retry: Callable[[int, Exception, None] | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        执行带重试的函数

        Args:
            func: 要执行的函数
            *args: 位置参数
            on_retry: 重试回调函数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 重试耗尽后抛出最后一次异常
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)

            except self.config.retry_on as e:
                last_exception = e

                # 最后一次尝试失败
                if attempt == self.config.max_attempts - 1:
                    logger.error(
                        f"函数 {func.__name__} 重试 " f"{self.config.max_attempts} 次后仍失败"
                    )
                    break

                # 计算延迟
                delay = min(
                    self.config.base_delay * (self.config.exponential_base**attempt),
                    self.config.max_delay,
                )

                # 添加抖动
                if self.config.jitter:
                    import random

                    delay = delay * (0.5 + random.random())

                # 调用回调
                if on_retry:
                    try:
                        on_retry(attempt + 1, e)
                    except Exception as callback_error:
                        logger.error(f"重试回调函数出错: {callback_error}")

                logger.warning(
                    f"函数 {func.__name__} 执行失败 "
                    f"(尝试 {attempt + 1}/{self.config.max_attempts}): {e}, "
                    f"{delay:.2f}秒后重试"
                )

                time.sleep(delay)

        # 抛出最后一次异常
        if last_exception:
            raise last_exception


# =============================================================================
# 错误处理器
# =============================================================================


class ErrorHandler:
    """
    统一错误处理器

    提供错误捕获、日志记录和格式化响应

    Examples:
        >>> handler = ErrorHandler()
        >>>
        >>> try:
        >>>     risky_operation()
        >>> except Exception as e:
        >>>     error_dict = handler.handle_error(e)
        >>>     return error_dict
    """

    def __init__(self, include_traceback: bool = False):
        """
        初始化错误处理器

        Args:
            include_traceback: 是否包含堆栈跟踪
        """
        self.include_traceback = include_traceback

    def handle_error(
        self, error: Exception, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        处理错误并返回格式化的错误信息

        Args:
            error: 异常对象
            context: 额外上下文信息

        Returns:
            格式化的错误信息
        """
        # 如果是自定义异常,直接转换
        if isinstance(error, AthenaError):
            error_dict = error.to_dict()
        else:
            # 将标准异常转换为自定义异常
            error_type = self._classify_error(error)
            athena_error = AthenaError(
                message=str(error), error_type=error_type, original_error=error
            )
            error_dict = athena_error.to_dict()

        # 添加堆栈跟踪
        if self.include_traceback:
            error_dict["traceback"] = traceback.format_exc()

        # 添加上下文
        if context:
            error_dict["context"] = context

        # 记录错误日志
        self._log_error(error_dict)

        return error_dict

    def _classify_error(self, error: Exception) -> ErrorType:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            错误类型
        """
        error_name = type(error).__name__

        # 根据异常名称分类
        if "Connection" in error_name or "Connect" in error_name:
            return ErrorType.CONNECTION_ERROR
        elif "Timeout" in error_name:
            return ErrorType.TIMEOUT_ERROR
        elif "Auth" in error_name:
            return ErrorType.AUTHENTICATION_ERROR
        elif "Value" in error_name or "Validation" in error_name:
            return ErrorType.VALIDATION_ERROR
        elif "NotFound" in error_name or "NotExist" in error_name:
            return ErrorType.NOT_FOUND_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR

    def _log_error(self, error_dict: dict[str, Any]) -> None:
        """
        记录错误日志

        Args:
            error_dict: 错误信息字典
        """
        error_type = error_dict.get("error_type", "unknown")

        # 根据错误类型选择日志级别
        if error_type in (
            ErrorType.VALIDATION_ERROR,
            ErrorType.NOT_FOUND_ERROR,
            ErrorType.AUTHORIZATION_ERROR,
        ):
            log_func = logger.warning
        else:
            log_func = logger.error

        log_func(
            f"错误: [{error_type}] {error_dict.get('message')}", extra={"error_details": error_dict}
        )


# =============================================================================
# 便捷函数
# =============================================================================


def handle_errors(reraise: bool = False, default_return: Any = None):
    """
    错误处理装饰器

    Args:
        reraise: 是否重新抛出异常
        default_return: 异常时的默认返回值

    Returns:
        装饰器函数

    Examples:
        >>> @handle_errors(reraise=False, default_return={"error": True})
        >>> def risky_function():
        >>>     raise ValueError("出错了")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = ErrorHandler()
                error_dict = handler.handle_error(e)

                if reraise:
                    raise
                else:
                    return default_return if default_return is not None else error_dict

        return wrapper

    return decorator


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 异常类
    "AthenaError",
    "AuthenticationError",
    "AuthorizationError",
    # 错误处理
    "ErrorHandler",
    # 枚举
    "ErrorType",
    "ExternalServiceError",
    "NotFoundError",
    "RateLimitError",
    # 重试相关
    "RetryConfig",
    "RetryManager",
    "ValidationError",
    "handle_errors",
    "retry",
]
