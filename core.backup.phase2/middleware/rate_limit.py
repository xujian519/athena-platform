#!/usr/bin/env python3
from __future__ import annotations
"""
速率限制中间件
Rate Limiting Middleware

版本: 1.0.0
功能:
- 基于IP的速率限制
- 基于用户的速率限制
- 滑动窗口算法
- 分布式支持(Redis)
"""

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    # 每分钟请求数
    requests_per_minute: int = 60
    # 每小时请求数
    requests_per_hour: int = 1000
    # 每天请求数
    requests_per_day: int = 10000

    # 窗口大小(秒)
    minute_window: int = 60
    hour_window: int = 3600
    day_window: int = 86400

    # 是否启用分布式模式(Redis)
    enable_distributed: bool = False
    redis_key_prefix: str = "rate_limit"

    # 限制策略
    strategy: str = "sliding_window"  # sliding_window, token_bucket, fixed_window

    # 超出限制时的响应
    block_duration: int = 60  # 被封禁的时长(秒)
    retry_after_header: bool = True  # 是否返回Retry-After头


@dataclass
class RateLimitInfo:
    """速率限制信息"""

    key: str
    requests: deque = field(default_factory=deque)
    blocked_until: datetime | None = None
    total_requests: int = 0
    blocked_count: int = 0

    def is_blocked(self) -> bool:
        """检查是否被封禁"""
        if self.blocked_until is None:
            return False
        return datetime.now() < self.blocked_until

    def get_remaining_time(self) -> int:
        """获取剩余封禁时间(秒)"""
        if self.blocked_until is None:
            return 0
        remaining = (self.blocked_until - datetime.now()).total_seconds()
        return max(0, int(remaining))


class MemoryRateLimiter:
    """
    内存速率限制器

    使用滑动窗口算法实现速率限制
    """

    def __init__(self, config: RateLimitConfig):
        """
        初始化速率限制器

        Args:
            config: 速率限制配置
        """
        self.config = config
        # 存储每个key的请求历史
        self._limit_info: dict[str, RateLimitInfo] = defaultdict(lambda: RateLimitInfo(key=""))
        self._lock = asyncio.Lock()

        logger.info(
            f"✅ 速率限制器初始化: "
            f"{config.requests_per_minute}/min, "
            f"{config.requests_per_hour}/hour"
        )

    def _get_key(self, request: Request) -> str:
        """
        获取速率限制的key

        Args:
            request: FastAPI请求对象

        Returns:
            限制key
        """
        # 优先使用用户ID
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # 使用IP地址
        # 获取真实IP(考虑代理)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        # 使用IP的hash作为key(保护隐私)
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
        return f"ip:{ip_hash}"

    async def check_rate_limit(self, request: Request) -> tuple[bool, int | None]:
        """
        检查是否超过速率限制

        Args:
            request: FastAPI请求对象

        Returns:
            (is_allowed, retry_after): 是否允许和重试时间
        """
        key = self._get_key(request)
        now = datetime.now()

        async with self._lock:
            info = self._limit_info[key]
            info.key = key

            # 检查是否被封禁
            if info.is_blocked():
                retry_after = info.get_remaining_time()
                logger.warning(f"🚫 请求被拒绝(已封禁): {key}, 剩余 {retry_after}s")
                return False, retry_after

            # 清理过期请求
            cutoff_time = now - timedelta(seconds=self.config.day_window)
            while info.requests and info.requests[0] < cutoff_time:
                info.requests.popleft()

            # 记录当前请求
            info.requests.append(now)
            info.total_requests += 1

            # 检查各时间窗口的限制
            minute_ago = now - timedelta(seconds=self.config.minute_window)
            hour_ago = now - timedelta(seconds=self.config.hour_window)

            minute_count = sum(1 for t in info.requests if t > minute_ago)
            hour_count = sum(1 for t in info.requests if t > hour_ago)
            day_count = len(info.requests)

            # 检查是否超出限制
            if minute_count > self.config.requests_per_minute:
                logger.warning(
                    f"🚫 超出分钟限制: {key}, {minute_count} > {self.config.requests_per_minute}"
                )
                return self._block(info, self.config.minute_window)

            if hour_count > self.config.requests_per_hour:
                logger.warning(
                    f"🚫 超出小时限制: {key}, {hour_count} > {self.config.requests_per_hour}"
                )
                return self._block(info, self.config.hour_window)

            if day_count > self.config.requests_per_day:
                logger.warning(
                    f"🚫 超出每日限制: {key}, {day_count} > {self.config.requests_per_day}"
                )
                return self._block(info, self.config.day_window)

            logger.debug(
                f"✅ 请求允许: {key}, 分钟: {minute_count}, 小时: {hour_count}, 天: {day_count}"
            )
            return True, None

    def _block(self, info: RateLimitInfo, window_size: int) -> tuple[bool, int | None]:
        """
        封禁请求者

        Args:
            info: 速率限制信息
            window_size: 窗口大小

        Returns:
            (is_allowed, retry_after)
        """
        info.blocked_until = datetime.now() + timedelta(seconds=self.config.block_duration)
        info.blocked_count += 1
        retry_after = self.config.block_duration
        return False, retry_after

    def get_stats(self, key: str) -> dict[str, Any]:
        """
        获取速率限制统计

        Args:
            key: 限制key

        Returns:
            统计信息
        """
        info = self._limit_info[key]
        now = datetime.now()

        minute_ago = now - timedelta(seconds=self.config.minute_window)
        hour_ago = now - timedelta(seconds=self.config.hour_window)

        minute_count = sum(1 for t in info.requests if t > minute_ago)
        hour_count = sum(1 for t in info.requests if t > hour_ago)
        day_count = len(info.requests)

        return {
            "key": key,
            "total_requests": info.total_requests,
            "blocked_count": info.blocked_count,
            "current_minute": minute_count,
            "current_hour": hour_count,
            "current_day": day_count,
            "limits": {
                "minute": self.config.requests_per_minute,
                "hour": self.config.requests_per_hour,
                "day": self.config.requests_per_day,
            },
            "is_blocked": info.is_blocked(),
            "blocked_until": info.blocked_until.isoformat() if info.blocked_until else None,
        }

    def reset(self, key: str | None = None):
        """
        重置速率限制

        Args:
            key: 限制key(None表示重置所有)
        """

        async def _reset():
            async with self._lock:
                if key is None:
                    self._limit_info.clear()
                    logger.info("🗑️ 已重置所有速率限制")
                else:
                    if key in self._limit_info:
                        del self._limit_info[key]
                        logger.info(f"🗑️ 已重置速率限制: {key}")

        return _reset()


