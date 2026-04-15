"""
CORS 中间件

处理跨域资源共享（Cross-Origin Resource Sharing）。
"""

from collections.abc import Awaitable, Callable

from starlette.responses import Response

from .base import Middleware, MiddlewareContext


class CORSMiddleware(Middleware):
    """CORS 中间件

    处理跨域请求，支持：
    - 预检请求（OPTIONS）
    - 自定义头部
    - 凭证模式

    配置选项：
    - allow_origins: 允许的源列表，["*"] 表示允许所有
    - allow_methods: 允许的 HTTP 方法
    - allow_headers: 允许的请求头
    - expose_headers: 暴露的响应头
    - allow_credentials: 是否允许凭证，默认 True
    - max_age: 预检请求缓存时间（秒），默认 600
    """

    def __init__(
        self,
        allow_origins: list[str] = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        allow_credentials: bool = True,
        max_age: int = 600,
        **kwargs
    ):
        if allow_origins is None:
            allow_origins = ["*"]
        super().__init__(**kwargs)
        self._allow_origins = allow_origins
        self._allow_methods = allow_methods or [
            "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"
        ]
        self._allow_headers = allow_headers or [
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Request-ID",
        ]
        self._expose_headers = expose_headers or []
        self._allow_credentials = allow_credentials
        self._max_age = max_age

    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """处理 CORS"""

        request = ctx.request
        origin = request.headers.get("origin", "")

        # 处理预检请求
        if request.method == "OPTIONS":
            return self._create_preflight_response(origin)

        # 处理正常请求
        response = await call_next(ctx)
        self._add_cors_headers(response, origin)

        return response

    def _create_preflight_response(self, origin: str) -> Response:
        """创建预检响应"""
        headers = {}

        # 检查源是否允许
        if self._is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = self._get_allow_origin(origin)
            headers["Access-Control-Allow-Credentials"] = str(self._allow_credentials).lower()
            headers["Access-Control-Allow-Methods"] = ", ".join(self._allow_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self._allow_headers)
            headers["Access-Control-Max-Age"] = str(self._max_age)

        return Response(
            status_code=204,
            headers=headers
        )

    def _add_cors_headers(self, response: Response, origin: str) -> None:
        """添加 CORS 响应头"""
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = self._get_allow_origin(origin)
            response.headers["Access-Control-Allow-Credentials"] = str(self._allow_credentials).lower()

            if self._expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(self._expose_headers)

    def _is_origin_allowed(self, origin: str) -> bool:
        """检查源是否允许"""
        if not origin:
            return False

        if "*" in self._allow_origins:
            return True

        return origin in self._allow_origins

    def _get_allow_origin(self, origin: str) -> str:
        """获取允许的源"""
        if "*" in self._allow_origins:
            if self._allow_credentials:
                # 凭证模式下不能使用 "*"
                return origin
            return "*"
        return origin
