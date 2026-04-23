from __future__ import annotations
"""
任务编排引擎 - Task Orchestration Engine

实现复杂任务的多智能体编排功能:
1. DAG任务图 - 有向无环图任务编排
2. 智能体能力路由 - 自动选择合适的智能体
3. 结果聚合和优化 - 融合多个智能体的输出
4. 任务状态管理 - 追踪任务执行状态
5. 错误处理和重试 - 容错机制
"""

import asyncio
import logging
import threading
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"  # 等待执行
    READY = "ready"  # 准备执行(依赖已完成)
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 已跳过
    CANCELLED = "cancelled"  # 已取消


class AgentType(Enum):
    """智能体类型"""

    XIAONUO = "xiaonuo"  # 小诺 - 平台调度官
    XIANA = "xiana"  # 小娜 - 专利法律专家
    XIAOCHEN = "xiaochen"  # 小宸 - 自媒体专家
    ATHENA = "athena"  # Athena - 核心智能体


class Capability(Enum):
    """能力类型"""

    PATENT_SEARCH = "patent_search"  # 专利检索
    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    PATENT_WRITING = "patent_writing"  # 专利撰写
    LEGAL_CONSULTING = "legal_consulting"  # 法律咨询
    DOCUMENT_REVIEW = "document_review"  # 文档审查
    IP_MANAGEMENT = "ip_management"  # IP管理
    CONTENT_CREATION = "content_creation"  # 内容创作
    CODING = "coding"  # 编程
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    GENERAL_CHAT = "general_chat"  # 通用对话


@dataclass
class TaskResult:
    """任务执行结果"""

    task_id: str  # 任务ID
    status: TaskStatus  # 执行状态
    result: Any = None  # 执行结果
    error: Optional[str] = None  # 错误信息
    start_time: Optional[float] = None  # 开始时间
    end_time: Optional[float] = None  # 结束时间
    duration_ms: Optional[float] = None  # 耗时(毫秒)
    agent_used: Optional[str] = None  # 使用的智能体
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "agent_used": self.agent_used,
            "metadata": self.metadata,
        }


@dataclass
class Task:
    """任务定义"""

    task_id: str  # 任务ID
    name: str  # 任务名称
    description: str  # 任务描述
    capability: Capability  # 需要的能力
    input_data: dict[str, Any]  # 输入数据
    dependencies: list[str] = field(default_factory=list)  # 依赖任务ID列表
    status: TaskStatus = TaskStatus.PENDING  # 任务状态
    priority: int = 0  # 优先级(越大越优先)
    retry_count: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数
    timeout: int = 60  # 超时时间(秒)
    result: TaskResult | None = None  # 执行结果
    agent_preference: AgentType | None = None  # 优先使用的智能体
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def can_execute(self, completed_tasks: set[str]) -> bool:
        """检查是否可以执行(所有依赖都已完成)"""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)

    def __hash__(self):
        return hash(self.task_id)

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False
        return self.task_id == other.task_id


