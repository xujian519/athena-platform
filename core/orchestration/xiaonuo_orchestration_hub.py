#!/usr/bin/env python3
"""
小诺编排中枢 - 系统级智能编排引擎
Xiaonuo Orchestration Hub - System-Level Intelligent Orchestration Engine

从任务分发者升级为系统级编排中枢,具备动态任务分解、资源调度、接口网关能力

作者: 小诺·双鱼座
创建时间: 2025-12-14
版本: v1.0.0
"""
import networkx as nx

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any



class TaskType(Enum):
    """任务类型"""

    PATENT_APPLICATION = "patent_application"  # 专利申报
    MEDIA_OPERATION = "media_operation"  # 自媒体运营
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    CONTENT_CREATION = "content_creation"  # 内容创作
    LEGAL_REVIEW = "legal_review"  # 法律审查
    TECHNICAL_DEVELOPMENT = "technical_dev"  # 技术开发


class TaskPriority(Enum):
    """任务优先级"""

    CRITICAL = 3  # 紧急
    HIGH = 2  # 高
    NORMAL = 1  # 普通
    LOW = 0  # 低


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"  # 待处理
    DECOMPOSED = "decomposed"  # 已分解
    SCHEDULED = "scheduled"  # 已调度
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class AgentCapability(Enum):
    """智能体能力标签"""

    PATENT_SEARCH = "patent_search"  # 专利检索
    PATENT_WRITING = "patent_writing"  # 专利撰写
    PATENT_FILING = "patent_filing"  # 专利提交
    CONTENT_WRITING = "content_writing"  # 内容写作
    CONTENT_PUBLISHING = "content_pub"  # 内容发布
    DATA_PROCESSING = "data_processing"  # 数据处理
    LEGAL_ANALYSIS = "legal_analysis"  # 法律分析
    CODE_DEVELOPMENT = "code_dev"  # 代码开发
    GPU_COMPUTE = "gpu_compute"  # GPU计算


@dataclass
class ResourceRequirement:
    """资源需求"""

    cpu_cores: float = 1.0
    memory_gb: float = 2.0
    gpu_required: bool = False
    gpu_memory_gb: float = 0.0
    network_bandwidth: float = 100.0  # Mbps
    storage_gb: float = 10.0
    estimated_duration: float = 300.0  # 秒


@dataclass
class AgentInfo:
    """智能体信息"""

    id: str
    name: str
    capabilities: set[AgentCapability]
    max_concurrent_tasks: int = 1
    current_load: int = 0
    avg_task_duration: float = 300.0
    success_rate: float = 0.95
    resource_pool: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubTask:
    """子任务"""

    id: str
    parent_id: str
    task_type: TaskType
    title: str
    description: str
    priority: TaskPriority
    dependencies: list[str] = field(default_factory=list)
    required_capabilities: set[AgentCapability] = field(default_factory=set)
    resource_requirement: ResourceRequirement = field(default_factory=ResourceRequirement)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class Task:
    """主任务"""

    id: str
    task_type: TaskType
    title: str
    description: str
    priority: TaskPriority
    subtasks: list[SubTask] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None


