#!/usr/bin/env python3
from __future__ import annotations
"""
Supervisor编排器 - 多智能体Supervisor模式实现
Supervisor Orchestrator - Multi-Agent Supervisor Pattern Implementation

基于Vellum.ai和行业最佳实践,实现清晰的Supervisor模式:
- Supervisor: 小诺负责任务分解、智能体选择、结果整合
- Workers: 小娜、云熙、小宸等专注执行特定子任务

作者: 小诺·双鱼公主
创建时间: 2026-01-07
版本: v1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class TaskComplexity(Enum):
    """任务复杂度"""

    SIMPLE = "simple"  # 简单任务: 单个智能体可完成
    MODERATE = "moderate"  # 中等任务: 需要2-3个智能体协作
    COMPLEX = "complex"  # 复杂任务: 需要多个智能体深度协作
    CRITICAL = "critical"  # 关键任务: 需要HITL确认


class AgentCapability(Enum):
    """智能体能力"""

    PLATFORM_MANAGEMENT = "platform_management"  # 平台管理
    PATENT_LEGAL = "patent_legal"  # 专利法律
    IP_MANAGEMENT = "ip_management"  # IP管理
    MEDIA_OPERATION = "media_operation"  # 自媒体运营
    TECHNICAL_ANALYSIS = "technical_analysis"  # 技术分析
    DATA_PROCESSING = "data_processing"  # 数据处理


@dataclass
class AgentInfo:
    """智能体信息"""

    name: str  # 智能体名称
    agent_id: str  # 智能体ID
    capabilities: list[AgentCapability]  # 能力列表
    availability: bool = True  # 是否可用
    avg_response_time: float = 2.0  # 平均响应时间(秒)
    success_rate: float = 0.95  # 成功率
    current_load: int = 0  # 当前负载


@dataclass
class SubTask:
    """子任务"""

    task_id: str  # 任务ID
    description: str  # 任务描述
    required_capabilities: list[AgentCapability]  # 所需能力
    priority: int = 5  # 优先级(1-10)
    estimated_time: float = 60.0  # 预计耗时(秒)
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他子任务
    context: dict[str, Any] = field(default_factory=dict)  # 任务上下文
    status: str = "pending"  # 状态: pending/running/completed/failed


@dataclass
class TaskDecomposition:
    """任务分解结果"""

    original_task: str  # 原始任务
    complexity: TaskComplexity  # 任务复杂度
    subtasks: list[SubTask]  # 子任务列表
    execution_order: list[list[str]]  # 执行顺序(可并行的分组)
    estimated_total_time: float  # 预计总耗时


@dataclass
class AgentAssignment:
    """智能体分配"""

    subtask_id: str  # 子任务ID
    assigned_agent: str  # 分配的智能体
    confidence: float  # 匹配置信度(0-1)
    reason: str  # 分配理由


@dataclass
class WorkerResult:
    """Worker执行结果"""

    subtask_id: str  # 子任务ID
    agent: str  # 执行智能体
    success: bool  # 是否成功
    result: Any  # 结果数据
    error: Optional[str] = None  # 错误信息
    execution_time: float = 0.0  # 执行耗时
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class ConflictDetection:
    """冲突检测结果"""

    has_conflict: bool  # 是否有冲突
    conflict_type: str  # 冲突类型
    agents_involved: list[str]  # 涉及的智能体
    description: str  # 冲突描述
    resolution_suggestion: str  # 解决建议


class SupervisorOrchestrator:
    """
    Supervisor编排器

    核心职责:
    1. 任务分析和分解
    2. Worker智能体选择
    3. 任务协调和监控
    4. 结果整合和质量控制
    5. 冲突检测和解决
    """

    def __init__(self):
        """初始化Supervisor编排器"""
        self.version = "1.0.0"
        self.registered_agents: dict[str, AgentInfo] = {}
        self.task_history: list[dict] = []
        self.performance_metrics: dict[str, Any] = {}

        # 注册默认智能体
        self._register_default_agents()

        logger.info(f"Supervisor编排器初始化完成 (v{self.version})")

    def _register_default_agents(self) -> Any:
        """注册默认智能体"""
        # 小诺 - 平台总调度官
        self.register_agent(
            AgentInfo(
                name="小诺",
                agent_id="xiaonuo_pisces_princess",
                capabilities=[AgentCapability.PLATFORM_MANAGEMENT, AgentCapability.DATA_PROCESSING],
                avg_response_time=1.5,
                success_rate=0.98,
            )
        )

        # 小娜 - 专利法律专家
        self.register_agent(
            AgentInfo(
                name="小娜",
                agent_id="xiaona_libra",
                capabilities=[AgentCapability.PATENT_LEGAL, AgentCapability.TECHNICAL_ANALYSIS],
                avg_response_time=3.0,
                success_rate=0.95,
            )
        )


        # 小宸 - 自媒体运营
        self.register_agent(
            AgentInfo(
                name="小宸",
                agent_id="xiaochen_media",
                capabilities=[AgentCapability.MEDIA_OPERATION, AgentCapability.DATA_PROCESSING],
                avg_response_time=2.5,
                success_rate=0.94,
            )
        )

        logger.info(f"已注册 {len(self.registered_agents)} 个智能体")

    def register_agent(self, agent_info: AgentInfo) -> Any:
        """注册智能体"""
        self.registered_agents[agent_info.agent_id] = agent_info
        logger.info(f"注册智能体: {agent_info.name} ({agent_info.agent_id})")

    async def decompose_task(
        self, task_description: str, context: dict | None = None
    ) -> TaskDecomposition:
        """
        任务分解 - Superrisor核心能力

        分析任务复杂度,将复杂任务分解为可并行执行的子任务

        Args:
            task_description: 任务描述
            context: 任务上下文

        Returns:
            TaskDecomposition: 任务分解结果
        """
        logger.info(f"开始任务分解: {task_description[:100]}...")

        # 1. 分析任务复杂度
        complexity = await self._analyze_task_complexity(task_description, context or {})

        # 2. 识别所需能力
        required_capabilities = await self._identify_required_capabilities(task_description)

        # 3. 分解任务
        if complexity == TaskComplexity.SIMPLE:
            subtasks = await self._decompose_simple_task(task_description, required_capabilities)
        elif complexity == TaskComplexity.MODERATE:
            subtasks = await self._decompose_moderate_task(task_description, required_capabilities)
        elif complexity in [TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]:
            subtasks = await self._decompose_complex_task(task_description, required_capabilities)
        else:
            subtasks = []

        # 4. 确定执行顺序
        execution_order = self._determine_execution_order(subtasks)

        # 5. 估算总耗时
        total_time = sum(subtask.estimated_time for subtask in subtasks)

        decomposition = TaskDecomposition(
            original_task=task_description,
            complexity=complexity,
            subtasks=subtasks,
            execution_order=execution_order,
            estimated_total_time=total_time,
        )

        logger.info(f"任务分解完成: {complexity.value} -> {len(subtasks)}个子任务")

        return decomposition

    async def _analyze_task_complexity(self, task: str, context: dict) -> TaskComplexity:
        """分析任务复杂度"""
        # 简单任务判断标准
        simple_keywords = ["查询", "状态", "简单", "快速"]
        if any(kw in task for kw in simple_keywords):
            return TaskComplexity.SIMPLE

        # 关键任务判断标准
        critical_keywords = ["答复", "撰写", "无效", "审查意见"]
        if any(kw in task for kw in critical_keywords):
            return TaskComplexity.CRITICAL

        # 复杂任务判断标准
        complex_keywords = ["分析", "对比", "综合", "多步骤", "深度"]
        if any(kw in task for kw in complex_keywords):
            return TaskComplexity.COMPLEX

        # 默认中等复杂度
        return TaskComplexity.MODERATE

    async def _identify_required_capabilities(self, task: str) -> list[AgentCapability]:
        """识别任务所需能力"""
        capabilities = []

        # 专利法律相关
        if any(kw in task for kw in ["专利", "法律", "审查", "答复", "撰写"]):
            capabilities.append(AgentCapability.PATENT_LEGAL)

        # 技术分析相关
        if any(kw in task for kw in ["技术", "分析", "对比"]):
            capabilities.append(AgentCapability.TECHNICAL_ANALYSIS)

        # IP管理相关
        if any(kw in task for kw in ["管理", "费用", "期限", "流程"]):
            capabilities.append(AgentCapability.IP_MANAGEMENT)

        # 平台管理相关
        if any(kw in task for kw in ["服务", "启动", "停止", "监控"]):
            capabilities.append(AgentCapability.PLATFORM_MANAGEMENT)

        # 数据处理相关
        if any(kw in task for kw in ["数据", "检索", "查询", "统计"]):
            capabilities.append(AgentCapability.DATA_PROCESSING)

        # 自媒体运营相关
        if any(kw in task for kw in ["文章", "发布", "运营"]):
            capabilities.append(AgentCapability.MEDIA_OPERATION)

        return capabilities

    async def _decompose_simple_task(
        self, task: str, capabilities: list[AgentCapability]
    ) -> list[SubTask]:
        """分解简单任务"""
        return [
            SubTask(
                task_id="task_001",
                description=task,
                required_capabilities=capabilities,
                priority=5,
                estimated_time=30.0,
            )
        ]

    async def _decompose_moderate_task(
        self, task: str, capabilities: list[AgentCapability]
    ) -> list[SubTask]:
        """分解中等任务"""
        # 示例: 专利检索任务
        if AgentCapability.PATENT_LEGAL in capabilities:
            return [
                SubTask(
                    task_id="task_001",
                    description=f"理解检索需求: {task}",
                    required_capabilities=[AgentCapability.PATENT_LEGAL],
                    priority=8,
                    estimated_time=20.0,
                ),
                SubTask(
                    task_id="task_002",
                    description="执行专利检索",
                    required_capabilities=[AgentCapability.DATA_PROCESSING],
                    priority=7,
                    estimated_time=40.0,
                    dependencies=["task_001"],
                ),
                SubTask(
                    task_id="task_003",
                    description="分析检索结果",
                    required_capabilities=[AgentCapability.PATENT_LEGAL],
                    priority=6,
                    estimated_time=30.0,
                    dependencies=["task_002"],
                ),
            ]

        # 默认分解
        return [
            SubTask(
                task_id="task_001",
                description=task,
                required_capabilities=capabilities,
                priority=5,
                estimated_time=60.0,
            )
        ]

    async def _decompose_complex_task(
        self, task: str, capabilities: list[AgentCapability]
    ) -> list[SubTask]:
        """分解复杂任务"""
        # 示例: 审查意见答复任务
        if "审查意见" in task or "答复" in task:
            return [
                SubTask(
                    task_id="task_001",
                    description="解析审查意见文档",
                    required_capabilities=[AgentCapability.PATENT_LEGAL],
                    priority=10,
                    estimated_time=30.0,
                ),
                SubTask(
                    task_id="task_002",
                    description="技术解构和分析",
                    required_capabilities=[AgentCapability.TECHNICAL_ANALYSIS],
                    priority=9,
                    estimated_time=60.0,
                    dependencies=["task_001"],
                ),
                SubTask(
                    task_id="task_003",
                    description="现有技术检索",
                    required_capabilities=[AgentCapability.DATA_PROCESSING],
                    priority=8,
                    estimated_time=90.0,
                    dependencies=["task_001"],
                ),
                SubTask(
                    task_id="task_004",
                    description="创造性分析",
                    required_capabilities=[AgentCapability.PATENT_LEGAL],
                    priority=9,
                    estimated_time=60.0,
                    dependencies=["task_002", "task_003"],
                ),
                SubTask(
                    task_id="task_005",
                    description="制定答复策略",
                    required_capabilities=[AgentCapability.PATENT_LEGAL],
                    priority=8,
                    estimated_time=40.0,
                    dependencies=["task_004"],
                ),
                SubTask(
                    task_id="task_006",
                    description="撰写答复文件",
                    required_capabilities=[AgentCapability.PATENT_LEGAL],
                    priority=7,
                    estimated_time=90.0,
                    dependencies=["task_005"],
                ),
            ]

        # 默认复杂任务分解
        return [
            SubTask(
                task_id=f"task_{i:03d}",
                description=f"子任务{i}: {task}",
                required_capabilities=capabilities,
                priority=5,
                estimated_time=60.0,
            )
            for i in range(1, 4)
        ]

    def _determine_execution_order(self, subtasks: list[SubTask]) -> list[list[str]]:
        """
        确定执行顺序 - 支持并行执行

        返回可并行的任务分组
        """
        if not subtasks:
            return []

        # 构建依赖图
        dependency_graph = {}
        for subtask in subtasks:
            dependency_graph[subtask.task_id] = subtask.dependencies

        # 拓扑排序,识别可并行的任务
        order = []
        executed = set()
        remaining = {subtask.task_id for subtask in subtasks}

        while remaining:
            # 找出没有未完成依赖的任务
            ready = [
                task_id
                for task_id in remaining
                if all(dep in executed for dep in dependency_graph[task_id])
            ]

            if not ready:
                # 循环依赖,强制执行第一个
                ready = [next(iter(remaining))]

            order.append(ready)
            executed.update(ready)
            remaining -= set(ready)

        return order

    async def select_workers(self, subtask: SubTask) -> list[AgentAssignment]:
        """
        选择Worker智能体 - Superrisor核心能力

        根据子任务需求,智能选择最合适的Worker智能体

        Args:
            subtask: 子任务

        Returns:
            list[AgentAssignment]: 智能体分配列表(按优先级排序)
        """
        logger.info(f"为子任务选择Worker: {subtask.task_id}")

        assignments = []

        # 遍历所有注册的智能体
        for agent_id, agent_info in self.registered_agents.items():
            if not agent_info.availability:
                continue

            # 计算能力匹配度
            capability_match = self._calculate_capability_match(
                subtask.required_capabilities, agent_info.capabilities
            )

            if capability_match > 0:
                # 计算综合置信度
                confidence = self._calculate_assignment_confidence(
                    subtask, agent_info, capability_match
                )

                assignments.append(
                    AgentAssignment(
                        subtask_id=subtask.task_id,
                        assigned_agent=agent_id,
                        confidence=confidence,
                        reason=self._generate_assignment_reason(
                            subtask, agent_info, capability_match
                        ),
                    )
                )

        # 按置信度排序
        assignments.sort(key=lambda x: x.confidence, reverse=True)

        logger.info(f"选择了 {len(assignments)} 个候选Worker")

        return assignments

    def _calculate_capability_match(
        self, required: list[AgentCapability], available: list[AgentCapability]
    ) -> float:
        """计算能力匹配度"""
        if not required:
            return 1.0

        required_set = set(required)
        available_set = set(available)

        # 完全匹配
        if required_set.issubset(available_set):
            return 1.0

        # 部分匹配
        intersection = required_set & available_set
        return len(intersection) / len(required_set)

    def _calculate_assignment_confidence(
        self, subtask: SubTask, agent: AgentInfo, capability_match: float
    ) -> float:
        """计算分配置信度"""
        # 因素1: 能力匹配度 (50%)
        capability_score = capability_match * 0.5

        # 因素2: 成功率 (30%)
        success_score = agent.success_rate * 0.3

        # 因素3: 当前负载 (20%)
        load_score = max(0, (1 - agent.current_load / 10)) * 0.2

        return capability_score + success_score + load_score

    def _generate_assignment_reason(
        self, subtask: SubTask, agent: AgentInfo, capability_match: float
    ) -> str:
        """生成分配理由"""
        caps = ", ".join([cap.value for cap in agent.capabilities])
        return f"{agent.name}具备所需能力({caps}),匹配度{capability_match:.2%}"

    async def coordinate_workers(
        self, decomposition: TaskDecomposition, max_parallel: int = 3
    ) -> list[WorkerResult]:
        """
        协调Workers执行任务 - Superrisor核心能力

        Args:
            decomposition: 任务分解结果
            max_parallel: 最大并行数

        Returns:
            list[WorkerResult]: 所有Worker的执行结果
        """
        logger.info(f"开始协调Workers执行,共{len(decomposition.subtasks)}个子任务")

        all_results = []

        # 按执行顺序执行任务组
        for group in decomposition.execution_order:
            # 检测组内任务是否有冲突
            conflict = await self._detect_conflicts(group, decomposition.subtasks)
            if conflict.has_conflict:
                logger.warning(f"检测到冲突: {conflict.description}")
                # 应用解决建议
                group = await self._resolve_conflicts(group, conflict)

            # 并行执行任务组
            group_tasks = [
                self._execute_subtask(
                    next(st for st in decomposition.subtasks if st.task_id == task_id),
                    decomposition,
                )
                for task_id in group
            ]

            # 限制并行数
            for i in range(0, len(group_tasks), max_parallel):
                batch = group_tasks[i : i + max_parallel]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)

                # 处理结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"任务执行异常: {result}")
                    elif isinstance(result, WorkerResult):
                        all_results.append(result)

        logger.info(f"所有任务执行完成,共{len(all_results)}个结果")

        return all_results

    async def _execute_subtask(
        self, subtask: SubTask, decomposition: TaskDecomposition
    ) -> WorkerResult:
        """执行单个子任务"""
        start_time = datetime.now()

        # 选择Worker
        assignments = await self.select_workers(subtask)

        if not assignments:
            return WorkerResult(
                subtask_id=subtask.task_id,
                agent="none",
                success=False,
                result=None,
                error="没有可用的Worker智能体",
            )

        # 使用最佳匹配的Worker
        best_assignment = assignments[0]
        agent = self.registered_agents[best_assignment.assigned_agent]

        logger.info(f"执行子任务 {subtask.task_id}, 分配给: {agent.name}")

        # 模拟执行 (实际应该调用智能体的API)
        try:
            # 这里应该是实际的智能体调用
            # result = await agent.execute(subtask)

            # 模拟执行
            await asyncio.sleep(1.0)

            execution_time = (datetime.now() - start_time).total_seconds()

            return WorkerResult(
                subtask_id=subtask.task_id,
                agent=agent.name,
                success=True,
                result={"status": "completed", "data": "模拟结果"},
                execution_time=execution_time,
                metadata={
                    "assignment_confidence": best_assignment.confidence,
                    "assignment_reason": best_assignment.reason,
                },
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"子任务 {subtask.task_id} 执行失败: {e}")

            return WorkerResult(
                subtask_id=subtask.task_id,
                agent=agent.name,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
            )

    async def _detect_conflicts(
        self, task_ids: list[str], all_subtasks: list[SubTask]
    ) -> ConflictDetection:
        """检测任务冲突"""
        # 获取任务组
        tasks = [st for st in all_subtasks if st.task_id in task_ids]

        # 检测能力重叠(可能导致Coordination Drift)
        capability_sets = {}
        for _task in tasks:
            for task_id in task_ids:
                st = next((s for s in all_subtasks if s.task_id == task_id), None)
                if st:
                    caps_tuple = tuple(st.required_capabilities)
                    capability_sets.setdefault(caps_tuple, []).append(st.task_id)

        # 检查是否有能力重叠
        for _caps, related_tasks in capability_sets.items():
            if len(related_tasks) > 1:
                # 这些任务需要相同的能力,可能需要智能体协调
                return ConflictDetection(
                    has_conflict=True,
                    conflict_type="capability_overlap",
                    agents_involved=[],
                    description=f"任务 {related_tasks} 需要相同的能力,可能需要协调执行顺序",
                    resolution_suggestion="按优先级顺序执行,或分配到不同的智能体实例",
                )

        # 无冲突
        return ConflictDetection(
            has_conflict=False,
            conflict_type=None,
            agents_involved=[],
            description="无冲突",
            resolution_suggestion="",
        )

    async def _resolve_conflicts(
        self, task_ids: list[str], conflict: ConflictDetection
    ) -> list[str]:
        """解决冲突"""
        if not conflict.has_conflict:
            return task_ids

        logger.info(f"应用冲突解决策略: {conflict.resolution_suggestion}")

        # 简单策略: 按优先级排序
        # 实际应该根据冲突类型应用不同的解决策略

        return task_ids  # 简化处理

    async def integrate_results(
        self, worker_results: list[WorkerResult], original_task: str
    ) -> dict[str, Any]:
        """
        整合Worker结果 - Superrisor核心能力

        Args:
            worker_results: Worker执行结果列表
            original_task: 原始任务

        Returns:
            dict[str, Any]: 整合后的最终结果
        """
        logger.info(f"整合 {len(worker_results)} 个Worker结果")

        # 1. 分类结果
        successful_results = [r for r in worker_results if r.success]
        failed_results = [r for r in worker_results if not r.success]

        # 2. 统计
        total_time = sum(r.execution_time for r in worker_results)
        success_rate = len(successful_results) / len(worker_results) if worker_results else 0

        # 3. 整合结果数据
        integrated_data = {}
        for result in successful_results:
            if isinstance(result.result, dict):
                integrated_data.update(result.result)

        # 4. 质量检查
        quality_score = self._assess_result_quality(successful_results, failed_results)

        # 5. 生成最终报告
        final_result = {
            "original_task": original_task,
            "status": "completed" if success_rate > 0.8 else "partial",
            "success_rate": success_rate,
            "total_execution_time": total_time,
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "integrated_data": integrated_data,
            "quality_score": quality_score,
            "worker_results": [
                {
                    "subtask_id": r.subtask_id,
                    "agent": r.agent,
                    "success": r.success,
                    "execution_time": r.execution_time,
                }
                for r in worker_results
            ],
        }

        logger.info(f"结果整合完成,成功率: {success_rate:.2%},质量分数: {quality_score:.2f}")

        return final_result

    def _assess_result_quality(
        self, successful_results: list[WorkerResult], failed_results: list[WorkerResult]
    ) -> float:
        """评估结果质量 (0-1)"""
        if not successful_results and not failed_results:
            return 0.0

        # 基础分数: 成功率
        total = len(successful_results) + len(failed_results)
        success_rate = len(successful_results) / total if total > 0 else 0

        # 惩罚因子: 失败任务的影响
        failure_penalty = len(failed_results) * 0.1

        # 质量分数
        quality = max(0.0, min(1.0, success_rate - failure_penalty))

        return quality

    async def orchestrate_task(self, user_request: str, context: dict | None = None) -> dict[str, Any]:
        """
        完整的编排流程 - Superrisor模式的主入口

        步骤:
        1. 任务分析和分解
        2. 选择Worker智能体
        3. 协调执行
        4. 整合结果
        5. 质量控制

        Args:
            user_request: 用户请求
            context: 任务上下文

        Returns:
            dict[str, Any]: 最终结果
        """
        logger.info("=" * 60)
        logger.info(f"开始Supervisor编排: {user_request[:100]}...")
        logger.info("=" * 60)

        start_time = datetime.now()

        try:
            # 1. 任务分解
            decomposition = await self.decompose_task(user_request, context)

            # 2. 协调Workers执行
            worker_results = await self.coordinate_workers(decomposition)

            # 3. 整合结果
            final_result = await self.integrate_results(worker_results, user_request)

            # 4. 添加元数据
            total_time = (datetime.now() - start_time).total_seconds()
            final_result["orchestration_metadata"] = {
                "supervisor_version": self.version,
                "task_complexity": decomposition.complexity.value,
                "total_subtasks": len(decomposition.subtasks),
                "total_orchestration_time": total_time,
                "timestamp": datetime.now().isoformat(),
            }

            # 5. 记录历史
            self.task_history.append(
                {
                    "request": user_request,
                    "result": final_result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            logger.info(f"Supervisor编排完成,总耗时: {total_time:.2f}秒")
            logger.info("=" * 60)

            return final_result

        except Exception as e:
            logger.error(f"Supervisor编排失败: {e}", exc_info=True)
            return {"status": "error", "error": str(e), "original_request": user_request}


# ============================================================================
# 便捷函数
# ============================================================================

_supervisor_instance: SupervisorOrchestrator | None = None


def get_supervisor_orchestrator() -> SupervisorOrchestrator:
    """获取Supervisor编排器单例"""
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = SupervisorOrchestrator()
    return _supervisor_instance


async def orchestrate_task(user_request: str, context: dict | None = None) -> dict[str, Any]:
    """便捷函数: 编排任务"""
    supervisor = get_supervisor_orchestrator()
    return await supervisor.orchestrate_task(user_request, context)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "AgentAssignment",
    "AgentCapability",
    "AgentInfo",
    "ConflictDetection",
    "SubTask",
    "SupervisorOrchestrator",
    "TaskComplexity",
    "TaskDecomposition",
    "WorkerResult",
    "get_supervisor_orchestrator",
    "orchestrate_task",
]
