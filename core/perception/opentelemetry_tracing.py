#!/usr/bin/env python3
from __future__ import annotations

"""
OpenTelemetry分布式追踪模块
OpenTelemetry Distributed Tracing Module

为感知模块提供OpenTelemetry标准的分布式追踪功能,
支持请求链路追踪、性能分析和问题诊断。

功能特性:
1. 自动span创建和传播
2. 性能指标采集
3. 错误追踪和报告
4. 上下文传播
5. 与Prometheus/Grafana集成

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import inspect
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any

# OpenTelemetry导入(可选依赖)
try:
    from opentelemetry import trace
    from opentelemetry.context import Context
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    # 支持的导出器
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter

        JAEGAR_AVAILABLE = True
    except ImportError:
        JAEGAR_AVAILABLE = False

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        OTLP_AVAILABLE = True
    except ImportError:
        OTLP_AVAILABLE = False

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    JAEGAR_AVAILABLE = False
    OTLP_AVAILABLE = False

logger = logging.getLogger(__name__)


class TracerBackend(Enum):
    """追踪后端类型"""

    CONSOLE = "console"  # 控制台输出(开发调试)
    JAEGER = "jaeger"  # Jaeger分布式追踪
    OTLP = "otlp"  # OpenTelemetry Protocol
    NONE = "none"  # 不启用追踪


@dataclass
class TracingConfig:
    """追踪配置"""

    enabled: bool = True
    backend: TracerBackend = TracerBackend.CONSOLE
    service_name: str = "athena-perception"
    service_version: str = "1.0.0"
    sample_rate: float = 1.0  # 采样率(0.0-1.0)

    # Jaeger配置
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    jaeger_agent_host_name: str = "localhost"
    jaeger_agent_port: int = 6831

    # OTLP配置
    otlp_endpoint: str = "http://localhost:4317"
    otlp_headers: dict[str, str] = field(default_factory=dict)

    # 其他配置
    export_timeout_ms: int = 30000
    max_queue_size: int = 2048
    schedule_delay_millis: int = 5000


class PerceptionTracer:
    """感知模块追踪器

    提供OpenTelemetry标准的分布式追踪功能。

    使用示例:
        >>> tracer = PerceptionTracer()
        >>> await tracer.initialize()
        >>>
        >>> # 使用装饰器
        >>> @tracer.trace_method("process_document")
        >>> async def process_document(doc):
        >>>     ...
        >>>
        >>> # 或使用上下文管理器
        >>> async with tracer.trace_operation("analyze"):
        >>>     ...
    """

    def __init__(self, config: TracingConfig | None = None):
        """初始化追踪器

        Args:
            config: 追踪配置
        """
        self.config = config or TracingConfig()
        self.tracer = None
        self.provider = None
        self.propagator = TraceContextTextMapPropagator() if OPENTELEMETRY_AVAILABLE else None

        if not OPENTELEMETRY_AVAILABLE:
            logger.warning(
                "⚠️ OpenTelemetry未安装,追踪功能将被禁用。"
                "安装命令: pip install opentelemetry-api opentelemetry-sdk"
            )
            self.config.enabled = False

        logger.info(
            f"🔍 初始化追踪器 (enabled={self.config.enabled}, backend={self.config.backend.value})"
        )

    async def initialize(self) -> None:
        """初始化追踪器"""
        if not self.config.enabled or not OPENTELEMETRY_AVAILABLE:
            logger.info("⏭️ 追踪功能未启用")
            return

        try:
            # 创建资源
            resource = Resource.create(
                {
                    SERVICE_NAME: self.config.service_name,
                    SERVICE_VERSION: self.config.service_version,
                }
            )

            # 创建TracerProvider
            self.provider = TracerProvider(resource=resource)

            # 配置导出器
            if self.config.backend == TracerBackend.CONSOLE:
                exporter = ConsoleSpanExporter()
                self.provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info("📺 使用控制台导出器")

            elif self.config.backend == TracerBackend.JAEGER:
                if not JAEGAR_AVAILABLE:
                    logger.warning(
                        "⚠️ Jaeger导出器不可用,回退到控制台导出器。"
                        "安装命令: pip install opentelemetry-exporter-jaeger"
                    )
                    exporter = ConsoleSpanExporter()
                else:
                    exporter = JaegerExporter(
                        agent_host_name=self.config.jaeger_agent_host_name,
                        agent_port=self.config.jaeger_agent_port,
                    )
                    logger.info(
                        f"🦊 使用Jaeger导出器 ({self.config.jaeger_agent_host_name}:{self.config.jaeger_agent_port})"
                    )

                self.provider.add_span_processor(BatchSpanProcessor(exporter))

            elif self.config.backend == TracerBackend.OTLP:
                if not OTLP_AVAILABLE:
                    logger.warning(
                        "⚠️ OTLP导出器不可用,回退到控制台导出器。"
                        "安装命令: pip install opentelemetry-exporter-otlp"
                    )
                    exporter = ConsoleSpanExporter()
                else:
                    exporter = OTLPSpanExporter(
                        endpoint=self.config.otlp_endpoint,
                        headers=self.config.otlp_headers,
                    )
                    logger.info(f"📡 使用OTLP导出器 ({self.config.otlp_endpoint})")

                self.provider.add_span_processor(BatchSpanProcessor(exporter))

            # 设置全局TracerProvider
            trace.set_tracer_provider(self.provider)

            # 获取Tracer
            self.tracer = trace.get_tracer(__name__)

            logger.info("✅ OpenTelemetry追踪器初始化完成")

        except Exception as e:
            logger.error(f"❌ 追踪器初始化失败: {e}")
            self.tracer = None

    @asynccontextmanager
    async def trace_operation(
        self,
        operation_name: str,
        attributes: dict[str, Any] | None = None,
    ):
        """追踪操作上下文管理器

        Args:
            operation_name: 操作名称
            attributes: 附加属性

        Yields:
            Span对象
        """
        if not self.tracer:
            yield None
            return

        span = self.tracer.start_span(
            operation_name,
            attributes=attributes or {},
        )

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        finally:
            span.end()

    def trace_method(self, operation_name: str | None = None):
        """方法追踪装饰器

        Args:
            operation_name: 操作名称(默认使用方法名)

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.tracer:
                    return await func(*args, **kwargs)

                op_name = operation_name or func.__name__
                attributes = {
                    "function": func.__name__,
                    "module": func.__module__,
                }

                with self.tracer.start_as_current_span(
                    op_name,
                    attributes=attributes,
                ) as span:
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.tracer:
                    return func(*args, **kwargs)

                op_name = operation_name or func.__name__
                attributes = {
                    "function": func.__name__,
                    "module": func.__module__,
                }

                with self.tracer.start_as_current_span(
                    op_name,
                    attributes=attributes,
                ) as span:
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise

            # 根据函数类型返回异步或同步包装器
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """添加事件到当前span

        Args:
            name: 事件名称
            attributes: 事件属性
        """
        if not self.tracer:
            return

        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.add_event(name, attributes or {})

    def set_attribute(self, key: str, value: Any) -> None:
        """设置当前span的属性

        Args:
            key: 属性键
            value: 属性值
        """
        if not self.tracer:
            return

        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.set_attribute(key, value)

    def record_error(self, error: Exception) -> None:
        """记录错误到当前span

        Args:
            error: 异常对象
        """
        if not self.tracer:
            return

        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.record_exception(error)
            current_span.set_status(Status(StatusCode.ERROR, str(error)))

    def inject_context(self, carrier: dict[str, str]) -> None:
        """注入追踪上下文到载体

        Args:
            carrier: 载体字典(用于HTTP headers等)
        """
        if not self.propagator:
            return

        ctx = Context()
        self.propagator.inject(carrier, context=ctx)

    def extract_context(self, carrier: dict[str, str]) -> Context | None:
        """从载体提取追踪上下文

        Args:
            carrier: 载体字典

        Returns:
            提取的上下文
        """
        if not self.propagator:
            return None

        return self.propagator.extract(carrier)

    async def shutdown(self) -> None:
        """关闭追踪器"""
        if self.provider:
            self.provider.shutdown()
            logger.info("⏹️ 追踪器已关闭")


# 全局追踪器实例
_global_tracer: PerceptionTracer | None = None


def get_tracer(config: TracingConfig | None = None) -> PerceptionTracer:
    """获取全局追踪器实例

    Args:
        config: 追踪配置

    Returns:
        追踪器实例
    """
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = PerceptionTracer(config)
    return _global_tracer


async def initialize_tracing(config: TracingConfig | None = None) -> PerceptionTracer:
    """初始化全局追踪器

    Args:
        config: 追踪配置

    Returns:
        追踪器实例
    """
    tracer = get_tracer(config)
    await tracer.initialize()
    return tracer


# 便捷装饰器
def trace(operation_name: str | None = None) -> Callable:
    """追踪装饰器(使用全局追踪器)

    Args:
        operation_name: 操作名称

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer.tracer:
                return await func(*args, **kwargs)

            op_name = operation_name or func.__name__
            with tracer.tracer.start_as_current_span(op_name):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer.tracer:
                return func(*args, **kwargs)

            op_name = operation_name or func.__name__
            with tracer.tracer.start_as_current_span(op_name):
                return func(*args, **kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


__all__ = [
    "PerceptionTracer",
    "TracerBackend",
    "TracingConfig",
    "get_tracer",
    "initialize_tracing",
    "trace",
]