class DynamicTaskDecomposer:
    """动态任务分解引擎"""

    def __init__(self):
        self.name = "小诺动态任务分解引擎"
        self.version = "1.0.0"

        # 任务分解规则库
        self.decomposition_rules = {
            TaskType.PATENT_APPLICATION: self._decompose_patent_application,
            TaskType.MEDIA_OPERATION: self._decompose_media_operation,
            TaskType.DATA_ANALYSIS: self._decompose_data_analysis,
            TaskType.CONTENT_CREATION: self._decompose_content_creation,
            TaskType.LEGAL_REVIEW: self._decompose_legal_review,
            TaskType.TECHNICAL_DEVELOPMENT: self._decompose_technical_development,
        }

        # 任务知识图谱
        self.task_knowledge_graph = nx.DiGraph()
        self._build_task_knowledge_graph()

        print(f"🧠 {self.name} 初始化完成")

    def _build_task_knowledge_graph(self) -> Any:
        """构建任务知识图谱"""
        # 添加节点
        self.task_knowledge_graph.add_nodes_from(
            [
                "专利检索",
                "技术分析",
                "权利要求设计",
                "说明书撰写",
                "附图绘制",
                "申请文件准备",
                "提交审查",
                "审查答复",
                "内容策划",
                "内容创作",
                "多媒体制作",
                "多平台发布",
                "数据收集",
                "数据清洗",
                "数据分析",
                "报告生成",
                "内容构思",
                "撰写",
                "编辑校对",
                "质量检查",
            ]
        )

        # 添加依赖关系边
        dependencies = [
            ("专利检索", "技术分析"),
            ("技术分析", "权利要求设计"),
            ("技术分析", "说明书撰写"),
            ("权利要求设计", "附图绘制"),
            ("说明书撰写", "申请文件准备"),
            ("附图绘制", "申请文件准备"),
            ("申请文件准备", "提交审查"),
            ("提交审查", "审查答复"),
            ("内容策划", "内容创作"),
            ("内容创作", "多媒体制作"),
            ("多媒体制作", "多平台发布"),
            ("数据收集", "数据清洗"),
            ("数据清洗", "数据分析"),
            ("数据分析", "报告生成"),
            ("内容构思", "撰写"),
            ("撰写", "编辑校对"),
            ("编辑校对", "质量检查"),
        ]

        self.task_knowledge_graph.add_edges_from(dependencies)

    def decompose(self, task: Task) -> list[SubTask]:
        """分解任务为子任务"""
        print(f"🔄 开始分解任务: {task.title}")

        # 获取分解策略
        decomposition_func = self.decomposition_rules.get(task.task_type)
        if not decomposition_func:
            raise ValueError(f"不支持的任务类型: {task.task_type}")

        # 执行分解
        subtasks = decomposition_func(task)

        # 更新任务状态
        task.subtasks = subtasks
        task.status = TaskStatus.DECOMPOSED

        print(f"✅ 任务分解完成,生成 {len(subtasks)} 个子任务")
        return subtasks

    def _decompose_patent_application(self, task: Task) -> list[SubTask]:
        """分解专利申报任务"""
        subtasks = [
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.PATENT_APPLICATION,
                title="现有技术检索",
                description="全面检索相关现有技术,评估专利性",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.PATENT_SEARCH},
                resource_requirement=ResourceRequirement(
                    cpu_cores=2.0, memory_gb=4.0, estimated_duration=1800.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.PATENT_APPLICATION,
                title="技术方案分析",
                description="深入分析技术创新点和保护范围",
                priority=TaskPriority.HIGH,
                required_capabilities={
                    AgentCapability.PATENT_SEARCH,
                    AgentCapability.TECHNICAL_DEVELOPMENT,
                },
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.5, memory_gb=3.0, estimated_duration=1200.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.PATENT_APPLICATION,
                title="权利要求书撰写",
                description="撰写专利权利要求书,确定保护范围",
                priority=TaskPriority.CRITICAL,
                required_capabilities={
                    AgentCapability.PATENT_WRITING,
                    AgentCapability.LEGAL_ANALYSIS,
                },
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, estimated_duration=2400.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.PATENT_APPLICATION,
                title="说明书撰写",
                description="详细撰写技术说明书和附图说明",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.PATENT_WRITING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, estimated_duration=3000.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.PATENT_APPLICATION,
                title="专利申请文件准备",
                description="整理所有申请文件,确保格式规范",
                priority=TaskPriority.NORMAL,
                required_capabilities={AgentCapability.PATENT_FILING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=0.5, memory_gb=1.0, estimated_duration=600.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.PATENT_APPLICATION,
                title="提交专利申请",
                description="向专利局正式提交申请",
                priority=TaskPriority.CRITICAL,
                required_capabilities={AgentCapability.PATENT_FILING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=0.5, memory_gb=1.0, network_bandwidth=500.0, estimated_duration=300.0
                ),
            ),
        ]

        # 设置任务依赖
        for i in range(1, len(subtasks)):
            subtasks[i].dependencies = [subtasks[i - 1].id]

        return subtasks

    def _decompose_media_operation(self, task: Task) -> list[SubTask]:
        """分解自媒体运营任务"""
        subtasks = [
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.MEDIA_OPERATION,
                title="内容策划",
                description="策划今日发布内容和主题",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.CONTENT_WRITING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, estimated_duration=600.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.MEDIA_OPERATION,
                title="内容创作",
                description="创作文章、视频或图文内容",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.CONTENT_WRITING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.5, memory_gb=3.0, estimated_duration=1800.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.MEDIA_OPERATION,
                title="多媒体制作",
                description="制作封面、视频剪辑等多媒体素材",
                priority=TaskPriority.NORMAL,
                required_capabilities={AgentCapability.CONTENT_PUBLISHING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=2.0,
                    memory_gb=4.0,
                    gpu_required=True,
                    gpu_memory_gb=4.0,
                    estimated_duration=1200.0,
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.MEDIA_OPERATION,
                title="多平台发布",
                description="在各平台发布内容并优化",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.CONTENT_PUBLISHING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, network_bandwidth=300.0, estimated_duration=900.0
                ),
            ),
        ]

        # 设置依赖关系
        subtasks[1].dependencies = [subtasks[0].id]
        subtasks[2].dependencies = [subtasks[1].id]
        subtasks[3].dependencies = [subtasks[2].id]

        return subtasks

    def _decompose_data_analysis(self, task: Task) -> list[SubTask]:
        """分解数据分析任务"""
        subtasks = [
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.DATA_ANALYSIS,
                title="数据收集",
                description="收集所需的数据源",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.DATA_PROCESSING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, storage_gb=50.0, estimated_duration=600.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.DATA_ANALYSIS,
                title="数据清洗",
                description="清洗和预处理数据",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.DATA_PROCESSING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=2.0, memory_gb=4.0, estimated_duration=1200.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.DATA_ANALYSIS,
                title="数据分析",
                description="执行深度数据分析",
                priority=TaskPriority.CRITICAL,
                required_capabilities={
                    AgentCapability.DATA_PROCESSING,
                    AgentCapability.GPU_COMPUTE,
                },
                resource_requirement=ResourceRequirement(
                    cpu_cores=4.0,
                    memory_gb=8.0,
                    gpu_required=True,
                    gpu_memory_gb=8.0,
                    estimated_duration=1800.0,
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.DATA_ANALYSIS,
                title="报告生成",
                description="生成分析报告和可视化",
                priority=TaskPriority.NORMAL,
                required_capabilities={AgentCapability.DATA_PROCESSING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, estimated_duration=900.0
                ),
            ),
        ]

        # 设置依赖
        subtasks[1].dependencies = [subtasks[0].id]
        subtasks[2].dependencies = [subtasks[1].id]
        subtasks[3].dependencies = [subtasks[2].id]

        return subtasks

    def _decompose_content_creation(self, task: Task) -> list[SubTask]:
        """分解内容创作任务"""
        return [
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.CONTENT_CREATION,
                title="内容构思",
                description="构思创作主题和框架",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.CONTENT_WRITING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, estimated_duration=300.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.CONTENT_CREATION,
                title="撰写内容",
                description="撰写完整内容",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.CONTENT_WRITING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, estimated_duration=1200.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.CONTENT_CREATION,
                title="编辑校对",
                description="编辑和校对内容",
                priority=TaskPriority.NORMAL,
                required_capabilities={AgentCapability.CONTENT_WRITING},
                resource_requirement=ResourceRequirement(
                    cpu_cores=0.5, memory_gb=1.0, estimated_duration=600.0
                ),
            ),
        ]

    def _decompose_legal_review(self, task: Task) -> list[SubTask]:
        """分解法律审查任务"""
        return [
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.LEGAL_REVIEW,
                title="法律条文检索",
                description="检索相关法律法规",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.LEGAL_ANALYSIS},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, estimated_duration=900.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.LEGAL_REVIEW,
                title="合规性分析",
                description="分析合规性问题",
                priority=TaskPriority.CRITICAL,
                required_capabilities={AgentCapability.LEGAL_ANALYSIS},
                resource_requirement=ResourceRequirement(
                    cpu_cores=2.0, memory_gb=4.0, estimated_duration=1800.0
                ),
            ),
        ]

    def _decompose_technical_development(self, task: Task) -> list[SubTask]:
        """分解技术开发任务"""
        return [
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.TECHNICAL_DEVELOPMENT,
                title="需求分析",
                description="分析技术需求",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.CODE_DEVELOPMENT},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.0, memory_gb=2.0, estimated_duration=600.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.TECHNICAL_DEVELOPMENT,
                title="代码开发",
                description="编写核心代码",
                priority=TaskPriority.CRITICAL,
                required_capabilities={AgentCapability.CODE_DEVELOPMENT},
                resource_requirement=ResourceRequirement(
                    cpu_cores=2.0, memory_gb=4.0, estimated_duration=3600.0
                ),
            ),
            SubTask(
                id=str(uuid.uuid4()),
                parent_id=task.id,
                task_type=TaskType.TECHNICAL_DEVELOPMENT,
                title="测试验证",
                description="测试和验证功能",
                priority=TaskPriority.HIGH,
                required_capabilities={AgentCapability.CODE_DEVELOPMENT},
                resource_requirement=ResourceRequirement(
                    cpu_cores=1.5, memory_gb=3.0, estimated_duration=1800.0
                ),
            ),
        ]


