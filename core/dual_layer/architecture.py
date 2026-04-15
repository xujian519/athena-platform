#!/usr/bin/env python3
from __future__ import annotations
"""
双层级架构系统
Dual-Layer Architecture System - Work Level + Task Level两层架构

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"

架构说明:
    Work Level (工作层):
        - 负责任务分解、规划、资源分配
        - 协调多个Agent和工具
        - 监控整体进度

    Task Level (任务层):
        - 负责具体步骤执行
        - 调用工具和API
        - 处理数据和生成结果
"""

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.context_management import ContextStatus, TaskContextManager
from core.plan_documents import PlanDocument, PlanStep
from core.real_time_feedback import FeedbackLevel, RealTimeFeedback

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """层级类型"""

    WORK_LEVEL = "work_level"  # 工作层
    TASK_LEVEL = "task_level"  # 任务层


@dataclass
class WorkLevelPlan:
    """工作层计划"""

    task_id: str
    objective: str  # 总体目标
    sub_tasks: list[str]  # 子任务列表
    resource_allocation: dict[str, Any]  # 资源分配
    agent_assignment: dict[str, str]  # Agent分配
    dependencies: dict[str, list[str]]  # 任务依赖关系
    estimated_duration: int | None = None  # 预估时长(秒)


@dataclass
class TaskLevelExecution:
    """任务层执行"""

    task_id: str
    sub_task_id: str
    step_number: int
    action: str  # 执行的动作
    tools_used: list[str]  # 使用的工具
    input_data: dict[str, Any]  # 输入数据
    output_data: dict[str, Any] | None = None  # 输出数据
    status: str = "pending"
    start_time: str | None = None
    end_time: str | None = None


class WorkLevelOrchestrator:
    """工作层编排器 - 负责高层规划和协调"""

    def __init__(self):
        """初始化工作层编排器"""
        self.context_manager = TaskContextManager()
        self.plan_generator = PlanDocument()
        self.active_plans: dict[str, WorkLevelPlan] = {}

        logger.info("🎯 工作层编排器初始化")

    async def plan_work(
        self, task_id: str, objective: str, domain: str = "general"
    ) -> WorkLevelPlan:
        """
        制定工作计划

        Args:
            task_id: 任务ID
            objective: 总体目标
            domain: 任务领域

        Returns:
            WorkLevelPlan: 工作计划
        """
        logger.info(f"📋 制定工作计划: {objective[:50]}...")

        # 将总体目标分解为子任务
        sub_tasks = await self._decompose_objective(objective, domain)

        # 分配资源
        resource_allocation = await self._allocate_resources(sub_tasks, domain)

        # 分配Agent
        agent_assignment = await self._assign_agents(sub_tasks, domain)

        # 分析依赖关系
        dependencies = await self._analyze_dependencies(sub_tasks)

        # 创建工作计划
        plan = WorkLevelPlan(
            task_id=task_id,
            objective=objective,
            sub_tasks=sub_tasks,
            resource_allocation=resource_allocation,
            agent_assignment=agent_assignment,
            dependencies=dependencies,
            estimated_duration=len(sub_tasks) * 300,  # 假设每个子任务5分钟
        )

        self.active_plans[task_id] = plan

        # 生成plan.md文档
        await self._generate_plan_document(task_id, objective, sub_tasks, domain)

        logger.info(f"✅ 工作计划制定完成: {len(sub_tasks)}个子任务")

        return plan

    async def _decompose_objective(self, objective: str, domain: str) -> list[str]:
        """
        分解总体目标为子任务

        Args:
            objective: 总体目标
            domain: 领域

        Returns:
            list[str]: 子任务列表
        """
        # TODO: 实际实现中,这里应该使用LLM进行智能分解

        # 根据领域提供不同的分解策略
        if domain == "patent":
            return [
                "分析专利需求",
                "检索相关专利",
                "分析专利技术方案",
                "撰写专利申请文件",
                "审查和修改",
            ]
        elif domain == "legal":
            return ["理解法律问题", "检索相关法规", "分析案例", "形成法律意见"]
        else:
            # 通用任务分解
            return ["理解需求", "制定方案", "执行实施", "验证结果", "总结报告"]

    async def _allocate_resources(self, sub_tasks: list[str], domain: str) -> dict[str, Any]:
        """
        分配资源

        Args:
            sub_tasks: 子任务列表
            domain: 领域

        Returns:
            Dict: 资源分配
        """
        # 根据领域和任务类型分配资源
        return {
            "database_access": True,
            "vector_search": domain in ["patent", "legal"],
            "knowledge_graph": domain == "patent",
            "external_apis": domain == "general",
            "max_concurrent_tasks": min(len(sub_tasks), 3),
        }

    async def _assign_agents(self, sub_tasks: list[str], domain: str) -> dict[str, str]:
        """
        分配Agent

        Args:
            sub_tasks: 子任务列表
            domain: 领域

        Returns:
            Dict: Agent分配
        """
        # 根据领域分配Agent
        if domain == "patent" or domain == "legal":
            return dict.fromkeys(sub_tasks, "xiaona")
        else:
            return dict.fromkeys(sub_tasks, "xiaonuo")

    async def _analyze_dependencies(self, sub_tasks: list[str]) -> dict[str, list[str]]:
        """
        分析任务依赖关系

        Args:
            sub_tasks: 子任务列表

        Returns:
            Dict: 依赖关系
        """
        # 简单的顺序依赖
        dependencies = {}
        for i in range(1, len(sub_tasks)):
            dependencies[sub_tasks[i]] = [sub_tasks[i - 1]]

        return dependencies

    async def _generate_plan_document(
        self, task_id: str, objective: str, sub_tasks: list[str], domain: str
    ) -> None:
        """生成plan.md文档"""
        steps = [
            PlanStep(
                step_id=f"step_{i}",
                name=sub_task,
                description=f"执行子任务: {sub_task}",
                status="pending",
            )
            for i, sub_task in enumerate(sub_tasks, 1)
        ]

        # 这里需要一个简单的分类对象,暂时用None代替
        # 实际使用时应该从task_classifier获取
        await self.plan_generator.create_plan(
            task_id=task_id,
            task_description=objective,
            classification=None,  # TODO: 使用实际的分类结果
            steps=steps,
            thinking_mode="Plan",
        )

    async def monitor_progress(self, task_id: str) -> dict[str, Any]:
        """
        监控任务进度

        Args:
            task_id: 任务ID

        Returns:
            Dict: 进度信息
        """
        context = await self.context_manager.load_context(task_id)

        if not context:
            return {"task_id": task_id, "status": "not_found", "progress": 0.0}

        plan = self.active_plans.get(task_id)

        return {
            "task_id": task_id,
            "status": context.status.value,
            "current_step": context.current_step,
            "total_steps": context.total_steps,
            "progress": (
                context.current_step / context.total_steps if context.total_steps > 0 else 0.0
            ),
            "sub_tasks": len(plan.sub_tasks) if plan else 0,
        }


