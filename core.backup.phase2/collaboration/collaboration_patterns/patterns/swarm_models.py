#!/usr/bin/env python3
from __future__ import annotations

"""
Swarm协作模式数据模型
Swarm Collaboration Pattern Data Models

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

定义Swarm群体智能协作模式的核心数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


# ============================================================================
# 枚举类型定义
# ============================================================================


class SwarmRole(Enum):
    """Swarm角色枚举

    定义群体中成员可以承担的角色类型。
    """

    EXPLORER = "explorer"  # 探索者：发现新信息、搜索资源
    WORKER = "worker"  # 工作者：执行具体任务
    ANALYZER = "analyzer"  # 分析者：处理和分析数据
    COORDINATOR = "coordinator"  # 协调者：轻量级协调（非强制）
    OBSERVER = "observer"  # 观察者：监控状态、收集指标
    SCOUT = "scout"  # 侦察兵：快速侦察、风险评估


class SwarmMessageType(Enum):
    """Swarm消息类型枚举

    定义群体内部通信的消息类型。
    """

    # 协调消息
    JOIN_SWARM = "join_swarm"  # 加入群体
    LEAVE_SWARM = "leave_swarm"  # 离开群体
    ROLE_CHANGE = "role_change"  # 角色变更
    HEARTBEAT = "heartbeat"  # 心跳信号

    # 任务消息
    TASK_ANNOUNCE = "task_announce"  # 任务公告
    TASK_CLAIM = "task_claim"  # 任务认领
    TASK_COMPLETE = "task_complete"  # 任务完成
    TASK_FAILED = "task_failed"  # 任务失败

    # 决策消息
    PROPOSAL = "proposal"  # 提案
    VOTE = "vote"  # 投票
    DECISION = "decision"  # 决策结果
    DISCUSSION = "discussion"  # 讨论

    # 状态消息
    STATE_UPDATE = "state_update"  # 状态更新
    KNOWLEDGE_SHARE = "knowledge_share"  # 知识共享
    KNOWLEDGE_QUERY = "knowledge_query"  # 知识查询

    # 紧急消息
    EMERGENCY = "emergency"  # 紧急情况
    HELP_REQUEST = "help_request"  # 求助信号
    HELP_RESPONSE = "help_response"  # 求助响应


class SwarmDecisionType(Enum):
    """Swarm决策类型枚举

    定义群体决策的机制类型。
    """

    CONSENSUS = "consensus"  # 完全共识（所有人同意）
    MAJORITY = "majority"  # 多数决（超过50%）
    SUPER_MAJORITY = "super_majority"  # 超级多数（通常2/3）
    WEIGHTED = "weighted"  # 加权投票（根据权重）
    DELEGATED = "delegated"  # 委托决策（委托给代表）
    EMERGENCY = "emergency"  # 紧急决策（快速响应）
    AUTOMATIC = "automatic"  # 自动决策（基于规则）


class SwarmConsensusType(Enum):
    """Swarm共识类型枚举

    定义达成共识的具体算法类型。
    """

    FULL_CONSENSUS = "full_consensus"  # 完全共识（100%同意）
    QUORUM_CONSENSUS = "quorum_consensus"  # 法定人数共识
    THRESHOLD_CONSENSUS = "threshold_consensus"  # 阈值共识
    PROBABILISTIC_CONSENSUS = "probabilistic_consensus"  # 概率共识


class SwarmEmergencyType(Enum):
    """Swarm紧急类型枚举

    定义需要紧急响应的情况类型。
    """

    HIGH_PRIORITY = "high_priority"  # 高优先级任务
    DEADLINE = "deadline"  # 截止时间临近
    FAILURE = "failure"  # 成员失败
    SECURITY = "security"  # 安全威胁
    RESOURCE_SHORTAGE = "resource_shortage"  # 资源短缺
    NETWORK_PARTITION = "network_partition"  # 网络分区
    OVERLOAD = "overload"  # 系统过载


# ============================================================================
# 数据类定义
# ============================================================================


@dataclass
class SwarmKnowledgeItem:
    """Swarm知识项

    表示群体中共享的一条知识。
    """

    key: str  # 知识键
    value: Any  # 知识值
    source: str  # 来源Agent ID
    confidence: float  # 置信度 (0.0 - 1.0)
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    ttl: int | None = None  # 生存时间（秒），None表示永久
    version: int = 1  # 版本号
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def is_expired(self) -> bool:
        """检查知识是否已过期"""
        if self.ttl is None:
            return False
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)

    def increment_version(self) -> None:
        """增加版本号"""
        self.version += 1
        self.timestamp = datetime.now()


@dataclass
class SwarmStatistics:
    """Swarm统计信息

    记录群体运行的各种统计数据。
    """

    total_members: int = 0  # 总成员数
    active_members: int = 0  # 活跃成员数
    total_tasks: int = 0  # 总任务数
    completed_tasks: int = 0  # 已完成任务数
    failed_tasks: int = 0  # 失败任务数
    total_decisions: int = 0  # 总决策数
    successful_decisions: int = 0  # 成功决策数
    total_knowledge_items: int = 0  # 总知识条目数
    sync_rounds: int = 0  # 同步轮数
    emergency_count: int = 0  # 紧急情况次数
    average_decision_time: float = 0.0  # 平均决策时间（秒）
    average_task_completion_time: float = 0.0  # 平均任务完成时间（秒）

    def task_success_rate(self) -> float:
        """计算任务成功率"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks

    def decision_success_rate(self) -> float:
        """计算决策成功率"""
        if self.total_decisions == 0:
            return 0.0
        return self.successful_decisions / self.total_decisions

    def member_activity_rate(self) -> float:
        """计算成员活跃率"""
        if self.total_members == 0:
            return 0.0
        return self.active_members / self.total_members

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_members": self.total_members,
            "active_members": self.active_members,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_decisions": self.total_decisions,
            "successful_decisions": self.successful_decisions,
            "total_knowledge_items": self.total_knowledge_items,
            "sync_rounds": self.sync_rounds,
            "emergency_count": self.emergency_count,
            "average_decision_time": self.average_decision_time,
            "average_task_completion_time": self.average_task_completion_time,
            "task_success_rate": self.task_success_rate(),
            "decision_success_rate": self.decision_success_rate(),
            "member_activity_rate": self.member_activity_rate(),
        }


