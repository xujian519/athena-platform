
from pathlib import Path

#!/usr/bin/env python3
"""
增强多智能体协作系统 (Multi-Agent Collaboration Pattern)
基于《智能体设计》多智能体协作模式的实现

功能:
- 智能体通信协议
- 任务分配和调度
- 协作会话管理
- 状态同步和冲突解决
- 负载均衡和资源管理

应用场景:
- 专利分析项目: 小娜(检索) + 小诺(分析) + 小宸(报告)协作
- 系统优化项目: 小诺(规划) + 小娜(评估) + 云熙(监控)协作
- 目标管理项目: 云熙(目标) + 小诺(执行) + 小宸(跟踪)协作
- 内容创作项目: 小娜(研究) + 小宸(创作) + 云熙(优化)协作

实施优先级: ⭐⭐⭐⭐⭐ (最高)
预期收益: 实现真正的多智能体协同工作
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """智能体角色"""

    ANALYST = "analyst"  # 分析师
    COORDINATOR = "coordinator"  # 协调者
    EXECUTOR = "executor"  # 执行者
    SPECIALIST = "specialist"  # 专家
    SUPERVISOR = "supervisor"  # 监督者
    OBSERVER = "observer"  # 观察者


class CollaborationMode(Enum):
    """协作模式"""

    HIERARCHICAL = "hierarchical"  # 层次模式
    PEER_TO_PEER = "peer_to_peer"  # 对等模式
    PIPELINE = "pipeline"  # 流水线模式
    SWARM = "swarm"  # 群体模式
    MASTER_SLAVE = "master_slave"  # 主从模式


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessagePriority(Enum):
    """消息优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentCapability:
    """智能体能力"""

    name: str
    description: str
    confidence: float  # 置信度 0-1
    max_concurrent_tasks: int
    specializations: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)