@dataclass
class DAGWorkflow:
    """DAG工作流"""

    workflow_id: str  # 工作流ID
    name: str  # 工作流名称
    description: str  # 工作流描述
    tasks: dict[str, Task] = field(default_factory=dict)  # 任务字典 {task_id: Task}
    edges: list[tuple[str, str]] = field(default_factory=list)  # 边列表 (from_task_id, to_task_id)
    status: TaskStatus = TaskStatus.PENDING  # 工作流状态
    created_at: float = field(default_factory=time.time)  # 创建时间
    started_at: Optional[float] = None  # 开始时间
    completed_at: Optional[float] = None  # 完成时间
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks[task.task_id] = task

    def add_edge(self, from_task_id: str, to_task_id: str) -> None:
        """添加边(依赖关系)"""
        if from_task_id not in self.tasks:
            raise ValueError(f"源任务不存在: {from_task_id}")
        if to_task_id not in self.tasks:
            raise ValueError(f"目标任务不存在: {to_task_id}")

        # 添加依赖
        if to_task_id not in self.tasks[from_task_id].dependencies:
            self.tasks[from_task_id].dependencies.append(to_task_id)

        # 添加边
        self.edges.append((from_task_id, to_task_id))

        # 检查环
        if self._has_cycle():
            # 移除刚才添加的边
            self.tasks[from_task_id].dependencies.remove(to_task_id)
            self.edges.pop()
            raise ValueError(f"添加边会形成环: {from_task_id} -> {to_task_id}")

    def _has_cycle(self) -> bool:
        """检测是否有环(DFS)"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = dict.fromkeys(self.tasks, WHITE)

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in self.tasks[node].dependencies:
                if color[neighbor] == GRAY:
                    return True  # 找到环
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        return any(color[task_id] == WHITE and dfs(task_id) for task_id in self.tasks)

    def get_ready_tasks(self) -> list[Task]:
        """获取可以执行的任务(依赖已完成,状态为PENDING或READY)"""
        completed_task_ids = {
            task_id for task_id, task in self.tasks.items() if task.status == TaskStatus.COMPLETED
        }

        ready_tasks = []
        for task in self.tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.READY]:
                if task.can_execute(completed_task_ids):
                    ready_tasks.append(task)

        # 按优先级排序
        ready_tasks.sort(key=lambda t: t.priority, reverse=True)
        return ready_tasks

    def is_complete(self) -> bool:
        """检查工作流是否完成"""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED, TaskStatus.FAILED]
            for task in self.tasks.values()
        )

    def get_execution_summary(self) -> dict[str, Any]:
        """获取执行摘要"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)

        duration = None
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
        elif self.started_at:
            duration = time.time() - self.started_at

        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.value,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "progress": f"{completed_tasks}/{total_tasks}",
            "duration_seconds": duration,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class AgentRouter:
    """
    智能体路由器

    根据能力需求自动选择合适的智能体
    """

    # 智能体能力映射表
    AGENT_CAPABILITIES: dict[AgentType, set[Capability]] = {
        AgentType.XIANA: {
            Capability.PATENT_SEARCH,
            Capability.PATENT_ANALYSIS,
            Capability.PATENT_WRITING,
            Capability.LEGAL_CONSULTING,
            Capability.DOCUMENT_REVIEW,
        },
        AgentType.XIAOCHEN: {Capability.CONTENT_CREATION, Capability.GENERAL_CHAT},
        AgentType.XIAONUO: {Capability.GENERAL_CHAT, Capability.CODING, Capability.DATA_ANALYSIS},
        AgentType.ATHENA: {Capability.CODING, Capability.DATA_ANALYSIS, Capability.GENERAL_CHAT},
    }

    def __init__(self):
        """初始化路由器"""
        self.agent_health: dict[AgentType, bool] = dict.fromkeys(AgentType, True)
        self.agent_load: dict[AgentType, int] = defaultdict(int)

    def route(self, capability: Capability, preference: AgentType | None = None) -> AgentType:
        """
        路由到合适的智能体

        Args:
            capability: 需要的能力
            preference: 优先使用的智能体

        Returns:
            选中的智能体
        """
        # 如果有偏好且该智能体健康且有此能力
        if preference and self._is_agent_capable(preference, capability):
            if self.agent_health.get(preference, False):
                self.agent_load[preference] += 1
                return preference

        # 查找所有具备此能力的健康智能体
        capable_agents = [
            agent
            for agent, capabilities in self.AGENT_CAPABILITIES.items()
            if capability in capabilities and self.agent_health.get(agent, False)
        ]

        if not capable_agents:
            logger.warning(f"没有智能体具备能力: {capability}")
            # 返回默认智能体
            return AgentType.XIAONUO

        # 选择负载最低的智能体
        selected = min(capable_agents, key=lambda a: self.agent_load[a])
        self.agent_load[selected] += 1

        return selected

    def _is_agent_capable(self, agent: AgentType, capability: Capability) -> bool:
        """检查智能体是否具备某能力"""
        return capability in self.AGENT_CAPABILITIES.get(agent, set())

    def mark_agent_unhealthy(self, agent: AgentType) -> None:
        """标记智能体不健康"""
        self.agent_health[agent] = False
        logger.warning(f"智能体标记为不健康: {agent.value}")

    def mark_agent_healthy(self, agent: AgentType) -> None:
        """标记智能体健康"""
        self.agent_health[agent] = True
        logger.info(f"智能体标记为健康: {agent.value}")

    def reset_load(self, agent: AgentType) -> None:
        """重置智能体负载"""
        self.agent_load[agent] = 0

    def get_load_stats(self) -> dict[str, int]:
        """获取负载统计"""
        return {agent.value: load for agent, load in self.agent_load.items()}


