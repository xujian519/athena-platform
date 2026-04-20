#!/usr/bin/env python3
"""
认证和授权

Gateway 的认证和授权系统。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class AuthToken:
    """认证令牌"""

    token: str
    user_id: str
    expires_at: datetime
    metadata: Dict[str, Any] | None = None

    def is_valid(self) -> bool:
        """检查令牌是否有效

        Returns:
            bool: 是否有效
        """
        return datetime.now() < self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            dict: 令牌信息
        """
        return {
            "token": self.token,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata,
        }


class AuthManager:
    """认证管理器

    管理认证令牌和权限检查。
    """

    def __init__(
        self,
        secret_key: str = "athena_gateway_secret",
        token_expiry: int = 86400,  # 24小时
    ):
        """初始化认证管理器

        Args:
            secret_key: 密钥
            token_expiry: 令牌过期时间（秒）
        """
        self.secret_key = secret_key
        self.token_expiry = token_expiry
        self._tokens: Dict[str, AuthToken] = {}
        self._user_tokens: Dict[str, set[str]] = {}  # user_id -> tokens

        logger.info(f"🔐 认证管理器已初始化 (令牌过期: {token_expiry}秒)")

    def generate_token(
        self,
        user_id: str,
        metadata: Dict[str, Any] | None = None,
    ) -> AuthToken:
        """生成认证令牌

        Args:
            user_id: 用户 ID
            metadata: 元数据

        Returns:
            AuthToken: 认证令牌
        """
        # 生成令牌字符串
        timestamp = str(int(time.time()))
        raw = f"{user_id}:{timestamp}:{self.secret_key}"
        token_hash = hmac.new(
            self.secret_key.encode(),
            raw.encode(),
            hashlib.sha256,
        ).hexdigest()

        token = f"{user_id}:{timestamp}:{token_hash[:16]}"

        # 创建令牌对象
        expires_at = datetime.now() + timedelta(seconds=self.token_expiry)
        auth_token = AuthToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            metadata=metadata,
        )

        # 存储令牌
        self._tokens[token] = auth_token

        if user_id not in self._user_tokens:
            self._user_tokens[user_id] = set()
        self._user_tokens[user_id].add(token)

        logger.info(f"✅ 令牌已生成: {user_id}")
        return auth_token

    def verify_token(self, token: str) -> AuthToken | None:
        """验证令牌

        Args:
            token: 令牌字符串

        Returns:
            AuthToken | None: 认证令牌（如果有效）
        """
        auth_token = self._tokens.get(token)

        if not auth_token:
            logger.warning(f"⚠️ 令牌不存在: {token[:8]}...")
            return None

        if not auth_token.is_valid():
            logger.warning(f"⚠️ 令牌已过期: {token[:8]}...")
            # 移除过期令牌
            self.revoke_token(token)
            return None

        return auth_token

    def revoke_token(self, token: str) -> bool:
        """撤销令牌

        Args:
            token: 令牌字符串

        Returns:
            bool: 是否撤销成功
        """
        auth_token = self._tokens.get(token)

        if not auth_token:
            return False

        # 从存储中移除
        del self._tokens[token]

        if auth_token.user_id in self._user_tokens:
            self._user_tokens[auth_token.user_id].discard(token)

        logger.info(f"🗑️ 令牌已撤销: {token[:8]}...")
        return True

    def revoke_user_tokens(self, user_id: str) -> int:
        """撤销用户的所有令牌

        Args:
            user_id: 用户 ID

        Returns:
            int: 撤销的令牌数
        """
        tokens = self._user_tokens.get(user_id, set()).copy()
        count = 0

        for token in tokens:
            if self.revoke_token(token):
                count += 1

        return count

    def cleanup_expired_tokens(self) -> int:
        """清理过期令牌

        Returns:
            int: 清理的令牌数
        """
        now = datetime.now()
        expired_tokens = []

        for token, auth_token in self._tokens.items():
            if auth_token.expires_at < now:
                expired_tokens.append(token)

        for token in expired_tokens:
            self.revoke_token(token)

        if expired_tokens:
            logger.info(f"🧹 清理了 {len(expired_tokens)} 个过期令牌")

        return len(expired_tokens)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "total_tokens": len(self._tokens),
            "total_users": len(self._user_tokens),
        }


