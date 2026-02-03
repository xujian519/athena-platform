#!/usr/bin/env python3
"""
CSRF保护中间件
CSRF Protection Middleware

版本: 1.0.0
功能:
- CSRF Token生成和验证
- 基于Cookie和Header的Token传递
- Token过期管理
- 安全配置
"""

import logging
import secrets
from collections.abc import Callable
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class CSRFProtection:
    """
    CSRF保护中间件

    防止跨站请求伪造攻击
    """

    def __init__(
        self,
        secret: str | None = None,
        token_age: int = 3600,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        secure: bool = False,
        httponly: bool = False,
        samesite: str = "lax",
        exclude_paths: set[str] | None = None,
    ):
        """
        初始化CSRF保护

        Args:
            secret: 用于签名token的密钥
            token_age: token有效期(秒)
            cookie_name: cookie名称
            header_name: header名称
            secure: 是否仅HTTPS
            httponly: 是否httpOnly
            samesite: SameSite属性
            exclude_paths: 排除的路径
        """
        self.secret = secret or secrets.token_urlsafe(32)
        self.token_age = token_age
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite
        self.exclude_paths = exclude_paths or {"/health", "/docs", "/openapi.json", "/metrics"}

        logger.info(f"✅ CSRF保护已启用: {cookie_name}/{header_name}")

    def generate_token(self, request: Request) -> str:
        """
        生成CSRF token

        Args:
            request: FastAPI请求对象

        Returns:
            CSRF token
        """
        # 生成随机token
        token = secrets.token_urlsafe(32)

        # 创建签名
        timestamp = int(datetime.now().timestamp())
        message = f"{token}:{timestamp}"

        # 使用HMAC签名
        import hashlib
        import hmac

        signature = hmac.new(self.secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        # 返回 token:timestamp:signature
        return f"{message}:{signature}"

    def validate_token(self, request: Request) -> bool:
        """
        验证CSRF token

        Args:
            request: FastAPI请求对象

        Returns:
            是否有效
        """
        # 从header获取token
        token = request.headers.get(self.header_name)
        if not token:
            return False

        # 验证格式
        parts = token.split(":")
        if len(parts) != 3:
            return False

        csrf_token, timestamp, signature = parts

        # 验证签名
        import hashlib
        import hmac

        message = f"{csrf_token}:{timestamp}"
        expected_signature = hmac.new(
            self.secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("⚠️ CSRF签名验证失败")
            return False

        # 验证时间戳
        try:
            token_time = datetime.fromtimestamp(float(timestamp))
            if datetime.now() - token_time > timedelta(seconds=self.token_age):
                logger.warning("⚠️ CSRF token已过期")
                return False
        except (ValueError, OSError):
            return False

        return True

    async def __call__(self, request: Request, call_next: Callable):
        """
        处理请求

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件/路由

        Returns:
            响应
        """
        # 检查是否需要CSRF保护
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            # 安全方法不需要验证
            return await call_next(request)

        # 检查是否排除路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # 检查Content-Type
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            # 只保护JSON API请求
            return await call_next(request)

        # 验证CSRF token
        if not self.validate_token(request):
            logger.warning(f"🚫 CSRF验证失败: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF验证失败", "message": "无效或过期的CSRF token"},
            )

        return await call_next(request)


def get_csrf_token(request: Request) -> str | None:
    """
    从请求中获取CSRF token

    Args:
        request: FastAPI请求对象

    Returns:
        CSRF token或None
    """
    csrf_config = request.app.state.csrf_config
    if csrf_config:
        return csrf_config.generate_token(request)
    return None


# 便捷装饰器
def csrf_protect(header_name: str = "X-CSRF-Token"):
    """
    CSRF保护装饰器

    Args:
        header_name: header名称

    Returns:
        装饰器
    """

    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            csrf_config = request.app.state.csrf_config
            if csrf_config and request.method not in ["GET", "HEAD", "OPTIONS"]:
                if not csrf_config.validate_token(request):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="CSRF验证失败"
                    )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
