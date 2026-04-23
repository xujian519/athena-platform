#!/usr/bin/env python3
from __future__ import annotations
"""
学习引擎错误处理和重试机制
Error Handling and Retry Mechanism for Learning Engines

提供完善的错误处理和重试机制：
1. 智能重试：指数退避、最大重试次数
2. 错误分类：可恢复错误、致命错误
3. 断路器模式：防止连续失败
4. 降级策略：失败时的备选方案

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorSeverity(str, Enum):
    """错误严重程度"""

    LOW = "low"  # 低：可以忽略的错误
    MEDIUM = "medium"  # 中：需要记录但不需要立即处理
    HIGH = "high"  # 高：需要立即处理
    CRITICAL = "critical"  # 严重：系统可能无法继续运行


class ErrorCategory(str, Enum):
    """错误类别"""

    TRANSIENT = "transient"  # 临时错误：可以重试
    PERMANENT = "permanent"  # 永久错误：重试无效
    RATE_LIMIT = "rate_limit"  # 速率限制：需要等待
    RESOURCE = "resource"  # 资源错误：内存、磁盘等
    NETWORK = "network"  # 网络错误
    VALIDATION = "validation"  # 验证错误：输入无效


@dataclass
class ErrorContext:
    """错误上下文"""

    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class LearningEngineError(Exception):
    """学习引擎基础异常"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.TRANSIENT,
        **metadata,
    ):
        self.message = message
        self.severity = severity
        self.category = category
        self.metadata = metadata
        self.timestamp = datetime.now()
        super().__init__(message)


class TransientError(LearningEngineError):
    """临时错误：可以重试"""

    def __init__(self, message: str, **metadata):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.TRANSIENT,
            **metadata,
        )


class PermanentError(LearningEngineError):
    """永久错误：重试无效"""

    def __init__(self, message: str, **metadata):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.PERMANENT,
            **metadata,
        )


class ValidationError(LearningEngineError):
    """验证错误：输入无效"""

    def __init__(self, message: str, **metadata):
        super().__init__(
            message,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            **metadata,
        )


class ResourceError(LearningEngineError):
    """资源错误：内存、磁盘等"""

    def __init__(self, message: str, **metadata):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.RESOURCE,
            **metadata,
        )


@dataclass
class RetryConfig:
    """重试配置"""

    max_attempts: int = 3  # 最大重试次数
    base_delay: float = 1.0  # 基础延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    exponential_base: float = 2.0  # 指数退避基数
    jitter: bool = True  # 是否添加随机抖动
    jitter_factor: float = 0.1  # 抖动因子


class RetryHandler:
    """
    重试处理器

    实现智能重试策略，包括指数退避和抖动。
    """

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self.retry_history: list[ErrorContext] = []
        self.total_retries = 0
        self.successful_retries = 0

    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[T] | T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        执行函数并在失败时重试

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            LearningEngineError: 重试耗尽后仍然失败
        """
        last_error: Exception | None = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                # 检查是否需要await
                if asyncio.iscoroutine(result):
                    return await result  # type: ignore
                return result  # type: ignore

            except LearningEngineError as e:
                last_error = e

                # 永久错误不重试
                if e.category == ErrorCategory.PERMANENT:
                    logger.error(f"永久错误，不重试: {e.message}")
                    raise

                # 验证错误不重试
                if e.category == ErrorCategory.VALIDATION:
                    logger.warning(f"验证错误，不重试: {e.message}")
                    raise

                # 记录错误
                error_context = ErrorContext(
                    error_type=type(e).__name__,
                    error_message=e.message,
                    severity=e.severity,
                    category=e.category,
                    retry_count=attempt,
                )
                self.retry_history.append(error_context)

                # 最后一次尝试失败，不再等待
                if attempt == self.config.max_attempts - 1:
                    break

                # 计算延迟
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"第{attempt + 1}次尝试失败: {e.message}, {delay:.2f}秒后重试..."
                )

                await asyncio.sleep(delay)

            except Exception as e:
                # 未知错误，记录并重试
                last_error = e
                logger.error(f"未预期的错误: {e}")

                if attempt == self.config.max_attempts - 1:
                    break

                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)

        # 重试耗尽
        self.total_retries += self.config.max_attempts
        raise LearningEngineError(
            f"重试{self.config.max_attempts}次后仍然失败: {last_error}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.TRANSIENT,
        ) from last_error

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟（带指数退避和抖动）"""
        # 指数退避
        delay = self.config.base_delay * (self.config.exponential_base**attempt)

        # 限制最大延迟
        delay = min(delay, self.config.max_delay)

        # 添加抖动
        if self.config.jitter:
            import random

            jitter_amount = delay * self.config.jitter_factor
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_retries": self.total_retries,
            "successful_retries": self.successful_retries,
            "recent_errors": self.retry_history[-10:] if self.retry_history else [],
        }