@dataclass
class AgentInfo:
    """智能体信息"""

    id: str
    name: str
    role: AgentRole
    capabilities: list[AgentCapability]
    current_load: int = 0
    max_load: int = 5
    availability_schedule: dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationTask:
    """协作任务"""

    title: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    required_capabilities: list[str] = field(default_factory=list)
    priority: int = 2
    estimated_duration: timedelta = field(default_factory=lambda: timedelta(minutes=10))
    dependencies: list[str] = field(default_factory=list)
    assigned_agents: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationMessage:
    """协作消息"""

    sender_id: str
    receiver_id: str  # None表示广播
    message_type: str  # task, status, coordination, data, etc.
    content: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    response_to: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationSession:
    """协作会话"""

    title: str
    description: str
    mode: CollaborationMode
    coordinator_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participants: list[str] = field(default_factory=list)
    tasks: list[CollaborationTask] = field(default_factory=list)
    messages: list[CollaborationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "active"
    workflow: list[str] = field(default_factory=list)


class EnhancedAgentCoordinator:
    """增强智能体协调器"""

    def __init__(self):
        # 智能体管理
        self.agents: dict[str, AgentInfo] = {}
        self.agent_capabilities: dict[str, set[str] = defaultdict(set)

        # 会话管理
        self.sessions: dict[str, CollaborationSession] = {}
        self.active_sessions: set[str] = set()

        # 消息传递
        self.message_queues: dict[str, asyncio.Queue]] = {}
        self.message_handlers: dict[str, Callable] = {}

        # 任务调度
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.task_assignments: dict[str, set[str] = defaultdict(set)
        self.agent_workloads: dict[str, int] = defaultdict(int)

        # 统计信息
        self.stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_messages": 0,
            "average_session_duration": 0,
        }

    def register_agent(self, agent_info: AgentInfo) -> bool:
        """注册智能体"""
        try:
            self.agents[agent_info.id] = agent_info

            # 更新能力索引
            self.agent_capabilities[agent_info.id]] = {cap.name for cap in agent_info.capabilities}

            # 创建消息队列
            self.message_queues[agent_info.id] = asyncio.Queue()

            logger.info(f"智能体 {agent_info.id} ({agent_info.name}) 注册成功")
            return True

        except Exception as e:
            logger.error(f"注册智能体失败: {e}")
            return False

    async def create_collaboration_session(
        self,
        title: str,
        description: str,
        mode: CollaborationMode,
        participants: list[str],
        coordinator_id: str,
        workflow: Optional[list[str]] = None,
    ) -> str:
        """创建协作会话"""
        try:
            # 验证参与者
            for agent_id in participants:
                if agent_id not in self.agents:
                    raise ValueError(f"智能体 {agent_id} 未注册")

            # 验证协调者
            if coordinator_id not in self.agents:
                raise ValueError(f"协调者 {coordinator_id} 未注册")

            session = CollaborationSession(
                title=title,
                description=description,
                mode=mode,
                participants=participants,
                coordinator_id=coordinator_id,
                workflow=workflow or [],
            )

            self.sessions[session.id] = session
            self.active_sessions.add(session.id)

            # 通知参与者
            await self._broadcast_message(
                session.id, "system", f"协作会话 '{title}' 已创建,模式: {mode.value}"
            )

            self.stats["total_sessions"] += 1
            self.stats["active_sessions"] = len(self.active_sessions)

            logger.info(f"协作会话 {session.id} 创建成功")
            return session.id

        except Exception as e:
            logger.error(f"创建协作会话失败: {e}")
            return ""

    async def add_task_to_session(self, session_id: str, task: CollaborationTask) -> bool:
        """向会话添加任务"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                logger.error(f"会话 {session_id} 不存在")
                return False

            session.tasks.append(task)
            session.status = "active"

            # 提交到任务队列
            await self.task_queue.put((-task.priority, task))
            self.stats["total_tasks"] += 1

            logger.info(f"任务 {task.id} 已添加到会话 {session_id}")
            return True

        except Exception as e:
            logger.error(f"添加任务失败: {e}")
            return False

    async def start_session(self, session_id: str) -> bool:
        """启动协作会话"""
        try:
            session = self.sessions[session_id]
            if not session:
                return False

            session.started_at = datetime.now()
            session.status = "running"

            # 根据模式启动不同的协调器
            if session.mode == CollaborationMode.HIERARCHICAL:
                await self._start_hierarchical_session(session_id)
            elif session.mode == CollaborationMode.PEER_TO_PEER:
                await self._start_peer_to_peer_session(session_id)
            elif session.mode == CollaborationMode.PIPELINE:
                await self._start_pipeline_session(session_id)
            elif session.mode == CollaborationMode.SWARM:
                await self._start_swarm_session(session_id)

            logger.info(f"协作会话 {session_id} 已启动,模式: {session.mode.value}")
            return True

        except Exception as e:
            logger.error(f"启动会话失败: {e}")
            return False

    async def _start_hierarchical_session(self, session_id: str):
        """启动层次模式会话"""
        session = self.sessions[session_id]
        self.agents[session.coordinator_id]

        # 协调者接管所有任务
        for task in session.tasks:
            await self._assign_task_to_coordinator(session_id, task)

    async def _start_peer_to_peer_session(self, session_id: str):
        """启动对等模式会话"""
        session = self.sessions[session_id]

        # 每个参与者都可以处理任务
        for task in session.tasks:
            # 找到最合适的智能体
            best_agent = await self._find_best_agent_for_task(task)
            if best_agent:
                await self._assign_task_to_agent(best_agent, task)

    async def _start_pipeline_session(self, session_id: str):
        """启动流水线模式会话"""
        session = self.sessions[session_id]

        # 按工作流顺序分配任务
        workflow = session.workflow or [task.title for task in session.tasks]

        for _i, stage in enumerate(workflow):
            matching_tasks = [task for task in session.tasks if stage in task.title.lower()]
            for task in matching_tasks:
                # 流水线中每个阶段使用专门的智能体
                agent_for_stage = await self._find_agent_for_stage(stage)
                if agent_for_stage:
                    await self._assign_task_to_agent(agent_for_stage, task)

    async def _start_swarm_session(self, session_id: str):
        """启动群体模式会话"""
        session = self.sessions[session_id]

        # 所有智能体同时工作
        for task in session.tasks:
            # 分配给多个智能体并行处理
            suitable_agents = await self._find_suitable_agents_for_task(task)
            for agent_id in suitable_agents:
                await self._assign_task_to_agent(agent_id, task)

    async def _assign_task_to_coordinator(self, session_id: str, task: CollaborationTask):
        """将任务分配给协调者"""
        session = self.sessions[session_id]
        coordinator = self.agents[session.coordinator_id]
        await self._assign_task_to_agent(coordinator.id, task)

        # 记录分配关系
        self.task_assignments[task.id].add(coordinator.id)

    async def _assign_task_to_agent(self, agent_id: str, task: CollaborationTask):
        """将任务分配给智能体"""
        try:
            agent = self.agents[agent_id]

            # 检查负载
            if agent.current_load >= agent.max_load:
                logger.warning(f"智能体 {agent_id} 已达到最大负载")
                return False

            # 分配任务
            task.assigned_agents = [agent_id]
            task.status = TaskStatus.ASSIGNED
            task.started_at = datetime.now()

            agent.current_load += 1

            # 发送任务消息
            message = CollaborationMessage(
                sender_id="coordinator",
                receiver_id=agent_id,
                message_type="task_assignment",
                content=task,
                priority=MessagePriority.HIGH,
                requires_response=True,
            )

            await self._send_message(message)
            logger.info(f"任务 {task.id} 已分配给智能体 {agent_id}")
            return True

        except Exception as e:
            logger.error(f"分配任务失败: {e}")
            return False

    async def _find_best_agent_for_task(self, task: CollaborationTask) -> Optional[str]:
        """找到最适合处理任务的智能体"""
        best_agent = None
        best_score = 0.0

        for agent_id, agent in self.agents.items():
            if agent.status != "active":
                continue

            # 检查负载
            if agent.current_load >= agent.max_load:
                continue

            # 计算匹配度
            score = self._calculate_agent_task_match(agent, task)

            if score > best_score:
                best_score = score
                best_agent = agent_id

        return best_agent

    async def _find_agent_for_stage(self, stage: str) -> Optional[str]:
        """找到处理特定阶段的智能体"""
        stage_keywords = {
            "analysis": ["analyst", "小娜"],
            "planning": ["planner", "小诺"],
            "execution": ["executor", "小宸"],
            "monitoring": ["monitor", "小娜"],
            "coordination": ["coordinator", "小诺"],
        }

        # 简化实现:基于角色和名称匹配
        stage_lower = stage.lower()
        for role, keywords in stage_keywords.items():
            if any(keyword.lower() in stage_lower for keyword in keywords):
                for agent_id, agent in self.agents.items():
                    if role.value in agent.role.value or any(
                        keyword in agent.name.lower() for keyword in keywords
                    ):
                        return agent_id

        return None

    async def _find_suitable_agents_for_task(self, task: CollaborationTask) -> list[str]:
        """找到适合处理任务的智能体列表"""
        suitable_agents = []

        for agent_id, agent in self.agents.items():
            if agent.status != "active":
                continue

            if agent.current_load < agent.max_load:
                # 检查能力匹配
                match_score = self._calculate_agent_task_match(agent, task)
                if match_score > 0.5:  # 匹配阈值
                    suitable_agents.append(agent_id)

        return suitable_agents[:3]  # 最多返回3个

    def _calculate_agent_task_match(self, agent: AgentInfo, task: CollaborationTask) -> float:
        """计算智能体与任务的匹配度"""
        score = 0.0

        # 检查能力匹配
        agent_capabilities = self.agent_capabilities.get(agent.id, set())
        required_capabilities = set(task.required_capabilities)

        capability_matches = len(agent_capabilities & required_capabilities)
        if required_capabilities:
            capability_score = capability_matches / len(required_capabilities)
            score += capability_score * 0.7

        # 检查角色匹配
        if (agent.role == AgentRole.ANALYST and "analysis" in task.title.lower()) or (agent.role == AgentRole.COORDINATOR and "coordination" in task.title.lower()) or (agent.role == AgentRole.EXECUTOR and "execution" in task.title.lower()):
            score += 0.3

        # 检查负载情况
        load_factor = (agent.max_load - agent.current_load) / agent.max_load
        score += load_factor * 0.2

        return min(score, 1.0)

    async def _send_message(self, message: CollaborationMessage):
        """发送消息"""
        try:
            if message.receiver_id:
                # 单播消息
                if message.receiver_id in self.message_queues:
                    await self.message_queues[message.receiver_id].put(message)
            else:
                # 广播消息
                for queue in self.message_queues.values():
                    await queue.put(message)

            self.stats["total_messages"] += 1
            logger.info(f"消息已发送: {message.id}")

        except Exception as e:
            logger.error(f"发送消息失败: {e}")

    async def _broadcast_message(self, session_id: str, sender: str, content: str):
        """广播消息到会话参与者"""
        session = self.sessions[session_id]
        if not session:
            return

        for participant_id in session.participants:
            if participant_id != sender:
                message = CollaborationMessage(
                    sender_id=sender,
                    receiver_id=participant_id,
                    message_type="broadcast",
                    content=content,
                    priority=MessagePriority.NORMAL,
                )
                await self._send_message(message)

    async def process_agent_response(
        self, agent_id: str, task_id: str, result: Any, status: str = "completed"
    ) -> bool:
        """处理智能体响应"""
        try:
            # 更新任务状态
            for session in self.sessions.values():
                for task in session.tasks:
                    if task.id == task_id:
                        task.result = result
                        task.status = (
                            TaskStatus.COMPLETED if status == "completed" else TaskStatus.FAILED
                        )
                        task.completed_at = datetime.now()

                        # 减少智能体负载
                        if agent_id in self.agents:
                            self.agents[agent_id].current_load -= 1

                        if status == "completed":
                            self.stats["completed_tasks"] += 1
                        else:
                            self.stats["failed_tasks"] += 1

                        logger.info(f"智能体 {agent_id} 完成任务 {task_id}: {status}")
                        return True

        except Exception as e:
            logger.error(f"处理响应失败: {e}")
            return False

    async def get_session_status(self, session_id: str) -> Optional[dict[str, Any]]:
        """获取会话状态"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        status = {
            "session_id": session.id,
            "title": session.title,
            "mode": session.mode.value,
            "status": session.status,
            "participants": session.participants,
            "coordinator": session.coordinator_id,
            "total_tasks": len(session.tasks),
            "completed_tasks": len([t for t in session.tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in session.tasks if t.status == TaskStatus.FAILED]),
            "created_at": session.created_at.isoformat(),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "active_agents": len(
                [
                    agent_id
                    for agent_id in session.participants
                    if self.agents.get(agent_id, {}).status == "active"
                ]
            ),
            "messages_count": len(session.messages),
        }

        return status

    async def complete_session(self, session_id: str) -> bool:
        """完成协作会话"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False

            session.completed_at = datetime.now()
            session.status = "completed"

            # 计算持续时间
            duration = (
                (session.completed_at - session.started_at) if session.started_at else timedelta(0)
            )

            # 更新统计信息
            if self.stats["active_sessions"] > 0:
                self.stats["active_sessions"] -= 1

            # 通知参与者
            await self._broadcast_message(
                session_id, "system", f"协作会话 '{session.title}' 已完成"
            )

            logger.info(f"会话 {session_id} 已完成,耗时: {duration}")
            return True

        except Exception as e:
            logger.error(f"完成会话失败: {e}")
            return False

    def get_coordination_statistics(self) -> dict[str, Any]:
        """获取协调统计信息"""
        total_capacity = sum(agent.max_load for agent in self.agents.values())
        current_load = sum(agent.current_load for agent in self.agents.values())

        # 计算各角色分布
        role_distribution = {}
        for agent in self.agents.values():
            role = agent.role.value
            role_distribution[role] = role_distribution.get(role, 0) + 1

        return {
            "agent_stats": {
                "total_agents": len(self.agents),
                "active_agents": len([a for a in self.agents.values() if a.status == "active"]),
                "total_capacity": total_capacity,
                "current_load": current_load,
                "utilization_rate": current_load / total_capacity if total_capacity > 0 else 0,
            },
            "role_distribution": role_distribution,
            "session_stats": self.stats,
            "active_sessions": len(self.active_sessions),
        }

    def export_session_data(self, session_id: str, export_path: str) -> bool:
        """导出会话数据"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False

            export_data = {
                "session_info": {
                    "export_time": datetime.now().isoformat(),
                    "session_id": session.id,
                    "title": session.title,
                    "description": session.description,
                    "mode": session.mode.value,
                    "participants": session.participants,
                    "coordinator": session.coordinator_id,
                    "workflow": session.workflow,
                    "created_at": session.created_at.isoformat(),
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": (
                        session.completed_at.isoformat() if session.completed_at else None
                    ),
                    "status": session.status,
                },
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority,
                        "status": task.status.value,
                        "assigned_agents": task.assigned_agents,
                        "created_at": task.created_at.isoformat(),
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": (
                            task.completed_at.isoformat() if task.completed_at else None
                        ),
                    }
                    for task in session.tasks
                ],
                "messages": [
                    {
                        "id": msg.id,
                        "sender_id": msg.sender_id,
                        "receiver_id": msg.receiver_id,
                        "message_type": msg.message_type,
                        "content": str(msg.content),
                        "priority": msg.priority.value,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in session.messages
                ],
            }

            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"会话数据已导出到: {export_path}")
            return True

        except Exception as e:
            logger.error(f"导出会话数据失败: {e}")
            return False


