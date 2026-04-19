#!/usr/bin/env python3
from __future__ import annotations
"""
协作管理器
Collaboration Manager

负责管理多智能体协作的工作流程,包括任务分解、协调策略、冲突解决等
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .multi_agent_collaboration import (
    CollaborationStrategy,
    ConflictResolutionStrategy,
    Message,
    MessageType,
    MultiAgentCollaborationFramework,
    Priority,
    TaskStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class CollaborationTemplate:
    """协作模板"""

    id: str
    name: str
    description: str
    strategy: CollaborationStrategy
    required_agents: list[str]  # 所需智能体类型
    agent_roles: dict[str, str]  # 智能体角色定义
    workflow_steps: list[dict[str, Any]]  # 工作流步骤
    coordination_rules: dict[str, Any]  # 协调规则
    conflict_resolution: ConflictResolutionStrategy  # 冲突解决策略
    communication_pattern: str  # 通信模式
    success_criteria: dict[str, Any]  # 成功标准


@dataclass
class WorkflowStep:
    """工作流步骤"""

    step_id: str
    name: str
    description: str
    assigned_agents: list[str]  # 分配的智能体
    dependencies: list[str]  # 依赖的步骤
    expected_duration: timedelta
    inputs: dict[str, Any]  # 输入要求
    outputs: dict[str, Any]  # 输出期望
    validation_rules: dict[str, Any]  # 验证规则
    retry_policy: dict[str, Any]  # 重试策略
    status: str = "pending"  # 步骤状态


@dataclass
class Conflict:
    """冲突定义"""

    conflict_id: str
    conflict_type: str  # 冲突类型
    involved_agents: list[str]  # 涉及的智能体
    conflicting_resources: list[str]  # 冲突的资源
    conflict_description: str  # 冲突描述
    detected_at: datetime  # 检测时间
    severity: int  # 严重程度 (1-10)
    resolution_strategy: ConflictResolutionStrategy | None = None
    resolved_at: datetime | None = None  # 解决时间
    resolution_details: dict[str, Any] | None = None


class CollaborationOrchestrator:
    """协作编排器 - 负责编排和管理协作过程"""

    def __init__(self, framework: MultiAgentCollaborationFramework):
        self.framework = framework
        self.templates: dict[str, CollaborationTemplate] = {}
        self.active_workflows: dict[str, list[WorkflowStep]] = {}
        self.conflicts: list[Conflict] = []
        self.coordination_policies: dict[str, Any] = {}
        self.monitoring_metrics: dict[str, Any] = {}
        self._setup_default_templates()

    def _setup_default_templates(self) -> Any:
        """设置默认协作模板"""
        # 简单并行协作模板
        parallel_template = CollaborationTemplate(
            id="parallel_collaboration",
            name="并行协作模板",
            description="多个智能体并行处理任务",
            strategy=CollaborationStrategy.PARALLEL,
            required_agents=["any"],
            agent_roles={"all": "contributor"},
            workflow_steps=[
                {"step_id": "task_distribution", "name": "任务分发", "parallel": False},
                {"step_id": "parallel_execution", "name": "并行执行", "parallel": True},
                {"step_id": "result_aggregation", "name": "结果聚合", "parallel": False},
            ],
            coordination_rules={
                "communication_pattern": "broadcast",
                "synchronization_points": ["start", "end"],
            },
            conflict_resolution=ConflictResolutionStrategy.PRIORITY_BASED,
            communication_pattern="broadcast",
            success_criteria={"all_steps_completed": True, "min_quality_score": 0.8},
        )
        self.templates[parallel_template.id] = parallel_template

        # 层次协作模板
        hierarchical_template = CollaborationTemplate(
            id="hierarchical_collaboration",
            name="层次协作模板",
            description="主从式层次协作",
            strategy=CollaborationStrategy.HIERARCHICAL,
            required_agents=["coordinator", "worker"],
            agent_roles={"coordinator": "主协调者", "worker": "工作执行者"},
            workflow_steps=[
                {"step_id": "planning", "name": "规划阶段", "assigned_role": "coordinator"},
                {"step_id": "delegation", "name": "任务委派", "assigned_role": "coordinator"},
                {"step_id": "execution", "name": "执行阶段", "assigned_role": "worker"},
                {"step_id": "integration", "name": "结果集成", "assigned_role": "coordinator"},
            ],
            coordination_rules={
                "communication_pattern": "hierarchical",
                "reporting_interval": "progress",
            },
            conflict_resolution=ConflictResolutionStrategy.HIERARCHICAL,
            communication_pattern="hierarchical",
            success_criteria={"coordinator_approval": True, "worker_tasks_completed": True},
        )
        self.templates[hierarchical_template.id] = hierarchical_template

    def register_template(self, template: CollaborationTemplate) -> bool:
        """注册协作模板"""
        try:
            self.templates[template.id] = template
            logger.info(f"协作模板 {template.name} ({template.id}) 注册成功")
            return True
        except Exception as e:
            logger.error(f"注册协作模板失败: {e}")
            return False

    def start_collaboration_workflow(
        self,
        task_id: str,
        template_id: str,
        participating_agents: list[str],
        context: dict[str, Any],    ) -> str | None:
        """启动协作工作流"""
        try:
            if template_id not in self.templates:
                logger.error(f"协作模板 {template_id} 不存在")
                return None

            template = self.templates[template_id]
            workflow_id = str(uuid.uuid4())

            # 创建工作流步骤
            workflow_steps = []
            for _i, step_def in enumerate(template.workflow_steps):
                step = WorkflowStep(
                    step_id=f"{workflow_id}_{step_def['step_id']}",
                    name=step_def["name"],
                    description=step_def.get("description", ""),
                    assigned_agents=self._select_agents_for_step(
                        step_def, participating_agents, template.agent_roles
                    ),
                    dependencies=step_def.get("dependencies", []),
                    expected_duration=timedelta(minutes=step_def.get("duration_minutes", 30)),
                    inputs=step_def.get("inputs", {}),
                    outputs=step_def.get("outputs", {}),
                    validation_rules=step_def.get("validation_rules", {}),
                    retry_policy=step_def.get("retry_policy", {}),
                )
                workflow_steps.append(step)

            self.active_workflows[workflow_id] = workflow_steps

            # 启动协作会话
            self.framework.start_collaboration_session(
                task_id, participating_agents, template.strategy.value
            )

            # 初始化工作流执行
            self._execute_workflow(workflow_id, template, context)

            logger.info(f"协作工作流 {workflow_id} 已启动,使用模板 {template.name}")
            return workflow_id

        except Exception as e:
            logger.error(f"启动协作工作流失败: {e}")
            return None

    def _select_agents_for_step(
        self, step_def: dict[str, Any], available_agents: list[str], agent_roles: dict[str, str]
    ) -> list[str]:
        """为工作流步骤选择智能体"""
        step_agents = []

        assigned_role = step_def.get("assigned_role")
        if assigned_role:
            # 根据角色选择智能体
            for agent_id in available_agents:
                agent = self.framework.agents.get(agent_id)
                if agent and agent.metadata.get("role") == assigned_role:
                    step_agents.append(agent_id)
        else:
            # 使用所有可用智能体
            step_agents = available_agents.copy()

        return step_agents

    async def _execute_workflow(
        self, workflow_id: str, template: CollaborationTemplate, context: dict[str, Any]
    ):
        """执行工作流"""
        try:
            workflow_steps = self.active_workflows[workflow_id]

            if template.strategy == CollaborationStrategy.SEQUENTIAL:
                await self._execute_sequential_workflow(workflow_steps)
            elif template.strategy == CollaborationStrategy.PARALLEL:
                await self._execute_parallel_workflow(workflow_steps)
            elif template.strategy == CollaborationStrategy.HIERARCHICAL:
                await self._execute_hierarchical_workflow(workflow_steps)
            elif template.strategy == CollaborationStrategy.PIPELINE:
                await self._execute_pipeline_workflow(workflow_steps)

            logger.info(f"工作流 {workflow_id} 执行完成")

        except Exception as e:
            logger.error(f"执行工作流失败: {e}")

    async def _execute_sequential_workflow(self, steps: list[WorkflowStep]):
        """执行串行工作流"""
        for step in steps:
            await self._execute_workflow_step(step)
            if step.status != "completed":
                logger.error(f"工作流步骤 {step.step_id} 执行失败")
                break

    async def _execute_parallel_workflow(self, steps: list[WorkflowStep]):
        """执行并行工作流"""
        parallel_steps = []
        for step in steps:
            if not step.dependencies:  # 无依赖的步骤可以并行执行
                parallel_steps.append(step)

        # 并行执行无依赖步骤
        tasks = [self._execute_workflow_step(step) for step in parallel_steps]
        await asyncio.gather(*tasks, return_exceptions=True)

        # 处理有依赖的步骤
        for step in steps:
            if step.dependencies and step.status == "pending":
                await self._execute_workflow_step(step)

    async def _execute_hierarchical_workflow(self, steps: list[WorkflowStep]):
        """执行层次工作流"""
        coordinator_steps = [s for s in steps if "coordinator" in s.assigned_agents]
        worker_steps = [s for s in steps if "worker" in s.assigned_agents]

        # 先执行协调者步骤
        for step in coordinator_steps:
            await self._execute_workflow_step(step)

        # 再执行工作者步骤
        for step in worker_steps:
            await self._execute_workflow_step(step)

    async def _execute_pipeline_workflow(self, steps: list[WorkflowStep]):
        """执行流水线工作流"""
        for i, step in enumerate(steps):
            await self._execute_workflow_step(step)
            if i < len(steps) - 1:
                # 将当前步骤的输出传递给下一步
                next_step = steps[i + 1]
                next_step.inputs.update(step.outputs)

    async def _execute_workflow_step(self, step: WorkflowStep) -> bool:
        """执行工作流步骤"""
        try:
            step.status = "in_progress"
            logger.info(f"开始执行工作流步骤: {step.name}")

            # 发送步骤执行消息给相关智能体
            execution_message = Message(
                sender_id="collaboration_manager",
                receiver_id="",
                message_type=MessageType.TASK_REQUEST,
                content={
                    "action": "execute_workflow_step",
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "assigned_agents": step.assigned_agents,
                    "inputs": step.inputs,
                    "validation_rules": step.validation_rules,
                },
            )

            self.framework.message_broker.publish(execution_message)

            # 等待步骤完成(这里简化处理)
            await asyncio.sleep(1)  # 实际应该等待智能体的完成确认

            step.status = "completed"
            logger.info(f"工作流步骤 {step.name} 执行完成")
            return True

        except Exception as e:
            step.status = "failed"
            logger.error(f"执行工作流步骤 {step.name} 失败: {e}")
            return False

    def detect_conflicts(self) -> list[Conflict]:
        """检测冲突"""
        detected_conflicts = []

        # 检测资源冲突
        resource_conflicts = self._detect_resource_conflicts()
        detected_conflicts.extend(resource_conflicts)

        # 检测任务分配冲突
        task_conflicts = self._detect_task_conflicts()
        detected_conflicts.extend(task_conflicts)

        # 检测时间冲突
        time_conflicts = self._detect_time_conflicts()
        detected_conflicts.extend(time_conflicts)

        self.conflicts.extend(detected_conflicts)
        return detected_conflicts

    def _detect_resource_conflicts(self) -> list[Conflict]:
        """检测资源冲突"""
        conflicts = []

        # 检查同时请求同一资源的多个智能体
        resource_requests = defaultdict(list)
        for allocation in self.framework.resource_manager.allocations.values():
            resource_id = allocation["resource_id"]
            resource_requests[resource_id].append(allocation)

        for resource_id, requests in resource_requests.items():
            if len(requests) > 1:
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type="resource_conflict",
                    involved_agents=[req["agent_id"] for req in requests],
                    conflicting_resources=[resource_id],
                    conflict_description=f"多个智能体同时请求资源 {resource_id}",
                    detected_at=datetime.now(),
                    severity=7,
                )
                conflicts.append(conflict)

        return conflicts

    def _detect_task_conflicts(self) -> list[Conflict]:
        """检测任务分配冲突"""
        conflicts = []

        # 检查智能体过载
        for agent_id, agent in self.framework.agents.items():
            if agent.current_load > agent.max_load:
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type="agent_overload",
                    involved_agents=[agent_id],
                    conflicting_resources=[],
                    conflict_description=f"智能体 {agent_id} 过载",
                    detected_at=datetime.now(),
                    severity=5,
                )
                conflicts.append(conflict)

        return conflicts

    def _detect_time_conflicts(self) -> list[Conflict]:
        """检测时间冲突"""
        conflicts = []

        # 检查任务截止时间冲突
        for task in self.framework.tasks.values():
            if task.deadline and datetime.now() > task.deadline:
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type="deadline_miss",
                    involved_agents=task.assigned_agents,
                    conflicting_resources=[task.id],
                    conflict_description=f"任务 {task.id} 错过截止时间",
                    detected_at=datetime.now(),
                    severity=8,
                )
                conflicts.append(conflict)

        return conflicts

    def resolve_conflicts(self) -> bool:
        """解决冲突"""
        try:
            for conflict in self.conflicts:
                if conflict.resolved_at is None:
                    resolved = self._resolve_single_conflict(conflict)
                    if resolved:
                        conflict.resolved_at = datetime.now()

            # 移除已解决的冲突
            self.conflicts = [c for c in self.conflicts if c.resolved_at is None]

            logger.info(f"冲突解决完成,剩余 {len(self.conflicts)} 个未解决冲突")
            return True

        except Exception as e:
            logger.error(f"解决冲突失败: {e}")
            return False

    def _resolve_single_conflict(self, conflict: Conflict) -> bool:
        """解决单个冲突"""
        try:
            resolution_strategy = (
                conflict.resolution_strategy or ConflictResolutionStrategy.PRIORITY_BASED
            )

            if conflict.conflict_type == "resource_conflict":
                return self._resolve_resource_conflict(conflict, resolution_strategy)
            elif conflict.conflict_type == "agent_overload":
                return self._resolve_agent_overload(conflict, resolution_strategy)
            elif conflict.conflict_type == "deadline_miss":
                return self._resolve_deadline_miss(conflict, resolution_strategy)

            return False

        except Exception as e:
            logger.error(f"解决冲突 {conflict.conflict_id} 失败: {e}")
            return False

    def _resolve_resource_conflict(
        self, conflict: Conflict, strategy: ConflictResolutionStrategy
    ) -> bool:
        """解决资源冲突"""
        if strategy == ConflictResolutionStrategy.PRIORITY_BASED:
            # 基于优先级解决:保留高优先级智能体的资源分配
            involved_agents = conflict.involved_agents
            if not involved_agents:
                return False

            # 按智能体优先级排序
            agent_priorities = []
            for agent_id in involved_agents:
                agent = self.framework.agents.get(agent_id)
                priority = agent.metadata.get("priority", 0) if agent else 0
                agent_priorities.append((agent_id, priority))

            agent_priorities.sort(key=lambda x: x[1], reverse=True)

            # 保留最高优先级智能体的资源,释放其他智能体的资源
            for i, (agent_id, _) in enumerate(agent_priorities):
                if i > 0:  # 释放除最高优先级外的所有资源
                    allocations_to_release = [
                        alloc_id
                        for alloc_id, alloc in self.framework.resource_manager.allocations.items()
                        if alloc["agent_id"] == agent_id
                    ]
                    for alloc_id in allocations_to_release:
                        self.framework.resource_manager.release_resource(alloc_id)

            conflict.resolution_details = {
                "strategy": strategy.value,
                "retained_agent": agent_priorities[0][0] if agent_priorities else None,
                "released_agents": [agent_id for agent_id, _ in agent_priorities[1:]],
            }
            return True

        return False

    def _resolve_agent_overload(
        self, conflict: Conflict, strategy: ConflictResolutionStrategy
    ) -> bool:
        """解决智能体过载冲突"""
        agent_id = conflict.involved_agents[0] if conflict.involved_agents else None
        if not agent_id:
            return False

        agent = self.framework.agents.get(agent_id)
        if not agent:
            return False

        # 降低智能体负载
        if strategy == ConflictResolutionStrategy.LOAD_BALANCING:
            # 重新分配部分任务给其他智能体
            tasks_to_reassign = []
            for task_id, task in self.framework.tasks.items():
                if agent_id in task.assigned_agents and task.status == TaskStatus.ASSIGNED:
                    tasks_to_reassign.append(task_id)
                    if len(tasks_to_reassign) >= 2:  # 重新分配2个任务
                        break

            # 尝试重新分配任务
            for task_id in tasks_to_reassign:
                task = self.framework.tasks.get(task_id)
                if task:
                    # 移除当前智能体
                    task.assigned_agents.remove(agent_id)
                    agent.current_load -= 1

                    # 寻找其他合适的智能体
                    suitable_agents = self.framework.find_suitable_agents(
                        {"capabilities": task.required_capabilities}
                    )

                    if suitable_agents:
                        new_agent_id = suitable_agents[0][0]
                        task.assign_agent(new_agent_id)

                        new_agent = self.framework.agents.get(new_agent_id)
                        if new_agent:
                            new_agent.current_load += 1

            conflict.resolution_details = {
                "strategy": strategy.value,
                "reassigned_tasks": tasks_to_reassign,
            }
            return True

        return False

    def _resolve_deadline_miss(
        self, conflict: Conflict, strategy: ConflictResolutionStrategy
    ) -> bool:
        """解决截止时间冲突"""
        task_id = conflict.conflicting_resources[0] if conflict.conflicting_resources else None
        if not task_id:
            return False

        task = self.framework.tasks.get(task_id)
        if not task:
            return False

        # 延长截止时间或调整优先级
        if strategy == ConflictResolutionStrategy.PRIORITY_BASED:
            # 提高任务优先级
            task.priority = Priority.URGENT

            # 通知相关智能体提高处理优先级
            priority_message = Message(
                sender_id="collaboration_manager",
                receiver_id="",
                message_type=MessageType.COORDINATION,
                content={
                    "action": "priority_escalation",
                    "task_id": task_id,
                    "new_priority": Priority.URGENT.value,
                },
            )
            self.framework.message_broker.publish(priority_message)

        conflict.resolution_details = {"strategy": strategy.value, "task_priority_updated": True}
        return True

    def get_collaboration_metrics(self) -> dict[str, Any]:
        """获取协作指标"""
        total_workflows = len(self.active_workflows)
        completed_steps = sum(
            1
            for workflow in self.active_workflows.values()
            for step in workflow
            if step.status == "completed"
        )
        total_steps = sum(len(workflow) for workflow in self.active_workflows.values())

        return {
            "active_workflows": total_workflows,
            "workflow_completion_rate": completed_steps / max(total_steps, 1),
            "active_conflicts": len(self.conflicts),
            "registered_templates": len(self.templates),
            "framework_status": self.framework.get_framework_status(),
        }
