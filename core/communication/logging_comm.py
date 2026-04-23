#!/usr/bin/env python3
from __future__ import annotations
"""
Athena通信系统 - 结构化日志
Structured Logging for Communication System

提供统一的结构化日志记录功能。

主要功能:
1. JSON格式日志
2. 组件标识
3. 上下文支持
4. 日志采样
5. 敏感信息过滤

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import json
import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SensitiveDataFilter:
    """敏感数据过滤器"""

    # 敏感字段模式
    SENSITIVE_PATTERNS = [
        r"password",
        r"passwd",
        r"secret",
        r"token",
        r"api_key",
        r"apikey",
        r"authorization",
        r"cookie",
        r"session",
    ]

    def __init__(self):
        """初始化敏感数据过滤器"""
        import re

        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS]

    def filter(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        过滤敏感数据

        Args:
            data: 原始数据

        Returns:
            过滤后的数据
        """
        filtered = {}

        for key, value in data.items():
            # 检查是否是敏感字段
            is_sensitive = any(pattern.search(key) for pattern in self.patterns)

            if is_sensitive and isinstance(value, str):
                # 掩盖敏感值
                if len(value) > 0:
                    filtered[key] = value[0] + "*" * (len(value) - 2) + value[-1]
                else:
                    filtered[key] = "***"
            elif isinstance(value, dict):
                # 递归过滤嵌套字典
                filtered[key] = self.filter(value)
            else:
                filtered[key] = value

        return filtered


class StructuredLogger:
    """
    结构化日志记录器

    提供JSON格式的结构化日志记录。
    """

    def __init__(
        self,
        name: str,
        component: str,
        level: LogLevel = LogLevel.INFO,
        enable_sensitive_filter: bool = True,
    ):
        """
        初始化结构化日志记录器

        Args:
            name: 日志记录器名称
            component: 组件名称
            level: 日志级别
            enable_sensitive_filter: 是否启用敏感数据过滤
        """
        self.logger = logging.getLogger(name)
        self.component = component
        self.level = level
        self.sensitive_filter = SensitiveDataFilter() if enable_sensitive_filter else None

    def _format(self, message: str, **kwargs) -> str:
        """格式化日志消息"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": self.level.value,
            "component": self.component,
            "message": message,
            **kwargs,
        }

        # 过滤敏感数据
        if self.sensitive_filter:
            log_entry = self.sensitive_filter.filter(log_entry)

        return json.dumps(log_entry, ensure_ascii=False)

    def debug(self, message: str, **kwargs) -> Any:
        """记录DEBUG级别日志"""
        self.logger.debug(self._format(message, **kwargs))

    def info(self, message: str, **kwargs) -> Any:
        """记录INFO级别日志"""
        self.logger.info(self._format(message, **kwargs))

    def warning(self, message: str, **kwargs) -> Any:
        """记录WARNING级别日志"""
        self.logger.warning(self._format(message, **kwargs))

    def error(self, message: str, **kwargs) -> Any:
        """记录ERROR级别日志"""
        self.logger.error(self._format(message, **kwargs))

    def critical(self, message: str, **kwargs) -> Any:
        """记录CRITICAL级别日志"""
        self.logger.critical(self._format(message, **kwargs))

    def exception(self, message: str, **kwargs) -> Any:
        """记录异常日志"""
        import traceback

        exc_info = traceback.format_exc()
        kwargs["exception"] = exc_info
        self.logger.error(self._format(message, **kwargs))


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器

    用于Python标准logging模块的格式化器。
    """

    def __init__(self, component: str):
        """
        初始化格式化器

        Args:
            component: 组件名称
        """
        super().__init__()
        self.component = component
        self.sensitive_filter = SensitiveDataFilter()

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基本字段
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "component": self.component,
            "logger": record.name,
            "message": record.get_message(),
            "module": record.module,
            "function": record.func_name,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.format_exception(record.exc_info)

        # 添加额外字段
        if hasattr(record, "custom_attributes"):
            log_entry.update(record.custom_attributes)

        # 过滤敏感数据
        log_entry = self.sensitive_filter.filter(log_entry)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_structured_logging(
    component: str, level: str = "INFO", log_file: Optional[str] = None, log_format: str = "json"
):
    """
    设置结构化日志

    Args:
        component: 组件名称
        level: 日志级别
        log_file: 日志文件路径
        log_format: 日志格式 (json, text)
    """
    root_logger = logging.getLogger()
    root_logger.set_level(getattr(logging, level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    if log_format == "json":
        formatter = StructuredFormatter(component)
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.set_formatter(formatter)
    root_logger.add_handler(console_handler)

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.set_formatter(formatter)
        root_logger.add_handler(file_handler)

    logger.info(f"结构化日志已设置: component={component}, level={level}, format={log_format}")


# =============================================================================
# 便捷函数
# =============================================================================


def create_logger(name: str, component: str) -> StructuredLogger:
    """创建结构化日志记录器"""
    return StructuredLogger(name, component)


def get_logger(component: str) -> StructuredLogger:
    """获取组件日志记录器"""
    return StructuredLogger(f"athena.communication.{component}", component)


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "LogLevel",
    "StructuredFormatter",
    "StructuredLogger",
    "create_logger",
    "get_logger",
    "setup_structured_logging",
]
