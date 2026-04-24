"""
Framework路由模块适配器

兼容: core/framework/routing/agent_registry.py

重定向所有调用到统一注册中心，保持API完全兼容。
"""

import logging
import threading
from typing import Any, Optional

from core.framework.agents.xiaona.base_component import AgentCapability, BaseXiaonaComponent
from core.registry_center.agent_registry import (
    AgentInfo as UnifiedAgentInfo,
    AgentType,
    get_agent_registry,
)

logger = logging.getLogger(__name__)


# 导出原有类型
__all__ = ["AgentInfo", "AgentRegistry"]


class AgentInfo:
    """
    智能体信息（兼容层）

    重定向到统一AgentInfo，保持原有API。
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        agent_instance: BaseXiaonaComponent,
        capabilities: list[AgentCapability],
        phase: int,
        enabled: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        初始化AgentInfo（兼容原有接口）

        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型（用于记录，保留兼容性）
            agent_instance: 智能体实例
            capabilities: 能力列表
            phase: 所属阶段
            enabled: 是否启用
            metadata: 元数据
        """
        # agent_type参数用于保持接口兼容性，实际类型由统一注册中心管理
        _ = agent_type  # 标记为intentionally unused

        # 转换为统一AgentInfo
        self._impl = UnifiedAgentInfo(
            agent_id=agent_id,
            agent_type=AgentType.XIAONA_COMPONENT,
            # 从agent实例获取名称，或使用类名
            name=getattr(agent_instance, "name", agent_instance.__class__.__name__),
            # 从agent实例获取描述，或生成默认描述
            description=getattr(
                agent_instance,
                "description",
                f"{agent_instance.__class__.__name__} agent"
            ),
            capabilities=[cap.name for cap in capabilities],
            enabled=enabled,
            phase=phase,
            metadata=metadata or {},
            agent_instance=agent_instance,
        )

        # 保存原始capabilities以保持类型兼容性
        self._capabilities: list[AgentCapability] = capabilities

    # 代理所有属性访问
    @property
    def agent_id(self) -> str:
        return self._impl.agent_id

    @property
    def agent_type(self) -> str:
        return str(self._impl.agent_type)

    @property
    def agent_instance(self) -> BaseXiaonaComponent:
        # 类型断言：我们确保agent_instance是BaseXiaonaComponent
        instance = self._impl.agent_instance
        if instance is None:
            raise RuntimeError(f"Agent instance for {self.agent_id} is None")
        # 类型断言：绕过类型检查器的警告
        assert isinstance(instance, BaseXiaonaComponent)
        return instance

    @property
    def capabilities(self) -> list[AgentCapability]:
        # 返回原始的AgentCapability列表以保持类型兼容性
        return self._capabilities

    @property
    def phase(self) -> int:
        return self._impl.phase or 1

    @property
    def enabled(self) -> bool:
        return self._impl.enabled

    @property
    def metadata(self) -> dict[str, Any]:
        return self._impl.metadata


