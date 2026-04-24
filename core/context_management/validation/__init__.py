#!/usr/bin/env python3
"""
上下文验证模块 - Phase 3.1安全加固

Context Validation Module - 提供完整的输入验证和安全检查框架

核心组件:
- BaseContextValidator: 基础验证器实现
- SchemaValidator: Schema验证器（Pydantic）
- SecurityChecker: 安全检查器
- ContextValidator: 通用上下文验证器
- TaskContextValidator: 任务上下文验证器
- SessionContextValidator: 会话上下文验证器

安全功能:
- 数据验证（Schema、类型、长度、格式）
- 恶意输入检测（SQL注入、XSS、命令注入、路径遍历）
- 注入攻击防护（清理、转义、白名单）

作者: Athena平台团队
创建时间: 2026-04-24
版本: v3.1.0 "安全加固"
"""

from .base_validator import BaseContextValidator, ValidationError, SecurityIssue
from .context_validators import ContextValidator, SessionContextValidator, TaskContextValidator
from .schema_validator import SchemaValidator
from .security_checker import SecurityChecker

__all__ = [
    "BaseContextValidator",
    "ContextValidator",
    "SessionContextValidator",
    "TaskContextValidator",
    "SchemaValidator",
    "SecurityChecker",
    "ValidationError",
    "SecurityIssue",
]
