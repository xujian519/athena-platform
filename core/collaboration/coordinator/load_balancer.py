"""
负载均衡器实现

负责Agent间的负载均衡。
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from .types import AgentInfo, TaskInfo, AgentStatus


logger = logging.getLogger(__name__)


class LoadBalancer:
    """
    负载均衡器

    实现多种负载均衡策略。
    """

    def __init__(self, strategy: str = "least_loaded"):
        """
        初始化负载均衡器

        Args:
            strategy: 负载均衡策略
                - "round_robin": 轮询
                - "least_loaded": 最少负载（默认）
                - "capability_based": 基于能力
        """
        self.strategy = strategy
        self._round_robin_index = 0
        self._agent_stats: dict[str, dict] = {}  # Agent统计信息

        logger.info(f"LoadBalancer initialized with strategy: {strategy}")

    def select_agent(
        self,
        task: TaskInfo,
        available_agents: list[AgentInfo]
    ) -> Optional[AgentInfo]:
        """
        选择最适合的Agent

        Args:
            task: 任务信息
            available_agents: 可用Agent列表

        Returns:
            选中的Agent，如果没有合适的则返回None
        """
        if not available_agents:
            logger.warning("No available agents for task")
            return None

        # 根据策略选择Agent
        if self.strategy == "round_robin":
            return self._round_robin_select(available_agents)
        elif self.strategy == "least_loaded":
            return self._least_loaded_select(available_agents)
        elif self.strategy == "capability_based":
            return self._capability_based_select(task, available_agents)
        else:
            logger.warning(f"Unknown strategy: {self.strategy}, using least_loaded")
            return self._least_loaded_select(available_agents)

    def _round_robin_select(self, agents: list[AgentInfo]) -> AgentInfo:
        """轮询选择"""
        agent = agents[self._round_robin_index % len(agents)]
        self._round_robin_index += 1
        return agent

    def _least_loaded_select(self, agents: list[AgentInfo]) -> AgentInfo:
        """选择负载最少的Agent"""
        # 按当前任务数排序
        sorted_agents = sorted(agents, key=lambda a: len(a.current_tasks))
        return sorted_agents[0]

    def _capability_based_select(
        self,
        task: TaskInfo,
        agents: list[AgentInfo]
    ) -> Optional[AgentInfo]:
        """
        基于能力选择Agent

        优先选择具备任务所需能力的Agent
        """
        # 筛选具备所需能力的Agent
        capable_agents = []
        for agent in agents:
            if self._agent_can_handle_task(agent, task):
                capable_agents.append(agent)

        if not capable_agents:
            logger.warning(f"No agents capable of handling task {task.task_id}")
            return None

        # 在具备能力的Agent中选择负载最少的
        return self._least_loaded_select(capable_agents)

    def _agent_can_handle_task(self, agent: AgentInfo, task: TaskInfo) -> bool:
        """检查Agent是否能处理任务"""
        # 检查能力匹配
        if task.required_capabilities:
            has_capabilities = all(
                cap in agent.capabilities for cap in task.required_capabilities
            )
            if not has_capabilities:
                return False

        # 检查Agent状态
        return agent.status == AgentStatus.IDLE

    async def update_agent_performance(
        self,
        agent_id: str,
        task_id: str,
        execution_time: float,
        success: bool
    ) -> None:
        """
        更新Agent性能统计

        Args:
            agent_id: Agent ID
            task_id: 任务ID
            execution_time: 执行时间（秒）
            success: 是否成功
        """
        if agent_id not in self._agent_stats:
            self._agent_stats[agent_id] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "last_task_time": None,
            }

        stats = self._agent_stats[agent_id]
        stats["total_tasks"] += 1
        stats["total_execution_time"] += execution_time

        if success:
            stats["successful_tasks"] += 1
        else:
            stats["failed_tasks"] += 1

        stats["average_execution_time"] = (
            stats["total_execution_time"] / stats["total_tasks"]
        )
        stats["last_task_time"] = datetime.now()

        logger.debug(f"Agent {agent_id} performance updated")

    def get_agent_stats(self, agent_id: str) -> Optional[dict]:
        """获取Agent统计信息"""
        return self._agent_stats.get(agent_id)

    def get_all_stats(self) -> dict[str, dict]:
        """获取所有Agent统计信息"""
        return self._agent_stats.copy()