class TaskLevelExecutor:
    """任务层执行器 - 负责具体步骤执行"""

    def __init__(self):
        """初始化任务层执行器"""
        self.context_manager = TaskContextManager()
        self.feedback: RealTimeFeedback | None = None
        self.tool_registry: dict[str, Callable] = {}

        logger.info("⚙️ 任务层执行器初始化")

    def register_tool(self, name: str, func: Callable) -> None:
        """
        注册工具

        Args:
            name: 工具名称
            func: 工具函数
        """
        self.tool_registry[name] = func
        logger.info(f"🔧 注册工具: {name}")

    async def execute_step(
        self,
        task_id: str,
        sub_task_id: str,
        step_number: int,
        action: str,
        tools: list[str],
        input_data: dict[str, Any],        enable_feedback: bool = True,
    ) -> TaskLevelExecution:
        """
        执行单个步骤

        Args:
            task_id: 任务ID
            sub_task_id: 子任务ID
            step_number: 步骤编号
            action: 执行动作
            tools: 使用的工具列表
            input_data: 输入数据
            enable_feedback: 是否启用反馈

        Returns:
            TaskLevelExecution: 执行结果
        """
        if enable_feedback:
            self.feedback = RealTimeFeedback(task_id, FeedbackLevel.VERBOSE)

        execution = TaskLevelExecution(
            task_id=task_id,
            sub_task_id=sub_task_id,
            step_number=step_number,
            action=action,
            tools_used=tools,
            input_data=input_data,
            status="in_progress",
            start_time=datetime.now().isoformat(),
        )

        try:
            # 发送执行反馈
            if self.feedback:
                await self.feedback.executing(
                    f"执行步骤 {step_number}: {action}", step_id=sub_task_id
                )

            # 执行工具
            output_data = {}
            for tool_name in tools:
                if tool_name in self.tool_registry:
                    if self.feedback:
                        await self.feedback.info(f"调用工具: {tool_name}")

                    tool_result = await self.tool_registry[tool_name](**input_data)
                    output_data[tool_name] = tool_result
                else:
                    logger.warning(f"⚠️ 工具不存在: {tool_name}")

            execution.output_data = output_data
            execution.status = "completed"
            execution.end_time = datetime.now().isoformat()

            # 更新上下文
            await self.context_manager.update_step(
                task_id=task_id,
                step_id=sub_task_id,
                step_name=action,
                status="completed",
                output_data=output_data,
            )

            if self.feedback:
                await self.feedback.success(f"步骤 {step_number} 完成")

        except Exception as e:
            execution.status = "failed"
            execution.end_time = datetime.now().isoformat()

            if self.feedback:
                await self.feedback.error(f"步骤执行失败: {e!s}")

            logger.error(f"❌ 步骤执行失败: {e}")

        return execution

    async def execute_workflow(
        self, task_id: str, workflow: list[dict[str, Any]], enable_feedback: bool = True
    ) -> list[TaskLevelExecution]:
        """
        执行完整工作流

        Args:
            task_id: 任务ID
            workflow: 工作流定义
            enable_feedback: 是否启用反馈

        Returns:
            list[TaskLevelExecution]: 所有执行结果
        """
        results = []

        for step_def in workflow:
            execution = await self.execute_step(
                task_id=task_id,
                sub_task_id=step_def["sub_task_id"],
                step_number=step_def["step_number"],
                action=step_def["action"],
                tools=step_def.get("tools", []),
                input_data=step_def.get("input_data", {}),
                enable_feedback=enable_feedback,
            )

            results.append(execution)

            # 如果步骤失败,停止执行
            if execution.status == "failed":
                logger.error(f"❌ 工作流在步骤 {step_def['step_number']} 失败,停止执行")
                break

        return results


