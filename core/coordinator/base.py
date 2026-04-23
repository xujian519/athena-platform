#!/usr/bin/env python3
"""Coordinator模式基础类

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

Coordinator模式的核心实现，提供:
- Agent注册和注销
- 任务分配和负载均衡
- 优先级调度
- Agent间通信协调
- 冲突解决机制
- 状态同步管理
"""

from __future__ import annotations

import heapq
import logging
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# 枚举类型
# ============================================================================


class AgentStatus(Enum):
    """Agent状态枚举"""

    IDLE = "idle"  # 空闲
    BUSY = "busy"  # 忙碌
    OFFLINE = "offline"  # 离线
    ERROR = "error"  # 错误


class MessagePriority(IntEnum):
    """消息优先级枚举"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class ConflictType(Enum):
    """冲突类型枚举"""

    RESOURCE = "resource"  # 资源冲突
    DATA = "data"  # 数据冲突
    TIMING = "timing"  # 时序冲突
    ACCESS = "access"  # 访问冲突


class ConflictResolutionStrategy(Enum):
    """冲突解决策略枚举"""

    PRIORITY = "priority"  # 按优先级
    NEGOTIATE = "negotiate"  # 协商解决
    DEFER = "defer"  # 延迟处理
    ESCALATE = "escalate"  # 上报处理


# ============================================================================
# 配置类
# ============================================================================


@dataclass
class CoordinatorConfig:
    """Coordinator配置

    Attributes:
        max_concurrent_tasks: 最大并发任务数
        task_timeout: 任务超时时间（秒）
        heartbeat_interval: 心跳间隔（秒）
        enable_load_balancing: 是否启用负载均衡
        enable_conflict_detection: 是否启用冲突检测
        enable_state_sync: 是否启用状态同步
    """

    max_concurrent_tasks: int = 10
    task_timeout: int = 300
    heartbeat_interval: int = 30
    enable_load_balancing: bool = True
    enable_conflict_detection: bool = True
    enable_state_sync: bool = True


# ============================================================================
# Agent信息类
# ============================================================================


@dataclass
class AgentInfo:
    """Agent信息

    Attributes:
        agent_id: Agent唯一标识
        name: Agent名称
        capabilities: Agent能力列表
        max_concurrent_tasks: 最大并发任务数
        status: Agent状态
        current_tasks: 当前任务数
        completed_tasks: 已完成任务数
        priority: Agent优先级（用于冲突解决）
        metadata: 扩展元数据
        last_heartbeat: 最后心跳时间
    """

    agent_id: str
    name: str
    capabilities: list[str] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    status: AgentStatus = AgentStatus.IDLE
    current_tasks: int = 0
    completed_tasks: int = 0
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=datetime.now)

    def can_handle_task(self, task_type: str) -> bool:
        """检查是否能处理指定类型的任务

        Args:
            task_type: 任务类型

        Returns:
            bool: 是否能处理
        """
        if task_type not in self.capabilities:
            return False
        # 只检查是否达到并发上限，不检查状态（状态由current_tasks动态决定）
        if self.current_tasks >= self.max_concurrent_tasks:
            return False
        return True

    def increment_tasks(self) -> None:
        """增加当前任务数"""
        self.current_tasks += 1
        if self.current_tasks > 0:
            self.status = AgentStatus.BUSY

    def decrement_tasks(self) -> None:
        """减少当前任务数"""
        if self.current_tasks > 0:
            self.current_tasks -= 1
        if self.current_tasks == 0:
            self.status = AgentStatus.IDLE

    def update_heartbeat(self) -> None:
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()


# ============================================================================
# 消息类
# ============================================================================


@dataclass
class Message:
    """Agent间消息

    Attributes:
        message_id: 消息唯一标识
        sender: 发送者Agent ID
        receiver: 接收者Agent ID
        content: 消息内容
        priority: 消息优先级
        timestamp: 发送时间
        status: 消息状态
        metadata: 扩展元数据
    """

    message_id: str
    sender: str
    receiver: str
    content: Any
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 任务分配类
# ============================================================================


@dataclass
class TaskAssignment:
    """任务分配

    Attributes:
        task_id: 任务唯一标识
        agent_id: 分配的Agent ID
        task_type: 任务类型
        priority: 任务优先级
        payload: 任务数据
        status: 任务状态
        created_at: 创建时间
        started_at: 开始时间
        completed_at: 完成时间
        result: 任务结果
        error: 错误信息
        metadata: 扩展元数据
    """

    task_id: str
    agent_id: str
    task_type: str
    priority: int = 1
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: TaskAssignment) -> bool:
        """用于优先级队列排序（高优先级在前）"""
        return self.priority > other.priority


# ============================================================================
# 冲突信息类
# ============================================================================


@dataclass
class ConflictInfo:
    """冲突信息

    Attributes:
        conflict_id: 冲突唯一标识
        conflict_type: 冲突类型
        agents: 涉及的Agent列表
        resource_id: 涉及的资源ID
        description: 冲突描述
        status: 冲突状态
        resolution_strategy: 解决策略
        created_at: 创建时间
        resolved_at: 解决时间
    """

    conflict_id: str
    conflict_type: ConflictType
    agents: list[str]
    resource_id: Optional[str] = None
    description: str = ""
    status: str = "detected"
    resolution_strategy: ConflictResolutionStrategy | None = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: datetime | None = None


# ============================================================================
# Coordinator主类
# ============================================================================


class Coordinator:
    """Coordinator协调器

    负责多Agent系统的协调和管理。

    核心功能:
    - Agent注册和注销
    - 任务分配和负载均衡
    - 优先级调度
    - Agent间通信协调
    - 冲突解决机制
    - 状态同步管理
    """

    def __init__(self, config: CoordinatorConfig | None = None):
        """初始化Coordinator

        Args:
            config: Coordinator配置
        """
        self.config = config or CoordinatorConfig()
        self._lock = threading.RLock()

        # Agent管理
        self._agents: dict[str, AgentInfo] = {}

        # 任务管理
        self._task_queue: list[TaskAssignment] = []  # 优先级队列
        self._task_assignments: dict[str, TaskAssignment] = {}
        self._agent_tasks: dict[str, list[str]] = {}  # agent_id -> [task_ids]

        # 消息管理
        self._messages: dict[str, deque[Message]] = {}  # receiver_id -> messages

        # 冲突管理
        self._conflicts: dict[str, ConflictInfo] = {}

        # 指标统计
        self._metrics = {
            "total_tasks_submitted": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "total_messages_sent": 0,
            "total_conflicts_detected": 0,
            "total_conflicts_resolved": 0,
        }

        # 负载均衡状态
        self._last_assigned_index = 0

        logger.info("Coordinator初始化完成")

    # ========================================================================
    # Agent管理
    # ========================================================================

    def register_agent(self, agent: AgentInfo) -> bool:
        """注册Agent

        Args:
            agent: Agent信息

        Returns:
            bool: 是否成功注册
        """
        with self._lock:
            if agent.agent_id in self._agents:
                logger.warning(f"Agent {agent.agent_id} 已存在")
                return False

            self._agents[agent.agent_id] = agent
            self._messages[agent.agent_id] = deque()
            self._agent_tasks[agent.agent_id] = []

            logger.info(f"注册Agent: {agent.agent_id} - {agent.name}")
            return True

    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent

        Args:
            agent_id: Agent ID

        Returns:
            bool: 是否成功注销
        """
        with self._lock:
            if agent_id not in self._agents:
                logger.warning(f"Agent {agent_id} 不存在")
                return False

            # 取消该Agent的所有待处理任务
            if agent_id in self._agent_tasks:
                for task_id in self._agent_tasks[agent_id]:
                    if task_id in self._task_assignments:
                        assignment = self._task_assignments[task_id]
                        if assignment.status == "pending":
                            assignment.status = "cancelled"

            del self._agents[agent_id]
            if agent_id in self._messages:
                del self._messages[agent_id]
            if agent_id in self._agent_tasks:
                del self._agent_tasks[agent_id]

            logger.info(f"注销Agent: {agent_id}")
            return True

    def get_agent(self, agent_id: str) -> AgentInfo | None:
        """获取Agent信息

        Args:
            agent_id: Agent ID

        Returns:
            AgentInfo | None: Agent信息
        """
        with self._lock:
            return self._agents.get(agent_id)

    def list_agents(self) -> list[AgentInfo]:
        """列出所有Agent

        Returns:
            list[AgentInfo]: Agent列表
        """
        with self._lock:
            return list(self._agents.values())

    def get_agents_by_capability(self, capability: str) -> list[AgentInfo]:
        """按能力获取Agent

        Args:
            capability: 能力类型

        Returns:
            list[AgentInfo]: 具有该能力的Agent列表
        """
        with self._lock:
            return [
                agent
                for agent in self._agents.values()
                if capability in agent.capabilities
            ]

    # ========================================================================
    # 任务管理
    # ========================================================================

    def submit_task(
        self,
        task_id: str,
        task_type: str,
        payload: dict[str, Any],
        priority: int = 1,
    ) -> TaskAssignment | None:
        """提交任务

        Args:
            task_id: 任务ID
            task_type: 任务类型
            payload: 任务数据
            priority: 任务优先级

        Returns:
            TaskAssignment | None: 任务分配对象
        """
        with self._lock:
            # 查找能处理该任务的Agent
            capable_agents = self.get_agents_by_capability(task_type)
            if not capable_agents:
                logger.warning(f"没有Agent能处理任务类型: {task_type}")
                return None

            # 选择Agent
            agent = self._select_agent(capable_agents)
            if not agent:
                logger.warning(f"没有可用Agent处理任务: {task_id}")
                return None

            # 创建任务分配
            assignment = TaskAssignment(
                task_id=task_id,
                agent_id=agent.agent_id,
                task_type=task_type,
                priority=priority,
                payload=payload,
            )

            # 保存任务
            self._task_assignments[task_id] = assignment
            heapq.heappush(self._task_queue, assignment)
            self._agent_tasks[agent.agent_id].append(task_id)

            # 更新Agent状态
            agent.increment_tasks()

            # 更新指标
            self._metrics["total_tasks_submitted"] += 1

            logger.info(f"提交任务: {task_id} -> {agent.agent_id}")
            return assignment

    def _select_agent(self, agents: list[AgentInfo]) -> AgentInfo | None:
        """选择Agent处理任务

        Args:
            agents: 候选Agent列表

        Returns:
            AgentInfo | None: 选中的Agent
        """
        if not agents:
            return None

        # 过滤出可用的Agent（未达到并发上限）
        available = [a for a in agents if a.can_handle_task(a.capabilities[0] if a.capabilities else "")]
        if not available:
            return None

        if not self.config.enable_load_balancing:
            # 不启用负载均衡，返回第一个
            return available[0]

        # 负载均衡策略：选择当前任务最少的
        return min(available, key=lambda a: a.current_tasks)

    def get_task_assignment(self, task_id: str) -> TaskAssignment | None:
        """获取任务分配

        Args:
            task_id: 任务ID

        Returns:
            TaskAssignment | None: 任务分配对象
        """
        with self._lock:
            return self._task_assignments.get(task_id)

    def complete_task(
        self,
        task_id: str,
        agent_id: str,
        result: dict[str, Any],
    ) -> bool:
        """完成任务

        Args:
            task_id: 任务ID
            agent_id: Agent ID
            result: 任务结果

        Returns:
            bool: 是否成功
        """
        with self._lock:
            assignment = self._task_assignments.get(task_id)
            if not assignment:
                logger.warning(f"任务不存在: {task_id}")
                return False

            assignment.status = "completed"
            assignment.completed_at = datetime.now()
            assignment.result = result

            # 更新Agent状态
            agent = self._agents.get(agent_id)
            if agent:
                agent.decrement_tasks()
                agent.completed_tasks += 1

            # 更新指标
            self._metrics["total_tasks_completed"] += 1

            logger.info(f"完成任务: {task_id} by {agent_id}")
            return True

    def fail_task(self, task_id: str, agent_id: str, error: str) -> bool:
        """标记任务失败

        Args:
            task_id: 任务ID
            agent_id: Agent ID
            error: 错误信息

        Returns:
            bool: 是否成功
        """
        with self._lock:
            assignment = self._task_assignments.get(task_id)
            if not assignment:
                logger.warning(f"任务不存在: {task_id}")
                return False

            assignment.status = "failed"
            assignment.error = error

            # 更新Agent状态
            agent = self._agents.get(agent_id)
            if agent:
                agent.decrement_tasks()

            # 更新指标
            self._metrics["total_tasks_failed"] += 1

            logger.warning(f"任务失败: {task_id} - {error}")
            return True

    def get_pending_tasks(self) -> list[TaskAssignment]:
        """获取待处理任务（按优先级排序）

        Returns:
            list[TaskAssignment]: 待处理任务列表
        """
        with self._lock:
            pending = [
                t for t in self._task_assignments.values() if t.status == "pending"
            ]
            return sorted(pending, key=lambda x: x.priority, reverse=True)

    # ========================================================================
    # 通信协调
    # ========================================================================

    def send_message(
        self,
        sender: str,
        receiver: str,
        content: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> bool:
        """发送消息

        Args:
            sender: 发送者Agent ID
            receiver: 接收者Agent ID
            content: 消息内容
            priority: 消息优先级

        Returns:
            bool: 是否成功发送
        """
        with self._lock:
            if receiver not in self._agents:
                logger.warning(f"接收者不存在: {receiver}")
                return False

            message = Message(
                message_id=str(uuid.uuid4()),
                sender=sender,
                receiver=receiver,
                content=content,
                priority=priority,
            )

            self._messages[receiver].append(message)
            self._metrics["total_messages_sent"] += 1

            logger.debug(f"发送消息: {sender} -> {receiver}")
            return True

    def broadcast_message(
        self,
        sender: str,
        content: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> int:
        """广播消息

        Args:
            sender: 发送者Agent ID
            content: 消息内容
            priority: 消息优先级

        Returns:
            int: 接收者数量
        """
        with self._lock:
            count = 0
            for agent_id in self._agents:
                if agent_id != sender:
                    if self.send_message(sender, agent_id, content, priority):
                        count += 1

            logger.debug(f"广播消息: {sender} -> {count} 个接收者")
            return count

    def get_pending_messages(self, agent_id: str) -> list[Message]:
        """获取Agent的待处理消息

        Args:
            agent_id: Agent ID

        Returns:
            list[Message]: 待处理消息列表
        """
        with self._lock:
            if agent_id not in self._messages:
                return []
            return list(self._messages[agent_id])

    # ========================================================================
    # 冲突解决
    # ========================================================================

    def detect_conflict(
        self,
        conflict_type: ConflictType,
        agents: list[str],
        resource_id: Optional[str] = None,
        description: str = "",
    ) -> ConflictInfo | None:
        """检测冲突

        Args:
            conflict_type: 冲突类型
            agents: 涉及的Agent列表
            resource_id: 涉及的资源ID
            description: 冲突描述

        Returns:
            ConflictInfo | None: 冲突信息
        """
        with self._lock:
            conflict_id = str(uuid.uuid4())
            conflict = ConflictInfo(
                conflict_id=conflict_id,
                conflict_type=conflict_type,
                agents=agents,
                resource_id=resource_id,
                description=description,
            )

            self._conflicts[conflict_id] = conflict
            self._metrics["total_conflicts_detected"] += 1

            logger.warning(f"检测到冲突: {conflict_id} - {description}")
            return conflict

    def resolve_conflict(
        self,
        conflict_id: str,
        strategy: ConflictResolutionStrategy,
    ) -> bool:
        """解决冲突

        Args:
            conflict_id: 冲突ID
            strategy: 解决策略

        Returns:
            bool: 是否成功解决
        """
        with self._lock:
            conflict = self._conflicts.get(conflict_id)
            if not conflict:
                logger.warning(f"冲突不存在: {conflict_id}")
                return False

            conflict.resolution_strategy = strategy
            conflict.status = "resolved"
            conflict.resolved_at = datetime.now()

            self._metrics["total_conflicts_resolved"] += 1

            logger.info(f"解决冲突: {conflict_id} 使用策略 {strategy.value}")
            return True

    def get_active_conflicts(self) -> list[ConflictInfo]:
        """获取活跃冲突

        Returns:
            list[ConflictInfo]: 活跃冲突列表
        """
        with self._lock:
            return [c for c in self._conflicts.values() if c.status == "detected"]

    # ========================================================================
    # 状态同步
    # ========================================================================

    def get_state(self) -> dict[str, Any]:
        """获取Coordinator状态

        Returns:
            dict: 状态信息
        """
        with self._lock:
            active_agents = sum(
                1 for a in self._agents.values() if a.status == AgentStatus.IDLE
            )
            pending_tasks = sum(
                1 for t in self._task_assignments.values() if t.status == "pending"
            )

            return {
                "total_agents": len(self._agents),
                "active_agents": active_agents,
                "total_tasks": len(self._task_assignments),
                "pending_tasks": pending_tasks,
                "active_conflicts": len(self.get_active_conflicts()),
            }

    def sync_agent_state(self, agent_id: str, state: dict[str, Any]) -> bool:
        """同步Agent状态

        Args:
            agent_id: Agent ID
            state: 状态数据

        Returns:
            bool: 是否成功同步
        """
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                logger.warning(f"Agent不存在: {agent_id}")
                return False

            agent.metadata.update(state)
            agent.update_heartbeat()

            logger.debug(f"同步Agent状态: {agent_id}")
            return True

    # ========================================================================
    # 指标统计
    # ========================================================================

    def get_metrics(self) -> dict[str, int]:
        """获取指标统计

        Returns:
            dict: 指标数据
        """
        with self._lock:
            metrics = self._metrics.copy()
            metrics["total_agents"] = len(self._agents)
            return metrics


# ============================================================================
# 全局Coordinator实例
# ============================================================================

_global_coordinator: Coordinator | None = None


def get_coordinator(config: CoordinatorConfig | None = None) -> Coordinator:
    """获取全局Coordinator实例

    Args:
        config: Coordinator配置

    Returns:
        Coordinator: Coordinator实例
    """
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = Coordinator(config)
    return _global_coordinator
