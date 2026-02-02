#!/usr/bin/env python3
"""
协作协议 - 决策协议实现
Collaboration Protocols - Decision Protocol Implementation

处理多智能体集体决策

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

# 从本地模块导入
from core.protocols.collaboration.base import BaseProtocol
from core.protocols.collaboration.types import (
    ProtocolContext,
    ProtocolMessage,
    ProtocolPhase,
    ProtocolStatus,
    ProtocolType,
)

logger = logging.getLogger(__name__)


class DecisionProtocol(BaseProtocol):
    """决策协议 - 处理多智能体集体决策"""

    def __init__(self, protocol_id: str):
        super().__init__(protocol_id, ProtocolType.DECISION)
        self.decision_rules: dict[str, Any] = {}
        self.active_proposals: dict[str, dict[str, Any]] = {}
        self.voting_history: list[dict[str, Any]] = []
        self.consensus_threshold: float = 0.7

    async def initialize(self) -> bool:
        """初始化决策协议"""
        try:
            # 设置决策规则
            self.decision_rules = {
                "decision_making_method": "consensus",  # consensus, majority, weighted_vote, delegated
                "voting_timeout": timedelta(minutes=10),
                "min_participation": 0.5,  # 最少参与率
                "tie_breaking": "random",  # random, seniority, priority
                "revote_allowed": True,
                "max_revote_attempts": 2,
            }

            # 注册消息处理器
            self.register_message_handler("proposal", self._handle_proposal)
            self.register_message_handler("vote", self._handle_vote)
            self.register_message_handler(
                "decision_request", self._handle_decision_request
            )
            self.register_message_handler("objection", self._handle_objection)

            logger.info(f"决策协议 {self.protocol_id} 初始化完成")
            return True

        except Exception as e:
            logger.error(f"决策协议 {self.protocol_id} 初始化失败: {e}")
            return False

    async def execute(self) -> bool:
        """执行决策协议"""
        try:
            self.context.current_phase = ProtocolPhase.EXECUTION

            # 处理提案和投票
            while self.running:
                # 检查提案超时
                await self._check_proposal_timeouts()

                # 检查投票结果
                await self._process_voting_results()

                # 等待下次检查
                await asyncio.sleep(5)  # 每5秒检查一次

            return True

        except Exception as e:
            logger.error(f"决策协议 {self.protocol_id} 执行失败: {e}")
            return False

    async def _check_proposal_timeouts(self) -> None:
        """检查提案超时"""
        try:
            current_time = datetime.now()
            timeout = self.decision_rules["voting_timeout"]

            expired_proposals = []
            for proposal_id, proposal in self.active_proposals.items():
                if current_time - proposal["created_at"] > timeout:
                    expired_proposals.append(proposal_id)

            for proposal_id in expired_proposals:
                await self._handle_proposal_timeout(proposal_id)

        except Exception as e:
            logger.error(f"检查提案超时失败: {e}")

    async def _process_voting_results(self) -> None:
        """处理投票结果"""
        try:
            for proposal_id, proposal in list(self.active_proposals.items()):
                if await self._is_voting_complete(proposal):
                    result = await self._tally_votes(proposal)
                    await self._finalize_decision(proposal_id, result)

        except Exception as e:
            logger.error(f"处理投票结果失败: {e}")

    async def _is_voting_complete(self, proposal: dict[str, Any]) -> bool:
        """检查投票是否完成"""
        participants = proposal.get("participants", [])
        votes = proposal.get("votes", {})
        min_participation = self.decision_rules["min_participation"]

        # 检查参与率
        participation_rate = len(votes) / len(participants) if participants else 0
        if participation_rate < min_participation:
            return False

        # 检查是否所有人都已投票
        return len(votes) >= len(participants)

    async def _tally_votes(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """统计投票结果"""
        try:
            votes = proposal.get("votes", {})
            method = self.decision_rules["decision_making_method"]

            if method == "consensus":
                return await self._tally_consensus_votes(votes)
            elif method == "majority":
                return await self._tally_majority_votes(votes)
            elif method == "weighted_vote":
                return await self._tally_weighted_votes(votes, proposal)
            elif method == "delegated":
                return await self._tally_delegated_votes(votes, proposal)

            return {"decision": "undetermined", "reason": "unknown_voting_method"}

        except Exception as e:
            logger.error(f"统计投票失败: {e}")
            return {"decision": "error", "reason": str(e)}

    async def _tally_consensus_votes(
        self, votes: dict[str, dict[str, Any]) -> dict[str, Any]:
        """统计共识投票"""
        agree_votes = sum(
            1 for vote in votes.values() if vote.get("decision") == "agree"
        )
        total_votes = len(votes)

        consensus_ratio = agree_votes / total_votes if total_votes > 0 else 0

        if consensus_ratio >= self.consensus_threshold:
            return {
                "decision": "consensus_reached",
                "method": "consensus",
                "agree_votes": agree_votes,
                "total_votes": total_votes,
                "consensus_ratio": consensus_ratio,
            }
        else:
            return {
                "decision": "no_consensus",
                "method": "consensus",
                "agree_votes": agree_votes,
                "total_votes": total_votes,
                "consensus_ratio": consensus_ratio,
            }

    async def _tally_majority_votes(
        self, votes: dict[str, dict[str, Any]) -> dict[str, Any]:
        """统计多数投票"""
        agree_votes = sum(
            1 for vote in votes.values() if vote.get("decision") == "agree"
        )
        total_votes = len(votes)

        if agree_votes > total_votes / 2:
            return {
                "decision": "majority_agree",
                "method": "majority",
                "agree_votes": agree_votes,
                "disagree_votes": total_votes - agree_votes,
                "total_votes": total_votes,
            }
        else:
            return {
                "decision": "majority_disagree",
                "method": "majority",
                "agree_votes": agree_votes,
                "disagree_votes": total_votes - agree_votes,
                "total_votes": total_votes,
            }

    async def _tally_weighted_votes(
        self, votes: dict[str, dict[str, Any], proposal: dict[str, Any]
    ) -> dict[str, Any]:
        """统计加权投票"""
        # 获取参与者权重
        participant_weights = proposal.get("participant_weights", {})

        agree_weight = 0
        total_weight = 0

        for voter_id, vote in votes.items():
            weight = participant_weights.get(voter_id, 1)  # 默认权重为1
            total_weight += weight

            if vote.get("decision") == "agree":
                agree_weight += weight

        agree_ratio = agree_weight / total_weight if total_weight > 0 else 0

        if agree_ratio > 0.5:
            return {
                "decision": "weighted_majority_agree",
                "method": "weighted_vote",
                "agree_weight": agree_weight,
                "total_weight": total_weight,
                "agree_ratio": agree_ratio,
            }
        else:
            return {
                "decision": "weighted_majority_disagree",
                "method": "weighted_vote",
                "agree_weight": agree_weight,
                "total_weight": total_weight,
                "agree_ratio": agree_ratio,
            }

    async def _tally_delegated_votes(
        self, votes: dict[str, dict[str, Any], proposal: dict[str, Any]
    ) -> dict[str, Any]:
        """统计委托投票"""
        # 实现委托投票统计逻辑
        # 这里简化处理,实际实现需要考虑委托关系
        return await self._tally_majority_votes(votes)

    async def _finalize_decision(
        self, proposal_id: str, result: dict[str, Any]
    ) -> None:
        """最终确定决策"""
        try:
            proposal = self.active_proposals.get(proposal_id)
            if not proposal:
                return

            # 记录决策结果
            decision_record = {
                "proposal_id": proposal_id,
                "decision": result["decision"],
                "method": result["method"],
                "voting_summary": result,
                "decided_at": datetime.now(),
                "proposal_content": proposal["content"],
            }

            self.voting_history.append(decision_record)

            # 从活跃提案中移除
            del self.active_proposals[proposal_id]

            # 更新共享状态
            self.update_shared_state(f"decision_{proposal_id}", result)
            self.trigger_event("decision_made", decision_record)

            # 通知所有参与者
            notification = ProtocolMessage(
                sender_id="decision_protocol",
                receiver_id="broadcast",
                message_type="notification",
                content={
                    "event_type": "decision_finalized",
                    "proposal_id": proposal_id,
                    "decision": result,
                },
            )
            self.send_message(notification)

            logger.info(f"提案 {proposal_id} 决策完成: {result['decision']}")

        except Exception as e:
            logger.error(f"最终确定决策失败: {e}")

    async def _handle_proposal_timeout(self, proposal_id: str) -> None:
        """处理提案超时"""
        try:
            proposal = self.active_proposals.get(proposal_id)
            if not proposal:
                return

            # 检查是否允许重新投票
            if self.decision_rules["revote_allowed"]:
                revote_attempts = proposal.get("revote_attempts", 0)
                max_revote_attempts = self.decision_rules["max_revote_attempts"]

                if revote_attempts < max_revote_attempts:
                    # 重新发起投票
                    proposal["revote_attempts"] = revote_attempts + 1
                    proposal["created_at"] = datetime.now()  # 重置时间戳
                    proposal["votes"] = {}  # 清空之前投票

                    # 通知参与者重新投票
                    notification = ProtocolMessage(
                        sender_id="decision_protocol",
                        receiver_id="broadcast",
                        message_type="notification",
                        content={
                            "event_type": "revote_requested",
                            "proposal_id": proposal_id,
                            "attempt": revote_attempts + 1,
                        },
                    )
                    self.send_message(notification)

                    logger.info(
                        f"提案 {proposal_id} 重新投票,第 {revote_attempts + 1} 次尝试"
                    )
                    return

            # 超时且无法重新投票,标记为失败
            await self._finalize_decision(
                proposal_id,
                {
                    "decision": "timeout",
                    "reason": "voting_timeout",
                    "revote_attempts": proposal.get("revote_attempts", 0),
                },
            )

        except Exception as e:
            logger.error(f"处理提案超时失败: {e}")

    async def _handle_proposal(self, message: ProtocolMessage) -> None:
        """处理提案"""
        try:
            proposal_content = message.content.get("proposal")
            proposer_id = message.sender_id

            if proposal_content:
                proposal_id = str(uuid.uuid4())

                proposal = {
                    "proposal_id": proposal_id,
                    "proposer_id": proposer_id,
                    "content": proposal_content,
                    "participants": self.context.participants.copy(),
                    "votes": {},
                    "created_at": datetime.now(),
                    "status": "active",
                    "revote_attempts": 0,
                }

                self.active_proposals[proposal_id] = proposal

                # 通知所有参与者有新提案
                notification = ProtocolMessage(
                    sender_id="decision_protocol",
                    receiver_id="broadcast",
                    message_type="notification",
                    content={
                        "event_type": "new_proposal",
                        "proposal_id": proposal_id,
                        "proposer": proposer_id,
                        "proposal_content": proposal_content,
                    },
                )
                self.send_message(notification)

                logger.info(f"收到新提案 {proposal_id},来自 {proposer_id}")

        except Exception as e:
            logger.error(f"处理提案失败: {e}")

    async def _handle_vote(self, message: ProtocolMessage) -> None:
        """处理投票"""
        try:
            proposal_id = message.content.get("proposal_id")
            vote_decision = message.content.get("decision")
            voter_id = message.sender_id
            vote_reason = message.content.get("reason", "")

            if proposal_id and vote_decision:
                proposal = self.active_proposals.get(proposal_id)
                if proposal:
                    # 记录投票
                    proposal["votes"][voter_id] = {
                        "decision": vote_decision,
                        "reason": vote_reason,
                        "voted_at": datetime.now(),
                    }

                    logger.info(
                        f"智能体 {voter_id} 对提案 {proposal_id} 投票: {vote_decision}"
                    )

        except Exception as e:
            logger.error(f"处理投票失败: {e}")

    async def _handle_decision_request(self, message: ProtocolMessage) -> None:
        """处理决策请求"""
        try:
            decision_type = message.content.get("decision_type")
            message.content.get("context", {})

            if decision_type == "quick_poll":
                # 快速投票
                await self._handle_quick_poll(message)
            elif decision_type == "consensus_building":
                # 共识建立
                await self._handle_consensus_building(message)

        except Exception as e:
            logger.error(f"处理决策请求失败: {e}")

    async def _handle_objection(self, message: ProtocolMessage) -> None:
        """处理异议"""
        try:
            proposal_id = message.content.get("proposal_id")
            objection_reason = message.content.get("reason")
            objector_id = message.sender_id

            if proposal_id and objection_reason:
                proposal = self.active_proposals.get(proposal_id)
                if proposal:
                    # 记录异议
                    if "objections" not in proposal:
                        proposal["objections"] = []

                    proposal["objections"].append(
                        {
                            "objector_id": objector_id,
                            "reason": objection_reason,
                            "timestamp": datetime.now(),
                        }
                    )

                    # 异议可能需要重新协商
                    self.trigger_event(
                        "objection_raised",
                        {
                            "proposal_id": proposal_id,
                            "objector_id": objector_id,
                            "reason": objection_reason,
                        },
                    )

                    logger.info(f"收到对提案 {proposal_id} 的异议: {objection_reason}")

        except Exception as e:
            logger.error(f"处理异议失败: {e}")

    async def _handle_quick_poll(self, message: ProtocolMessage) -> None:
        """处理快速投票"""
        # 实现快速投票逻辑
        pass

    async def _handle_consensus_building(self, message: ProtocolMessage) -> None:
        """处理共识建立"""
        # 实现共识建立逻辑
        pass
