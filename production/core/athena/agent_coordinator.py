#!/usr/bin/env python3
from __future__ import annotations
"""
Athena智能体协调器
Agent Coordinator for Athena

协调多个智能体协同工作:
1. 智能体组队 - 动态组建智能体团队
2. 任务分解 - 将复杂任务分解为子任务
3. 协作协议 - 定义智能体间协作规则
4. 冲突解决 - 处理智能体间的冲突
5. 知识共享 - 促进智能体间知识共享
6. 集体智能 - 汇聚多智能体智慧

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "智能协奏曲"
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """协作模式"""

    SEQUENTIAL = "sequential"  # 顺序协作 - 按顺序执行
    PARALLEL = "parallel"  # 并行协作 - 同时执行
    HIERARCHICAL = "hierarchical"  # 层级协作 - 上下级关系
    PEER = "peer"  # 平等协作 - 平等协商
    CONSENSUS = "consensus"  # 共识协作 - 达成一致
    COMPETITIVE = "competitive"  # 竞争协作 - 最优者胜


class TaskType(Enum):
    """任务类型"""

    SIMPLE = "simple"  # 简单任务 - 单智能体
    COLLABORATIVE = "collaborative"  # 协作任务 - 多智能体
    COMPLEX = "complex"  # 复杂任务 - 需要分解
    CRITICAL = "critical"  # 关键任务 - 高可靠性要求


class ConflictType(Enum):
    """冲突类型"""

    RESOURCE = "resource"  # 资源冲突
    OPINION = "opinion"  # 意见冲突
    PRIORITY = "priority"  # 优先级冲突
    GOAL = "goal"  # 目标冲突
    STRATEGY = "strategy"  # 策略冲突


@dataclass
class AgentRole:
    """智能体角色"""

    agent_id: str
    role_name: str  # leader, contributor, reviewer, executor
    responsibilities: list[str]
    authority_level: int = 5  # 1-10, 10最高
    voting_weight: float = 1.0


@dataclass
class CollaborationTeam:
    """协作团队"""

    team_id: str
    task_id: str
    mode: CollaborationMode
    leader: str | None = None
    members: list[AgentRole] = field(default_factory=list)
    formed_at: datetime = field(default_factory=datetime.now)
    status: str = "forming"


@dataclass
class SubTask:
    """子任务"""

    subtask_id: str
    parent_task_id: str
    description: str
    assigned_to: str | None = None
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    priority: int = 5
    estimated_duration: float = 60.0  # 秒
    result: Any | None = None


@dataclass
class Conflict:
    """冲突"""

    conflict_id: str
    conflict_type: ConflictType
    involved_agents: list[str]
    description: str
    detected_at: datetime = field(default_factory=datetime.now)
    severity: str = "medium"  # low, medium, high, critical
    resolution_strategy: str | None = None
    resolved: bool = False


@dataclass
class ConsensusResult:
    """共识结果"""

    decision: str
    agreement_level: float  # 0-1, 1表示完全一致
    voting_record: dict[str, str] = field(default_factory=dict)
    dissenting_opinions: list[str] = field(default_factory=list)
    reasoning: str = ""


class AgentCoordinator:
    """
    智能体协调器

    核心功能:
    1. 动态组建协作团队
    2. 智能任务分解
    3. 协作协议执行
    4. 冲突检测和解决
    5. 集体决策
    6. 知识共享协调
    """

    def __init__(self):
        # 活跃团队
        self.active_teams: dict[str, CollaborationTeam] = {}

        # 任务分解历史
        self.decomposition_history: deque[dict] = deque(maxlen=1000)

        # 冲突记录
        self.active_conflicts: dict[str, Conflict] = {}
        self.resolved_conflicts: deque[Conflict] = deque(maxlen=500)

        # 协作模式统计
        self.collaboration_stats: dict[CollaborationMode, dict] = defaultdict(
            lambda: {
                "usage_count": 0,
                "success_count": 0,
                "avg_duration": 0.0,
                "avg_team_size": 0.0,
            }
        )

        # 协作协议
        self.protocols = {
            CollaborationMode.SEQUENTIAL: self._sequential_protocol,
            CollaborationMode.PARALLEL: self._parallel_protocol,
            CollaborationMode.HIERARCHICAL: self._hierarchical_protocol,
            CollaborationMode.PEER: self._peer_protocol,
            CollaborationMode.CONSENSUS: self._consensus_protocol,
            CollaborationMode.COMPETITIVE: self._competitive_protocol,
        }

        # 知识共享记录
        self.knowledge_sharing_events: deque[dict] = deque(maxlen=1000)

        logger.info("🤝 Athena智能体协调器初始化完成")

    async def form_team(
        self,
        task_id: str,
        required_agents: list[tuple[str, str]],  # (agent_id, role_name)
        mode: CollaborationMode,
        leader_id: str | None = None,
    ) -> CollaborationTeam:
        """组建协作团队"""
        team_id = f"team_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建智能体角色
        members = []
        for agent_id, role_name in required_agents:
            # 根据角色定义职责
            if role_name == "leader":
                responsibilities = ["决策", "协调", "监督"]
                authority_level = 10
                voting_weight = 1.5
            elif role_name == "contributor":
                responsibilities = ["执行", "建议", "协作"]
                authority_level = 5
                voting_weight = 1.0
            elif role_name == "reviewer":
                responsibilities = ["审核", "验证", "反馈"]
                authority_level = 7
                voting_weight = 1.2
            else:  # executor
                responsibilities = ["执行", "实现"]
                authority_level = 3
                voting_weight = 0.8

            members.append(
                AgentRole(
                    agent_id=agent_id,
                    role_name=role_name,
                    responsibilities=responsibilities,
                    authority_level=authority_level,
                    voting_weight=voting_weight,
                )
            )

        # 创建团队
        team = CollaborationTeam(
            team_id=team_id,
            task_id=task_id,
            mode=mode,
            leader=leader_id or (required_agents[0][0] if required_agents else None),
            members=members,
            status="active",
        )

        self.active_teams[team_id] = team

        # 更新统计
        self.collaboration_stats[mode]["usage_count"] += 1
        self.collaboration_stats[mode]["avg_team_size"] = (
            self.collaboration_stats[mode]["avg_team_size"] * 0.9 + len(members) * 0.1
        )

        logger.info(f"👥 团队已组建: {team_id} " f"({len(members)}成员, 模式: {mode.value})")

        return team

    async def decompose_task(
        self, task_description: str, available_agents: list[str]
    ) -> list[SubTask]:
        """分解复杂任务"""
        # 简单分解策略
        subtasks = []

        # 根据任务描述识别子任务
        # 这里使用启发式规则,实际应该使用AI分解
        keywords = {
            "分析": ["分析", "研究", "调查"],
            "设计": ["设计", "规划", "构思"],
            "实现": ["实现", "开发", "编码"],
            "测试": ["测试", "验证", "检查"],
            "文档": ["文档", "记录", "说明"],
        }

        for phase, phase_keywords in keywords.items():
            if any(kw in task_description for kw in phase_keywords):
                subtask = SubTask(
                    subtask_id=f"subtask_{len(subtasks) + 1}",
                    parent_task_id=task_description[:30],
                    description=f"{phase}阶段: {task_description[:50]}",
                    priority=5,
                    estimated_duration=60.0,
                )
                subtasks.append(subtask)

        # 如果没有识别出明确的子任务,创建默认分解
        if not subtasks:
            for i in range(3):  # 默认分为3个子任务
                subtask = SubTask(
                    subtask_id=f"subtask_{i + 1}",
                    parent_task_id=task_description[:30],
                    description=f"子任务 {i + 1}: {task_description[50:100]}...",
                    priority=5,
                    estimated_duration=60.0,
                )
                subtasks.append(subtask)

        # 记录分解历史
        self.decomposition_history.append(
            {
                "task": task_description,
                "subtask_count": len(subtasks),
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"🔪 任务分解完成: {len(subtasks)} 个子任务")

        return subtasks

    async def execute_collaboration(
        self, team: CollaborationTeam, subtasks: list[SubTask], context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行协作任务"""
        protocol = self.protocols[team.mode]

        logger.info(f"🎬 开始协作: {team.team_id} (模式: {team.mode.value})")

        start_time = datetime.now()

        try:
            result = await protocol(team, subtasks, context)

            duration = (datetime.now() - start_time).total_seconds()

            # 更新统计
            self.collaboration_stats[team.mode]["success_count"] += 1
            self.collaboration_stats[team.mode]["avg_duration"] = (
                self.collaboration_stats[team.mode]["avg_duration"] * 0.9 + duration * 0.1
            )

            logger.info(f"✅ 协作完成: {team.team_id} (耗时: {duration:.1f}秒)")

            return {
                "success": True,
                "result": result,
                "duration": duration,
                "team_id": team.team_id,
            }

        except Exception as e:
            logger.error(f"❌ 协作失败: {team.team_id} - {e}")
            return {"success": False, "error": str(e), "team_id": team.team_id}

    async def _sequential_protocol(
        self, team: CollaborationTeam, subtasks: list[SubTask], context: dict[str, Any]
    ) -> dict[str, Any]:
        """顺序协作协议"""
        results = {}

        for i, subtask in enumerate(subtasks):
            # 分配给团队成员(轮询)
            member = team.members[i % len(team.members)]
            subtask.assigned_to = member.agent_id

            logger.info(f"  📋 执行子任务 {i + 1}/{len(subtasks)}: {subtask.description[:30]}...")

            # 模拟执行(实际应该调用智能体)
            await asyncio.sleep(0.1)

            # 假设执行成功
            subtask.status = "completed"
            subtask.result = f"完成: {subtask.description}"
            results[subtask.subtask_id] = subtask.result

        return {"subtask_results": results}

    async def _parallel_protocol(
        self, team: CollaborationTeam, subtasks: list[SubTask], context: dict[str, Any]
    ) -> dict[str, Any]:
        """并行协作协议"""
        results = {}

        # 为每个子任务分配成员
        for i, subtask in enumerate(subtasks):
            member = team.members[i % len(team.members)]
            subtask.assigned_to = member.agent_id

        # 并行执行
        async def execute_subtask(subtask: SubTask):
            logger.info(f"  📋 并行执行: {subtask.description[:30]}...")
            await asyncio.sleep(0.1)
            subtask.status = "completed"
            return subtask.subtask_id, f"完成: {subtask.description}"

        # 创建并行任务
        tasks = [execute_subtask(st) for st in subtasks]
        parallel_results = await asyncio.gather(*tasks)

        # 收集结果
        for subtask_id, result in parallel_results:
            results[subtask_id] = result

        return {"subtask_results": results}

    async def _hierarchical_protocol(
        self, team: CollaborationTeam, subtasks: list[SubTask], context: dict[str, Any]
    ) -> dict[str, Any]:
        """层级协作协议"""
        results = {}

        # 找到领导者
        leader = next((m for m in team.members if m.role_name == "leader"), None)
        if not leader:
            leader = team.members[0]

        # 领导者分配任务
        for subtask in subtasks:
            # 找最合适的成员
            suitable_member = None
            for member in team.members:
                if member.agent_id != leader.agent_id:
                    suitable_member = member
                    break

            if suitable_member:
                subtask.assigned_to = suitable_member.agent_id

        # 执行并收集结果
        for subtask in subtasks:
            logger.info(f"  📋 [层级] {subtask.description[:30]}...")
            await asyncio.sleep(0.1)
            subtask.status = "completed"
            results[subtask.subtask_id] = f"完成: {subtask.description}"

        return {"subtask_results": results}

    async def _peer_protocol(
        self, team: CollaborationTeam, subtasks: list[SubTask], context: dict[str, Any]
    ) -> dict[str, Any]:
        """平等协作协议"""
        results = {}

        # 所有成员平等协商
        for subtask in subtasks:
            # 投票选择执行者
            votes = {}
            for member in team.members:
                # 简化:轮询
                votes[member.agent_id] = member.voting_weight

            # 选择得票最高的
            selected = max(votes.items(), key=lambda x: x[1])[0]
            subtask.assigned_to = selected

            # 执行
            logger.info(f"  📋 [平等] {subtask.description[:30]}...")
            await asyncio.sleep(0.1)
            subtask.status = "completed"
            results[subtask.subtask_id] = f"完成: {subtask.description}"

        return {"subtask_results": results}

    async def _consensus_protocol(
        self, team: CollaborationTeam, subtasks: list[SubTask], context: dict[str, Any]
    ) -> dict[str, Any]:
        """共识协作协议"""
        results = {}

        for subtask in subtasks:
            # 收集所有成员的意见
            opinions = {}
            for member in team.members:
                # 模拟成员意见
                opinions[member.agent_id] = f"方案_{member.agent_id}"

            # 计算共识
            if len(set(opinions.values())) == 1:
                # 完全一致
                agreement_level = 1.0
                selected_opinion = next(iter(opinions.values()))
                dissenting_opinions = []
            else:
                # 需要协商
                agreement_level = 0.6
                selected_opinion = max(
                    set(opinions.values()), key=lambda x: list(opinions.values()).count(x)
                )
                dissenting_opinions = [
                    op for agent, op in opinions.items() if op != selected_opinion
                ]

            logger.info(
                f"  📋 [共识] {subtask.description[:30]}... (一致度: {agreement_level:.2f})"
            )

            await asyncio.sleep(0.1)
            subtask.status = "completed"
            results[subtask.subtask_id] = ConsensusResult(
                decision=selected_opinion,
                agreement_level=agreement_level,
                voting_record=opinions,
                dissenting_opinions=dissenting_opinions,
            )

        return {"subtask_results": results}

    async def _competitive_protocol(
        self, team: CollaborationTeam, subtasks: list[SubTask], context: dict[str, Any]
    ) -> dict[str, Any]:
        """竞争协作协议"""
        results = {}

        for subtask in subtasks:
            # 所有成员竞争执行
            best_score = -1
            best_agent = None
            best_proposal = None

            for member in team.members:
                # 模拟各成员的提案
                score = np.random.random()  # 实际应该基于提案质量
                proposal = f"{member.agent_id}的提案"

                if score > best_score:
                    best_score = score
                    best_agent = member.agent_id
                    best_proposal = proposal

            # 选择最佳方案
            subtask.assigned_to = best_agent

            logger.info(f"  📋 [竞争] {subtask.description[:30]}... (胜者: {best_agent})")

            await asyncio.sleep(0.1)
            subtask.status = "completed"
            results[subtask.subtask_id] = {
                "winner": best_agent,
                "proposal": best_proposal,
                "score": best_score,
            }

        return {"subtask_results": results}

    async def detect_conflict(
        self, agent1_id: str, agent2_id: str, conflict_type: ConflictType, description: str
    ) -> Conflict:
        """检测冲突"""
        conflict_id = f"conflict_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        conflict = Conflict(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            involved_agents=[agent1_id, agent2_id],
            description=description,
            severity="medium",
        )

        self.active_conflicts[conflict_id] = conflict

        logger.warning(f"⚠️ 检测到冲突: {conflict_type.value} - {description[:50]}...")

        return conflict

    async def resolve_conflict(self, conflict: Conflict, strategy: str = "negotiation") -> bool:
        """解决冲突"""
        logger.info(f"🔧 解决冲突: {conflict.conflict_id} (策略: {strategy})")

        # 根据冲突类型选择解决策略
        if conflict.conflict_type == ConflictType.RESOURCE:
            resolution = await self._resolve_resource_conflict(conflict)
        elif conflict.conflict_type == ConflictType.OPINION:
            resolution = await self._resolve_opinion_conflict(conflict)
        elif conflict.conflict_type == ConflictType.PRIORITY:
            resolution = await self._resolve_priority_conflict(conflict)
        else:
            resolution = await self._resolve_generic_conflict(conflict, strategy)

        conflict.resolved = resolution
        conflict.resolution_strategy = strategy

        # 从活跃冲突移到已解决
        if conflict.conflict_id in self.active_conflicts:
            del self.active_conflicts[conflict.conflict_id]
        self.resolved_conflicts.append(conflict)

        logger.info(f"✅ 冲突已解决: {conflict.conflict_id}")

        return resolution

    async def _resolve_resource_conflict(self, conflict: Conflict) -> bool:
        """解决资源冲突"""
        # 简单策略:时间片轮转
        return True

    async def _resolve_opinion_conflict(self, conflict: Conflict) -> bool:
        """解决意见冲突"""
        # 投票或协商
        return True

    async def _resolve_priority_conflict(self, conflict: Conflict) -> bool:
        """解决优先级冲突"""
        # 基于任务紧急度
        return True

    async def _resolve_generic_conflict(self, conflict: Conflict, strategy: str) -> bool:
        """通用冲突解决"""
        if strategy == "negotiation":
            # 协商解决
            return True
        elif strategy == "arbitration":
            # 仲裁
            return True
        else:
            # 默认解决
            return True

    async def share_knowledge(
        self, from_agent: str, to_agents: list[str], knowledge: dict[str, Any]
    ):
        """知识共享"""
        event = {
            "from_agent": from_agent,
            "to_agents": to_agents,
            "knowledge_type": knowledge.get("type", "general"),
            "timestamp": datetime.now().isoformat(),
        }

        self.knowledge_sharing_events.append(event)

        logger.info(
            f"📚 知识共享: {from_agent} -> {', '.join(to_agents)} " f"({event['knowledge_type']})"
        )

    async def get_coordination_report(self) -> dict[str, Any]:
        """获取协调报告"""
        return {
            "active_teams": len(self.active_teams),
            "active_conflicts": len(self.active_conflicts),
            "resolved_conflicts": len(self.resolved_conflicts),
            "collaboration_modes": {
                mode.value: {
                    "usage": stats["usage_count"],
                    "success_rate": (stats["success_count"] / max(stats["usage_count"], 1)),
                    "avg_duration": stats["avg_duration"],
                    "avg_team_size": stats["avg_team_size"],
                }
                for mode, stats in self.collaboration_stats.items()
            },
            "knowledge_sharing_events": len(self.knowledge_sharing_events),
            "recent_teams": [
                {
                    "team_id": team.team_id,
                    "mode": team.mode.value,
                    "members": len(team.members),
                    "status": team.status,
                }
                for team in list(self.active_teams.values())[-5:]
            ],
        }


# 导出便捷函数
_agent_coordinator: AgentCoordinator | None = None


def get_agent_coordinator() -> AgentCoordinator:
    """获取智能体协调器单例"""
    global _agent_coordinator
    if _agent_coordinator is None:
        _agent_coordinator = AgentCoordinator()
    return _agent_coordinator