class ResultAggregator:
    """
    结果聚合器

    融合多个智能体的输出结果
    """

    async def aggregate(
        self, results: list[TaskResult], aggregation_strategy: str = "first_success"
    ) -> TaskResult:
        """
        聚合多个结果

        Args:
            results: 结果列表
            aggregation_strategy: 聚合策略
                - first_success: 第一个成功的结果
                - highest_confidence: 置信度最高的结果
                - majority_vote: 多数投票
                - all: 合并所有结果

        Returns:
            聚合后的结果
        """
        if not results:
            return TaskResult(
                task_id="aggregated", status=TaskStatus.FAILED, error="没有可聚合的结果"
            )

        successful_results = [r for r in results if r.status == TaskStatus.COMPLETED]

        if not successful_results:
            return TaskResult(
                task_id="aggregated",
                status=TaskStatus.FAILED,
                error=f"所有任务都失败了: {[r.error for r in results if r.error]}",
            )

        if aggregation_strategy == "first_success":
            return successful_results[0]

        elif aggregation_strategy == "highest_confidence":
            # 选择置信度最高的结果
            def get_confidence(r: TaskResult) -> float:
                return r.metadata.get("confidence", 0.0)

            return max(successful_results, key=get_confidence)

        elif aggregation_strategy == "majority_vote":
            # 简单多数投票(适用于分类/选择类结果)
            result_counts = defaultdict(int)
            for r in successful_results:
                result_key = str(r.result)
                result_counts[result_key] += 1

            most_common = max(result_counts.items(), key=lambda x: x[1])
            for r in successful_results:
                if str(r.result) == most_common[0]:
                    return r

        elif aggregation_strategy == "all":
            # 合并所有结果
            aggregated = TaskResult(
                task_id="aggregated",
                status=TaskStatus.COMPLETED,
                result=[r.result for r in successful_results],
                metadata={
                    "aggregation_strategy": aggregation_strategy,
                    "source_count": len(successful_results),
                    "sources": [r.task_id for r in successful_results],
                },
            )
            return aggregated

        # 默认返回第一个成功结果
        return successful_results[0]


class TaskExecutor:
    """
    任务执行器

    执行单个任务,调用相应的智能体
    """

    def __init__(self, router: AgentRouter):
        """初始化执行器"""
        self.router = router
        self.executor_functions: dict[Capability, Callable] = {}

    def register_executor(self, capability: Capability, executor: Callable) -> None:
        """注册能力执行函数"""
        self.executor_functions[capability] = executor
        logger.info(f"注册执行器: {capability.value}")

    async def execute(self, task: Task) -> TaskResult:
        """
        执行任务

        Args:
            task: 要执行的任务

        Returns:
            任务结果
        """
        start_time = time.time()
        result = TaskResult(task_id=task.task_id, status=TaskStatus.RUNNING)

        try:
            # 路由到合适的智能体
            agent = self.router.route(task.capability, task.agent_preference)
            result.agent_used = agent.value

            logger.info(f"执行任务: {task.name} -> {agent.value} ({task.capability.value})")

            # 获取执行函数
            executor = self.executor_functions.get(task.capability)
            if not executor:
                raise ValueError(f"没有找到执行器: {task.capability.value}")

            # 执行任务(带超时)
            task_result = await asyncio.wait_for(
                executor(task.input_data, agent), timeout=task.timeout
            )

            result.status = TaskStatus.COMPLETED
            result.result = task_result

        except asyncio.TimeoutError:
            result.status = TaskStatus.FAILED
            result.error = f"任务超时: {task.timeout}秒"
            logger.error(f"任务超时: {task.task_id}")

        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")

        finally:
            end_time = time.time()
            result.start_time = start_time
            result.end_time = end_time
            result.duration_ms = (end_time - start_time) * 1000

        return result


