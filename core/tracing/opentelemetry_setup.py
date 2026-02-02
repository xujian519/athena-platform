#!/usr/bin/env python3
"""
OpenTelemetry分布式追踪配置
OpenTelemetry Distributed Tracing Setup

集成Jaeger分布式追踪到FastAPI应用
"""

import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# OpenTelemetry导入
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

    OTEL_AVAILABLE = True
except Exception as e:
    OTEL_AVAILABLE = False
    logger.warning(f"⚠️  OpenTelemetry导入失败: {type(e).__name__}: {e}")
    import traceback

    logger.debug(f"OpenTelemetry导入失败详情:\n{traceback.format_exc()}")


class OpenTelemetryManager:
    """OpenTelemetry管理器"""

    def __init__(
        self,
        service_name: str = "athena-prompt-system",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        enabled: bool = True,
    ):
        """
        初始化OpenTelemetry管理器

        Args:
            service_name: 服务名称
            jaeger_host: Jaeger Agent主机
            jaeger_port: Jaeger Agent端口
            enabled: 是否启用追踪
        """
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.enabled = enabled and OTEL_AVAILABLE
        self.tracer = None

        if self.enabled:
            self._setup_tracing()
        else:
            logger.info("⚠️  分布式追踪未启用")

    def _setup_tracing(self):
        """设置追踪"""
        try:
            # 创建资源
            resource = Resource.create(
                {
                    "service.name": self.service_name,
                    "service.version": "2.0.0",
                    "deployment.environment": "production",
                }
            )

            # 创建追踪器提供者
            tracer_provider = TracerProvider(resource=resource)

            # 配置OTLP导出器(使用gRPC连接到collector)
            otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True, timeout=10)

            # 添加批处理器(使用更短的调度延迟以便更快看到追踪数据)
            # 临时使用SimpleSpanProcessor以便立即发送数据进行测试
            span_processor = SimpleSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)

            # 设置全局追踪器提供者
            trace.set_tracer_provider(tracer_provider)

            # 获取追踪器
            self.tracer = trace.get_tracer(__name__)

            logger.info(f"✅ OpenTelemetry追踪已配置: {self.service_name}")
            logger.info("   OTLP Endpoint: localhost:4317")

        except Exception as e:
            logger.error(f"❌ OpenTelemetry配置失败: {e}")
            import traceback

            logger.error(traceback.format_exc())
            self.enabled = False

    def instrument_fastapi(self, app):
        """为FastAPI应用添加自动追踪"""
        if not self.enabled:
            return

        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("✅ FastAPI自动追踪已启用")
        except Exception as e:
            logger.error(f"❌ FastAPI追踪失败: {e}")

    def instrument_httpx(self):
        """为HTTPX客户端添加自动追踪"""
        if not self.enabled:
            return

        try:
            HTTPXClientInstrumentor().instrument()
            logger.info("✅ HTTPX自动追踪已启用")
        except Exception as e:
            logger.error(f"❌ HTTPX追踪失败: {e}")

    def instrument_sqlalchemy(self):
        """为SQLAlchemy添加自动追踪"""
        if not self.enabled:
            return

        try:
            SQLAlchemyInstrumentor().instrument()
            logger.info("✅ SQLAlchemy自动追踪已启用")
        except Exception as e:
            logger.error(f"❌ SQLAlchemy追踪失败: {e}")

    def get_tracer(self):
        """获取追踪器"""
        return self.tracer

    @asynccontextmanager
    async def trace_async(self, operation_name: str, attributes: dict | None = None):
        """
        异步追踪上下文管理器

        Args:
            operation_name: 操作名称
            attributes: 追踪属性
        """
        if not self.enabled or not self.tracer:
            yield
            return

        with self.tracer.start_as_current_span(operation_name, attributes=attributes or {}) as span:
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise

    def trace_sync(self, operation_name: str, attributes: dict | None = None):
        """
        同步追踪装饰器

        Args:
            operation_name: 操作名称
            attributes: 追踪属性
        """

        def decorator(func):
            if not self.enabled or not self.tracer:
                return func

            def wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(
                    operation_name, attributes=attributes or {}
                ) as span:
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        raise

            return wrapper

        return decorator


# 全局实例
_tracing_manager: OpenTelemetryManager = None


def get_tracing_manager(
    service_name: str = "athena-prompt-system", enabled: bool = True
) -> OpenTelemetryManager:
    """
    获取追踪管理器单例

    Args:
        service_name: 服务名称
        enabled: 是否启用

    Returns:
        OpenTelemetryManager实例
    """
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = OpenTelemetryManager(service_name=service_name, enabled=enabled)
    return _tracing_manager


def setup_tracing(
    service_name: str = "athena-prompt-system",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    instrument_fastapi: bool = True,
    instrument_httpx: bool = True,
    instrument_sqlalchemy: bool = False,
    app=None,
) -> OpenTelemetryManager:
    """
    设置分布式追踪

    Args:
        service_name: 服务名称
        jaeger_host: Jaeger Agent主机
        jaeger_port: Jaeger Agent端口
        instrument_fastapi: 是否追踪FastAPI
        instrument_httpx: 是否追踪HTTPX
        instrument_sqlalchemy: 是否追踪SQLAlchemy
        app: FastAPI应用实例(用于instrument_fastapi)

    Returns:
        OpenTelemetryManager实例
    """
    manager = get_tracing_manager(service_name, enabled=True)

    if instrument_fastapi and app is not None:
        logger.info("🔧 配置FastAPI追踪...")
        manager.instrument_fastapi(app)

    if instrument_httpx:
        manager.instrument_httpx()

    if instrument_sqlalchemy:
        manager.instrument_sqlalchemy()

    return manager


# 追踪装饰器(简化版)
def trace_operation(operation_name: Optional[str]
    attributes: Optional["key"] = None):
    """
    操作追踪装饰器

    Args:
        operation_name: 操作名称
        attributes: 追踪属性

    Usage:
        @trace_operation("database_query", {"table": "users"})
        def query_users():
            ...
    """
    manager = get_tracing_manager()
    return manager.trace_sync(operation_name, attributes)
