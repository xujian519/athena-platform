"""
生产环境模块 - Production Module

提供生产环境的配置、日志收集、告警等功能
"""

from __future__ import annotations
from .log_collector import (
    JSONFormatter,
    LoggerAdapter,
    LoggerFactory,
    RequestContextLogger,
    StructuredLogger,
    log_execution_time,
)
from .production_config import (
    DEFAULT_ALERT_RULES,
    AlertRule,
    HealthCheckConfig,
    LogConfig,
    MetricsConfig,
    NotificationChannel,
    ProductionConfig,
    ProductionConfigManager,
)

__all__ = [
    # 生产配置
    "AlertRule",
    "NotificationChannel",
    "LogConfig",
    "MetricsConfig",
    "HealthCheckConfig",
    "ProductionConfig",
    "ProductionConfigManager",
    "DEFAULT_ALERT_RULES",

    # 日志收集
    "JSONFormatter",
    "StructuredLogger",
    "LoggerAdapter",
    "RequestContextLogger",
    "LoggerFactory",
    "log_execution_time",
]
