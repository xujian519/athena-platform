"""
FastAPI 中间件集成

将 Athena 中间件系统集成到 FastAPI 应用中。
"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .base import MiddlewareContext, Pipeline


class FastAPIMiddlewareAdapter(BaseHTTPMiddleware):
    """FastAPI 中间件适配器

    将 Athena 中间件系统适配到 FastAPI 的中间件接口。
    """

    def __init__(self, pipeline: Pipeline, app):
        super().__init__(app)
        self._pipeline = pipeline

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """分发请求到中间件管道"""

        # 创建中间件上下文
        ctx = MiddlewareContext(request=request)

        # 定义最终处理器
        async def final_handler(ctx: MiddlewareContext) -> Response:
            return await call_next(ctx.request)

        # 执行中间件管道
        return await self._pipeline.execute(ctx, final_handler)


def setup_middleware(
    app,
    jwt_secret: str,
    enable_auth: bool = True,
    enable_logging: bool = True,
    enable_rate_limit: bool = True,
    enable_cors: bool = True,
    **config
) -> Pipeline:
    """设置中间件管道

    Args:
        app: FastAPI 应用实例
        jwt_secret: JWT 密钥
        enable_auth: 是否启用认证中间件
        enable_logging: 是否启用日志中间件
        enable_rate_limit: 是否启用限流中间件
        enable_cors: 是否启用 CORS 中间件
        **config: 中间件配置

    Returns:
        Pipeline: 配置好的中间件管道
    """
    from .auth import AuthMiddleware
    from .cors import CORSMiddleware
    from .logging import LoggingMiddleware
    from .rate_limit import RateLimitMiddleware

    pipeline = Pipeline()

    # 添加中间件（按执行顺序）
    if enable_cors:
        pipeline.add(CORSMiddleware(
            allow_origins=config.get("cors_origins", ["*"]),
            allow_credentials=config.get("cors_credentials", True),
        ), order=1)

    if enable_logging:
        pipeline.add(LoggingMiddleware(
            log_level=config.get("log_level", 20),  # INFO
            log_body=config.get("log_body", False),
            slow_threshold=config.get("slow_threshold", 5.0),
        ), order=2)

    if enable_auth:
        pipeline.add(AuthMiddleware(
            jwt_secret=jwt_secret,
            jwt_algorithm=config.get("jwt_algorithm", "HS256"),
            jwt_expiry=config.get("jwt_expiry", 86400),
            api_keys=config.get("api_keys", []),
            skip_paths=config.get("auth_skip_paths", []),
        ), order=3)

    if enable_rate_limit:
        pipeline.add(RateLimitMiddleware(
            strategy=config.get("rate_limit_strategy", "fixed_window"),
            requests_per_window=config.get("rate_limit_requests", 100),
            window_size=config.get("rate_limit_window", 60),
            redis_url=config.get("redis_url", "redis://localhost:6379/0"),
        ), order=4)

    # 添加适配器到 FastAPI
    app.add_middleware(FastAPIMiddlewareAdapter, pipeline=pipeline)

    return pipeline


# 便捷函数
def enable_middleware(
    app,
    jwt_secret: str,
    config: dict | None = None
) -> Pipeline:
    """启用中间件系统

    简化的配置接口，适合快速启动。

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> pipeline = enable_middleware(app, jwt_secret="your-secret-key")
    """
    config = config or {}
    return setup_middleware(app, jwt_secret=jwt_secret, **config)
