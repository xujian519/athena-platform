from __future__ import annotations
"""
API认证系统
提供JWT认证、API密钥管理和访问控制
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import aioredis
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.logging_config import setup_logging
from core.security.env_config import SecurityConfigError, get_jwt_secret

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class TokenType(Enum):
    """令牌类型"""

    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class UserRole(Enum):
    """用户角色"""

    ADMIN = "admin"
    DEVELOPER = "developer"
    AI_SERVICE = "ai_service"
    USER = "user"
    GUEST = "guest"


@dataclass
class User:
    """用户信息"""

    id: str
    username: str
    email: str
    role: UserRole
    permissions: list[str]
    created_at: datetime
    last_login: datetime | None = None
    active: bool = True


@dataclass
class APIKey:
    """API密钥"""

    id: str
    key_id: str
    key_hash: str
    user_id: str
    name: str
    permissions: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    last_used: datetime | None = None
    active: bool = True


@dataclass
class TokenInfo:
    """令牌信息"""

    token: str
    token_type: TokenType
    expires_at: datetime
    user_id: str
    scope: list[str]


class AuthenticationConfig:
    """认证配置"""

    def __init__(self):
        # 从环境变量读取JWT密钥，确保安全性
        try:
            self.jwt_secret = get_jwt_secret()
        except SecurityConfigError as e:
            logger.warning(f"JWT密钥配置错误: {e}，使用默认值（仅用于开发环境）")
            self.jwt_secret = "dev-only-secret-change-in-production"

        self.jwt_algorithm: str = "HS256"
        self.access_token_expire_minutes: int = 30
        self.refresh_token_expire_days: int = 7
        self.api_key_length: int = 32
        self.redis_host: str = "localhost"
        self.redis_port: int = 6379
        self.redis_db: int = 1
        self.password_min_length: int = 8
        self.max_login_attempts: int = 5
        self.lockout_duration_minutes: int = 15


class PasswordManager:
    """密码管理器"""

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def generate_password(length: int = 12) -> str:
        """生成随机密码"""
        alphabet = "abcdefghijklmnopqrstuvwxyz_abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))


class TokenManager:
    """令牌管理器"""

    def __init__(self, config: AuthenticationConfig):
        self.config = config

    def create_access_token(
        self, user: User, additional_claims: dict | None = None
    ) -> TokenInfo:
        """创建访问令牌"""
        expires_at = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)

        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "permissions": user.permissions,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "type": TokenType.ACCESS.value,
            **(additional_claims or {}),
        }

        token = jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

        return TokenInfo(
            token=token,
            token_type=TokenType.ACCESS,
            expires_at=expires_at,
            user_id=user.id,
            scope=user.permissions,
        )

    def create_refresh_token(self, user: User) -> TokenInfo:
        """创建刷新令牌"""
        expires_at = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)

        payload = {
            "sub": user.id,
            "type": TokenType.REFRESH.value,
            "exp": expires_at,
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

        return TokenInfo(
            token=token,
            token_type=TokenType.REFRESH,
            expires_at=expires_at,
            user_id=user.id,
            scope=[],
        )

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效令牌")
            return None

    def refresh_access_token(self, refresh_token: str) -> TokenInfo | None:
        """刷新访问令牌"""
        payload = self.verify_token(refresh_token)

        if not payload or payload.get("type") != TokenType.REFRESH.value:
            return None

        # 这里应该从数据库加载用户信息
        # 简化实现,实际应用中需要查询数据库
        user_id = payload.get("sub")
        mock_user = User(
            id=user_id,
            username="mock_user",
            email="mock@example.com",
            role=UserRole.USER,
            permissions=["read"],
            created_at=datetime.utcnow(),
        )

        return self.create_access_token(mock_user)


class APIKeyManager:
    """API密钥管理器"""

    def __init__(self, config: AuthenticationConfig):
        self.config = config
        self.redis: aioredis.Redis | None = None

    async def connect_redis(self):
        """连接Redis"""
        try:
            self.redis = aioredis.from_url(
                f"redis://{self.config.redis_host}:{self.config.redis_port}/{self.config.redis_db}",
                decode_responses=True,
            )
            await self.redis.ping()
            logger.info("API密钥管理器连接Redis成功")
        except Exception as e:
            logger.error(f"连接Redis失败: {e}")

    async def create_api_key(
        self, user_id: str, name: str, permissions: list[str], expires_in_days: int | None = None
    ) -> str:
        """创建API密钥"""
        # 生成密钥
        key_id = secrets.token_urlsafe(16)
        raw_key = secrets.token_urlsafe(self.config.api_key_length)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # 创建API密钥对象
        api_key = APIKey(
            id=key_id,
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            permissions=permissions,
            created_at=datetime.utcnow(),
            expires_at=(
                datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
            ),
        )

        # 存储到Redis
        if self.redis:
            key_data = {
                "key_hash": key_hash,
                "user_id": user_id,
                "name": name,
                "permissions": ",".join(permissions),
                "created_at": api_key.created_at.isoformat(),
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else "",
                "active": "true",
            }

            await self.redis.hset(f"api_key:{key_id}", mapping=key_data)
            if api_key.expires_at:
                await self.redis.expireat(f"api_key:{key_id}", int(api_key.expires_at.timestamp()))

        # 返回完整密钥(只显示一次)
        full_key = f"{key_id}.{raw_key}"
        logger.info(f"创建API密钥: {key_id} for user {user_id}")

        return full_key

    async def verify_api_key(self, api_key: str) -> APIKey | None:
        """验证API密钥"""
        if not self.redis:
            return None

        try:
            # 解析密钥
            key_id, raw_key = api_key.split(".", 1)
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            # 从Redis获取密钥信息
            key_data = await self.redis.hgetall(f"api_key:{key_id}")

            if not key_data:
                return None

            # 验证哈希
            if key_data["key_hash"] != key_hash:
                return None

            # 检查是否过期
            if key_data.get("expires_at"):
                expires_at = datetime.fromisoformat(key_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    return None

            # 检查是否激活
            if key_data.get("active", "true") != "true":
                return None

            # 更新最后使用时间
            await self.redis.hset(f"api_key:{key_id}', 'last_used", datetime.utcnow().isoformat())

            # 返回API密钥对象
            return APIKey(
                id=key_id,
                key_id=key_id,
                key_hash=key_hash,
                user_id=key_data["user_id"],
                name=key_data["name"],
                permissions=key_data["permissions"].split(","),
                created_at=datetime.fromisoformat(key_data["created_at"]),
                expires_at=(
                    datetime.fromisoformat(key_data["expires_at"])
                    if key_data.get("expires_at")
                    else None
                ),
                last_used=(
                    datetime.fromisoformat(key_data["last_used"])
                    if key_data.get("last_used")
                    else None
                ),
            )

        except Exception as e:
            logger.error(f"API密钥验证错误: {e}")
            return None

    async def revoke_api_key(self, key_id: str) -> bool:
        """撤销API密钥"""
        if not self.redis:
            return False

        try:
            await self.redis.hset(f"api_key:{key_id}', 'active', 'false")
            logger.info(f"撤销API密钥: {key_id}")
            return True
        except Exception as e:
            logger.error(f"撤销API密钥失败: {e}")
            return False

    async def list_user_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """列出用户的API密钥"""
        if not self.redis:
            return []

        try:
            # 搜索用户的所有密钥
            pattern = "api_key:*"
            keys = await self.redis.keys(pattern)

            user_keys = []
            for key in keys:
                key_data = await self.redis.hgetall(key)
                if key_data.get("user_id") == user_id:
                    # 不返回密钥哈希
                    safe_data = {k: v for k, v in key_data.items() if k != "key_hash"}
                    user_keys.append(safe_data)

            return user_keys

        except Exception as e:
            logger.error(f"列出API密钥失败: {e}")
            return []


class AuthenticationService:
    """认证服务"""

    def __init__(self, config: AuthenticationConfig | None = None):
        self.config = config or AuthenticationConfig()
        self.token_manager = TokenManager(self.config)
        self.api_key_manager = APIKeyManager(self.config)
        self.login_attempts: dict[str, int] = {}
        self.locked_accounts: dict[str, datetime] = {}

        # Mock用户数据(实际应用中应该使用数据库)
        self.users: dict[str, dict] = {
            "admin": {
                "id": "1",
                "username": "admin",
                "password_hash": PasswordManager.hash_password("admin123"),
                "email": "admin@example.com",
                "role": UserRole.ADMIN,
                "permissions": ["read", "write", "delete", "admin"],
                "created_at": datetime.utcnow(),
            },
            "athena": {
                "id": "2",
                "username": "athena",
                "password_hash": PasswordManager.hash_password("athena123"),
                "email": "athena@example.com",
                "role": UserRole.AI_SERVICE,
                "permissions": ["read", "write", "analyze"],
                "created_at": datetime.utcnow(),
            },
            "xiaonuo": {
                "id": "3",
                "username": "xiaonuo",
                "password_hash": PasswordManager.hash_password("xiaonuo123"),
                "email": "xiaonuo@example.com",
                "role": UserRole.AI_SERVICE,
                "permissions": ["read", "write", "implement"],
                "created_at": datetime.utcnow(),
            },
        }

    async def initialize(self):
        """初始化认证服务"""
        await self.api_key_manager.connect_redis()

    def is_account_locked(self, username: str) -> bool:
        """检查账户是否被锁定"""
        if username in self.locked_accounts:
            lock_time = self.locked_accounts[username]
            if datetime.utcnow() - lock_time < timedelta(
                minutes=self.config.lockout_duration_minutes
            ):
                return True
            else:
                del self.locked_accounts[username]
                del self.login_attempts[username]
        return False

    def record_login_attempt(self, username: str, success: bool) -> Any:
        """记录登录尝试"""
        if success:
            # 清除失败记录
            self.login_attempts.pop(username, None)
            self.locked_accounts.pop(username, None)
        else:
            # 增加失败计数
            self.login_attempts[username] = self.login_attempts.get(username, 0) + 1

            # 检查是否需要锁定账户
            if self.login_attempts[username] >= self.config.max_login_attempts:
                self.locked_accounts[username] = datetime.utcnow()
                logger.warning(f"账户已锁定: {username}")

    async def authenticate(self, username: str, password: str) -> User | None:
        """用户认证"""
        # 检查账户是否被锁定
        if self.is_account_locked(username):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED, detail="账户已被锁定,请稍后再试"
            )

        # 获取用户信息
        user_data = self.users.get(username)
        if not user_data:
            self.record_login_attempt(username, False)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

        # 验证密码
        if not PasswordManager.verify_password(password, user_data["password_hash"]):
            self.record_login_attempt(username, False)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

        # 认证成功
        self.record_login_attempt(username, True)

        # 创建用户对象
        user = User(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"],
            permissions=user_data["permissions"],
            created_at=user_data["created_at"],
            last_login=datetime.utcnow(),
        )

        return user

    async def login(self, username: str, password: str) -> dict[str, Any]:
        """用户登录"""
        user = await self.authenticate(username, password)

        # 创建令牌
        access_token = self.token_manager.create_access_token(user)
        refresh_token = self.token_manager.create_refresh_token(user)

        return {
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
            "token_type": "bearer",
            "expires_in": self.config.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role.value,
                "permissions": user.permissions,
            },
        }

    async def refresh_token(self, refresh_token: str) -> str | None:
        """刷新访问令牌"""
        new_token = self.token_manager.refresh_access_token(refresh_token)
        return new_token.token if new_token else None

    def verify_jwt_token(self, token: str) -> dict[str, Any] | None:
        """验证JWT令牌"""
        return self.token_manager.verify_token(token)

    async def verify_api_key(self, api_key: str) -> APIKey | None:
        """验证API密钥"""
        return await self.api_key_manager.verify_api_key(api_key)

    async def create_api_key(
        self, user_id: str, name: str, permissions: list[str], expires_in_days: int | None = None
    ) -> str:
        """创建API密钥"""
        return await self.api_key_manager.create_api_key(
            user_id, name, permissions, expires_in_days
        )

    async def revoke_api_key(self, key_id: str) -> bool:
        """撤销API密钥"""
        return await self.api_key_manager.revoke_api_key(key_id)


# FastAPI依赖
security = HTTPBearer()

# 全局认证服务实例
auth_service = AuthenticationService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """获取当前用户"""
    payload = auth_service.verify_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def require_permission(permission: str):
    """权限检查装饰器工厂"""

    async def check_permission(current_user: dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"需要权限: {permission}"
            )
        return current_user

    return check_permission


async def api_key_auth(api_key: str) -> APIKey | None:
    """API密钥认证"""
    return await auth_service.verify_api_key(api_key)


# 初始化认证服务
async def initialize_auth():
    """初始化认证服务"""
    await auth_service.initialize()
    logger.info("认证服务初始化完成")
