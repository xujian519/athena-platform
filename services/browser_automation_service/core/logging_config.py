#!/usr/bin/env python3
"""
结构化日志配置
Structured Logging Configuration for Browser Automation Service

提供结构化日志、请求追踪、动态日志级别等功能

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import json
import logging
import logging.handlers
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import settings


class ContextFilter(logging.Filter):
    """日志上下文过滤器"""

    def __init__(self):
        super().__init__()
        self._context = {}

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文值"""
        self._context[key] = value

    def clear_context(self, key: str | None = None) -> None:
        """清除上下文值"""
        if key:
            self._context.pop(key, None)
        else:
            self._context.clear()

    def filter(self, record: logging.LogRecord) -> bool:
        """添加上下文到日志记录"""
        for key, value in self._context.items():
            setattr(record, key, value)
        return True


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""

    def __init__(
        self,
        service_name: str = "browser_automation",
        version: str = "1.0.0",
    ):
        super().__init__()
        self.service_name = service_name
        self.version = version

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        # 基础字段
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "version": self.version,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info else None,
                "message": str(record.exc_info[1]) if record.exc_info else None,
                "traceback": self.formatException(record.exc_info),
            }

        # 添加位置信息
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        # 添加上下文字段
        context_fields = [
            "request_id",
            "session_id",
            "user_id",
            "operation",
            "duration_ms",
            "error_id",
        ]

        for field in context_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        return json.dumps(log_data, ensure_ascii=False)


class RequestTracker:
    """请求追踪器"""

    def __init__(self):
        self._request_count = 0
        self._context_filter = ContextFilter()

    def generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid

        return f"REQ-{uuid.uuid4().hex[:12].upper()}"

    @contextmanager
    def track_request(
        self,
        operation: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ):
        """
        追踪请求上下文

        Args:
            operation: 操作名称
            user_id: 用户ID
            session_id: 会话ID

        Yields:
            str: 请求ID
        """
        request_id = self.generate_request_id()
        start_time = time.monotonic()

        # 设置上下文
        self._context_filter.set_context("request_id", request_id)
        self._context_filter.set_context("operation", operation)

        if user_id:
            self._context_filter.set_context("user_id", user_id)

        if session_id:
            self._context_filter.set_context("session_id", session_id)

        try:
            yield request_id
        finally:
            # 计算持续时间
            duration_ms = (time.monotonic() - start_time) * 1000
            self._context_filter.set_context("duration_ms", round(duration_ms, 2))

            # 清除上下文
            self._context_filter.clear_context()

    def get_context_filter(self) -> ContextFilter:
        """获取上下文过滤器"""
        return self._context_filter


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(
        self,
        name: str,
        service_name: str = "browser_automation",
        version: str = "1.0.0",
    ):
        """
        初始化结构化日志记录器

        Args:
            name: 日志记录器名称
            service_name: 服务名称
            version: 服务版本
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        self.logger.propagate = False

        # 清除现有处理器
        self.logger.handlers.clear()

        # 上下文过滤器
        self._context_filter = ContextFilter()

        # 控制台处理器（彩色）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)

        # 文件处理器（JSON格式）
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = JSONFormatter(
            service_name=service_name,
            version=version,
        )
        file_handler.setFormatter(file_formatter)

        # 添加过滤器
        console_handler.addFilter(self._context_filter)
        file_handler.addFilter(self._context_filter)

        # 添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def set_level(self, level: str | int) -> None:
        """动态设置日志级别"""
        self.logger.setLevel(level)

    def add_context(self, key: str, value: Any) -> None:
        """添加日志上下文"""
        self._context_filter.set_context(key, value)

    def clear_context(self, key: str | None = None) -> None:
        """清除日志上下文"""
        self._context_filter.clear_context(key)

    @contextmanager
    def context(self, **kwargs):
        """临时上下文管理器"""
        for key, value in kwargs.items():
            self.add_context(key, value)

        try:
            yield
        finally:
            for key in kwargs.keys():
                self.clear_context(key)

    # 便捷方法
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        with self.context(**kwargs):
            self.logger.debug(message)

    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        with self.context(**kwargs):
            self.logger.info(message)

    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        with self.context(**kwargs):
            self.logger.warning(message)

    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        with self.context(**kwargs):
            self.logger.error(message)

    def critical(self, message: str, **kwargs) -> None:
        """记录严重错误日志"""
        with self.context(**kwargs):
            self.logger.critical(message)

    def exception(self, message: str, **kwargs) -> None:
        """记录异常日志"""
        with self.context(**kwargs):
            self.logger.exception(message)


class ColoredFormatter(logging.Formatter):
    """彩色格式化器（用于控制台输出）"""

    # ANSI颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """添加颜色到日志级别"""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # 添加上下文信息
        parts = []
        if hasattr(record, "request_id"):
            parts.append(f"REQ:{record.request_id}")
        if hasattr(record, "operation"):
            parts.append(f"OP:{record.operation}")
        if hasattr(record, "duration_ms"):
            parts.append(f"DUR:{record.duration_ms}ms")

        if parts:
            record.message = f"[{' '.join(parts)}] {record.message}"

        return super().format(record)


# 全局日志记录器
_structured_logger: StructuredLogger | None = None
_request_tracker: RequestTracker | None = None


def get_structured_logger() -> StructuredLogger:
    """获取全局结构化日志记录器"""
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger(
            name="browser_automation",
            service_name=settings.SERVICE_NAME,
            version=settings.VERSION,
        )
    return _structured_logger


def get_request_tracker() -> RequestTracker:
    """获取全局请求追踪器"""
    global _request_tracker
    if _request_tracker is None:
        _request_tracker = RequestTracker()
    return _request_tracker


# 导出
__all__ = [
    "StructuredLogger",
    "RequestTracker",
    "ContextFilter",
    "JSONFormatter",
    "ColoredFormatter",
    "get_structured_logger",
    "get_request_tracker",
]
