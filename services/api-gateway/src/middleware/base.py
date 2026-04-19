"""
中间件基类和管道管理器

定义中间件接口和管道执行模式。
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import Request, Response

logger = logging.getLogger(__name__)


@dataclass
class MiddlewareContext:
    """中间件上下文

    存储请求处理过程中的共享数据，允许中间件之间传递信息。
    """
    request: Request
    response: Response | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    user_id: str | None = None
    session_id: str | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.metadata.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self.metadata[key] = value

    def has(self, key: str) -> bool:
        """检查上下文数据是否存在"""
        return key in self.metadata


class Middleware(ABC):
    """中间件抽象基类

    所有中间件必须实现 process 方法，该方法接收上下文和下一个处理器。
    """

    def __init__(self, name: str | None = None, enabled: bool = True):
        self.name = name or self.__class__.__name__
        self.enabled = enabled
        self._config: dict[str, Any] = {}

    @abstractmethod
    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """处理请求

        Args:
            ctx: 中间件上下文
            call_next: 调用下一个中间件的函数

        Returns:
            Response: HTTP响应对象

        Raises:
            MiddlewareException: 中间件处理异常
        """
        pass

    async def on_request(self, ctx: MiddlewareContext) -> None:
        """请求前置处理（可选重写）"""
        pass

    async def on_response(self, ctx: MiddlewareContext, response: Response) -> Response:
        """响应后置处理（可选重写）"""
        return response

    def configure(self, **kwargs) -> "Middleware":
        """配置中间件

        支持链式调用：
            middleware.configure(key=value).configure(key2=value2)
        """
        self._config.update(kwargs)
        return self

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(enabled={self.enabled})"


class Pipeline:
    """中间件管道

    管理中间件的注册、排序和执行。
    """

    def __init__(self):
        self._middlewares: list[Middleware] = []
        self._sorted: bool = False

    def add(self, middleware: Middleware, order: int | None = None) -> "Pipeline":
        """添加中间件

        Args:
            middleware: 中间件实例
            order: 执行顺序（数字越小越先执行），None表示追加到末尾

        Returns:
            Pipeline: 支持链式调用
        """
        if order is not None:
            middleware.order = order  # type: ignore
        self._middlewares.append(middleware)
        self._sorted = False
        return self

    def remove(self, name: str) -> bool:
        """移除中间件

        Args:
            name: 中间件名称

        Returns:
            bool: 是否成功移除
        """
        original_len = len(self._middlewares)
        self._middlewares = [m for m in self._middlewares if m.name != name]
        return len(self._middlewares) < original_len

    def get(self, name: str) -> Middleware | None:
        """获取中间件

        Args:
            name: 中间件名称

        Returns:
            Optional[Middleware]: 中间件实例，不存在则返回None
        """
        for middleware in self._middlewares:
            if middleware.name == name:
                return middleware
        return None

    def sort(self) -> "Pipeline":
        """按order字段排序中间件"""
        # 按order字段排序，没有order的放在最后
        def get_order(m: Middleware) -> int:
            return getattr(m, "order", 9999)

        self._middlewares.sort(key=get_order)
        self._sorted = True
        return self

    async def execute(
        self,
        ctx: MiddlewareContext,
        handler: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """执行中间件管道

        Args:
            ctx: 中间件上下文
            handler: 最终的请求处理器

        Returns:
            Response: HTTP响应对象

        Raises:
            Exception: 中间件或处理器抛出的异常
        """
        if not self._sorted:
            self.sort()

        # 创建中间件调用链
        async def call_next(
            current_idx: int,
            context: MiddlewareContext
        ) -> Response:
            """递归调用下一个中间件"""
            if current_idx >= len(self._middlewares):
                # 所有中间件执行完毕，调用最终处理器
                return await handler(context)

            middleware = self._middlewares[current_idx]

            # 跳过禁用的中间件
            if not middleware.enabled:
                return await call_next(current_idx + 1, context)

            # 执行当前中间件
            try:
                # 前置处理
                await middleware.on_request(context)

                # 调用下一个中间件
                response = await middleware.process(
                    context,
                    lambda ctx: call_next(current_idx + 1, ctx)
                )

                # 后置处理
                response = await middleware.on_response(context, response)

                return response

            except Exception as e:
                logger.error(
                    f"Middleware {middleware.name} error: {e}",
                    exc_info=True
                )
                raise

        # 从第一个中间件开始执行
        return await call_next(0, ctx)

    def list(self) -> list[str]:
        """列出所有中间件名称"""
        return [m.name for m in self._middlewares]

    def enable(self, name: str) -> bool:
        """启用中间件"""
        middleware = self.get(name)
        if middleware:
            middleware.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """禁用中间件"""
        middleware = self.get(name)
        if middleware:
            middleware.enabled = False
            return True
        return False

    def __len__(self) -> int:
        return len(self._middlewares)

    def __repr__(self) -> str:
        enabled = [m.name for m in self._middlewares if m.enabled]
        disabled = [m.name for m in self._middlewares if not m.enabled]
        return (
            f"Pipeline(middlewares={len(self._middlewares)}, "
            f"enabled={len(enabled)}, disabled={len(disabled)})"
        )


class MiddlewareException(Exception):
    """中间件异常基类"""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthRequiredException(MiddlewareException):
    """认证失败异常"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, code=401)


class RateLimitExceededException(MiddlewareException):
    """速率限制异常"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message, code=429)
        self.retry_after = retry_after