class PermissionChecker:
    """权限检查器

    检查用户权限。
    """

    def __init__(self):
        """初始化权限检查器"""
        # 角色权限映射
        self._role_permissions: Dict[str, set[str]] = {
            "admin": {"*"},  # 管理员拥有所有权限
            "user": {
                "agent:run",
                "agent:stream",
                "session:create",
                "session:read",
            },
            "guest": {
                "agent:run",
                "session:create",
            },
        }

        logger.info("🔑 权限检查器已初始化")

    def check_permission(
        self,
        user_id: str,
        role: str,
        permission: str,
    ) -> bool:
        """检查权限

        Args:
            user_id: 用户 ID
            role: 角色
            permission: 权限

        Returns:
            bool: 是否有权限
        """
        permissions = self._role_permissions.get(role, set())

        # 检查通配符权限
        if "*" in permissions:
            return True

        # 检查具体权限
        if permission in permissions:
            return True

        logger.warning(
            f"⚠️ 权限不足: user={user_id}, role={role}, permission={permission}"
        )
        return False

    def add_role_permissions(self, role: str, permissions: list[str]) -> None:
        """添加角色权限

        Args:
            role: 角色
            permissions: 权限列表
        """
        if role not in self._role_permissions:
            self._role_permissions[role] = set()

        self._role_permissions[role].update(permissions)
        logger.info(f"✅ 已为角色 {role} 添加 {len(permissions)} 个权限")

    def get_role_permissions(self, role: str) -> set[str]:
        """获取角色权限

        Args:
            role: 角色

        Returns:
            set[str]: 权限集合
        """
        return self._role_permissions.get(role, set()).copy()


class ConnectionLimiter:
    """连接限制器

    限制并发连接数。
    """

    def __init__(
        self,
        max_connections: int = 100,
        max_connections_per_user: int = 5,
    ):
        """初始化连接限制器

        Args:
            max_connections: 最大连接数
            max_connections_per_user: 每用户最大连接数
        """
        self.max_connections = max_connections
        self.max_connections_per_user = max_connections_per_user
        self._connection_count = 0
        self._user_connections: Dict[str, int] = {}

        logger.info(
            f"🚦 连接限制器已初始化 "
            f"(最大: {max_connections}, 每用户: {max_connections_per_user})"
        )

    async def acquire_connection(self, user_id: str | None = None) -> bool:
        """获取连接许可

        Args:
            user_id: 用户 ID

        Returns:
            bool: 是否允许连接
        """
        # 检查全局连接数
        if self._connection_count >= self.max_connections:
            logger.warning(f"⚠️ 连接数已达上限: {self._connection_count}")
            return False

        # 检查用户连接数
        if user_id:
            user_count = self._user_connections.get(user_id, 0)
            if user_count >= self.max_connections_per_user:
                logger.warning(
                    f"⚠️ 用户连接数已达上限: {user_id} ({user_count})"
                )
                return False

        # 允许连接
        self._connection_count += 1

        if user_id:
            self._user_connections[user_id] = (
                self._user_connections.get(user_id, 0) + 1
            )

        logger.debug(
            f"✅ 连接已允许: {user_id} "
            f"(总计: {self._connection_count}, 用户: {self._user_connections.get(user_id, 0)})"
        )
        return True

    async def release_connection(self, user_id: str | None = None) -> None:
        """释放连接

        Args:
            user_id: 用户 ID
        """
        if self._connection_count > 0:
            self._connection_count -= 1

        if user_id and user_id in self._user_connections:
            self._user_connections[user_id] -= 1

            if self._user_connections[user_id] <= 0:
                del self._user_connections[user_id]

        logger.debug(
            f"🔌 连接已释放: {user_id} "
            f"(总计: {self._connection_count}, 用户: {self._user_connections.get(user_id, 0)})"
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "current_connections": self._connection_count,
            "max_connections": self.max_connections,
            "user_connections": self._user_connections.copy(),
        }


# 全局单例
_global_auth_manager: AuthManager | None = None
_global_permission_checker: PermissionChecker | None = None
_global_connection_limiter: ConnectionLimiter | None = None


def get_global_auth_manager() -> AuthManager:
    """获取全局认证管理器

    Returns:
        AuthManager: 全局认证管理器
    """
    global _global_auth_manager
    if _global_auth_manager is None:
        _global_auth_manager = AuthManager()
    return _global_auth_manager


def get_global_permission_checker() -> PermissionChecker:
    """获取全局权限检查器

    Returns:
        PermissionChecker: 全局权限检查器
    """
    global _global_permission_checker
    if _global_permission_checker is None:
        _global_permission_checker = PermissionChecker()
    return _global_permission_checker


def get_global_connection_limiter() -> ConnectionLimiter:
    """获取全局连接限制器

    Returns:
        ConnectionLimiter: 全局连接限制器
    """
    global _global_connection_limiter
    if _global_connection_limiter is None:
        _global_connection_limiter = ConnectionLimiter()
    return _global_connection_limiter


__all__ = [
    "AuthToken",
    "AuthManager",
    "PermissionChecker",
    "ConnectionLimiter",
    "get_global_auth_manager",
    "get_global_permission_checker",
    "get_global_connection_limiter",
]
