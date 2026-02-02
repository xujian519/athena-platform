#!/usr/bin/env python3
"""
Gateway模块
WebSocket通信和会话管理

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.2
"""

from .protocol import (
    FrameType,
    GatewayProtocol,
    GatewayMethod,
    GatewayEventType,
)

from .session import (
    GatewaySession,
    GatewaySessionManager,
)

from .error_handler import (
    GatewayErrorCode,
    GatewayError,
    AuthenticationError,
    ValidationError,
    MethodError,
    ModuleError,
    GatewayErrorHandler,
    create_auth_error,
    create_validation_error,
    create_method_error,
    create_module_error,
)

__all__ = [
    # 协议相关
    "FrameType",
    "GatewayProtocol",
    "GatewayMethod",
    "GatewayEventType",
    # 会话相关
    "GatewaySession",
    "GatewaySessionManager",
    # 错误处理相关
    "GatewayErrorCode",
    "GatewayError",
    "AuthenticationError",
    "ValidationError",
    "MethodError",
    "ModuleError",
    "GatewayErrorHandler",
    "create_auth_error",
    "create_validation_error",
    "create_method_error",
    "create_module_error",
]
