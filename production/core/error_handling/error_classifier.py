#!/usr/bin/env python3
from __future__ import annotations
"""
错误分类器
Error Classifier

作者: Athena平台团队
版本: v1.0
创建: 2025-12-30

功能:
- 自动分类错误类型和严重程度
- 判断错误是否可重试
- 提供重试延迟建议
"""

import logging
from enum import Enum

logger = logging.getLogger("ErrorClassifier")


class ErrorSeverity(Enum):
    """错误严重程度"""

    INFO = "info"  # 信息性,不需要处理
    WARNING = "warning"  # 警告,需要关注
    ERROR = "error"  # 错误,需要处理
    CRITICAL = "critical"  # 严重,需要立即处理


class ErrorCategory(Enum):
    """错误类别"""

    NETWORK = "network"  # 网络错误
    TIMEOUT = "timeout"  # 超时错误
    VALIDATION = "validation"  # 验证错误
    CAPABILITY = "capability"  # 能力错误
    SERVICE = "service"  # 服务错误
    AUTH = "auth"  # 认证错误
    RATE_LIMIT = "rate_limit"  # 速率限制
    RESOURCE = "resource"  # 资源错误(内存、磁盘等)
    UNKNOWN = "unknown"  # 未知错误


class ErrorClassifier:
    """错误分类器"""

    # 可重试的错误类别
    RETRYABLE_CATEGORIES = [
        ErrorCategory.NETWORK,
        ErrorCategory.TIMEOUT,
        ErrorCategory.RATE_LIMIT,
        ErrorCategory.SERVICE,  # 某些服务错误可能暂时性
    ]

    # 不可重试的错误类别
    NON_RETRYABLE_CATEGORIES = [ErrorCategory.VALIDATION, ErrorCategory.AUTH]

    @staticmethod
    def classify(error: Exception) -> tuple[ErrorSeverity, ErrorCategory]:
        """
        分类错误

        Args:
            error: 异常对象

        Returns:
            (严重程度, 错误类别)
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()
        error_class = error.__class__

        # 网络错误
        if ErrorClassifier._is_network_error(error_type, error_msg, error_class):
            return ErrorSeverity.ERROR, ErrorCategory.NETWORK

        # 超时错误
        if ErrorClassifier._is_timeout_error(error_type, error_msg, error_class):
            return ErrorSeverity.WARNING, ErrorCategory.TIMEOUT

        # 认证错误
        if ErrorClassifier._is_auth_error(error_type, error_msg):
            return ErrorSeverity.ERROR, ErrorCategory.AUTH

        # 验证错误
        if ErrorClassifier._is_validation_error(error_type, error_class):
            return ErrorSeverity.WARNING, ErrorCategory.VALIDATION

        # 速率限制错误
        if ErrorClassifier._is_rate_limit_error(error_msg):
            return ErrorSeverity.WARNING, ErrorCategory.RATE_LIMIT

        # 能力错误
        if ErrorClassifier._is_capability_error(error_msg):
            return ErrorSeverity.ERROR, ErrorCategory.CAPABILITY

        # 服务错误
        if ErrorClassifier._is_service_error(error_msg):
            return ErrorSeverity.CRITICAL, ErrorCategory.SERVICE

        # 资源错误
        if ErrorClassifier._is_resource_error(error_type, error_msg):
            return ErrorSeverity.CRITICAL, ErrorCategory.RESOURCE

        # 默认未知错误
        return ErrorSeverity.ERROR, ErrorCategory.UNKNOWN

    @staticmethod
    def _is_network_error(error_type: str, error_msg: str, error_class) -> bool:
        """判断是否为网络错误"""
        network_indicators = [
            "connection",
            "network",
            "connect",
            "dns",
            "socket",
            "tcp",
            "http",
            "https",
            "ssl",
            "tls",
        ]

        # 检查错误类型
        if error_type in ["ConnectionError", "ConnectTimeout", "SocketError"]:
            return True

        # 检查错误消息
        if any(indicator in error_msg for indicator in network_indicators):
            return True

        # 检查错误类名
        class_name = error_class.__name__
        return bool("connection" in class_name.lower() or "network" in class_name.lower())

    @staticmethod
    def _is_timeout_error(error_type: str, error_msg: str, error_class) -> bool:
        """判断是否为超时错误"""
        if error_type == "TimeoutError":
            return True

        if "timeout" in error_msg or "timed out" in error_msg:
            return True

        class_name = error_class.__name__
        return "timeout" in class_name.lower()

    @staticmethod
    def _is_auth_error(error_type: str, error_msg: str) -> bool:
        """判断是否为认证错误"""
        auth_indicators = [
            "authentication",
            "authorization",
            "unauthorized",
            "forbidden",
            "401",
            "403",
            "invalid token",
            "expired",
        ]

        return any(indicator in error_msg for indicator in auth_indicators)

    @staticmethod
    def _is_validation_error(error_type: str, error_class) -> bool:
        """判断是否为验证错误"""
        validation_errors = [
            "ValidationError",
            "ValueError",
            "TypeError",
            "FieldError",
            "SchemaError",
        ]

        return error_type in validation_errors

    @staticmethod
    def _is_rate_limit_error(error_msg: str) -> bool:
        """判断是否为速率限制错误"""
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "throttle",
            "quota exceeded",
            "request limit",
        ]

        return any(indicator in error_msg for indicator in rate_limit_indicators)

    @staticmethod
    def _is_capability_error(error_msg: str) -> bool:
        """判断是否为能力错误"""
        capability_indicators = ["capability", "agent", "model", "llm", "ai service"]

        return any(indicator in error_msg for indicator in capability_indicators)

    @staticmethod
    def _is_service_error(error_msg: str) -> bool:
        """判断是否为服务错误"""
        service_indicators = [
            "service unavailable",
            "502",
            "503",
            "504",
            "bad gateway",
            "service error",
            "internal server error",
            "500",
        ]

        return any(indicator in error_msg for indicator in service_indicators)

    @staticmethod
    def _is_resource_error(error_type: str, error_msg: str) -> bool:
        """判断是否为资源错误"""
        if error_type in ["MemoryError", "DiskFull", "OutOfMemory"]:
            return True

        resource_indicators = [
            "out of memory",
            "no space left",
            "disk full",
            "resource limit",
            "allocation failed",
        ]

        return any(indicator in error_msg for indicator in resource_indicators)

    @staticmethod
    def should_retry(error: Exception) -> bool:
        """
        判断是否应该重试

        Args:
            error: 异常对象

        Returns:
            是否应该重试
        """
        severity, category = ErrorClassifier.classify(error)

        # CRITICAL级别的错误通常不应重试
        if severity == ErrorSeverity.CRITICAL:
            return False

        # 检查是否在可重试类别中
        return category in ErrorClassifier.RETRYABLE_CATEGORIES

    @staticmethod
    def get_retry_delay(attempt: int | None,
                        error: Exception | None = None) -> float:
        """
        获取重试延迟(指数退避)

        Args:
            attempt: 当前尝试次数(从0开始)
            error: 异常对象(可选)

        Returns:
            延迟秒数
        """
        # 基础指数退避
        base_delay = min(2**attempt, 60)  # 最大60秒

        # 如果有错误,根据错误类型调整延迟
        if error:
            _, category = ErrorClassifier.classify(error)

            # 速率限制错误需要更长的延迟
            if category == ErrorCategory.RATE_LIMIT:
                return min(base_delay * 3, 120)  # 最大120秒

            # 网络错误使用标准延迟
            if category == ErrorCategory.NETWORK:
                return base_delay

            # 超时错误可以稍长一点
            if category == ErrorCategory.TIMEOUT:
                return min(base_delay * 1.5, 90)

        return base_delay

    @staticmethod
    def get_max_retries(error: Exception | None = None) -> int:
        """
        获取最大重试次数

        Args:
            error: 异常对象(可选)

        Returns:
            最大重试次数
        """
        if not error:
            return 3  # 默认重试3次

        _, category = ErrorClassifier.classify(error)

        # 根据错误类别返回不同的重试次数
        max_retries_map = {
            ErrorCategory.NETWORK: 3,  # 网络错误重试3次
            ErrorCategory.TIMEOUT: 2,  # 超时错误重试2次
            ErrorCategory.RATE_LIMIT: 2,  # 速率限制重试2次
            ErrorCategory.SERVICE: 3,  # 服务错误重试3次
        }

        return max_retries_map.get(category, 3)
