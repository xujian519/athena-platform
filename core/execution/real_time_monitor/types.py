#!/usr/bin/env python3
from __future__ import annotations
"""
实时执行监控系统 - 类型定义
Real-time Execution Monitoring System - Type Definitions

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表盘
    HISTOGRAM = "histogram"  # 直方图
    SUMMARY = "summary"  # 摘要


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResourceStatus(Enum):
    """资源状态"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """指标定义"""

    name: str
    metric_type: MetricType
    description: str
    labels: dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""


@dataclass
class Alert:
    """告警信息"""

    alert_id: str
    name: str
    level: AlertLevel
    message: str
    metric_name: str
    threshold: float
    current_value: float
    triggered_at: datetime
    resolved_at: datetime | None = None
    acknowledged: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """性能快照"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: dict[str, float]
    active_tasks: int
    queued_tasks: int
    response_time: float
    throughput: float
    error_rate: float


@dataclass
class MonitoringConfig:
    """监控配置"""

    collection_interval: float = 1.0  # 收集间隔(秒)
    retention_period: int = 86400  # 保留期(秒)
    enable_system_monitoring: bool = True
    enable_performance_monitoring: bool = True
    enable_custom_metrics: bool = True
    enable_alerts: bool = True
    alert_cooldown: int = 60  # 告警冷却期(秒)
    webhook_url: Optional[str] = None  # Webhook通知URL
    websocket_port: int = 8765  # WebSocket端口
