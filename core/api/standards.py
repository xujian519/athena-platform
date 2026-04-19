from __future__ import annotations
"""
Athena工作平台 - API标准化模块
API Standards Module

提供统一的错误处理、响应格式和API版本控制
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# =============================================================================
# 标准响应格式
# =============================================================================


class APIResponse(BaseModel):
    """标准API响应格式"""

    success: bool
    message: str
    data: Any | None = None
    errors: list | None = None
    timestamp: str = None
    request_id: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {},
                "timestamp": "2025-12-24T12:00:00",
            }
        }


class PaginatedResponse(BaseModel):
    """分页响应格式"""

    success: bool
    message: str
    data: list
    pagination: dict[str, Any]
    timestamp: str


# =============================================================================
# 标准错误类
# =============================================================================


class APIError(Exception):
    """API错误基类"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class ValidationError(APIError):
    """验证错误"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(APIError):
    """资源未找到"""

    def __init__(self, message: str = "资源未找到", details: dict | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class AuthenticationError(APIError):
    """认证错误"""

    def __init__(self, message: str = "认证失败", details: dict | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class PermissionError(APIError):
    """权限错误"""

    def __init__(self, message: str = "权限不足", details: dict | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_ERROR",
            details=details,
        )


class ConflictError(APIError):
    """冲突错误"""

    def __init__(self, message: str = "资源冲突", details: dict | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT_ERROR",
            details=details,
        )


class RateLimitError(APIError):
    """速率限制错误"""

    def __init__(self, message: str = "请求过于频繁", details: dict | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
        )


# =============================================================================
# 统一错误处理器
# =============================================================================


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """处理自定义API错误"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证错误"""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": "请求验证失败",
            "error_code": "VALIDATION_ERROR",
            "errors": errors,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的异常"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
        },
    )


# =============================================================================
# API中间件配置
# =============================================================================


def setup_api_middleware(app: FastAPI, config: dict | None = None) -> None:
    """
    设置API标准中间件

    Args:
        app: FastAPI应用实例
        config: 配置字典(可选)
    """
    config = config or {}

    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("cors_origins", ["*"]),
        allow_credentials=config.get("cors_credentials", True),
        allow_methods=config.get("cors_methods", ["*"]),
        allow_headers=config.get("cors_headers", ["*"]),
    )

    # 注册错误处理器
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("API中间件配置完成")


# =============================================================================
# 辅助函数
# =============================================================================


def success_response(
    message: str = "操作成功", data: Any | None = None, request_id: str | None = None
) -> dict[str, Any]:
    """创建成功响应"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
    }


def error_response(
    message: str, error_code: str = "ERROR", details: dict | None = None
) -> dict[str, Any]:
    """创建错误响应"""
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "details": details,
        "timestamp": datetime.now().isoformat(),
    }


def paginated_response(
    message: str = "查询成功", data: list | None = None, page: int = 1, page_size: int = 10, total: int = 0
) -> dict[str, Any]:
    """创建分页响应"""
    return {
        "success": True,
        "message": message,
        "data": data or [],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        },
        "timestamp": datetime.now().isoformat(),
    }
