"""
导出器配置模块

提供各种追踪导出器的工厂函数和配置。
"""

from typing import Optional
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
    SpanProcessor
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# 尝试导入JaegerExporter（可选依赖）
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False
    JaegerExporter = None  # type: ignore

from .config import TracingConfig


class ConsoleSpanExporter(SpanExporter):
    """
    控制台导出器

    用于开发和调试，将Span输出到控制台。
    """

    def export(self, spans):
        """导出Span到控制台"""
        for span in spans:
            print(f"[TRACE] {span.name}")
            if span.attributes:
                for key, value in span.attributes.items():
                    print(f"  {key}: {value}")
        return SpanExportResult.SUCCESS

    def shutdown(self):
        """关闭导出器"""
        pass

    def force_flush(self, timeout_millis: int = 30000):
        return True


def create_otlp_exporter(
    endpoint: str,
    headers: Optional[dict] = None,
    timeout: int = 30000
) -> OTLPSpanExporter:
    """
    创建OTLP导出器

    Args:
        endpoint: OTLP端点（如http://localhost:4317）
        headers: 可选的HTTP headers
        timeout: 超时时间（毫秒）

    Returns:
        OTLPSpanExporter实例
    """
    return OTLPSpanExporter(
        endpoint=endpoint,
        headers=headers or {},
        timeout=timeout / 1000  # 转换为秒
    )


def create_jaeger_exporter(
    agent_host_name: str = "localhost",
    agent_port: int = 6831,
    endpoint: Optional[str] = None
) -> Optional[SpanExporter]:
    """
    创建Jaeger导出器

    Args:
        agent_host_name: Jaeger Agent主机名
        agent_port: Jaeger Agent端口
        endpoint: Jaeger Collector端点（可选）

    Returns:
        JaegerExporter实例，如果不可用则返回None
    """
    if not JAEGER_AVAILABLE:
        import warnings
        warnings.warn(
            "Jaeger exporter不可用，请安装opentelemetry-exporter-jaeger-thrift。"
            "将使用OTLP导出器代替。"
        )
        return None

    if endpoint:
        return JaegerExporter(  # type: ignore
            collector_endpoint=endpoint
        )
    return JaegerExporter(  # type: ignore
        agent_host_name=agent_host_name,
        agent_port=agent_port
    )


def create_batch_processor(
    exporter: SpanExporter,
    max_queue_size: int = 2048,
    schedule_delay_millis: int = 5000,
    export_timeout_millis: int = 30000
) -> BatchSpanProcessor:
    """
    创建批处理器

    Args:
        exporter: 底层导出器
        max_queue_size: 最大队列大小
        schedule_delay_millis: 调度延迟（毫秒）
        export_timeout_millis: 导出超时（毫秒）

    Returns:
        BatchSpanProcessor实例
    """
    return BatchSpanProcessor(
        exporter=exporter,
        max_queue_size=max_queue_size,
        schedule_delay_millis=schedule_delay_millis,
        export_timeout_millis=export_timeout_millis
    )


def create_simple_processor(exporter: SpanExporter) -> SimpleSpanProcessor:
    """
    创建简单处理器（每个Span立即导出）

    Args:
        exporter: 底层导出器

    Returns:
        SimpleSpanProcessor实例
    """
    return SimpleSpanProcessor(exporter=exporter)


def create_processor_from_config(config: TracingConfig) -> SpanProcessor:
    """
    根据配置创建处理器

    Args:
        config: 追踪配置

    Returns:
        SpanProcessor实例
    """
    # 根据配置选择导出器
    if config.otlp_endpoint:
        exporter = create_otlp_exporter(
            endpoint=config.otlp_endpoint,
            timeout=config.trace_export_timeout_ms
        )
    else:
        # 默认使用控制台导出器
        exporter = ConsoleSpanExporter()

    # 创建批处理器
    return create_batch_processor(
        exporter=exporter,
        max_queue_size=config.max_queue_size,
        schedule_delay_millis=config.schedule_delay_millis,
        export_timeout_millis=config.trace_export_timeout_ms
    )


def create_console_processor() -> SimpleSpanProcessor:
    """创建控制台处理器（用于开发调试）"""
    return SimpleSpanProcessor(exporter=ConsoleSpanExporter())