# 使用示例
async def example_collaboration_usage():
    """多智能体协作使用示例"""

    coordinator = EnhancedAgentCoordinator()

    # 注册智能体
    xiaonuo = AgentInfo(
        id="xiaonuo_001",
        name="小诺",
        role=AgentRole.COORDINATOR,
        capabilities=[
            AgentCapability("planning", "任务规划能力", 0.9, 3),
            AgentCapability("analysis", "系统分析能力", 0.85, 2),
        ],
        max_load=5,
    )

    xiana = AgentInfo(
        id="xiana_001",
        name="小娜",
        role=AgentRole.ANALYST,
        capabilities=[
            AgentCapability("patent_search", "专利检索能力", 0.95, 2),
            AgentCapability("document_analysis", "文档分析能力", 0.9, 3),
        ],
        max_load=3,
    )


    xiaochen = AgentInfo(
        id="xiaochen_001",
        name="小宸",
        role=AgentRole.EXECUTOR,
        capabilities=[
            AgentCapability("content_creation", "内容创建能力", 0.92, 3),
            AgentCapability("report_generation", "报告生成能力", 0.88, 2),
        ],
        max_load=3,
    )

    # 注册智能体
    coordinator.register_agent(xiaonuo)
    coordinator.register_agent(xiana)
    # yunxi - 云熙智能体 (此处应该创建但未定义，跳过注册)
    coordinator.register_agent(xiaochen)

    # 创建协作会话
    session_id = await coordinator.create_collaboration_session(
        title="专利分析协作项目",
        description="从检索到报告生成的完整专利分析流程",
        mode=CollaborationMode.HIERARCHICAL,
        participants=["xiaonuo_001", "xiana_001", "xiaochen_001"],
        coordinator_id="xiaonuo_001",
    )

    # 添加任务
    analysis_task = CollaborationTask(
        title="专利文献检索",
        description="检索相关的专利文献",
        required_capabilities=["patent_search"],
        priority=3,
        estimated_duration=timedelta(minutes=15),
    )

    evaluation_task = CollaborationTask(
        title="专利质量评估",
        description="评估检索到的专利质量",
        required_capabilities=["document_analysis"],
        priority=2,
        estimated_duration=timedelta(minutes=10),
        dependencies=["analysis_task"],
    )

    report_task = CollaborationTask(
        title="分析报告生成",
        description="基于分析结果生成专业报告",
        required_capabilities=["report_generation"],
        priority=2,
        estimated_duration=timedelta(minutes=20),
        dependencies=["evaluation_task"],
    )

    await coordinator.add_task_to_session(session_id, analysis_task)
    await coordinator.add_task_to_session(session_id, evaluation_task)
    await coordinator.add_task_to_session(session_id, report_task)

    # 启动会话
    await coordinator.start_session(session_id)

    # 等待一段时间后完成会话
    await asyncio.sleep(5)

    await coordinator.complete_session(session_id)

    # 获取统计信息
    stats = coordinator.get_coordination_statistics()
    print(f"协作统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    asyncio.run(example_collaboration_usage())

