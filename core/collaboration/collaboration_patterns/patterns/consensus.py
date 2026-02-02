#!/usr/bin/env python3
"""
共识协作模式
Consensus Collaboration Pattern

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0

基于投票和共识的协作决策模式。
"""

import logging
import uuid
from collections import defaultdict
from typing import Any

from ..base import CollaborationPattern
from ...collaboration_manager import Conflict
from ...multi_agent_collaboration import (
    Message,
    MessageType,
    MultiAgentCollaborationFramework,
    Task,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class ConsensusCollaborationPattern(CollaborationPattern):
    """
    共识协作模式

    基于投票和共识的协作决策模式。
    参与者通过多轮讨论和投票达成共识，支持提案、投票、决策的完整流程。
    """

    def __init__(self, framework: MultiAgentCollaborationFramework):
        """初始化共识协作模式"""
        super().__init__(framework)
        self.pattern_name = "共识协作"
        self.description = "基于投票和共识的协作决策"

    async def initiate_collaboration(
        self, task: Task, participants: list[str], context: dict[str, Any]
    ) -> str | None:
        """启动共识协作"""
        try:
            session_id = str(uuid.uuid4())

            # 创建共识执行计划
            execution_plan = {
                "session_id": session_id,
                "task_id": task.id,
                "participants": participants,
                "consensus_threshold": 0.7,  # 70%同意即达成共识
                "current_proposal": None,
                "votes": {},
                "discussion_rounds": 0,
                "max_rounds": 5,
                "shared_context": context.copy(),
                "consensus_reached": False,
                "final_decision": None,
            }

            self.active_sessions[session_id] = execution_plan

            # 启动第一轮讨论
            await self._start_discussion_round(session_id)

            logger.info(f"共识协作会话 {session_id} 已启动")
            return session_id

        except Exception as e:
            logger.error(f"启动共识协作失败: {e}")
            return None

    async def _start_discussion_round(self, session_id: str):
        """启动讨论轮次"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            discussion_message = Message(
                sender_id="consensus_collaboration",
                receiver_id="",
                message_type=MessageType.COORDINATION,
                content={
                    "action": "start_discussion",
                    "session_id": session_id,
                    "round": session["discussion_rounds"] + 1,
                    "context": session["shared_context"],
                    "current_proposal": session["current_proposal"],
                },
            )

            self.framework.message_broker.publish(discussion_message)

        except Exception as e:
            logger.error(f"启动讨论轮次失败: {e}")

    async def coordinate_execution(self, session_id: str) -> bool:
        """协调共识执行"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False

            if session["consensus_reached"]:
                # 共识已达成,执行最终决策
                await self._execute_consensus_decision(session_id)
                return True

            # 检查是否需要进入下一轮讨论
            if len(session["votes"]) >= len(session["participants"]):
                await self._tally_votes_and_decide(session_id)

            return True

        except Exception as e:
            logger.error(f"协调共识执行失败: {e}")
            return False

    async def handle_proposal(self, session_id: str, agent_id: str, proposal: dict[str, Any]):
        """处理提案"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 广播提案给所有参与者
            proposal_broadcast = Message(
                sender_id="consensus_collaboration",
                receiver_id="",
                message_type=MessageType.COORDINATION,
                content={
                    "action": "proposal_received",
                    "session_id": session_id,
                    "proposer": agent_id,
                    "proposal": proposal,
                },
            )

            self.framework.message_broker.publish(proposal_broadcast)

        except Exception as e:
            logger.error(f"处理提案失败: {e}")

    async def handle_vote(self, session_id: str, agent_id: str, vote: dict[str, Any]):
        """处理投票"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 记录投票
            session["votes"][agent_id] = vote

            logger.info(
                f"智能体 {agent_id} 在会话 {session_id} 中投票: {vote.get('decision', 'unknown')}"
            )

        except Exception as e:
            logger.error(f"处理投票失败: {e}")

    async def _tally_votes_and_decide(self, session_id: str):
        """统计投票并决定下一步"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            votes = session["votes"]
            total_votes = len(votes)
            agree_votes = sum(1 for vote in votes.values() if vote.get("decision") == "agree")
            consensus_ratio = agree_votes / total_votes if total_votes > 0 else 0

            if consensus_ratio >= session["consensus_threshold"]:
                # 达成共识
                session["consensus_reached"] = True
                session["final_decision"] = self._aggregate_votes_to_decision(votes)
                await self._announce_consensus(session_id)
            else:
                # 未达成共识,进入下一轮讨论
                session["discussion_rounds"] += 1
                session["votes"] = {}  # 重置投票

                if session["discussion_rounds"] < session["max_rounds"]:
                    await self._start_discussion_round(session_id)
                else:
                    # 达到最大轮次仍未达成共识,使用多数决
                    await self._fallback_to_majority_vote(session_id)

        except Exception as e:
            logger.error(f"统计投票失败: {e}")

    def _aggregate_votes_to_decision(self, votes: dict[str, Any]) -> dict[str, Any]:
        """聚合投票为最终决策"""
        # 简化的决策聚合逻辑
        agree_votes = [vote for vote in votes.values() if vote.get("decision") == "agree"]

        if agree_votes:
            # 选择得票最多的提案作为最终决策
            proposal_votes = defaultdict(int)
            for vote in agree_votes:
                proposal_key = str(vote.get("proposal", "default"))
                proposal_votes[proposal_key] += 1

            best_proposal = max(proposal_votes.items(), key=lambda x: x[1])
            return {
                "decision": "consensus_reached",
                "proposal": best_proposal[0],
                "support_count": best_proposal[1],
                "total_participants": len(votes),
            }

        return {"decision": "no_consensus", "reason": "no_agreement_reached"}

    async def _announce_consensus(self, session_id: str):
        """宣布共识达成"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            announcement_message = Message(
                sender_id="consensus_collaboration",
                receiver_id="",
                message_type=MessageType.COORDINATION,
                content={
                    "action": "consensus_announced",
                    "session_id": session_id,
                    "decision": session["final_decision"],
                    "rounds_taken": session["discussion_rounds"] + 1,
                },
            )

            self.framework.message_broker.publish(announcement_message)

        except Exception as e:
            logger.error(f"宣布共识失败: {e}")

    async def _execute_consensus_decision(self, session_id: str):
        """执行共识决策"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 更新任务状态
            task = self.framework.tasks.get(session["task_id"])
            if task:
                task.status = TaskStatus.COMPLETED
                task.result = {
                    "session_id": session_id,
                    "decision": session["final_decision"],
                    "consensus_process": {
                        "rounds": session["discussion_rounds"] + 1,
                        "participants": len(session["participants"]),
                        "votes_collected": len(session["votes"]),
                    },
                }
                task.update_progress(1.0)

            logger.info(f"共识决策已执行: {session['final_decision']}")

        except Exception as e:
            logger.error(f"执行共识决策失败: {e}")

    async def _fallback_to_majority_vote(self, session_id: str):
        """回退到多数决"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            votes = session["votes"]
            agree_votes = sum(1 for vote in votes.values() if vote.get("decision") == "agree")
            total_votes = len(votes)

            if agree_votes > total_votes / 2:
                # 多数同意
                session["consensus_reached"] = True
                session["final_decision"] = {
                    "decision": "majority_vote",
                    "method": "simple_majority",
                    "agree_votes": agree_votes,
                    "total_votes": total_votes,
                }
            else:
                # 多数反对
                session["final_decision"] = {
                    "decision": "rejected",
                    "method": "simple_majority",
                    "agree_votes": agree_votes,
                    "total_votes": total_votes,
                }

            await self._announce_consensus(session_id)

        except Exception as e:
            logger.error(f"多数决失败: {e}")

    async def handle_conflicts(self, session_id: str, conflicts: list[Conflict]) -> bool:
        """处理共识协作中的冲突"""
        # 共识协作中的冲突主要通过讨论和投票解决
        for conflict in conflicts:
            if conflict.conflict_type == "disagreement":
                # 启动额外讨论轮次
                await self._start_extra_discussion(session_id, conflict)

        return True

    async def _start_extra_discussion(self, session_id: str, conflict: Conflict):
        """启动额外讨论"""
        # 实现额外讨论逻辑
        pass
