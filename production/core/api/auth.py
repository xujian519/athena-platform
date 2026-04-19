#!/usr/bin/env python3
from __future__ import annotations
"""
API认证和安全模块
API Authentication and Security Module

提供API密钥认证、JWT令牌、速率限制等安全功能

作者: Athena AI系统
创建时间: 2025-12-19
版本: 1.0.0
"""

import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # 突发请求容量


@dataclass
class RateLimitStats:
    """速率限制统计"""

    requests: list[float] = field(default_factory=list)
    blocked_count: int = 0
    last_request_time: float | None = None
    total_requests: int = 0


class APIKeyAuth:
    """API密钥认证器"""

    def __init__(self):
        """初始化API密钥认证器"""
        # 从环境变量加载有效的API密钥
        self._valid_keys: set[str] = self._load_api_keys()

    def _load_api_keys(self) -> set[str]:
        """从环境变量加载有效的API密钥"""
        keys_string = os.getenv("ATHENA_API_KEYS", "")
        if not keys_string:
            logger.warning("⚠️ 未配置ATHENA_API_KEYS环境变量,API认证将被禁用")
            return set()

        keys = {k.strip() for k in keys_string.split(",") if k.strip()}
        logger.info(f"✅ 已加载 {len(keys)} 个有效的API密钥")
        return keys

    def verify_key(self, api_key: str) -> bool:
        """
        验证API密钥

        Args:
            api_key: 要验证的API密钥

        Returns:
            密钥是否有效
        """
        if not self._valid_keys:
            # 如果没有配置密钥,则禁用认证(用于开发环境)
            return True

        # 使用HMAC进行安全比较,防止时序攻击
        for valid_key in self._valid_keys:
            try:
                if hmac.compare_digest(api_key.encode(), valid_key.encode()):
                    return True
            except Exception:
                continue

        return False

    def reload_keys(self) -> Any:
        """重新加载API密钥"""
        self._valid_keys = self._load_api_keys()
        logger.info("🔄 API密钥已重新加载")


