"""
Athena API Gateway - 中间件系统

基于管道模式设计的中间件系统，提供请求/响应处理链。

参考：DeerFlow 中间件设计模式
"""

from .auth import AuthMiddleware
from .base import (
    AuthRequiredException,
    Middleware,
    MiddlewareContext,
    MiddlewareException,
    Pipeline,
    RateLimitExceededException,
)
from .cache import CacheMiddleware
from .cors import CORSMiddleware
from .fastapi import (
    FastAPIMiddlewareAdapter,
    enable_middleware,
    setup_middleware,
)
from .logging import LoggingMiddleware
from .monitoring import MetricsExporter, MonitoringMiddleware
from .rate_limit import RateLimitMiddleware
from .validation import ValidationException, ValidationMiddleware

__all__ = [
    # 基础组件
    "Middleware",
    "MiddlewareContext",
    "Pipeline",
    "MiddlewareException",
    "AuthRequiredException",
    "RateLimitExceededException",
    "ValidationException",

    # 核心中间件
    "AuthMiddleware",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "CORSMiddleware",

    # 扩展中间件
    "CacheMiddleware",
    "ValidationMiddleware",
    "MonitoringMiddleware",
    "MetricsExporter",

    # FastAPI 集成
    "FastAPIMiddlewareAdapter",
    "setup_middleware",
    "enable_middleware",
]

# 中间件执行顺序（严格按此顺序执行）
DEFAULT_MIDDLEWARE_ORDER = [
    "CORSMiddleware",         # 1. CORS 预检处理
    "LoggingMiddleware",       # 2. 请求日志记录
    "AuthMiddleware",          # 3. 身份验证
    "ValidationMiddleware",    # 4. 请求验证
    "CacheMiddleware",         # 5. 响应缓存
    "MonitoringMiddleware",    # 6. 性能监控
    "RateLimitMiddleware",     # 7. 速率限制
]
