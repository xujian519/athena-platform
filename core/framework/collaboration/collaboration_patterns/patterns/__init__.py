#!/usr/bin/env python3

"""
协作模式实现
Collaboration Patterns Implementation

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0

导出所有协作模式实现。
"""
from .swarm_communication import (
    SwarmCommunicationProtocol,
    SwarmGossipProtocol,
    SwarmKnowledgeSharing,
    SwarmMessage,
)
from .swarm_models import (
    AgentState,
    Proposal,
    SwarmConsensusType,
    SwarmDecisionType,
    SwarmEmergencyType,
    SwarmKnowledgeItem,
    SwarmMessageType,
    SwarmRole,
    SwarmStatistics,
)

__all__ = [
    # 原有模式
    "SequentialCollaborationPattern",
    "ParallelCollaborationPattern",
    "HierarchicalCollaborationPattern",
    "ConsensusCollaborationPattern",
    # Swarm模式
    "SwarmCollaborationPattern",
    "SwarmAgent",
    "SwarmCommunicationProtocol",
    "SwarmGossipProtocol",
    "SwarmKnowledgeSharing",
    "SwarmMessage",
    "SwarmDecisionEngine",
    # Swarm数据模型
    "AgentState",
    "Proposal",
    "SwarmRole",
    "SwarmMessageType",
    "SwarmDecisionType",
    "SwarmConsensusType",
    "SwarmEmergencyType",
    "SwarmKnowledgeItem",
    "SwarmStatistics",
    "SwarmSharedState",
]

