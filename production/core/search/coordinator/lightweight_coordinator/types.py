#!/usr/bin/env python3
from __future__ import annotations
"""
轻量协调器 - 数据类型定义
Lightweight Coordinator - Data Types

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ConfigType(Enum):
    """配置类型枚举"""

    API_KEYS = "api_keys"
    RATE_LIMITS = "rate_limits"
    TIMEOUTS = "timeouts"
    FEATURES = "features"
    CUSTOM = "custom"


class MetricType(Enum):
    """指标类型枚举"""

    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    USAGE = "usage"
    ERRORS = "errors"
    CUSTOM = "custom"


class AlertLevel(Enum):
    """告警级别枚举"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ConfigItem:
    """配置项"""

    key: str
    value: Any
    type: ConfigType
    description: str
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    scope: str = "global"  # global, tool_name
    encrypted: bool = False


@dataclass
class MetricPoint:
    """指标数据点"""

    tool_name: str
    metric_type: MetricType
    metric_name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """健康状态"""

    tool_name: str
    status: str  # healthy, warning, error, critical
    score: float  # 0-1
    last_check: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """告警信息"""

    id: str
    level: AlertLevel
    title: str
    message: str
    tool_name: str | None = None
    metric_point: MetricPoint | None = None
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False


__all__ = [
    "ConfigType",
    "MetricType",
    "AlertLevel",
    "ConfigItem",
    "MetricPoint",
    "HealthStatus",
    "Alert",
]
