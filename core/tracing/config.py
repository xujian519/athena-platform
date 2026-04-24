"""
OpenTelemetry追踪配置模块

提供追踪系统的配置管理，包括采样率、导出端点、超时设置等。
"""

from dataclasses import dataclass, field
from typing import Optional
from os import getenv


@dataclass
class TracingConfig:
    """
    OpenTelemetry追踪配置

    Attributes:
        service_name: 服务名称，用于标识追踪来源
        otlp_endpoint: OTLP导出端点（默认使用OpenTelemetry Collector）
        jaeger_endpoint: Jaeger导出端点（兼容旧系统）
        sample_rate: 采样率（0.0-1.0），默认1%用于生产环境
        trace_export_timeout_ms: 追踪导出超时时间（毫秒）
        max_queue_size: 最大队列大小
        schedule_delay_millis: 批处理导出延迟（毫秒）
        enabled: 是否启用追踪
        environment: 环境标识（dev/test/prod）
    """

    service_name: str = "athena-platform"
    otlp_endpoint: str = field(
        default_factory=lambda: getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )
    jaeger_endpoint: str = field(
        default_factory=lambda: getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
    )
    sample_rate: float = field(
        default_factory=lambda: float(getenv("OTEL_TRACE_SAMPLE_RATE", "0.01"))
    )
    trace_export_timeout_ms: int = 30000
    max_queue_size: int = 2048
    schedule_delay_millis: int = 5000
    enabled: bool = field(
        default_factory=lambda: getenv("OTEL_TRACING_ENABLED", "true").lower() == "true"
    )
    environment: str = field(
        default_factory=lambda: getenv("ENVIRONMENT", "dev")
    )

    def __post_init__(self):
        """配置验证"""
        if not 0.0 <= self.sample_rate <= 1.0:
            raise ValueError(f"采样率必须在0.0-1.0之间，当前值: {self.sample_rate}")

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment.lower() in ("prod", "production")

    @property
    def effective_sample_rate(self) -> float:
        """获取有效采样率（生产环境使用配置值，开发环境更高）"""
        if self.is_production:
            return self.sample_rate
        # 开发环境使用更高采样率便于调试
        return min(self.sample_rate * 10, 1.0)


# 预定义配置实例
DEV_CONFIG = TracingConfig(
    service_name="athena-platform-dev",
    sample_rate=0.1,  # 开发环境10%采样
    environment="dev"
)

TEST_CONFIG = TracingConfig(
    service_name="athena-platform-test",
    sample_rate=1.0,  # 测试环境100%采样
    environment="test"
)

PROD_CONFIG = TracingConfig(
    service_name="athena-platform-prod",
    sample_rate=0.01,  # 生产环境1%采样
    environment="prod"
)


def get_config() -> TracingConfig:
    """
    获取当前环境的追踪配置

    根据环境变量ENVIRONMENT自动选择合适的配置。
    """
    env = getenv("ENVIRONMENT", "dev").lower()

    if env in ("prod", "production"):
        return PROD_CONFIG
    elif env == "test":
        return TEST_CONFIG
    else:
        return DEV_CONFIG
