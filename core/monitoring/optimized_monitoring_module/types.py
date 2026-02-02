#!/usr/bin/env python3
"""
优化版监控告警模块 - 类型定义
Optimized Monitoring and Alerting Module - Type Definitions

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class MetricType(Enum):
    """指标类型

    类型说明:
    - COUNTER: 计数器,只增不减的值
    - GAUGE: 仪表盘,可增可减的瞬时值
    - HISTOGRAM: 直方图,记录值的分布
    - TIMER: 计时器,记录时间持续时间
    """
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    """告警级别

    级别说明:
    - INFO: 信息级别,仅供参考
    - WARNING: 警告级别,需要关注
    - ERROR: 错误级别,需要处理
    - CRITICAL: 严重级别,需要立即处理
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态

    状态说明:
    - ACTIVE: 活跃状态,告警正在发生
    - RESOLVED: 已解决,告警条件已消除
    - SUPPRESSED: 已抑制,告警被人工抑制
    """
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class MetricValue:
    """指标值

    表示单个指标的值及其元数据。

    Attributes:
        name: 指标名称
        value: 指标值
        timestamp: 时间戳
        labels: 标签字典
        metric_type: 指标类型
    """
    name: str
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class AlertRule:
    """告警规则

    定义触发告警的条件和行为。

    Attributes:
        id: 规则ID
        name: 规则名称
        description: 规则描述
        metric_name: 监控的指标名称
        condition: 条件运算符 (>, <, >=, <=, ==, !=)
        threshold: 阈值
        level: 告警级别
        duration: 持续时间(条件需持续多久才触发)
        labels: 标签过滤器
        enabled: 是否启用
        last_triggered: 最后触发时间
        trigger_count: 触发次数统计
    """
    id: str
    name: str
    description: str
    metric_name: str
    condition: str  # >, <, >=, <=, ==, !=
    threshold: float
    level: AlertLevel
    duration: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    labels: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    last_triggered: datetime | None = None
    trigger_count: int = 0


@dataclass
class Alert:
    """告警

    表示一个已触发的告警。

    Attributes:
        id: 告警ID
        rule_id: 关联的规则ID
        name: 告警名称
        description: 告警描述
        level: 告警级别
        status: 告警状态
        message: 告警消息
        timestamp: 触发时间
        resolved_at: 解决时间
        metric_values: 相关指标值列表
        labels: 标签字典
    """
    id: str
    rule_id: str
    name: str
    description: str
    level: AlertLevel
    status: AlertStatus
    message: str
    timestamp: datetime
    resolved_at: datetime | None = None
    metric_values: list[MetricValue] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
