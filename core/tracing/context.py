"""
追踪上下文管理

提供跨服务、跨线程的追踪上下文管理功能。
支持W3C Trace Context标准的跨服务传播。
"""

from typing import Dict, Any, Optional
from contextvars import ContextVar
from opentelemetry.context import Context
from opentelemetry.trace import Span, get_current_span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# 当前请求上下文变量
_request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context", default={})

# W3C Trace Context传播器
_propagator = TraceContextTextMapPropagator()


class RequestContext:
    """
    请求上下文管理器

    在追踪过程中存储和传递请求相关元数据。
    """

    @staticmethod
    def set(key: str, value: Any) -> None:
        """设置上下文值"""
        context = _request_context.get()
        context[key] = value
        _request_context.set(context)

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """获取上下文值"""
        return _request_context.get().get(key, default)

    @staticmethod
    def get_all() -> Dict[str, Any]:
        """获取所有上下文"""
        return _request_context.get().copy()

    @staticmethod
    def clear() -> None:
        """清空上下文"""
        _request_context.set({})

    @staticmethod
    def update(data: Dict[str, Any]) -> None:
        """更新上下文"""
        context = _request_context.get()
        context.update(data)
        _request_context.set(context)


class TraceContext:
    """
    追踪上下文工具类

    提供便捷的追踪信息获取方法和跨服务传播功能。
    实现W3C Trace Context标准。
    """

    @staticmethod
    def get_current_span() -> Optional[Span]:
        """获取当前Span"""
        return get_current_span()

    @staticmethod
    def get_trace_id() -> Optional[str]:
        """获取当前Trace ID"""
        span = get_current_span()
        if span and span.context:
            return format(span.context.trace_id, "032x")
        return None

    @staticmethod
    def get_span_id() -> Optional[str]:
        """获取当前Span ID"""
        span = get_current_span()
        if span and span.context:
            return format(span.context.span_id, "016x")
        return None

    @staticmethod
    def is_valid() -> bool:
        """检查当前是否在有效的追踪上下文中"""
        span = get_current_span()
        return span is not None and span.context is not None

    @staticmethod
    def inject_to_headers(carrier: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        将当前TraceContext注入到HTTP headers

        使用W3C Trace Context标准，生成包含traceparent的headers。

        Args:
            carrier: 可选的载体字典，如果为None则创建新的

        Returns:
            包含traceparent等追踪信息的headers字典

        Example:
            >>> headers = TraceContext.inject_to_headers()
            >>> # headers = {'traceparent': '00-abcdef0123456789abcdef0123456789-0123456789abcdef-01'}
            >>> # 将headers传递给HTTP请求
        """
        if carrier is None:
            carrier = {}
        _propagator.inject(carrier)
        return carrier

    @staticmethod
    def extract_from_headers(headers: Dict[str, str]) -> Optional[Context]:
        """
        从HTTP headers提取TraceContext

        解析W3C Trace Context标准的headers，恢复追踪上下文。

        Args:
            headers: 包含traceparent等追踪信息的HTTP headers字典

        Returns:
            OpenTelemetry Context对象，如果headers无效则返回None

        Example:
            >>> context = TraceContext.extract_from_headers(request.headers)
            >>> # 使用context恢复追踪上下文
        """
        if not headers:
            return None
        try:
            return _propagator.extract(headers)
        except Exception:
            return None

    @staticmethod
    def get_trace_parent_from_headers(headers: Dict[str, str]) -> Optional[str]:
        """
        从headers获取traceparent值

        Args:
            headers: HTTP headers字典

        Returns:
            traceparent字符串或None
        """
        return headers.get("traceparent")

    @staticmethod
    def parse_trace_parent(trace_parent: str) -> Optional[Dict[str, str]]:
        """
        解析traceparent字符串

        traceparent格式: version-trace_id-span_id-trace_flags

        Args:
            trace_parent: traceparent字符串

        Returns:
            包含各部分的字典，或None（解析失败时）
        """
        try:
            parts = trace_parent.split("-")
            if len(parts) != 4:
                return None

            return {
                "version": parts[0],
                "trace_id": parts[1],
                "span_id": parts[2],
                "trace_flags": parts[3]
            }
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def create_trace_parent(
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        sampled: bool = True
    ) -> str:
        """
        创建traceparent字符串

        Args:
            trace_id: 可选的trace_id（16字节十六进制），默认使用当前
            span_id: 可选的span_id（8字节十六进制），默认使用当前
            sampled: 是否采样

        Returns:
            traceparent字符串
        """
        # 获取当前上下文值
        current_span = get_current_span()
        if current_span and current_span.context:
            trace_id = trace_id or format(current_span.context.trace_id, "032x")
            span_id = span_id or format(current_span.context.span_id, "016x")
        else:
            # 生成新的
            import uuid
            trace_id = trace_id or uuid.uuid4().hex + uuid.uuid4().hex[:16]
            span_id = span_id or uuid.uuid4().hex[:16]

        # trace_flags: 01 = sampled, 00 = not sampled
        trace_flags = "01" if sampled else "00"

        return f"00-{trace_id}-{span_id}-{trace_flags}"


# ========== Agent会话上下文 ==========

class AgentSessionContext:
    """
    Agent会话上下文

    存储Agent会话期间的追踪相关信息。
    """

    SESSION_ID = "session_id"
    REQUEST_ID = "request_id"
    USER_ID = "user_id"
    AGENT_NAME = "agent_name"
    TASK_TYPE = "task_type"

    @classmethod
    def start_session(
        cls,
        session_id: str,
        agent_name: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """开始新的Agent会话"""
        RequestContext.set(cls.SESSION_ID, session_id)
        RequestContext.set(cls.AGENT_NAME, agent_name)
        if request_id:
            RequestContext.set(cls.REQUEST_ID, request_id)
        if user_id:
            RequestContext.set(cls.USER_ID, user_id)

    @classmethod
    def end_session(cls) -> None:
        """结束当前Agent会话"""
        RequestContext.clear()

    @classmethod
    def get_session_id(cls) -> Optional[str]:
        """获取当前会话ID"""
        return RequestContext.get(cls.SESSION_ID)

    @classmethod
    def get_request_id(cls) -> Optional[str]:
        """获取当前请求ID"""
        return RequestContext.get(cls.REQUEST_ID)

    @classmethod
    def get_agent_name(cls) -> Optional[str]:
        """获取当前Agent名称"""
        return RequestContext.get(cls.AGENT_NAME)
