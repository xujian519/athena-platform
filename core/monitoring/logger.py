"""
统一日志记录器

> 版本: v1.0
> 更新: 2026-04-21
> 说明: 统一的日志记录系统，支持结构化日志和上下文追踪
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextlib import contextmanager
from threading import local


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        
        # 基础日志数据
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加上下文信息
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # 添加扩展信息
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra
        
        return json.dumps(log_data, ensure_ascii=False)


class UnifiedLogger:
    """统一日志记录器"""
    
    def __init__(self, name: str):
        """
        初始化日志记录器
        
        参数:
            name: 日志记录器名称
        """
        self._logger = logging.getLogger(name)
        self._context = local()
    
    def _add_context(self, **context) -> logging.LogRecord:
        """添加上下文到日志记录"""
        # 创建日志记录的额外参数
        extra = {}
        current_context = getattr(self._context, "data", {}).copy()
        current_context.update(context)
        if current_context:
            extra["context"] = current_context
        if context:
            extra["extra"] = context
        return extra
    
    def debug(self, message: str, **context) -> None:
        """记录DEBUG级别日志"""
        self._logger.debug(message, extra=self._add_context(**context))
    
    def info(self, message: str, **context) -> None:
        """记录INFO级别日志"""
        self._logger.info(message, extra=self._add_context(**context))
    
    def warning(self, message: str, **context) -> None:
        """记录WARNING级别日志"""
        self._logger.warning(message, extra=self._add_context(**context))
    
    def error(self, message: str, **context) -> None:
        """记录ERROR级别日志"""
        self._logger.error(message, extra=self._add_context(**context))
    
    def critical(self, message: str, **context) -> None:
        """记录CRITICAL级别日志"""
        self._logger.critical(message, extra=self._add_context(**context))
    
    def exception(self, message: str, **context) -> None:
        """记录异常日志"""
        self._logger.exception(message, extra=self._add_context(**context))


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self):
        """初始化日志上下文"""
        self._local = local()
        self._local.data = {}
    
    def bind(self, **context) -> None:
        """绑定上下文"""
        self._local.data.update(context)
    
    def clear(self) -> None:
        """清除上下文"""
        self._local.data = {}
    
    def get_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        return getattr(self._local, "data", {}).copy()


# 全局日志上下文
_log_context = LogContext()


def get_logger(name: str) -> UnifiedLogger:
    """
    获取日志记录器
    
    参数:
        name: 日志记录器名称
        
    返回:
        日志记录器实例
    """
    return UnifiedLogger(name)


@contextmanager
def bind_context(**context):
    """
    绑定日志上下文
    
    参数:
        **context: 上下文信息
        
    示例:
        ```python
        with bind_context(agent_id="xiaona-001", task_id="task-123"):
            logger.info("开始执行任务")
            # 上下文会自动添加到日志
        ```
    """
    old_context = _log_context.get_context()
    _log_context.bind(**context)
    try:
        yield
    finally:
        _log_context.clear()
        _log_context.bind(**old_context)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True
) -> None:
    """
    配置日志系统
    
    参数:
        level: 日志级别
        log_file: 日志文件路径（可选）
        json_format: 是否使用JSON格式
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # 添加文件处理器（如果指定）
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)


__all__ = [
    "UnifiedLogger",
    "get_logger",
    "bind_context",
    "setup_logging",
]
