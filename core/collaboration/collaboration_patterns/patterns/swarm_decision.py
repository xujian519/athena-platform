#!/usr/bin/env python3
from __future__ import annotations

"""
Swarm决策引擎实现
Swarm Decision Engine Implementation

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

实现Swarm群体的分布式决策机制。
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from .swarm_models import (
    AgentState,
    Proposal,
    SwarmDecisionType,
    SwarmMessageType,
)

logger = logging.getLogger(__name__)


class SwarmDecisionEngine:
    """
    Swarm决策引擎

    实现分布式决策机制，包括投票、共识和加权决策。
    """

    def __init__(
        self,
        default_decision_type: SwarmDecisionType = SwarmDecisionType.MAJORITY,
        default_consensus_threshold: float = 0.7,
        decision_timeout: float = 30.0,
    ):
        """
        初始化决策引擎

        Args:
            default_decision_type: 默认决策类型
            default_consensus_threshold: 默认共识阈值
            decision_timeout: 决策超时时间（秒）
        """
        self.default_decision_type = default_decision_type
        self.default_consensus_threshold = default_consensus_threshold
        self.decision_timeout = decision_timeout

        # 活跃的提案
        self.active_proposals: dict[str, Proposal] = {}

        # 决策历史
        self.decision_history: list[dict[str, Any]] = []

        logger.debug(
            f"创建Swarm决策引擎: 类型={default_decision_type.value}, "
            f"阈值={default_consensus_threshold}"
        )

    async def create_proposal(
        self,
        proposer: str,
        content: dict[str, Any],
        proposal_type: str,
        decision_type: SwarmDecisionType | None = None,
        consensus_threshold: float | None = None,
        expires_in: float | None = None,
    ) -> Proposal:
        """
        创建提案

        Args:
            proposer: 提案者ID
            content: 提案内容
            proposal_type: 提案类型
            decision_type: 决策类型（可选）
            consensus_threshold: 共识阈值（可选）
            expires_in: 过期时间（秒，可选）

        Returns:
            创建的提案
        """
        proposal_id = str(uuid.uuid4())

        proposal = Proposal(
            proposal_id=proposal_id,
            proposer=proposer,
            content=content,
            proposal_type=proposal_type,
            decision_type=decision_type or self.default_decision_type,
            consensus_threshold=consensus_threshold or self.default_consensus_threshold,
        )

        if expires_in:
            proposal.expires_at = datetime.now() + timedelta(seconds=expires_in)

        self.active_proposals[proposal_id] = proposal

        logger.info(
            f"创建提案: {proposal_id}, 类型={proposal_type}, "
            f"提案者={proposer}"
        )

        return proposal

    async def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        vote: str,
        weight: float = 1.0,
    ) -> bool:
        """
        投票

        Args:
            proposal_id: 提案ID
            voter_id: 投票者ID
            vote: 投票（agree, disagree, abstain）
            weight: 投票权重

        Returns:
            是否成功
        """
        proposal = self.active_proposals.get(proposal_id)

        if not proposal:
            logger.warning(f"提案不存在: {proposal_id}")
            return False

        if proposal.is_expired():
            logger.warning(f"提案已过期: {proposal_id}")
            return False

        if proposal.status != "pending":
            logger.warning(f"提案已关闭: {proposal_id}, 状态={proposal.status}")
            return False

        if vote not in ("agree", "disagree", "abstain"):
            logger.warning(f"无效的投票: {vote}")
            return False

        proposal.add_vote(voter_id, vote, weight)

        logger.debug(
            f"收到投票: 提案={proposal_id}, 投票者={voter_id}, "
            f"选择={vote}, 权重={weight}"
        )

        return True

    async def tally_votes(self, proposal_id: str) -> dict[str, Any]:
        """
        统计投票

        Args:
            proposal_id: 提案ID

        Returns:
            统计结果
        """
        proposal = self.active_proposals.get(proposal_id)

        if not proposal:
            logger.warning(f"提案不存在: {proposal_id}")
            return {"error": "proposal_not_found"}

        counts = proposal.get_vote_count()
        total_votes = sum(counts.values())
        total_weight = sum(
            v.get("weight", 1.0) for v in proposal.votes.values()
        )

        agree_weight = sum(
            v.get("weight", 1.0)
            for v in proposal.votes.values()
            if v["vote"] == "agree"
        )
        disagree_weight = sum(
            v.get("weight", 1.0)
            for v in proposal.votes.values()
            if v["vote"] == "disagree"
        )

        return {
            "proposal_id": proposal_id,
            "counts": counts,
            "total_votes": total_votes,
            "total_weight": total_weight,
            "agree_weight": agree_weight,
            "disagree_weight": disagree_weight,
            "agree_ratio": agree_weight / total_weight if total_weight > 0 else 0,
            "disagree_ratio": disagree_weight / total_weight if total_weight > 0 else 0,
        }

    async def calculate_decision(self, proposal_id: str) -> dict[str, Any]:
        """
        计算决策结果

        Args:
            proposal_id: 提案ID

        Returns:
            决策结果
        """
        proposal = self.active_proposals.get(proposal_id)

        if not proposal:
            return {"error": "proposal_not_found"}

        tally = await self.tally_votes(proposal_id)

        if "error" in tally:
            return tally

        decision_type = proposal.decision_type
        result = "pending"

        if decision_type == SwarmDecisionType.CONSENSUS:
            # 完全共识：所有人必须同意
            if (
                tally["counts"]["agree"] == tally["total_votes"]
                and tally["total_votes"] > 0
            ):
                result = "approved"
            elif tally["counts"]["disagree"] > 0:
                result = "rejected"

        elif decision_type == SwarmDecisionType.MAJORITY:
            # 简单多数
            if tally["agree_ratio"] > 0.5:
                result = "approved"
            elif tally["disagree_ratio"] >= 0.5:
                result = "rejected"

        elif decision_type == SwarmDecisionType.SUPER_MAJORITY:
            # 超级多数（2/3）
            if tally["agree_ratio"] >= 2 / 3:
                result = "approved"
            else:
                result = "rejected"

        elif decision_type == SwarmDecisionType.WEIGHTED:
            # 加权投票
            if tally["agree_weight"] > tally["disagree_weight"]:
                result = "approved"
            else:
                result = "rejected"

        elif decision_type == SwarmDecisionType.CONSENSUS:
            # 阈值共识
            if tally["agree_ratio"] >= proposal.consensus_threshold:
                result = "approved"
            else:
                result = "rejected"

        # 检查是否所有成员都已投票
        expected_voters = proposal.content.get("expected_voters", 0)
        if expected_voters > 0 and tally["total_votes"] < expected_voters:
            result = "pending"

        return {
            "proposal_id": proposal_id,
            "result": result,
            "tally": tally,
            "decision_type": decision_type.value,
        }

    async def finalize_decision(
        self,
        proposal_id: str,
        member_states: dict[str, AgentState],
    ) -> dict[str, Any]:
        """
        最终决策并关闭提案

        Args:
            proposal_id: 提案ID
            member_states: 成员状态（用于确定预期投票数）

        Returns:
            最终决策结果
        """
        proposal = self.active_proposals.get(proposal_id)

        if not proposal:
            return {"error": "proposal_not_found"}

        # 设置预期投票者
        proposal.content["expected_voters"] = len(member_states)

        # 计算决策
        decision = await self.calculate_decision(proposal_id)

        # 更新提案状态
        if decision["result"] in ("approved", "rejected"):
            proposal.status = decision["result"]
        elif proposal.is_expired():
            proposal.status = "expired"
            decision["result"] = "expired"

        # 记录历史
        history_entry = {
            "proposal_id": proposal_id,
            "decision": decision,
            "proposal": proposal.to_dict(),
            "timestamp": datetime.now().isoformat(),
        }
        self.decision_history.append(history_entry)

        # 如果已决策，从活跃提案中移除
        if proposal.status != "pending":
            del self.active_proposals[proposal_id]

        logger.info(
            f"决策完成: 提案={proposal_id}, 结果={decision['result']}, "
            f"类型={proposal.decision_type.value}"
        )

        return decision

    def calculate_vote_weight(
        self,
        agent_state: AgentState,
        proposal_context: dict[str, Any],
    ) -> float:
        """
        计算投票权重

        Args:
            agent_state: Agent状态
            proposal_context: 提案上下文

        Returns:
            投票权重
        """
        weight = 1.0

        # 基于声誉评分
        weight *= agent_state.reputation_score

        # 基于成功率
        total_tasks = (
            agent_state.tasks_completed + agent_state.tasks_failed
        )
        if total_tasks > 0:
            success_rate = agent_state.tasks_completed / total_tasks
            weight *= (0.5 + 0.5 * success_rate)

        # 基于专长匹配
        required_capability = proposal_context.get("required_capability")
        if required_capability:
            if agent_state.can_handle_capability(required_capability):
                weight *= 1.5  # 专长加权
            else:
                weight *= 0.5  # 非专长降权

        # 基于负载
        if agent_state.current_load > 0.8:
            weight *= 0.7  # 高负载降权

        return max(0.1, min(2.0, weight))  # 限制在[0.1, 2.0]范围内

    async def initiate_emergency_decision(
        self,
        emergency_type: str,
        context: dict[str, Any],
        participants: list[str],
    ) -> dict[str, Any]:
        """
        启动紧急决策

        Args:
            emergency_type: 紧急类型
            context: 上下文信息
            participants: 参与者列表

        Returns:
            决策结果
        """
        # 紧急决策使用快速流程
        proposal = await self.create_proposal(
            proposer="system",
            content={
                "emergency_type": emergency_type,
                "context": context,
                "expected_voters": len(participants),
            },
            proposal_type="emergency_response",
            decision_type=SwarmDecisionType.EMERGENCY,
            expires_in=5.0,  # 5秒快速决策
        )

        logger.warning(f"启动紧急决策: {proposal.proposal_id}, 类型={emergency_type}")

        return {
            "proposal_id": proposal.proposal_id,
            "status": "pending_votes",
            "timeout": 5.0,
        }

    def cleanup_expired_proposals(self) -> int:
        """
        清理过期提案

        Returns:
            清理的数量
        """
        expired_ids = []

        for proposal_id, proposal in self.active_proposals.items():
            if proposal.is_expired():
                expired_ids.append(proposal_id)

        for proposal_id in expired_ids:
            proposal = self.active_proposals.pop(proposal_id)
            proposal.status = "expired"
            logger.debug(f"清理过期提案: {proposal_id}")

        return len(expired_ids)

    def get_active_proposals(self) -> list[dict[str, Any]]:
        """
        获取活跃提案列表

        Returns:
            提案列表
        """
        return [p.to_dict() for p in self.active_proposals.values()]

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        total_proposals = len(self.decision_history)
        approved = sum(
            1
            for h in self.decision_history
            if h["proposal"].get("status") == "approved"
        )
        rejected = sum(
            1
            for h in self.decision_history
            if h["proposal"].get("status") == "rejected"
        )

        return {
            "active_proposals": len(self.active_proposals),
            "total_decisions": total_proposals,
            "approved_decisions": approved,
            "rejected_decisions": rejected,
            "success_rate": approved / total_proposals if total_proposals > 0 else 0,
        }
