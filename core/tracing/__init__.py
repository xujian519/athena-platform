"""
OpenTelemetry追踪模块

提供Athena平台的分布式追踪功能。

主要组件:
- AthenaTracer: 专用追踪器
- TracingConfig: 配置管理
- setup_tracing: 快速初始化函数

Example:
    >>> from core.tracing import setup_tracing, AthenaTracer
    >>>
    >>> # 初始化追踪
    >>> setup_tracing(service_name="my-service")
    >>>
    >>> # 使用追踪器
    >>> tracer = AthenaTracer("my-service")
    >>> with tracer.start_agent_span("xiaona", "patent_analysis"):
    ...     result = process_patent()
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from .config import TracingConfig, get_config, DEV_CONFIG, TEST_CONFIG, PROD_CONFIG
from .tracer import (
    AthenaTracer,
    get_default_tracer,
    trace_method,
    record_exception,
    record_error,
    add_span_attributes,
    set_span_ok,
    ExceptionRecorder,
)
from .context import RequestContext, TraceContext, AgentSessionContext
from .propagator import TracePropagator, get_propagator
from .exporter import (
    create_otlp_exporter,
    create_jaeger_exporter,
    create_batch_processor,
    create_processor_from_config,
    create_console_processor
)

__all__ = [
    # 配置
    "TracingConfig",
    "get_config",
    "DEV_CONFIG",
    "TEST_CONFIG",
    "PROD_CONFIG",
    # 追踪器
    "AthenaTracer",
    "get_default_tracer",
    "trace_method",
    # 异常记录
    "record_exception",
    "record_error",
    "add_span_attributes",
    "set_span_ok",
    "ExceptionRecorder",
    # 上下文
    "RequestContext",
    "TraceContext",
    "AgentSessionContext",
    # 传播
    "TracePropagator",
    "get_propagator",
    # 导出器
    "create_otlp_exporter",
    "create_jaeger_exporter",
    "create_batch_processor",
    "create_processor_from_config",
    "create_console_processor",
    # 初始化
    "setup_tracing",
    "shutdown_tracing",
]


# 全局状态
_provider: TracerProvider | None = None
_initialized: bool = False


def setup_tracing(
    service_name: str,
    config: TracingConfig | None = None,
    processors: list[SpanProcessor] | None = None
) -> TracerProvider:
    """
    初始化OpenTelemetry追踪

    Args:
        service_name: 服务名称
        config: 追踪配置，默认使用环境配置
        processors: 自定义处理器列表，默认使用配置创建

    Returns:
        TracerProvider实例

    Example:
        >>> provider = setup_tracing(
        ...     service_name="athena-gateway",
        ...     config=PROD_CONFIG
        ... )
    """
    global _provider, _initialized

    if _initialized:
        return _provider

    config = config or get_config()

    # 创建资源
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "service.version": "1.0.0",
        "deployment.environment": config.environment
    })

    # 创建Provider
    _provider = TracerProvider(resource=resource)

    # 添加处理器
    if processors:
        for processor in processors:
            _provider.add_span_processor(processor)
    else:
        # 使用配置创建处理器
        processor = create_processor_from_config(config)
        _provider.add_span_processor(processor)

    # 设置全局Provider
    trace.set_tracer_provider(_provider)
    _initialized = True

    return _provider


def shutdown_tracing() -> None:
    """关闭追踪系统，刷新所有待处理的Span"""
    global _provider, _initialized

    if _provider:
        _provider.shutdown()
        _provider = None
        _initialized = False


def is_initialized() -> bool:
    """检查追踪系统是否已初始化"""
    return _initialized
