"""
Swarm Agent实现

定义Swarm中的Agent行为和角色管理。
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import logging

from .swarm_state import AgentState, AgentRole


logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"  # 已分配
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SwarmTask:
    """
    Swarm任务类

    代表Swarm中的一个任务。
    """

    def __init__(
        self,
        id: str,
        description: str,
        required_capabilities: list[str] = None,
        status: TaskStatus = TaskStatus.PENDING,
    ):
        """初始化Swarm任务"""
        self.id = id
        self.description = description
        self.required_capabilities = required_capabilities or []
        self.status = status
        self.assignees: list[str] = []
        self.subtasks: list["SwarmTask"] = []
        self.parent_id: Optional[str] = None
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.result: Optional[dict[str, Any]] = None  # 任务执行结果
        self.error: Optional[str] = None  # 任务失败原因

        logger.debug(f"SwarmTask {id} created: {description}")

    def add_subtask(self, subtask: "SwarmTask") -> None:
        """添加子任务"""
        subtask.parent_id = self.id
        self.subtasks.append(subtask)
        logger.debug(f"Subtask {subtask.id} added to task {self.id}")

    def assign_to(self, agent_id: str) -> None:
        """分配任务给Agent"""
        if agent_id not in self.assignees:
            self.assignees.append(agent_id)
            self.status = TaskStatus.ASSIGNED
            logger.debug(f"Task {self.id} assigned to agent {agent_id}")

    def complete(self, result: dict[str, Any] = None) -> None:
        """标记任务为完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        logger.info(f"Task {self.id} completed")

    def fail(self, error: str = None) -> None:
        """标记任务为失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        logger.warning(f"Task {self.id} failed")


class SwarmAgent:
    """
    Swarm Agent类

    代表Swarm中的一个Agent，具有角色、负载和协作能力。
    """

    def __init__(
        self,
        agent_id: str,
        initial_role: AgentRole = AgentRole.WORKER,
        capabilities: list[str] = None,
    ):
        """初始化Swarm Agent"""
        self.agent_id = agent_id
        self._state = AgentState(
            agent_id=agent_id,
            role=initial_role,
            capabilities=capabilities or [],
        )
        self._task_history: list[str] = []
        self._performance_metrics: dict[str, float] = {}

        logger.info(f"SwarmAgent {agent_id} initialized with role {initial_role}")

    async def execute_task(self, task_id: str, task_data: dict[str, Any]) -> Any:
        """
        执行任务

        Args:
            task_id: 任务ID
            task_data: 任务数据

        Returns:
            任务结果
        """
        self._state.current_task = task_id
        self._state.load = 1.0  # 设置为满负载

        try:
            # 模拟任务执行
            logger.info(f"Agent {self.agent_id} executing task {task_id}")
            await asyncio.sleep(0.1)  # 模拟异步执行

            result = {
                "task_id": task_id,
                "agent_id": self.agent_id,
                "status": "completed",
                "result": "success",
            }

            self._task_history.append(task_id)
            self._state.load = 0.0  # 重置负载
            self._state.current_task = None

            return result

        except Exception as e:
            logger.error(f"Agent {self.agent_id} failed task {task_id}: {e}")
            self._state.load = 0.0
            self._state.current_task = None
            self._state.status = "error"
            raise

    async def change_role(self, new_role: AgentRole) -> None:
        """
        改变Agent角色

        Args:
            new_role: 新角色
        """
        old_role = self._state.role
        self._state.assign_role(new_role)
        logger.info(f"Agent {self.agent_id} role changed: {old_role} -> {new_role}")

    async def update_load(self, load: float) -> None:
        """
        更新Agent负载

        Args:
            load: 负载值（0-1）
        """
        self._state.load = max(0.0, min(1.0, load))  # 限制在0-1范围

    def get_state(self) -> AgentState:
        """获取Agent状态"""
        return self._state

    def get_role(self) -> AgentRole:
        """获取当前角色"""
        return self._state.role

    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return self._state.is_available()

    def get_capabilities(self) -> list[str]:
        """获取Agent能力"""
        return self._state.capabilities

    # 属性访问器（为了向后兼容）
    @property
    def role(self) -> AgentRole:
        """获取当前角色（属性访问）"""
        return self._state.role

    @property
    def capabilities(self) -> list[str]:
        """获取能力列表（属性访问）"""
        return self._state.capabilities

    @property
    def load(self) -> float:
        """获取当前负载（属性访问）"""
        return self._state.load

    @load.setter
    def load(self, value: float) -> None:
        """设置当前负载"""
        self._state.load = max(0.0, min(1.0, value))

    @property
    def current_load(self) -> float:
        """获取当前负载（别名，为了向后兼容）"""
        return self._state.load

    @current_load.setter
    def current_load(self, value: float) -> None:
        """设置当前负载（别名）"""
        self._state.load = max(0.0, min(1.0, value))

    @property
    def role_history(self) -> list[AgentRole]:
        """获取角色历史（属性访问）"""
        return self._state.role_history

    @property
    def neighbors(self) -> list[str]:
        """获取邻居列表（属性访问）"""
        return self._state.neighbors

    @property
    def is_active(self) -> bool:
        """检查Agent是否活跃（属性访问）"""
        return self._state.status == "active"

    @is_active.setter
    def is_active(self, value: bool) -> None:
        """设置Agent活跃状态"""
        self._state.status = "active" if value else "inactive"

    def add_neighbor(self, neighbor_id: str) -> None:
        """添加邻居"""
        if neighbor_id not in self._state.neighbors:
            self._state.neighbors.append(neighbor_id)

    def remove_neighbor(self, neighbor_id: str) -> None:
        """移除邻居"""
        if neighbor_id in self._state.neighbors:
            self._state.neighbors.remove(neighbor_id)

    def can_handle_capability(self, capability: str) -> bool:
        """
        检查Agent是否具备某个能力

        Args:
            capability: 能力名称

        Returns:
            是否具备该能力
        """
        return capability in self._state.capabilities

    def can_handle_task(self, task) -> bool:
        """
        检查Agent是否能处理任务

        Args:
            task: Swarm任务对象或字典（包含required_capabilities键）

        Returns:
            是否能处理
        """
        if not self.is_available():
            return False

        # 支持SwarmTask对象或字典
        if isinstance(task, dict):
            required_caps = task.get("required_capabilities", [])
        elif hasattr(task, 'required_capabilities'):
            required_caps = task.required_capabilities
        else:
            return False

        # 检查是否具备所有必需的能力
        return all(cap in self._state.capabilities for cap in required_caps)

    def get_task_history(self) -> list[str]:
        """获取任务历史"""
        return self._task_history.copy()

    def get_performance_metrics(self) -> dict[str, float]:
        """获取性能指标"""
        return self._performance_metrics.copy()

    async def update_performance(self, metric_name: str, value: float) -> None:
        """
        更新性能指标

        Args:
            metric_name: 指标名称
            value: 指标值
        """
        self._performance_metrics[metric_name] = value
        logger.debug(f"Agent {self.agent_id} performance {metric_name} = {value}")


class SwarmKnowledgeItem:
    """
    Swarm知识项类（适配器）

    适配测试期望的接口。
    """

    def __init__(
        self,
        key: str,
        value: Any,
        source: str = None,
        confidence: float = 1.0,
    ):
        """
        初始化知识项

        Args:
            key: 知识键
            value: 知识值
            source: 来源
            confidence: 置信度
        """
        self.key = key
        self.value = value
        self.source = source
        self.confidence = confidence


class SwarmStatistics:
    """Swarm统计信息类"""

    def __init__(self):
        """初始化统计信息"""
        self.total_tasks: int = 0
        self.completed_tasks: int = 0
        self.failed_tasks: int = 0
        self.total_agents: int = 0
        self.active_agents: int = 0
        self.average_load: float = 0.0


class SwarmSharedState:
    """
    Swarm共享状态类

    管理Swarm的共享状态，包括成员状态、知识和紧急标志。
    """

    def __init__(self):
        """初始化共享状态"""
        self.member_states: dict[str, AgentState] = {}
        self.knowledge: dict[str, Any] = {}
        self.emergency_flags: list[str] = []
        self.statistics = SwarmStatistics()

    def update_member_state(self, agent_id: str, state_dict: dict[str, Any]) -> None:
        """
        更新成员状态

        Args:
            agent_id: Agent ID
            state_dict: 状态字典
        """
        if agent_id not in self.member_states:
            # 创建新的AgentState
            self.member_states[agent_id] = AgentState(
                agent_id=agent_id,
                role=state_dict.get("role", AgentRole.WORKER),
                capabilities=state_dict.get("capabilities", []),
            )
            self.statistics.total_agents += 1
            self.statistics.active_agents += 1

        # 更新状态
        agent_state = self.member_states[agent_id]
        if "role" in state_dict:
            agent_state.role = state_dict["role"]
        if "current_load" in state_dict:
            agent_state.load = state_dict["current_load"]

    def add_knowledge(self, knowledge: Any) -> None:
        """
        添加知识

        Args:
            knowledge: 知识对象（SwarmKnowledgeItem或SharedKnowledge）
        """
        # 支持SharedKnowledge对象
        if hasattr(knowledge, "knowledge_id"):
            key = knowledge.knowledge_id
            self.knowledge[key] = knowledge
        # 支持SwarmKnowledgeItem对象（key-value格式）
        elif hasattr(knowledge, "key"):
            self.knowledge[knowledge.key] = knowledge

    def get_knowledge(self, key: str) -> Any:
        """
        获取知识

        Args:
            key: 知识键

        Returns:
            知识对象
        """
        return self.knowledge.get(key)

    def add_emergency_flag(self, flag: str) -> None:
        """
        添加紧急标志

        Args:
            flag: 紧急标志
        """
        if flag not in self.emergency_flags:
            self.emergency_flags.append(flag)
            logger.warning(f"Emergency flag added: {flag}")

    def clear_emergency_flags(self) -> None:
        """清除所有紧急标志"""
        self.emergency_flags.clear()
        logger.info("All emergency flags cleared")

    def is_emergency(self) -> bool:
        """
        检查是否处于紧急状态

        Returns:
            是否紧急
        """
        return len(self.emergency_flags) > 0
