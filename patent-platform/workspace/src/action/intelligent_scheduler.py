#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能任务调度器
Intelligent Task Scheduler

基于AI算法和认知指导的智能任务调度系统，
优化专利任务的执行顺序和资源分配。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import heapq
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchedulingStrategy(str, Enum):
    """调度策略"""
    PRIORITY_FIRST = 'priority_first'
    DEPENDENCY_AWARE = 'dependency_aware'
    RESOURCE_OPTIMIZED = 'resource_optimized'
    DEADLINE_DRIVEN = 'deadline_driven'
    COGNITIVE_GUIDED = 'cognitive_guided'
    BALANCED = 'balanced'


class TaskState(str, Enum):
    """任务状态"""
    WAITING = 'waiting'
    READY = 'ready'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


@dataclass
class ResourceRequirement:
    """资源需求"""
    cpu_cores: float = 1.0
    memory_gb: float = 1.0
    disk_space_gb: float = 1.0
    network_bandwidth_mbps: float = 10.0
    gpu_required: bool = False


@dataclass
class SchedulingTask:
    """调度任务"""
    task_id: str
    priority: int = 1
    deadline: datetime | None = None
    estimated_duration: timedelta = timedelta(minutes=30)
    resource_requirements: ResourceRequirement = field(default_factory=ResourceRequirement)
    dependencies: Set[str] = field(default_factory=set)
    cognitive_score: float = 0.0  # 认知指导分数
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        # 优先级队列排序（优先级高的在前）
        return self.priority > other.priority


@dataclass
class SystemLoad:
    """系统负载"""
    cpu_usage: float = 0.0  # 0-1
    memory_usage: float = 0.0  # 0-1
    disk_usage: float = 0.0  # 0-1
    active_tasks: int = 0
    available_cores: int = 8
    available_memory_gb: float = 16.0
    available_disk_gb: float = 100.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionPlan:
    """执行计划"""
    plan_id: str
    tasks: List[SchedulingTask]
    execution_order: List[str]
    estimated_completion_time: datetime
    resource_allocation: Dict[str, ResourceRequirement]
    total_duration: timedelta
    strategy: SchedulingStrategy


