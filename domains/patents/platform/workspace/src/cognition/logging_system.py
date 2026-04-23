#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认知系统统一日志管理
Cognitive System Unified Logging

提供统一的日志格式、错误处理和性能监控功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import gzip
import hashlib
import json
import logging
import sys
import threading
import traceback
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """日志级别"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class LogCategory(Enum):
    """日志分类"""
    SYSTEM = 'system'                 # 系统日志
    PERFORMANCE = 'performance'       # 性能日志
    SECURITY = 'security'            # 安全日志
    BUSINESS = 'business'            # 业务日志
    AUDIT = 'audit'                  # 审计日志
    DEBUG = 'debug'                  # 调试日志
    ERROR = 'error'                  # 错误日志

class ErrorType(Enum):
    """错误类型"""
    SYSTEM_ERROR = 'system_error'           # 系统错误
    BUSINESS_ERROR = 'business_error'       # 业务错误
    VALIDATION_ERROR = 'validation_error'   # 验证错误
    NETWORK_ERROR = 'network_error'         # 网络错误
    DATABASE_ERROR = 'database_error'       # 数据库错误
    MEMORY_ERROR = 'memory_error'           # 内存错误
    TIMEOUT_ERROR = 'timeout_error'         # 超时错误
    UNKNOWN_ERROR = 'unknown_error'         # 未知错误

@dataclass
class LogEntry:
    """日志条目"""
    log_id: str
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    component: str
    message: str
    details: Optional[Dict[str, Any] = None
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None
    stack_trace: str | None = None
    performance_metrics: Optional[Dict[str, float] = None
    tags: List[str] = field(default_factory=list)
    correlation_id: str | None = None

@dataclass
class ErrorReport:
    """错误报告"""
    error_id: str
    timestamp: datetime
    error_type: ErrorType
    error_code: Optional[str]
    message: str
    details: Dict[str, Any]
    stack_trace: str
    context: Dict[str, Any]
    severity: str
    recovery_action: str | None = None
    resolved: bool = False
    resolution_time: datetime | None = None

class LogFormatter(logging.Formatter):
    """自定义日志格式化器"""

    def __init__(self, include_details: bool = True):
        super().__init__()
        self.include_details = include_details

    def format(self, record: logging.LogRecord) -> str:
        # 创建基础日志字典
        log_dict = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # 添加额外信息
        if hasattr(record, 'category'):
            log_dict['category'] = record.category
        if hasattr(record, 'component'):
            log_dict['component'] = record.component
        if hasattr(record, 'user_id'):
            log_dict['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_dict['session_id'] = record.session_id
        if hasattr(record, 'request_id'):
            log_dict['request_id'] = record.request_id
        if hasattr(record, 'correlation_id'):
            log_dict['correlation_id'] = record.correlation_id
        if hasattr(record, 'tags'):
            log_dict['tags'] = record.tags

        # 添加详细信息
        if self.include_details and hasattr(record, 'details'):
            log_dict['details'] = record.details

        # 添加性能指标
        if hasattr(record, 'performance_metrics'):
            log_dict['performance_metrics'] = record.performance_metrics

        # 异常信息
        if record.exc_info:
            log_dict['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_dict, ensure_ascii=False, separators=(',', ':'))

class CognitiveLogHandler:
    """认知系统日志处理器"""

    def __init__(self, log_dir: str = 'logs', max_file_size: int = 100 * 1024 * 1024):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size

        # 日志文件配置
        self.log_files = {
            LogCategory.SYSTEM: self.log_dir / 'system.log',
            LogCategory.PERFORMANCE: self.log_dir / 'performance.log',
            LogCategory.SECURITY: self.log_dir / 'security.log',
            LogCategory.BUSINESS: self.log_dir / 'business.log',
            LogCategory.AUDIT: self.log_dir / 'audit.log',
            LogCategory.DEBUG: self.log_dir / 'debug.log',
            LogCategory.ERROR: self.log_dir / 'error.log'
        }

        # 日志缓冲区
        self.log_buffers: Dict[LogCategory, deque] = {
            category: deque(maxlen=10000) for category in LogCategory
        }

        # 压缩的旧日志
        self.archive_dir = self.log_dir / 'archive'
        self.archive_dir.mkdir(exist_ok=True)

        # 异步写入队列
        self.write_queue = asyncio.Queue()
        self.writer_task: asyncio.Task | None = None

        # 性能指标
        self.metrics = {
            'total_logs': 0,
            'logs_per_category': defaultdict(int),
            'average_write_time': 0.0,
            'write_errors': 0
        }

    async def start(self):
        """启动日志处理器"""
        self.writer_task = asyncio.create_task(self._write_loop())
        logger.info('🚀 认知系统日志处理器已启动')

    async def stop(self):
        """停止日志处理器"""
        if self.writer_task:
            # 处理剩余的日志
            await self._flush_queue()
            self.writer_task.cancel()
            try:
                await self.writer_task
            except asyncio.CancelledError:
                pass
        logger.info('🛑 认知系统日志处理器已停止')

    async def write_log(self, entry: LogEntry):
        """写入日志条目"""
        try:
            # 添加到缓冲区
            self.log_buffers[entry.category].append(entry)

            # 添加到异步写入队列
            await self.write_queue.put(entry)

            # 更新指标
            self.metrics['total_logs'] += 1
            self.metrics['logs_per_category'][entry.category.value] += 1

        except Exception as e:
            logger.error(f"❌ 写入日志失败: {e}")
            self.metrics['write_errors'] += 1

    async def _write_loop(self):
        """异步写入循环"""
        while True:
            try:
                entry = await asyncio.wait_for(self.write_queue.get(), timeout=0.1)
                await self._write_to_file(entry)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ 日志写入循环错误: {e}")

    async def _write_to_file(self, entry: LogEntry):
        """写入到文件"""
        start_time = datetime.now()

        try:
            log_file = self.log_files[entry.category]

            # 检查文件大小
            if log_file.exists() and log_file.stat().st_size > self.max_file_size:
                await self._rotate_log_file(entry.category)

            # 写入日志
            log_line = json.dumps({
                'log_id': entry.log_id,
                'timestamp': entry.timestamp.isoformat(),
                'level': entry.level.name,
                'category': entry.category.value,
                'component': entry.component,
                'message': entry.message,
                'details': entry.details,
                'user_id': entry.user_id,
                'session_id': entry.session_id,
                'request_id': entry.request_id,
                'correlation_id': entry.correlation_id,
                'tags': entry.tags,
                'performance_metrics': entry.performance_metrics,
                'stack_trace': entry.stack_trace
            }, ensure_ascii=False)

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')

            # 更新写入时间指标
            write_time = (datetime.now() - start_time).total_seconds()
            total_logs = self.metrics['total_logs']
            if total_logs > 0:
                current_avg = self.metrics['average_write_time']
                self.metrics['average_write_time'] = (
                    (current_avg * (total_logs - 1) + write_time) / total_logs
                )

        except Exception as e:
            logger.error(f"❌ 写入日志文件失败: {e}")
            self.metrics['write_errors'] += 1

    async def _rotate_log_file(self, category: LogCategory):
        """轮转日志文件"""
        log_file = self.log_files[category]

        # 生成归档文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_file = self.archive_dir / f"{category.value}_{timestamp}.log.gz"

        # 压缩并移动旧文件
        with open(log_file, 'rb') as f_in:
            with gzip.open(archive_file, 'wb') as f_out:
                f_out.writelines(f_in)

        # 清空当前文件
        log_file.unlink()

        logger.info(f"📦 日志文件已轮转: {category.value} -> {archive_file}")

    async def _flush_queue(self):
        """刷新队列"""
        while not self.write_queue.empty():
            entry = await self.write_queue.get()
            await self._write_to_file(entry)

    def get_logs(self,
                 category: LogCategory | None = None,
                 level: LogLevel | None = None,
                 start_time: datetime | None = None,
                 end_time: datetime | None = None,
                 limit: int = 100) -> List[LogEntry]:
        """获取日志"""
        results = []

        # 确定要搜索的缓冲区
        categories = [category] if category else list(LogCategory)

        for cat in categories:
            buffer = self.log_buffers[cat]
            for entry in reversed(buffer):
                # 过滤条件
                if level and entry.level != level:
                    continue
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue

                results.append(entry)
                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'total_logs': self.metrics['total_logs'],
            'logs_per_category': dict(self.metrics['logs_per_category']),
            'average_write_time': self.metrics['average_write_time'],
            'write_errors': self.metrics['write_errors'],
            'buffer_sizes': {
                category.value: len(buffer)
                for category, buffer in self.log_buffers.items()
            }
        }

class ErrorManager:
    """错误管理器"""

    def __init__(self):
        self.error_reports: Dict[str, ErrorReport] = {}
        self.error_handlers: Dict[ErrorType, List[Callable] = defaultdict(list)
        self.error_patterns: Dict[str, ErrorType] = {}
        self.metrics = {
            'total_errors': 0,
            'errors_by_type': defaultdict(int),
            'resolved_errors': 0,
            'average_resolution_time': 0.0
        }

    def register_error_handler(self, error_type: ErrorType, handler: Callable):
        """注册错误处理器"""
        self.error_handlers[error_type].append(handler)
        logger.info(f"📝 已注册错误处理器: {error_type.value}")

    def register_error_pattern(self, pattern: str, error_type: ErrorType):
        """注册错误模式"""
        self.error_patterns[pattern] = error_type
        logger.debug(f"🔍 已注册错误模式: {pattern} -> {error_type.value}")

    async def handle_error(self,
                          exception: Exception,
                          context: Optional[Dict[str, Any] = None,
                          user_id: str | None = None,
                          session_id: str | None = None) -> str:
        """处理错误"""
        error_id = str(uuid.uuid4())
        context = context or {}

        # 确定错误类型
        error_type = self._classify_error(exception)

        # 创建错误报告
        error_report = ErrorReport(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=error_type,
            error_code=getattr(exception, 'code', None),
            message=str(exception),
            details={
                'exception_type': type(exception).__name__,
                'module': getattr(exception, '__module__', 'unknown'),
                'args': getattr(exception, 'args', [])
            },
            stack_trace=traceback.format_exc(),
            context=context,
            severity=self._determine_severity(error_type, exception)
        )

        # 添加用户和会话信息
        if user_id:
            error_report.context['user_id'] = user_id
        if session_id:
            error_report.context['session_id'] = session_id

        # 存储错误报告
        self.error_reports[error_id] = error_report

        # 更新指标
        self.metrics['total_errors'] += 1
        self.metrics['errors_by_type'][error_type.value] += 1

        # 执行错误处理器
        await self._execute_error_handlers(error_type, error_report)

        logger.error(f"❌ 错误已处理 [{error_type.value}]: {error_id} - {str(exception)}")
        return error_id

    def _classify_error(self, exception: Exception) -> ErrorType:
        """分类错误"""
        exception_type = type(exception).__name__
        exception_message = str(exception).lower()

        # 检查错误模式
        for pattern, error_type in self.error_patterns.items():
            if pattern.lower() in exception_message:
                return error_type

        # 基于异常类型分类
        type_mapping = {
            'MemoryError': ErrorType.MEMORY_ERROR,
            'TimeoutError': ErrorType.TIMEOUT_ERROR,
            'ConnectionError': ErrorType.NETWORK_ERROR,
            'DatabaseError': ErrorType.DATABASE_ERROR,
            'ValidationError': ErrorType.VALIDATION_ERROR,
            'ValueError': ErrorType.BUSINESS_ERROR,
            'KeyError': ErrorType.BUSINESS_ERROR,
            'IndexError': ErrorType.BUSINESS_ERROR
        }

        return type_mapping.get(exception_type, ErrorType.UNKNOWN_ERROR)

    def _determine_severity(self, error_type: ErrorType, exception: Exception) -> str:
        """确定错误严重程度"""
        severity_mapping = {
            ErrorType.MEMORY_ERROR: 'critical',
            ErrorType.DATABASE_ERROR: 'high',
            ErrorType.NETWORK_ERROR: 'medium',
            ErrorType.TIMEOUT_ERROR: 'medium',
            ErrorType.BUSINESS_ERROR: 'low',
            ErrorType.VALIDATION_ERROR: 'low',
            ErrorType.SYSTEM_ERROR: 'high',
            ErrorType.UNKNOWN_ERROR: 'medium'
        }

        return severity_mapping.get(error_type, 'medium')

    async def _execute_error_handlers(self, error_type: ErrorType, error_report: ErrorReport):
        """执行错误处理器"""
        handlers = self.error_handlers.get(error_type, [])
        if not handlers:
            handlers = self.error_handlers.get(ErrorType.UNKNOWN_ERROR, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error_report)
                else:
                    handler(error_report)
            except Exception as e:
                logger.error(f"❌ 错误处理器执行失败: {e}")

    async def resolve_error(self, error_id: str, resolution_action: str) -> bool:
        """解决错误"""
        if error_id not in self.error_reports:
            logger.warning(f"⚠️ 错误报告不存在: {error_id}")
            return False

        error_report = self.error_reports[error_id]
        error_report.resolved = True
        error_report.resolution_time = datetime.now()
        error_report.recovery_action = resolution_action

        # 更新指标
        self.metrics['resolved_errors'] += 1

        # 计算平均解决时间
        total_resolved = self.metrics['resolved_errors']
        if total_resolved > 0:
            resolution_times = []
            for report in self.error_reports.values():
                if report.resolved and report.resolution_time:
                    resolution_time = (report.resolution_time - report.timestamp).total_seconds()
                    resolution_times.append(resolution_time)

            if resolution_times:
                self.metrics['average_resolution_time'] = sum(resolution_times) / len(resolution_times)

        logger.info(f"✅ 错误已解决: {error_id}")
        return True

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        unresolved_count = sum(
            1 for report in self.error_reports.values()
            if not report.resolved
        )

        resolution_rate = (
            self.metrics['resolved_errors'] / max(self.metrics['total_errors'], 1) * 100
        )

        return {
            'total_errors': self.metrics['total_errors'],
            'unresolved_errors': unresolved_count,
            'resolved_errors': self.metrics['resolved_errors'],
            'resolution_rate': f"{resolution_rate:.1f}%",
            'errors_by_type': dict(self.metrics['errors_by_type']),
            'average_resolution_time': self.metrics['average_resolution_time'],
            'recent_errors': [
                {
                    'error_id': report.error_id,
                    'type': report.error_type.value,
                    'message': report.message,
                    'timestamp': report.timestamp.isoformat(),
                    'resolved': report.resolved
                }
                for report in sorted(
                    self.error_reports.values(),
                    key=lambda x: x.timestamp,
                    reverse=True
                )[:10]
            ]
        }

class CognitiveLogger:
    """认知系统统一日志管理器"""

    def __init__(self, component_name: str, log_dir: str = 'logs'):
        self.component_name = component_name
        self.log_handler = CognitiveLogHandler(log_dir)
        self.error_manager = ErrorManager()

        # 创建标准日志记录器
        self.logger = logging.getLogger(component_name)
        self.logger.setLevel(logging.DEBUG)

        # 添加自定义处理器
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(LogFormatter())
        self.logger.addHandler(self.handler)

        # 上下文信息
        self.context = {
            'component': component_name,
            'session_id': str(uuid.uuid4())
        }

        # 性能监控
        self.performance_timers: Dict[str, datetime] = {}

    async def start(self):
        """启动日志管理器"""
        await self.log_handler.start()
        self.info('日志管理器已启动', category=LogCategory.SYSTEM)

    async def stop(self):
        """停止日志管理器"""
        self.info('日志管理器已停止', category=LogCategory.SYSTEM)
        await self.log_handler.stop()

    def set_context(self, **kwargs):
        """设置上下文信息"""
        self.context.update(kwargs)

    def log(self,
            level: LogLevel,
            message: str,
            category: LogCategory = LogCategory.SYSTEM,
            details: Optional[Dict[str, Any] = None,
            tags: Optional[List[str] = None,
            performance_metrics: Optional[Dict[str, float] = None):
        """记录日志"""
        log_entry = LogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level=level,
            category=category,
            component=self.component_name,
            message=message,
            details=details,
            tags=tags or [],
            performance_metrics=performance_metrics,
            **self.context
        )

        # 异步写入
        asyncio.create_task(self.log_handler.write_log(log_entry))

        # 同时输出到标准日志
        log_level = getattr(logging, level.name)
        extra = {
            'category': category.value,
            'component': self.component_name,
            'details': details,
            'tags': tags or [],
            'performance_metrics': performance_metrics
        }
        extra.update(self.context)

        self.logger.log(log_level, message, extra=extra)

    def trace(self, message: str, **kwargs):
        """跟踪日志"""
        self.log(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """调试日志"""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """信息日志"""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """警告日志"""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """错误日志"""
        self.log(LogLevel.ERROR, message, category=LogCategory.ERROR, **kwargs)

    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self.log(LogLevel.CRITICAL, message, category=LogCategory.ERROR, **kwargs)

    async def handle_error(self, exception: Exception, context: Optional[Dict[str, Any] = None) -> str:
        """处理错误"""
        context = context or {}
        context.update(self.context)

        # 记录错误日志
        self.error(
            f"异常处理: {type(exception).__name__}: {str(exception)}",
            details={
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'context': context
            },
            category=LogCategory.ERROR
        )

        # 使用错误管理器处理
        return await self.error_manager.handle_error(
            exception,
            context=context,
            user_id=self.context.get('user_id'),
            session_id=self.context.get('session_id')
        )

    def start_timer(self, timer_name: str):
        """开始计时"""
        self.performance_timers[timer_name] = datetime.now()

    def end_timer(self, timer_name: str) -> float:
        """结束计时并返回耗时"""
        if timer_name in self.performance_timers:
            duration = (datetime.now() - self.performance_timers[timer_name]).total_seconds()
            del self.performance_timers[timer_name]

            # 记录性能日志
            self.info(
                f"性能计时 [{timer_name}]: {duration:.3f}秒",
                category=LogCategory.PERFORMANCE,
                performance_metrics={f"{timer_name}_duration": duration}
            )

            return duration
        return 0.0

    def log_business_event(self, event_name: str, **details):
        """记录业务事件"""
        self.info(
            f"业务事件: {event_name}",
            category=LogCategory.BUSINESS,
            details={'event_name': event_name, **details}
        )

    def log_audit_event(self, action: str, resource: str, **details):
        """记录审计事件"""
        self.info(
            f"审计事件: {action} on {resource}",
            category=LogCategory.AUDIT,
            details={'action': action, 'resource': resource, **details}
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'log_metrics': self.log_handler.get_metrics(),
            'error_statistics': self.error_manager.get_error_statistics(),
            'active_timers': list(self.performance_timers.keys())
        }

# 全局日志管理器实例
_loggers: Dict[str, CognitiveLogger] = {}

def get_logger(component_name: str, log_dir: str = 'logs') -> CognitiveLogger:
    """获取日志管理器实例"""
    if component_name not in _loggers:
        _loggers[component_name] = CognitiveLogger(component_name, log_dir)
    return _loggers[component_name]

# 便捷的装饰器
def log_performance(logger_name: str = None):
    """性能日志装饰器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger_instance = get_logger(logger_name or func.__module__)
            timer_name = f"{func.__name__}_execution"

            logger_instance.start_timer(timer_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                logger_instance.end_timer(timer_name)

        def sync_wrapper(*args, **kwargs):
            logger_instance = get_logger(logger_name or func.__module__)
            timer_name = f"{func.__name__}_execution"

            logger_instance.start_timer(timer_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                logger_instance.end_timer(timer_name)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def log_errors(logger_name: str = None):
    """错误日志装饰器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger_instance = get_logger(logger_name or func.__module__)
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await logger_instance.handle_error(e, {
                    'function': func.__name__,
                    'args': str(args)[:100],
                    'kwargs': str(kwargs)[:100]
                })
                raise

        def sync_wrapper(*args, **kwargs):
            logger_instance = get_logger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 同步函数中的异步处理
                asyncio.create_task(logger_instance.handle_error(e, {
                    'function': func.__name__,
                    'args': str(args)[:100],
                    'kwargs': str(kwargs)[:100]
                }))
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 认知系统日志管理测试')
    logger.info(str('='*50))

    # 创建日志管理器
    logger = get_logger('TestComponent')

    # 启动日志管理器
    await logger.start()

    # 设置上下文
    logger.set_context(user_id='user123', request_id='req456')

    # 记录各种类型的日志
    logger.info("\n📝 记录测试日志...")
    logger.trace('这是一个跟踪消息')
    logger.debug('这是一个调试消息')
    logger.info('这是一个信息消息')
    logger.warning('这是一个警告消息')
    logger.error('这是一个错误消息')
    logger.critical('这是一个严重错误消息')

    # 记录业务事件
    logger.log_business_event('用户登录', user_id='user123', ip='192.168.1.1')

    # 记录审计事件
    logger.log_audit_event('数据访问', '专利数据库', record_id='patent001')

    # 性能测试
    logger.start_timer('test_operation')
    await asyncio.sleep(0.1)
    duration = logger.end_timer('test_operation')
    logger.info(f"操作耗时: {duration:.3f}秒")

    # 错误处理测试
    logger.info("\n❌ 测试错误处理...")
    try:
        raise ValueError('这是一个测试错误')
    except Exception as e:
        error_id = await logger.handle_error(e, {'test': True})
        logger.info(f"错误ID: {error_id}")

    # 获取性能报告
    logger.info("\n📊 性能报告:")
    report = logger.get_performance_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 获取日志
    logger.info("\n📋 获取最近的日志:")
    recent_logs = await logger.log_handler.get_logs(limit=5)
    for log in recent_logs:
        logger.info(f"[{log.level.name}] {log.message}")

    # 停止日志管理器
    await logger.stop()

    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    asyncio.run(main())