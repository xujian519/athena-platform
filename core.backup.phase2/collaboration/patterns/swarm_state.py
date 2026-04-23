"""
Swarm状态管理

定义Swarm模式的状态类，包括：
- SwarmState: Swarm整体状态
- SharedKnowledge: 共享知识库
- SwarmMetrics: Swarm指标
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Agent角色枚举"""
    COORDINATOR = "coordinator"  # 协调者
    WORKER = "worker"  # 工作者
    SPECIALIST = "specialist"  # 专家
    OBSERVER = "observer"  # 观察者
    BACKUP = "backup"  # 备用
    EXPLORER = "explorer"  # 探索者（用于任务探索）


class SwarmDecisionType(str, Enum):
    """Swarm决策类型枚举"""
    CONSENSUS = "consensus"  # 完全共识（所有人同意）
    MAJORITY = "majority"  # 多数决（超过50%）
    SUPER_MAJORITY = "super_majority"  # 超级多数（通常2/3）
    WEIGHTED = "weighted"  # 加权投票（根据权重）
    DELEGATED = "delegated"  # 委托决策（委托给代表）


class SwarmEmergencyType(str, Enum):
    """Swarm紧急类型枚举"""
    TASK_FAILURE = "task_failure"  # 任务失败
    AGENT_FAILURE = "agent_failure"  # Agent失败
    DEADLOCK = "deadlock"  # 死锁
    TIMEOUT = "timeout"  # 超时
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # 资源耗尽


class SwarmMessageType(str, Enum):
    """Swarm消息类型枚举"""
    PROPOSAL = "proposal"  # 提案
    VOTE = "vote"  # 投票
    DECISION = "decision"  # 决策
    STATUS_UPDATE = "status_update"  # 状态更新
    EMERGENCY = "emergency"  # 紧急情况
    SYNC = "sync"  # 同步


class SwarmHealth(str, Enum):
    """Swarm健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class AgentState:
    """单个Agent的状态"""
    agent_id: str
    role: AgentRole = AgentRole.WORKER
    load: float = 0.0  # 负载（0-1）
    last_seen: datetime = field(default_factory=datetime.now)
    capabilities: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    status: str = "active"  # active, inactive, error
    neighbors: List[str] = field(default_factory=list)  # 邻居Agent列表
    role_history: List[AgentRole] = field(default_factory=list)  # 角色变更历史

    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return (
            self.status == "active"
            and self.load < 0.8  # 负载低于80%
            and (datetime.now() - self.last_seen).seconds < 60  # 60秒内活跃
        )

    def assign_role(self, new_role: AgentRole) -> None:
        """分配新角色"""
        old_role = self.role
        self.role = new_role
        self.role_history.append(old_role)  # 记录历史角色
        logger.info(f"Agent {self.agent_id} role changed: {old_role} -> {new_role}")


@dataclass
class SharedKnowledge:
    """共享知识库"""
    knowledge_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    contributors: Set[str] = field(default_factory=set)

    def update(self, key: str, value: Any, agent_id: str) -> None:
        """更新知识"""
        self.data[key] = value
        self.version += 1
        self.updated_at = datetime.now()
        self.contributors.add(agent_id)
        logger.debug(f"Knowledge {self.knowledge_id} updated: {key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取知识"""
        return self.data.get(key, default)

    def merge(self, other: 'SharedKnowledge') -> None:
        """合并另一个知识库"""
        for key, value in other.data.items():
            if key not in self.data or other.updated_at > self.updated_at:
                self.data[key] = value
        self.version += 1
        self.updated_at = datetime.now()
        self.contributors.update(other.contributors)


