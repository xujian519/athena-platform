#!/usr/bin/env python3
from __future__ import annotations
"""
HTN层次规划器 (Hierarchical Task Network Planner)
实现分层任务网络规划算法

核心思想:
1. 目标分解:将复杂目标分解为子任务
2. 层次组织:形成任务层次结构
3. 依赖分析:识别任务间依赖关系
4. 执行计划:生成可执行的计划序列

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """任务定义"""

    task_id: str
    name: str
    description: str
    task_type: str  # 操作类型
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 3  # 1-5,5最高
    estimated_duration: float = 1.0  # 分钟
    assignee: Optional[str] = None
    result: Any | None = None
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "subtasks": self.subtasks,
            "status": self.status.value,
            "priority": self.priority,
            "estimated_duration": self.estimated_duration,
            "assignee": self.assignee,
            "result": str(self.result) if self.result else None,
            "error": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """从字典创建"""
        return cls(
            task_id=data["task_id"],
            name=data["name"],
            description=data["description"],
            task_type=data["task_type"],
            parameters=data.get("parameters", {}),
            dependencies=data.get("dependencies", []),
            subtasks=data.get("subtasks", []),
            status=TaskStatus(data.get("status", "pending")),
            priority=data.get("priority", 3),
            estimated_duration=data.get("estimated_duration", 1.0),
            assignee=data.get("assignee"),
            result=data.get("result"),
            error_message=data.get("error"),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )


@dataclass
class ExecutionPlan:
    """执行计划"""

    plan_id: str
    goal: str
    tasks: dict[str, Task]  # 所有任务
    execution_order: list[str]  # 执行顺序(任务ID列表)
    total_duration: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "execution_order": self.execution_order,
            "total_duration": self.total_duration,
            "created_at": self.created_at,
        }


class HierarchicalPlanner:
    """
    HTN层次规划器

    实现分层任务网络规划:
    1. 目标分解:递归分解复杂目标
    2. 依赖分析:识别任务依赖关系
    3. 排序调度:确定执行顺序
    4. 资源分配:分配任务给Agent
    """

    def __init__(self):
        """初始化规划器"""
        self._task_templates = self._load_task_templates()
        self.stats = {
            "total_plans": 0,
            "successful_plans": 0,
            "failed_plans": 0,
            "avg_tasks_per_plan": 0.0,
        }

    def _load_task_templates(self) -> dict[str, dict[str, Any]]:
        """加载任务模板"""
        return {
            "专利检索": {
                "subtasks": ["关键词提取", "数据库查询", "结果筛选"],
                "estimated_duration": 5.0,
            },
            "专利分析": {
                "subtasks": ["技术理解", "新颖性分析", "创造性评估"],
                "estimated_duration": 10.0,
            },
            "专利申请": {
                "subtasks": ["撰写权利要求", "撰写说明书", "形式审查"],
                "estimated_duration": 30.0,
            },
            "文献调研": {
                "subtasks": ["搜索策略制定", "文献检索", "综述撰写"],
                "estimated_duration": 15.0,
            },
        }

    async def plan(
        self,
        goal: str,
        context: Optional[dict[str, Any]] = None,
        available_agents: Optional[list[str]] = None,
        max_depth: int = 3,
    ) -> ExecutionPlan:
        """
        生成执行计划

        Args:
            goal: 目标描述
            context: 上下文信息
            available_agents: 可用Agent列表
            max_depth: 最大分解深度

        Returns:
            执行计划
        """
        logger.info(f"📋 开始规划: {goal[:100]}...")

        context = context or {}
        available_agents = available_agents or ["xiaonuo_main"]

        # 生成计划ID
        plan_id = f"plan_{int(time.time() * 1000)}_{hashlib.md5(goal.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"

        # 创建任务字典
        tasks = {}

        # 第1步:分解目标为根任务
        root_task = await self._decompose_goal(goal, context, f"{plan_id}_root")
        tasks[root_task.task_id] = root_task

        # 第2步:递归分解子任务
        await self._decompose_recursively(
            root_task, tasks, context, max_depth=max_depth, current_depth=1
        )

        # 第3步:分析依赖关系
        await self._analyze_dependencies(tasks)

        # 第4步:确定执行顺序(拓扑排序)
        execution_order = self._topological_sort(tasks)

        # 第5步:分配Agent
        await self._assign_agents(tasks, available_agents)

        # 第6步:计算总时间
        total_duration = sum(
            tasks[task_id].estimated_duration for task_id in execution_order if task_id in tasks
        )

        plan = ExecutionPlan(
            plan_id=plan_id,
            goal=goal,
            tasks=tasks,
            execution_order=execution_order,
            total_duration=total_duration,
        )

        # 更新统计
        self.stats["total_plans"] += 1
        self.stats["avg_tasks_per_plan"] = (
            self.stats["avg_tasks_per_plan"] * (self.stats["total_plans"] - 1) + len(tasks)
        ) / self.stats["total_plans"]

        logger.info(f"✅ 规划完成: {len(tasks)}个任务, 预计{total_duration:.1f}分钟")

        return plan

    async def _decompose_goal(self, goal: str, context: dict[str, Any], parent_id: str) -> Task:
        """分解目标为任务"""
        # 分析目标类型
        task_type = await self._identify_task_type(goal, context)

        # 检查是否有模板
        template = self._find_matching_template(goal)

        if template:
            # 使用模板
            return Task(
                task_id=parent_id,
                name=goal[:50],
                description=goal,
                task_type=task_type,
                subtasks=[],  # 将在递归分解中填充
                priority=3,
                estimated_duration=template.get("estimated_duration", 5.0),
            )
        else:
            # 原子任务
            return Task(
                task_id=parent_id,
                name=goal[:50],
                description=goal,
                task_type=task_type,
                parameters={"goal": goal},
                priority=3,
                estimated_duration=1.0,
            )

    async def _decompose_recursively(
        self,
        parent_task: Task,
        tasks: dict[str, Task],
        context: dict[str, Any],        max_depth: int,
        current_depth: int,
    ):
        """递归分解任务"""
        if current_depth >= max_depth:
            return

        # 查找模板
        template = self._find_matching_template(parent_task.description)

        if template and "subtasks" in template:
            # 创建子任务
            for i, subtask_desc in enumerate(template["subtasks"]):
                subtask_id = f"{parent_task.task_id}_sub{i}"
                subtask = Task(
                    task_id=subtask_id,
                    name=subtask_desc[:30],
                    description=subtask_desc,
                    task_type="subtask",
                    dependencies=[parent_task.task_id],
                    priority=parent_task.priority,
                    estimated_duration=1.0,
                )
                tasks[subtask_id] = subtask
                parent_task.subtasks.append(subtask_id)

                # 递归分解子任务
                await self._decompose_recursively(
                    subtask, tasks, context, max_depth, current_depth + 1
                )

    async def _identify_task_type(self, goal: str, context: dict[str, Any]) -> str:
        """识别任务类型"""
        goal_lower = goal.lower()

        if "专利" in goal_lower and "检索" in goal_lower:
            return "patent_search"
        elif "专利" in goal_lower and "分析" in goal_lower:
            return "patent_analysis"
        elif "申请" in goal_lower:
            return "patent_application"
        elif "文献" in goal_lower or "调研" in goal_lower:
            return "literature_review"
        else:
            return "general_task"

    def _find_matching_template(self, goal: str) -> Optional[dict[str, Any]]:
        """查找匹配的任务模板"""
        for template_name, template in self._task_templates.items():
            if template_name in goal:
                return template
        return None

    async def _analyze_dependencies(self, tasks: dict[str, Task]):
        """分析任务依赖关系"""
        # 确保依赖的任务存在
        for task in tasks.values():
            valid_dependencies = []
            for dep_id in task.dependencies:
                if dep_id in tasks:
                    valid_dependencies.append(dep_id)
            task.dependencies = valid_dependencies

    def _topological_sort(self, tasks: dict[str, Task]) -> list[str]:
        """拓扑排序(确定执行顺序)"""
        visited = set()
        temp_visited = set()
        result = []

        def visit(task_id: str):
            if task_id in temp_visited:
                # 检测到循环依赖
                logger.warning(f"⚠️  检测到循环依赖: {task_id}")
                return
            if task_id in visited:
                return

            temp_visited.add(task_id)

            task = tasks.get(task_id)
            if task:
                # 先访问依赖
                for dep_id in task.dependencies:
                    visit(dep_id)

                temp_visited.remove(task_id)
                visited.add(task_id)
                result.append(task_id)

        # 从所有任务开始访问
        for task_id in tasks:
            if task_id not in visited:
                visit(task_id)

        return result

    async def _assign_agents(self, tasks: dict[str, Task], available_agents: list[str]):
        """分配Agent到任务"""
        # 简单策略:轮询分配
        for i, (_task_id, task) in enumerate(tasks.items()):
            if not task.assignee:
                task.assignee = available_agents[i % len(available_agents)]

    async def execute_plan(
        self, plan: ExecutionPlan, executor_func: callable | None = None
    ) -> dict[str, Any]:
        """
        执行计划

        Args:
            plan: 执行计划
            executor_func: 任务执行函数

        Returns:
            执行结果
        """
        logger.info(f"🚀 开始执行计划: {plan.plan_id}")

        results = {
            "completed_tasks": [],
            "failed_tasks": [],
            "skipped_tasks": [],
            "total_duration": 0.0,
        }

        start_time = datetime.now()

        # 按顺序执行任务
        for task_id in plan.execution_order:
            task = plan.tasks.get(task_id)
            if not task:
                continue

            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now().isoformat()

            try:
                if executor_func:
                    # 使用提供的执行函数
                    result = await executor_func(task)
                else:
                    # 模拟执行
                    await asyncio.sleep(task.estimated_duration * 0.01)  # 模拟
                    result = f"任务 '{task.name}' 模拟执行完成"

                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                task.result = result
                results["completed_tasks"].append(task_id)

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now().isoformat()
                results["failed_tasks"].append(task_id)

        execution_time = (datetime.now() - start_time).total_seconds()
        results["total_duration"] = execution_time

        success = len(results["failed_tasks"]) == 0
        self.stats["successful_plans"] += 1 if success else 0
        self.stats["failed_plans"] += 0 if success else 1

        logger.info(f"✅ 计划执行完成: 成功={success}, 耗时={execution_time:.2f}s")

        return results

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self.stats["total_plans"]
        return {
            **self.stats,
            "success_rate": (self.stats["successful_plans"] / total if total > 0 else 0),
        }


# 便捷函数
async def create_planner() -> HierarchicalPlanner:
    """创建规划器"""
    return HierarchicalPlanner()
