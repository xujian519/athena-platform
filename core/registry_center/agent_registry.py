"""
统一Agent注册表 - 整合3个重复的Agent注册表

整合目标：
1. core/agent_collaboration/agent_registry.py (AgentRegistry + AgentInfo)
2. core/framework/routing/agent_registry.py (AgentRegistry + AgentInfo)
3. core/agents/subagent_registry.py (SubagentRegistry + SubagentConfig)

统一特性：
- 整合所有3个注册表的功能
- 保留原有API（向后兼容）
- 添加事件通知机制
- 统一健康检查
- 统一性能监控
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from core.registry_center.base import BaseRegistry, RegistryEvent, RegistryEventType
from core.registry_center.unified import UnifiedRegistryCenter

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class AgentType(Enum):
    """Agent类型枚举（整合自core/agent_collaboration/agent_registry.py）"""
    SEARCH = "search"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    COORDINATOR = "coordinator"
    GENERAL = "general"
    XIAONA_COMPONENT = "xiaona_component"  # 小娜专业组件
    SUBAGENT = "subagent"  # 子代理


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


# ==================== 数据类定义 ====================

@dataclass
class AgentInfo:
    """
    统一Agent信息（整合3个版本的AgentInfo）

    整合来源：
    1. core/agent_collaboration/agent_registry.py - AgentInfo
    2. core/framework/routing/agent_registry.py - AgentInfo
    3. core/agents/subagent_registry.py - SubagentConfig
    """

    # 基础信息（通用）
    agent_id: str
    agent_type: AgentType
    name: str
    description: str

    # 能力配置
    capabilities: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    # 状态管理
    status: AgentStatus = AgentStatus.IDLE
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    current_task_id: Optional[str] = None

    # 性能指标
    performance_metrics: dict[str, Any] = field(default_factory=dict)

    # 扩展字段（兼容SubagentConfig）
    enabled: bool = True
    phase: Optional[int] = None  # 所属阶段
    priority: int = 5  # 优先级
    max_concurrent_tasks: int = 3
    system_prompt: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # 实例引用（兼容framework/routing/agent_registry.py）
    agent_instance: Optional[Any] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value if isinstance(self.agent_type, AgentType) else self.agent_type,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "config": self.config,
            "status": self.status.value if isinstance(self.status, AgentStatus) else self.status,
            "last_heartbeat": self.last_heartbeat,
            "current_task_id": self.current_task_id,
            "performance_metrics": self.performance_metrics,
            "enabled": self.enabled,
            "phase": self.phase,
            "priority": self.priority,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "system_prompt": self.system_prompt,
            "allowed_tools": self.allowed_tools,
            "metadata": self.metadata,
        }


# ==================== 统一Agent注册表 ====================

class UnifiedAgentRegistry(BaseRegistry):
    """
    统一Agent注册表

    整合3个重复的Agent注册表功能：
    1. Agent注册/注销/查询（core/agent_collaboration/agent_registry.py）
    2. 小娜专业组件注册（core/framework/routing/agent_registry.py）
    3. 子代理配置管理（core/agents/subagent_registry.py）

    特性：
    - 单例模式，线程安全
    - 支持按类型/能力/阶段查询
    - 心跳检测和健康检查
    - 事件通知机制
    - 性能监控
    - 向后兼容所有原有API
    """

    _instance: Optional["UnifiedAgentRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # 在__new__中设置初始化标志，确保__init__只执行一次
                    cls._instance._initialized = False  # type: ignore[attr-defined]
        return cls._instance

    def __init__(self):
        # 使用getattr安全访问_initialized属性，避免类型检查器警告
        if getattr(self, "_initialized", False):
            return

        # 使用统一注册中心作为底层存储
        self._center = UnifiedRegistryCenter.get_instance()

        # 并发控制
        self._lock = threading.RLock()

        # 心跳配置
        self.heartbeat_interval = 30  # 心跳间隔(秒)
        self.heartbeat_timeout = 90  # 心跳超时(秒)

        # 初始化完成
        self._initialized = True
        logger.info("✅ 统一Agent注册表初始化完成")

    @classmethod
    def get_instance(cls) -> "UnifiedAgentRegistry":
        """获取单例实例"""
        return cls()

    # ==================== 核心CRUD操作 ====================

    def register(self, entity_id: str, entity: Any) -> bool:
        """
        注册Agent（兼容BaseRegistry接口）

        Args:
            entity_id: Agent ID
            entity: AgentInfo对象或Agent实例

        Returns:
            bool: 注册是否成功
        """
        if isinstance(entity, AgentInfo):
            return self.register_agent(entity)
        else:
            # 尝试从实例创建AgentInfo
            logger.warning(f"⚠️ 传入的不是AgentInfo对象，尝试自动转换")
            return self.register_agent(
                AgentInfo(
                    agent_id=entity_id,
                    agent_type=AgentType.GENERAL,
                    name=entity.__class__.__name__,
                    description=f"Auto-created from {type(entity).__name__}",
                    agent_instance=entity,
                )
            )

    def unregister(self, entity_id: str) -> bool:
        """
        注销Agent

        Args:
            entity_id: Agent ID

        Returns:
            bool: 注销是否成功
        """
        return self.unregister_agent(entity_id)

    def get(self, entity_id: str) -> Optional[Any]:
        """
        获取Agent

        Args:
            entity_id: Agent ID

        Returns:
            AgentInfo或Agent实例
        """
        agent_info = self.get_agent_info(entity_id)
        if agent_info and agent_info.agent_instance:
            return agent_info.agent_instance
        return agent_info

    def exists(self, entity_id: str) -> bool:
        """检查Agent是否存在"""
        return self._center.exists(f"agent:{entity_id}")

    def list_all(self) -> list[Any]:
        """列出所有Agent"""
        return self._center.list_by_type("agent")

    def count(self) -> int:
        """获取Agent数量"""
        return self._center.count_by_type("agent")

    def clear(self) -> None:
        """清空注册表"""
        # 清空所有agent类型的实体
        agents = self.list_all()
        for agent_info in agents:
            if isinstance(agent_info, AgentInfo):
                self.unregister_agent(agent_info.agent_id)

    # ==================== Agent专用操作 ====================

    def register_agent(self, agent_info: AgentInfo) -> bool:
        """
        注册Agent（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_info: Agent信息

        Returns:
            bool: 注册是否成功
        """
        try:
            entity_id = f"agent:{agent_info.agent_id}"
            success = self._center.register(entity_id, agent_info, entity_type="agent")

            if success:
                logger.info(f"✅ Agent {agent_info.name} ({agent_info.agent_id}) 注册成功")

                # 发布事件
                self._center._emit_event(
                    RegistryEvent(
                        event_type=RegistryEventType.ENTITY_REGISTERED,
                        entity_id=agent_info.agent_id,
                        entity_type="agent",
                        data={"agent_type": agent_info.agent_type.value},
                    )
                )

            return success

        except Exception as e:
            logger.error(f"❌ Agent注册失败: {e}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """
        注销Agent（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_id: Agent ID

        Returns:
            bool: 注销是否成功
        """
        entity_id = f"agent:{agent_id}"
        return self._center.unregister(entity_id)

    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """
        获取Agent信息（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_id: Agent ID

        Returns:
            AgentInfo对象，不存在返回None
        """
        entity_id = f"agent:{agent_id}"
        return self._center.get(entity_id)

    def find_agents_by_type(
        self, agent_type: AgentType, status: Optional[AgentStatus] = None
    ) -> list[AgentInfo]:
        """
        根据类型查找Agent（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_type: Agent类型
            status: Agent状态过滤

        Returns:
            匹配的Agent列表
        """
        all_agents = self.list_all()
        result = []

        for agent_info in all_agents:
            if not isinstance(agent_info, AgentInfo):
                continue

            # 类型过滤
            if agent_info.agent_type != agent_type:
                continue

            # 状态过滤
            if status and agent_info.status != status:
                continue

            result.append(agent_info)

        return result

    def find_available_agents(self, agent_type: Optional[AgentType] = None) -> list[AgentInfo]:
        """
        查找可用的Agent（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_type: Agent类型过滤

        Returns:
            可用的Agent列表
        """
        all_agents = self.list_all()
        result = []

        for agent_info in all_agents:
            if not isinstance(agent_info, AgentInfo):
                continue

            # 状态过滤
            if agent_info.status != AgentStatus.IDLE:
                continue

            # 类型过滤
            if agent_type and agent_info.agent_type != agent_type:
                continue

            result.append(agent_info)

        return result

    def find_agents_by_capability(self, capability_name: str) -> list[AgentInfo]:
        """
        根据能力查找Agent（兼容core/framework/routing/agent_registry.py）

        Args:
            capability_name: 能力名称

        Returns:
            匹配的Agent列表
        """
        all_agents = self.list_all()
        result = []

        for agent_info in all_agents:
            if not isinstance(agent_info, AgentInfo):
                continue

            if capability_name in agent_info.capabilities:
                result.append(agent_info)

        return result

    def find_agents_by_phase(self, phase: int) -> list[AgentInfo]:
        """
        根据阶段查找Agent（兼容core/framework/routing/agent_registry.py）

        Args:
            phase: 阶段编号（1/2/3）

        Returns:
            匹配的Agent列表
        """
        all_agents = self.list_all()
        result = []

        for agent_info in all_agents:
            if not isinstance(agent_info, AgentInfo):
                continue

            if agent_info.phase == phase:
                result.append(agent_info)

        return result

    def get_best_agent(
        self, agent_type: AgentType, capabilities: Optional[list[str]] = None
    ) -> Optional[AgentInfo]:
        """
        获取最适合的Agent（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_type: Agent类型
            capabilities: 能力需求

        Returns:
            最适合的Agent，无可用Agent返回None
        """
        candidates = self.find_available_agents(agent_type)

        if not candidates:
            return None

        # 如果有能力需求，进行能力匹配
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

        # 无能力需求，返回第一个可用Agent
        return candidates[0]

    # ==================== 状态更新 ====================

    async def update_agent_status(
        self, agent_id: str, status: AgentStatus, task_id: Optional[str] = None
    ) -> None:
        """
        更新Agent状态（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_id: Agent ID
            status: 新状态
            task_id: 当前任务ID
        """
        agent_info = self.get_agent_info(agent_id)
        if agent_info:
            agent_info.status = status
            agent_info.current_task_id = task_id
            agent_info.last_heartbeat = datetime.now().isoformat()

            # 更新到底层存储
            entity_id = f"agent:{agent_id}"
            self._center.register(entity_id, agent_info, entity_type="agent")

    async def update_heartbeat(self, agent_id: str) -> None:
        """
        更新Agent心跳（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_id: Agent ID
        """
        self._center.update_heartbeat(f"agent:{agent_id}")

    async def update_performance_metrics(self, agent_id: str, metrics: dict[str, Any]) -> None:
        """
        更新Agent性能指标（兼容core/agent_collaboration/agent_registry.py）

        Args:
            agent_id: Agent ID
            metrics: 性能指标
        """
        agent_info = self.get_agent_info(agent_id)
        if agent_info:
            agent_info.performance_metrics.update(metrics)

            # 更新到底层存储
            entity_id = f"agent:{agent_id}"
            self._center.register(entity_id, agent_info, entity_type="agent")

    # ==================== 启用/禁用 ====================

    def enable_agent(self, agent_id: str) -> None:
        """
        启用Agent（兼容core/framework/routing/agent_registry.py）

        Args:
            agent_id: Agent ID
        """
        agent_info = self.get_agent_info(agent_id)
        if agent_info:
            agent_info.enabled = True
            logger.info(f"✅ 启用Agent: {agent_id}")

    def disable_agent(self, agent_id: str) -> None:
        """
        禁用Agent（兼容core/framework/routing/agent_registry.py）

        Args:
            agent_id: Agent ID
        """
        agent_info = self.get_agent_info(agent_id)
        if agent_info:
            agent_info.enabled = False
            logger.info(f"✅ 禁用Agent: {agent_id}")

    # ==================== 健康检查 ====================

    async def check_agent_health(self) -> list[str]:
        """
        检查Agent健康状态（兼容core/agent_collaboration/agent_registry.py）

        Returns:
            不健康的Agent ID列表
        """
        all_agents = self.list_all()
        unhealthy_agents = []
        current_time = datetime.now()

        for agent_info in all_agents:
            if not isinstance(agent_info, AgentInfo):
                continue

            try:
                last_heartbeat = datetime.fromisoformat(agent_info.last_heartbeat)
                time_diff = (current_time - last_heartbeat).total_seconds()

                if time_diff > self.heartbeat_timeout:
                    # 心跳超时，标记为离线
                    if agent_info.status != AgentStatus.OFFLINE:
                        logger.warning(f"⚠️ Agent {agent_info.agent_id} 心跳超时，标记为离线")
                        agent_info.status = AgentStatus.OFFLINE
                        unhealthy_agents.append(agent_info.agent_id)

            except Exception as e:
                logger.error(f"❌ 检查Agent {agent_info.agent_id} 健康状态失败: {e}")

        return unhealthy_agents

    # ==================== 统计信息 ====================

    def get_registry_stats(self) -> dict[str, Any]:
        """
        获取注册中心统计信息（兼容core/agent_collaboration/agent_registry.py）

        Returns:
            统计信息字典
        """
        all_agents = self.list_all()

        stats: dict[str, Any] = {
            "total_agents": len(all_agents),
            "agents_by_type": {},
            "agents_by_status": {},
        }

        # 按类型统计
        for agent_info in all_agents:
            if isinstance(agent_info, AgentInfo):
                agent_type = agent_info.agent_type.value if isinstance(agent_info.agent_type, AgentType) else str(agent_info.agent_type)
                stats["agents_by_type"][agent_type] = stats["agents_by_type"].get(agent_type, 0) + 1

                status = agent_info.status.value if isinstance(agent_info.status, AgentStatus) else str(agent_info.status)
                stats["agents_by_status"][status] = stats["agents_by_status"].get(status, 0) + 1

        return stats

    def list_all_agents(self) -> list[dict[str, Any]]:
        """
        列出所有Agent信息（兼容core/agent_collaboration/agent_registry.py）

        Returns:
            Agent信息字典列表
        """
        all_agents = self.list_all()
        return [agent.to_dict() for agent in all_agents if isinstance(agent, AgentInfo)]

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息（兼容core/framework/routing/agent_registry.py）

        Returns:
            统计信息字典
        """
        all_agents = self.list_all()

        total = len(all_agents)
        enabled = sum(1 for a in all_agents if isinstance(a, AgentInfo) and a.enabled)
        disabled = total - enabled

        phase_stats: dict[str, int] = {}
        for agent_info in all_agents:
            if isinstance(agent_info, AgentInfo) and agent_info.phase:
                phase_key = f"phase_{agent_info.phase}"
                phase_stats[phase_key] = phase_stats.get(phase_key, 0) + 1

        # 能力统计
        all_capabilities = set()
        for agent_info in all_agents:
            if isinstance(agent_info, AgentInfo):
                all_capabilities.update(agent_info.capabilities)

        return {
            "total_agents": total,
            "enabled": enabled,
            "disabled": disabled,
            "total_capabilities": len(all_capabilities),
            "phase_distribution": phase_stats,
        }

    def list_capabilities(self) -> list[str]:
        """
        列出所有能力（兼容core/framework/routing/agent_registry.py）

        Returns:
            能力名称列表
        """
        all_agents = self.list_all()
        capabilities = set()

        for agent_info in all_agents:
            if isinstance(agent_info, AgentInfo):
                capabilities.update(agent_info.capabilities)

        return list(capabilities)


# ==================== 全局单例 ====================

def get_agent_registry() -> UnifiedAgentRegistry:
    """
    获取全局Agent注册表单例

    Returns:
        UnifiedAgentRegistry实例
    """
    return UnifiedAgentRegistry.get_instance()
