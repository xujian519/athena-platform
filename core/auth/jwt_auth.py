#!/usr/bin/env python3
from __future__ import annotations
"""
身份认证和授权模块
Authentication and Authorization Module

提供JWT令牌认证和API Key认证功能
"""

import logging
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)


# =============================================================================
# 角色和权限枚举
# =============================================================================


class Role(str, Enum):
    """用户角色"""

    ADMIN = "admin"  # 管理员
    USER = "user"  # 普通用户
    GUEST = "guest"  # 访客
    SERVICE = "service"  # 服务账号


class Permission(str, Enum):
    """权限"""

    # 搜索相关
    SEARCH_READ = "search:read"
    SEARCH_WRITE = "search:write"
    SEARCH_ADMIN = "search:admin"

    # 文档相关
    DOC_READ = "document:read"
    DOC_WRITE = "document:write"
    DOC_DELETE = "document:delete"

    # 管理相关
    USER_MANAGE = "user:manage"
    SYSTEM_MANAGE = "system:manage"
    API_KEY_MANAGE = "apikey:manage"


# =============================================================================
# 角色权限映射
# =============================================================================

ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.ADMIN: [
        Permission.SEARCH_READ,
        Permission.SEARCH_WRITE,
        Permission.SEARCH_ADMIN,
        Permission.DOC_READ,
        Permission.DOC_WRITE,
        Permission.DOC_DELETE,
        Permission.USER_MANAGE,
        Permission.SYSTEM_MANAGE,
        Permission.API_KEY_MANAGE,
    ],
    Role.USER: [
        Permission.SEARCH_READ,
        Permission.SEARCH_WRITE,
        Permission.DOC_READ,
        Permission.DOC_WRITE,
    ],
    Role.GUEST: [
        Permission.SEARCH_READ,
        Permission.DOC_READ,
    ],
    Role.SERVICE: [
        Permission.SEARCH_READ,
        Permission.SEARCH_WRITE,
        Permission.DOC_READ,
    ],
}


# =============================================================================
# JWT配置
# =============================================================================


@dataclass
class JWTConfig:
    """JWT配置"""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire: int = 3600  # 访问令牌过期时间(秒)
    refresh_token_expire: int = 2592000  # 刷新令牌过期时间(30天)
    issuer: str = "athena_platform"


# =============================================================================
# 用户信息
# =============================================================================


@dataclass
class User:
    """用户信息"""

    user_id: str
    username: str
    email: str
    role: Role
    permissions: list[Permission]
    is_active: bool = True

    def has_permission(self, permission: Permission) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.permissions

    def has_any_permission(self, permissions: list[Permission]) -> bool:
        """检查用户是否有任意一个指定权限"""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, permissions: list[Permission]) -> bool:
        """检查用户是否有所有指定权限"""
        return all(p in self.permissions for p in permissions)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "permissions": [p.value for p in self.permissions],
            "is_active": self.is_active,
        }


# =============================================================================
# JWT认证管理器
# =============================================================================


class JWTAuthManager:
    """
    JWT认证管理器

    提供JWT令牌的生成、验证和刷新功能

    Examples:
        >>> from core.config.env_loader import get_env_str
        >>>
        >>> manager = JWTAuthManager(
        >>>     secret_key=get_env_str('JWT_SECRET_KEY', 'your-secret-key')
        >>> )
        >>>
        >>> # 生成令牌
        >>> token = manager.create_access_token(user)
        >>>
        >>> # 验证令牌
        >>> user = manager.verify_token(token)
    """

    def __init__(self, config: JWTConfig):
        """
        初始化JWT认证管理器

        Args:
            config: JWT配置
        """
        self.config = config
        logger.info("JWT认证管理器初始化完成")

    def create_access_token(self, user: User) -> str:
        """
        创建访问令牌

        Args:
            user: 用户信息

        Returns:
            JWT令牌字符串
        """
        now = time.time()

        payload = {
            "sub": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "iat": now,
            "exp": now + self.config.access_token_expire,
            "iss": self.config.issuer,
            "type": "access",
        }

        token = jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)

        logger.debug(f"为用户 {user.username} 创建访问令牌")
        return token

    def create_refresh_token(self, user: User) -> str:
        """
        创建刷新令牌

        Args:
            user: 用户信息

        Returns:
            刷新令牌字符串
        """
        now = time.time()

        payload = {
            "sub": user.user_id,
            "iat": now,
            "exp": now + self.config.refresh_token_expire,
            "iss": self.config.issuer,
            "type": "refresh",
        }

        token = jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)

        logger.debug(f"为用户 {user.username} 创建刷新令牌")
        return token

    def verify_token(self, token: str) -> User:
        """
        验证令牌并返回用户信息

        Args:
            token: JWT令牌字符串

        Returns:
            用户信息

        Raises:
            HTTPException: 令牌无效或过期
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
            )

            # 检查令牌类型
            token_type = payload.get("type")
            if token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌类型"
                )

            # 构建用户对象
            user = User(
                user_id=payload["sub"],
                username=payload["username"],
                email=payload["email"],
                role=Role(payload["role"]),
                permissions=[Permission(p) for p in payload["permissions"]],
                is_active=True,
            )

            logger.debug(f"令牌验证成功: {user.username}")
            return user

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"无效的令牌: {e!s}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        使用刷新令牌获取新的访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的访问令牌

        Raises:
            HTTPException: 刷新令牌无效
        """
        try:
            payload = jwt.decode(
                refresh_token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
            )

            # 验证令牌类型
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
                )

            # 这里应该从数据库获取完整用户信息
            # 简化实现,仅使用payload中的信息
            user = User(
                user_id=payload["sub"],
                username=payload.get("sub", "user"),  # 简化
                email=f"{payload['sub']}@example.com",  # 简化
                role=Role.USER,
                permissions=ROLE_PERMISSIONS[Role.USER],
                is_active=True,
            )

            # 生成新的访问令牌
            return self.create_access_token(user)

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌已过期") from None
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"无效的刷新令牌: {e!s}"
            ) from e


