#!/usr/bin/env python3
from __future__ import annotations
"""
层次协作模式
Hierarchical Collaboration Pattern

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0

基于主从关系的层次化协作，协调者-工作者模式。
"""

import logging
import uuid
from typing import Any

from ...collaboration_manager import Conflict
from ...multi_agent_collaboration import (
    Message,
    MessageType,
    MultiAgentCollaborationFramework,
    Task,
)
from ..base import CollaborationPattern

logger = logging.getLogger(__name__)


class HierarchicalCollaborationPattern(CollaborationPattern):
    """
    层次协作模式

    基于主从关系的层次化协作，有一个协调智能体和多个工作者智能体。
    协作过程分为三个阶段:规划阶段、执行阶段、集成阶段。
    """

    def __init__(self, framework: MultiAgentCollaborationFramework):
        """初始化层次协作模式"""
        super().__init__(framework)
        self.pattern_name = "层次协作"
        self.description = "基于主从关系的层次化协作"

    async def initiate_collaboration(
        self, task: Task, participants: list[str], context: dict[str, Any]
    ) -> Optional[str]:
        """启动层次协作"""
        try:
            session_id = str(uuid.uuid4())

            # 确定协调者和工作者
            coordinator, workers = self._identify_roles(participants)

            # 创建层次执行计划
            execution_plan = {
                "session_id": session_id,
                "task_id": task.id,
                "coordinator": coordinator,
                "workers": workers,
                "hierarchy_level": 0,  # 0=规划阶段, 1=执行阶段, 2=集成阶段
                "shared_context": context.copy(),
                "subtask_assignments": {},
                "worker_status": dict.fromkeys(workers, "idle"),
                "aggregated_results": {},
            }

            self.active_sessions[session_id] = execution_plan

            # 启动协调者进行任务规划
            await self._start_planning_phase(session_id)

            logger.info(f"层次协作会话 {session_id} 已启动,协调者: {coordinator}")
            return session_id

        except Exception as e:
            logger.error(f"启动层次协作失败: {e}")
            return None

    def _identify_roles(self, participants: list[str]) -> tuple[str, list[str]]:
        """识别协调者和工作者"""
        coordinator = None
        workers = []

        for participant_id in participants:
            agent = self.framework.agents.get(participant_id)
            if agent:
                role = agent.metadata.get("role", "worker")
                if role == "coordinator" and coordinator is None:
                    coordinator = participant_id
                else:
                    workers.append(participant_id)

        # 如果没有明确指定协调者,选择能力最强的
        if coordinator is None and workers:
            coordinator = workers[0]
            workers = workers[1:]

        return coordinator, workers

    async def _start_planning_phase(self, session_id: str):
        """启动规划阶段"""
        try:
            session = self.active_sessions.get(session_id)
            if not session or not session["coordinator"]:
                return

            planning_message = Message(
                sender_id="hierarchical_collaboration",
                receiver_id=session["coordinator"],
                message_type=MessageType.TASK_REQUEST,
                content={
                    "action": "plan_task_decomposition",
                    "session_id": session_id,
                    "task_id": session["task_id"],
                    "available_workers": session["workers"],
                    "context": session["shared_context"],
                },
                requires_response=True,
            )

            self.framework.message_broker.publish(planning_message)
            session["hierarchy_level"] = 1  # 进入执行阶段

        except Exception as e:
            logger.error(f"启动规划阶段失败: {e}")

    async def coordinate_execution(self, session_id: str) -> bool:
        """协调层次执行"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False

            if session["hierarchy_level"] == 1:
                # 执行阶段
                await self._coordinate_execution_phase(session_id)
            elif session["hierarchy_level"] == 2:
                # 集成阶段
                await self._coordinate_integration_phase(session_id)

            return True

        except Exception as e:
            logger.error(f"协调层次执行失败: {e}")
            return False

    async def _coordinate_execution_phase(self, session_id: str):
        """协调执行阶段"""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        # 检查是否所有工作者都完成
        all_completed = all(status == "completed" for status in session["worker_status"].values())

        if all_completed and session["hierarchy_level"] == 1:
            # 启动集成阶段
            await self._start_integration_phase(session_id)

    async def _start_integration_phase(self, session_id: str):
        """启动集成阶段"""
        try:
            session = self.active_sessions.get(session_id)
            if not session or not session["coordinator"]:
                return

            integration_message = Message(
                sender_id="hierarchical_collaboration",
                receiver_id=session["coordinator"],
                message_type=MessageType.TASK_REQUEST,
                content={
                    "action": "integrate_results",
                    "session_id": session_id,
                    "task_id": session["task_id"],
                    "worker_results": session["aggregated_results"],
                    "context": session["shared_context"],
                },
                requires_response=True,
            )

            self.framework.message_broker.publish(integration_message)
            session["hierarchy_level"] = 2  # 进入集成阶段

        except Exception as e:
            logger.error(f"启动集成阶段失败: {e}")

    async def _coordinate_integration_phase(self, session_id: str):
        """协调集成阶段"""
        # 等待协调者完成结果集成
        pass

    async def handle_planning_result(self, session_id: str, decomposition: dict[str, Any]):
        """处理规划结果"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 分配子任务给工作者
            subtask_assignments = decomposition.get("subtask_assignments", {})
            session["subtask_assignments"] = subtask_assignments

            # 通知各个工作者
            for worker_id, subtask in subtask_assignments.items():
                assignment_message = Message(
                    sender_id="hierarchical_collaboration",
                    receiver_id=worker_id,
                    message_type=MessageType.TASK_REQUEST,
                    content={
                        "action": "execute_assigned_subtask",
                        "session_id": session_id,
                        "subtask": subtask,
                        "coordinator": session["coordinator"],
                        "context": session["shared_context"],
                    },
                    requires_response=True,
                )

                self.framework.message_broker.publish(assignment_message)
                session["worker_status"][worker_id] = "assigned"

        except Exception as e:
            logger.error(f"处理规划结果失败: {e}")

    async def handle_worker_completion(
        self, session_id: str, worker_id: str, result: dict[str, Any]
    ):
        """处理工作者完成"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 记录工作者结果
            session["aggregated_results"][worker_id] = result
            session["worker_status"][worker_id] = "completed"

            # 更新共享上下文
            context_updates = result.get("context_updates", {})
            session["shared_context"].update(context_updates)

            # 通知协调者进度更新
            progress_message = Message(
                sender_id="hierarchical_collaboration",
                receiver_id=session["coordinator"],
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "action": "worker_progress_update",
                    "session_id": session_id,
                    "worker_id": worker_id,
                    "status": "completed",
                    "result_summary": result.get("summary", {}),
                },
            )

            self.framework.message_broker.publish(progress_message)

        except Exception as e:
            logger.error(f"处理工作者完成失败: {e}")

    async def handle_conflicts(self, session_id: str, conflicts: list[Conflict]) -> bool:
        """处理层次协作中的冲突"""
        for conflict in conflicts:
            if conflict.conflict_type == "coordination_conflict":
                # 协调冲突:由协调者解决
                await self._escalate_to_coordinator(session_id, conflict)
            elif conflict.conflict_type == "worker_failure":
                # 工作者失败:重新分配任务
                await self._handle_worker_failure(session_id, conflict)

        return True

    async def _escalate_to_coordinator(self, session_id: str, conflict: Conflict):
        """将冲突上报给协调者"""
        try:
            session = self.active_sessions.get(session_id)
            if not session or not session["coordinator"]:
                return

            escalation_message = Message(
                sender_id="hierarchical_collaboration",
                receiver_id=session["coordinator"],
                message_type=MessageType.COORDINATION,
                content={
                    "action": "conflict_escalation",
                    "session_id": session_id,
                    "conflict": conflict.__dict__,
                },
            )

            self.framework.message_broker.publish(escalation_message)

        except Exception as e:
            logger.error(f"冲突上报失败: {e}")

    async def _handle_worker_failure(self, session_id: str, conflict: Conflict):
        """处理工作者失败"""
        # 实现工作者失败处理逻辑
        pass
