#!/usr/bin/env python3

"""
串行协作模式
Sequential Collaboration Pattern

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0

智能体按顺序依次完成任务。
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from ...collaboration_manager import Conflict
from ...multi_agent_collaboration import (
    Message,
    MessageType,
    MultiAgentCollaborationFramework,
    Task,
    TaskStatus,
)
from ..base import CollaborationPattern

logger = logging.getLogger(__name__)


class SequentialCollaborationPattern(CollaborationPattern):
    """
    串行协作模式

    智能体按优先级顺序依次执行任务，每个智能体完成后才启动下一个。
    适用于有明确依赖关系和执行顺序的任务。
    """

    def __init__(self, framework: MultiAgentCollaborationFramework):
        """初始化串行协作模式"""
        super().__init__(framework)
        self.pattern_name = "串行协作"
        self.description = "智能体按顺序依次完成任务"

    async def initiate_collaboration(
        self, task: Task, participants: list[str], context: dict[str, Any]]
    ) -> Optional[str]:
        """启动串行协作"""
        try:
            session_id = str(uuid.uuid4())

            # 按优先级和能力排序参与者
            sorted_participants = self._sort_participants(participants, task)

            # 创建串行执行计划
            execution_plan = {
                "session_id": session_id,
                "task_id": task.id,
                "participants": sorted_participants,
                "current_index": 0,
                "execution_order": sorted_participants,
                "shared_context": context.copy(),
                "completed_steps": [],
                "results": {},
            }

            self.active_sessions[session_id] = execution_plan

            # 启动第一个智能体
            if sorted_participants:
                await self._start_agent_execution(session_id, sorted_participants[0])

            logger.info(f"串行协作会话 {session_id} 已启动")
            return session_id

        except Exception as e:
            logger.error(f"启动串行协作失败: {e}")
            return None

    def _sort_participants(self, participants: list[str], task: Task) -> list[str]:
        """按优先级和能力排序参与者"""
        participant_scores = []
        for participant_id in participants:
            agent = self.framework.agents.get(participant_id)
            if agent:
                # 计算适合度分数
                requirements = {"capabilities": task.required_capabilities}
                score = agent.calculate_suitability_score(requirements)
                participant_scores.append((participant_id, score))

        # 按分数降序排列
        participant_scores.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in participant_scores]

    async def _start_agent_execution(self, session_id: str, agent_id: str):
        """启动智能体执行"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 发送执行消息
            execution_message = Message(
                sender_id="sequential_collaboration",
                receiver_id=agent_id,
                message_type=MessageType.TASK_REQUEST,
                content={
                    "action": "execute_sequential_task",
                    "session_id": session_id,
                    "task_id": session["task_id"],
                    "context": session["shared_context"],
                    "step_index": session["current_index"],
                },
                requires_response=True,
            )

            self.framework.message_broker.publish(execution_message)

        except Exception as e:
            logger.error(f"启动智能体 {agent_id} 执行失败: {e}")

    async def coordinate_execution(self, session_id: str) -> bool:
        """协调串行执行"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False

            # 检查当前步骤是否完成
            current_index = session["current_index"]
            execution_order = session["execution_order"]

            if current_index < len(execution_order):
                # 当前步骤还在进行中
                return True
            else:
                # 所有步骤已完成
                await self._finalize_session(session_id)
                return True

        except Exception as e:
            logger.error(f"协调串行执行失败: {e}")
            return False

    async def handle_step_completion(self, session_id: str, agent_id: str, result: dict[str, Any]):
        """处理步骤完成"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 记录完成步骤和结果
            session["completed_steps"].append(agent_id)
            session["results"][agent_id] = result
            session["shared_context"].update(result.get("context_updates", {}))

            # 移动到下一个智能体
            session["current_index"] += 1
            next_index = session["current_index"]

            if next_index < len(session["execution_order"]):
                next_agent = session["execution_order"][next_index]
                await self._start_agent_execution(session_id, next_agent)
            else:
                # 所有步骤完成
                await self._finalize_session(session_id)

        except Exception as e:
            logger.error(f"处理步骤完成失败: {e}")

    async def _finalize_session(self, session_id: str):
        """完成会话"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 聚合所有结果
            final_result = {
                "session_id": session_id,
                "task_id": session["task_id"],
                "execution_order": session["execution_order"],
                "completed_steps": session["completed_steps"],
                "results": session["results"],
                "final_context": session["shared_context"],
                "completed_at": datetime.now(),
            }

            # 更新任务状态
            task = self.framework.tasks.get(session["task_id"])
            if task:
                task.status = TaskStatus.COMPLETED
                task.result = final_result
                task.update_progress(1.0)

            logger.info(f"串行协作会话 {session_id} 已完成")

        except Exception as e:
            logger.error(f"完成会话失败: {e}")

    async def handle_conflicts(self, session_id: str, conflicts: list[Conflict]) -> bool:
        """处理串行协作中的冲突"""
        # 串行协作冲突较少,主要是超时问题
        for conflict in conflicts:
            if conflict.conflict_type == "timeout":
                # 跳过当前智能体,继续下一个
                await self._skip_current_agent(session_id)
            elif conflict.conflict_type == "agent_failure":
                # 寻找替代智能体
                await self._find_replacement_agent(session_id)

        return True

    async def _skip_current_agent(self, session_id: str):
        """跳过当前智能体"""
        session = self.active_sessions.get(session_id)
        if session:
            session["current_index"] += 1
            next_index = session["current_index"]
            if next_index < len(session["execution_order"]):
                next_agent = session["execution_order"][next_index]
                await self._start_agent_execution(session_id, next_agent)

    async def _find_replacement_agent(self, session_id: str):
        """寻找替代智能体"""
        # 实现智能体替换逻辑
        pass

