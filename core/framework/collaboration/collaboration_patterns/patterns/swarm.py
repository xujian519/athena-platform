#!/usr/bin/env python3

"""
Swarm协作模式实现
Swarm Collaboration Pattern Implementation

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

实现Swarm群体智能协作模式。
采用依赖倒置原则，通过接口与框架交互。
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Protocol, Optional

# 导入TaskStatus用于SwarmTask
from core.framework.collaboration.multi_agent_collaboration import TaskStatus

from .swarm_agent import SwarmAgent
from .swarm_communication import (
    SwarmCommunicationProtocol,
    SwarmGossipProtocol,
    SwarmKnowledgeSharing,
    SwarmMessage,
)
from .swarm_decision import SwarmDecisionEngine

# 重新导出所有Swarm相关的类，方便测试导入
from .swarm_models import (
    SwarmDecisionType,
    SwarmEmergencyType,
    SwarmKnowledgeItem,
    SwarmMessageType,
    SwarmRole,
)
from .swarm_state import SwarmSharedState


# 定义SwarmTask（在测试中使用）
class SwarmTask:
    """Swarm任务（简化版）"""

    def __init__(
        self,
        id: str,
        description: str,
        required_capabilities: list[str],
    ):
        self.id = id
        self.description = description
        self.required_capabilities = required_capabilities
        self.parent_id = None
        self.subtasks = []
        self.status = TaskStatus.PENDING
        self.assignees = []
        self.result = None
        self.error = None

    def add_subtask(self, subtask: SwarmTask) -> None:
        """添加子任务"""
        subtask.parent_id = self.id
        self.subtasks.append(subtask)

    def assign_to(self, agent_id: str) -> None:
        """分配给Agent"""
        if agent_id not in self.assignees:
            self.assignees.append(agent_id)
        self.status = TaskStatus.ASSIGNED

    def complete(self, result: Optional[dict] = None) -> None:
        """完成任务"""
        self.result = result
        self.status = TaskStatus.COMPLETED

    def fail(self, error: str) -> None:
        """标记失败"""
        self.error = error
        self.status = TaskStatus.FAILED

logger = logging.getLogger(__name__)


# ============================================================================
# 框架接口（依赖倒置）
# ============================================================================


class IMessageBroker(Protocol):
    """消息代理接口"""

    async def publish(self, message: Any) -> None:
        """发布消息"""
        ...

    async def subscribe(self, handler: Any, pattern: str) -> None:
        """订阅消息"""
        ...


class ICollaborationFramework(Protocol):
    """协作框架接口"""

    message_broker: IMessageBroker
    tasks: dict[str, Any]
    agents: dict[str, Any]


# ============================================================================
# Swarm协作模式主类
# ============================================================================


class SwarmCollaborationPattern:
    """
    Swarm协作模式

    实现群体智能协作，支持：
    - 自组织协调
    - 分布式决策
    - 状态同步（Gossip协议）
    - 知识共享
    - 紧急响应
    """

    def __init__(self, framework: ICollaborationFramework):
        """
        初始化Swarm协作模式

        Args:
            framework: 协作框架实例
        """
        self.framework = framework
        self.pattern_id = str(uuid.uuid4())
        self.pattern_name = "Swarm协作"

        # Swarm核心组件
        self.swarm_agents: dict[str, SwarmAgent] = {}
        self.shared_states: dict[str, SwarmSharedState] = {}
        self.active_sessions: dict[str, dict[str, Any] = {}

        # 通信和决策组件
        self.communication_protocols: dict[str, SwarmCommunicationProtocol] = {}
        self.gossip_protocols: dict[str, SwarmGossipProtocol] = {}
        self.knowledge_sharing: dict[str, SwarmKnowledgeSharing] = {}
        self.decision_engines: dict[str, SwarmDecisionEngine] = {}

        logger.info(f"初始化Swarm协作模式: {self.pattern_id}")

    # ========================================================================
    # 核心协作方法（实现CollaborationPattern接口）
    # ========================================================================

    async def initiate_collaboration(
        self,
        task: Any,
        participants: list[str],
        context: dict[str, Any],
    ) -> Optional[str]:
        """
        启动Swarm协作

        Args:
            task: 任务对象
            participants: 参与者ID列表
            context: 上下文信息

        Returns:
            会话ID或None
        """
        try:
            session_id = str(uuid.uuid4())

            # 创建共享状态
            shared_state = SwarmSharedState()
            self.shared_states[session_id] = shared_state

            # 创建决策引擎
            decision_type = context.get(
                "decision_type",
                SwarmDecisionType.MAJORITY,
            )
            decision_engine = SwarmDecisionEngine(
                default_decision_type=decision_type,
                default_consensus_threshold=context.get("consensus_threshold", 0.7),
            )
            self.decision_engines[session_id] = decision_engine

            # 创建通信协议
            comm_protocol = SwarmCommunicationProtocol(session_id)
            self.communication_protocols[session_id] = comm_protocol

            # 创建Gossip协议
            gossip = SwarmGossipProtocol(
                session_id,
                gossip_interval=context.get("gossip_interval", 10.0),
            )
            self.gossip_protocols[session_id] = gossip

            # 创建知识共享
            knowledge_sharing = SwarmKnowledgeSharing(session_id)
            self.knowledge_sharing[session_id] = knowledge_sharing

            # 初始化Swarm Agents
            for agent_id in participants:
                await self._add_agent_to_swarm(
                    session_id,
                    agent_id,
                    context.get("agent_capabilities", {}).get(agent_id, []),
                )

            # 创建会话
            self.active_sessions[session_id]] = {
                "session_id": session_id,
                "task_id": task.id if hasattr(task, "id") else task.get("id"),
                "participants": participants.copy(),
                "mode": context.get("mode", "standard"),
                "decision_type": decision_type,
                "status": "running",
                "created_at": datetime.now(),
                "emergency_mode": False,
                "emergency_type": None,
                "proposals": {},
                "sync_rounds": 0,
            }

            # 初始角色分配
            await self._assign_initial_roles(session_id)

            # 启动Gossip同步任务
            asyncio.create_task(self._gossip_sync_loop(session_id))

            logger.info(
                f"Swarm协作会话已启动: {session_id}, "
                f"参与者={len(participants)}, 模式={context.get('mode', 'standard')}"
            )

            return session_id

        except Exception as e:
            logger.error(f"启动Swarm协作失败: {e}", exc_info=True)
            return None

    async def coordinate_execution(self, session_id: str) -> bool:
        """
        协调执行

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        try:
            session = self.active_sessions.get(session_id)

            if not session:
                logger.warning(f"会话不存在: {session_id}")
                return False

            # 检查是否需要自组织
            await self._check_and_reorganize(session_id)

            # 处理待决策的提案
            await self._process_pending_proposals(session_id)

            # 检查紧急情况
            await self._check_emergency_conditions(session_id)

            return True

        except Exception as e:
            logger.error(f"协调执行失败: {e}", exc_info=True)
            return False

    async def handle_conflicts(
        self,
        session_id: str,
        conflicts: list[Any],
    ) -> bool:
        """
        处理冲突

        Args:
            session_id: 会话ID
            conflicts: 冲突列表

        Returns:
            是否成功解决
        """
        try:
            session = self.active_sessions.get(session_id)

            if not session:
                return False

            for conflict in conflicts:
                conflict_type = getattr(conflict, "conflict_type", "unknown")

                if conflict_type == "resource_contention":
                    await self._handle_resource_contention(session_id, conflict)
                elif conflict_type == "disagreement":
                    await self._handle_disagreement(session_id, conflict)
                else:
                    logger.warning(f"未知冲突类型: {conflict_type}")

            return True

        except Exception as e:
            logger.error(f"处理冲突失败: {e}", exc_info=True)
            return False

    # ========================================================================
    # 成员管理
    # ========================================================================

    async def add_member(self, session_id: str, agent_id: str) -> bool:
        """
        动态添加成员

        Args:
            session_id: 会话ID
            agent_id: Agent ID

        Returns:
            是否成功
        """
        try:
            session = self.active_sessions.get(session_id)

            if not session:
                return False

            if agent_id in session["participants"]:
                return False

            # 添加Agent
            await self._add_agent_to_swarm(session_id, agent_id, [])

            # 更新会话
            session["participants"].append(agent_id)
            session["sync_rounds"] += 1

            # 广播新成员加入
            comm = self.communication_protocols.get(session_id)
            if comm:
                message = await comm.broadcast(
                    sender_id="system",
                    message_type=SwarmMessageType.JOIN_SWARM,
                    content={"agent_id": agent_id},
                )
                await self._publish_message(session_id, message)

            logger.info(f"添加成员到Swarm: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"添加成员失败: {e}", exc_info=True)
            return False

    async def remove_member(self, session_id: str, agent_id: str) -> bool:
        """
        移除成员

        Args:
            session_id: 会话ID
            agent_id: Agent ID

        Returns:
            是否成功
        """
        try:
            session = self.active_sessions.get(session_id)

            if not session or agent_id not in session["participants"]:
                return False

            # 移除Agent
            if agent_id in self.swarm_agents:
                del self.swarm_agents[agent_id]

            # 更新共享状态
            shared_state = self.shared_states.get(session_id)
            if shared_state:
                shared_state.remove_member_state(agent_id)

            # 更新会话
            session["participants"].remove(agent_id)

            # 广播成员离开
            comm = self.communication_protocols.get(session_id)
            if comm:
                message = await comm.broadcast(
                    sender_id="system",
                    message_type=SwarmMessageType.LEAVE_SWARM,
                    content={"agent_id": agent_id},
                )
                await self._publish_message(session_id, message)

            logger.info(f"从Swarm移除成员: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"移除成员失败: {e}", exc_info=True)
            return False

    async def _add_agent_to_swarm(
        self,
        session_id: str,
        agent_id: str,
        capabilities: list[str],
    ) -> None:
        """
        添加Agent到Swarm

        Args:
            session_id: 会话ID
            agent_id: Agent ID
            capabilities: 能力列表
        """
        agent = SwarmAgent(
            agent_id=agent_id,
            capabilities=capabilities,
            initial_role=SwarmRole.WORKER,
        )
        self.swarm_agents[agent_id] = agent

        # 更新共享状态
        shared_state = self.shared_states.get(session_id)
        if shared_state:
            shared_state.update_member_state(agent_id, agent.get_state().to_dict())

    # ========================================================================
    # 自组织机制
    # ========================================================================

    async def _assign_initial_roles(self, session_id: str) -> None:
        """
        分配初始角色

        Args:
            session_id: 会话ID
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return

        participants = session["participants"]
        mode = session.get("mode", "standard")

        # 根据模式和参与者数量分配角色
        role_distribution = self._calculate_role_distribution(
            len(participants),
            mode,
        )

        for i, agent_id in enumerate(participants):
            agent = self.swarm_agents.get(agent_id)
            if agent:
                role = role_distribution[i]
                agent.change_role(role)

                # 更新共享状态
                shared_state = self.shared_states.get(session_id)
                if shared_state:
                    shared_state.update_member_state(agent_id, agent.get_state().to_dict())

        logger.debug(
            f"初始角色分配完成: session={session_id}, "
            f"分布={role_distribution}"
        )

    def _calculate_role_distribution(
        self,
        num_agents: int,
        mode: str,
    ) -> list[SwarmRole]:
        """
        计算角色分布

        Args:
            num_agents: Agent数量
            mode: 运行模式

        Returns:
            角色列表
        """
        roles = []

        if mode == "exploration":
            # 探索模式：更多探索者
            num_explorers = max(1, num_agents // 3)
            num_workers = max(1, num_agents // 2)
            num_analyzers = max(1, num_agents - num_explorers - num_workers)

            roles.extend([SwarmRole.EXPLORER] * num_explorers)
            roles.extend([SwarmRole.WORKER] * num_workers)
            roles.extend([SwarmRole.ANALYZER] * num_analyzers)

        elif mode == "analysis":
            # 分析模式：更多分析者
            num_analyzers = max(1, num_agents // 2)
            num_workers = max(1, num_agents - num_analyzers)

            roles.extend([SwarmRole.ANALYZER] * num_analyzers)
            roles.extend([SwarmRole.WORKER] * num_workers)

        else:
            # 标准模式：均匀分布
            roles.extend([SwarmRole.WORKER] * max(1, num_agents // 2))
            roles.extend([SwarmRole.ANALYZER] * max(1, num_agents // 4))

        # 填充剩余位置
        while len(roles) < num_agents:
            roles.append(SwarmRole.WORKER)

        return roles[:num_agents]

    async def _check_and_reorganize(self, session_id: str) -> None:
        """
        检查并重组

        Args:
            session_id: 会话ID
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return

        # 检查是否需要重组（简化版）
        # 实际实现可以基于性能指标、负载等
        reorganize_threshold = session.get("reorganize_threshold", 5)

        session["sync_rounds"] += 1

        if session["sync_rounds"] % reorganize_threshold == 0:
            await self._self_organize(session_id)

    async def _self_organize(self, session_id: str) -> None:
        """
        自组织

        Args:
            session_id: 会话ID
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return

        # 评估当前状态
        shared_state = self.shared_states.get(session_id)
        if not shared_state:
            return

        # 获取角色分布
        role_dist = shared_state.get_role_distribution()

        # 检查是否需要调整
        # （简化版，实际可以更复杂）
        total_members = sum(role_dist.values())

        if total_members == 0:
            return

        # 检查负载平衡
        overloaded_agents = []
        for agent_id, state in shared_state.member_states.items():
            if state.current_load > 0.8:
                overloaded_agents.append(agent_id)

        # 如果有过载Agent，考虑角色调整
        if overloaded_agents:
            logger.info(
                f"检测到过载Agent，触发重组: {overloaded_agents}"
            )
            # 这里可以添加角色调整逻辑

    # ========================================================================
    # 分布式决策
    # ========================================================================

    async def create_proposal(
        self,
        session_id: str,
        proposer: str,
        content: dict[str, Any],
        proposal_type: str,
    ) -> Optional[str]:
        """
        创建提案

        Args:
            session_id: 会话ID
            proposer: 提案者ID
            content: 提案内容
            proposal_type: 提案类型

        Returns:
            提案ID或None
        """
        try:
            decision_engine = self.decision_engines.get(session_id)

            if not decision_engine:
                return None

            proposal = await decision_engine.create_proposal(
                proposer=proposer,
                content=content,
                proposal_type=proposal_type,
            )

            # 添加到会话
            session = self.active_sessions.get(session_id)
            if session:
                session["proposals"][proposal.proposal_id] = proposal.to_dict()

            # 广播提案
            comm = self.communication_protocols.get(session_id)
            if comm:
                message = await comm.broadcast(
                    sender_id=proposer,
                    message_type=SwarmMessageType.PROPOSAL,
                    content={
                        "proposal_id": proposal.proposal_id,
                        "proposal": proposal.to_dict(),
                    },
                )
                await self._publish_message(session_id, message)

            logger.info(
                f"创建提案: {proposal.proposal_id}, 类型={proposal_type}"
            )

            return proposal.proposal_id

        except Exception as e:
            logger.error(f"创建提案失败: {e}", exc_info=True)
            return None

    async def handle_proposal(
        self,
        session_id: str,
        proposal: dict[str, Any],
    ) -> None:
        """
        处理提案

        Args:
            session_id: 会话ID
            proposal: 提案字典
        """
        # 在实际实现中，这里会处理提案
        pass

    async def handle_vote(
        self,
        session_id: str,
        vote: dict[str, Any],
    ) -> bool:
        """
        处理投票

        Args:
            session_id: 会话ID
            vote: 投票字典

        Returns:
            是否成功
        """
        try:
            decision_engine = self.decision_engines.get(session_id)

            if not decision_engine:
                return False

            proposal_id = vote.get("proposal_id")
            voter_id = vote.get("voter")
            decision = vote.get("decision")
            weight = vote.get("weight", 1.0)

            success = await decision_engine.cast_vote(
                proposal_id=proposal_id,
                voter_id=voter_id,
                vote=decision,
                weight=weight,
            )

            return success

        except Exception as e:
            logger.error(f"处理投票失败: {e}", exc_info=True)
            return False

    async def _process_pending_proposals(self, session_id: str) -> None:
        """
        处理待决策提案

        Args:
            session_id: 会话ID
        """
        decision_engine = self.decision_engines.get(session_id)
        shared_state = self.shared_states.get(session_id)

        if not decision_engine or not shared_state:
            return

        # 获取活跃提案
        active_proposals = decision_engine.get_active_proposals()

        for proposal_dict in active_proposals:
            proposal_id = proposal_dict["proposal_id"]

            # 尝试最终决策
            result = await decision_engine.finalize_decision(
                proposal_id,
                shared_state.member_states,
            )

            if result.get("result") in ("approved", "rejected"):
                # 决策完成，广播结果
                comm = self.communication_protocols.get(session_id)
                if comm:
                    message = await comm.broadcast(
                        sender_id="system",
                        message_type=SwarmMessageType.DECISION,
                        content={
                            "proposal_id": proposal_id,
                            "decision": result,
                        },
                    )
                    await self._publish_message(session_id, message)

                logger.info(
                    f"决策完成: {proposal_id}, 结果={result['result']}"
                )

    # ========================================================================
    # 状态同步（Gossip）
    # ========================================================================

    async def _gossip_sync_loop(self, session_id: str) -> None:
        """
        Gossip同步循环

        Args:
            session_id: 会话ID
        """
        gossip = self.gossip_protocols.get(session_id)

        if not gossip:
            return

        while session_id in self.active_sessions:
            try:
                await asyncio.sleep(gossip.gossip_interval)

                # 执行一轮Gossip
                await self._gossip_round(session_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Gossip同步错误: {e}", exc_info=True)

    async def _gossip_round(self, session_id: str) -> None:
        """
        一轮Gossip

        Args:
            session_id: 会话ID
        """
        session = self.active_sessions.get(session_id)
        gossip = self.gossip_protocols.get(session_id)
        shared_state = self.shared_states.get(session_id)

        if not session or not gossip or not shared_state:
            return

        # 选择Gossip伙伴
        partners = gossip.select_gossip_partners(session["participants"])

        # 交换状态
        for partner_id in partners:
            await self._exchange_state_with_member(session_id, partner_id)

        # 更新统计
        session["sync_rounds"] += 1
        shared_state.statistics.sync_rounds += 1

    async def _exchange_state_with_member(
        self,
        session_id: str,
        member_id: str,
    ) -> None:
        """
        与成员交换状态

        Args:
            session_id: 会话ID
            member_id: 成员ID
        """
        # 在实际实现中，这里会通过网络与成员交换状态
        # 简化版：仅记录日志
        logger.debug(f"与成员交换状态: {member_id}")

    # ========================================================================
    # 知识共享
    # ========================================================================

    async def share_knowledge(
        self,
        session_id: str,
        knowledge: SwarmKnowledgeItem,
    ) -> None:
        """
        共享知识

        Args:
            session_id: 会话ID
            knowledge: 知识项
        """
        knowledge_sharing = self.knowledge_sharing.get(session_id)
        shared_state = self.shared_states.get(session_id)

        if not knowledge_sharing or not shared_state:
            return

        # 添加到本地和共享状态
        knowledge_sharing.share_knowledge(knowledge)
        shared_state.add_knowledge(knowledge)

        # 广播知识
        comm = self.communication_protocols.get(session_id)
        if comm:
            message = await comm.broadcast(
                sender_id=knowledge.source,
                message_type=SwarmMessageType.KNOWLEDGE_SHARE,
                content={
                    "key": knowledge.key,
                    "value": knowledge.value,
                    "confidence": knowledge.confidence,
                },
            )
            await self._publish_message(session_id, message)

        logger.debug(f"共享知识: {knowledge.key}")

    # ========================================================================
    # 紧急响应
    # ========================================================================

    async def initiate_emergency_mode(
        self,
        session_id: str,
        emergency_type: SwarmEmergencyType,
    ) -> None:
        """
        启动紧急模式

        Args:
            session_id: 会话ID
            emergency_type: 紧急类型
        """
        session = self.active_sessions.get(session_id)
        shared_state = self.shared_states.get(session_id)

        if not session or not shared_state:
            return

        # 设置紧急状态
        session["emergency_mode"] = True
        session["emergency_type"] = emergency_type

        # 添加紧急标志
        shared_state.add_emergency_flag(emergency_type.value)

        # 组建应急小组
        emergency_team = await self._form_emergency_team(
            session_id,
            emergency_type,
        )
        session["emergency_team"] = emergency_team

        # 广播紧急情况
        comm = self.communication_protocols.get(session_id)
        if comm:
            message = await comm.broadcast(
                sender_id="system",
                message_type=SwarmMessageType.EMERGENCY,
                content={
                    "emergency_type": emergency_type.value,
                    "emergency_team": emergency_team,
                },
            )
            await self._publish_message(session_id, message)

        logger.warning(
            f"启动紧急模式: {session_id}, 类型={emergency_type.value}"
        )

    async def _form_emergency_team(
        self,
        session_id: str,
        emergency_type: SwarmEmergencyType,
    ) -> list[str]:
        """
        组建应急小组

        Args:
            session_id: 会话ID
            emergency_type: 紧急类型

        Returns:
            应急小组成员ID列表
        """
        session = self.active_sessions.get(session_id)
        shared_state = self.shared_states.get(session_id)

        if not session or not shared_state:
            return []

        # 选择最可用的成员
        available = shared_state.get_available_members()

        # 选择前5个（或全部）
        team_size = min(5, len(available))
        emergency_team = available[:team_size]

        logger.info(f"组建应急小组: {emergency_team}")

        return emergency_team

    async def handle_emergency(
        self,
        session_id: str,
        emergency_data: dict[str, Any],
    ) -> None:
        """
        处理紧急情况

        Args:
            session_id: 会话ID
            emergency_data: 紧急数据
        """
        session = self.active_sessions.get(session_id)

        if not session or not session.get("emergency_mode"):
            return

        action = emergency_data.get("action")

        if action == "resolve":
            await self.exit_emergency_mode(session_id)

    async def exit_emergency_mode(self, session_id: str) -> None:
        """
        退出紧急模式

        Args:
            session_id: 会话ID
        """
        session = self.active_sessions.get(session_id)
        shared_state = self.shared_states.get(session_id)

        if not session or not shared_state:
            return

        session["emergency_mode"] = False
        session["emergency_type"] = None
        session.pop("emergency_team", None)

        shared_state.clear_emergency_flags()

        logger.info(f"退出紧急模式: {session_id}")

    async def _check_emergency_conditions(self, session_id: str) -> None:
        """
        检查紧急情况

        Args:
            session_id: 会话ID
        """
        session = self.active_sessions.get(session_id)
        shared_state = self.shared_states.get(session_id)

        if not session or not shared_state:
            return

        # 检查各种紧急条件
        # （简化版，实际可以检测更多条件）

        # 检查是否有大量成员失败
        failed_ratio = 0
        if shared_state.statistics.total_members > 0:
            failed_ratio = (
                shared_state.statistics.total_members
                - shared_state.statistics.active_members
            ) / shared_state.statistics.total_members

        if failed_ratio > 0.5:  # 超过50%成员失败
            await self.initiate_emergency_mode(
                session_id,
                SwarmEmergencyType.FAILURE,
            )

    # ========================================================================
    # 消息处理
    # ========================================================================

    async def broadcast_message(
        self,
        session_id: str,
        message: SwarmMessage,
    ) -> None:
        """
        广播消息

        Args:
            session_id: 会话ID
            message: 消息对象
        """
        await self._publish_message(session_id, message)

    async def _publish_message(
        self,
        session_id: str,
        message: SwarmMessage,
    ) -> None:
        """
        发布消息到框架

        Args:
            session_id: 会话ID
            message: 消息对象
        """
        try:
            # 通过框架的消息代理发布
            if hasattr(self.framework, "message_broker"):
                await self.framework.message_broker.publish(message)
        except Exception as e:
            logger.error(f"发布消息失败: {e}", exc_info=True)

    # ========================================================================
    # 工具方法
    # ========================================================================

    def get_session_info(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典
        """
        session = self.active_sessions.get(session_id)

        if not session:
            return None

        shared_state = self.shared_states.get(session_id)
        decision_engine = self.decision_engines.get(session_id)

        return {
            **session,
            "shared_state": shared_state.to_dict() if shared_state else None,
            "decision_stats": (
                decision_engine.get_statistics() if decision_engine else None
            ),
        }

    def get_statistics(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        获取统计信息

        Args:
            session_id: 会话ID

        Returns:
            统计信息字典
        """
        shared_state = self.shared_states.get(session_id)
        decision_engine = self.decision_engines.get(session_id)
        comm_protocol = self.communication_protocols.get(session_id)
        gossip = self.gossip_protocols.get(session_id)
        knowledge = self.knowledge_sharing.get(session_id)

        return {
            "shared_state": (
                shared_state.statistics.to_dict() if shared_state else None
            ),
            "decision": (
                decision_engine.get_statistics() if decision_engine else None
            ),
            "communication": (
                comm_protocol.get_statistics() if comm_protocol else None
            ),
            "gossip": gossip.get_statistics() if gossip else None,
            "knowledge": knowledge.get_statistics() if knowledge else None,
        }