class IntelligentScheduler:
    """智能任务调度器"""

    def __init__(self, max_concurrent_tasks: int = 10):
        """
        初始化智能调度器

        Args:
            max_concurrent_tasks: 最大并发任务数
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger(f"{__name__}.IntelligentScheduler")

        # 任务队列管理
        self.task_queue = []
        self.ready_queue = []
        self.running_tasks: Dict[str, SchedulingTask] = {}
        self.completed_tasks: Dict[str, SchedulingTask] = {}

        # 依赖关系图
        self.dependency_graph = nx.DiGraph()

        # 系统负载监控
        self.system_load = SystemLoad()

        # 调度统计
        self.scheduling_stats = {
            'total_scheduled': 0,
            'total_completed': 0,
            'total_failed': 0,
            'average_wait_time': 0.0,
            'average_execution_time': 0.0
        }

        # 资源预留
        self.resource_reservations: Dict[str, ResourceRequirement] = {}

        # 认知指导权重
        self.cognitive_weights = {
            'priority_weight': 0.3,
            'deadline_weight': 0.3,
            'cognitive_score_weight': 0.2,
            'resource_efficiency_weight': 0.2
        }

        self.logger.info('智能任务调度器初始化完成')

    async def schedule_tasks(self,
                           tasks: List[SchedulingTask],
                           strategy: SchedulingStrategy = SchedulingStrategy.COGNITIVE_GUIDED,
                           cognitive_context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        智能任务调度

        Args:
            tasks: 要调度的任务列表
            strategy: 调度策略
            cognitive_context: 认知上下文

        Returns:
            ExecutionPlan: 执行计划
        """
        self.logger.info(f"开始智能调度 {len(tasks)} 个任务，策略: {strategy}")

        try:
            # 构建依赖关系图
            await self._build_dependency_graph(tasks)

            # 验证依赖关系
            if not await self._validate_dependencies():
                raise ValueError('依赖关系验证失败')

            # 根据策略生成执行计划
            if strategy == SchedulingStrategy.PRIORITY_FIRST:
                plan = await self._schedule_priority_first(tasks)
            elif strategy == SchedulingStrategy.DEPENDENCY_AWARE:
                plan = await self._schedule_dependency_aware(tasks)
            elif strategy == SchedulingStrategy.RESOURCE_OPTIMIZED:
                plan = await self._schedule_resource_optimized(tasks)
            elif strategy == SchedulingStrategy.DEADLINE_DRIVEN:
                plan = await self._schedule_deadline_driven(tasks)
            elif strategy == SchedulingStrategy.COGNITIVE_GUIDED:
                plan = await self._schedule_cognitive_guided(tasks, cognitive_context)
            else:  # BALANCED
                plan = await self._schedule_balanced(tasks, cognitive_context)

            # 优化执行计划
            optimized_plan = await self._optimize_execution_plan(plan)

            self.logger.info(f"任务调度完成，预计完成时间: {optimized_plan.estimated_completion_time}")

            return optimized_plan

        except Exception as e:
            self.logger.error(f"任务调度失败: {str(e)}")
            raise

    async def _build_dependency_graph(self, tasks: List[SchedulingTask]):
        """构建依赖关系图"""
        self.dependency_graph.clear()

        # 添加节点
        for task in tasks:
            self.dependency_graph.add_node(task.task_id, task=task)

        # 添加边（依赖关系）
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in self.dependency_graph:
                    self.dependency_graph.add_edge(dep_id, task.task_id)
                else:
                    self.logger.warning(f"任务 {task.task_id} 依赖不存在的任务 {dep_id}")

        # 检查循环依赖
        if not nx.is_directed_acyclic_graph(self.dependency_graph):
            cycles = list(nx.simple_cycles(self.dependency_graph))
            raise ValueError(f"检测到循环依赖: {cycles}")

        self.logger.info(f"依赖关系图构建完成，节点数: {len(self.dependency_graph.nodes)}")

    async def _validate_dependencies(self) -> bool:
        """验证依赖关系"""
        try:
            # 检查所有任务是否在图中
            for task_id in self.dependency_graph.nodes():
                if task_id not in [t.task_id for t in self.task_queue]:
                    self.logger.warning(f"图中存在未注册的任务: {task_id}")

            return True
        except Exception as e:
            self.logger.error(f"依赖关系验证失败: {str(e)}")
            return False

    async def _schedule_priority_first(self, tasks: List[SchedulingTask]) -> ExecutionPlan:
        """优先级优先调度"""
        # 按优先级排序
        sorted_tasks = sorted(tasks, key=lambda t: (t.priority, t.deadline or datetime.max), reverse=True)

        # 考虑依赖关系生成执行顺序
        execution_order = []
        for task in sorted_tasks:
            if task.task_id not in execution_order:
                execution_order.extend(self._get_task_with_dependencies(task.task_id))

        return ExecutionPlan(
            plan_id=f"priority_{int(time.time())}",
            tasks=sorted_tasks,
            execution_order=execution_order,
            estimated_completion_time=self._calculate_completion_time(sorted_tasks, execution_order),
            resource_allocation=self._allocate_resources(sorted_tasks),
            total_duration=self._calculate_total_duration(sorted_tasks, execution_order),
            strategy=SchedulingStrategy.PRIORITY_FIRST
        )

    async def _schedule_dependency_aware(self, tasks: List[SchedulingTask]) -> ExecutionPlan:
        """依赖感知调度"""
        # 使用拓扑排序
        execution_order = list(nx.topological_sort(self.dependency_graph))

        # 按执行顺序重新组织任务
        task_map = {t.task_id: t for t in tasks}
        ordered_tasks = [task_map[tid] for tid in execution_order]

        return ExecutionPlan(
            plan_id=f"dependency_{int(time.time())}",
            tasks=ordered_tasks,
            execution_order=execution_order,
            estimated_completion_time=self._calculate_completion_time(ordered_tasks, execution_order),
            resource_allocation=self._allocate_resources(ordered_tasks),
            total_duration=self._calculate_total_duration(ordered_tasks, execution_order),
            strategy=SchedulingStrategy.DEPENDENCY_AWARE
        )

    async def _schedule_resource_optimized(self, tasks: List[SchedulingTask]) -> ExecutionPlan:
        """资源优化调度"""
        # 按资源需求分组
        resource_groups = defaultdict(list)
        for task in tasks:
            resource_key = f"{task.resource_requirements.cpu_cores}_{task.resource_requirements.memory_gb}"
            resource_groups[resource_key].append(task)

        # 优化分组内调度
        execution_order = []
        for resource_key, group_tasks in resource_groups.items():
            # 组内按优先级排序
            group_tasks.sort(key=lambda t: t.priority, reverse=True)
            for task in group_tasks:
                if task.task_id not in execution_order:
                    execution_order.extend(self._get_task_with_dependencies(task.task_id))

        task_map = {t.task_id: t for t in tasks}
        ordered_tasks = [task_map[tid] for tid in execution_order if tid in task_map]

        return ExecutionPlan(
            plan_id=f"resource_{int(time.time())}",
            tasks=ordered_tasks,
            execution_order=execution_order,
            estimated_completion_time=self._calculate_completion_time(ordered_tasks, execution_order),
            resource_allocation=self._allocate_resources(ordered_tasks),
            total_duration=self._calculate_total_duration(ordered_tasks, execution_order),
            strategy=SchedulingStrategy.RESOURCE_OPTIMIZED
        )

    async def _schedule_deadline_driven(self, tasks: List[SchedulingTask]) -> ExecutionPlan:
        """截止时间驱动调度"""
        # 计算任务的紧急程度
        now = datetime.now()
        for task in tasks:
            if task.deadline:
                time_to_deadline = (task.deadline - now).total_seconds()
                task.metadata['urgency_score'] = max(0, 100 - time_to_deadline / 3600)  # 小时为单位
            else:
                task.metadata['urgency_score'] = 0

        # 按紧急程度排序
        sorted_tasks = sorted(tasks, key=lambda t: (
            t.metadata.get('urgency_score', 0),
            t.priority
        ), reverse=True)

        execution_order = []
        for task in sorted_tasks:
            if task.task_id not in execution_order:
                execution_order.extend(self._get_task_with_dependencies(task.task_id))

        return ExecutionPlan(
            plan_id=f"deadline_{int(time.time())}",
            tasks=sorted_tasks,
            execution_order=execution_order,
            estimated_completion_time=self._calculate_completion_time(sorted_tasks, execution_order),
            resource_allocation=self._allocate_resources(sorted_tasks),
            total_duration=self._calculate_total_duration(sorted_tasks, execution_order),
            strategy=SchedulingStrategy.DEADLINE_DRIVEN
        )

    async def _schedule_cognitive_guided(self,
                                       tasks: List[SchedulingTask],
                                       cognitive_context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """认知指导调度"""
        # 应用认知指导分数
        if cognitive_context:
            await self._apply_cognitive_guidance(tasks, cognitive_context)

        # 计算综合调度分数
        for task in tasks:
            task.metadata['schedule_score'] = self._calculate_schedule_score(task)

        # 按调度分数排序
        sorted_tasks = sorted(tasks, key=lambda t: t.metadata['schedule_score'], reverse=True)

        # 智能执行顺序优化
        execution_order = await self._optimize_execution_order(sorted_tasks)

        return ExecutionPlan(
            plan_id=f"cognitive_{int(time.time())}",
            tasks=sorted_tasks,
            execution_order=execution_order,
            estimated_completion_time=self._calculate_completion_time(sorted_tasks, execution_order),
            resource_allocation=self._allocate_resources(sorted_tasks),
            total_duration=self._calculate_total_duration(sorted_tasks, execution_order),
            strategy=SchedulingStrategy.COGNITIVE_GUIDED
        )

    async def _schedule_balanced(self,
                               tasks: List[SchedulingTask],
                               cognitive_context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """平衡调度"""
        # 综合考虑多个因素
        for task in tasks:
            # 计算各项分数
            priority_score = task.priority * 20
            deadline_score = self._calculate_deadline_score(task)
            cognitive_score = task.cognitive_score * 10

            # 综合分数
            task.metadata['schedule_score'] = (
                priority_score * 0.4 +
                deadline_score * 0.3 +
                cognitive_score * 0.3
            )

        # 按综合分数排序
        sorted_tasks = sorted(tasks, key=lambda t: t.metadata['schedule_score'], reverse=True)

        # 优化执行顺序
        execution_order = await self._optimize_execution_order_balanced(sorted_tasks)

        return ExecutionPlan(
            plan_id=f"balanced_{int(time.time())}",
            tasks=sorted_tasks,
            execution_order=execution_order,
            estimated_completion_time=self._calculate_completion_time(sorted_tasks, execution_order),
            resource_allocation=self._allocate_resources(sorted_tasks),
            total_duration=self._calculate_total_duration(sorted_tasks, execution_order),
            strategy=SchedulingStrategy.BALANCED
        )

    async def _apply_cognitive_guidance(self, tasks: List[SchedulingTask], cognitive_context: Dict[str, Any]):
        """应用认知指导"""
        # 从认知上下文中提取指导信息
        guidance = cognitive_context.get('scheduling_guidance', {})

        # 应用业务优先级调整
        business_priorities = guidance.get('business_priorities', {})
        for task in tasks:
            task_type = task.metadata.get('task_type', '')
            if task_type in business_priorities:
                task.cognitive_score += business_priorities[task_type]

        # 应用相关性权重
        related_tasks = guidance.get('related_tasks', [])
        for task in tasks:
            for related in related_tasks:
                if related['task_id'] == task.task_id:
                    task.cognitive_score += related.get('relevance_score', 0)

        # 应用经验指导
        experience_insights = guidance.get('experience_insights', [])
        for insight in experience_insights:
            if insight.get('pattern') == 'sequential_execution':
                # 顺序执行模式
                sequential_tasks = insight.get('tasks', [])
                for i, task_id in enumerate(sequential_tasks):
                    for task in tasks:
                        if task.task_id == task_id:
                            task.cognitive_score += (len(sequential_tasks) - i) * 5

    def _calculate_schedule_score(self, task: SchedulingTask) -> float:
        """计算调度分数"""
        priority_score = task.priority * self.cognitive_weights['priority_weight'] * 20
        deadline_score = self._calculate_deadline_score(task) * self.cognitive_weights['deadline_weight']
        cognitive_score = task.cognitive_score * self.cognitive_weights['cognitive_score_weight'] * 10
        resource_score = self._calculate_resource_efficiency_score(task) * self.cognitive_weights['resource_efficiency_weight']

        return priority_score + deadline_score + cognitive_score + resource_score

    def _calculate_deadline_score(self, task: SchedulingTask) -> float:
        """计算截止时间分数"""
        if not task.deadline:
            return 0

        time_to_deadline = (task.deadline - datetime.now()).total_seconds()
        if time_to_deadline <= 0:
            return 100  # 已过期，最高优先级
        elif time_to_deadline <= 3600:  # 1小时内
            return 80
        elif time_to_deadline <= 86400:  # 1天内
            return 60
        elif time_to_deadline <= 604800:  # 1周内
            return 40
        else:
            return 20

    def _calculate_resource_efficiency_score(self, task: SchedulingTask) -> float:
        """计算资源效率分数"""
        # 资源需求越低，效率分数越高
        cpu_score = max(0, 100 - task.resource_requirements.cpu_cores * 10)
        memory_score = max(0, 100 - task.resource_requirements.memory_gb * 5)

        return (cpu_score + memory_score) / 2

    def _get_task_with_dependencies(self, task_id: str) -> List[str]:
        """获取任务及其所有依赖"""
        try:
            # 获取所有前置依赖
            predecessors = list(nx.ancestors(self.dependency_graph, task_id))
            predecessors.sort(key=lambda x: len(list(nx.ancestors(self.dependency_graph, x))))

            return predecessors + [task_id]
        except Exception:
            return [task_id]

    async def _optimize_execution_order(self, tasks: List[SchedulingTask]) -> List[str]:
        """优化执行顺序"""
        # 使用关键路径方法优化
        try:
            # 计算关键路径
            longest_path = nx.dag_longest_path(self.dependency_graph)

            # 识别可以并行执行的任务
            parallel_groups = []
            remaining_tasks = set(t.task_id for t in tasks)

            while remaining_tasks:
                current_level = []
                for task_id in remaining_tasks:
                    dependencies = set(self.dependency_graph.predecessors(task_id))
                    if not dependencies or dependencies.issubset(set().union(*[set(group) for group in parallel_groups])):
                        current_level.append(task_id)

                if not current_level:
                    break

                parallel_groups.append(current_level)
                remaining_tasks -= set(current_level)

            # 生成优化后的执行顺序
            execution_order = []
            for group in parallel_groups:
                # 组内按优先级排序
                task_map = {t.task_id: t for t in tasks}
                group_sorted = sorted(group, key=lambda x: task_map[x].priority, reverse=True)
                execution_order.extend(group_sorted)

            return execution_order

        except Exception as e:
            self.logger.warning(f"执行顺序优化失败: {str(e)}，使用拓扑排序")
            return list(nx.topological_sort(self.dependency_graph))

    async def _optimize_execution_order_balanced(self, tasks: List[SchedulingTask]) -> List[str]:
        """平衡的执行顺序优化"""
        # 简化版优化：按依赖关系和调度分数排序
        task_map = {t.task_id: t for t in tasks}

        # 拓扑排序
        topo_order = list(nx.topological_sort(self.dependency_graph))

        # 在依赖允许的情况下，按调度分数调整顺序
        optimized_order = []
        processed = set()

        for task_id in topo_order:
            if task_id in processed:
                continue

            # 检查是否所有依赖都已处理
            dependencies = set(self.dependency_graph.predecessors(task_id))
            if dependencies.issubset(processed):
                optimized_order.append(task_id)
                processed.add(task_id)

                # 检查是否有其他任务现在可以处理（同一级别的）
                candidates = []
                for other_id in topo_order:
                    if other_id not in processed:
                        other_deps = set(self.dependency_graph.predecessors(other_id))
                        if other_deps.issubset(processed):
                            candidates.append(other_id)

                # 候选任务按分数排序
                candidates.sort(key=lambda x: task_map[x].metadata['schedule_score'], reverse=True)
                for candidate in candidates:
                    if candidate not in processed:
                        optimized_order.append(candidate)
                        processed.add(candidate)

        return optimized_order

    def _calculate_completion_time(self,
                                 tasks: List[SchedulingTask],
                                 execution_order: List[str]) -> datetime:
        """计算完成时间"""
        if not tasks:
            return datetime.now()

        task_map = {t.task_id: t for t in tasks}

        # 并行执行计算
        current_time = datetime.now()
        resource_timeline = defaultdict(int)  # 资源释放时间

        for task_id in execution_order:
            if task_id not in task_map:
                continue

            task = task_map[task_id]

            # 计算资源就绪时间
            cpu_ready = max(resource_timeline[f"cpu_{task.resource_requirements.cpu_cores}"], current_time)
            memory_ready = max(resource_timeline[f"memory_{task.resource_requirements.memory_gb}"], current_time)

            start_time = max(cpu_ready, memory_ready)
            end_time = start_time + task.estimated_duration

            # 更新资源时间线
            resource_timeline[f"cpu_{task.resource_requirements.cpu_cores}"] = end_time
            resource_timeline[f"memory_{task.resource_requirements.memory_gb}"] = end_time

            current_time = max(current_time, end_time)

        return current_time

    def _calculate_total_duration(self,
                                tasks: List[SchedulingTask],
                                execution_order: List[str]) -> timedelta:
        """计算总执行时长"""
        if not tasks:
            return timedelta(0)

        completion_time = self._calculate_completion_time(tasks, execution_order)
        return completion_time - datetime.now()

    def _allocate_resources(self, tasks: List[SchedulingTask]) -> Dict[str, ResourceRequirement]:
        """分配资源"""
        allocation = {}

        for task in tasks:
            allocation[task.task_id] = task.resource_requirements

        return allocation

    async def _optimize_execution_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """优化执行计划"""
        # 资源负载均衡优化
        optimized_tasks = await self._balance_resource_load(plan.tasks)

        # 时间窗口优化
        optimized_tasks = await self._optimize_time_windows(optimized_tasks)

        # 生成新的执行计划
        return ExecutionPlan(
            plan_id=f"optimized_{plan.plan_id}",
            tasks=optimized_tasks,
            execution_order=plan.execution_order,
            estimated_completion_time=plan.estimated_completion_time,
            resource_allocation=plan.resource_allocation,
            total_duration=plan.total_duration,
            strategy=plan.strategy
        )

    async def _balance_resource_load(self, tasks: List[SchedulingTask]) -> List[SchedulingTask]:
        """资源负载均衡"""
        # 简单的资源均衡：将高资源需求任务分散
        high_resource_tasks = [t for t in tasks if t.resource_requirements.cpu_cores >= 4]
        normal_tasks = [t for t in tasks if t not in high_resource_tasks]

        # 交错排列
        optimized_tasks = []
        high_idx, normal_idx = 0, 0

        while high_idx < len(high_resource_tasks) or normal_idx < len(normal_tasks):
            if high_idx < len(high_resource_tasks):
                optimized_tasks.append(high_resource_tasks[high_idx])
                high_idx += 1

            if normal_idx < min(normal_idx + 2, len(normal_tasks)):
                optimized_tasks.append(normal_tasks[normal_idx])
                normal_idx += 1

        return optimized_tasks

    async def _optimize_time_windows(self, tasks: List[SchedulingTask]) -> List[SchedulingTask]:
        """时间窗口优化"""
        # 为有截止时间的任务预留时间窗口
        now = datetime.now()

        for task in tasks:
            if task.deadline and (task.deadline - now).total_seconds() < 7200:  # 2小时内
                # 提升紧急任务的优先级
                task.priority = max(task.priority, 5)
                task.metadata['time_critical'] = True

        return tasks

    def update_system_load(self, load: SystemLoad):
        """更新系统负载"""
        self.system_load = load
        self.logger.info(f"系统负载更新: CPU {load.cpu_usage:.1%}, 内存 {load.memory_usage:.1%}")

    def get_scheduling_status(self) -> Dict[str, Any]:
        """获取调度状态"""
        return {
            'strategy_weights': self.cognitive_weights,
            'system_load': {
                'cpu_usage': self.system_load.cpu_usage,
                'memory_usage': self.system_load.memory_usage,
                'active_tasks': self.system_load.active_tasks
            },
            'statistics': self.scheduling_stats,
            'queue_status': {
                'task_queue_length': len(self.task_queue),
                'ready_queue_length': len(self.ready_queue),
                'running_tasks': len(self.running_tasks),
                'completed_tasks': len(self.completed_tasks)
            }
        }

    def adjust_cognitive_weights(self, weights: Dict[str, float]):
        """调整认知权重"""
        total_weight = sum(weights.values())
        if total_weight > 0:
            # 归一化权重
            for key, value in weights.items():
                if key in self.cognitive_weights:
                    self.cognitive_weights[key] = value / total_weight

        self.logger.info(f"认知权重已调整: {self.cognitive_weights}")


# 测试代码
async def test_intelligent_scheduler():
    """测试智能调度器"""
    scheduler = IntelligentScheduler(max_concurrent_tasks=5)

    # 创建测试任务
    tasks = [
        SchedulingTask(
            task_id='task_1',
            priority=3,
            deadline=datetime.now() + timedelta(hours=2),
            estimated_duration=timedelta(minutes=30),
            cognitive_score=0.8
        ),
        SchedulingTask(
            task_id='task_2',
            priority=5,
            deadline=datetime.now() + timedelta(hours=1),
            estimated_duration=timedelta(minutes=45),
            dependencies={'task_1'},
            cognitive_score=0.9
        ),
        SchedulingTask(
            task_id='task_3',
            priority=2,
            estimated_duration=timedelta(minutes=20),
            dependencies={'task_1'},
            cognitive_score=0.6
        ),
        SchedulingTask(
            task_id='task_4',
            priority=4,
            deadline=datetime.now() + timedelta(hours=3),
            estimated_duration=timedelta(minutes=60),
            cognitive_score=0.7
        )
    ]

    # 测试不同调度策略
    strategies = [
        SchedulingStrategy.PRIORITY_FIRST,
        SchedulingStrategy.DEPENDENCY_AWARE,
        SchedulingStrategy.DEADLINE_DRIVEN,
        SchedulingStrategy.COGNITIVE_GUIDED
    ]

    for strategy in strategies:
        logger.info(f"\n测试调度策略: {strategy}")

        plan = await scheduler.schedule_tasks(tasks, strategy)

        logger.info(f"  执行顺序: {plan.execution_order}")
        logger.info(f"  预计完成时间: {plan.estimated_completion_time}")
        logger.info(f"  总执行时长: {plan.total_duration}")

    # 测试认知指导调度
    logger.info(f"\n测试认知指导调度:")
    cognitive_context = {
        'scheduling_guidance': {
            'business_priorities': {
                'patent_analysis': 0.9,
                'patent_filing': 0.8
            },
            'related_tasks': [
                {'task_id': 'task_1', 'relevance_score': 0.8}
            ],
            'experience_insights': [
                {
                    'pattern': 'sequential_execution',
                    'tasks': ['task_1', 'task_2', 'task_3']
                }
            ]
        }
    }

    plan = await scheduler.schedule_tasks(tasks, SchedulingStrategy.COGNITIVE_GUIDED, cognitive_context)
    logger.info(f"  认知指导执行顺序: {plan.execution_order}")

    # 获取调度状态
    status = scheduler.get_scheduling_status()
    logger.info(f"\n调度器状态: {status}")


if __name__ == '__main__':
    asyncio.run(test_intelligent_scheduler())