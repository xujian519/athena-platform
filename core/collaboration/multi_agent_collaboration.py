#!/usr/bin/env python3
"""
多智能体协作框架核心模块
Multi-Agent Collaboration Framework Core Module

实现智能体间的协作机制,包括任务分配、通信协调、资源共享等功能
"""

import logging
import threading
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AgentStatus(Enum):
    """智能体状态枚举"""

    IDLE = "idle"  # 空闲状态
    BUSY = "busy"  # 忙碌状态
    COLLABORATING = "collaborating"  # 协作状态
    UNAVAILABLE = "unavailable"  # 不可用状态
    ERROR = "error"  # 错误状态


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待中
    ASSIGNED = "assigned"  # 已分配
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class MessageType(Enum):
    """消息类型枚举"""

    TASK_REQUEST = "task_request"  # 任务请求
    TASK_RESPONSE = "task_response"  # 任务响应
    COORDINATION = "coordination"  # 协调消息
    RESOURCE_REQUEST = "resource_request"  # 资源请求
    RESOURCE_RESPONSE = "resource_response"  # 资源响应
    STATUS_UPDATE = "status_update"  # 状态更新
    COLLABORATION_REQUEST = "collaboration_request"  # 协作请求
    COLLABORATION_RESPONSE = "collaboration_response"  # 协作响应
    HEARTBEAT = "heartbeat"  # 心跳消息
    ERROR = "error"  # 错误消息


class Priority(Enum):
    """优先级枚举"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class CollaborationStrategy(Enum):
    """协作策略枚举"""

    SEQUENTIAL = "sequential"  # 串行协作
    PARALLEL = "parallel"  # 并行协作
    HIERARCHICAL = "hierarchical"  # 层次协作
    PEER_TO_PEER = "peer_to_peer"  # 点对点协作
    PIPELINE = "pipeline"  # 流水线协作
    CONSENSUS = "consensus"  # 共识协作


class ConflictResolutionStrategy(Enum):
    """冲突解决策略枚举"""

    PRIORITY_BASED = "priority_based"  # 基于优先级
    FIRST_COME_FIRST_SERVE = "fcfs"  # 先到先服务
    LOAD_BALANCING = "load_balancing"  # 负载均衡
    NEGOTIATION = "negotiation"  # 协商解决
    ARBITRATION = "arbitration"  # 仲裁解决


@dataclass
class AgentCapability:
    """智能体能力描述"""

    name: str  # 能力名称
    description: str  # 能力描述
    max_concurrent_tasks: int = 3  # 最大并发任务数
    estimated_duration: timedelta = timedelta(minutes=30)  # 预估执行时间
    resource_requirements: dict[str, Any] = field(default_factory=dict)  # 资源需求
    dependencies: set[str] = field(default_factory=set)  # 依赖的其他能力


@dataclass
class Agent:
    """智能体实体"""

    id: str  # 智能体唯一标识
    name: str  # 智能体名称
    capabilities: list[AgentCapability] = field(default_factory=list)  # 能力列表
    status: AgentStatus = AgentStatus.IDLE  # 当前状态
    current_load: int = 0  # 当前负载
    max_load: int = 10  # 最大负载
    availability_schedule: dict[str, Any] = field(default_factory=dict)  # 可用性时间表
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据
    last_heartbeat: datetime | None = None  # 最后心跳时间

    def can_handle_task(self, task_requirements: dict[str, str]) -> bool:
        """检查是否能处理指定任务"""
        if self.status in [AgentStatus.ERROR, AgentStatus.UNAVAILABLE]:
            return False

        if self.current_load >= self.max_load:
            return False

        required_capabilities = set(task_requirements.get("capabilities", []))
        available_capabilities = {cap.name for cap in self.capabilities}

        return required_capabilities.issubset(available_capabilities)

    def calculate_suitability_score(self, task_requirements: dict[str, Any]) -> float:
        """计算对任务的适合度分数"""
        score = 0.0

        # 能力匹配度 (40%)
        required_capabilities = set(task_requirements.get("capabilities", []))
        available_capabilities = {cap.name for cap in self.capabilities}
        capability_match = len(required_capabilities & available_capabilities) / max(
            len(required_capabilities), 1
        )
        score += capability_match * 0.4

        # 负载情况 (30%)
        load_factor = (self.max_load - self.current_load) / self.max_load
        score += load_factor * 0.3

        # 状态因素 (20%)
        status_weights = {
            AgentStatus.IDLE: 1.0,
            AgentStatus.BUSY: 0.6,
            AgentStatus.COLLABORATING: 0.8,
            AgentStatus.UNAVAILABLE: 0.0,
            AgentStatus.ERROR: 0.0,
        }
        score += status_weights.get(self.status, 0) * 0.2

        # 历史表现 (10%) - 这里简化为固定值
        score += 0.1

        return min(score, 1.0)


@dataclass
class Task:
    """协作任务"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""  # 任务标题
    description: str = ""  # 任务描述
    required_capabilities: list[str] = field(default_factory=list)  # 所需能力
    priority: Priority = Priority.NORMAL  # 优先级
    status: TaskStatus = TaskStatus.PENDING  # 任务状态
    assigned_agents: list[str] = field(default_factory=list)  # 分配的智能体
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    deadline: datetime | None = None  # 截止时间
    estimated_duration: timedelta | None = None  # 预估持续时间
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他任务
    metadata: dict[str, Any] = field(default_factory=dict)  # 任务元数据
    subtasks: list["Task"] = field(default_factory=list)  # 子任务
    parent_task: str | None = None  # 父任务ID
    progress: float = 0.0  # 进度 (0.0 - 1.0)
    result: Any | None = None  # 任务结果
    error_message: str | None = None  # 错误信息

    def add_dependency(self, task_id: str) -> None:
        """添加任务依赖"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def assign_agent(self, agent_id: str) -> Any:
        """分配智能体到任务"""
        if agent_id not in self.assigned_agents:
            self.assigned_agents.append(agent_id)

    def update_progress(self, progress: float) -> None:
        """更新任务进度"""
        self.progress = max(0.0, min(1.0, progress))
        if self.progress >= 1.0:
            self.status = TaskStatus.COMPLETED

    def can_start(self, completed_tasks: set[str]) -> bool:
        """检查任务是否可以开始"""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)


@dataclass
class Message:
    """智能体间通信消息"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""  # 发送者ID
    receiver_id: str = ""  # 接收者ID
    message_type: MessageType = MessageType.TASK_REQUEST  # 消息类型
    content: dict[str, Any] = field(default_factory=dict)  # 消息内容
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    priority: Priority = Priority.NORMAL  # 优先级
    requires_response: bool = False  # 是否需要响应
    correlation_id: str | None = None  # 关联ID(用于请求-响应匹配)
    expires_at: datetime | None = None  # 过期时间
    retry_count: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数


