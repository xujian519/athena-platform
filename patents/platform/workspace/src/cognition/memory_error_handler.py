#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统错误处理器
Memory System Error Handler

提供统一的异常定义、错误处理机制和日志记录功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import functools
import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, Union

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class MemorySystemError(Exception):
    """记忆系统基础异常"""

    def __init__(self, message: str, error_code: str = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.timestamp = datetime.now()
        self.traceback_str = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'traceback': self.traceback_str
        }

class MemoryStorageError(MemorySystemError):
    """存储异常"""

    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message, error_code or 'STORAGE_ERROR', ErrorSeverity.HIGH)
        self.details = details or {}

class MemoryRetrievalError(MemorySystemError):
    """检索异常"""

    def __init__(self, message: str, error_code: str = None, query: str = None):
        super().__init__(message, error_code or 'RETRIEVAL_ERROR', ErrorSeverity.MEDIUM)
        self.query = query

class MemoryInitializationError(MemorySystemError):
    """初始化异常"""

    def __init__(self, message: str, component: str = None):
        super().__init__(message, 'INITIALIZATION_ERROR', ErrorSeverity.CRITICAL)
        self.component = component

class MemoryConfigurationError(MemorySystemError):
    """配置异常"""

    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, 'CONFIGURATION_ERROR', ErrorSeverity.HIGH)
        self.config_key = config_key

class MemoryIndexError(MemorySystemError):
    """索引异常"""

    def __init__(self, message: str, index_type: str = None):
        super().__init__(message, 'INDEX_ERROR', ErrorSeverity.MEDIUM)
        self.index_type = index_type

class MemoryVectorError(MemorySystemError):
    """向量操作异常"""

    def __init__(self, message: str, operation: str = None, vector_size: int = None):
        super().__init__(message, 'VECTOR_ERROR', ErrorSeverity.MEDIUM)
        self.operation = operation
        self.vector_size = vector_size

class MemoryConcurrentError(MemorySystemError):
    """并发操作异常"""

    def __init__(self, message: str, operation: str = None):
        super().__init__(message, 'CONCURRENT_ERROR', ErrorSeverity.MEDIUM)
        self.operation = operation

class ErrorHandler:
    """错误处理器"""

    def __init__(self, logger_name: str = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_stats: Dict[str, int] = {}
        self.error_history: list = []

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> MemorySystemError:
        """处理错误"""
        # 统计错误
        error_type = type(error).__name__
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1

        # 转换为记忆系统错误
        if isinstance(error, MemorySystemError):
            memory_error = error
        else:
            memory_error = MemorySystemError(
                message=str(error),
                error_code=f"UNHANDLED_{error_type.upper()}",
                severity=ErrorSeverity.HIGH
            )

        # 添加上下文信息
        if context:
            memory_error.context = context

        # 记录错误
        self._log_error(memory_error)

        # 保存错误历史
        self.error_history.append(memory_error.to_dict())

        # 限制历史记录大小
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]

        return memory_error

    def _log_error(self, error: MemorySystemError):
        """记录错误"""
        error_dict = error.to_dict()

        # 根据严重程度选择日志级别
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"🚨 {error.message}: {extra=error_dict}")
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"❌ {error.message}: {extra=error_dict}")
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"⚠️ {error.message}: {extra=error_dict}")
        else:
            self.logger.info(f"ℹ️ {error.message}: {extra=error_dict}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            'total_errors': sum(self.error_stats.values()),
            'error_types': self.error_stats.copy(),
            'recent_errors': len(self.error_history),
            'last_24h_errors': len([
                e for e in self.error_history
                if (datetime.now() - datetime.fromisoformat(e['timestamp'])).total_seconds() < 86400
            ])
        }

# 全局错误处理器实例
_global_error_handler: ErrorHandler | None = None

def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler

