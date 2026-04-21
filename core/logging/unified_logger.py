"""
统一日志记录器
Unified Logger for Athena Platform
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

try:
    import pythonjsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


class LogLevel(Enum):
    """日志级别"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class ContextFilter(logging.Filter):
    """上下文过滤器 - 自动添加上下文信息"""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.context: Dict[str, Any] = {}

    def add_context(self, key: str, value: Any):
        """添加上下文"""
        self.context[key] = value

    def clear_context(self):
        """清除上下文"""
        self.context.clear()

    def get_context(self) -> Dict[str, Any]:
        """获取所有上下文"""
        return self.context.copy()

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录，添加上下文"""
        # 添加服务名
        record.service_name = self.service_name

        # 添加时间戳（ISO格式）
        record.timestamp = datetime.utcnow().isoformat() + "Z"

        # 添加上下文信息
        for key, value in self.context.items():
            setattr(record, key, value)

        return True


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        import json

        log_data = {
            "timestamp": getattr(record, 'timestamp', datetime.utcnow().isoformat() + "Z"),
            "level": record.levelname,
            "service": self.service_name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "context": self._extract_context(record),
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self._format_exception(record.exc_info)

        # 添加额外字段
        if hasattr(record, 'extra'):
            log_data["extra"] = record.extra

        return json.dumps(log_data, ensure_ascii=False)

    def _extract_context(self, record: logging.LogRecord) -> Dict[str, Any]:
        """提取上下文信息"""
        context = {}

        # 常见上下文字段
        context_fields = [
            'request_id', 'user_id', 'correlation_id',
            'task_id', 'session_id', 'trace_id'
        ]

        for field in context_fields:
            if hasattr(record, field):
                context[field] = getattr(record, field)

        return context

    def _format_exception(self, exc_info) -> Dict[str, str]:
        """格式化异常信息"""
        import traceback

        return {
            "type": exc_info[0].__name__ if exc_info[0] else None,
            "message": str(exc_info[1]) if exc_info[1] else None,
            "traceback": traceback.format_exception(*exc_info)
        }


class TextFormatter(logging.Formatter):
    """文本格式化器（用于控制台输出）"""

    def __init__(self):
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        super().__init__(fmt, datefmt='%Y-%m-%d %H:%M:%S')


class UnifiedLogger:
    """统一日志记录器"""

    _instances: Dict[str, 'UnifiedLogger'] = {}

    def __init__(
        self,
        service_name: str,
        level: LogLevel = LogLevel.INFO
    ):
        """初始化统一日志记录器

        Args:
            service_name: 服务名称
            level: 日志级别
        """
        self.service_name = service_name
        self.level = level

        # 创建logger
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(level.value)

        # 如果已经配置过，不再重复配置
        if not self.logger.handlers:
            self._setup_logger()

        # 上下文过滤器
        self.context_filter = None
        for handler in self.logger.handlers:
            for filter in handler.filters:
                if isinstance(filter, ContextFilter):
                    self.context_filter = filter
                    break

    def _setup_logger(self):
        """配置日志记录器"""
        # 清除现有处理器
        self.logger.handlers.clear()

        # 添加上下文过滤器
        context_filter = ContextFilter(self.service_name)

        # 控制台处理器（开发环境）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level.value)
        console_handler.setFormatter(TextFormatter())
        console_handler.addFilter(context_filter)
        self.logger.addHandler(console_handler)

        # 避免传播到父logger
        self.logger.propagate = False

    @classmethod
    def get_instance(cls, service_name: str, level: LogLevel = LogLevel.INFO) -> 'UnifiedLogger':
        """获取日志记录器实例（单例模式）

        Args:
            service_name: 服务名称
            level: 日志级别

        Returns:
            UnifiedLogger实例
        """
        if service_name not in cls._instances:
            cls._instances[service_name] = cls(service_name, level)
        return cls._instances[service_name]

    def set_level(self, level: LogLevel):
        """设置日志级别

        Args:
            level: 日志级别
        """
        self.level = level
        self.logger.setLevel(level.value)
        for handler in self.logger.handlers:
            handler.setLevel(level.value)

    def add_context(self, key: str, value: Any):
        """添加上下文信息

        Args:
            key: 键
            value: 值
        """
        if self.context_filter:
            self.context_filter.add_context(key, value)

    def clear_context(self):
        """清除上下文信息"""
        if self.context_filter:
            self.context_filter.clear_context()

    def _log(self, level: LogLevel, message: str, **kwargs):
        """记录日志

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外字段
        """
        extra = kwargs.pop('extra', None)
        exc_info = kwargs.pop('exc_info', None)

        # 添加额外字段
        if extra or kwargs:
            record = self.logger.makeRecord(
                self.logger.name,
                level.value,
                fn=self._log.__code__.co_firstlineno,
                lno=0,
                msg=message,
                args=(),
                exc_info=exc_info
            )
            if extra:
                record.extra = extra
            if kwargs:
                if not hasattr(record, 'extra'):
                    record.extra = {}
                record.extra.update(kwargs)
            self.logger.handle(record)
        else:
            self.logger.log(level.value, message, exc_info=exc_info)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """记录ERROR级别日志

        Args:
            message: 日志消息
            exception: 异常对象
            **kwargs: 额外字段
        """
        exc_info = (type(exception), exception, exception.__traceback__) if exception else None
        self._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """记录CRITICAL级别日志

        Args:
            message: 日志消息
            exception: 异常对象
            **kwargs: 额外字段
        """
        exc_info = (type(exception), exception, exception.__traceback__) if exception else None
        self._log(LogLevel.CRITICAL, message, exc_info=exc_info, **kwargs)

    def exception(self, message: str, **kwargs):
        """记录异常（ERROR级别）

        Args:
            message: 日志消息
            **kwargs: 额外字段
        """
        import sys
        self.error(message, exc_info=sys.exc_info(), **kwargs)


# 便捷函数
def get_logger(service_name: str, level: LogLevel = LogLevel.INFO) -> UnifiedLogger:
    """获取日志记录器

    Args:
        service_name: 服务名称
        level: 日志级别

    Returns:
        UnifiedLogger实例
    """
    return UnifiedLogger.get_instance(service_name, level)
