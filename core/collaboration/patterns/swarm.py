"""
Swarm协作模式核心实现

实现Swarm模式的主要协作逻辑。
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .swarm_state import SwarmState, AgentRole, SwarmDecisionType


logger = logging.getLogger(__name__)


class SwarmCollaborationPattern:
    """
    Swarm协作模式核心类

    实现群体智能协作功能，包括：
    - 会话管理
    - 提案处理
    - 投票机制
    - 分布式决策
    - 状态同步
    """

    def __init__(self, swarm_id: str, framework=None):
        """初始化Swarm"""
        self.swarm_id = swarm_id
        self._state = SwarmState(swarm_id)
        self._running = False
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # 活跃会话（公开属性）
        self.swarm_agents: Dict[str, Any] = {}  # Swarm agents（公开属性）
        self._session_counter = 0
        self.framework = framework  # 协作框架（用于消息传递）

        logger.info(f"Swarm {swarm_id} initialized")

    async def start(self) -> None:
        """启动Swarm"""
        if self._running:
            logger.warning(f"Swarm {self.swarm_id} is already running")
            return

        self._running = True
        logger.info(f"Swarm {self.swarm_id} started")

    async def stop(self) -> None:
        """停止Swarm"""
        if not self._running:
            logger.warning(f"Swarm {self.swarm_id} is not running")
            return

        self._running = False
        # 清理所有活跃会话
        self.active_sessions.clear()
        logger.info(f"Swarm {self.swarm_id} stopped")

    async def add_agent(self, agent_id: str, capabilities: List[str] = None) -> bool:
        """添加Agent到Swarm"""
        await self._state.add_agent(agent_id, capabilities)
        return True

    async def remove_agent(self, agent_id: str) -> bool:
        """从Swarm移除Agent"""
        await self._state.remove_agent(agent_id)
        return True

    async def get_state(self) -> SwarmState:
        """获取Swarm状态"""
        return self._state

    async def get_statistics(self) -> Dict[str, Any]:
        """获取Swarm统计信息"""
        metrics = await self._state.get_metrics()
        return metrics.to_dict()

    # ========================================================================
    # 会话管理
    # ========================================================================

    async def initiate_collaboration(
        self,
        task: Any,
        participants: List[Any],
        context: Dict[str, Any] = None
    ) -> str:
        """
        发起协作会话

        Args:
            task: 协作任务
            participants: 参与者列表
            context: 上下文信息

        Returns:
            会话ID
        """
        self._session_counter += 1
        session_id = f"session_{self._session_counter}"

        # 提取task_id
        task_id = task.id if hasattr(task, 'id') else str(task)

        # 创建会话（符合测试期望的结构）
        session = {
            "session_id": session_id,
            "task_id": task_id,
            "task": task,  # 保存完整task对象
            "participants": participants,  # 保存完整的participants对象列表
            "context": context or {},
            "proposals": {},  # 提案ID -> 提案详情
            "votes": {},  # 提案ID -> 投票记录
            "decisions": [],  # 已做出的决策
            "status": "active",
            "mode": context.get("mode", "exploration") if context else "exploration",
            "created_at": datetime.now().isoformat(),
        }

        self.active_sessions[session_id] = session

        # 将参与者添加到Swarm agents
        for participant in participants:
            # 提取agent_id
            if hasattr(participant, 'agent_id'):
                agent_id = participant.agent_id
                capabilities = participant.capabilities if hasattr(participant, 'capabilities') else []
                agent_obj = participant
            else:
                # 如果是字符串，创建一个简单的agent对象
                agent_id = str(participant)
                capabilities = []
                from .swarm_agent import SwarmAgent
                agent_obj = SwarmAgent(agent_id=agent_id, capabilities=[])
                self.swarm_agents[agent_id] = agent_obj

            # 添加到SwarmState
            await self.add_agent(agent_id, capabilities)

            # 保存agent引用到swarm_agents（如果还没有）
            if agent_id not in self.swarm_agents:
                self.swarm_agents[agent_id] = agent_obj

        logger.info(f"Collaboration session {session_id} initiated with {len(participants)} participants")
        return session_id

    async def add_member(self, session_id: str, agent_id: str) -> bool:
        """向会话添加成员"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return False

        session = self.active_sessions[session_id]
        participants = session["participants"]

        # 检查是否已存在（支持字符串和对象）
        for p in participants:
            p_id = p.agent_id if hasattr(p, 'agent_id') else str(p)
            if p_id == agent_id:
                logger.warning(f"Agent {agent_id} already in session")
                return False

        # 创建或获取agent对象
        if agent_id not in self.swarm_agents:
            from .swarm_agent import SwarmAgent
            agent = SwarmAgent(agent_id=agent_id, capabilities=[])
            self.swarm_agents[agent_id] = agent
            await self.add_agent(agent_id, [])

        # 添加到participants列表（添加agent对象）
        session["participants"].append(self.swarm_agents[agent_id])

        logger.info(f"Agent {agent_id} added to session {session_id}")
        return True

    async def remove_member(self, session_id: str, agent_id: str) -> bool:
        """从会话移除成员"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return False

        session = self.active_sessions[session_id]
        participants = session["participants"]

        # 查找并移除
        for i, p in enumerate(participants):
            p_id = p.agent_id if hasattr(p, 'agent_id') else str(p)
            if p_id == agent_id:
                removed = participants.pop(i)
                # 从swarm_agents中移除
                if agent_id in self.swarm_agents:
                    del self.swarm_agents[agent_id]
                logger.info(f"Agent {agent_id} removed from session {session_id}")
                return True

        logger.warning(f"Agent {agent_id} not found in session {session_id}")
        return False

    async def coordinate_execution(self, session_id: str) -> bool:
        """协调执行"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return False

        session = self.active_sessions[session_id]
        session["status"] = "coordinating"
        logger.info(f"Coordinating execution for session {session_id}")
        return True

    async def broadcast_message(self, session_id: str, message: Any) -> bool:
        """
        广播消息到所有参与者

        Args:
            session_id: 会话ID
            message: 消息对象

        Returns:
            是否成功广播
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return False

        session = self.active_sessions[session_id]

        # 如果有framework，通过message_broker发布消息
        if self.framework and hasattr(self.framework, 'message_broker'):
            try:
                await self.framework.message_broker.publish(message)
                logger.info(f"Message published via message_broker for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to publish message: {e}")
                return False

        logger.info(f"Broadcasting message to {len(session['participants'])} participants")
        return True

    # ========================================================================
    # 提案处理
    # ========================================================================

    async def handle_proposal(
        self,
        session_id: str,
        proposal: Dict[str, Any]
    ) -> bool:
        """
        处理提案

        Args:
            session_id: 会话ID
            proposal: 提案内容

        Returns:
            是否成功处理
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return False

        session = self.active_sessions[session_id]
        proposal_id = proposal.get("proposal_id")

        if not proposal_id:
            logger.warning("Proposal missing proposal_id")
            return False

        # 存储提案
        session["proposals"][proposal_id] = {
            "proposal_id": proposal_id,
            "proposer": proposal.get("proposer"),
            "content": proposal.get("content"),
            "type": proposal.get("type", "general"),
            "status": "pending",  # pending, approved, rejected
            "created_at": datetime.now().isoformat(),
            "votes": {},  # 投票记录存储在提案对象中
        }

        logger.info(f"Proposal {proposal_id} added to session {session_id}")
        return True

    async def handle_vote(
        self,
        session_id: str,
        vote: Dict[str, Any]
    ) -> bool:
        """
        处理投票

        Args:
            session_id: 会话ID
            vote: 投票内容

        Returns:
            是否成功处理
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return False

        session = self.active_sessions[session_id]
        proposal_id = vote.get("proposal_id")
        voter = vote.get("voter")
        decision = vote.get("decision")  # approve, reject

        if not proposal_id or not voter or not decision:
            logger.warning("Vote missing required fields")
            return False

        if proposal_id not in session["proposals"]:
            logger.warning(f"Proposal {proposal_id} not found")
            return False

        # 记录投票到提案对象中
        proposal = session["proposals"][proposal_id]
        proposal["votes"][voter] = {
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Vote from {voter} recorded for proposal {proposal_id}: {decision}")

        # 检查是否达成共识并更新提案状态
        # 根据决策类型确定阈值
        decision_type = session.get("context", {}).get("decision_type", SwarmDecisionType.CONSENSUS)
        threshold = 0.5 if decision_type == SwarmDecisionType.MAJORITY else 0.7

        if await self.check_consensus(session_id, proposal_id, threshold):
            proposal["status"] = "approved"
            logger.info(f"Proposal {proposal_id} approved by consensus")
        elif len(proposal["votes"]) >= len(session["participants"]):
            # 所有成员都已投票但未达成共识
            proposal["status"] = "rejected"
            logger.info(f"Proposal {proposal_id} rejected (no consensus)")

        return True

    # ========================================================================
    # 分布式决策
    # ========================================================================

    async def check_consensus(
        self,
        session_id: str,
        proposal_id: str,
        threshold: float = 0.7
    ) -> bool:
        """
        检查是否达到共识

        Args:
            session_id: 会话ID
            proposal_id: 提案ID
            threshold: 共识阈值（0-1）

        Returns:
            是否达成共识
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        if proposal_id not in session["proposals"]:
            return False

        proposal = session["proposals"][proposal_id]
        votes = proposal.get("votes", {})
        if not votes:
            return False

        # 计算支持率（支持多种决策格式）
        approve_count = sum(
            1 for v in votes.values()
            if v["decision"] in ("approve", "agree", "yes")
        )
        approval_rate = approve_count / len(votes)

        return approval_rate >= threshold

    # ========================================================================
    # 自组织
    # ========================================================================

    async def _self_organize(self, session_id: str) -> Dict[str, Any]:
        """
        自组织 - 自动分配角色

        Args:
            session_id: 会话ID

        Returns:
            角色分配结果
        """
        if session_id not in self.active_sessions:
            return {"status": "error", "message": "Session not found"}

        session = self.active_sessions[session_id]
        participants = session["participants"]

        # 简单的角色分配策略
        role_assignment = {}
        for i, participant in enumerate(participants):
            # 提取agent_id（支持SwarmAgent对象和字符串）
            if hasattr(participant, 'agent_id'):
                agent_id = participant.agent_id
            else:
                agent_id = str(participant)

            if i == 0:
                role = AgentRole.COORDINATOR
            elif i < len(participants) / 2:
                role = AgentRole.WORKER
            else:
                role = AgentRole.SPECIALIST

            role_assignment[agent_id] = role
            await self._state.assign_role(agent_id, role)

            # 更新SwarmAgent对象的角色（如果存在）
            if agent_id in self.swarm_agents:
                agent = self.swarm_agents[agent_id]
                if hasattr(agent, '_state'):
                    agent._state.role = role

        logger.info(f"Self-organization completed for session {session_id}")
        return {
            "status": "success",
            "roles": role_assignment,
        }

    # ========================================================================
    # 紧急模式
    # ========================================================================

    async def initiate_emergency_mode(
        self,
        session_id: str,
        emergency_type: str = "task_failure"
    ) -> bool:
        """
        启动紧急模式

        Args:
            session_id: 会话ID
            emergency_type: 紧急类型

        Returns:
            是否成功启动
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        session["emergency_mode"] = {
            "active": True,
            "type": emergency_type,
            "initiated_at": datetime.now().isoformat(),
        }

        # 创建应急小组
        session["emergency_team"] = list(session["participants"])[:3]  # 选择前3个参与者

        logger.warning(f"Emergency mode initiated for session {session_id}: {emergency_type}")
        return True

    async def handle_emergency(self, session_id: str, action: Dict[str, Any]) -> bool:
        """
        处理紧急情况

        Args:
            session_id: 会话ID
            action: 处理动作

        Returns:
            是否成功处理
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        if not session.get("emergency_mode", {}).get("active", False):
            logger.warning(f"Session {session_id} not in emergency mode")
            return False

        # 记录处理动作
        if "emergency_actions" not in session:
            session["emergency_actions"] = []

        session["emergency_actions"].append({
            "action": action.get("action"),
            "timestamp": datetime.now().isoformat(),
        })

        logger.info(f"Emergency handled for session {session_id}: {action}")
        return True

    async def exit_emergency_mode(self, session_id: str) -> bool:
        """
        退出紧急模式

        Args:
            session_id: 会话ID

        Returns:
            是否成功退出
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        if not session.get("emergency_mode", {}).get("active", False):
            logger.warning(f"Session {session_id} not in emergency mode")
            return False

        session["emergency_mode"]["active"] = False
        logger.info(f"Emergency mode exited for session {session_id}")
        return True
