#!/usr/bin/env python3
"""
错误处理模块 - Athena平台错误处理系统
Error Handlers Module - Athena Platform Error Handling System

提供统一的异常定义和错误处理机制

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

from .exceptions import (
    AthenaError,
    # 基础异常
    AthenaException,
    AuthenticationException,
    # 缓存相关异常
    CacheException,
    # 配置相关异常
    ConfigurationException,
    DatabaseException,
    FileNotFoundException,
    FileProcessingException,
    # 文件相关异常
    FileUploadException,
    FileValidationException,
    # 网络相关异常
    NetworkException,
    # 存储相关异常
    StorageException,
)
from .handlers import (
    athena_exception_handler,
    create_error_response,
    format_error_response,
    generic_exception_handler,
    setup_error_handlers,
)

__all__ = [
    "AthenaError",
    # 基础异常
    "AthenaException",
    "AuthenticationException",
    # 缓存相关异常
    "CacheException",
    # 配置相关异常
    "ConfigurationException",
    "DatabaseException",
    "FileNotFoundException",
    "FileProcessingException",
    # 文件相关异常
    "FileUploadException",
    "FileValidationException",
    # 网络相关异常
    "NetworkException",
    # 存储相关异常
    "StorageException",
    # 错误处理器
    "athena_exception_handler",
    "create_error_response",
    "format_error_response",
    "generic_exception_handler",
    "setup_error_handlers",
]
