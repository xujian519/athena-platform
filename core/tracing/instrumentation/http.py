"""
HTTP自动埋点模块

提供HTTP请求的自动追踪装饰器和工具。
"""

from functools import wraps
from typing import Callable, Optional
from contextlib import contextmanager

from ..tracer import AthenaTracer
from ..attributes import HTTPAttributes


@contextmanager
def trace_http_request(
    tracer: AthenaTracer,
    method: str,
    url: str,
    **kwargs
):
    """
    HTTP请求追踪上下文管理器

    Args:
        tracer: 追踪器实例
        method: HTTP方法
        url: 请求URL
        **kwargs: 额外属性

    Yields:
        包含Span和状态码设置函数的元组

    Example:
        >>> with trace_http_request(tracer, "GET", "https://api.example.com") as (span, set_status):
        ...     response = await httpx.get(url)
        ...     set_status(response.status_code)
    """
    with tracer.start_http_span(
        method=method,
        url=url,
        **kwargs
    ) as span:
        def set_status(status_code: int):
            """设置HTTP状态码"""
            span.set_attribute(HTTPAttributes.HTTP_STATUS_CODE, status_code)

        yield span, set_status


def trace_http_method(method: Optional[str] = None, url_arg: str = "url"):
    """
    HTTP方法装饰器

    自动为HTTP请求方法添加追踪。

    Args:
        method: HTTP方法（默认从方法名推断）
        url_arg: 包含URL的参数名

    Example:
        >>> @trace_http_method(method="GET")
        ... async def fetch_data(self, url: str):
        ...     return await httpx.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None) or getattr(self, 'tracer', None)
            if tracer is None:
                return await func(self, *args, **kwargs)

            # 推断HTTP方法
            actual_method = method
            if actual_method is None:
                func_name = func.__name__.upper()
                for m in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
                    if m in func_name:
                        actual_method = m
                        break
                if actual_method is None:
                    actual_method = "REQUEST"

            # 尝试获取URL
            url = kwargs.get(url_arg, "unknown")

            with trace_http_request(tracer, actual_method, url) as (span, set_status):
                try:
                    result = await func(self, *args, **kwargs)

                    # 尝试从响应中提取状态码
                    if hasattr(result, 'status_code'):
                        set_status(result.status_code)
                    elif hasattr(result, 'status'):
                        set_status(result.status)

                    return result

                except Exception as e:
                    tracer.record_exception(e, span)
                    raise

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            tracer = getattr(self, '_tracer', None) or getattr(self, 'tracer', None)
            if tracer is None:
                return func(self, *args, **kwargs)

            actual_method = method
            if actual_method is None:
                func_name = func.__name__.upper()
                for m in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
                    if m in func_name:
                        actual_method = m
                        break
                if actual_method is None:
                    actual_method = "REQUEST"

            url = kwargs.get(url_arg, "unknown")

            with trace_http_request(tracer, actual_method, url) as (span, set_status):
                try:
                    result = func(self, *args, **kwargs)

                    if hasattr(result, 'status_code'):
                        set_status(result.status_code)
                    elif hasattr(result, 'status'):
                        set_status(result.status)

                    return result

                except Exception as e:
                    tracer.record_exception(e, span)
                    raise

        # 检测是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class HTTPTracerMixin:
    """
    HTTP追踪混入类

    为HTTP客户端类提供追踪功能。

    Example:
        >>> class MyHTTPClient(HTTPTracerMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.setup_http_tracer()
    """

    _http_tracer: Optional[AthenaTracer] = None

    def setup_http_tracer(self, tracer: Optional[AthenaTracer] = None) -> None:
        """
        设置HTTP追踪器

        Args:
            tracer: 自定义追踪器
        """
        self._http_tracer = tracer or AthenaTracer("http.client")

    @contextmanager
    def trace_http(self, method: str, url: str):
        """
        HTTP请求追踪上下文管理器

        Args:
            method: HTTP方法
            url: 请求URL

        Yields:
            (span, set_status) 元组
        """
        if self._http_tracer:
            with trace_http_request(self._http_tracer, method, url) as result:
                yield result
        else:
            from contextlib import nullcontext
            yield nullcontext()


# HTTP方法常量
class HTTPMethod:
    """HTTP方法常量"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


# HTTP状态码常量
class HTTPStatus:
    """HTTP状态码常量"""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