@dataclass
class AgentState:
    """Agent状态

    记录单个Agent在群体中的状态。
    """

    agent_id: str  # Agent ID
    role: SwarmRole  # 当前角色
    status: str  # 状态（active, idle, busy, failed）
    current_load: float  # 当前负载 (0.0 - 1.0)
    capabilities: list[str]  # 能力列表
    neighbors: list[str]  # 邻居列表
    last_heartbeat: datetime  # 最后心跳时间
    tasks_completed: int = 0  # 已完成任务数
    tasks_failed: int = 0  # 失败任务数
    reputation_score: float = 1.0  # 声誉评分 (0.0 - 1.0)
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return (
            self.status == "active"
            and self.current_load < 0.8
            and (datetime.now() - self.last_heartbeat).total_seconds() < 30
        )

    def can_handle_capability(self, capability: str) -> bool:
        """检查Agent是否具有某能力"""
        return capability in self.capabilities

    def update_heartbeat(self) -> None:
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "status": self.status,
            "current_load": self.current_load,
            "capabilities": self.capabilities,
            "neighbors": self.neighbors,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "reputation_score": self.reputation_score,
            "metadata": self.metadata,
        }


@dataclass
class Proposal:
    """提案

    表示群体中的一个决策提案。
    """

    proposal_id: str  # 提案ID
    proposer: str  # 提案者ID
    content: dict[str, Any]  # 提案内容
    proposal_type: str  # 提案类型
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    expires_at: datetime | None = None  # 过期时间
    status: str = "pending"  # 状态（pending, approved, rejected, expired）
    votes: dict[str, dict[str, Any]] = field(default_factory=dict)  # 投票记录
    decision_type: SwarmDecisionType = SwarmDecisionType.MAJORITY  # 决策类型
    consensus_threshold: float = 0.5  # 共识阈值
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def add_vote(self, voter_id: str, vote: str, weight: float = 1.0) -> None:
        """添加投票"""
        self.votes[voter_id] = {
            "vote": vote,
            "weight": weight,
            "timestamp": datetime.now().isoformat(),
        }

    def get_vote_count(self) -> dict[str, int]:
        """获取投票统计"""
        counts = {"agree": 0, "disagree": 0, "abstain": 0}
        for vote_data in self.votes.values():
            vote = vote_data["vote"]
            if vote in counts:
                counts[vote] += 1
        return counts

    def is_expired(self) -> bool:
        """检查提案是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def calculate_result(self) -> str:
        """计算投票结果"""
        counts = self.get_vote_count()
        total_votes = sum(counts.values())

        if total_votes == 0:
            return "no_votes"

        agree_ratio = counts["agree"] / total_votes

        if agree_ratio >= self.consensus_threshold:
            return "approved"
        else:
            return "rejected"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "proposal_id": self.proposal_id,
            "proposer": self.proposer,
            "content": self.content,
            "proposal_type": self.proposal_type,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "votes": self.votes,
            "decision_type": self.decision_type.value,
            "consensus_threshold": self.consensus_threshold,
            "metadata": self.metadata,
        }
