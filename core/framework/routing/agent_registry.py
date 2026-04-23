"""
智能体注册表

管理所有小娜专业智能体的注册、发现和获取。
类似统一工具注册表的设计，支持智能体的动态注册和查询。
"""

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

from core.framework.agents.xiaona.base_component import AgentCapability, BaseXiaonaComponent

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """智能体信息"""
    agent_id: str                          # 智能体ID
    agent_type: str                        # 智能体类型
    agent_instance: BaseXiaonaComponent    # 智能体实例
    capabilities: list[AgentCapability]    # 能力列表
    phase: int                             # 所属阶段
    enabled: bool = True                   # 是否启用
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


class AgentRegistry:
    """
    智能体注册表

    单例模式，线程安全，管理所有智能体的注册和查询。
    """

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._agents: dict[str, AgentInfo] = {}
        self._capability_index: dict[str, list[str] = {}  # capability -> agent_ids
        self._phase_index: dict[int, list[str] = {}       # phase -> agent_ids
        self._lock = threading.RLock()
        self._initialized = True

        self.logger = logging.getLogger(__name__)
        self.logger.info("智能体注册表初始化完成")

    def register(
        self,
        agent: BaseXiaonaComponent,
        phase: int = 1,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        注册智能体

        Args:
            agent: 智能体实例
            phase: 所属阶段（1/2/3）
            metadata: 元数据

        Raises:
            ValueError: 如果agent_id已存在
        """
        agent_id = agent.agent_id

        with self._lock:
            # 检查是否已注册
            if agent_id in self._agents:
                raise ValueError(f"智能体 {agent_id} 已注册")

            # 创建AgentInfo
            info = AgentInfo(
                agent_id=agent_id,
                agent_type=agent.__class__.__name__,
                agent_instance=agent,
                capabilities=agent.get_capabilities(),
                phase=phase,
                enabled=True,
                metadata=metadata or {},
            )

            # 注册
            self._agents[agent_id] = info

            # 更新能力索引
            for cap in info.capabilities:
                if cap.name not in self._capability_index:
                    self._capability_index[cap.name]] = []
                self._capability_index[cap.name].append(agent_id)

            # 更新阶段索引
            if phase not in self._phase_index:
                self._phase_index[phase]] = []
            self._phase_index[phase].append(agent_id)

            self.logger.info(
                f"注册智能体: {agent_id} ({info.agent_type}), "
                f"阶段: {phase}, 能力: {len(info.capabilities)}"
            )

    def unregister(self, agent_id: str) -> None:
        """
        注销智能体

        Args:
            agent_id: 智能体ID
        """
        with self._lock:
            if agent_id not in self._agents:
                self.logger.warning(f"智能体 {agent_id} 未注册")
                return

            info = self._agents[agent_id]

            # 清理能力索引
            for cap in info.capabilities:
                if cap.name in self._capability_index:
                    self._capability_index[cap.name].remove(agent_id)
                    if not self._capability_index[cap.name]:
                        del self._capability_index[cap.name]

            # 清理阶段索引
            if info.phase in self._phase_index:
                self._phase_index[info.phase].remove(agent_id)
                if not self._phase_index[info.phase]:
                    del self._phase_index[info.phase]

            # 删除智能体
            del self._agents[agent_id]

            self.logger.info(f"注销智能体: {agent_id}")

    def get_agent(self, agent_id: str) -> Optional[BaseXiaonaComponent]:
        """
        获取智能体实例

        Args:
            agent_id: 智能体ID

        Returns:
            智能体实例，如果不存在返回None
        """
        with self._lock:
            info = self._agents.get(agent_id)
            if info and info.enabled:
                return info.agent_instance
            return None

    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """
        获取智能体信息

        Args:
            agent_id: 智能体ID

        Returns:
            智能体信息，如果不存在返回None
        """
        with self._lock:
            return self._agents.get(agent_id)

    def find_agents_by_capability(self, capability_name: str) -> list[BaseXiaonaComponent]:
        """
        根据能力查找智能体

        Args:
            capability_name: 能力名称

        Returns:
            智能体列表
        """
        with self._lock:
            agent_ids = self._capability_index.get(capability_name, [])
            agents = []
            for agent_id in agent_ids:
                agent = self.get_agent(agent_id)
                if agent:
                    agents.append(agent)
            return agents

    def find_agents_by_phase(self, phase: int) -> list[BaseXiaonaComponent]:
        """
        根据阶段查找智能体

        Args:
            phase: 阶段编号（1/2/3）

        Returns:
            智能体列表
        """
        with self._lock:
            agent_ids = self._phase_index.get(phase, [])
            agents = []
            for agent_id in agent_ids:
                agent = self.get_agent(agent_id)
                if agent:
                    agents.append(agent)
            return agents

    def list_all_agents(self) -> dict[str, AgentInfo]:
        """
        列出所有智能体

        Returns:
            智能体信息字典
        """
        with self._lock:
            return self._agents.copy()

    def list_capabilities(self) -> list[str]:
        """
        列出所有能力

        Returns:
            能力名称列表
        """
        with self._lock:
            return list(self._capability_index.keys())

    def enable_agent(self, agent_id: str) -> None:
        """
        启用智能体

        Args:
            agent_id: 智能体ID
        """
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].enabled = True
                self.logger.info(f"启用智能体: {agent_id}")

    def disable_agent(self, agent_id: str) -> None:
        """
        禁用智能体

        Args:
            agent_id: 智能体ID
        """
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].enabled = False
                self.logger.info(f"禁用智能体: {agent_id}")

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            total = len(self._agents)
            enabled = sum(1 for info in self._agents.values() if info.enabled)
            disabled = total - enabled

            phase_stats = {}
            for phase, agent_ids in self._phase_index.items():
                phase_stats[f"phase_{phase}"] = len(agent_ids)

            return {
                "total_agents": total,
                "enabled": enabled,
                "disabled": disabled,
                "total_capabilities": len(self._capability_index),
                "phase_distribution": phase_stats,
            }

    def clear(self) -> None:
        """
        清空注册表（主要用于测试）
        """
        with self._lock:
            self._agents.clear()
            self._capability_index.clear()
            self._phase_index.clear()
            self.logger.info("清空智能体注册表")


# 全局单例
def get_agent_registry() -> AgentRegistry:
    """
    获取智能体注册表单例

    Returns:
        AgentRegistry实例
    """
    return AgentRegistry()
