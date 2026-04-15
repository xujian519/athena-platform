#!/usr/bin/env python3
"""
协作模式实现
Collaboration Patterns Implementation

实现各种多智能体协作模式的具体逻辑
"""

from __future__ import annotations
import logging
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from .collaboration_manager import Conflict
from .multi_agent_collaboration import (
    Message,
    MessageType,
    MultiAgentCollaborationFramework,
    Task,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class CollaborationPattern(ABC):
    """协作模式抽象基类"""

    def __init__(self, framework: MultiAgentCollaborationFramework):
        self.framework = framework
        self.pattern_id = str(uuid.uuid4())
        self.active_sessions: dict[str, dict[str, Any]] = {}

    @abstractmethod
    async def initiate_collaboration(
        self, task: Task, participants: list[str], context: dict[str, Any]
    ) -> str | None:
        """启动协作"""
        pass

    @abstractmethod
    async def coordinate_execution(self, session_id: str) -> bool:
        """协调执行"""
        pass

    @abstractmethod
    async def handle_conflicts(self, session_id: str, conflicts: list[Conflict]) -> bool:
        """处理冲突"""
        pass


class SequentialCollaborationPattern(CollaborationPattern):
    """串行协作模式"""

    def __init__(self, framework: MultiAgentCollaborationFramework):
        super().__init__(framework)
        self.pattern_name = "串行协作"
        self.description = "智能体按顺序依次完成任务"

    async def initiate_collaboration(
        self, task: Task, participants: list[str], context: dict[str, Any]
    ) -> str | None:
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


class ParallelCollaborationPattern(CollaborationPattern):
    """并行协作模式"""

    def __init__(self, framework: MultiAgentCollaborationFramework):
        super().__init__(framework)
        self.pattern_name = "并行协作"
        self.description = "智能体同时并行处理任务的不同部分"

    async def initiate_collaboration(
        self, task: Task, participants: list[str], context: dict[str, Any]
    ) -> str | None:
        """启动并行协作"""
        try:
            session_id = str(uuid.uuid4())

            # 分解任务为子任务
            subtasks = await self._decompose_task(task, participants)

            # 创建并行执行计划
            execution_plan = {
                "session_id": session_id,
                "task_id": task.id,
                "participants": participants,
                "subtasks": subtasks,
                "shared_context": context.copy(),
                "completed_subtasks": set(),
                "subtask_results": {},
                "synchronization_points": ["start", "mid", "end"],
            }

            self.active_sessions[session_id] = execution_plan

            # 同时启动所有智能体
            for subtask in subtasks:
                await self._start_subtask_execution(session_id, subtask)

            logger.info(f"并行协作会话 {session_id} 已启动,{len(subtasks)} 个子任务")
            return session_id

        except Exception as e:
            logger.error(f"启动并行协作失败: {e}")
            return None

    async def _decompose_task(self, task: Task, participants: list[str]) -> list[dict[str, Any]]:
        """分解任务为子任务"""
        subtasks = []
        max(1, len(participants) // 3)  # 每个子任务至少1个参与者

        # 简单的按能力分组分解
        capability_groups = self._group_agents_by_capability(participants)

        for i, (capability, agents) in enumerate(capability_groups.items()):
            subtask = {
                "subtask_id": f"subtask_{i}",
                "capability_focus": capability,
                "assigned_agents": agents,
                "description": f"处理与{capability}相关的任务部分",
                "dependencies": [],  # 子任务间无依赖
                "estimated_duration": timedelta(minutes=30),
            }
            subtasks.append(subtask)

        return subtasks

    def _group_agents_by_capability(self, participants: list[str]) -> dict[str, list[str]]:
        """按能力分组智能体"""
        groups = {}
        for participant_id in participants:
            agent = self.framework.agents.get(participant_id)
            if agent and agent.capabilities:
                # 使用主要能力进行分组
                primary_capability = agent.capabilities[0].name if agent.capabilities else "general"
                if primary_capability not in groups:
                    groups[primary_capability] = []
                groups[primary_capability].append(participant_id)

        return groups

    async def _start_subtask_execution(self, session_id: str, subtask: dict[str, Any]):
        """启动子任务执行"""
        try:
            for agent_id in subtask["assigned_agents"]:
                execution_message = Message(
                    sender_id="parallel_collaboration",
                    receiver_id=agent_id,
                    message_type=MessageType.TASK_REQUEST,
                    content={
                        "action": "execute_parallel_subtask",
                        "session_id": session_id,
                        "subtask_id": subtask["subtask_id"],
                        "capability_focus": subtask["capability_focus"],
                        "context": self.active_sessions[session_id]["shared_context"],
                        "agents_in_subtask": subtask["assigned_agents"],
                    },
                    requires_response=True,
                )

                self.framework.message_broker.publish(execution_message)

        except Exception as e:
            logger.error(f"启动子任务 {subtask['subtask_id']} 执行失败: {e}")

    async def coordinate_execution(self, session_id: str) -> bool:
        """协调并行执行"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False

            total_subtasks = len(session["subtasks"])
            completed_subtasks = len(session["completed_subtasks"])

            if completed_subtasks < total_subtasks:
                # 还有子任务未完成
                # 检查是否需要同步点协调
                await self._check_synchronization_points(session_id)
                return True
            else:
                # 所有子任务完成
                await self._finalize_parallel_session(session_id)
                return True

        except Exception as e:
            logger.error(f"协调并行执行失败: {e}")
            return False

    async def _check_synchronization_points(self, session_id: str):
        """检查同步点"""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        completed_ratio = len(session["completed_subtasks"]) / len(session["subtasks"])

        # 中点同步
        if completed_ratio >= 0.5 and "mid_sync_completed" not in session:
            await self._perform_midpoint_sync(session_id)
            session["mid_sync_completed"] = True

    async def _perform_midpoint_sync(self, session_id: str):
        """执行中点同步"""
        try:
            # 收集中间结果
            session = self.active_sessions[session_id]
            intermediate_results = session["subtask_results"]

            # 创建同步消息
            sync_message = Message(
                sender_id="parallel_collaboration",
                receiver_id="",
                message_type=MessageType.COORDINATION,
                content={
                    "action": "midpoint_sync",
                    "session_id": session_id,
                    "intermediate_results": intermediate_results,
                    "progress_ratio": len(session["completed_subtasks"]) / len(session["subtasks"]),
                },
            )

            self.framework.message_broker.publish(sync_message)

            logger.info(f"并行协作会话 {session_id} 中点同步完成")

        except Exception as e:
            logger.error(f"中点同步失败: {e}")

    async def handle_subtask_completion(
        self, session_id: str, subtask_id: str, agent_id: str, result: dict[str, Any]
    ):
        """处理子任务完成"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 记录子任务结果
            if subtask_id not in session["subtask_results"]:
                session["subtask_results"][subtask_id] = {}

            session["subtask_results"][subtask_id][agent_id] = result

            # 更新共享上下文
            context_updates = result.get("context_updates", {})
            session["shared_context"].update(context_updates)

            # 检查该子任务是否所有智能体都完成
            subtask = next(
                (st for st in session["subtasks"] if st["subtask_id"] == subtask_id), None
            )
            if subtask:
                completed_agents = set(session["subtask_results"][subtask_id].keys())
                assigned_agents = set(subtask["assigned_agents"])

                if completed_agents >= assigned_agents:
                    session["completed_subtasks"].add(subtask_id)

            logger.info(f"子任务 {subtask_id} 由智能体 {agent_id} 完成")

        except Exception as e:
            logger.error(f"处理子任务完成失败: {e}")

    async def _finalize_parallel_session(self, session_id: str):
        """完成并行会话"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # 聚合所有子任务结果
            final_result = {
                "session_id": session_id,
                "task_id": session["task_id"],
                "subtask_results": session["subtask_results"],
                "completed_subtasks": list(session["completed_subtasks"]),
                "final_context": session["shared_context"],
                "completion_ratio": len(session["completed_subtasks"]) / len(session["subtasks"]),
                "completed_at": datetime.now(),
            }

            # 更新任务状态
            task = self.framework.tasks.get(session["task_id"])
            if task:
                if len(session["completed_subtasks"]) == len(session["subtasks"]):
                    task.status = TaskStatus.COMPLETED
                    task.update_progress(1.0)
                else:
                    task.status = TaskStatus.IN_PROGRESS
                    task.update_progress(
                        len(session["completed_subtasks"]) / len(session["subtasks"])
                    )

                task.result = final_result

            logger.info(f"并行协作会话 {session_id} 已完成")

        except Exception as e:
            logger.error(f"完成并行会话失败: {e}")

    async def handle_conflicts(self, session_id: str, conflicts: list[Conflict]) -> bool:
        """处理并行协作中的冲突"""
        for conflict in conflicts:
            if conflict.conflict_type == "resource_conflict":
                # 资源冲突:使用优先级调度
                await self._handle_resource_conflict(session_id, conflict)
            elif conflict.conflict_type == "inconsistent_results":
                # 结果不一致:启动冲突解决流程
                await self._handle_result_conflict(session_id, conflict)

        return True

    async def _handle_resource_conflict(self, session_id: str, conflict: Conflict):
        """处理资源冲突"""
        # 实现资源冲突解决逻辑
        pass

    async def _handle_result_conflict(self, session_id: str, conflict: Conflict):
        """处理结果冲突"""
        # 实现结果冲突解决逻辑
        pass


class HierarchicalCollaborationPattern(CollaborationPattern):
    """层次协作模式"""

    def __init__(self, framework: MultiAgentCollaborationFramework):
        super().__init__(framework)
        self.pattern_name = "层次协作"
        self.description = "基于主从关系的层次化协作"

    async def initiate_collaboration(
        self, task: Task, participants: list[str], context: dict[str, Any]
    ) -> str | None:
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


class ConsensusCollaborationPattern(CollaborationPattern):
    """共识协作模式"""

    def __init__(self, framework: MultiAgentCollaborationFramework):
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


class CollaborationPatternFactory:
    """协作模式工厂"""

    _patterns = {
        "sequential": SequentialCollaborationPattern,
        "parallel": ParallelCollaborationPattern,
        "hierarchical": HierarchicalCollaborationPattern,
        "consensus": ConsensusCollaborationPattern,
    }

    @classmethod
    def create_pattern(
        cls, pattern_type: str, framework: MultiAgentCollaborationFramework
    ) -> CollaborationPattern | None:
        """创建协作模式实例"""
        pattern_class = cls._patterns.get(pattern_type.lower())
        if pattern_class:
            return pattern_class(framework)
        else:
            logger.error(f"未知的协作模式类型: {pattern_type}")
            return None

    @classmethod
    def get_available_patterns(cls) -> list[str]:
        """获取可用的协作模式列表"""
        return list(cls._patterns.keys())

    @classmethod
    def register_pattern(cls, pattern_type: str, pattern_class: type) -> Any:
        """注册新的协作模式"""
        cls._patterns[pattern_type.lower()] = pattern_class
        logger.info(f"协作模式 {pattern_type} 已注册")
