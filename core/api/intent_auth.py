"""
意图识别服务 - 认证和安全模块

提供JWT认证、API密钥认证、速率限制等安全功能。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

import hashlib
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.api_key import APIKeyHeader

# 配置日志
logger = logging.getLogger("api.intent_auth")


# ========================================================================
# 配置
# ========================================================================

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# API密钥配置
API_KEY_NAME = "X-API-Key"
API_KEY_HEADER = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


# ========================================================================
# API密钥验证
# ========================================================================


def get_valid_api_keys() -> dict[str, str]:
    """
    获取有效的API密钥列表

    在运行时从环境变量读取,支持密钥更新。

    Returns:
        密钥到用户ID的映射字典
    """
    # 从环境变量读取密钥(支持逗号分隔的多个密钥)
    api_key_str = os.getenv("INTENT_API_KEY", "sk-intent-test-key-2025")
    api_keys = [key.strip() for key in api_key_str.split(",") if key.strip()]

    # 构建密钥映射
    valid_keys = {}
    for key in api_keys:
        # 默认使用"default_user",可以在密钥中指定用户(格式:key:user_id)
        if ":" in key:
            key_value, user_id = key.split(":", 1)
            valid_keys[key_value] = user_id
        else:
            valid_keys[key] = "default_user"

    return valid_keys


# 测试API密钥(生产环境应从数据库读取)
VALID_API_KEYS = {}  # 将在运行时动态填充


# ========================================================================
# JWT工具
# ========================================================================


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    创建访问令牌

    Args:
        data: 令牌数据
        expires_delta: 过期时间增量

    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码访问令牌

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的令牌数据

    Raises:
        HTTPException: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ========================================================================
# API密钥验证
# ========================================================================


def verify_api_key(api_key: str) -> str | None:
    """
    验证API密钥

    Args:
        api_key: API密钥字符串(可能包含:user_id后缀)

    Returns:
        用户ID,如果验证失败返回None
    """
    # 运行时从环境变量读取
    valid_keys = get_valid_api_keys()

    # 如果提供的密钥包含:user_id后缀,提取密钥部分
    key_to_check = api_key
    if ":" in api_key:
        key_to_check = api_key.split(":")[0]

    return valid_keys.get(key_to_check)


def generate_api_key(user_id: str, expire_days: int | None = None) -> str:
    """
    生成API密钥

    注意: 由于密钥现在从环境变量读取,生成的密钥需要添加到环境变量中才能使用。

    Args:
        user_id: 用户ID
        expire_days: 过期天数(当前未实现)

    Returns:
        API密钥字符串
    """
    # 生成密钥前缀
    prefix = "sk-intent"

    # 生成随机密钥
    random_part = secrets.token_urlsafe(32)

    # 组合密钥(格式:key:user_id)
    api_key = f"{prefix}-{random_part}:{user_id}"

    logger.info(f"为用户 {user_id} 生成API密钥: {api_key[:40}...")
    logger.info(f"请将以下内容添加到环境变量 INTENT_API_KEY: {api_key}")

    return api_key


# ========================================================================
# 认证依赖
# ========================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    api_key: str = Security(API_KEY_HEADER),
) -> str:
    """
    获取当前用户

    支持JWT和API密钥两种认证方式。

    Args:
        credentials: HTTP Bearer凭据
        api_key: API密钥

    Returns:
        用户ID

    Raises:
        HTTPException: 认证失败
    """
    # 优先使用API密钥认证
    if api_key:
        user_id = verify_api_key(api_key)
        if user_id:
            return user_id
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的API密钥")

    # 使用JWT认证
    if credentials:
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id:
            return user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="缺少有效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Security(security),
    api_key: str = Security(API_KEY_HEADER),
) -> str | None:
    """
    获取当前用户(可选)

    如果没有提供认证凭据,返回None而不是抛出异常。

    Args:
        credentials: HTTP Bearer凭据
        api_key: API密钥

    Returns:
        用户ID或None
    """
    try:
        return await get_current_user(credentials, api_key)
    except HTTPException:
        return None


# ========================================================================
# 速率限制
# ========================================================================


class RateLimiter:
    """
    速率限制器

    基于内存的简单速率限制实现。
    生产环境建议使用Redis。
    """

    def __init__(self, requests_per_minute: int = 100, requests_per_hour: int = 1000):
        """
        初始化速率限制器

        Args:
            requests_per_minute: 每分钟请求数限制
            requests_per_hour: 每小时请求数限制
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # 存储请求记录: {user_id: [(timestamp, count), ...]}
        self._requests: dict[str, list[tuple]] = {}

        # 清理过期记录的间隔
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600  # 1小时

    def _cleanup_old_records(self) -> Any:
        """清理过期的请求记录"""
        now = time.time()

        # 距离上次清理超过间隔时间才执行
        if now - self._last_cleanup < self._cleanup_interval:
            return

        cutoff_time = now - 3600  # 保留1小时内的记录

        for user_id in list(self._requests.keys()):
            # 过滤掉过期的记录
            self._requests[user_id] = [
                (timestamp, count)
                for timestamp, count in self._requests[user_id]
                if timestamp > cutoff_time
            ]

            # 如果用户没有记录了,删除该用户
            if not self._requests[user_id]:
                del self._requests[user_id]

        self._last_cleanup = now

    def check_rate_limit(self, user_id: str) -> tuple[bool, str | None]:
        """
        检查速率限制

        Args:
            user_id: 用户ID

        Returns:
            (是否允许, 拒绝原因)
        """
        now = time.time()
        self._cleanup_old_records()

        # 初始化用户记录
        if user_id not in self._requests:
            self._requests[user_id] = []

        user_requests = self._requests[user_id]

        # 计算最近1分钟和1小时的请求数
        minute_ago = now - 60
        hour_ago = now - 3600

        minute_count = sum(count for timestamp, count in user_requests if timestamp > minute_ago)
        hour_count = sum(count for timestamp, count in user_requests if timestamp > hour_ago)

        # 检查限制
        if minute_count >= self.requests_per_minute:
            return False, f"超过每分钟速率限制: {self.requests_per_minute} 请求/分钟"

        if hour_count >= self.requests_per_hour:
            return False, f"超过每小时速率限制: {self.requests_per_hour} 请求/小时"

        # 记录本次请求
        user_requests.append((now, 1))

        return True, None


