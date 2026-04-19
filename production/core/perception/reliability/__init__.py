"""
感知模块可靠性包
包含错误处理、重试管理、降级管理、熔断器
"""

from __future__ import annotations
from .degradation import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    DegradationLevel,
    DegradationManager,
)
from .error_handler import (
    ErrorCategory,
    ErrorHandler,
    ErrorInfo,
    ErrorSeverity,
    global_error_handler,
    handle_errors,
)
from .retry_manager import RetryConfig, RetryManager, RetryResult, RetryStrategy, retry

__all__ = [
    'ErrorHandler',
    'ErrorCategory',
    'ErrorSeverity',
    'ErrorInfo',
    'handle_errors',
    'global_error_handler',
    'RetryManager',
    'RetryConfig',
    'RetryStrategy',
    'RetryResult',
    'retry',
    'CircuitBreaker',
    'DegradationManager',
    'DegradationLevel',
    'CircuitState',
    'CircuitBreakerConfig'
]
