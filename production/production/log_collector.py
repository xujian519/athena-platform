#!/usr/bin/env python3
"""
生产环境日志收集模块

提供结构化日志、JSON日志、日志轮转等功能
"""

from __future__ import annotations
import json
import logging
import logging.handlers
import sys
import time
import traceback
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from .production_config import LogConfig

# =============================================================================
# JSON日志格式化器
# =============================================================================

class JSONFormatter(logging.Formatter):
    """JSON格式化器 - 生产环境使用"""

    def __init__(
        self,
        service_name: str = "xiaonuo",
        service_version: str = "5.0.0",
        timestamp_format: str = "%Y-%m-%d_t%H:%M:%S.%f_z"
    ):
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version
        self.timestamp_format = timestamp_format

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        # 基础字段
        log_data = {
            "timestamp": datetime.utcnow().strftime(self.timestamp_format),
            "level": record.levelname,
            "logger": record.name,
            "message": record.get_message(),
            "service": self.service_name,
            "version": self.service_version,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.format_exception(record.exc_info),
            }

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # 添加位置信息
        if record.pathname and record.lineno:
            log_data["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.func_name,
            }

        # 添加进程/线程信息
        log_data["process"] = {
            "id": record.process,
            "name": record.process_name,
        }
        log_data["thread"] = {
            "id": record.thread,
            "name": record.thread_name,
        }

        return json.dumps(log_data, ensure_ascii=False)


# =============================================================================
# 增强的日志记录器
# =============================================================================