# 全局限速限制器实例
rate_limiter = RateLimiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", 100)),
    requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", 1000)),
)


async def check_rate_limit_depends(user_id: str = Security(get_current_user)):
    """
    速率限制依赖函数

    用于FastAPI的Depends。

    Args:
        user_id: 用户ID

    Raises:
        HTTPException: 超过速率限制
    """
    # 默认用户ID(用于无认证场景)
    if not user_id:
        user_id = "anonymous"

    allowed, reason = rate_limiter.check_rate_limit(user_id)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason,
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(rate_limiter.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 60),
            },
        )


# ========================================================================
# 装饰器
# ========================================================================


def require_auth(permission: Optional[str | None = None) -> Any:
    """
    需要认证的装饰器

    Args:
        permission: 所需权限

    Returns:
        装饰器函数
    """

    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, current_user: str = Security(get_current_user), **kwargs):
            # 这里可以添加权限检查逻辑
            if permission:
                # TODO: 实现权限检查
                pass

            # 将current_user注入到kwargs中
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


# ========================================================================
# 辅助函数
# ========================================================================


def hash_password(password: str) -> str:
    """
    哈希密码

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    # 在生产环境应使用bcrypt或argon2
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        password: 明文密码
        hashed_password: 哈希密码

    Returns:
        是否匹配
    """
    return hash_password(password) == hashed_password


# ========================================================================
# 导出
# ========================================================================

__all__ = [
    # 速率限制
    "RateLimiter",
    "check_rate_limit_depends",
    # JWT
    "create_access_token",
    "decode_access_token",
    "generate_api_key",
    # 认证依赖
    "get_current_user",
    "get_current_user_optional",
    # 辅助
    "hash_password",
    "rate_limiter",
    # 装饰器
    "require_auth",
    # API密钥
    "verify_api_key",
    "verify_password",
]
