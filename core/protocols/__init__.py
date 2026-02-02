#!/usr/bin/env python3
"""
多智能体协作协议模块
Multi-Agent Collaboration Protocols Module

提供标准化的多智能体协作协议,包括:
- 通信协议 (Communication Protocol)
- 协调协议 (Coordination Protocol)
- 决策协议 (Decision Protocol)
- 同步协议 (Synchronization Protocol)
- 协商协议 (Negotiation Protocol)
- 冲突解决协议 (Conflict Resolution Protocol)
"""

from datetime import timedelta

from .collaboration import (
    # 基础协议类
    BaseProtocol,
    # 具体协议实现
    CommunicationProtocol,
    CoordinationProtocol,
    DecisionProtocol,
    ProtocolContext,
    # 核心数据类
    ProtocolMessage,
    ProtocolPhase,
    ProtocolStatus,
    # 核心枚举类
    ProtocolType,
)

from .collaboration import (
    ProtocolManager,
    protocol_manager,
)
from .collaboration.utils import (
    create_protocol_session,
    get_protocol_session_status,
    shutdown_protocol_manager,
    start_protocol_session,
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Athena AI Team"

# 导出的主要接口
__all__ = [
    # 基础类
    "BaseProtocol",
    # 协议实现
    "CommunicationProtocol",
    "CoordinationProtocol",
    "DecisionProtocol",
    "ProtocolContext",
    # 管理器
    "ProtocolManager",
    "protocol_manager",
    # 数据类
    "ProtocolMessage",
    "ProtocolPhase",
    "ProtocolStatus",
    # 枚举类
    "ProtocolType",
    # 便捷函数
    "create_communication_protocol",
    "create_coordination_protocol",
    "create_decision_protocol",
    "create_protocol_session",
    "start_protocol_session",
    "get_protocol_session_status",
    "shutdown_protocol_manager",
]


# 便捷函数
def create_communication_protocol(
    protocol_id: str, participants: list[str]
) -> CommunicationProtocol:
    """创建通信协议实例"""
    protocol = CommunicationProtocol(protocol_id)
    for participant in participants:
        protocol.add_participant(participant)
    return protocol


def create_coordination_protocol(protocol_id: str, participants: list[str]) -> CoordinationProtocol:
    """创建协调协议实例"""
    protocol = CoordinationProtocol(protocol_id)
    for participant in participants:
        protocol.add_participant(participant)
    return protocol


def create_decision_protocol(protocol_id: str, participants: list[str]) -> DecisionProtocol:
    """创建决策协议实例"""
    protocol = DecisionProtocol(protocol_id)
    for participant in participants:
        protocol.add_participant(participant)
    return protocol


# 模块级别的配置
DEFAULT_PROTOCOL_TIMEOUT = timedelta(minutes=30)
DEFAULT_MESSAGE_TTL = timedelta(minutes=5)
DEFAULT_RETRY_COUNT = 3
DEFAULT_CONSENSUS_THRESHOLD = 0.7
