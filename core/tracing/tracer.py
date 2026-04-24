"""
OpenTelemetry追踪器实现

提供Athena平台专用的追踪器类，封装OpenTelemetry API。
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional, Generator, Callable
from functools import wraps
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import Context

from .config import TracingConfig, get_config
from .attributes import (
    AgentAttributes,
    LLMAttributes,
    ToolAttributes,
    ErrorAttributes,
    DatabaseAttributes,
    HTTPAttributes,
)


class AthenaTracer:
    """
    Athena平台专用追踪器

    提供便捷的追踪方法，封装OpenTelemetry API。
    支持Agent处理、LLM调用、工具调用等常见场景的追踪。

    Example:
        >>> tracer = AthenaTracer("xiaona-agent")
        >>> with tracer.start_agent_span("xiaona", "patent_analysis"):
        ...     result = process_patent()
    """

    def __init__(
        self,
        service_name: str,
        config: Optional[TracingConfig] = None
    ):
        """
        初始化追踪器

        Args:
            service_name: 服务名称（如agent.xiaona, service.gateway）
            config: 追踪配置，默认使用环境配置
        """
        self.service_name = service_name
        self.config = config or get_config()
        self._tracer = trace.get_tracer(service_name)
        self._propagator = TraceContextTextMapPropagator()

    @property
    def tracer(self) -> trace.Tracer:
        """获取底层OpenTelemetry Tracer"""
        return self._tracer

    def start_as_current_span(
        self,
        name: str,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Span:
        """
        启动一个Span作为当前Span

        Args:
            name: Span名称
            kind: Span类型
            attributes: Span属性
            **kwargs: 额外参数

        Returns:
            Span对象
        """
        return self._tracer.start_as_current_span(
            name=name,
            kind=kind,
            attributes=attributes,
            **kwargs
        )

    @contextmanager
    def start_agent_span(
        self,
        agent_name: str,
        task_type: str,
        agent_role: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Generator[Span, None, None]:
        """
        创建Agent处理Span

        Args:
            agent_name: Agent名称
            task_type: 任务类型
            agent_role: Agent角色
            request_id: 请求ID
            session_id: 会话ID

        Yields:
            Span对象
        """
        attributes = AgentAttributes.create(
            agent_name=agent_name,
            task_type=task_type,
            agent_role=agent_role,
            request_id=request_id,
            session_id=session_id,
            **kwargs
        )

        with self._tracer.start_as_current_span(
            name=f"{agent_name}.{task_type}",
            kind=trace.SpanKind.SERVER,
            attributes=attributes
        ) as span:
            yield span

    @contextmanager
    def start_llm_span(
        self,
        provider: str,
        model: str,
        request_type: str = "chat",
        **kwargs
    ) -> Generator[Span, None, None]:
        """
        创建LLM调用Span

        Args:
            provider: LLM提供商
            model: 模型名称
            request_type: 请求类型

        Yields:
            Span对象，可用于添加响应属性
        """
        attributes = LLMAttributes.create(
            provider=provider,
            model=model,
            request_type=request_type,
            **kwargs
        )

        with self._tracer.start_as_current_span(
            name=f"llm.{provider}",
            kind=trace.SpanKind.CLIENT,
            attributes=attributes
        ) as span:
            yield span

    @contextmanager
    def start_tool_span(
        self,
        tool_name: str,
        category: str,
        **kwargs
    ) -> Generator[Span, None, None]:
        """
        创建工具调用Span

        Args:
            tool_name: 工具名称
            category: 工具分类

        Yields:
            Span对象
        """
        attributes = ToolAttributes.create(
            tool_name=tool_name,
            category=category,
            **kwargs
        )

        with self._tracer.start_as_current_span(
            name=f"tool.{tool_name}",
            kind=trace.SpanKind.INTERNAL,
            attributes=attributes
        ) as span:
            yield span

    @contextmanager
    def start_database_span(
        self,
        db_system: str,
        operation: str,
        table: Optional[str] = None,
        **kwargs
    ) -> Generator[Span, None, None]:
        """
        创建数据库操作Span

        Args:
            db_system: 数据库系统（postgresql, redis, neo4j）
            operation: 操作类型（SELECT, INSERT, UPDATE, DELETE）
            table: 表名

        Yields:
            Span对象
        """
        attributes = DatabaseAttributes.create(
            db_system=db_system,
            operation=operation,
            table=table,
            **kwargs
        )

        with self._tracer.start_as_current_span(
            name=f"db.{operation.lower()}",
            kind=trace.SpanKind.CLIENT,
            attributes=attributes
        ) as span:
            yield span

    @contextmanager
    def start_http_span(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Generator[Span, None, None]:
        """
        创建HTTP请求Span

        Args:
            method: HTTP方法
            url: 请求URL

        Yields:
            Span对象，可用于添加状态码
        """
        attributes = HTTPAttributes.create(
            method=method,
            url=url,
            **kwargs
        )

        with self._tracer.start_as_current_span(
            name=f"http.{method.lower()}",
            kind=trace.SpanKind.CLIENT,
            attributes=attributes
        ) as span:
            yield span

    def record_exception(
        self,
        exception: Exception,
        span: Optional[Span] = None
    ):
        """
        记录异常到Span

        Args:
            exception: 异常对象
            span: 目标Span，默认使用当前Span
        """
        target_span = span or trace.get_current_span()
        target_span.record_exception(exception)

        # 添加错误属性
        attributes = ErrorAttributes.create(
            error_type=type(exception).__name__,
            message=str(exception)
        )
        for key, value in attributes.items():
            target_span.set_attribute(key, value)

        # 设置Span状态为错误
        target_span.set_status(Status(StatusCode.ERROR, str(exception)))

    def inject_context(self, carrier: Dict[str, str]) -> None:
        """
        将当前Trace Context注入到载体

        用于跨服务传播追踪上下文。

        Args:
            carrier: 载体字典（如HTTP headers）
        """
        self._propagator.inject(carrier)

    def extract_context(self, carrier: Dict[str, str]) -> Context:
        """
        从载体提取Trace Context

        用于恢复跨服务传播的追踪上下文。

        Args:
            carrier: 载体字典（如HTTP headers）

        Returns:
            OpenTelemetry Context对象
        """
        return self._propagator.extract(carrier)

    def get_trace_id(self) -> Optional[str]:
        """
        获取当前Trace ID

        Returns:
            十六进制格式的Trace ID，或None
        """
        current_span = trace.get_current_span()
        if current_span and current_span.context:
            return format(current_span.context.trace_id, "032x")
        return None

    def get_span_id(self) -> Optional[str]:
        """
        获取当前Span ID

        Returns:
            十六进制格式的Span ID，或None
        """
        current_span = trace.get_current_span()
        if current_span and current_span.context:
            return format(current_span.context.span_id, "016x")
        return None


def trace_method(
    span_name: Optional[str] = None,
    agent_name: Optional[str] = None,
    task_type: Optional[str] = None
):
    """
    方法追踪装饰器

    自动为方法创建追踪Span。

    Args:
        span_name: Span名称，默认使用方法名
        agent_name: Agent名称（用于Agent属性）
        task_type: 任务类型（用于Agent属性）

    Example:
        >>> @trace_method(agent_name="xiaona", task_type="analysis")
        ... async def analyze_patent(self, patent_id: str):
        ...     return analysis_result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = AthenaTracer("method")
            name = span_name or f"{func.__module__}.{func.__name__}"

            attributes = {}
            if agent_name:
                attributes.update(AgentAttributes.create(
                    agent_name=agent_name,
                    task_type=task_type or func.__name__
                ))

            with tracer.start_as_current_span(name, attributes=attributes or None):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = AthenaTracer("method")
            name = span_name or f"{func.__module__}.{func.__name__}"

            attributes = {}
            if agent_name:
                attributes.update(AgentAttributes.create(
                    agent_name=agent_name,
                    task_type=task_type or func.__name__
                ))

            with tracer.start_as_current_span(name, attributes=attributes or None):
                return func(*args, **kwargs)

        # 检测函数是否为协程函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 全局默认追踪器