class ResourceAwareScheduler:
    """资源感知调度器"""

    def __init__(self):
        self.name = "小诺资源感知调度器"
        self.version = "1.0.0"

        # 智能体注册表
        self.agents: dict[str, AgentInfo] = {}

        # 资源池
        self.resource_pool = {
            "total_cpu_cores": 16.0,
            "total_memory_gb": 64.0,
            "total_gpu_count": 2,
            "total_gpu_memory_gb": 32.0,
            "total_network_bandwidth": 1000.0,
            "total_storage_gb": 1000.0,
        }

        # 当前资源使用情况
        self.current_usage = {
            "cpu_cores": 0.0,
            "memory_gb": 0.0,
            "gpu_count": 0,
            "gpu_memory_gb": 0.0,
            "network_bandwidth": 0.0,
            "storage_gb": 0.0,
        }

        # 调度策略
        self.scheduling_strategies = {
            "load_balance": self._schedule_load_balance,
            "capability_match": self._schedule_capability_match,
            "resource_optimal": self._schedule_resource_optimal,
            "priority_first": self._schedule_priority_first,
        }

        print(f"⚙️ {self.name} 初始化完成")

    def register_agent(self, agent_info: AgentInfo) -> Any:
        """注册智能体"""
        self.agents[agent_info.id] = agent_info
        print(f"✅ 注册智能体: {agent_info.name} (ID: {agent_info.id})")

    def assign_tasks(
        self, subtasks: list[SubTask], strategy: str = "resource_optimal"
    ) -> dict[str, str]:
        """分配任务给合适的智能体"""
        print(f"🎯 使用 {strategy} 策略分配 {len(subtasks)} 个子任务")

        # 获取调度策略
        schedule_func = self.scheduling_strategies.get(strategy, self._schedule_resource_optimal)

        # 执行调度
        assignments = schedule_func(subtasks)

        # 更新智能体负载
        for agent_id in assignments.values():
            if agent_id in self.agents:
                self.agents[agent_id].current_load += 1

        print("✅ 任务分配完成")
        return assignments

    def _schedule_load_balance(self, subtasks: list[SubTask]) -> dict[str, str]:
        """负载均衡调度"""
        assignments = {}

        # 按负载排序智能体
        sorted_agents = sorted(
            self.agents.items(), key=lambda x: x[1].current_load / x[1].max_concurrent_tasks
        )

        for subtask in subtasks:
            # 找到第一个有能力的智能体
            for agent_id, agent in sorted_agents:
                if (
                    subtask.required_capabilities.issubset(agent.capabilities)
                    and agent.current_load < agent.max_concurrent_tasks
                ):
                    assignments[subtask.id] = agent_id
                    break

        return assignments

    def _schedule_capability_match(self, subtasks: list[SubTask]) -> dict[str, str]:
        """能力匹配调度"""
        assignments = {}

        for subtask in subtasks:
            best_agent = None
            best_score = 0

            for agent_id, agent in self.agents.items():
                if (
                    subtask.required_capabilities.issubset(agent.capabilities)
                    and agent.current_load < agent.max_concurrent_tasks
                ):

                    # 计算匹配分数
                    capability_match = len(subtask.required_capabilities & agent.capabilities)
                    load_factor = 1 - (agent.current_load / agent.max_concurrent_tasks)
                    success_factor = agent.success_rate

                    score = capability_match * load_factor * success_factor

                    if score > best_score:
                        best_score = score
                        best_agent = agent_id

            if best_agent:
                assignments[subtask.id] = best_agent

        return assignments

    def _schedule_resource_optimal(self, subtasks: list[SubTask]) -> dict[str, str]:
        """资源最优调度"""
        assignments = {}

        # 按资源需求排序任务(高需求先调度)
        sorted_subtasks = sorted(
            subtasks,
            key=lambda x: (
                x.resource_requirement.cpu_cores,
                x.resource_requirement.memory_gb,
                x.resource_requirement.gpu_memory_gb,
            ),
            reverse=True,
        )

        for subtask in sorted_subtasks:
            best_agent = None
            min_resource_waste = float("inf")

            for agent_id, agent in self.agents.items():
                if (
                    subtask.required_capabilities.issubset(agent.capabilities)
                    and agent.current_load < agent.max_concurrent_tasks
                ):

                    # 计算资源浪费
                    req = subtask.resource_requirement
                    available = agent.resource_pool

                    waste = abs(available.get("cpu_cores", 0) - req.cpu_cores)
                    waste += abs(available.get("memory_gb", 0) - req.memory_gb)
                    waste += abs(available.get("gpu_memory_gb", 0) - req.gpu_memory_gb)

                    if waste < min_resource_waste:
                        min_resource_waste = waste
                        best_agent = agent_id

            if best_agent:
                assignments[subtask.id] = best_agent

        return assignments

    def _schedule_priority_first(self, subtasks: list[SubTask]) -> dict[str, str]:
        """优先级优先调度"""
        assignments = {}

        # 按优先级排序
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
        }

        sorted_subtasks = sorted(subtasks, key=lambda x: priority_order[x.priority])

        for subtask in sorted_subtasks:
            # 优先分配给成功率高的智能体
            capable_agents = [
                (agent_id, agent)
                for agent_id, agent in self.agents.items()
                if (
                    subtask.required_capabilities.issubset(agent.capabilities)
                    and agent.current_load < agent.max_concurrent_tasks
                )
            ]

            if capable_agents:
                # 按成功率排序
                capable_agents.sort(key=lambda x: x[1].success_rate, reverse=True)
                assignments[subtask.id] = capable_agents[0][0]

        return assignments

    def update_agent_status(self, agent_id: str, task_completed: bool) -> None:
        """更新智能体状态"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.current_load = max(0, agent.current_load - 1)

            # 更新成功率
            if task_completed:
                # 简单的指数移动平均
                agent.success_rate = 0.95 * agent.success_rate + 0.05 * 1.0
            else:
                agent.success_rate = 0.95 * agent.success_rate + 0.05 * 0.0

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        active_agents = sum(1 for agent in self.agents.values() if agent.current_load > 0)
        total_capacity = sum(agent.max_concurrent_tasks for agent in self.agents.values())
        current_load = sum(agent.current_load for agent in self.agents.values())

        return {
            "total_agents": len(self.agents),
            "active_agents": active_agents,
            "system_load": current_load / total_capacity if total_capacity > 0 else 0,
            "average_success_rate": (
                sum(agent.success_rate for agent in self.agents.values()) / len(self.agents)
                if self.agents
                else 0
            ),
            "resource_utilization": {
                k: v / self.resource_pool[f"total_{k}"] for k, v in self.current_usage.items()
            },
        }


# 导出主类
__all__ = [
    "AgentCapability",
    "AgentInfo",
    "DynamicTaskDecomposer",
    "ResourceAwareScheduler",
    "ResourceRequirement",
    "SubTask",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "TaskType",
    "XiaonuoOrchestrationHub",
]
