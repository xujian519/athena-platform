#!/usr/bin/env python3
"""
协作协议 - 统一接口
Collaboration Protocols - Unified Interface

提供智能体协作协议的完整实现

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0

使用示例:
    from core.protocols.collaboration import (
        CommunicationProtocol,
        CoordinationProtocol,
        DecisionProtocol,
        ProtocolManager,
        create_protocol_session,
    )

    # 使用协议管理器
    manager = ProtocolManager()
    protocol_id = manager.create_communication_protocol(
        participants=["agent1", "agent2"]
    )

    # 使用便捷函数
    protocol_id = create_protocol_session(
        protocol_type="communication",
        participants=["agent1", "agent2"]
    )
"""

# 数据模型
# 基础类
from __future__ import annotations
from .base import BaseProtocol

# 管理器和工具
from .manager import ProtocolManager, protocol_manager

# 协议实现
from .protocols.communication import CommunicationProtocol
from .protocols.coordination import CoordinationProtocol
from .protocols.decision import DecisionProtocol
from .types import (
    ProtocolContext,
    ProtocolMessage,
    ProtocolPhase,
    ProtocolStatus,
    ProtocolType,
)
from .utils import (
    create_protocol_session,
    get_protocol_session_status,
    shutdown_protocol_manager,
    start_protocol_session,
)

__all__ = [
    # 数据模型
    "ProtocolType",
    "ProtocolPhase",
    "ProtocolStatus",
    "ProtocolMessage",
    "ProtocolContext",
    # 基础类
    "BaseProtocol",
    # 协议实现
    "CommunicationProtocol",
    "CoordinationProtocol",
    "DecisionProtocol",
    # 管理器和工具
    "ProtocolManager",
    "protocol_manager",
    "create_protocol_session",
    "start_protocol_session",
    "get_protocol_session_status",
    "shutdown_protocol_manager",
]