_default_tracer: Optional[AthenaTracer] = None


def get_default_tracer() -> AthenaTracer:
    """获取默认追踪器（单例）"""
    global _default_tracer
    if _default_tracer is None:
        _default_tracer = AthenaTracer("athena-platform")
    return _default_tracer


def record_exception(
    exception: Exception,
    additional_info: Optional[Dict[str, Any]] = None,
    span: Optional[Span] = None,
    escape_common: bool = False
) -> None:
    """
    记录异常到当前Span（全局函数）

    便捷的异常记录函数，自动获取当前Span并记录异常信息。

    Args:
        exception: 异常对象
        additional_info: 额外的上下文信息（如变量值、状态等）
        span: 目标Span，默认使用当前Span
        escape_common: 是否转义常见异常类型（如TimeoutError）

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     record_exception(e, {"context": "processing patent CN123456"})
    """
    target_span = span or trace.get_current_span()

    # 检查Span是否有效
    if target_span is None or not hasattr(target_span, 'is_recording') or not target_span.is_recording():
        return

    # 记录异常
    target_span.record_exception(
        exception=exception,
        attributes=additional_info or {},
        escaped=escape_common
    )

    # 添加错误属性
    target_span.set_attribute("error.type", type(exception).__name__)
    target_span.set_attribute("error.message", str(exception))

    if additional_info:
        for key, value in additional_info.items():
            if value is not None:
                target_span.set_attribute(f"error.context.{key}", str(value))

    # 设置Span状态为错误
    target_span.set_status(Status(StatusCode.ERROR, str(exception)))