# =============================================================================
# API Key管理器
# =============================================================================


class APIKeyManager:
    """
    API Key管理器

    提供API Key的生成、验证和管理功能

    Examples:
        >>> manager = APIKeyManager()
        >>>
        >>> # 生成API Key
        >>> api_key = manager.generate_api_key(user_id="user123")
        >>>
        >>> # 验证API Key
        >>> user_info = manager.verify_api_key(api_key)
    """

    def __init__(self):
        """初始化API Key管理器"""
        # 简化实现,实际应该存储在数据库
        self._api_keys: dict[str, dict[str, Any]] = {}
        logger.info("API Key管理器初始化完成")

    def generate_api_key(
        self, user_id: str, name: str = "default", permissions: list[Permission] | None = None
    ) -> str:
        """
        生成API Key

        Args:
            user_id: 用户ID
            name: API Key名称
            permissions: 权限列表

        Returns:
            API Key字符串
        """
        # 生成随机密钥
        key = f"athena_{secrets.token_urlsafe(32)}"

        # 存储API Key信息
        self._api_keys[key] = {
            "user_id": user_id,
            "name": name,
            "permissions": permissions or [],
            "created_at": time.time(),
            "last_used_at": None,
            "is_active": True,
        }

        logger.info(f"为用户 {user_id} 生成API Key: {name}")
        return key

    def verify_api_key(self, api_key: str) -> Optional[dict[str, Any]]:
        """
        验证API Key

        Args:
            api_key: API Key字符串

        Returns:
            API Key信息,验证失败返回None
        """
        key_info = self._api_keys.get(api_key)

        if not key_info:
            logger.warning("无效的API Key")
            return None

        if not key_info["is_active"]:
            logger.warning(f"API Key已停用: {api_key}")
            return None

        # 更新最后使用时间
        key_info["last_used_at"] = time.time()

        logger.debug(f"API Key验证成功: {key_info['name']}")
        return key_info

    def revoke_api_key(self, api_key: str) -> bool:
        """
        停用API Key

        Args:
            api_key: API Key字符串

        Returns:
            是否成功停用
        """
        if api_key in self._api_keys:
            self._api_keys[api_key]["is_active"] = False
            logger.info(f"API Key已停用: {api_key}")
            return True
        return False

    def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """
        列出用户的所有API Key

        Args:
            user_id: 用户ID

        Returns:
            API Key列表(不包含完整密钥)
        """
        user_keys = []
        for key, info in self._api_keys.items():
            if info["user_id"] == user_id:
                user_keys.append(
                    {
                        "name": info["name"],
                        "prefix": key[:20] + "...",
                        "created_at": info["created_at"],
                        "last_used_at": info["last_used_at"],
                        "is_active": info["is_active"],
                    }
                )
        return user_keys


# =============================================================================
# FastAPI安全方案
# =============================================================================

# JWT认证方案
security_jwt = HTTPBearer(auto_error=False)

# API Key认证方案
security_api_key = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_jwt),
    jwt_config: JWTConfig | None = None,
) -> User | None:
    """
    获取当前用户(JWT认证)

    Args:
        credentials: HTTP认证凭据
        jwt_config: JWT配置

    Returns:
        当前用户信息,未认证返回None

    Raises:
        HTTPException: 认证失败
    """
    if not credentials:
        return None

    if jwt_config is None:
        from core.config.env_loader import get_env_str

        jwt_config = JWTConfig(secret_key=get_env_str("JWT_SECRET_KEY", "your-secret-key"))

    manager = JWTAuthManager(jwt_config)
    return manager.verify_token(credentials.credentials)


def require_permission(required_permission: Permission) -> Any:
    """
    权限检查装饰器

    Args:
        required_permission: 需要的权限

    Returns:
        装饰器函数

    Examples:
        >>> @app.get("/admin")
        >>> @require_permission(Permission.SYSTEM_MANAGE)
        >>> async def admin_endpoint():
        >>>     return {"message": "Admin access"}
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取当前用户
            user: User = kwargs.get("current_user")

            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")

            if not user.has_permission(required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要权限: {required_permission.value}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(required_role: Role) -> Any:
    """
    角色检查装饰器

    Args:
        required_role: 需要的角色

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            user: User = kwargs.get("current_user")

            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")

            if user.role != required_role and user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=f"需要角色: {required_role.value}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 常量
    "ROLE_PERMISSIONS",
    "APIKeyManager",
    # 管理器
    "JWTAuthManager",
    # 数据类
    "JWTConfig",
    "Permission",
    # 枚举
    "Role",
    "User",
    "get_current_user",
    "require_permission",
    "require_role",
    "security_api_key",
    # FastAPI集成
    "security_jwt",
]
