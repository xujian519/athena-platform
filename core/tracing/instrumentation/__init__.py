"""
自动埋点模块

提供各组件的自动追踪装饰器和工具。
"""

from .agent import trace_agent, trace_agent_method
from .llm import trace_llm_call, trace_llm_method, LLMTracer, LLMSpanContext
from .database import (
    trace_database_operation,
    DatabaseTracer,
    DatabaseSpanContext,
)
from .http import trace_http_request
from .gateway import (
    trace_gateway_request,
    trace_agent_communication,
    trace_gateway_method,
    GatewayTracerMixin,
    GatewayService,
    MessageType,
)

__all__ = [
    "trace_agent",
    "trace_agent_method",
    "trace_llm_call",
    "trace_llm_method",
    "LLMTracer",
    "LLMSpanContext",
    "trace_database_operation",
    "DatabaseTracer",
    "DatabaseSpanContext",
    "trace_http_request",
    # Gateway追踪
    "trace_gateway_request",
    "trace_agent_communication",
    "trace_gateway_method",
    "GatewayTracerMixin",
    "GatewayService",
    "MessageType",
]
