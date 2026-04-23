#!/usr/bin/env python3
from __future__ import annotations

"""
Swarm Agent实现
Swarm Agent Implementation

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

实现Swarm群体中的个体Agent。
"""

import logging
from typing import Any

from .swarm_models import AgentState, SwarmRole

logger = logging.getLogger(__name__)


class SwarmAgent:
    """
    Swarm个体Agent

    代表群体中的一个成员，具有角色、能力和状态。
    """

    def __init__(
        self,
        agent_id: str,
        capabilities: list[str],
        initial_role: SwarmRole = SwarmRole.WORKER,
        metadata: dict[str, Any] | None = None,
    ):
        """
        初始化Swarm Agent

        Args:
            agent_id: Agent唯一标识
            capabilities: 能力列表
            initial_role: 初始角色
            metadata: 元数据
        """
        self.agent_id = agent_id
        self.capabilities = capabilities.copy()
        self.role = initial_role
        self.role_history: list[SwarmRole] = [initial_role]
        self.neighbors: list[str] = []
        self.is_active: bool = True
        self.current_load: float = 0.0
        self.metadata = metadata or {}

        # 统计信息
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.reputation_score: float = 1.0

        logger.debug(f"创建Swarm Agent: {agent_id}, 角色: {initial_role.value}")

    def change_role(self, new_role: SwarmRole) -> None:
        """
        更改角色

        Args:
            new_role: 新角色
        """
        if self.role == new_role:
            return

        old_role = self.role
        self.role = new_role
        self.role_history.append(new_role)

        logger.info(
            f"Agent {self.agent_id} 角色变更: {old_role.value} -> {new_role.value}"
        )

    def add_neighbor(self, neighbor_id: str) -> None:
        """
        添加邻居

        Args:
            neighbor_id: 邻居Agent ID
        """
        if neighbor_id not in self.neighbors:
            self.neighbors.append(neighbor_id)
            logger.debug(f"Agent {self.agent_id} 添加邻居: {neighbor_id}")

    def remove_neighbor(self, neighbor_id: str) -> None:
        """
        移除邻居

        Args:
            neighbor_id: 邻居Agent ID
        """
        if neighbor_id in self.neighbors:
            self.neighbors.remove(neighbor_id)
            logger.debug(f"Agent {self.agent_id} 移除邻居: {neighbor_id}")

    def can_handle_capability(self, capability: str) -> bool:
        """
        检查是否具有某能力

        Args:
            capability: 能力名称

        Returns:
            是否具有该能力
        """
        return capability in self.capabilities

    def can_handle_task(self, task_requirements: dict[str, Any]) -> bool:
        """
        检查是否能处理任务

        Args:
            task_requirements: 任务需求（包含required_capabilities等）

        Returns:
            是否能处理
        """
        if not self.is_active:
            return False

        if not self.is_available():
            return False

        required_capabilities = task_requirements.get("required_capabilities", [])
        for capability in required_capabilities:
            if not self.can_handle_capability(capability):
                return False

        return True

    def is_available(self) -> bool:
        """
        检查是否可用

        Returns:
            是否可用（活跃且负载不过高）
        """
        return self.is_active and self.current_load < 0.8

    def update_load(self, load: float) -> None:
        """
        更新负载

        Args:
            load: 负载值 (0.0 - 1.0)
        """
        self.current_load = max(0.0, min(1.0, load))

    def increment_tasks_completed(self) -> None:
        """增加完成任务数"""
        self.tasks_completed += 1
        self._update_reputation()

    def increment_tasks_failed(self) -> None:
        """增加失败任务数"""
        self.tasks_failed += 1
        self._update_reputation()

    def _update_reputation(self) -> None:
        """更新声誉评分"""
        total = self.tasks_completed + self.tasks_failed
        if total > 0:
            success_rate = self.tasks_completed / total
            # 声誉评分 = 成功率的加权，历史表现影响较小
            self.reputation_score = 0.3 * self.reputation_score + 0.7 * success_rate

    def get_state(self) -> AgentState:
        """
        获取Agent状态

        Returns:
            AgentState对象
        """
        from datetime import datetime

        return AgentState(
            agent_id=self.agent_id,
            role=self.role,
            status="active" if self.is_active else "inactive",
            current_load=self.current_load,
            capabilities=self.capabilities.copy(),
            neighbors=self.neighbors.copy(),
            last_heartbeat=datetime.now(),
            tasks_completed=self.tasks_completed,
            tasks_failed=self.tasks_failed,
            reputation_score=self.reputation_score,
            metadata=self.metadata.copy(),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典

        Returns:
            Agent字典表示
        """
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "neighbors": self.neighbors,
            "is_active": self.is_active,
            "current_load": self.current_load,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "reputation_score": self.reputation_score,
            "role_history": [r.value for r in self.role_history],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SwarmAgent":
        """
        从字典创建SwarmAgent

        Args:
            data: Agent字典

        Returns:
            SwarmAgent实例
        """
        agent = cls(
            agent_id=data["agent_id"],
            capabilities=data["capabilities"],
            initial_role=SwarmRole(data["role"]),
            metadata=data.get("metadata", {}),
        )

        agent.neighbors = data.get("neighbors", [])
        agent.is_active = data.get("is_active", True)
        agent.current_load = data.get("current_load", 0.0)
        agent.tasks_completed = data.get("tasks_completed", 0)
        agent.tasks_failed = data.get("tasks_failed", 0)
        agent.reputation_score = data.get("reputation_score", 1.0)

        # 恢复角色历史
        role_history = data.get("role_history", [])
        agent.role_history = [SwarmRole(r) for r in role_history]

        return agent

    def __repr__(self) -> str:
        return f"SwarmAgent(id={self.agent_id}, role={self.role.value}, load={self.current_load:.2f})"
