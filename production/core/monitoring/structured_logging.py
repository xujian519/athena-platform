#!/usr/bin/env python3
"""
结构化日志系统
Structured Logging System

版本: 1.0.0
功能:
- JSON格式日志输出
- 请求ID追踪
- 结构化字段
- 日志级别管理
- 上下文信息记录
"""

from __future__ import annotations
import json
import logging
import sys
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# 请求ID上下文变量
REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default=None)


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器

    输出JSON格式的日志,便于日志分析系统解析
    集成日志脱敏功能
    """

    def __init__(
        self,
        service_name: str = "athena-platform",
        environment: str = "development",
        include_extra: bool = True,
        enable_sanitization: bool = True,
    ):
        """
        初始化格式化器

        Args:
            service_name: 服务名称
            environment: 环境名称
            include_extra: 是否包含额外字段
            enable_sanitization: 是否启用日志脱敏
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_extra = include_extra
        self.enable_sanitization = enable_sanitization

        # 延迟导入脱敏器(避免循环导入)
        if enable_sanitization:
            try:
                from core.monitoring.log_sanitizer import get_log_sanitizer

                self.sanitizer = get_log_sanitizer()
            except ImportError:
                self.sanitizer = None
                logger.warning("⚠️ 日志脱敏器导入失败,将不进行脱敏")
        else:
            self.sanitizer = None

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON

        Args:
            record: 日志记录

        Returns:
            JSON字符串
        """
        # 获取原始消息
        original_message = record.getMessage()

        # 脱敏处理
        if self.sanitizer:
            sanitized_message = self.sanitizer.sanitize(original_message)
        else:
            sanitized_message = original_message

        # 基础字段
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitized_message,
            "service": self.service_name,
            "environment": self.environment,
            "sanitized": self.sanitizer is not None,
        }

        # 添加请求ID
        request_id = REQUEST_ID_CTX.get()
        if request_id:
            log_data["request_id"] = request_id

        # 异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # 位置信息
        if record.pathname and record.lineno:
            log_data["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # 额外字段
        if self.include_extra and hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """
    结构化日志记录器包装类

    提供更方便的日志记录方法
    """

    def __init__(self, name: str, level: int = logging.INFO, service_name: str = "athena-platform"):
        """
        初始化结构化日志记录器

        Args:
            name: 日志记录器名称
            level: 日志级别
            service_name: 服务名称
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 避免重复添加处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(StructuredFormatter(service_name=service_name))
            self.logger.addHandler(handler)

    def _add_extra_fields(self, extra: dict[str, Any]) -> dict[str, Any] | None:
        """添加额外字段到日志记录"""
        if not extra:
            return None

        # 创建新的日志记录
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.extra_fields = extra
            return record

        logging.setLogRecordFactory(record_factory)

        try:
            return extra
        finally:
            logging.setLogRecordFactory(old_factory)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        extra = kwargs.pop("extra", None)
        if extra:
            self._add_extra_fields(extra)
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        extra = kwargs.pop("extra", None)
        if extra:
            self._add_extra_fields(extra)
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        extra = kwargs.pop("extra", None)
        if extra:
            self._add_extra_fields(extra)
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        extra = kwargs.pop("extra", None)
        if extra:
            self._add_extra_fields(extra)
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        extra = kwargs.pop("extra", None)
        if extra:
            self._add_extra_fields(extra)
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """记录异常信息"""
        extra = kwargs.pop("extra", None)
        if extra:
            self._add_extra_fields(extra)
        self.logger.exception(message, **kwargs)


def get_structured_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """
    获取结构化日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        StructuredLogger实例
    """
    return StructuredLogger(name, level)


@contextmanager
def request_context(request_id: str | None = None):
    """
    请求上下文管理器

    Args:
        request_id: 请求ID(None自动生成)

    Usage:
        with request_context("req-123"):
            logger.info("处理请求")
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    token = REQUEST_ID_CTX.set(request_id)
    try:
        yield request_id
    finally:
        REQUEST_ID_CTX.reset(token)


def with_request_id(request_id: str):
    """
    装饰器:为函数调用添加请求ID

    Args:
        request_id: 请求ID

    Returns:
        装饰器
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            token = REQUEST_ID_CTX.set(request_id)
            try:
                return func(*args, **kwargs)
            finally:
                REQUEST_ID_CTX.reset(token)

        return wrapper

    return decorator


