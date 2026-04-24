"""
Agent协作模块适配器

兼容: core/agent_collaboration/agent_registry.py

重定向所有调用到统一注册中心，保持API完全兼容。
"""

import logging
from typing import Any, Optional

from core.registry_center.agent_registry import (
    AgentInfo,
    AgentStatus,
    AgentType,
    UnifiedAgentRegistry,
    get_agent_registry,
)

logger = logging.getLogger(__name__)


# 导出原有类型
__all__ = ["AgentType", "AgentStatus", "AgentInfo", "AgentRegistry"]


class AgentRegistry:
    """
    Agent注册中心（兼容层）

    重定向到UnifiedAgentRegistry，保持原有API完全兼容。

    原模块: core/agent_collaboration/agent_registry.py
    """

    def __init__(self):
        """初始化 - 使用统一注册中心"""
        self._impl = get_agent_registry()

    async def register_agent(self, agent_info: AgentInfo) -> bool:
        """
        注册Agent

        Args:
            agent_info: Agent信息

        Returns:
            bool: 注册是否成功
        """
        return self._impl.register_agent(agent_info)

    async def unregister_agent(self, agent_id: str) -> bool:
        """
        注销Agent

        Args:
            agent_id: Agent ID

        Returns:
            bool: 注销是否成功
        """
        return self._impl.unregister_agent(agent_id)

    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """
        获取Agent信息

        Args:
            agent_id: Agent ID

        Returns:
            AgentInfo: Agent信息，不存在返回None
        """
        return self._impl.get_agent_info(agent_id)

    def find_agents_by_type(
        self, agent_type: AgentType, status: Optional[AgentStatus] = None
    ) -> list[AgentInfo]:
        """
        根据类型查找Agent

        Args:
            agent_type: Agent类型
            status: Agent状态过滤

        Returns:
            list[AgentInfo]: 匹配的Agent列表
        """
        return self._impl.find_agents_by_type(agent_type, status)

    def find_available_agents(self, agent_type: Optional[AgentType] = None) -> list[AgentInfo]:
        """
        查找可用的Agent

        Args:
            agent_type: Agent类型过滤

        Returns:
            list[AgentInfo]: 可用的Agent列表
        """
        return self._impl.find_available_agents(agent_type)

    def get_best_agent(
        self, agent_type: AgentType, capabilities: Optional[list[str]] = None
    ) -> Optional[AgentInfo]:
        """
        获取最适合的Agent

        Args:
            agent_type: Agent类型
            capabilities: 能力需求

        Returns:
            AgentInfo: 最适合的Agent，无可用Agent返回None
        """
        return self._impl.get_best_agent(agent_type, capabilities)

    async def update_agent_status(
        self, agent_id: str, status: AgentStatus, task_id: Optional[str] = None
    ) -> None:
        """
        更新Agent状态

        Args:
            agent_id: Agent ID
            status: 新状态
            task_id: 当前任务ID
        """
        await self._impl.update_agent_status(agent_id, status, task_id)

    async def update_heartbeat(self, agent_id: str) -> None:
        """
        更新Agent心跳

        Args:
            agent_id: Agent ID
        """
        await self._impl.update_heartbeat(agent_id)

    async def update_performance_metrics(self, agent_id: str, metrics: dict[str, Any]) -> None:
        """
        更新Agent性能指标

        Args:
            agent_id: Agent ID
            metrics: 性能指标
        """
        await self._impl.update_performance_metrics(agent_id, metrics)

    async def check_agent_health(self) -> list[str]:
        """
        检查Agent健康状态

        Returns:
            不健康的Agent ID列表
        """
        return await self._impl.check_agent_health()

    def get_registry_stats(self) -> dict[str, Any]:
        """
        获取注册中心统计信息

        Returns:
            统计信息字典
        """
        return self._impl.get_registry_stats()

    def list_all_agents(self) -> list[dict[str, Any]]:
        """
        列出所有Agent信息

        Returns:
            Agent信息字典列表
        """
        return self._impl.list_all_agents()


# 全局单例（兼容原有代码）
_agent_registry = None


def get_agent_registry() -> AgentRegistry:
    """
    获取全局Agent注册中心实例（兼容层）

    Returns:
        AgentRegistry实例（适配器）
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