class StructuredLogger:
    """结构化日志记录器"""

    def __init__(
        self,
        name: str,
        config: LogConfig | None = None,
        service_name: str = "xiaonuo",
        service_version: str = "5.0.0"
    ):
        """
        初始化结构化日志记录器

        Args:
            name: 日志记录器名称
            config: 日志配置
            service_name: 服务名称
            service_version: 服务版本
        """
        self.name = name
        self.config = config or LogConfig()
        self.service_name = service_name
        self.service_version = service_version
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(self.name)
        logger.set_level(getattr(logging, self.config.level.upper()))

        # 清除现有处理器
        logger.handlers.clear()

        # JSON格式化器
        formatter = JSONFormatter(
            service_name=self.service_name,
            service_version=self.service_version
        )

        # 文件处理器（带轮转）
        if self.config.log_to_file:
            log_dir = Path(self.config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            # 所有日志文件
            all_handler = logging.handlers.RotatingFileHandler(
                log_dir / f"{self.name}.log",
                max_bytes=self.config.max_bytes,
                backup_count=self.config.backup_count,
                encoding="utf-8"
            )
            all_handler.set_level(logging.DEBUG)
            all_handler.set_formatter(formatter)
            logger.add_handler(all_handler)

            # 错误日志文件
            error_handler = logging.handlers.RotatingFileHandler(
                log_dir / f"{self.name}.error.log",
                max_bytes=self.config.max_bytes,
                backup_count=self.config.backup_count,
                encoding="utf-8"
            )
            error_handler.set_level(logging.ERROR)
            error_handler.set_formatter(formatter)
            logger.add_handler(error_handler)

        # 控制台处理器
        if self.config.log_to_console:
            console_handler = logging.stream_handler(sys.stdout)
            console_handler.set_level(getattr(logging, self.config.level.upper()))

            # 控制台使用可读格式
            if self.config.json_logs:
                console_handler.set_formatter(formatter)
            else:
                console_formatter = logging.formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                console_handler.set_formatter(console_formatter)

            logger.add_handler(console_handler)

        return logger

    def with_fields(self, **fields) -> "LoggerAdapter":
        """创建带额外字段的日志适配器"""
        return LoggerAdapter(self.logger, extra_fields=fields)

    def debug(self, msg: str, **kwargs) -> Any:
        """调试日志"""
        self._log(logging.DEBUG, msg, kwargs)

    def info(self, msg: str, **kwargs) -> Any:
        """信息日志"""
        self._log(logging.INFO, msg, kwargs)

    def warning(self, msg: str, **kwargs) -> Any:
        """警告日志"""
        self._log(logging.WARNING, msg, kwargs)

    def error(self, msg: str, **kwargs) -> Any:
        """错误日志"""
        self._log(logging.ERROR, msg, kwargs)

    def critical(self, msg: str, **kwargs) -> Any:
        """严重日志"""
        self._log(logging.CRITICAL, msg, kwargs)

    def exception(self, msg: str, **kwargs) -> Any:
        """异常日志（自动包含异常信息）"""
        self.logger.exception(msg, extra={"extra_fields": kwargs})

    def _log(self, level: int, msg: str, extra: dict[str, Any]) -> Any:
        """内部日志方法"""
        extra_fields = extra if extra else {}
        self.logger.log(level, msg, extra={"extra_fields": extra_fields})


# =============================================================================
# 日志适配器（支持额外字段）
# =============================================================================

class LoggerAdapter:
    """日志适配器"""

    def __init__(self, logger: logging.Logger, extra_fields: dict[str, Any]):
        self.logger = logger
        self.extra_fields = extra_fields

    def with_fields(self, **fields) -> "LoggerAdapter":
        """添加更多字段"""
        return LoggerAdapter(
            self.logger,
            {**self.extra_fields, **fields}
        )

    def debug(self, msg: str, **kwargs) -> Any:
        self.logger.debug(msg, extra={"extra_fields": {**self.extra_fields, **kwargs}})

    def info(self, msg: str, **kwargs) -> Any:
        self.logger.info(msg, extra={"extra_fields": {**self.extra_fields, **kwargs}})

    def warning(self, msg: str, **kwargs) -> Any:
        self.logger.warning(msg, extra={"extra_fields": {**self.extra_fields, **kwargs}})

    def error(self, msg: str, **kwargs) -> Any:
        self.logger.error(msg, extra={"extra_fields": {**self.extra_fields, **kwargs}})

    def critical(self, msg: str, **kwargs) -> Any:
        self.logger.critical(msg, extra={"extra_fields": {**self.extra_fields, **kwargs}})

    def exception(self, msg: str, **kwargs) -> Any:
        self.logger.exception(msg, extra={"extra_fields": {**self.extra_fields, **kwargs}})


# =============================================================================
# 性能日志装饰器
# =============================================================================

def log_execution_time(
    logger: logging.Logger | None = None,
    level: int = logging.INFO
):
    """
    记录函数执行时间的装饰器

    Args:
        logger: 日志记录器
        level: 日志级别
    """
    def decorator(func: Callable) -> Any:
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                if logger:
                    logger.log(
                        level,
                        f"{func.__name__} executed in {execution_time:.3f}s",
                        extra={"extra_fields": {
                            "function": func.__name__,
                            "execution_time": execution_time,
                            "status": "success"
                        }}
                    )

                return result
            except Exception as e:
                execution_time = time.time() - start_time

                if logger:
                    logger.error(
                        f"{func.__name__} failed after {execution_time:.3f}s: {e}",
                        extra={"extra_fields": {
                            "function": func.__name__,
                            "execution_time": execution_time,
                            "status": "error",
                            "error": str(e),
                            "traceback": traceback.format_exc()
                        }}
                    )

                raise

        return wrapper
    return decorator


# =============================================================================
# 请求上下文日志
# =============================================================================

class RequestContextLogger:
    """请求上下文日志记录器"""

    def __init__(self, base_logger: StructuredLogger):
        self.base_logger = base_logger

    @contextmanager
    def request_context(self, request_id: str, **context_fields) -> Any:
        """
        请求上下文管理器

        Args:
            request_id: 请求ID
            **context_fields: 上下文字段
        """
        request_logger = self.base_logger.with_fields(
            request_id=request_id,
            **context_fields
        )

        start_time = time.time()

        try:
            request_logger.info("Request started")
            yield request_logger

            execution_time = time.time() - start_time
            request_logger.info(
                "Request completed",
                status="success",
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            request_logger.error(
                f"Request failed: {e}",
                status="error",
                execution_time=execution_time,
                error_type=type(e).__name__
            )
            raise


# =============================================================================
# 日志工厂
# =============================================================================

class LoggerFactory:
    """日志工厂"""

    _instances: dict[str, StructuredLogger] = {}
    _config: LogConfig | None = None

    @classmethod
    def set_config(cls, config: LogConfig) -> None:
        """设置全局日志配置"""
        cls._config = config

    @classmethod
    def get_logger(
        cls,
        name: str,
        config: LogConfig | None = None,
        service_name: str = "xiaonuo",
        service_version: str = "5.0.0"
    ) -> StructuredLogger:
        """
        获取日志记录器实例

        Args:
            name: 日志记录器名称
            config: 日志配置（可选，使用全局配置）
            service_name: 服务名称
            service_version: 服务版本

        Returns:
            结构化日志记录器
        """
        if name not in cls._instances:
            log_config = config or cls._config
            cls._instances[name] = StructuredLogger(
                name=name,
                config=log_config,
                service_name=service_name,
                service_version=service_version
            )
        return cls._instances[name]


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "JSONFormatter",
    "StructuredLogger",
    "LoggerAdapter",
    "RequestContextLogger",
    "LoggerFactory",
    "log_execution_time",
]