@dataclass
class CollaborationSession:
    """协作会话"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""  # 关联任务ID
    participants: list[str] = field(default_factory=list)  # 参与者
    session_type: str = "general"  # 会话类型
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    status: str = "active"  # 会话状态
    shared_context: dict[str, Any] = field(default_factory=dict)  # 共享上下文
    messages: list[Message] = field(default_factory=list)  # 消息历史
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


class MessageBroker:
    """消息代理 - 负责智能体间的消息路由"""

    def __init__(self):
        self.message_queues: dict[str, deque] = defaultdict(deque)  # 每个智能体的消息队列
        self.subscribers: dict[str, set[str]] = defaultdict(set)  # 订阅关系
        self.message_handlers: dict[MessageType, list[Callable]] = defaultdict(list)  # 消息处理器
        self.dead_letter_queue: deque = deque()  # 死信队列
        self.message_history: list[Message] = []  # 消息历史
        self.max_queue_size = 1000  # 最大队列长度
        self.running = False
        self._lock = threading.Lock()

    def register_agent(self, agent_id: str) -> Any:
        """注册智能体"""
        with self._lock:
            if agent_id not in self.message_queues:
                self.message_queues[agent_id] = deque(maxlen=self.max_queue_size)
                logger.info(f"智能体 {agent_id} 已注册到消息代理")

    def unregister_agent(self, agent_id: str) -> Any:
        """注销智能体"""
        with self._lock:
            if agent_id in self.message_queues:
                del self.message_queues[agent_id]
            if agent_id in self.subscribers:
                del self.subscribers[agent_id]
            logger.info(f"智能体 {agent_id} 已从消息代理注销")

    def subscribe(self, agent_id: str, message_types: list[MessageType]) -> Any:
        """订阅消息类型"""
        with self._lock:
            for msg_type in message_types:
                self.subscribers[msg_type.value].add(agent_id)
        logger.info(f"智能体 {agent_id} 已订阅 {[t.value for t in message_types]}")

    def publish(self, message: Message) -> bool:
        """发布消息"""
        try:
            with self._lock:
                # 添加到消息历史
                self.message_history.append(message)

                # 检查消息是否过期
                if message.expires_at and datetime.now() > message.expires_at:
                    logger.warning(f"消息 {message.id} 已过期,移入死信队列")
                    self.dead_letter_queue.append(message)
                    return False

                # 路由消息
                if message.receiver_id:
                    # 点对点消息
                    if message.receiver_id in self.message_queues:
                        self.message_queues[message.receiver_id].append(message)
                        logger.debug(f"消息已路由到 {message.receiver_id}")
                    else:
                        logger.warning(f"接收者 {message.receiver_id} 不存在,移入死信队列")
                        self.dead_letter_queue.append(message)
                        return False
                else:
                    # 广播消息
                    message_type_subscribers = self.subscribers.get(
                        message.message_type.value, set()
                    )
                    for subscriber_id in message_type_subscribers:
                        if subscriber_id != message.sender_id:  # 不发送给自己
                            self.message_queues[subscriber_id].append(message)
                    logger.debug(f"消息已广播给 {len(message_type_subscribers)} 个订阅者")

                return True
        except Exception as e:
            logger.error(f"发布消息失败: {e}")
            return False

    def get_messages(self, agent_id: str, max_messages: int = 10) -> list[Message]:
        """获取智能体的消息"""
        with self._lock:
            messages = []
            queue = self.message_queues.get(agent_id, deque())
            while len(messages) < max_messages and queue:
                messages.append(queue.popleft())
            return messages

    def add_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """添加消息处理器"""
        self.message_handlers[message_type].append(handler)
        logger.info(f"已为 {message_type.value} 添加消息处理器")

    def start_processing(self) -> Any:
        """开始处理消息"""
        self.running = True
        logger.info("消息代理开始处理消息")

    def stop_processing(self) -> Any:
        """停止处理消息"""
        self.running = False
        logger.info("消息代理停止处理消息")


class ResourceManager:
    """资源管理器 - 管理共享资源的分配和使用"""

    def __init__(self):
        self.resources: dict[str, dict[str, Any]] = {}  # 资源池
        self.allocations: dict[str, dict[str, Any]] = {}  # 分配记录
        self.reservations: dict[str, dict[str, Any]] = {}  # 预约记录
        self.usage_history: list[dict[str, Any]] = []  # 使用历史
        self._lock = threading.Lock()

    def register_resource(self, resource_id: str, resource_spec: dict[str, Any]) -> Any:
        """注册资源"""
        with self._lock:
            self.resources[resource_id] = {
                **resource_spec,
                "available": True,
                "allocated_to": None,
                "allocated_at": None,
                "usage_count": 0,
            }
            logger.info(f"资源 {resource_id} 已注册")

    def request_resource(
        self,
        agent_id: str,
        resource_type: str,
        requirements: dict[str, Any],        duration: timedelta | None = None,
    ) -> str | None:
        """请求资源"""
        with self._lock:
            # 查找合适资源
            for resource_id, resource in self.resources.items():
                if (
                    resource.get("type") == resource_type
                    and resource.get("available")
                    and self._check_requirements(resource, requirements)
                ):

                    # 分配资源
                    resource["available"] = False
                    resource["allocated_to"] = agent_id
                    resource["allocated_at"] = datetime.now()
                    resource["usage_count"] += 1

                    # 记录分配
                    allocation_id = str(uuid.uuid4())
                    self.allocations[allocation_id] = {
                        "resource_id": resource_id,
                        "agent_id": agent_id,
                        "allocated_at": datetime.now(),
                        "duration": duration,
                        "requirements": requirements,
                    }

                    logger.info(f"资源 {resource_id} 已分配给智能体 {agent_id}")
                    return allocation_id

            logger.warning(f"无法为智能体 {agent_id} 分配 {resource_type} 资源")
            return None

    def release_resource(self, allocation_id: str) -> bool:
        """释放资源"""
        with self._lock:
            if allocation_id not in self.allocations:
                logger.warning(f"分配记录 {allocation_id} 不存在")
                return False

            allocation = self.allocations[allocation_id]
            resource_id = allocation["resource_id"]

            if resource_id in self.resources:
                self.resources[resource_id]["available"] = True
                self.resources[resource_id]["key"] = None
                self.resources[resource_id]["key"] = None

            # 移除分配记录
            del self.allocations[allocation_id]

            logger.info(f"资源 {resource_id} 已释放")
            return True

    def _check_requirements(self, resource: dict[str, str]) -> bool:
        """检查资源是否满足要求"""
        for key, required_value in requirements.items():
            if key not in resource or resource[key] < required_value:
                return False
        return True

    def get_resource_status(self) -> dict[str, Any]:
        """获取资源状态"""
        with self._lock:
            total_resources = len(self.resources)
            available_resources = sum(1 for r in self.resources.values() if r.get("available"))
            allocated_resources = total_resources - available_resources

            return {
                "total_resources": total_resources,
                "available_resources": available_resources,
                "allocated_resources": allocated_resources,
                "utilization_rate": allocated_resources / max(total_resources, 1),
                "active_allocations": len(self.allocations),
            }


class MultiAgentCollaborationFramework:
    """多智能体协作框架主类"""

    def __init__(self):
        self.agents: dict[str, Agent] = {}  # 智能体注册表
        self.tasks: dict[str, Task] = {}  # 任务注册表
        self.sessions: dict[str, CollaborationSession] = {}  # 协作会话
        self.message_broker = MessageBroker()  # 消息代理
        self.resource_manager = ResourceManager()  # 资源管理器
        self.completed_tasks: set[str] = set()  # 已完成任务
        self.task_dependencies: dict[str, list[str]] = defaultdict(list)  # 任务依赖图
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)  # 线程池
        self._setup_default_handlers()

    def _setup_default_handlers(self) -> Any:
        """设置默认消息处理器"""
        self.message_broker.add_message_handler(MessageType.TASK_REQUEST, self._handle_task_request)
        self.message_broker.add_message_handler(MessageType.COORDINATION, self._handle_coordination)
        self.message_broker.add_message_handler(MessageType.HEARTBEAT, self._handle_heartbeat)

    def register_agent(self, agent: Agent) -> bool:
        """注册智能体"""
        try:
            if agent.id in self.agents:
                logger.warning(f"智能体 {agent.id} 已存在")
                return False

            self.agents[agent.id] = agent
            self.message_broker.register_agent(agent.id)

            # 订阅相关消息类型
            self.message_broker.subscribe(
                agent.id,
                [
                    MessageType.TASK_REQUEST,
                    MessageType.COORDINATION,
                    MessageType.STATUS_UPDATE,
                    MessageType.COLLABORATION_REQUEST,
                    MessageType.HEARTBEAT,
                ],
            )

            logger.info(f"智能体 {agent.name} ({agent.id}) 注册成功")
            return True

        except Exception as e:
            logger.error(f"注册智能体失败: {e}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"智能体 {agent_id} 不存在")
                return False

            del self.agents[agent_id]
            self.message_broker.unregister_agent(agent_id)

            logger.info(f"智能体 {agent_id} 注销成功")
            return True

        except Exception as e:
            logger.error(f"注销智能体失败: {e}")
            return False

    def create_task(self, task_definition: dict[str, Any]) -> Task | None:
        """创建协作任务"""
        try:
            task = Task(
                title=task_definition.get("title", "Untitled Task"),
                description=task_definition.get("description", ""),
                required_capabilities=task_definition.get("required_capabilities", []),
                priority=Priority(task_definition.get("priority", 2)),
                deadline=(
                    datetime.fromisoformat(task_definition["deadline"])
                    if task_definition.get("deadline")
                    else None
                ),
                estimated_duration=timedelta(
                    minutes=task_definition.get("estimated_duration_minutes", 30)
                ),
                dependencies=task_definition.get("dependencies", []),
                metadata=task_definition.get("metadata", {}),
            )

            self.tasks[task.id] = task

            # 更新任务依赖图
            for dep_id in task.dependencies:
                self.task_dependencies[dep_id].append(task.id)

            logger.info(f"任务 {task.title} ({task.id}) 创建成功")
            return task

        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return None

    def assign_task(self, task_id: str, agent_ids: list[str]) -> bool:
        """分配任务给智能体"""
        try:
            if task_id not in self.tasks:
                logger.error(f"任务 {task_id} 不存在")
                return False

            task = self.tasks[task_id]

            # 检查智能体是否存在且有能力完成任务
            task_requirements = {"capabilities": task.required_capabilities}

            for agent_id in agent_ids:
                if agent_id not in self.agents:
                    logger.error(f"智能体 {agent_id} 不存在")
                    return False

                agent = self.agents[agent_id]
                if not agent.can_handle_task(task_requirements):
                    logger.error(f"智能体 {agent_id} 无法处理任务 {task_id}")
                    return False

                task.assign_agent(agent_id)
                agent.current_load += 1
                agent.status = AgentStatus.BUSY

            task.status = TaskStatus.ASSIGNED

            # 发送任务分配消息
            assignment_message = Message(
                sender_id="collaboration_framework",
                receiver_id="",
                message_type=MessageType.TASK_REQUEST,
                content={
                    "action": "task_assignment",
                    "task_id": task_id,
                    "task_data": task.__dict__,
                },
            )
            self.message_broker.publish(assignment_message)

            logger.info(f"任务 {task_id} 已分配给智能体 {agent_ids}")
            return True

        except Exception as e:
            logger.error(f"分配任务失败: {e}")
            return False

    def start_collaboration_session(
        self, task_id: str, participants: list[str], session_type: str = "general"
    ) -> str | None:
        """启动协作会话"""
        try:
            session_id = str(uuid.uuid4())

            session = CollaborationSession(
                task_id=task_id, participants=participants, session_type=session_type
            )

            self.sessions[session_id] = session

            # 发送协作邀请消息
            invitation_message = Message(
                sender_id="collaboration_framework",
                receiver_id="",
                message_type=MessageType.COLLABORATION_REQUEST,
                content={
                    "action": "session_invitation",
                    "session_id": session_id,
                    "task_id": task_id,
                    "session_type": session_type,
                },
            )
            self.message_broker.publish(invitation_message)

            logger.info(f"协作会话 {session_id} 已启动,参与者: {participants}")
            return session_id

        except Exception as e:
            logger.error(f"启动协作会话失败: {e}")
            return None

    def find_suitable_agents(
        self, task_requirements: dict[str, Any], max_agents: int = 3
    ) -> list[tuple[str, float]]:
        """查找适合处理任务的智能体"""
        suitable_agents = []

        for agent_id, agent in self.agents.items():
            if agent.can_handle_task(task_requirements):
                score = agent.calculate_suitability_score(task_requirements)
                suitable_agents.append((agent_id, score))

        # 按适合度分数排序
        suitable_agents.sort(key=lambda x: x[1], reverse=True)

        return suitable_agents[:max_agents]

    def get_framework_status(self) -> dict[str, Any]:
        """获取框架状态"""
        total_agents = len(self.agents)
        active_agents = sum(
            1 for agent in self.agents.values() if agent.status != AgentStatus.UNAVAILABLE
        )

        total_tasks = len(self.tasks)
        completed_tasks = len(self.completed_tasks)

        return {
            "agents": {
                "total": total_agents,
                "active": active_agents,
                "status_distribution": {
                    status.value: sum(1 for agent in self.agents.values() if agent.status == status)
                    for status in AgentStatus
                },
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "pending": sum(
                    1 for task in self.tasks.values() if task.status == TaskStatus.PENDING
                ),
                "in_progress": sum(
                    1 for task in self.tasks.values() if task.status == TaskStatus.IN_PROGRESS
                ),
            },
            "sessions": {
                "active": len([s for s in self.sessions.values() if s.status == "active"]),
                "total": len(self.sessions),
            },
            "resources": self.resource_manager.get_resource_status(),
            "message_broker": {
                "total_messages": len(self.message_broker.message_history),
                "dead_letter_queue_size": len(self.message_broker.dead_letter_queue),
            },
        }

    # 消息处理器
    async def _handle_task_request(self, message: Message):
        """处理任务请求消息"""
        try:
            content = message.content
            action = content.get("action")

            if action == "task_assignment":
                task_id = content.get("task_id")
                logger.info(f"处理任务分配请求: {task_id}")
                # 这里可以添加任务分配的具体逻辑

        except Exception as e:
            logger.error(f"处理任务请求消息失败: {e}")

    async def _handle_coordination(self, message: Message):
        """处理协调消息"""
        try:
            content = message.content
            coordination_type = content.get("type")

            if coordination_type == "resource_sharing":
                # 处理资源共享请求
                pass
            elif coordination_type == "status_sync":
                # 处理状态同步请求
                pass

        except Exception as e:
            logger.error(f"处理协调消息失败: {e}")

    async def _handle_heartbeat(self, message: Message):
        """处理心跳消息"""
        try:
            agent_id = message.sender_id
            if agent_id in self.agents:
                self.agents[agent_id].last_heartbeat = datetime.now()

        except Exception as e:
            logger.error(f"处理心跳消息失败: {e}")

    def start_framework(self) -> Any:
        """启动协作框架"""
        self.running = True
        self.message_broker.start_processing()
        logger.info("多智能体协作框架已启动")

    def stop_framework(self) -> Any:
        """停止协作框架"""
        self.running = False
        self.message_broker.stop_processing()
        self.executor.shutdown(wait=True)
        logger.info("多智能体协作框架已停止")