class DualLayerCoordinator:
    """双层级协调器 - 连接工作层和任务层"""

    def __init__(self):
        """初始化双层级协调器"""
        self.work_level = WorkLevelOrchestrator()
        self.task_level = TaskLevelExecutor()

        logger.info("🤝 双层级协调器初始化完成")

    async def execute_task(
        self, task_id: str, objective: str, domain: str = "general", enable_feedback: bool = True
    ) -> dict[str, Any]:
        """
        执行完整任务(工作层 + 任务层)

        Args:
            task_id: 任务ID
            objective: 总体目标
            domain: 任务领域
            enable_feedback: 是否启用反馈

        Returns:
            Dict: 执行结果
        """
        logger.info(f"🚀 开始执行任务: {objective[:50]}...")

        # 创建任务上下文
        await self.task_level.context_manager.create_context(
            task_id=task_id, task_description=objective
        )

        # 工作层:制定计划
        work_plan = await self.work_level.plan_work(
            task_id=task_id, objective=objective, domain=domain
        )

        # 任务层:执行工作流
        workflow = []
        for i, sub_task in enumerate(work_plan.sub_tasks, 1):
            workflow.append(
                {
                    "sub_task_id": f"subtask_{i}",
                    "step_number": i,
                    "action": sub_task,
                    "tools": [],  # TODO: 根据任务类型选择工具
                    "input_data": {},
                }
            )

        execution_results = await self.task_level.execute_workflow(
            task_id=task_id, workflow=workflow, enable_feedback=enable_feedback
        )

        # 更新任务状态
        all_completed = all(r.status == "completed" for r in execution_results)
        final_status = ContextStatus.COMPLETED if all_completed else ContextStatus.FAILED

        await self.task_level.context_manager.set_status(task_id, final_status)

        return {
            "task_id": task_id,
            "objective": objective,
            "status": final_status.value,
            "work_plan": work_plan,
            "execution_results": execution_results,
            "total_steps": len(workflow),
            "completed_steps": len([r for r in execution_results if r.status == "completed"]),
        }


# 便捷函数
async def execute_dual_layer_task(
    task_id: str, objective: str, domain: str = "general"
) -> dict[str, Any]:
    """
    便捷的双层级任务执行函数

    Args:
        task_id: 任务ID
        objective: 总体目标
        domain: 任务领域

    Returns:
        Dict: 执行结果
    """
    coordinator = DualLayerCoordinator()
    return await coordinator.execute_task(task_id, objective, domain)


__all__ = [
    "DualLayerCoordinator",
    "LayerType",
    "TaskLevelExecution",
    "TaskLevelExecutor",
    "WorkLevelOrchestrator",
    "WorkLevelPlan",
    "execute_dual_layer_task",
]
