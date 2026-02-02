#!/usr/bin/env python3
"""
认证模块
提供JWT认证和用户验证功能

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.1
"""

from .jwt_handler import JWTAuthHandler, TokenPayload, get_jwt_handler

__all__ = [
    "JWTAuthHandler",
    "TokenPayload",
    "get_jwt_handler",
]