class CircuitBreaker:
    """
    断路器

    防止连续访问失败的服务，保护系统资源。
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        half_open_attempts: int = 3,
    ):
        """
        初始化断路器

        Args:
            failure_threshold: 失败阈值（连续失败次数）
            timeout: 断路器恢复超时（秒）
            half_open_attempts: 半开状态的尝试次数
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts

        self._failures = 0
        self._state = "closed"  # closed, open, half_open
        self._last_failure_time: datetime | None = None
        self._half_open_success_count = 0

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        通过断路器调用函数

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            LearningEngineError: 断路器处于打开状态
        """
        # 检查是否应该恢复
        if self._state == "open" and self._should_attempt_reset():
            self._state = "half_open"
            self._half_open_success_count = 0
            logger.info("断路器进入半开状态")

        # 拒绝请求
        if self._state == "open":
            raise LearningEngineError(
                "断路器处于打开状态，拒绝请求",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.TRANSIENT,
            )

        try:
            result = await func(*args, **kwargs)  # type: ignore[misc]

            # 成功，重置失败计数
            if self._state == "half_open":
                self._half_open_success_count += 1
                if self._half_open_success_count >= self.half_open_attempts:
                    self._state = "closed"
                    self._failures = 0
                    logger.info("断路器恢复到关闭状态")
            else:
                self._failures = 0

            return result  # type: ignore[no-any-return]

        except Exception:
            self._failures += 1
            self._last_failure_time = datetime.now()

            # 达到失败阈值，打开断路器
            if self._failures >= self.failure_threshold:
                self._state = "open"
                logger.error(
                    f"断路器打开（连续失败{self._failures}次），"
                    f"{self.timeout}秒后将尝试恢复"
                )

            raise

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试恢复"""
        if self._last_failure_time is None:
            return False

        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        return elapsed >= self.timeout

    def get_state(self) -> dict[str, Any]:
        """获取断路器状态"""
        return {
            "state": self._state,
            "failures": self._failures,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self._last_failure_time.isoformat()
            if self._last_failure_time
            else None,
        }


class FallbackHandler:
    """
    降级处理器

    提供失败时的备选方案。
    """

    def __init__(self):
        self.fallback_functions: dict[str, Callable] = {}
        self.fallback_stats: dict[str, dict[str, Any]] = {}

    def register_fallback(
        self, name: str, func: Callable, primary: Callable | None = None
    ) -> None:
        """
        注册降级函数

        Args:
            name: 函数名称
            func: 降级函数
            primary: 主函数（可选）
        """
        self.fallback_functions[name] = func
        self.fallback_stats[name] = {
            "primary_calls": 0,
            "fallback_calls": 0,
            "primary_failures": 0,
        }
        logger.info(f"注册降级函数: {name}")

    async def execute_with_fallback(
        self,
        name: str,
        primary_func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        执行主函数，失败时使用降级函数

        Args:
            name: 函数名称
            primary_func: 主函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            LearningEngineError: 主函数和降级函数都失败
        """
        if name not in self.fallback_functions:
            return await primary_func(*args, **kwargs)  # type: ignore

        stats = self.fallback_stats[name]
        stats["primary_calls"] += 1

        try:
            return await primary_func(*args, **kwargs)  # type: ignore

        except Exception as e:
            stats["primary_failures"] += 1
            logger.warning(f"主函数失败: {name}, 使用降级函数: {e}")

            fallback_func = self.fallback_functions[name]
            stats["fallback_calls"] += 1

            try:
                return await fallback_func(*args, **kwargs)  # type: ignore

            except Exception as fallback_error:
                logger.error(f"降级函数也失败: {name}: {fallback_error}")
                raise LearningEngineError(
                    f"主函数和降级函数都失败: {name}",
                    severity=ErrorSeverity.HIGH,
                ) from fallback_error

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.fallback_stats.copy()


class ErrorHandlingMixin:
    """
    错误处理混入类

    为学习引擎提供错误处理能力。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.retry_handler = RetryHandler()
        self.circuit_breaker = CircuitBreaker()
        self.fallback_handler = FallbackHandler()
        self.error_history: list[ErrorContext] = []

    def _handle_error(self, error: Exception, context: Optional[dict[str, Any]] = None) -> None:
        """处理错误"""
        if isinstance(error, LearningEngineError):
            error_context = ErrorContext(
                error_type=type(error).__name__,
                error_message=error.message,
                severity=error.severity,
                category=error.category,
                metadata=context or error.metadata,
            )
        else:
            error_context = ErrorContext(
                error_type=type(error).__name__,
                error_message=str(error),
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.TRANSIENT,
                metadata=context or {},
            )

        self.error_history.append(error_context)

        # 限制历史大小
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

        # 记录日志
        log_method = {
            ErrorSeverity.LOW: logger.debug,
            ErrorSeverity.MEDIUM: logger.warning,
            ErrorSeverity.HIGH: logger.error,
            ErrorSeverity.CRITICAL: logger.critical,
        }.get(error_context.severity, logger.error)

        log_method(
            f"错误: {error_context.error_type} - {error_context.error_message}",
            extra={"context": error_context.metadata},
        )

    def get_error_statistics(self) -> dict[str, Any]:
        """获取错误统计信息"""
        return {
            "total_errors": len(self.error_history),
            "recent_errors": self.error_history[-10:] if self.error_history else [],
            "retry_stats": self.retry_handler.get_statistics(),
            "circuit_breaker": self.circuit_breaker.get_state(),
            "fallback_stats": self.fallback_handler.get_statistics(),
        }


# 为保持兼容性，提供别名
LearningErrorHandler = ErrorHandlingMixin


__all__ = [
    # 异常类
    "LearningEngineError",
    "TransientError",
    "PermanentError",
    "ValidationError",
    "ResourceError",
    # 数据类
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "RetryConfig",
    # 处理器类
    "RetryHandler",
    "CircuitBreaker",
    "FallbackHandler",
    "ErrorHandlingMixin",
    "LearningErrorHandler",  # 别名
]