class RequestContextMiddleware:
    """
    请求上下文中间件(用于FastAPI等Web框架)
    """

    def __init__(self, app):
        """
        初始化中间件

        Args:
            app: ASGI应用
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """
        处理ASGI请求

        Args:
            scope: ASGI scope
            receive: ASGI receive
            send: ASGI send
        """
        if scope["type"] == "http":
            # 从请求头获取或生成请求ID
            headers = dict(scope.get("headers", []))
            request_id = headers.get(b"x-request-id", b"").decode()

            if not request_id:
                request_id = str(uuid.uuid4())

            # 设置上下文
            token = REQUEST_ID_CTX.set(request_id)

            try:
                await self.app(scope, receive, send)
            finally:
                REQUEST_ID_CTX.reset(token)
        else:
            await self.app(scope, receive, send)


class PerformanceLogger:
    """
    性能日志记录器

    专门用于记录性能相关的结构化日志
    """

    def __init__(self, logger: StructuredLogger):
        """
        初始化性能日志记录器

        Args:
            logger: 结构化日志记录器
        """
        self.logger = logger

    def log_api_request(
        self, method: str, path: str, status_code: int, duration_ms: float, **kwargs
    ):
        """
        记录API请求日志

        Args:
            method: HTTP方法
            path: 请求路径
            status_code: 状态码
            duration_ms: 响应时间(毫秒)
            **kwargs: 额外字段
        """
        self.logger.info(
            f"{method} {path} - {status_code}",
            extra={
                "event_type": "api_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                **kwargs,
            },
        )

    def log_database_query(
        self, query_type: str, table: str, duration_ms: float, rows_affected: int = 0, **kwargs
    ):
        """
        记录数据库查询日志

        Args:
            query_type: 查询类型(SELECT, INSERT等)
            table: 表名
            duration_ms: 执行时间(毫秒)
            rows_affected: 影响行数
            **kwargs: 额外字段
        """
        self.logger.debug(
            f"{query_type} {table}",
            extra={
                "event_type": "database_query",
                "query_type": query_type,
                "table": table,
                "duration_ms": round(duration_ms, 2),
                "rows_affected": rows_affected,
                **kwargs,
            },
        )

    def log_cache_operation(self, operation: str, cache_type: str, hit: bool, **kwargs):
        """
        记录缓存操作日志

        Args:
            operation: 操作类型(get, set, delete)
            cache_type: 缓存类型(redis, memory)
            hit: 是否命中
            **kwargs: 额外字段
        """
        self.logger.debug(
            f"cache {operation} - {'hit' if hit else 'miss'}",
            extra={
                "event_type": "cache_operation",
                "operation": operation,
                "cache_type": cache_type,
                "hit": hit,
                **kwargs,
            },
        )

    def log_external_api_call(
        self, service: str, endpoint: str, status: str, duration_ms: float, **kwargs
    ):
        """
        记录外部API调用日志

        Args:
            service: 服务名称
            endpoint: 端点路径
            status: 状态(success/error)
            duration_ms: 响应时间(毫秒)
            **kwargs: 额外字段
        """
        self.logger.info(
            f"external_api: {service} - {status}",
            extra={
                "event_type": "external_api_call",
                "service": service,
                "endpoint": endpoint,
                "status": status,
                "duration_ms": round(duration_ms, 2),
                **kwargs,
            },
        )


def get_performance_logger(name: str) -> PerformanceLogger:
    """
    获取性能日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        PerformanceLogger实例
    """
    logger = get_structured_logger(name)
    return PerformanceLogger(logger)


# 预配置的日志记录器
def setup_logging(
    service_name: str = "athena-platform",
    environment: str = "development",
    level: int = logging.INFO,
):
    """
    设置全局日志配置

    Args:
        service_name: 服务名称
        environment: 环境名称
        level: 日志级别
    """
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 移除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加结构化处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter(service_name=service_name, environment=environment))
    root_logger.addHandler(handler)

    # 配置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