class OrchestrationEngine:
    """
    任务编排引擎

    管理DAG工作流的执行
    """

    def __init__(self, max_concurrent_tasks: int = 5):
        """
        初始化编排引擎

        Args:
            max_concurrent_tasks: 最大并发任务数
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.router = AgentRouter()
        self.aggregator = ResultAggregator()
        self.executor = TaskExecutor(self.router)

        # 活跃工作流
        self.active_workflows: dict[str, DAGWorkflow] = {}

        # 工作流历史
        self.workflow_history: list[DAGWorkflow] = []

        # 最大历史记录数
        self.max_history = 1000

        # 锁
        self.lock = threading.RLock()

        logger.info("✅ 任务编排引擎初始化完成")
        logger.info(f"   最大并发任务数: {max_concurrent_tasks}")

    def create_workflow(
        self, name: str, description: str, metadata: Optional[dict[str, Any]] = None
    ) -> DAGWorkflow:
        """
        创建新工作流

        Args:
            name: 工作流名称
            description: 描述
            metadata: 元数据

        Returns:
            DAG工作流
        """
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

        workflow = DAGWorkflow(
            workflow_id=workflow_id, name=name, description=description, metadata=metadata or {}
        )

        with self.lock:
            self.active_workflows[workflow_id] = workflow

        logger.info(f"创建工作流: {workflow_id} - {name}")
        return workflow

    def register_executor(self, capability: Capability, executor: Callable) -> None:
        """注册能力执行函数"""
        self.executor.register_executor(capability, executor)

    async def execute_workflow(
        self, workflow: DAGWorkflow, stop_on_failure: bool = True
    ) -> dict[str, TaskResult]:
        """
        执行工作流

        Args:
            workflow: 要执行的工作流
            stop_on_failure: 是否在任务失败时停止

        Returns:
            所有任务的结果 {task_id: TaskResult}
        """
        logger.info(f"开始执行工作流: {workflow.workflow_id}")
        workflow.status = TaskStatus.RUNNING
        workflow.started_at = time.time()

        results: dict[str, TaskResult] = {}
        completed_tasks: set[str] = set()
        failed_tasks: list[str] = []

        # 执行循环
        while True:
            # 获取可执行的任务
            ready_tasks = workflow.get_ready_tasks()

            if not ready_tasks:
                # 没有更多可执行任务
                if workflow.is_complete():
                    break
                elif failed_tasks and stop_on_failure:
                    logger.error(f"工作流因失败而停止: {workflow.workflow_id}")
                    break
                else:
                    # 等待正在运行的任务
                    await asyncio.sleep(0.1)
                    continue

            # 限制并发数
            running_count = sum(
                1 for t in workflow.tasks.values() if t.status == TaskStatus.RUNNING
            )

            available_slots = self.max_concurrent_tasks - running_count
            if available_slots <= 0:
                await asyncio.sleep(0.1)
                continue

            # 执行任务(批量)
            tasks_to_execute = ready_tasks[:available_slots]
            execution_tasks = []

            for task in tasks_to_execute:
                task.status = TaskStatus.RUNNING
                execution_tasks.append(self.executor.execute(task))

            # 并发执行
            task_results = await asyncio.gather(*execution_tasks, return_exceptions=True)

            # 处理结果
            for task, task_result in zip(tasks_to_execute, task_results, strict=False):
                if isinstance(task_result, Exception):
                    task.status = TaskStatus.FAILED
                    failed_tasks.append(task.task_id)
                    logger.error(f"任务执行异常: {task.task_id}, {task_result}")
                else:
                    task.result = task_result
                    task.status = task_result.status

                    if task_result.status == TaskStatus.COMPLETED:
                        completed_tasks.add(task.task_id)
                    elif task_result.status == TaskStatus.FAILED:
                        failed_tasks.append(task.task_id)

                    results[task.task_id] = task_result

                    logger.info(
                        f"任务完成: {task.name} "
                        f"({task_result.status.value}) "
                        f"耗时: {task_result.duration_ms:.2f}ms"
                    )

        # 工作流完成
        workflow.completed_at = time.time()
        if failed_tasks:
            workflow.status = TaskStatus.FAILED if stop_on_failure else TaskStatus.COMPLETED
        else:
            workflow.status = TaskStatus.COMPLETED

        # 保存到历史
        with self.lock:
            self.workflow_history.append(workflow)
            if len(self.workflow_history) > self.max_history:
                self.workflow_history.pop(0)

            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]

        summary = workflow.get_execution_summary()
        logger.info(f"工作流执行完成: {workflow.workflow_id}")
        logger.info(f"   总任务数: {summary['total_tasks']}")
        logger.info(f"   完成任务: {summary['completed_tasks']}")
        logger.info(f"   失败任务: {summary['failed_tasks']}")
        logger.info(f"   总耗时: {summary['duration_seconds']:.2f}秒")

        return results

    def get_workflow_status(self, workflow_id: str) -> Optional[dict[str, Any]]:
        """获取工作流状态"""
        with self.lock:
            workflow = self.active_workflows.get(workflow_id)
            if workflow:
                return workflow.get_execution_summary()

            # 检查历史
            for wf in self.workflow_history:
                if wf.workflow_id == workflow_id:
                    return wf.get_execution_summary()

        return None

    def get_active_workflows(self) -> list[dict[str, Any]]:
        """获取所有活跃工作流"""
        with self.lock:
            return [
                {
                    "workflow_id": wf.workflow_id,
                    "name": wf.name,
                    "status": wf.status.value,
                    "progress": f"{sum(1 for t in wf.tasks.values() if t.status == TaskStatus.COMPLETED)}/{len(wf.tasks)}",
                }
                for wf in self.active_workflows.values()
            ]


# 全局单例
_orchestration_engine: OrchestrationEngine | None = None


def get_orchestration_engine() -> OrchestrationEngine:
    """获取编排引擎单例"""
    global _orchestration_engine
    if _orchestration_engine is None:
        _orchestration_engine = OrchestrationEngine()
    return _orchestration_engine


# 便捷函数
def create_task(
    name: str,
    capability: Capability,
    input_data: dict[str, Any],    description: str = "",
    dependencies: Optional[list[str]] = None,
    priority: int = 0,
    agent_preference: AgentType | None = None,
) -> Task:
    """
    创建任务

    Args:
        name: 任务名称
        capability: 需要的能力
        input_data: 输入数据
        description: 描述
        dependencies: 依赖任务ID列表
        priority: 优先级
        agent_preference: 优先使用的智能体

    Returns:
        任务对象
    """
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    return Task(
        task_id=task_id,
        name=name,
        description=description,
        capability=capability,
        input_data=input_data,
        dependencies=dependencies or [],
        priority=priority,
        agent_preference=agent_preference,
    )