def record_error(
    error_type: str,
    error_message: str,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    记录错误到当前Span（不依赖异常对象）

    当没有异常对象但仍需记录错误时使用。

    Args:
        error_type: 错误类型
        error_message: 错误消息
        additional_info: 额外的上下文信息

    Example:
        >>> record_error(
        ...     "validation_error",
        ...     "Invalid patent number format",
        ...     {"input": "CN123", "expected_format": "CNXXXXXXXXX"}
        ... )
    """
    current_span = trace.get_current_span()

    if current_span is None or not hasattr(current_span, 'is_recording') or not current_span.is_recording():
        return

    current_span.set_attribute("error.type", error_type)
    current_span.set_attribute("error.message", error_message)

    if additional_info:
        for key, value in additional_info.items():
            if value is not None:
                current_span.set_attribute(f"error.context.{key}", str(value))

    current_span.set_status(Status(StatusCode.ERROR, error_message))


def add_span_attributes(**attributes: Any) -> None:
    """
    添加属性到当前Span

    便捷函数，用于向当前Span添加自定义属性。

    Args:
        **attributes: 属性键值对

    Example:
        >>> add_span_attributes(
        ...     user_id="12345",
        ...     patent_id="CN123456789A",
        ...     processing_stage="analysis"
        ... )
    """
    current_span = trace.get_current_span()

    if current_span is None or not hasattr(current_span, 'is_recording') or not current_span.is_recording():
        return

    for key, value in attributes.items():
        if value is not None:
            current_span.set_attribute(key, value)


def set_span_ok(description: Optional[str] = None) -> None:
    """
    设置当前Span状态为OK

    Args:
        description: 可选的描述信息

    Example:
        >>> set_span_ok("Patent analysis completed successfully")
    """
    current_span = trace.get_current_span()

    if current_span is None or not hasattr(current_span, 'is_recording') or not current_span.is_recording():
        return

    current_span.set_status(Status(StatusCode.OK, description or ""))


class ExceptionRecorder:
    """
    异常记录器（上下文管理器）

    自动记录上下文中的异常。

    Example:
        >>> with ExceptionRecorder("processing_patent", patent_id="CN123456"):
        ...     risky_operation()
        >>> # 如果发生异常，自动记录到Span
    """

    def __init__(self, context_name: str, **context_info: Any):
        """
        初始化异常记录器

        Args:
            context_name: 上下文名称
            **context_info: 上下文信息
        """
        self.context_name = context_name
        self.context_info = context_info

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            additional_info = {
                "context": self.context_name,
                **self.context_info
            }
            record_exception(exc_val, additional_info)
        # 不抑制异常
        return False
