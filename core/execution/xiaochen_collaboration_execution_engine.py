#!/usr/bin/env python3
from __future__ import annotations
"""
小宸·星河射手 - 协作执行引擎
Xiaochen Sagittarius Collaboration Execution Engine

为小宸提供完整的协作执行能力:
1. 智能体间通信协调
2. 协作任务编排
3. 冲突调解
4. 会议管理
5. 协作效果追踪

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "协作之星"
"""

import asyncio
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class CollaborationEventType(Enum):
    """协作事件类型"""

    MESSAGE_EXCHANGE = "message_exchange"  # 消息交换
    TASK_DELEGATION = "task_delegation"  # 任务委派
    KNOWLEDGE_SHARING = "knowledge_sharing"  # 知识共享
    CONFLICT_OCCURRED = "conflict_occurred"  # 冲突发生
    CONFLICT_RESOLVED = "conflict_resolved"  # 冲突解决
    MEETING = "meeting"  # 会议
    JOINT_DECISION = "joint_decision"  # 联合决策


class ConflictSeverity(Enum):
    """冲突严重程度"""

    LOW = "low"  # 低 - 可忽略
    MEDIUM = "medium"  # 中 - 需要处理
    HIGH = "high"  # 高 - 立即处理
    CRITICAL = "critical"  # 严重 - 紧急


@dataclass
class CollaborationEvent:
    """协作事件"""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: CollaborationEventType = CollaborationEventType.MESSAGE_EXCHANGE
    participants: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)
    outcome: str | None = None
    resolved: bool = False


@dataclass
class ConflictRecord:
    """冲突记录"""

    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    involved_agents: list[str] = field(default_factory=list)
    conflict_type: str = ""
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)
    resolution_strategy: str | None = None
    resolved: bool = False  # 添加 resolved 字段
    resolved_at: datetime | None = None
    resolution_outcome: str | None = None


@dataclass
class CollaborationSession:
    """协作会话"""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participants: list[str] = field(default_factory=list)
    purpose: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    events: list[CollaborationEvent] = field(default_factory=list)
    outcomes: dict[str, Any] = field(default_factory=dict)


