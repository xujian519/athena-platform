#!/usr/bin/env python3
from __future__ import annotations
"""
认证管理器
Authentication Manager

提供用户认证、会话管理和身份验证功能
支持多种认证方式和安全策略

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import asyncio
import contextlib
import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """用户角色枚举"""

    ADMIN = "admin"  # 系统管理员
    DEVELOPER = "developer"  # 开发者
    USER = "user"  # 普通用户
    GUEST = "guest"  # 访客用户
    AGENT = "agent"  # AI Agent


class Permission(Enum):
    """权限枚举"""

    # 系统权限
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"

    # Agent权限
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    AGENT_DELETE = "agent:delete"

    # 数据权限
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"

    # API权限
    API_ACCESS = "api:access"
    API_ADMIN = "api:admin"


@dataclass
class User:
    """用户信息"""

    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    permissions: set[Permission] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime | None = None
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """会话信息"""

    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    last_accessed: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthToken:
    """认证令牌"""

    token: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    scopes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PasswordManager:
    """密码管理器"""

    def __init__(self, pepper: Optional[str] = None):
        self.pepper = pepper or secrets.token_hex(16)

    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """哈希密码"""
        if salt is None:
            salt = secrets.token_hex(16)

        # 使用pepper增加安全性
        salted_password = password + salt + self.pepper

        # 多次哈希提高安全性
        hash_value = hashlib.sha256(salted_password.encode()).hexdigest()
        for _ in range(1000):  # 1000次迭代
            hash_value = hashlib.sha256((hash_value + salted_password).encode()).hexdigest()

        return hash_value, salt

    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """验证密码"""
        computed_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)

    def generate_secure_token(self, length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)


class SessionManager:
    """会话管理器"""

    def __init__(self, session_timeout: int = 3600):
        self.sessions: dict[str, Session] = {}
        self.session_timeout = session_timeout
        self.lock = asyncio.Lock()

    async def create_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> Session:
        """创建会话"""
        async with self.lock:
            session_id = secrets.token_urlsafe(32)

            expires_at = None
            if expires_in:
                expires_at = datetime.now() + timedelta(seconds=expires_in)
            elif self.session_timeout:
                expires_at = datetime.now() + timedelta(seconds=self.session_timeout)

            session = Session(
                session_id=session_id,
                user_id=user_id,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            self.sessions[session_id] = session
            logger.info(f"✅ 创建会话: {session_id} (用户: {user_id})")

            return session

    async def get_session(self, session_id: str) -> Session | None:
        """获取会话"""
        async with self.lock:
            session = self.sessions.get(session_id)
            if session:
                # 检查会话是否过期
                if session.expires_at and datetime.now() > session.expires_at:
                    await self.delete_session(session_id)
                    return None

                # 更新最后访问时间
                session.last_accessed = datetime.now()
                return session
            return None

    async def update_session(self, session_id: str, **kwargs) -> bool:
        """更新会话"""
        async with self.lock:
            session = self.sessions.get(session_id)
            if session:
                for key, value in kwargs.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                return True
            return False

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        async with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"🗑️ 删除会话: {session_id}")
                return True
            return False

    async def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        async with self.lock:
            now = datetime.now()
            expired_sessions = [
                session_id
                for session_id, session in self.sessions.items()
                if session.expires_at and now > session.expires_at
            ]

            for session_id in expired_sessions:
                del self.sessions[session_id]

            if expired_sessions:
                logger.info(f"🧹 清理过期会话: {len(expired_sessions)} 个")

            return len(expired_sessions)

    async def get_user_sessions(self, user_id: str) -> list[Session]:
        """获取用户的所有会话"""
        async with self.lock:
            return [session for session in self.sessions.values() if session.user_id == user_id]


class TokenManager:
    """令牌管理器"""

    def __init__(self, default_expiry: int = 3600):
        self.tokens: dict[str, AuthToken] = {}
        self.default_expiry = default_expiry
        self.lock = asyncio.Lock()

    async def create_token(
        self,
        user_id: str,
        scopes: Optional[list[str]] = None,
        expires_in: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuthToken:
        """创建认证令牌"""
        async with self.lock:
            token = secrets.token_urlsafe(32)

            expires_at = None
            if expires_in:
                expires_at = datetime.now() + timedelta(seconds=expires_in)
            elif self.default_expiry:
                expires_at = datetime.now() + timedelta(seconds=self.default_expiry)

            auth_token = AuthToken(
                token=token,
                user_id=user_id,
                expires_at=expires_at,
                scopes=scopes or [],
                metadata=metadata or {},
            )

            self.tokens[token] = auth_token
            logger.info(f"✅ 创建令牌: {token[:8]}... (用户: {user_id})")

            return auth_token

    async def validate_token(self, token: str) -> AuthToken | None:
        """验证令牌"""
        async with self.lock:
            auth_token = self.tokens.get(token)
            if auth_token:
                # 检查令牌是否过期
                if auth_token.expires_at and datetime.now() > auth_token.expires_at:
                    await self.revoke_token(token)
                    return None
                return auth_token
            return None

    async def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        async with self.lock:
            if token in self.tokens:
                del self.tokens[token]
                logger.info(f"🚫 撤销令牌: {token[:8]}...")
                return True
            return False

    async def revoke_user_tokens(self, user_id: str) -> int:
        """撤销用户的所有令牌"""
        async with self.lock:
            user_tokens = [
                token for token, auth_token in self.tokens.items() if auth_token.user_id == user_id
            ]

            for token in user_tokens:
                del self.tokens[token]

            if user_tokens:
                logger.info(f"🚫 撤销用户令牌: {len(user_tokens)} 个 (用户: {user_id})")

            return len(user_tokens)


class AuthManager:
    """认证管理器主类"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False

        # 核心组件
        self.password_manager = PasswordManager(self.config.get("pepper"))
        self.session_manager = SessionManager(self.config.get("session_timeout", 3600))
        self.token_manager = TokenManager(self.config.get("token_timeout", 3600))

        # 用户存储
        self.users: dict[str, User] = {}

        # 角色权限映射
        self.role_permissions = {
            UserRole.ADMIN: {
                Permission.SYSTEM_READ,
                Permission.SYSTEM_WRITE,
                Permission.SYSTEM_ADMIN,
                Permission.AGENT_CREATE,
                Permission.AGENT_READ,
                Permission.AGENT_WRITE,
                Permission.AGENT_DELETE,
                Permission.DATA_READ,
                Permission.DATA_WRITE,
                Permission.DATA_DELETE,
                Permission.API_ACCESS,
                Permission.API_ADMIN,
            },
            UserRole.DEVELOPER: {
                Permission.AGENT_CREATE,
                Permission.AGENT_READ,
                Permission.AGENT_WRITE,
                Permission.DATA_READ,
                Permission.DATA_WRITE,
                Permission.API_ACCESS,
            },
            UserRole.USER: {Permission.AGENT_READ, Permission.DATA_READ, Permission.API_ACCESS},
            UserRole.GUEST: {Permission.AGENT_READ},
            UserRole.AGENT: {Permission.DATA_READ, Permission.DATA_WRITE, Permission.API_ACCESS},
        }

        # 启动清理任务
        self.cleanup_task = None

        logger.info("🔐 认证管理器创建")

    async def initialize(self):
        """初始化认证管理器"""
        if self.initialized:
            return

        logger.info("🚀 启动认证管理器")

        # 创建默认管理员用户
        await self.create_default_admin()

        # 启动清理任务
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.initialized = True
        logger.info("✅ 认证管理器启动完成")

    async def create_default_admin(self):
        """创建默认管理员用户"""
        admin_username = self.config.get("admin_username", "admin")
        admin_password = self.config.get("admin_password", "admin123")
        admin_email = self.config.get("admin_email", "admin@athena.ai")

        if not any(user.username == admin_username for user in self.users.values()):
            password_hash, salt = self.password_manager.hash_password(admin_password)

            admin_user = User(
                user_id=secrets.token_hex(8),
                username=admin_username,
                email=admin_email,
                password_hash=password_hash + ":" + salt,
                role=UserRole.ADMIN,
                permissions=self.role_permissions[UserRole.ADMIN],
            )

            self.users[admin_user.user_id] = admin_user
            logger.info(f"👤 创建默认管理员: {admin_username}")

    async def register_user(
        self, username: str, email: str, password: str, role: UserRole = UserRole.USER
    ) -> User | None:
        """注册用户"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        # 检查用户名是否已存在
        for user in self.users.values():
            if user.username == username or user.email == email:
                logger.warning(f"⚠️ 用户已存在: {username}/{email}")
                return None

        # 创建用户
        password_hash, salt = self.password_manager.hash_password(password)
        stored_hash = password_hash + ":" + salt

        user = User(
            user_id=secrets.token_hex(8),
            username=username,
            email=email,
            password_hash=stored_hash,
            role=role,
            permissions=self.role_permissions[role],
        )

        self.users[user.user_id] = user
        logger.info(f"👤 注册用户: {username} ({role.value})")

        return user

    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[tuple[User, Session]]:
        """用户认证"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        # 查找用户
        user = None
        for u in self.users.values():
            if u.username == username and u.is_active:
                user = u
                break

        if not user:
            logger.warning(f"⚠️ 用户不存在: {username}")
            return None

        # 验证密码
        try:
            password_hash, salt = user.password_hash.split(":")
            if not self.password_manager.verify_password(password, password_hash, salt):
                logger.warning(f"⚠️ 密码错误: {username}")
                return None
        except ValueError:
            logger.error(f"❌ 密码格式错误: {username}")
            return None

        # 更新最后登录时间
        user.last_login = datetime.now()

        # 创建会话
        session = await self.session_manager.create_session(
            user_id=user.user_id, ip_address=ip_address, user_agent=user_agent
        )

        logger.info(f"✅ 用户认证成功: {username}")
        return user, session

    async def login_with_token(
        self, token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None
    ) -> Optional[tuple[User, Session]]:
        """使用令牌登录"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        # 验证令牌
        auth_token = await self.token_manager.validate_token(token)
        if not auth_token:
            logger.warning(f"⚠️ 无效令牌: {token[:8]}...")
            return None

        # 查找用户
        user = self.users.get(auth_token.user_id)
        if not user or not user.is_active:
            logger.warning(f"⚠️ 用户不存在或已禁用: {auth_token.user_id}")
            return None

        # 创建会话
        session = await self.session_manager.create_session(
            user_id=user.user_id, ip_address=ip_address, user_agent=user_agent
        )

        logger.info(f"✅ 令牌登录成功: {user.username}")
        return user, session

    async def create_access_token(
        self, user_id: str, scopes: list[str]  | None = None, expires_in: Optional[int] = None
    ) -> AuthToken | None:
        """创建访问令牌"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        user = self.users.get(user_id)
        if not user or not user.is_active:
            return None

        return await self.token_manager.create_token(
            user_id=user_id, scopes=scopes, expires_in=expires_in
        )

    async def verify_permission(self, user_id: str, permission: Permission) -> bool:
        """验证用户权限"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False

        return permission in user.permissions

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False

        # 验证旧密码
        try:
            password_hash, salt = user.password_hash.split(":")
            if not self.password_manager.verify_password(old_password, password_hash, salt):
                return False
        except ValueError:
            return False

        # 设置新密码
        new_password_hash, new_salt = self.password_manager.hash_password(new_password)
        user.password_hash = new_password_hash + ":" + new_salt

        logger.info(f"🔒 密码修改成功: {user.username}")
        return True

    async def logout_user(self, session_id: str) -> bool:
        """用户登出"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        session = await self.session_manager.delete_session(session_id)
        return session

    async def logout_user_all_sessions(self, user_id: str) -> int:
        """登出用户所有会话"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        sessions = await self.session_manager.get_user_sessions(user_id)
        count = 0
        for session in sessions:
            if await self.session_manager.delete_session(session.session_id):
                count += 1

        # 同时撤销用户所有令牌
        await self.token_manager.revoke_user_tokens(user_id)

        logger.info(f"🚪 用户全量登出: {user_id} ({count} 个会话)")
        return count

    async def get_user_info(self, user_id: str) -> Optional[dict[str, Any]]:
        """获取用户信息"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        user = self.users.get(user_id)
        if not user:
            return None

        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_active": user.is_active,
            "metadata": user.metadata,
        }

    async def list_users(self, role: UserRole | None = None) -> list[dict[str, Any]]:
        """列出用户"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        users = []
        for user in self.users.values():
            if role is None or user.role == role:
                users.append(
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                        "created_at": user.created_at.isoformat(),
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                        "is_active": user.is_active,
                    }
                )

        return users

    async def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """更新用户角色"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        user = self.users.get(user_id)
        if not user:
            return False

        old_role = user.role
        user.role = new_role
        user.permissions = self.role_permissions[new_role]

        logger.info(f"🔄 用户角色更新: {user.username} {old_role.value} → {new_role.value}")
        return True

    async def deactivate_user(self, user_id: str) -> bool:
        """禁用用户"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        user = self.users.get(user_id)
        if not user:
            return False

        user.is_active = False

        # 登出用户所有会话
        await self.logout_user_all_sessions(user_id)

        logger.info(f"🚫 用户已禁用: {user.username}")
        return True

    async def _cleanup_loop(self):
        """清理循环"""
        while self.initialized:
            try:
                # 清理过期会话
                await self.session_manager.cleanup_expired_sessions()

                # 每小时清理一次
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"❌ 清理任务错误: {e}")
                await asyncio.sleep(3600)

    async def get_auth_stats(self) -> dict[str, Any]:
        """获取认证统计信息"""
        if not self.initialized:
            raise RuntimeError("认证管理器未初始化")

        active_sessions = len(self.session_manager.sessions)
        active_tokens = len(self.token_manager.tokens)

        role_counts = {}
        for user in self.users.values():
            role = user.role.value
            role_counts[role] = role_counts.get(role, 0) + 1

        return {
            "total_users": len(self.users),
            "active_sessions": active_sessions,
            "active_tokens": active_tokens,
            "role_distribution": role_counts,
            "timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self):
        """关闭认证管理器"""
        logger.info("🔄 关闭认证管理器")

        self.initialized = False

        # 取消清理任务
        if self.cleanup_task:
            self.cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.cleanup_task

        logger.info("✅ 认证管理器已关闭")


# 全局实例管理
_global_auth_manager: AuthManager | None = None


async def get_auth_manager_instance(config: Optional[dict[str, Any]] = None) -> AuthManager:
    """获取认证管理器实例"""
    global _global_auth_manager
    if _global_auth_manager is None:
        _global_auth_manager = AuthManager(config)
        await _global_auth_manager.initialize()
    return _global_auth_manager


async def shutdown_auth_manager():
    """关闭认证管理器实例"""
    global _global_auth_manager
    if _global_auth_manager:
        await _global_auth_manager.shutdown()
        _global_auth_manager = None


__all__ = [
    "AuthManager",
    "AuthToken",
    "PasswordManager",
    "Permission",
    "Session",
    "SessionManager",
    "TokenManager",
    "User",
    "UserRole",
    "get_auth_manager_instance",
    "shutdown_auth_manager",
]