def handle_memory_error(func: Callable) -> Callable:
    """记忆系统错误处理装饰器"""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MemorySystemError:
            # 重新抛出记忆系统错误
            raise
        except Exception as e:
            error_handler = get_error_handler()
            context = {
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            raise error_handler.handle_error(e, context) from e

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MemorySystemError:
            # 重新抛出记忆系统错误
            raise
        except Exception as e:
            error_handler = get_error_handler()
            context = {
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            raise error_handler.handle_error(e, context) from e

    # 判断是否是异步函数
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def safe_execute(func: Callable, default_value: Any = None,
                raise_on_error: bool = False) -> Callable:
    """安全执行装饰器，出错时返回默认值"""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_handler = get_error_handler()
            error_handler.handle_error(e, {
                'function': func.__name__,
                'safe_mode': True,
                'default_value': default_value
            })

            if raise_on_error:
                raise
            else:
                return default_value

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = get_error_handler()
            error_handler.handle_error(e, {
                'function': func.__name__,
                'safe_mode': True,
                'default_value': default_value
            })

            if raise_on_error:
                raise
            else:
                return default_value

    # 判断是否是异步函数
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def retry_on_error(max_retries: int = 3, delay: float = 1.0,
                  backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """错误重试装饰器"""

    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    error_handler = get_error_handler()

                    if attempt < max_retries:
                        error_handler.logger.warning(
                            f"🔄 重试 {func.__name__} (第{attempt + 1}次): {e}"
                        )
                    else:
                        error_handler.handle_error(e, {
                            'function': func.__name__,
                            'retry_attempts': max_retries,
                            'final_attempt': True
                        })

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        time.sleep(current_delay)
                        current_delay *= backoff

                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    error_handler = get_error_handler()

                    if attempt < max_retries:
                        error_handler.logger.warning(
                            f"🔄 重试 {func.__name__} (第{attempt + 1}次): {e}"
                        )
                    else:
                        error_handler.handle_error(e, {
                            'function': func.__name__,
                            'retry_attempts': max_retries,
                            'final_attempt': True
                        })

            raise last_exception

        # 判断是否是异步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

class MemorySystemLogger:
    """记忆系统专用日志器"""

    def __init__(self, name: str = 'memory_system'):
        self.logger = logging.getLogger(name)
        self.setup_logger()

    def setup_logger(self):
        """设置日志器"""
        # 添加自定义过滤器
        self.logger.addFilter(MemoryLogFilter())

    def log_operation(self, operation: str, duration: float = None,
                     details: Dict[str, Any] = None):
        """记录操作日志"""
        message = f"📝 操作: {operation}"
        if duration is not None:
            message += f" (耗时: {duration:.3f}s)"

        extra = {'operation': operation, 'duration': duration}
        if details:
            extra.update(details)

        self.logger.info(message, extra=extra)

    def log_performance(self, metric: str, value: float, unit: str = '',
                       details: Dict[str, Any] = None):
        """记录性能日志"""
        message = f"📊 性能指标: {metric} = {value}"
        if unit:
            message += f" {unit}"

        extra = {'metric': metric, 'value': value, 'unit': unit}
        if details:
            extra.update(details)

        self.logger.info(message, extra=extra)

    def log_memory_usage(self, component: str, memory_usage: float,
                         details: Dict[str, Any] = None):
        """记录内存使用日志"""
        message = f"💾 内存使用 [{component}]: {memory_usage:.2f} MB"

        extra = {'component': component, 'memory_usage': memory_usage}
        if details:
            extra.update(details)

        self.logger.info(message, extra=extra)

class MemoryLogFilter(logging.Filter):
    """记忆系统日志过滤器"""

    def filter(self, record):
        # 添加时间戳和调用栈信息
        record.timestamp = datetime.now().isoformat()

        # 添加性能相关信息
        if hasattr(record, 'duration') and record.duration:
            record.performance_level = self._get_performance_level(record.duration)

        return True

    def _get_performance_level(self, duration: float) -> str:
        """获取性能等级"""
        if duration < 0.1:
            return 'fast'
        elif duration < 1.0:
            return 'normal'
        elif duration < 5.0:
            return 'slow'
        else:
            return 'very_slow'

# 便捷函数
def get_logger(name: str = None) -> MemorySystemLogger:
    """获取记忆系统日志器"""
    return MemorySystemLogger(name)

def log_memory_operation(operation: str):
    """记录记忆操作的装饰器"""
    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = get_logger(func.__module__)

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()

                logger.log_operation(operation, duration, {
                    'success': True,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })

                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()

                logger.log_operation(f"{operation} (失败)", duration, {
                    'success': False,
                    'error': str(e)
                })

                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = get_logger(func.__module__)

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()

                logger.log_operation(operation, duration, {
                    'success': True,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })

                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()

                logger.log_operation(f"{operation} (失败)", duration, {
                    'success': False,
                    'error': str(e)
                })

                raise

        # 判断是否是异步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator