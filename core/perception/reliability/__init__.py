"""
感知模块可靠性包
包含错误处理、重试管理、降级管理、熔断器
"""

from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, ErrorInfo, handle_errors, global_error_handler
from .retry_manager import RetryManager, RetryConfig, RetryStrategy, RetryResult, retry
from .degradation import CircuitBreaker, DegradationManager, DegradationLevel, CircuitState, CircuitBreakerConfig

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
