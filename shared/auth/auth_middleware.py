"""
Athena工作平台统一认证中间件
提供API认证、权限验证、速率限制等功能
"""

import hashlib
import ipaddress
import json
import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

import jwt
import redis
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# 导入安全配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "core"))
from core.security.env_config import get_jwt_secret, get_env_var, SecurityConfigError


class AuthConfig:
    """认证配置类"""

    # JWT配置 - 从环境变量读取
    try:
        JWT_SECRET_KEY = get_jwt_secret()
    except SecurityConfigError:
        # 如果环境变量未设置，记录警告并使用默认值（仅用于开发）
        logging.warning("JWT_SECRET_KEY环境变量未设置，使用默认值（不推荐用于生产环境）")
        JWT_SECRET_KEY = 'dev-only-change-in-production'

    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRE_MINUTES = 720  # 12小时

    # Redis配置 - 从环境变量读取
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')  # 可以为空

    # 速率限制配置
    RATE_LIMIT_REQUESTS = 1000  # 每小时请求数
    RATE_LIMIT_WINDOW = 3600    # 时间窗口（秒）

    # IP白名单（可选）
    ALLOWED_IPS: List[str] = []

    # API密钥配置
    API_KEYS: Dict[str, Dict[str, Any]] = {
        # 示例：服务间通信密钥
        'athena_internal_key': {
            'name': '内部服务密钥',
            'permissions': ['read', 'write', 'admin'],
            'services': ['*']
        }
    }


class JWTManager:
    """JWT令牌管理器"""

    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, payload: dict, expires_delta: timedelta | None = None) -> str:
        """创建JWT令牌"""
        to_encode = payload.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=AuthConfig.JWT_EXPIRE_MINUTES)

        to_encode.update({'exp': expire, 'iat': datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token已过期',
                headers={'WWW-Authenticate': 'Bearer'},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token无效',
                headers={'WWW-Authenticate': 'Bearer'},
            )


class RateLimiter:
    """速率限制器"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=AuthConfig.REDIS_HOST,
            port=AuthConfig.REDIS_PORT,
            db=AuthConfig.REDIS_DB,
            password=AuthConfig.REDIS_PASSWORD,
            decode_responses=True
        )

    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        """检查是否允许请求"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window)

        # 清理过期记录
        self.redis_client.zremrangebyscore(key, 0, window_start.timestamp())

        # 获取当前请求数
        current_requests = self.redis_client.zcard(key)

        if current_requests >= limit:
            # 获取最早请求的时间
            earliest = self.redis_client.zrange(key, 0, 0, withscores=True)
            reset_time = int(earliest[0][1] + window) if earliest else int(now.timestamp() + window)

            return False, {
                'limit': limit,
                'remaining': 0,
                'reset': reset_time,
                'retry_after': reset_time - int(now.timestamp())
            }

        # 记录当前请求
        self.redis_client.zadd(key, {str(now.timestamp()): now.timestamp()})
        self.redis_client.expire(key, window)

        return True, {
            'limit': limit,
            'remaining': limit - current_requests - 1,
            'reset': int(now.timestamp() + window)
        }


class IPWhitelist:
    """IP白名单管理器"""

    @staticmethod
    def is_allowed(ip: str, allowed_ips: List[str]) -> bool:
        """检查IP是否在白名单中"""
        if not allowed_ips:
            return True  # 如果没有配置白名单，允许所有IP

        try:
            ip_obj = ipaddress.ip_address(ip)
            for allowed_ip in allowed_ips:
                # 支持CIDR格式
                if '/' in allowed_ip:
                    if ip_obj in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                else:
                    if ip_obj == ipaddress.ip_address(allowed_ip):
                        return True
            return False
        except ValueError:
            return False


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/', '/health', '/docs', '/openapi.json', '/metrics']
        self.jwt_manager = JWTManager(AuthConfig.JWT_SECRET_KEY, AuthConfig.JWT_ALGORITHM)
        self.rate_limiter = RateLimiter()
        self.security = HTTPBearer()

    async def dispatch(self, request: Request, call_next):
        # 检查是否为排除路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # 获取客户端IP
        client_ip = request.client.host
        if 'x-forwarded-for' in request.headers:
            client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()

        # IP白名单检查
        if not IPWhitelist.is_allowed(client_ip, AuthConfig.ALLOWED_IPS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='IP地址不在白名单中'
            )

        # 速率限制检查
        rate_limit_key = f"rate_limit:{client_ip}:{request.url.path}"
        is_allowed, limit_info = self.rate_limiter.is_allowed(
            rate_limit_key,
            AuthConfig.RATE_LIMIT_REQUESTS,
            AuthConfig.RATE_LIMIT_WINDOW
        )

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail='请求过于频繁，请稍后再试',
                headers={
                    'X-RateLimit-Limit': str(limit_info['limit']),
                    'X-RateLimit-Remaining': str(limit_info['remaining']),
                    'X-RateLimit-Reset': str(limit_info['reset']),
                    'Retry-After': str(limit_info['retry_after'])
                }
            )

        # 认证检查
        try:
            # 尝试从Authorization头获取token
            authorization = request.headers.get('Authorization')
            if authorization:
                scheme, token = authorization.split()
                if scheme.lower() != 'bearer':
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='无效的认证方案'
                    )

                # 验证JWT令牌
                payload = self.jwt_manager.verify_token(token)
                request.state.user = payload
            else:
                # 尝试从查询参数获取API密钥
                api_key = request.query_params.get('api_key')
                if api_key and api_key in AuthConfig.API_KEYS:
                    request.state.user = {
                        'type': 'api_key',
                        'name': AuthConfig.API_KEYS[api_key]['name'],
                        'permissions': AuthConfig.API_KEYS[api_key]['permissions']
                    }
                else:
                    # 未提供认证信息
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='需要提供认证信息',
                        headers={'WWW-Authenticate': 'Bearer'}
                    )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='认证失败'
            )

        # 添加速率限制响应头
        response = await call_next(request)
        response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(limit_info['remaining'])
        response.headers['X-RateLimit-Reset'] = str(limit_info['reset'])

        return response


def require_permissions(permissions: List[str]) -> Any:
    """权限装饰器"""
    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # 尝试从kwargs获取request
                request = kwargs.get('request')

            if not request or not hasattr(request.state, 'user'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='未认证'
                )

            user_permissions = request.state.user.get('permissions', [])

            # 检查是否有所需权限
            if not all(perm in user_permissions for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='权限不足'
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 依赖注入函数
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    """获取当前用户"""
    jwt_manager = JWTManager(AuthConfig.JWT_SECRET_KEY, AuthConfig.JWT_ALGORITHM)
    payload = jwt_manager.verify_token(credentials.credentials)
    return payload


async def get_api_key(api_key: str = Security(HTTPBearer())):
    """API密钥认证"""
    if api_key not in AuthConfig.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='无效的API密钥'
        )
    return AuthConfig.API_KEYS[api_key]


# 创建默认的认证中间件实例
def create_auth_middleware(app, exclude_paths: Optional[List[str]] = None) -> None:
    """创建认证中间件"""
    return AuthenticationMiddleware(app, exclude_paths)


# CORS中间件配置
CORS_CONFIG = {
    'allow_origins': ['http://localhost:3000', 'http://localhost:8080'],  # 应该从环境变量读取
    'allow_credentials': True,
    'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    'allow_headers': ['*'],
    'expose_headers': ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset']
}


def setup_cors(app) -> None:
    """设置CORS"""
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        **CORS_CONFIG
    )