class AgentRegistry:
    """
    智能体注册表（兼容层）

    重定向到UnifiedAgentRegistry，保持原有API完全兼容。

    原模块: core/framework/routing/agent_registry.py
    """

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False  # type: ignore[attr-defined]
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        # 使用统一注册中心（使用Any类型以避免循环导入和类型检查问题）
        self._impl: Any = get_agent_registry()

        self._initialized = True  # type: ignore[attr-defined]
        self.logger = logging.getLogger(__name__)
        self.logger.info("智能体注册表初始化完成（兼容层）")

    def register(
        self,
        agent: BaseXiaonaComponent,
        phase: int = 1,
        metadata: Optional[dict[str, Any]] = None,
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

        # 检查是否已注册
        if self._impl.exists(agent_id):
            raise ValueError(f"智能体 {agent_id} 已注册")

        # 创建统一AgentInfo
        agent_info = UnifiedAgentInfo(
            agent_id=agent_id,
            agent_type=AgentType.XIAONA_COMPONENT,
            name=getattr(agent, "name", agent.__class__.__name__),
            description=getattr(
                agent,
                "description",
                f"{agent.__class__.__name__} agent"
            ),
            capabilities=[cap.name for cap in agent.get_capabilities()],
            enabled=True,
            phase=phase,
            metadata=metadata or {},
            agent_instance=agent,
        )

        # 注册到统一注册中心
        self._impl.register_agent(agent_info)

        self.logger.info(
            f"注册智能体: {agent_id} ({agent.__class__.__name__}), "
            f"阶段: {phase}, 能力: {len(agent_info.capabilities)}"
        )

    def unregister(self, agent_id: str) -> None:
        """
        注销智能体

        Args:
            agent_id: 智能体ID
        """
        if not self._impl.exists(agent_id):
            self.logger.warning(f"智能体 {agent_id} 未注册")
            return

        self._impl.unregister_agent(agent_id)
        self.logger.info(f"注销智能体: {agent_id}")

    def get_agent(self, agent_id: str) -> Optional[BaseXiaonaComponent]:
        """
        获取智能体实例

        Args:
            agent_id: 智能体ID

        Returns:
            智能体实例，如果不存在返回None
        """
        agent_info = self._impl.get_agent_info(agent_id)
        if agent_info and agent_info.enabled and agent_info.agent_instance:
            return agent_info.agent_instance
        return None

    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """
        获取智能体信息

        Args:
            agent_id: 智能体ID

        Returns:
            智能体信息，如果不存在返回None
        """
        info = self._impl.get_agent_info(agent_id)
        if info and info.agent_instance:
            # 包装为兼容的AgentInfo
            capabilities = [
                AgentCapability(
                    name=cap,
                    description=f"Capability: {cap}",
                    input_types=[],
                    output_types=[],
                    estimated_time=30.0,
                )
                for cap in info.capabilities
            ]
            return AgentInfo(
                agent_id=info.agent_id,
                agent_type=str(info.agent_type),
                agent_instance=info.agent_instance,
                capabilities=capabilities,
                phase=info.phase or 1,
                enabled=info.enabled,
                metadata=info.metadata,
            )
        return None

    def find_agents_by_capability(self, capability_name: str) -> list[BaseXiaonaComponent]:
        """
        根据能力查找智能体

        Args:
            capability_name: 能力名称

        Returns:
            智能体列表
        """
        agent_infos = self._impl.find_agents_by_capability(capability_name)
        result: list[BaseXiaonaComponent] = []
        for info in agent_infos:
            if info.agent_instance:
                result.append(info.agent_instance)
        return result

    def find_agents_by_phase(self, phase: int) -> list[BaseXiaonaComponent]:
        """
        根据阶段查找智能体

        Args:
            phase: 阶段编号（1/2/3）

        Returns:
            智能体列表
        """
        agent_infos = self._impl.find_agents_by_phase(phase)
        result: list[BaseXiaonaComponent] = []
        for info in agent_infos:
            if info.agent_instance:
                result.append(info.agent_instance)
        return result

    def list_all_agents(self) -> dict[str, AgentInfo]:
        """
        列出所有智能体

        Returns:
            智能体信息字典
        """
        all_agents = self._impl.list_all()
        result: dict[str, AgentInfo] = {}
        for info in all_agents:
            if isinstance(info, UnifiedAgentInfo) and info.agent_instance:
                capabilities = [
                    AgentCapability(
                        name=cap,
                        description=f"Capability: {cap}",
                        input_types=[],
                        output_types=[],
                        estimated_time=30.0,
                    )
                    for cap in info.capabilities
                ]
                result[info.agent_id] = AgentInfo(
                    agent_id=info.agent_id,
                    agent_type=str(info.agent_type),
                    agent_instance=info.agent_instance,
                    capabilities=capabilities,
                    phase=info.phase or 1,
                    enabled=info.enabled,
                    metadata=info.metadata,
                )
        return result

    def list_capabilities(self) -> list[str]:
        """
        列出所有能力

        Returns:
            能力名称列表
        """
        return self._impl.list_capabilities()

    def enable_agent(self, agent_id: str) -> None:
        """
        启用智能体

        Args:
            agent_id: 智能体ID
        """
        self._impl.enable_agent(agent_id)
        self.logger.info(f"启用智能体: {agent_id}")

    def disable_agent(self, agent_id: str) -> None:
        """
        禁用智能体

        Args:
            agent_id: 智能体ID
        """
        self._impl.disable_agent(agent_id)
        self.logger.info(f"禁用智能体: {agent_id}")

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return self._impl.get_statistics()

    def clear(self) -> None:
        """
        清空注册表（主要用于测试）
        """
        self._impl.clear()
        self.logger.info("清空智能体注册表")


# 全局单例
def get_agent_registry() -> AgentRegistry:
    """
    获取智能体注册表单例

    Returns:
        AgentRegistry实例
    """
    return AgentRegistry()
