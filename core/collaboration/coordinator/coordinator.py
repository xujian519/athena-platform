"""
Coordinator核心实现

提供多Agent协调调度的主要功能。
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging

from .types import (
    AgentInfo,
    AgentStatus,
    TaskInfo,
    ConflictInfo,
    SchedulingResult,
    ConflictType,
    TaskPriority,
)


logger = logging.getLogger(__name__)


class Coordinator:
    """
    协调器核心类

    负责管理多个Agent的协调调度，包括：
    - Agent注册和生命周期管理
    - 任务分发和调度
    - 冲突检测和解决
    - 状态同步
    """

    def __init__(self, coordinator_id: str = "coordinator_main"):
        """初始化协调器"""
        self.coordinator_id = coordinator_id
        self._agents: dict[str, AgentInfo] = {}
        self._tasks: dict[str, TaskInfo] = {}
        self._completed_tasks: set[str] = set()
        self._pending_tasks: list[str] = []
        self._conflicts: list[ConflictingInfo] = []
        self._running = False

        logger.info(f"Coordinator {coordinator_id} initialized")

    async def start(self) -> None:
        """启动协调器"""
        if self._running:
            logger.warning(f"Coordinator {self.coordinator_id} is already running")
            return

        self._running = True
        logger.info(f"Coordinator {self.coordinator_id} started")

    async def stop(self) -> None:
        """停止协调器"""
        if not self._running:
            logger.warning(f"Coordinator {self.coordinator_id} is not running")
            return

        self._running = False
        logger.info(f"Coordinator {self.coordinator_id} stopped")

    def register_agent(self, agent_info: AgentInfo) -> bool:
        """
        注册Agent

        Args:
            agent_info: Agent信息

        Returns:
            注册是否成功
        """
        if agent_info.agent_id in self._agents:
            logger.warning(f"Agent {agent_info.agent_id} already registered")
            return False

        self._agents[agent_info.agent_id] = agent_info
        logger.info(f"Agent {agent_info.agent_id} registered")
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """
        注销Agent

        Args:
            agent_id: Agent ID

        Returns:
            注销是否成功
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent {agent_id} not found")
            return False

        del self._agents[agent_id]
        logger.info(f"Agent {agent_id} unregistered")
        return True

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """获取Agent信息"""
        return self._agents.get(agent_id)

    def list_agents(self, status: Optional[AgentStatus] = None) -> list[AgentInfo]:
        """
        列出Agent

        Args:
            status: 可选的状态过滤

        Returns:
            Agent列表
        """
        agents = list(self._agents.values())
        if status:
            agents = [a for a in agents if a.status == status]
        return agents

    async def submit_task(self, task_info: TaskInfo) -> SchedulingResult:
        """
        提交任务

        Args:
            task_info: 任务信息

        Returns:
            调度结果
        """
        if not self._running:
            return SchedulingResult(
                success=False,
                task_id=task_info.task_id,
                reason="Coordinator is not running"
            )

        # 检查任务是否已存在
        if task_info.task_id in self._tasks:
            return SchedulingResult(
                success=False,
                task_id=task_info.task_id,
                reason="Task already exists"
            )

        # 添加到任务队列
        self._tasks[task_info.task_id] = task_info
        self._pending_tasks.append(task_info.task_id)

        logger.info(f"Task {task_info.task_id} submitted")

        # 尝试立即调度
        return await self._schedule_task(task_info)

    async def _schedule_task(self, task_info: TaskInfo) -> SchedulingResult:
        """
        调度任务到合适的Agent

        Args:
            task_info: 任务信息

        Returns:
            调度结果
        """
        # 检查依赖是否满足
        if not task_info.is_ready(self._completed_tasks):
            return SchedulingResult(
                success=False,
                task_id=task_info.task_id,
                reason="Task dependencies not satisfied"
            )

        # 查找可用的Agent
        available_agents = [
            agent for agent in self._agents.values()
            if agent.is_available() and agent.can_handle_task(task_info.task_type)
        ]

        if not available_agents:
            return SchedulingResult(
                success=False,
                task_id=task_info.task_id,
                reason="No available agents"
            )

        # TODO: 实现更智能的调度策略
        # 目前简单选择第一个可用Agent
        selected_agent = available_agents[0]

        # 分配任务
        task_info.assigned_to = selected_agent.agent_id
        task_info.status = "assigned"
        selected_agent.current_tasks.append(task_info.task_id)

        logger.info(
            f"Task {task_info.task_id} assigned to agent {selected_agent.agent_id}"
        )

        return SchedulingResult(
            success=True,
            task_id=task_info.task_id,
            assigned_agent=selected_agent.agent_id,
            reason="Task scheduled successfully"
        )

    async def complete_task(self, task_id: str, agent_id: str, result: any = None) -> bool:
        """
        完成任务

        Args:
            task_id: 任务ID
            agent_id: Agent ID
            result: 任务结果

        Returns:
            是否成功
        """
        if task_id not in self._tasks:
            logger.warning(f"Task {task_id} not found")
            return False

        task_info = self._tasks[task_id]
        task_info.status = "completed"

        # 从Agent的任务列表中移除
        agent = self._agents.get(agent_id)
        if agent and task_id in agent.current_tasks:
            agent.current_tasks.remove(task_id)

        # 添加到已完成集合
        self._completed_tasks.add(task_id)

        logger.info(f"Task {task_id} completed by agent {agent_id}")

        # 触发依赖此任务的其他任务
        await self._trigger_dependent_tasks(task_id)

        return True

    async def _trigger_dependent_tasks(self, completed_task_id: str) -> None:
        """触发依赖已完成任务的其他任务"""
        for task_id, task_info in self._tasks.items():
            if task_info.status == "pending" and task_info.is_ready(self._completed_tasks):
                logger.info(f"Triggering task {task_id} (dependency {completed_task_id} completed)")
                await self._schedule_task(task_info)

    def get_statistics(self) -> dict[str, any]:
        """获取统计信息"""
        return {
            "coordinator_id": self.coordinator_id,
            "total_agents": len(self._agents),
            "total_tasks": len(self._tasks),
            "completed_tasks": len(self._completed_tasks),
            "pending_tasks": len(self._pending_tasks),
            "running": self._running,
        }