class XiaochenCollaborationEngine:
    """
    小宸协作执行引擎

    核心功能:
    1. 协作会话管理
    2. 冲突检测和解决
    3. 消息路由协调
    4. 任务委派
    5. 知识共享促进
    6. 协作效果评估
    """

    def __init__(self):
        # 活跃会话
        self.active_sessions: dict[str, CollaborationSession] = {}

        # 协作历史
        self.session_history: deque[CollaborationSession] = deque(maxlen=500)

        # 冲突记录
        self.active_conflicts: dict[str, ConflictRecord] = {}
        self.resolved_conflicts: deque[ConflictRecord] = deque(maxlen=200)

        # 协作统计
        self.collaboration_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "sessions_count": 0,
                "messages_exchanged": 0,
                "tasks_delegated": 0,
                "conflicts_involved": 0,
                "collaboration_score": 0.8,
            }
        )

        # 冲突解决策略
        self.resolution_strategies = {
            ConflictSeverity.LOW: "ignore",
            ConflictSeverity.MEDIUM: "negotiate",
            ConflictSeverity.HIGH: "mediate",
            ConflictSeverity.CRITICAL: "arbitrate",
        }

        logger.info("🏹 小宸协作执行引擎初始化完成")

    async def start_collaboration_session(
        self, participants: list[str], purpose: str, session_type: str = "general"
    ) -> str:
        """开始协作会话"""
        session = CollaborationSession(participants=participants, purpose=purpose)

        self.active_sessions[session.session_id] = session

        # 更新统计
        for participant in participants:
            self.collaboration_stats[participant]["sessions_count"] += 1

        logger.info(f"🤝 协作会话开始: {session.session_id[:8]}... ({len(participants)} 参与者)")

        return session.session_id

    async def add_event(
        self,
        session_id: str,
        event_type: CollaborationEventType,
        data: dict[str, Any],        participants: list[str] | None = None,
    ) -> str:
        """添加协作事件"""
        session = self.active_sessions.get(session_id)

        if not session:
            logger.error(f"会话不存在: {session_id}")
            return ""

        event = CollaborationEvent(
            event_type=event_type, participants=participants or session.participants, data=data
        )

        session.events.append(event)

        # 更新统计
        if event_type == CollaborationEventType.MESSAGE_EXCHANGE:
            for participant in event.participants:
                self.collaboration_stats[participant]["messages_exchanged"] += 1

        elif event_type == CollaborationEventType.TASK_DELEGATION:
            for participant in event.participants:
                self.collaboration_stats[participant]["tasks_delegated"] += 1

        logger.debug(f"📝 协作事件已添加: {event_type.value}")

        return event.event_id

    async def detect_conflict(
        self,
        agent1_id: str,
        agent2_id: str,
        conflict_type: str,
        description: str,
        severity: ConflictSeverity = ConflictSeverity.MEDIUM,
    ) -> str:
        """检测冲突"""
        conflict = ConflictRecord(
            involved_agents=[agent1_id, agent2_id],
            conflict_type=conflict_type,
            severity=severity,
            description=description,
        )

        self.active_conflicts[conflict.conflict_id] = conflict

        # 更新统计
        for agent_id in conflict.involved_agents:
            self.collaboration_stats[agent_id]["conflicts_involved"] += 1

        logger.warning(
            f"⚠️ 冲突检测: {agent1_id} <-> {agent2_id} " f"({conflict_type}, {severity.value})"
        )

        return conflict.conflict_id

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: str | None = None,
        outcome: str | None = None,
    ) -> bool:
        """解决冲突"""
        conflict = self.active_conflicts.get(conflict_id)

        if not conflict:
            logger.error(f"冲突不存在: {conflict_id}")
            return False

        # 选择解决策略
        if not resolution_strategy:
            resolution_strategy = self.resolution_strategies.get(conflict.severity, "negotiate")

        # 应用解决策略
        success = await self._apply_resolution_strategy(conflict, resolution_strategy)

        if success:
            conflict.resolution_strategy = resolution_strategy
            conflict.resolved_at = datetime.now()
            conflict.resolution_outcome = outcome
            conflict.resolved = True

            # 移到已解决
            self.resolved_conflicts.append(conflict)
            del self.active_conflicts[conflict_id]

            logger.info(f"✅ 冲突已解决: {conflict_id[:8]}... ({resolution_strategy})")

            return True
        else:
            logger.error(f"❌ 冲突解决失败: {conflict_id[:8]}...")
            return False

    async def _apply_resolution_strategy(self, conflict: ConflictRecord, strategy: str) -> bool:
        """应用冲突解决策略"""
        if strategy == "ignore":
            # 忽略冲突
            return True

        elif strategy == "negotiate":
            # 协商解决
            await asyncio.sleep(0.1)  # 模拟协商过程
            return True

        elif strategy == "mediate":
            # 调解
            await asyncio.sleep(0.2)
            return True

        elif strategy == "arbitrate":
            # 仲裁
            await asyncio.sleep(0.3)
            return True

        else:
            return False

    async def end_collaboration_session(
        self, session_id: str, outcomes: dict[str, Any] | None = None
    ) -> CollaborationSession:
        """结束协作会话"""
        session = self.active_sessions.get(session_id)

        if not session:
            logger.error(f"会话不存在: {session_id}")
            raise ValueError(f"会话不存在: {session_id}")

        session.ended_at = datetime.now()
        session.outcomes = outcomes or {}

        # 移到历史
        self.session_history.append(session)
        del self.active_sessions[session_id]

        # 计算协作分数
        duration = (session.ended_at - session.started_at).total_seconds()
        event_count = len(session.events)
        collaboration_score = min(1.0, event_count / max(duration / 60, 1))  # 每分钟事件数

        # 更新参与者统计
        for participant in session.participants:
            stats = self.collaboration_stats[participant]
            stats["collaboration_score"] = (
                stats["collaboration_score"] * 0.8 + collaboration_score * 0.2
            )

        logger.info(f"✅ 协作会话结束: {session_id[:8]}... (持续 {duration:.1f} 秒)")

        return session

    async def facilitate_communication(
        self,
        from_agent: str,
        to_agent: str,
        message: dict[str, Any],        session_id: str | None = None,
    ) -> bool:
        """促进智能体间通信"""
        # 添加通信事件
        if session_id:
            await self.add_event(
                session_id=session_id,
                event_type=CollaborationEventType.MESSAGE_EXCHANGE,
                data={"message": message, "from": from_agent, "to": to_agent},
            )

        logger.debug(f"💬 消息传递: {from_agent} -> {to_agent}")

        return True

    async def delegate_task(
        self, from_agent: str, to_agent: str, task: dict[str, Any], session_id: str | None = None
    ) -> bool:
        """委派任务"""
        # 添加任务委派事件
        if session_id:
            await self.add_event(
                session_id=session_id,
                event_type=CollaborationEventType.TASK_DELEGATION,
                data={"task": task, "from": from_agent, "to": to_agent},
            )

        logger.info(f"📋 任务委派: {from_agent} -> {to_agent}")

        return True

    async def share_knowledge(
        self,
        from_agent: str,
        knowledge: dict[str, Any],        participants: list[str],
        session_id: str | None = None,
    ) -> bool:
        """共享知识"""
        # 添加知识共享事件
        if session_id:
            await self.add_event(
                session_id=session_id,
                event_type=CollaborationEventType.KNOWLEDGE_SHARING,
                data={"knowledge": knowledge, "from": from_agent, "to": participants},
                participants=[from_agent, *participants],
            )

        logger.info(f"📚 知识共享: {from_agent} -> {len(participants)} 个智能体")

        return True

    async def get_engine_metrics(self) -> dict[str, Any]:
        """获取引擎指标"""
        total_conflicts = len(self.active_conflicts) + len(self.resolved_conflicts)
        resolved_count = len(self.resolved_conflicts)

        return {
            "sessions": {
                "active": len(self.active_sessions),
                "history": len(self.session_history),
                "avg_duration": (
                    np.mean(
                        [
                            (s.ended_at - s.started_at).total_seconds()
                            for s in self.session_history
                            if s.ended_at
                        ]
                    )
                    if self.session_history
                    else 0
                ),
            },
            "conflicts": {
                "active": len(self.active_conflicts),
                "resolved": resolved_count,
                "resolution_rate": resolved_count / max(total_conflicts, 1),
                "by_severity": {
                    severity.value: sum(
                        1 for c in self.resolved_conflicts if c.severity == severity
                    )
                    for severity in ConflictSeverity
                },
            },
            "collaboration": {
                "total_participants": len(self.collaboration_stats),
                "avg_collaboration_score": (
                    np.mean(
                        [
                            stats["collaboration_score"]
                            for stats in self.collaboration_stats.values()
                        ]
                    )
                    if self.collaboration_stats
                    else 0
                ),
                "top_collaborators": sorted(
                    [
                        (aid, stats["collaboration_score"])
                        for aid, stats in self.collaboration_stats.items()
                    ],
                    key=lambda x: x[1],
                    reverse=True,
                )[:5],
            },
        }


# 导出便捷函数
_xiaochen_engine: XiaochenCollaborationEngine | None = None


def get_xiaochen_collaboration_engine() -> XiaochenCollaborationEngine:
    """获取小宸协作执行引擎单例"""
    global _xiaochen_engine
    if _xiaochen_engine is None:
        _xiaochen_engine = XiaochenCollaborationEngine()
    return _xiaochen_engine