@dataclass
class SwarmMetrics:
    """Swarm指标"""
    total_agents: int = 0
    active_agents: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_load: float = 0.0
    knowledge_entries: int = 0
    last_update: datetime = field(default_factory=datetime.now)

    def update(self, **kwargs) -> None:
        """更新指标"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_update = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "average_load": self.average_load,
            "knowledge_entries": self.knowledge_entries,
            "last_update": self.last_update.isoformat(),
        }


class SwarmState:
    """
    Swarm整体状态管理

    负责管理Swarm的所有Agent的状态、共享知识和指标。
    """

    def __init__(self, swarm_id: str):
        """初始化Swarm状态"""
        self.swarm_id = swarm_id
        self._agents: Dict[str, AgentState] = {}
        self._knowledge: Dict[str, SharedKnowledge] = {}
        self._metrics = SwarmMetrics()
        self._health = SwarmHealth.HEALTHY
        self._lock = asyncio.Lock()

        logger.info(f"SwarmState {swarm_id} initialized")

    async def add_agent(self, agent_id: str, capabilities: List[str] = None) -> None:
        """添加Agent"""
        async with self._lock:
            if agent_id in self._agents:
                logger.warning(f"Agent {agent_id} already exists")
                return

            agent_state = AgentState(
                agent_id=agent_id,
                capabilities=capabilities or [],
            )
            self._agents[agent_id] = agent_state
            self._metrics.total_agents += 1
            self._metrics.active_agents += 1

            logger.info(f"Agent {agent_id} added to swarm")

    async def remove_agent(self, agent_id: str) -> None:
        """移除Agent"""
        async with self._lock:
            if agent_id not in self._agents:
                logger.warning(f"Agent {agent_id} not found")
                return

            del self._agents[agent_id]
            self._metrics.active_agents -= 1

            logger.info(f"Agent {agent_id} removed from swarm")

    async def get_agent(self, agent_id: str) -> Optional[AgentState]:
        """获取Agent状态"""
        return self._agents.get(agent_id)

    async def list_agents(self, role: Optional[AgentRole] = None) -> List[AgentState]:
        """列出Agent"""
        async with self._lock:
            agents = list(self._agents.values())
            if role:
                agents = [a for a in agents if a.role == role]
            return agents

    async def update_agent_load(self, agent_id: str, load: float) -> None:
        """更新Agent负载"""
        async with self._lock:
            agent = self._agents.get(agent_id)
            if agent:
                agent.load = load
                await self._recalculate_metrics()

    async def assign_role(self, agent_id: str, role: AgentRole) -> None:
        """分配Agent角色"""
        async with self._lock:
            agent = self._agents.get(agent_id)
            if agent:
                agent.assign_role(role)
                logger.info(f"Agent {agent_id} assigned role: {role}")

    async def add_knowledge(self, knowledge_id: str, initial_data: Dict[str, Any] = None) -> SharedKnowledge:
        """添加共享知识"""
        async with self._lock:
            if knowledge_id in self._knowledge:
                logger.warning(f"Knowledge {knowledge_id} already exists")
                return self._knowledge[knowledge_id]

            knowledge = SharedKnowledge(
                knowledge_id=knowledge_id,
                data=initial_data or {},
            )
            self._knowledge[knowledge_id] = knowledge
            self._metrics.knowledge_entries += 1

            logger.info(f"Knowledge {knowledge_id} added")
            return knowledge

    async def get_knowledge(self, knowledge_id: str) -> Optional[SharedKnowledge]:
        """获取共享知识"""
        return self._knowledge.get(knowledge_id)

    async def update_knowledge(self, knowledge_id: str, key: str, value: Any, agent_id: str) -> None:
        """更新共享知识"""
        async with self._lock:
            knowledge = self._knowledge.get(knowledge_id)
            if knowledge:
                knowledge.update(key, value, agent_id)

    async def merge_knowledge(self, knowledge_id: str, other: SharedKnowledge) -> None:
        """合并共享知识"""
        async with self._lock:
            knowledge = self._knowledge.get(knowledge_id)
            if knowledge:
                knowledge.merge(other)

    async def get_metrics(self) -> SwarmMetrics:
        """获取Swarm指标"""
        async with self._lock:
            await self._recalculate_metrics()
            return self._metrics

    async def _recalculate_metrics(self) -> None:
        """重新计算指标"""
        if not self._agents:
            self._metrics.average_load = 0.0
            return

        total_load = sum(agent.load for agent in self._agents.values())
        self._metrics.average_load = total_load / len(self._agents)

    async def get_health(self) -> SwarmHealth:
        """获取Swarm健康状态"""
        async with self._lock:
            # 计算健康状态
            if self._metrics.active_agents == 0:
                self._health = SwarmHealth.CRITICAL
            elif self._metrics.average_load > 0.9:
                self._health = SwarmHealth.DEGRADED
            else:
                self._health = SwarmHealth.HEALTHY

            return self._health

    async def get_available_agents(self) -> List[AgentState]:
        """获取可用的Agent"""
        async with self._lock:
            return [agent for agent in self._agents.values() if agent.is_available()]
