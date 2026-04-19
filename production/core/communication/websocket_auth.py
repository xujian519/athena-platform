#!/usr/bin/env python3
from __future__ import annotations
"""
Athena通信系统 - WebSocket认证模块
WebSocket Authentication for Communication System

提供WebSocket连接的JWT认证功能。

主要功能:
1. JWT令牌验证
2. 连接认证
3. 权限检查
4. 认证失败处理

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# 使用PyJWT进行令牌验证
import jwt

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """用户角色"""

    ADMIN = "admin"
    DEVELOPER = "developer"
    AI_SERVICE = "ai_service"
    USER = "user"
    GUEST = "guest"


class TokenType(Enum):
    """令牌类型"""

    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class WebSocketAuthResult:
    """WebSocket认证结果"""

    success: bool
    user_id: str | None = None
    username: str | None = None
    role: UserRole | None = None
    permissions: list[str] | None = None
    error: str | None = None
    client_type: str | None = None
    ai_name: str | None = None


@dataclass
class WebSocketAuthConfig:
    """WebSocket认证配置"""

    enable_auth: bool = True
    require_token: bool = True  # 是否要求必须提供令牌
    allow_guest: bool = False  # 是否允许访客连接
    token_expiry_buffer: int = 60  # 令牌过期缓冲时间(秒)
    max_auth_attempts: int = 3  # 最大认证尝试次数
    jwt_secret: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"


class WebSocketAuthenticator:
    """
    WebSocket认证器

    使用JWT令牌对WebSocket连接进行认证。
    """

    def __init__(self, config: WebSocketAuthConfig | None = None):
        """
        初始化WebSocket认证器

        Args:
            config: WebSocket认证配置
        """
        self.config = config or WebSocketAuthConfig()
        self.failed_attempts: dict[str, int] = {}

        logger.info("WebSocket认证器初始化完成")

    def _check_rate_limit(self, connection_id: str) -> bool:
        """
        检查认证尝试频率限制

        Args:
            connection_id: 连接ID

        Returns:
            是否允许继续尝试
        """
        if not self.config.enable_auth:
            return True

        attempts = self.failed_attempts.get(connection_id, 0)
        if attempts >= self.config.max_auth_attempts:
            logger.warning(f"认证尝试次数超限: {connection_id}")
            return False

        return True

    def _record_failed_attempt(self, connection_id: str) -> Any:
        """记录失败的认证尝试"""
        self.failed_attempts[connection_id] = self.failed_attempts.get(connection_id, 0) + 1

    def _clear_failed_attempts(self, connection_id: str) -> Any:
        """清除失败的认证记录"""
        self.failed_attempts.pop(connection_id, None)

    def _verify_jwt_token(self, token: str) -> dict[str, Any] | None:
        """
        验证JWT令牌

        Args:
            token: JWT令牌字符串

        Returns:
            令牌payload,验证失败返回None
        """
        try:
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {e}")
            return None

    def authenticate_token(self, token: str) -> WebSocketAuthResult:
        """
        验证JWT令牌

        Args:
            token: JWT令牌字符串

        Returns:
            认证结果
        """
        # 验证令牌
        payload = self._verify_jwt_token(token)

        if not payload:
            return WebSocketAuthResult(success=False, error="令牌无效或已过期")

        # 提取用户信息
        user_id = payload.get("sub")
        username = payload.get("username")
        role_str = payload.get("role")
        permissions = payload.get("permissions", [])

        # 验证令牌类型
        token_type = payload.get("type")
        if token_type != TokenType.ACCESS.value:
            return WebSocketAuthResult(success=False, error=f"无效的令牌类型: {token_type}")

        # 转换角色
        try:
            role = UserRole(role_str)
        except ValueError:
            return WebSocketAuthResult(success=False, error=f"无效的用户角色: {role_str}")

        logger.info(f"✅ JWT令牌验证成功: {username} ({role.value})")

        return WebSocketAuthResult(
            success=True,
            user_id=user_id,
            username=username,
            role=role,
            permissions=list(permissions) if permissions else [],
        )

    def authenticate_message(self, auth_message: str, connection_id: str) -> WebSocketAuthResult:
        """
        验证认证消息

        Args:
            auth_message: 认证消息(JSON字符串)
            connection_id: 连接ID

        Returns:
            认证结果
        """
        # 检查频率限制
        if not self._check_rate_limit(connection_id):
            return WebSocketAuthResult(success=False, error="认证尝试次数过多,请稍后再试")

        # 解析认证消息
        try:
            auth_data = json.loads(auth_message)
        except json.JSONDecodeError:
            self._record_failed_attempt(connection_id)
            return WebSocketAuthResult(success=False, error="无效的JSON格式")

        # 检查消息类型
        if auth_data.get("type") != "auth":
            self._record_failed_attempt(connection_id)
            return WebSocketAuthResult(success=False, error="期望认证消息")

        # 如果禁用认证,直接返回成功
        if not self.config.enable_auth:
            self._clear_failed_attempts(connection_id)
            return WebSocketAuthResult(
                success=True,
                client_type=auth_data.get("client_type", "client"),
                ai_name=auth_data.get("ai_name"),
                username="guest",
            )

        # 提取令牌
        token = auth_data.get("token")

        if not token:
            # 检查是否允许访客
            if self.config.allow_guest:
                self._clear_failed_attempts(connection_id)
                return WebSocketAuthResult(
                    success=True,
                    client_type=auth_data.get("client_type", "guest"),
                    ai_name=auth_data.get("ai_name"),
                    username="guest",
                    role=UserRole.GUEST,
                    permissions=[],
                )

            self._record_failed_attempt(connection_id)
            return WebSocketAuthResult(success=False, error="缺少认证令牌")

        # 验证令牌
        result = self.authenticate_token(token)

        if result.success:
            # 清除失败记录
            self._clear_failed_attempts(connection_id)

            # 添加客户端类型和AI名称
            result.client_type = auth_data.get("client_type", "client")
            result.ai_name = auth_data.get("ai_name")
        else:
            self._record_failed_attempt(connection_id)

        return result

    def create_auth_error_message(self, result: WebSocketAuthResult) -> str:
        """
        创建认证错误消息

        Args:
            result: 认证结果

        Returns:
            错误消息(JSON字符串)
        """
        error_data = {
            "type": "auth_error",
            "success": False,
            "error": result.error,
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(error_data)

    def create_auth_success_message(self, result: WebSocketAuthResult) -> str:
        """
        创建认证成功消息

        Args:
            result: 认证结果

        Returns:
            成功消息(JSON字符串)
        """
        success_data = {
            "type": "auth_success",
            "success": True,
            "user_id": result.user_id,
            "username": result.username,
            "role": result.role.value if result.role else None,
            "permissions": result.permissions or [],
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(success_data)


# =============================================================================
# 便捷函数
# =============================================================================


def create_websocket_authenticator(
    enable_auth: bool = True,
    require_token: bool = True,
    allow_guest: bool = False,
    jwt_secret: str | None = None,
) -> WebSocketAuthenticator:
    """创建WebSocket认证器实例"""
    config = WebSocketAuthConfig(
        enable_auth=enable_auth,
        require_token=require_token,
        allow_guest=allow_guest,
        jwt_secret=jwt_secret or "your-super-secret-key-change-in-production",
    )
    return WebSocketAuthenticator(config=config)


def generate_test_token(
    user_id: str,
    username: str,
    role: UserRole = UserRole.USER,
    permissions: list[str] | None = None,
    secret: str = "your-super-secret-key-change-in-production",
    expire_hours: int = 24,
) -> str:
    """
    生成测试用的JWT令牌

    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
        permissions: 权限列表
        secret: JWT密钥
        expire_hours: 过期时间(小时)

    Returns:
        JWT令牌字符串
    """
    from datetime import timedelta

    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "permissions": permissions or [],
        "type": TokenType.ACCESS.value,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expire_hours),
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


# 默认实例
_default_authenticator: WebSocketAuthenticator | None = None


def get_default_authenticator() -> WebSocketAuthenticator:
    """获取默认WebSocket认证器"""
    global _default_authenticator
    if _default_authenticator is None:
        _default_authenticator = create_websocket_authenticator()
    return _default_authenticator


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "TokenType",
    "UserRole",
    "WebSocketAuthConfig",
    "WebSocketAuthResult",
    "WebSocketAuthenticator",
    "create_websocket_authenticator",
    "generate_test_token",
    "get_default_authenticator",
]
