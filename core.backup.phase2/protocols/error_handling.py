#!/usr/bin/env python3
from __future__ import annotations
"""
协议错误处理增强模块
Protocol Error Handling Enhancement

提供统一的错误处理、重试机制、降级策略和恢复功能
"""

import asyncio
import functools
import logging
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 轻微错误,不影响主要功能
    MEDIUM = "medium"  # 中等错误,影响部分功能
    HIGH = "high"  # 严重错误,影响主要功能
    CRITICAL = "critical"  # 致命错误,系统不可用


class ErrorCategory(Enum):
    """错误类别"""

    INITIALIZATION = "initialization"  # 初始化错误
    COMMUNICATION = "communication"  # 通信错误
    COORDINATION = "coordination"  # 协调错误
    DECISION = "decision"  # 决策错误
    VALIDATION = "validation"  # 验证错误
    TIMEOUT = "timeout"  # 超时错误
    RESOURCE = "resource"  # 资源错误
    UNKNOWN = "unknown"  # 未知错误


class RecoveryAction(Enum):
    """恢复动作"""

    RETRY = "retry"  # 重试
    FALLBACK = "fallback"  # 降级
    IGNORE = "ignore"  # 忽略
    ESCALATE = "escalate"  # 升级
    TERMINATE = "terminate"  # 终止


@dataclass
class ErrorInfo:
    """错误信息"""

    error_id: str
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    timestamp: datetime
    context: dict[str, Any] = field(default_factory=dict)
    stack_trace: str | None = None
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    resolved: bool = False


@dataclass
class RetryConfig:
    """重试配置"""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_factor: float = 1.5


@dataclass
class ErrorHandlingConfig:
    """错误处理配置"""

    enable_retry: bool = True
    enable_fallback: bool = True
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    error_handlers: dict[ErrorCategory, Callable] = field(default_factory=dict)


