#!/usr/bin/env python3
from __future__ import annotations
"""
API限流器模块
Rate Limiter for Athena API
"""

import os
import time
from collections import defaultdict

from fastapi import HTTPException, Request


class RateLimiter:
    """简单的内存限流器"""

    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list] = defaultdict(list)

    def check_rate_limit(self, api_key: str) -> bool:
        """检查是否超过限流"""
        now = time.time()
        minute_ago = now - 60

        # 清理旧记录
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key] if req_time > minute_ago
        ]

        # 检查是否超过限制
        if len(self.requests[api_key]) >= self.requests_per_minute:
            return False

        # 记录新请求
        self.requests[api_key].append(now)
        return True


# 全局限流器实例
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """获取限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        )
    return _rate_limiter


async def check_rate_limit_middleware(request: Request, call_next):
    """限流中间件"""
    api_key = request.headers.get("X-API-Key", "anonymous")
    limiter = get_rate_limiter()

    if not limiter.check_rate_limit(api_key):
        raise HTTPException(
            status_code=429, detail="超过速率限制,请稍后重试", headers={"Retry-After": "60"}
        )

    response = await call_next(request)
    return response
