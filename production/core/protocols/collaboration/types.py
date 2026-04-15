#!/usr/bin/env python3
"""
协作协议 - 数据模型
Collaboration Protocols - Data Models

定义协议相关的数据结构

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class ProtocolType(Enum):
    """协议类型枚举"""

    COMMUNICATION = "communication"  # 通信协议
    COORDINATION = "coordination"  # 协调协议
    DECISION = "decision"  # 决策协议
    SYNCHRONIZATION = "synchronization"  # 同步协议
    NEGOTIATION = "negotiation"  # 协商协议
    CONFLICT_RESOLUTION = "conflict_resolution"  # 冲突解决协议


class ProtocolPhase(Enum):
    """协议阶段枚举"""

    INITIALIZATION = "initialization"  # 初始化阶段
    NEGOTIATION = "negotiation"  # 协商阶段
    EXECUTION = "execution"  # 执行阶段
    MONITORING = "monitoring"  # 监控阶段
    TERMINATION = "termination"  # 终止阶段
    ERROR_HANDLING = "error_handling"  # 错误处理阶段


class ProtocolStatus(Enum):
    """协议状态枚举"""

    ACTIVE = "active"  # 活跃状态
    SUSPENDED = "suspended"  # 暂停状态
    COMPLETED = "completed"  # 完成状态
    FAILED = "failed"  # 失败状态
    TIMEOUT = "timeout"  # 超时状态


@dataclass
class ProtocolMessage:
    """协议消息"""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: str = ""  # 协议ID
    sender_id: str = ""  # 发送者ID
    receiver_id: str = ""  # 接收者ID
    message_type: str = ""  # 消息类型
    content: dict[str, Any] = field(default_factory=dict)  # 消息内容
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    priority: int = 1  # 优先级 (1-10)
    requires_ack: bool = False  # 是否需要确认
    ttl: timedelta | None = None  # 生存时间
    retry_count: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数


@dataclass
class ProtocolContext:
    """协议上下文"""

    protocol_id: str = ""  # 协议ID
    protocol_type: ProtocolType = ProtocolType.COMMUNICATION
    participants: list[str] = field(default_factory=list)  # 参与者
    current_phase: ProtocolPhase = ProtocolPhase.INITIALIZATION
    status: ProtocolStatus = ProtocolStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    timeout: timedelta | None = None
    shared_state: dict[str, Any] = field(default_factory=dict)  # 共享状态
    private_states: dict[str, dict[str, Any]] = field(default_factory=dict)  # 私有状态
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据
