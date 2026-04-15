#!/usr/bin/env python3
from __future__ import annotations
"""
错误处理模块
Error Handling Module

作者: Athena平台团队
版本: v1.0
创建: 2025-12-30

功能:
- 错误分类系统
- 智能重试机制
- 错误恢复策略
"""


__all__ = [
    "ErrorCategory",
    "ErrorClassifier",
    "ErrorSeverity",
    "RetryHandler",
    "retry_async",
    "retry_with_backoff",
]
