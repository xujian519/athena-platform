#!/usr/bin/env python3
from __future__ import annotations
"""
Agent注册发现系统
Agent Registry and Discovery System

负责Agent的注册、发现和管理
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent类型枚举"""

    SEARCH = "search"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    COORDINATOR = "coordinator"
    GENERAL = "general"


class AgentStatus(Enum):
    """Agent状态枚举"""

    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentInfo:
    """Agent信息"""

    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    current_task_id: Optional[str] = None
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat,
            "current_task_id": self.current_task_id,
            "performance_metrics": self.performance_metrics,
            "config": self.config,
        }


class AgentRegistry:
    """Agent注册中心"""

    def __init__(self):
        self.agents: dict[str, AgentInfo] = {}
        self.agent_groups: dict[AgentType, list[str]] = {agent_type: [] for agent_type in AgentType}
        self.heartbeat_interval = 30  # 心跳间隔(秒)
        self.heartbeat_timeout = 90  # 心跳超时(秒)

    async def register_agent(self, agent_info: AgentInfo) -> bool:
        """
        注册Agent

        Args:
            agent_info: Agent信息

        Returns:
            bool: 注册是否成功
        """
        try:
            # 检查Agent是否已存在
            if agent_info.agent_id in self.agents:
                logger.warning(f"⚠️ Agent {agent_info.agent_id} 已存在,更新信息")
                # 保留性能指标
                old_metrics = self.agents[agent_info.agent_id].performance_metrics
                agent_info.performance_metrics.update(old_metrics)

            # 注册Agent
            self.agents[agent_info.agent_id] = agent_info

            # 添加到分组
            if agent_info.agent_type not in self.agent_groups:
                self.agent_groups[agent_info.agent_type] = []

            if agent_info.agent_id not in self.agent_groups[agent_info.agent_type]:
                self.agent_groups[agent_info.agent_type].append(agent_info.agent_id)

            logger.info(f"✅ Agent {agent_info.name} ({agent_info.agent_id}) 注册成功")
            return True

        except Exception as e:
            logger.error(f"❌ Agent注册失败: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """
        注销Agent

        Args:
            agent_id: Agent ID

        Returns:
            bool: 注销是否成功
        """
        try:
            if agent_id not in self.agents:
                logger.warning(f"⚠️ Agent {agent_id} 不存在")
                return False

            agent_info = self.agents[agent_id]

            # 从注册中心移除
            del self.agents[agent_id]

            # 从分组移除
            if agent_info.agent_type in self.agent_groups:
                if agent_id in self.agent_groups[agent_info.agent_type]:
                    self.agent_groups[agent_info.agent_type].remove(agent_id)

            logger.info(f"✅ Agent {agent_id} 注销成功")
            return True

        except Exception as e:
            logger.error(f"❌ Agent注销失败: {e}")
            return False

    def get_agent_info(self, agent_id: str) -> AgentInfo | None:
        """
        获取Agent信息

        Args:
            agent_id: Agent ID

        Returns:
            AgentInfo: Agent信息,不存在返回None
        """
        return self.agents.get(agent_id)

    def find_agents_by_type(
        self, agent_type: AgentType, status: AgentStatus | None = None
    ) -> list[AgentInfo]:
        """
        根据类型查找Agent

        Args:
            agent_type: Agent类型
            status: Agent状态过滤

        Returns:
            list[AgentInfo]: 匹配的Agent列表
        """
        agents = []
        agent_ids = self.agent_groups.get(agent_type, [])

        for agent_id in agent_ids:
            agent_info = self.agents.get(agent_id)
            if agent_info and (status is None or agent_info.status == status):
                agents.append(agent_info)

        return agents

    def find_available_agents(self, agent_type: AgentType | None = None) -> list[AgentInfo]:
        """
        查找可用的Agent

        Args:
            agent_type: Agent类型过滤

        Returns:
            list[AgentInfo]: 可用的Agent列表
        """
        available_agents = []

        for agent_info in self.agents.values():
            # 状态过滤
            if agent_info.status != AgentStatus.IDLE:
                continue

            # 类型过滤
            if agent_type and agent_info.agent_type != agent_type:
                continue

            available_agents.append(agent_info)

        return available_agents

    def get_best_agent(
        self, agent_type: AgentType, capabilities: Optional[list[str]] = None
    ) -> AgentInfo | None:
        """
        获取最适合的Agent

        Args:
            agent_type: Agent类型
            capabilities: 能力需求

        Returns:
            AgentInfo: 最适合的Agent,无可用Agent返回None
        """
        candidates = self.find_available_agents(agent_type)

        if not candidates:
            return None

        # 如果有能力需求,进行能力匹配
        if capabilities:
            best_agent = None
            best_score = -1

            for agent in candidates:
                # 计算能力匹配得分
                score = 0
                for capability in capabilities:
                    if capability in agent.capabilities:
                        score += 1

                # 考虑性能指标
                if "success_rate" in agent.performance_metrics:
                    score *= agent.performance_metrics["success_rate"]

                if score > best_score:
                    best_score = score
                    best_agent = agent

            return best_agent

        # 无能力需求,返回第一个可用Agent
        return candidates[0]

    async def update_agent_status(
        self, agent_id: str, status: AgentStatus, task_id: Optional[str] = None
    ):
        """
        更新Agent状态

        Args:
            agent_id: Agent ID
            status: 新状态
            task_id: 当前任务ID
        """
        if agent_id in self.agents:
            agent_info = self.agents[agent_id]
            agent_info.status = status
            agent_info.current_task_id = task_id
            agent_info.last_heartbeat = datetime.now().isoformat()

    async def update_heartbeat(self, agent_id: str):
        """
        更新Agent心跳

        Args:
            agent_id: Agent ID
        """
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = datetime.now().isoformat()

    async def update_performance_metrics(self, agent_id: str, metrics: dict[str, Any]):
        """
        更新Agent性能指标

        Args:
            agent_id: Agent ID
            metrics: 性能指标
        """
        if agent_id in self.agents:
            self.agents[agent_id].performance_metrics.update(metrics)

    async def check_agent_health(self):
        """检查Agent健康状态"""
        current_time = datetime.now()
        offline_agents = []

        for agent_id, agent_info in self.agents.items():
            # 检查心跳超时
            try:
                last_heartbeat = datetime.fromisoformat(agent_info.last_heartbeat)
                time_diff = (current_time - last_heartbeat).total_seconds()

                if time_diff > self.heartbeat_timeout:
                    # 心跳超时,标记为离线
                    if agent_info.status != AgentStatus.OFFLINE:
                        logger.warning(f"⚠️ Agent {agent_id} 心跳超时,标记为离线")
                        agent_info.status = AgentStatus.OFFLINE
                        offline_agents.append(agent_id)

            except Exception as e:
                logger.error(f"❌ 检查Agent {agent_id} 健康状态失败: {e}")

        return offline_agents

    def get_registry_stats(self) -> dict[str, Any]:
        """获取注册中心统计信息"""
        stats: dict[str, Any] = {
            "total_agents": len(self.agents),
            "agents_by_type": {},
            "agents_by_status": {},
        }

        # 按类型统计
        for agent_type, agent_ids in self.agent_groups.items():
            stats["agents_by_type"][agent_type.value] = len(agent_ids)  # type: ignore[index]

        # 按状态统计
        for agent_info in self.agents.values():
            status = agent_info.status.value
            stats["agents_by_status"][status] = stats["agents_by_status"].get(status, 0) + 1  # type: ignore[index]

        return stats

    def list_all_agents(self) -> list[dict[str, Any]]:
        """列出所有Agent信息"""
        return [agent_info.to_dict() for agent_info in self.agents.values()]


# 全局Agent注册中心实例
_agent_registry = None


def get_agent_registry() -> AgentRegistry:
    """获取全局Agent注册中心实例"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
