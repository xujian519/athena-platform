#!/usr/bin/env python3
from __future__ import annotations
"""
安全监控 - 数据类型定义
Security Monitor - Data Types

作者: Athena AI系统
创建时间: 2025-11-15
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SecurityLevel(Enum):
    """安全级别"""

    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中等风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


class AlertType(Enum):
    """警报类型"""

    UNAUTHORIZED_ACCESS = "unauthorized_access"  # 未授权访问
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"  # 异常行为
    RESOURCE_ABUSE = "resource_abuse"  # 资源滥用
    DECISION_MANIPULATION = "decision_manipulation"  # 决策操纵
    SYSTEM_COMPROMISE = "system_compromise"  # 系统入侵
    EMOTIONAL_INSTABILITY = "emotional_instability"  # 情感不稳定
    PERFORMANCE_DEGRADATION = "performance_degradation"  # 性能下降


class ActionType(Enum):
    """处理动作"""

    MONITOR = "monitor"  # 持续监控
    ALERT = "alert"  # 发出警报
    RESTRICT = "restrict"  # 限制访问
    QUARANTINE = "quarantine"  # 隔离系统
    SHUTDOWN = "shutdown"  # 紧急关闭
    ESCALATE = "escalate"  # 上报处理


@dataclass
class SecurityEvent:
    """安全事件"""

    id: str
    event_type: AlertType
    security_level: SecurityLevel
    description: str
    source: str
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)
    affected_components: list[str] = field(default_factory=list)
    mitigation_actions: list[ActionType] = field(default_factory=list)
    resolved: bool = False
    resolution_time: datetime | None = None


@dataclass
class AccessPattern:
    """访问模式"""

    ip_address: str
    user_agent: str
    request_count: int
    failed_attempts: int
    last_access: datetime
    suspicious_indicators: list[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class BehaviorProfile:
    """行为档案"""

    entity_id: str
    entity_type: str  # user, agent, system
    normal_behavior: dict[str, Any] = field(default_factory=dict)
    current_behavior: dict[str, Any] = field(default_factory=dict)
    anomalies_detected: int = 0
    trust_score: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)


__all__ = [
    "SecurityLevel",
    "AlertType",
    "ActionType",
    "SecurityEvent",
    "AccessPattern",
    "BehaviorProfile",
]