class CircuitBreaker:
    """熔断器"""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """通过熔断器调用函数"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e

    def record_failure(self) -> Any:
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def reset(self) -> Any:
        """重置熔断器"""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None


class ErrorHandler:
    """错误处理器"""

    def __init__(self, config: ErrorHandlingConfig):
        self.config = config
        self.error_history: list[ErrorInfo] = []
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.error_handlers: dict[ErrorCategory, list[Callable]] = {}

        # 初始化默认错误处理器
        self._initialize_default_handlers()

    def _initialize_default_handlers(self) -> Any:
        """初始化默认错误处理器"""
        for category in ErrorCategory:
            self.error_handlers[category] = []

    def register_handler(self, category: ErrorCategory, handler: Callable) -> Any:
        """注册错误处理器"""
        if category not in self.error_handlers:
            self.error_handlers[category] = []
        self.error_handlers[category].append(handler)

    def handle_error(self, error: Exception, context: dict[str, Any] | None = None) -> ErrorInfo:
        """处理错误"""
        if context is None:
            context = {}

        # 分类错误
        category = self._classify_error(error)
        severity = self._determine_severity(error, category)

        # 创建错误信息
        error_info = ErrorInfo(
            error_id=self._generate_error_id(),
            error_type=type(error).__name__,
            category=category,
            severity=severity,
            message=str(error),
            timestamp=datetime.now(),
            context=context,
            stack_trace=traceback.format_exc(),
        )

        # 记录错误
        self.error_history.append(error_info)

        # 触发错误处理器
        self._trigger_error_handlers(error_info)

        # 记录日志
        self._log_error(error_info)

        return error_info

    def _classify_error(self, error: Exception) -> ErrorCategory:
        """分类错误"""
        error_message = str(error).lower()
        type(error).__name__.lower()

        if any(keyword in error_message for keyword in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT
        elif any(keyword in error_message for keyword in ["connection", "network", "socket"]):
            return ErrorCategory.COMMUNICATION
        elif any(keyword in error_message for keyword in ["initialization", "initial", "setup"]):
            return ErrorCategory.INITIALIZATION
        elif any(keyword in error_message for keyword in ["validation", "invalid", "format"]):
            return ErrorCategory.VALIDATION
        elif any(keyword in error_message for keyword in ["resource", "memory", "cpu"]):
            return ErrorCategory.RESOURCE
        elif "decision" in error_message or "choice" in error_message:
            return ErrorCategory.DECISION
        elif "coordination" in error_message or "allocation" in error_message:
            return ErrorCategory.COORDINATION
        else:
            return ErrorCategory.UNKNOWN

    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """确定错误严重程度"""
        error_message = str(error).lower()

        # 致命错误关键词
        critical_keywords = ["critical", "fatal", "system", "crash"]
        if any(keyword in error_message for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL

        # 严重错误关键词
        high_keywords = ["failed", "error", "exception", "timeout"]
        if any(keyword in error_message for keyword in high_keywords):
            return ErrorSeverity.HIGH

        # 基于类别确定严重程度
        if category in [ErrorCategory.INITIALIZATION, ErrorCategory.RESOURCE]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.COMMUNICATION, ErrorCategory.TIMEOUT]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _generate_error_id(self) -> str:
        """生成错误ID"""
        return f"ERR_{int(time.time() * 1000)}_{len(self.error_history)}"

    def _trigger_error_handlers(self, error_info: ErrorInfo) -> Any:
        """触发错误处理器"""
        handlers = self.error_handlers.get(error_info.category, [])
        for handler in handlers:
            try:
                asyncio.create_task(handler(error_info))
            except Exception as e:
                logger.error(f"错误处理器执行失败: {e}")

    def _log_error(self, error_info: ErrorInfo) -> Any:
        """记录错误日志"""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(error_info.severity, logging.ERROR)

        logger.log(
            log_level,
            f"[{error_info.error_id}] {error_info.category.value.upper()} {error_info.error_type}: {error_info.message}",
        )

    def get_error_statistics(self) -> dict[str, Any]:
        """获取错误统计"""
        if not self.error_history:
            return {}

        total_errors = len(self.error_history)
        category_counts = {}
        severity_counts = {}

        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1

        resolved_errors = sum(1 for error in self.error_history if error.resolved)

        return {
            "total_errors": total_errors,
            "resolved_errors": resolved_errors,
            "resolution_rate": resolved_errors / total_errors,
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "recent_errors": [error.error_id for error in self.error_history[-10:]],
        }


def retry_handler(config: RetryConfig) -> Any:
    """重试装饰器"""

    def decorator(func: Callable) -> Any:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        # 计算延迟时间
                        delay = min(
                            config.base_delay * (config.exponential_base**attempt), config.max_delay
                        )

                        if config.jitter:
                            import random

                            delay *= 0.5 + random.random() * 0.5

                        logger.warning(
                            f"函数 {func.__name__} 第 {attempt + 1} 次调用失败,{delay:.2f}秒后重试: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"函数 {func.__name__} 重试 {config.max_attempts} 次后仍然失败: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


def circuit_breaker_handler(threshold: int = 5, timeout: float = 60.0) -> Any:
    """熔断器装饰器"""

    def decorator(func: Callable) -> Any:
        breaker = CircuitBreaker(threshold, timeout)

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await asyncio.get_event_loop().run_in_executor(
                None, breaker.call, func, *args, **kwargs
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator


def safe_execute(
    func: Callable,
    fallback_func: Callable | None = None,
    error_handler: Callable | None = None,
    *args,
    **kwargs,
):
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            try:
                error_handler(e, *args, **kwargs)
            except Exception as handler_error:
                logger.error(f"错误处理器执行失败: {handler_error}")

        if fallback_func:
            try:
                return fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"降级函数执行失败: {fallback_error}")

        raise e


async def safe_execute_async(
    func: Callable,
    fallback_func: Callable | None = None,
    error_handler: Callable | None = None,
    timeout: float | None = None,
    *args,
    **kwargs,
):
    """安全执行异步函数"""
    try:
        if timeout:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        else:
            return await func(*args, **kwargs)
    except asyncio.TimeoutError as e:
        logger.error(f"函数 {func.__name__} 执行超时 ({timeout}秒): {e}")
        raise e
    except Exception as e:
        if error_handler:
            try:
                if asyncio.iscoroutinefunction(error_handler):
                    await error_handler(e, *args, **kwargs)
                else:
                    error_handler(e, *args, **kwargs)
            except Exception as handler_error:
                logger.error(f"错误处理器执行失败: {handler_error}")

        if fallback_func:
            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*args, **kwargs)
                else:
                    return fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"降级函数执行失败: {fallback_error}")

        raise e


class ProtocolErrorEnhancer:
    """协议错误增强器"""

    def __init__(self, config: ErrorHandlingConfig | None = None):
        self.config = config or ErrorHandlingConfig()
        self.error_handler = ErrorHandler(self.config)
        self._setup_error_handlers()

    def _setup_error_handlers(self) -> Any:
        """设置错误处理器"""
        # 初始化错误错误处理器
        self.error_handler.register_handler(
            ErrorCategory.INITIALIZATION, self._handle_initialization_error
        )

        # 通信错误处理器
        self.error_handler.register_handler(
            ErrorCategory.COMMUNICATION, self._handle_communication_error
        )

        # 超时错误处理器
        self.error_handler.register_handler(ErrorCategory.TIMEOUT, self._handle_timeout_error)

        # 验证错误处理器
        self.error_handler.register_handler(ErrorCategory.VALIDATION, self._handle_validation_error)

    async def _handle_initialization_error(self, error_info: ErrorInfo):
        """处理初始化错误"""
        logger.warning(f"处理初始化错误: {error_info.message}")
        # 可以在这里实现自动重试、重新配置等逻辑

    async def _handle_communication_error(self, error_info: ErrorInfo):
        """处理通信错误"""
        logger.warning(f"处理通信错误: {error_info.message}")
        # 可以在这里实现重连、降级等逻辑

    async def _handle_timeout_error(self, error_info: ErrorInfo):
        """处理超时错误"""
        logger.warning(f"处理超时错误: {error_info.message}")
        # 可以在这里实现增加超时时间、减少并发等逻辑

    async def _handle_validation_error(self, error_info: ErrorInfo):
        """处理验证错误"""
        logger.warning(f"处理验证错误: {error_info.message}")
        # 可以在这里实现数据修复、默认值替换等逻辑

    def enhance_protocol_start(self, start_func: Callable) -> Any:
        """增强协议启动函数"""

        @functools.wraps(start_func)
        async def enhanced_start(*args, **kwargs):
            try:
                if self.config.enable_retry:
                    return await retry_handler(self.config.retry_config)(start_func)(
                        *args, **kwargs
                    )
                else:
                    return await start_func(*args, **kwargs)
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, context={"function": "protocol_start", "args": str(args)[:100]}
                )

                # 尝试降级策略
                if self.config.enable_fallback:
                    logger.info(f"协议启动失败,尝试降级策略: {error_info.error_id}")
                    return await self._fallback_start(*args, **kwargs)
                else:
                    raise e

        return enhanced_start

    def enhance_message_handling(self, handle_func: Callable) -> Any:
        """增强消息处理函数"""

        @functools.wraps(handle_func)
        async def enhanced_handle(*args, **kwargs):
            try:
                return await handle_func(*args, **kwargs)
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, context={"function": "message_handling", "args": str(args)[:100]}
                )

                # 对于消息处理错误,通常可以忽略并继续
                if error_info.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
                    logger.warning(f"消息处理失败,继续执行: {error_info.error_id}")
                    return False
                else:
                    raise e

        return enhanced_handle

    async def _fallback_start(self, *args, **kwargs):
        """降级启动策略"""
        logger.info("执行协议启动降级策略")
        # 实现简化的启动逻辑
        await asyncio.sleep(0.1)  # 短暂延迟
        return True  # 返回成功,但功能可能受限

    def get_enhanced_statistics(self) -> dict[str, Any]:
        """获取增强统计信息"""
        return {
            "error_stats": self.error_handler.get_error_statistics(),
            "circuit_breaker_stats": {
                name: {"state": breaker.state, "failure_count": breaker.failure_count}
                for name, breaker in self.error_handler.circuit_breakers.items()
            },
            "config": {
                "retry_enabled": self.config.enable_retry,
                "fallback_enabled": self.config.enable_fallback,
                "circuit_breaker_enabled": self.config.enable_circuit_breaker,
            },
        }


# 全局错误增强器实例
global_error_enhancer = ProtocolErrorEnhancer()


def enhance_protocol_protocol(protocol_instance) -> None:
    """增强协议实例"""
    # 增强启动方法
    if hasattr(protocol_instance, "start"):
        original_start = protocol_instance.start
        protocol_instance.start = global_error_enhancer.enhance_protocol_start(original_start)

    # 增强消息处理方法
    if hasattr(protocol_instance, "receive_message"):
        original_receive = protocol_instance.receive_message
        protocol_instance.receive_message = global_error_enhancer.enhance_message_handling(
            original_receive
        )

    return protocol_instance
