"""
认证中间件

支持多种认证方式：JWT Token、API Key、Bearer Token。
"""

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

import jwt
from fastapi import Request
from starlette.responses import Response

from .base import (
    AuthRequiredException,
    Middleware,
    MiddlewareContext,
)


class AuthMiddleware(Middleware):
    """认证中间件

    支持的认证方式：
    1. JWT Token (Authorization: Bearer <token>)
    2. API Key (X-API-Key: <key>)
    3. Session Cookie (session: <session_id>)

    配置选项：
    - jwt_secret: JWT 密钥（必需）
    - jwt_algorithm: JWT 算法，默认 HS256
    - jwt_expiry: JWT 过期时间（秒），默认 86400（24小时）
    - api_keys: 有效的 API Key 列表
    - skip_paths: 跳过认证的路径列表
    """

    def __init__(
        self,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        jwt_expiry: int = 86400,
        api_keys: list[str] | None = None,
        skip_paths: list[str] | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._jwt_expiry = jwt_expiry
        self._api_keys = set(api_keys or [])
        self._skip_paths = set(skip_paths or [])

        # 添加默认跳过路径
        self._skip_paths.update([
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/api/v1/auth/login",
        ])

    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """处理认证"""

        # 检查是否跳过认证
        if self._should_skip_auth(ctx.request.url.path):
            return await call_next(ctx)

        # 尝试各种认证方式
        user_id = await self._authenticate(ctx.request)

        if user_id is None:
            raise AuthRequiredException(
                "Invalid or missing authentication credentials"
            )

        # 认证成功，将用户信息存入上下文
        ctx.user_id = user_id
        ctx.set("authenticated", True)
        ctx.set("auth_method", self._get_auth_method(ctx.request))

        return await call_next(ctx)

    def _should_skip_auth(self, path: str) -> bool:
        """检查是否跳过认证"""
        for skip_path in self._skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    async def _authenticate(self, request: Request) -> str | None:
        """尝试认证请求"""

        # 1. 尝试 Bearer Token (JWT)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer "
            return self._verify_jwt_token(token)

        # 2. 尝试 API Key
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return self._verify_api_key(api_key)

        # 3. 尝试 Session Cookie
        session_id = request.cookies.get("session")
        if session_id:
            return await self._verify_session(session_id)

        # 认证失败
        return None

    def _verify_jwt_token(self, token: str) -> str | None:
        """验证 JWT Token"""
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm]
            )
            return payload.get("sub")  # subject (user_id)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def _verify_api_key(self, api_key: str) -> str | None:
        """验证 API Key

        使用哈希值作为用户标识，避免返回固定的用户名。
        实际应用中应该查询数据库或外部服务验证。
        """
        if api_key in self._api_keys:
            # 使用 API Key 的哈希值生成用户标识
            # 这样不同的 API Key 会产生不同的用户标识
            import hashlib
            import warnings

            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            user_id = f"api_user_{key_hash}"

            # 发出警告，提示需要实现完整的验证逻辑
            warnings.warn(
                "API Key verification is simplified. "
                "Implement full database verification for production.",
                DeprecationWarning,
                stacklevel=2
            )

            return user_id
        return None

    async def _verify_session(self, session_id: str) -> str | None:
        """验证 Session"""
        # TODO: 从 Redis 或数据库验证 session
        # 这里简化实现
        return f"session_{session_id}"

    def _get_auth_method(self, request: Request) -> str:
        """获取认证方式"""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return "jwt"
        if request.headers.get("X-API-Key"):
            return "api_key"
        if request.cookies.get("session"):
            return "session"
        return "unknown"

    def create_jwt_token(self, user_id: str, **extra_claims) -> str:
        """创建 JWT Token

        Args:
            user_id: 用户ID
            **extra_claims: 额外的声明

        Returns:
            str: JWT Token
        """
        payload = {
            "sub": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=self._jwt_expiry),
            **extra_claims
        }
        return jwt.encode(
            payload,
            self._jwt_secret,
            algorithm=self._jwt_algorithm
        )

    def add_api_key(self, api_key: str) -> None:
        """添加 API Key"""
        self._api_keys.add(api_key)

    def remove_api_key(self, api_key: str) -> bool:
        """移除 API Key"""
        return api_key in self._api_keys and self._api_keys.discard(api_key) is not None

    def add_skip_path(self, path: str) -> None:
        """添加跳过认证的路径"""
        self._skip_paths.add(path)

    def remove_skip_path(self, path: str) -> bool:
        """移除跳过认证的路径"""
        return path in self._skip_paths and self._skip_paths.discard(path) is not None
