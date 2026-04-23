#!/usr/bin/env python3
from __future__ import annotations
"""
错误处理器 - Athena平台统一错误处理
Error Handlers - Athena Platform Unified Error Handling

提供FastAPI的统一异常处理机制

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import logging
import traceback
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import (
    AthenaException,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 错误响应格式化
# ============================================================================


def format_error_response(
    code: str,
    message: str,
    status_code: int = 500,
    details: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    格式化错误响应

    Args:
        code: 错误代码
        message: 错误消息
        status_code: HTTP状态码
        details: 额外详情
        request_id: 请求ID(用于追踪)

    Returns:
        格式化的错误响应字典
    """
    response = {
        "success": False,
        "error": {"code": code, "message": message, "timestamp": datetime.now().isoformat()},
    }

    if details:
        response["error"]["details"] = details

    if request_id:
        response["request_id"] = request_id

    return response


def create_error_response(
    error: AthenaException | Exception | None = None, request_id: Optional[str] = None
) -> JSONResponse:
    """
    从异常创建错误响应

    Args:
        error: 异常对象
        request_id: 请求ID

    Returns:
        JSONResponse对象
    """
    if isinstance(error, AthenaException):
        content = format_error_response(
            code=error.code,
            message=error.message,
            status_code=error.status_code,
            details=error.details,
            request_id=request_id,
        )
        status_code = error.status_code
    else:
        content = format_error_response(
            code="INTERNAL_ERROR", message=str(error), status_code=500, request_id=request_id
        )
        status_code = 500

    return JSONResponse(status_code=status_code, content=content)


# ============================================================================
# 异常处理器
# ============================================================================


async def athena_exception_handler(request: Request, exc: AthenaException) -> JSONResponse:
    """
    Athena平台自定义异常处理器

    Args:
        request: FastAPI请求对象
        exc: AthenaException异常

    Returns:
        JSONResponse错误响应
    """
    # 获取请求ID(如果存在)
    request_id = getattr(request.state, "request_id", None)

    # 记录错误
    logger.error(
        f"Athena异常: {exc.code} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    # 返回错误响应
    return create_error_response(exc, request_id)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    请求验证异常处理器

    Args:
        request: FastAPI请求对象
        exc: RequestValidationError异常

    Returns:
        JSONResponse错误响应
    """
    request_id = getattr(request.state, "request_id", None)

    # 提取验证错误
    validation_errors = []
    for error in exc.errors():
        validation_errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"请求验证失败: {request.url.path}",
        extra={"request_id": request_id, "validation_errors": validation_errors},
    )

    content = format_error_response(
        code="VALIDATION_ERROR",
        message="请求参数验证失败",
        status_code=422,
        details={"validation_errors": validation_errors},
        request_id=request_id,
    )

    return JSONResponse(status_code=422, content=content)


async def http_exception_handler(
    request: Request, exc: HTTPException | StarletteHTTPException
) -> JSONResponse:
    """
    HTTP异常处理器

    Args:
        request: FastAPI请求对象
        exc: HTTPException异常

    Returns:
        JSONResponse错误响应
    """
    request_id = getattr(request.state, "request_id", None)

    # 标准HTTP状态码映射到错误代码
    status_code_to_code = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    code = status_code_to_code.get(exc.status_code, "HTTP_ERROR")

    logger.warning(
        f"HTTP异常: {code} - {exc.status_code}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "detail": exc.detail,
        },
    )

    content = format_error_response(
        code=code, message=exc.detail, status_code=exc.status_code, request_id=request_id
    )

    return JSONResponse(status_code=exc.status_code, content=content)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器(捕获所有未处理的异常)

    Args:
        request: FastAPI请求对象
        exc: 任意异常

    Returns:
        JSONResponse错误响应
    """
    request_id = getattr(request.state, "request_id", None)

    # 记录完整的堆栈跟踪
    logger.error(
        f"未捕获的异常: {type(exc).__name__}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "message": str(exc),
        },
    )

    # 在生产环境中,不暴露详细的错误信息
    error_message = "服务器内部错误"
    error_details = None

    # 在开发环境中,提供更多调试信息
    try:
        from core.config.settings import get_config

        config = get_config()
        if config.is_development():
            error_message = f"{type(exc).__name__}: {exc!s}"
            error_details = {
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }
    except Exception:
        pass  # 如果无法获取配置,使用默认值

    content = format_error_response(
        code="INTERNAL_ERROR",
        message=error_message,
        status_code=500,
        details=error_details,
        request_id=request_id,
    )

    return JSONResponse(status_code=500, content=content)


# ============================================================================
# FastAPI应用设置
# ============================================================================


def setup_error_handlers(app) -> None:
    """
    为FastAPI应用设置错误处理器

    Args:
        app: FastAPI应用实例
    """
    # Athena自定义异常
    app.add_exception_handler(AthenaException, athena_exception_handler)

    # FastAPI验证异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # HTTP异常
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # 通用异常(最后添加,作为fallback)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("错误处理器已设置完成")


# ============================================================================
# 中间件:请求ID生成
# ============================================================================


async def request_id_middleware(request: Request, call_next):
    """
    为每个请求生成唯一ID的中间件

    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件或路由处理器

    Returns:
        响应对象
    """
    import uuid

    # 生成或获取请求ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    # 添加请求ID到响应头
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# ============================================================================
# 便捷装饰器
# ============================================================================


def handle_exceptions(
    default_message: str = "操作失败", error_code: str = "OPERATION_FAILED", reraise: bool = False
):
    """
    异常处理装饰器

    Args:
        default_message: 默认错误消息
        error_code: 错误代码
        reraise: 是否重新抛出异常

    Returns:
        装饰器函数

    使用示例:
        @handle_exceptions("文件上传失败", "FILE_UPLOAD_ERROR")
        async def upload_file(file: UploadFile):
            ...
    """

    def decorator(func) -> None:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AthenaException:
                if reraise:
                    raise
                raise
            except Exception as e:
                logger.error(f"{error_code}: {e!s}", exc_info=True)
                if reraise:
                    raise
                raise AthenaException(
                    message=default_message, code=error_code, details={"original_error": str(e)}
                ) from e

        return wrapper

    return decorator


# ============================================================================
# 错误日志增强
# ============================================================================


class ErrorLogger:
    """增强的错误日志记录器"""

    @staticmethod
    def log_exception(
        exc: Exception, context: Optional[dict[str, Any]] = None, level: str = "ERROR"
    ):
        """
        记录异常信息

        Args:
            exc: 异常对象
            context: 上下文信息
            level: 日志级别
        """
        log_data = {
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "timestamp": datetime.now().isoformat(),
        }

        if context:
            log_data.update(context)

        if isinstance(exc, AthenaException):
            log_data.update(
                {"error_code": exc.code, "status_code": exc.status_code, "details": exc.details}
            )

        # 根据级别记录日志
        if level == "DEBUG":
            logger.debug("异常详情", extra=log_data)
        elif level == "INFO":
            logger.info("异常信息", extra=log_data)
        elif level == "WARNING":
            logger.warning("异常警告", extra=log_data)
        else:
            logger.error("异常错误", extra=log_data, exc_info=True)