# 全局限流器单例
_global_limiter: MemoryRateLimiter | None = None


def get_rate_limiter(config: RateLimitConfig | None = None) -> MemoryRateLimiter:
    """
    获取全局速率限制器

    Args:
        config: 速率限制配置(仅首次调用时需要)

    Returns:
        MemoryRateLimiter实例
    """
    global _global_limiter

    if _global_limiter is None:
        if config is None:
            config = RateLimitConfig()
        _global_limiter = MemoryRateLimiter(config)

    return _global_limiter


def reset_rate_limiter():
    """重置全局速率限制器(用于测试)"""
    global _global_limiter
    _global_limiter = None


# 装饰器
def rate_limit(
    requests_per_minute: int | None = None,
    requests_per_hour: int | None = None,
    key_func: Callable[[Request, str], Any] | None = None,
):
    """
    速率限制装饰器

    Args:
        requests_per_minute: 每分钟请求数限制
        requests_per_hour: 每小时请求数限制
        key_func: 自定义key生成函数

    Returns:
        装饰器
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            limiter = get_rate_limiter()

            # 允许自定义配置
            original_config = limiter.config
            if requests_per_minute or requests_per_hour:
                config = RateLimitConfig(
                    requests_per_minute=requests_per_minute or original_config.requests_per_minute,
                    requests_per_hour=requests_per_hour or original_config.requests_per_hour,
                )
                limiter = MemoryRateLimiter(config)

            is_allowed, retry_after = await limiter.check_rate_limit(request)

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求过于频繁,请稍后再试",
                    headers={"Retry-After": str(retry_after)} if retry_after else {},
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


class RateLimitMiddleware:
    """
    速率限制中间件

    自动对所有请求应用速率限制
    """

    def __init__(self, config: RateLimitConfig, exclude_paths: set[str] | None = None):
        """
        初始化中间件

        Args:
            config: 速率限制配置
            exclude_paths: 排除的路径(不限制)
        """
        self.config = config
        self.limiter = MemoryRateLimiter(config)
        self.exclude_paths = exclude_paths or {"/health", "/docs", "/openapi.json", "/metrics"}

        logger.info(f"✅ 速率限制中间件已启用,排除路径: {self.exclude_paths}")

    async def __call__(self, request: Request, call_next):
        """
        处理请求

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件/路由

        Returns:
            响应
        """
        # 检查是否需要跳过限制
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # 检查速率限制
        is_allowed, retry_after = await self.limiter.check_rate_limit(request)

        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "请求过于频繁",
                    "message": "您已超过速率限制,请稍后再试",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)} if retry_after else {},
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制头
        if self.config.retry_after_header:
            key = self.limiter._get_key(request)
            stats = self.limiter.get_stats(key)
            response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.config.requests_per_minute - stats["current_minute"])
            )
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response
