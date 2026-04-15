"""
日志中间件

记录所有请求和响应的详细信息。
"""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import datetime

from fastapi import Request
from starlette.responses import Response

from .base import Middleware, MiddlewareContext

logger = logging.getLogger(__name__)


class LoggingMiddleware(Middleware):
    """日志中间件

    记录请求和响应的详细信息，包括：
    - 请求方法、路径、查询参数
    - 响应状态码、处理时间
    - 客户端IP、User-Agent
    - 用户ID（如果已认证）

    配置选项：
    - log_level: 日志级别，默认 INFO
    - log_body: 是否记录请求/响应体，默认 False
    - log_query: 是否记录查询参数，默认 True
    - skip_paths: 跳过日志记录的路径列表
    - slow_threshold: 慢请求阈值（秒），超过此阈值会记录警告，默认 5.0
    """

    def __init__(
        self,
        log_level: int = logging.INFO,
        log_body: bool = False,
        log_query: bool = True,
        skip_paths: list[str] | None = None,
        slow_threshold: float = 5.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._log_level = log_level
        self._log_body = log_body
        self._log_query = log_query
        self._slow_threshold = slow_threshold
        self._skip_paths = set(skip_paths or [])

        # 添加默认跳过路径
        self._skip_paths.update([
            "/health",
            "/metrics",
        ])

    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """记录请求日志"""

        request = ctx.request
        path = request.url.path

        # 检查是否跳过日志
        if self._should_skip_log(path):
            return await call_next(ctx)

        # 记录请求开始
        start_time = time.time()

        # 提取请求信息
        request_info = {
            "method": request.method,
            "path": path,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "request_id": ctx.get("request_id"),
        }

        # 记录查询参数
        if self._log_query and request.url.query:
            request_info["query"] = request.url.query

        # 记录请求体（如果启用）
        if self._log_body:
            request_info["body"] = await self._get_request_body(request)

        # 调用下一个中间件
        response = await call_next(ctx)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录响应信息
        response_info = {
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
        }

        # 合并日志信息
        log_data = {**request_info, **response_info}

        # 根据处理时间选择日志级别
        if process_time > self._slow_threshold:
            log_data["level"] = "WARNING"
            log_data["message"] = "Slow request detected"
            logger.warning(f"Request log: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            logger.log(
                self._log_level,
                f"Request log: {json.dumps(log_data, ensure_ascii=False)}"
            )

        return response

    def _should_skip_log(self, path: str) -> bool:
        """检查是否跳过日志"""
        for skip_path in self._skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 返回直连IP
        if request.client:
            return request.client.host
        return "unknown"

    async def _get_request_body(self, request: Request) -> str | None:
        """获取请求体"""
        try:
            # 只记录 JSON 请求体
            if "application/json" in request.headers.get("content-type", ""):
                body = await request.body()
                return body.decode("utf-8")[:1000]  # 限制长度
        except Exception:
            pass
        return None

    async def on_request(self, ctx: MiddlewareContext) -> None:
        """请求前置处理"""
        # 生成请求ID
        import uuid
        ctx.set("request_id", str(uuid.uuid4()))
        ctx.set("start_time", datetime.now().isoformat())
