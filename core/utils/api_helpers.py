#!/usr/bin/env python3
from __future__ import annotations
"""
API辅助工具
API Helper Utilities

版本: 1.0.0
功能:
- 统一的异常处理
- 统一的响应格式
- 统一的错误响应
- 减少重复代码
"""

import logging
import traceback
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# 统一响应格式
# ============================================================================

class APIResponse:
    """统一API响应格式"""

    @staticmethod
    def success(
        data: Any,
        message: str = "操作成功",
        code: int = 200
    ) -> dict[str, Any]:
        """
        成功响应

        Args:
            data: 响应数据
            message: 响应消息
            code: 状态码

        Returns:
            响应字典
        """
        return {
            "success": True,
            "code": code,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def error(
        message: str,
        code: int = 500,
        details: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        错误响应

        Args:
            message: 错误消息
            code: 错误码
            details: 错误详情

        Returns:
            响应字典
        """
        response = {
            "success": False,
            "code": code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        if details:
            response["details"] = details

        return response


# ============================================================================
# 异常处理装饰器
# ============================================================================

def handle_api_errors(
    error_map: dict[type, tuple[int, str]] | None | None = None,
    default_message: str = "操作失败",
    log_error: bool = True
):
    """
    API异常处理装饰器

    Args:
        error_map: 异常类型映射 {异常类: (状态码, 消息)}
        default_message: 默认错误消息
        log_error: 是否记录错误日志

    Returns:
        装饰器
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                # 查找错误映射
                error_type = type(e)
                status_code, message = error_map.get(
                    error_type,
                    (status.HTTP_500_INTERNAL_SERVER_ERROR, default_message)
                )

                # 记录错误
                if log_error:
                    logger.error(
                        f"❌ {func.__name__} 执行失败: {str(e)}",
                        exc_info=True
                    )

                raise HTTPException(
                    status_code=status_code,
                    detail=message or str(e)
                ) from e

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                # 查找错误映射
                error_type = type(e)
                status_code, message = error_map.get(
                    error_type,
                    (status.HTTP_500_INTERNAL_SERVER_ERROR, default_message)
                )

                # 记录错误
                if log_error:
                    logger.error(
                        f"❌ {func.__name__} 执行失败: {str(e)}",
                        exc_info=True
                    )

                raise HTTPException(
                    status_code=status_code,
                    detail=message or str(e)
                ) from e

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# 数据验证装饰器
# ============================================================================

def validate_request(
    validators: dict[str, Callable[[Any], bool]],
    error_message: str = "请求参数验证失败"
):
    """
    请求验证装饰器

    Args:
        validators: 验证器字典 {字段名: 验证函数}
        error_message: 验证失败消息

    Returns:
        装饰器
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # 从kwargs中获取请求参数
            for field_name, validator in validators.items():
                if field_name in kwargs:
                    value = kwargs[field_name]
                    if not validator(value):
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"{error_message}: {field_name}"
                        )
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            for field_name, validator in validators.items():
                if field_name in kwargs:
                    value = kwargs[field_name]
                    if not validator(value):
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"{error_message}: {field_name}"
                        )
            return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# 性能监控装饰器
# ============================================================================

def monitor_performance(
    log_threshold_ms: float = 1000.0,
    collector_name: str = "default"
):
    """
    性能监控装饰器

    Args:
        log_threshold_ms: 记录慢请求的阈值(毫秒)
        collector_name: 指标收集器名称

    Returns:
        装饰器
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start_time = datetime.now()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000

                # 记录到指标收集器
                try:
                    from core.monitoring.metrics_collector import get_metrics_collector
                    collector = get_metrics_collector()
                    collector.observe_histogram(
                        f"{func.__name__}_duration_ms",
                        duration_ms
                    )
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[api_helpers] Exception: {e}")

                # 记录慢请求
                if duration_ms > log_threshold_ms:
                    logger.warning(
                        f"⚠️ 慢请求: {func.__name__} 耗时 {duration_ms:.0f}ms"
                    )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000

                # 记录到指标收集器
                try:
                    from core.monitoring.metrics_collector import get_metrics_collector
                    collector = get_metrics_collector()
                    collector.observe_histogram(
                        f"{func.__name__}_duration_ms",
                        duration_ms
                    )
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[api_helpers] Exception: {e}")

                # 记录慢请求
                if duration_ms > log_threshold_ms:
                    logger.warning(
                        f"⚠️ 慢请求: {func.__name__} 耗时 {duration_ms:.0f}ms"
                    )

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# 统一的异常响应
# ============================================================================

def create_error_response(
    error: Exception,
    include_traceback: bool = False
) -> JSONResponse:
    """
    创建统一错误响应

    Args:
        error: 异常对象
        include_traceback: 是否包含堆栈跟踪

    Returns:
        JSONResponse
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = str(error)

    # 如果是HTTPException,使用其状态码和详情
    if isinstance(error, HTTPException):
        status_code = error.status_code
        detail = error.detail

    response_data = {
        "success": False,
        "code": status_code,
        "message": detail,
        "timestamp": datetime.now().isoformat()
    }

    # 开发环境包含堆栈跟踪
    if include_traceback:
        response_data["traceback"] = traceback.format_exc()

    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


# ============================================================================
# 请求日志记录
# ============================================================================

def log_request(
    request: Request,
    response_status: int,
    duration_ms: float
):
    """
    记录请求日志

    Args:
        request: FastAPI请求对象
        response_status: 响应状态码
        duration_ms: 请求耗时(毫秒)
    """
    logger.info(
        f"✅ {request.method} {request.url.path} - "
        f"{response_status} - {duration_ms:.0f}ms"
    )


# ============================================================================
# 输入清理
# ============================================================================

def sanitize_input(text: str, max_length: int = 100000) -> str:
    """
    清理用户输入

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        清理后的文本
    """
    import html

    # 长度限制
    if len(text) > max_length:
        text = text[:max_length]

    # HTML解码
    text = html.unescape(text)

    # 移除控制字符
    text = ''.join(
        c for c in text
        if c == '\n' or c == '\t' or ord(c) >= 32
    )

    return text.strip()


# ============================================================================
# 分页辅助
# ============================================================================

def parse_pagination_params(
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
) -> tuple[int, int, int]:
    """
    解析分页参数

    Args:
        page: 页码
        page_size: 每页大小
        max_page_size: 最大每页大小

    Returns:
        (offset, limit, page)
    """
    # 限制范围
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)

    offset = (page - 1) * page_size
    limit = page_size

    return offset, limit, page


def create_pagination_response(
    items: list,
    total: int,
    page: int,
    page_size: int
) -> dict[str, Any]:
    """
    创建分页响应

    Args:
        items: 数据列表
        total: 总数
        page: 当前页码
        page_size: 每页大小

    Returns:
        分页响应字典
    """
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