class RateLimiter:
    """速率限制器(滑动窗口算法)"""

    def __init__(self, config: RateLimitConfig | None = None):
        """
        初始化速率限制器

        Args:
            config: 速率限制配置
        """
        self.config = config or RateLimitConfig()
        # 客户端标识符 -> 速率限制统计
        self._client_stats: dict[str, RateLimitStats] = defaultdict(lambda: RateLimitStats())

    def _get_client_identifier(self, request: Request) -> str:
        """
        获取客户端标识符

        Args:
            request: FastAPI请求对象

        Returns:
            客户端标识符
        """
        # 优先使用API密钥,然后使用IP地址
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            # 对API密钥进行哈希以保护隐私
            return hashlib.sha256(api_key.encode()).hexdigest()[:16]

        # 使用客户端IP地址
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, stats: RateLimitStats, cutoff_time: float) -> Any:
        """
        清理过期的请求记录

        Args:
            stats: 速率限制统计
            cutoff_time: 截止时间戳
        """
        stats.requests = [t for t in stats.requests if t > cutoff_time]

    def check_rate_limit(
        self, request: Request, raise_exception: bool = True
    ) -> tuple[bool, str | None]:
        """
        检查是否超过速率限制

        Args:
            request: FastAPI请求对象
            raise_exception: 是否在超过限制时抛出异常

        Returns:
            (是否允许, 错误消息)
        """
        client_id = self._get_client_identifier(request)
        current_time = time.time()

        stats = self._client_stats[client_id]
        stats.total_requests += 1
        stats.last_request_time = current_time

        # 清理过期的请求记录(超过1小时)
        self._cleanup_old_requests(stats, current_time - 3600)

        # 检查每分钟限制
        minute_ago = current_time - 60
        recent_requests = [t for t in stats.requests if t > minute_ago]

        if len(recent_requests) >= self.config.requests_per_minute:
            stats.blocked_count += 1
            message = (
                f"速率限制: 每分钟最多 {self.config.requests_per_minute} 个请求。"
                f"请在 {int(60 - (current_time - recent_requests[0]))} 秒后重试。"
            )
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=message,
                )
            return False, message

        # 检查每小时限制
        hour_ago = current_time - 3600
        hour_requests = [t for t in stats.requests if t > hour_ago]

        if len(hour_requests) >= self.config.requests_per_hour:
            stats.blocked_count += 1
            message = (
                f"速率限制: 每小时最多 {self.config.requests_per_hour} 个请求。"
                f"请在 {int(3600 - (current_time - hour_requests[0]))} 秒后重试。"
            )
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=message,
                )
            return False, message

        # 记录此次请求
        stats.requests.append(current_time)
        return True, None

    def get_stats(self) -> dict[str, Any]:
        """
        获取速率限制统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_clients": len(self._client_stats),
            "total_requests": sum(s.total_requests for s in self._client_stats.values()),
            "total_blocked": sum(s.blocked_count for s in self._client_stats.values()),
            "config": {
                "requests_per_minute": self.config.requests_per_minute,
                "requests_per_hour": self.config.requests_per_hour,
                "burst_size": self.config.burst_size,
            },
        }

    def reset_client(self, client_id: str) -> Any:
        """
        重置指定客户端的速率限制

        Args:
            client_id: 客户端标识符
        """
        if client_id in self._client_stats:
            del self._client_stats[client_id]
            logger.info(f"✅ 已重置客户端 '{client_id}' 的速率限制")

    def clear_all(self) -> None:
        """清除所有速率限制统计"""
        self._client_stats.clear()
        logger.info("✅ 已清除所有速率限制统计")


class SecurityMiddleware:
    """安全中间件(组合认证和速率限制)"""

    def __init__(
        self,
        enable_auth: bool = True,
        enable_rate_limit: bool = True,
        rate_limit_config: RateLimitConfig | None = None,
    ):
        """
        初始化安全中间件

        Args:
            enable_auth: 是否启用API密钥认证
            enable_rate_limit: 是否启用速率限制
            rate_limit_config: 速率限制配置
        """
        self.enable_auth = enable_auth
        self.enable_rate_limit = enable_rate_limit

        # 初始化认证器
        self.auth = APIKeyAuth() if enable_auth else None

        # 初始化速率限制器
        self.rate_limiter = RateLimiter(rate_limit_config) if enable_rate_limit else None

        logger.info(
            f"✅ 安全中间件初始化完成 " f"(认证: {enable_auth}, 速率限制: {enable_rate_limit})"
        )

    async def verify_request(self, request: Request, api_key: str | None = None) -> None:
        """
        验证请求(认证 + 速率限制)

        Args:
            request: FastAPI请求对象
            api_key: API密钥(从请求头或查询参数中提取)

        Raises:
            HTTPException: 验证失败时抛出
        """
        # API密钥认证
        if self.enable_auth and self.auth:
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="缺少API密钥,请在请求头中提供 X-API-Key",
                )

            if not self.auth.verify_key(api_key):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的API密钥",
                )

        # 速率限制
        if self.enable_rate_limit and self.rate_limiter:
            self.rate_limiter.check_rate_limit(request, raise_exception=True)

    def get_security_stats(self) -> dict[str, Any]:
        """
        获取安全统计信息

        Returns:
            安全统计字典
        """
        stats = {
            "auth_enabled": self.enable_auth,
            "rate_limit_enabled": self.enable_rate_limit,
        }

        if self.rate_limiter:
            stats["rate_limit_stats"] = self.rate_limiter.get_stats()

        return stats


# 全局安全中间件实例
_security_middleware: SecurityMiddleware | None = None


def get_security_middleware(
    enable_auth: bool = True,
    enable_rate_limit: bool = True,
    rate_limit_config: RateLimitConfig | None = None,
) -> SecurityMiddleware:
    """
    获取全局安全中间件实例

    Args:
        enable_auth: 是否启用API密钥认证
        enable_rate_limit: 是否启用速率限制
        rate_limit_config: 速率限制配置

    Returns:
        安全中间件实例
    """
    global _security_middleware

    if _security_middleware is None:
        _security_middleware = SecurityMiddleware(
            enable_auth=enable_auth,
            enable_rate_limit=enable_rate_limit,
            rate_limit_config=rate_limit_config,
        )

    return _security_middleware


# FastAPI依赖项
async def verify_api_key(
    request: Request,
    x_api_key: str | None = None,
) -> None:
    """
    FastAPI依赖项:验证API密钥

    使用方式:
    ```python
    @app.get("/protected")
    async def protected_endpoint(_: None = Depends(verify_api_key)):
        ...
    ```
    """
    security = get_security_middleware()
    await security.verify_request(request, x_api_key)


# 导出
__all__ = [
    "APIKeyAuth",
    "RateLimitConfig",
    "RateLimitStats",
    "RateLimiter",
    "SecurityMiddleware",
    "get_security_middleware",
    "verify_api_key",
]
