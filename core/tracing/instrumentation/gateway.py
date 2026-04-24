"""
Gateway自动埋点模块

提供Gateway↔Agent通信的自动追踪功能。
支持请求路由、负载均衡、健康检查等场景的追踪。
"""

from functools import wraps
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager

from ..tracer import AthenaTracer
from ..attributes import AgentAttributes, HTTPAttributes
from opentelemetry import trace, Status, StatusCode


@contextmanager
def trace_gateway_request(
    agent_name: str,
    task_type: str,
    gateway_service: str = "athena-gateway",
    **kwargs
):
    """
    Gateway请求追踪上下文管理器

    Args:
        agent_name: 目标Agent名称
        task_type: 任务类型
        gateway_service: Gateway服务名称
        **kwargs: 额外属性

    Yields:
        Span对象

    Example:
        >>> with trace_gateway_request("xiaona", "patent_analysis"):
        ...     result = await gateway.send_to_agent("xiaona", "analyze")
    """
    # 获取当前追踪器
    current_span = trace.get_current_span()
    tracer = None

    # 尝试从当前span获取tracer
    if current_span and hasattr(current_span, '__class__'):
        # 使用全局tracer
        tracer = trace.get_tracer(__name__)

    if tracer:
        with tracer.start_as_current_span(
            name=f"gateway.{agent_name}",
            kind=trace.SpanKind.SERVER,
            attributes={
                "gateway.service": gateway_service,
                "agent.target": agent_name,
                "task.type": task_type,
                **kwargs
            }
        ) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
    else:
        # 无追踪器时使用空上下文
        from contextlib import nullcontext
        yield nullcontext()


@contextmanager
def trace_agent_communication(
    from_agent: str,
    to_agent: str,
    message_type: str = "task",
    **kwargs
):
    """
    Agent间通信追踪上下文管理器

    Args:
        from_agent: 发送方Agent名称
        to_agent: 接收方Agent名称
        message_type: 消息类型（task, query, notify, response）
        **kwargs: 额外属性

    Yields:
        Span对象

    Example:
        >>> with trace_agent_communication("xiaonuo", "xiaona", "task"):
        ...     await send_message(xiaona, task_data)
    """
    current_span = trace.get_current_span()
    tracer = trace.get_tracer(__name__) if current_span else None

    if tracer:
        with tracer.start_as_current_span(
            name=f"agent.{from_agent}->{to_agent}",
            kind=trace.SpanKind.INTERNAL,
            attributes={
                "agent.from": from_agent,
                "agent.to": to_agent,
                "message.type": message_type,
                **kwargs
            }
        ) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
    else:
        from contextlib import nullcontext
        yield nullcontext()


def trace_gateway_method(
    agent_arg: str = "target_agent",
    task_type_arg: str = "task_type"
):
    """
    Gateway方法装饰器

    自动为Gateway通信方法添加追踪。

    Args:
        agent_arg: 包含目标Agent名的参数名
        task_type_arg: 包含任务类型的参数名

    Example:
        >>> @trace_gateway_method()
        ... async def send_to_agent(self, target_agent: str, task_type: str, **kwargs):
        ...     return await self._gateway.send(target_agent, task_type, **kwargs)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # 获取参数
            target_agent = kwargs.get(agent_arg, "unknown")
            task_type = kwargs.get(task_type_arg, "unknown")

            with trace_gateway_request(target_agent, task_type):
                return await func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            target_agent = kwargs.get(agent_arg, "unknown")
            task_type = kwargs.get(task_type_arg, "unknown")

            with trace_gateway_request(target_agent, task_type):
                return func(self, *args, **kwargs)

        # 检测是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class GatewayTracerMixin:
    """
    Gateway追踪混入类

    为Gateway客户端类提供追踪功能。

    Example:
        >>> class MyGateway(GatewayTracerMixin):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.setup_gateway_tracer()
    """

    _gateway_tracer: Optional[AthenaTracer] = None
    _gateway_service: str = "athena-gateway"

    def setup_gateway_tracer(
        self,
        service_name: str = "athena-gateway",
        tracer: Optional[AthenaTracer] = None
    ) -> None:
        """
        设置Gateway追踪器

        Args:
            service_name: 服务名称
            tracer: 自定义追踪器
        """
        self._gateway_service = service_name
        self._gateway_tracer = tracer or AthenaTracer(f"gateway.{service_name}")

    @contextmanager
    def trace_gateway_operation(
        self,
        agent_name: str,
        task_type: str
    ):
        """
        Gateway操作追踪上下文管理器

        Args:
            agent_name: 目标Agent
            task_type: 任务类型

        Yields:
            Span对象
        """
        if self._gateway_tracer:
            with trace_gateway_request(
                agent_name,
                task_type,
                self._gateway_service
            ):
                yield
        else:
            from contextlib import nullcontext
            yield nullcontext()


# Gateway服务常量
class GatewayService:
    """Gateway服务常量"""
    ATHENA_GATEWAY = "athena-gateway"
    API_GATEWAY = "api-gateway"
    WS_GATEWAY = "websocket-gateway"


# 消息类型常量
class MessageType:
    """消息类型常量"""
    TASK = "task"
    QUERY = "query"
    NOTIFY = "notify"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    HEALTH_CHECK = "health_check"
