#!/usr/bin/env python3
"""
异常处理模块
Exception Handling Module

提供结构化的异常处理和错误响应

作者: Athena AI系统
创建时间: 2025-12-19
版本: 1.0.0
"""

from __future__ import annotations
import logging
import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """错误代码枚举"""

    # 通用错误 (1xxx)
    INTERNAL_SERVER_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # 认证/授权错误 (2xxx)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_API_KEY = "INVALID_API_KEY"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # 输入验证错误 (3xxx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_QUERY = "INVALID_QUERY"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER_TYPE = "INVALID_PARAMETER_TYPE"

    # 搜索引擎错误 (4xxx)
    SEARCH_ENGINE_UNAVAILABLE = "SEARCH_ENGINE_UNAVAILABLE"
    SEARCH_FAILED = "SEARCH_FAILED"
    NO_RESULTS = "NO_RESULTS"
    SEARCH_TIMEOUT = "SEARCH_TIMEOUT"

    # 数据库错误 (5xxx)
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    QUERY_EXECUTION_ERROR = "QUERY_EXECUTION_ERROR"

    # 外部API错误 (6xxx)
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    EXTERNAL_API_TIMEOUT = "EXTERNAL_API_TIMEOUT"
    EXTERNAL_API_RATE_LIMIT = "EXTERNAL_API_RATE_LIMIT"

    # 缓存错误 (7xxx)
    CACHE_ERROR = "CACHE_ERROR"
    CACHE_MISS = "CACHE_MISS"

    # 并发错误 (8xxx)
    CONCURRENCY_LIMIT_EXCEEDED = "CONCURRENCY_LIMIT_EXCEEDED"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"


@dataclass
class ErrorDetail:
    """错误详情"""

    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None
    timestamp: str = ""
    request_id: str = ""
    stack_trace: str | None = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "code": self.code.value,
            "message": self.message,
            "timestamp": self.timestamp,
        }

        if self.details:
            result["details"] = self.details

        if self.request_id:
            result["request_id"] = self.request_id

        if self.stack_trace:
            result["stack_trace"] = self.stack_trace

        return result


class AthenaException(Exception):
    """Athena平台基础异常类"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        """
        初始化异常

        Args:
            code: 错误代码
            message: 错误消息
            details: 额外详情
        """
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)

    def to_error_detail(self, request_id: str = "", include_stack: bool = False) -> ErrorDetail:
        """
        转换为错误详情对象

        Args:
            request_id: 请求ID
            include_stack: 是否包含堆栈跟踪

        Returns:
            错误详情对象
        """
        return ErrorDetail(
            code=self.code,
            message=self.message,
            details=self.details,
            request_id=request_id,
            stack_trace=traceback.format_exc() if include_stack else None,
        )


class AuthenticationError(AthenaException):
    """认证错误"""

    def __init__(self, message: str = "认证失败", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.UNAUTHORIZED, message, details)


class RateLimitError(AthenaException):
    """速率限制错误"""

    def __init__(self, message: str = "超过速率限制", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.RATE_LIMIT_EXCEEDED, message, details)


class ValidationError(AthenaException):
    """验证错误"""

    def __init__(self, message: str = "输入验证失败", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details)


class SearchError(AthenaException):
    """搜索引擎错误"""

    def __init__(self, message: str = "搜索失败", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.SEARCH_FAILED, message, details)


class DatabaseError(AthenaException):
    """数据库错误"""

    def __init__(self, message: str = "数据库操作失败", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.DATABASE_ERROR, message, details)


class ExternalAPIError(AthenaException):
    """外部API错误"""

    def __init__(self, message: str = "外部API调用失败", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.EXTERNAL_API_ERROR, message, details)


def create_error_response(
    error: AthenaException | Exception,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    request_id: str = "",
    include_stack: bool = False,
) -> JSONResponse:
    """
    创建错误响应

    Args:
        error: 异常对象
        status_code: HTTP状态码
        request_id: 请求ID
        include_stack: 是否包含堆栈跟踪

    Returns:
        JSON响应
    """
    if isinstance(error, AthenaException):
        error_detail = error.to_error_detail(request_id, include_stack)
    else:
        # 将普通异常转换为AthenaException
        error_detail = ErrorDetail(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=str(error),
            request_id=request_id,
            stack_trace=traceback.format_exc() if include_stack else None,
        )

    # 记录错误
    logger.error(
        f"错误: {error_detail.code.value} - {error_detail.message}",
        extra={"error_detail": error_detail.to_dict()},
    )

    return JSONResponse(
        status_code=status_code,
        content={"error": error_detail.to_dict()},
    )


def create_http_exception(
    code: ErrorCode,
    message: str,
    details: dict[str, Any] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> HTTPException:
    """
    创建HTTP异常

    Args:
        code: 错误代码
        message: 错误消息
        details: 额外详情
        status_code: HTTP状态码

    Returns:
        HTTPException对象
    """
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code.value,
            "message": message,
            "details": details,
        },
    )


async def athena_exception_handler(request: Request, exc: AthenaException) -> JSONResponse:
    """
    FastAPI异常处理器:AthenaException

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", "")

    # 根据错误代码确定HTTP状态码
    status_code_map = {
        ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
        ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    }

    status_code = status_code_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return create_error_response(exc, status_code, request_id)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    FastAPI异常处理器:通用异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", "")
    return create_error_response(exc, status.HTTP_500_INTERNAL_SERVER_ERROR, request_id)


def setup_exception_handlers(app) -> None:
    """
    为FastAPI应用设置异常处理器

    Args:
        app: FastAPI应用实例
    """
    app.add_exception_handler(AthenaException, athena_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("✅ 异常处理器已设置")


# 便捷装饰器
def handle_errors(
    default_message: str = "操作失败",
    error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
    reraise: bool = False,
):
    """
    错误处理装饰器

    Args:
        default_message: 默认错误消息
        error_code: 默认错误代码
        reraise: 是否重新抛出异常

    Returns:
        装饰器函数
    """

    def decorator(func) -> None:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AthenaException:
                if reraise:
                    raise
                # 记录并返回
                logger.exception(f"AthenaException in {func.__name__}")
                raise
            except Exception as e:
                logger.exception(f"Unexpected error in {func.__name__}")
                if reraise:
                    raise AthenaException(error_code, default_message, {"original_error": str(e)}) from e
                raise

        return wrapper

    return decorator


# 导出
__all__ = [
    "AthenaException",
    "AuthenticationError",
    "DatabaseError",
    "ErrorCode",
    "ErrorDetail",
    "ExternalAPIError",
    "RateLimitError",
    "SearchError",
    "ValidationError",
    "athena_exception_handler",
    "create_error_response",
    "create_http_exception",
    "general_exception_handler",
    "handle_errors",
    "setup_exception_handlers",
]
