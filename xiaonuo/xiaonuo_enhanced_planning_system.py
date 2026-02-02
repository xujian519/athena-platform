#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺增强规划系统
Xiaonuo Enhanced Planning System

整合所有规划器，提供统一的规划管理能力，
增强模块间的协作和性能优化。

作者: 小诺·双鱼座
创建时间: 2025-12-17
版本: v2.0.0 "增强规划"
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

# 添加core路径
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from planning.unified_planning_interface import (
    PlannerType, PlanningRequest, PlanningResult, Priority, TaskStatus,
    get_planner_registry, get_integration_bridge, get_planner_coordinator,
    BasePlanner
)

# 导入现有规划器
try:
    from cognition.agentic_task_planner import AgenticTaskPlanner
    from management.goal_management_system import GoalManager
except ImportError as e:
    logging.warning(f"导入规划器失败: {e}")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTaskPlanner(BasePlanner):
    """增强任务规划器 - 适配原有任务规划器"""

    def __init__(self):
        super().__init__("小诺增强任务规划器", PlannerType.TASK_PLANNER)
        self.agentic_planner = None
        self._initialize_agentic_planner()

    def _initialize_agentic_planner(self):
        """初始化智能体任务规划器"""
        try:
            self.agentic_planner = AgenticTaskPlanner()
            logger.info("✅ 智能体任务规划器初始化成功")
        except Exception as e:
            logger.error(f"❌ 智能体任务规划器初始化失败: {e}")

    async def create_plan(self, request: PlanningRequest) -> PlanningResult:
        """创建增强任务规划"""
        if not self.agentic_planner:
            return PlanningResult(
                request_id=request.id,
                planner_type=self.planner_type,
                success=False,
                feedback="智能体任务规划器未初始化"
            )

        try:
            # 构建任务上下文
            context = {
                "goal": request.title,
                "description": request.description,
                "requirements": request.requirements,
                "constraints": request.constraints,
                "assigned_agent": request.assigned_agent or "xiaonuo",
                **request.context
            }

            # 调用原有规划器
            execution_plan = self.agentic_planner.plan_task(context)

            # 转换为统一格式
            steps = []
            for step in execution_plan.steps:
                steps.append({
                    "id": step.id,
                    "description": step.description,
                    "agent": step.agent,
                    "dependencies": step.dependencies,
                    "estimated_time": step.estimated_time,
                    "resources": step.required_resources
                })

            # 估算总时间
            total_time = sum(step.estimated_time for step in execution_plan.steps)
            estimated_duration = timedelta(seconds=total_time) if total_time > 0 else None

            # 创建规划结果
            result = PlanningResult(
                request_id=request.id,
                planner_type=self.planner_type,
                success=True,
                plan_id=execution_plan.id,
                steps=steps,
                estimated_duration=estimated_duration,
                resources=list(set(
                    resource for step in execution_plan.steps
                    for resource in step.required_resources
                )),
                dependencies=list(set(
                    dep for step in execution_plan.steps
                    for dep in step.dependencies
                )),
                confidence_score=0.85,  # 基于智能体能力评分
                feedback="任务规划创建成功"
            )

            # 存储规划
            self.active_plans[result.plan_id] = result
            self.planning_history.append(result)

            return result

        except Exception as e:
            logger.error(f"创建任务规划失败: {e}")
            return PlanningResult(
                request_id=request.id,
                planner_type=self.planner_type,
                success=False,
                feedback=f"任务规划创建失败: {str(e)}"
            )

    async def execute_plan(self, plan_id: str) -> bool:
        """执行任务规划"""
        if plan_id not in self.active_plans:
            return False

        try:
            plan = self.active_plans[plan_id]
            plan.status = TaskStatus.IN_PROGRESS

            # 这里可以集成实际的执行逻辑
            # 目前只是模拟执行
            await asyncio.sleep(1)  # 模拟执行时间

            plan.status = TaskStatus.COMPLETED
            return True

        except Exception as e:
            logger.error(f"执行任务规划失败: {e}")
            return False

    async def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """获取规划状态"""
        if plan_id not in self.active_plans:
            return {"error": "规划不存在"}

        plan = self.active_plans[plan_id]
        return {
            "plan_id": plan_id,
            "status": plan.status.value,
            "steps_count": len(plan.steps),
            "created_at": plan.created_at.isoformat(),
            "confidence_score": plan.confidence_score
        }

    async def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """更新规划"""
        if plan_id not in self.active_plans:
            return False

        try:
            plan = self.active_plans[plan_id]
            for key, value in updates.items():
                if hasattr(plan, key):
                    setattr(plan, key, value)

            return True

        except Exception as e:
            logger.error(f"更新规划失败: {e}")
            return False

class EnhancedGoalManager(BasePlanner):
    """增强目标管理器 - 适配原目标管理系统"""

    def __init__(self):
        super().__init__("小诺增强目标管理器", PlannerType.GOAL_MANAGER)
        self.goal_manager = None
        self._initialize_goal_manager()

    def _initialize_goal_manager(self):
        """初始化目标管理器"""
        try:
            self.goal_manager = GoalManager()
            logger.info("✅ 目标管理系统初始化成功")
        except Exception as e:
            logger.error(f"❌ 目标管理系统初始化失败: {e}")

    async def create_plan(self, request: PlanningRequest) -> PlanningResult:
        """创建目标规划"""
        if not self.goal_manager:
            return PlanningResult(
                request_id=request.id,
                planner_type=self.planner_type,
                success=False,
                feedback="目标管理系统未初始化"
            )

        try:
            # 构建目标定义
            goal_definition = {
                "title": request.title,
                "description": request.description,
                "priority": request.priority.value,
                "assigned_agent": request.assigned_agent,
                "due_date": request.deadline.isoformat() if request.deadline else None,
                "context": request.context,
                "tags": request.metadata.get("tags", [])
            }

            # 创建目标
            goal = self.goal_manager.create_goal(goal_definition)

            # 转换子目标为步骤
            steps = []
            for subgoal in goal.subgoals:
                steps.append({
                    "id": subgoal.id,
                    "description": subgoal.description,
                    "agent": subgoal.assigned_agent or goal.assigned_agent,
                    "dependencies": [],
                    "estimated_time": 3600,  # 默认1小时
                    "resources": [subgoal.assigned_agent or goal.assigned_agent]
                })

            # 估算时间
            total_steps = len(steps)
            estimated_duration = timedelta(hours=total_steps) if total_steps > 0 else None

            result = PlanningResult(
                request_id=request.id,
                planner_type=self.planner_type,
                success=True,
                plan_id=goal.id,
                steps=steps,
                estimated_duration=estimated_duration,
                resources=[goal.assigned_agent],
                confidence_score=0.90,
                feedback="目标规划创建成功"
            )

            # 存储规划
            self.active_plans[result.plan_id] = result
            self.planning_history.append(result)

            return result

        except Exception as e:
            logger.error(f"创建目标规划失败: {e}")
            return PlanningResult(
                request_id=request.id,
                planner_type=self.planner_type,
                success=False,
                feedback=f"目标规划创建失败: {str(e)}"
            )

    async def execute_plan(self, plan_id: str) -> bool:
        """执行目标规划"""
        if plan_id not in self.active_plans:
            return False

        try:
            plan = self.active_plans[plan_id]
            plan.status = TaskStatus.IN_PROGRESS

            # 目标执行逻辑
            # 这里可以集成实际的目标执行机制
            await asyncio.sleep(1)  # 模拟执行

            plan.status = TaskStatus.COMPLETED
            return True

        except Exception as e:
            logger.error(f"执行目标规划失败: {e}")
            return False

    async def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """获取目标状态"""
        if plan_id not in self.active_plans:
            return {"error": "目标不存在"}

        plan = self.active_plans[plan_id]
        return {
            "plan_id": plan_id,
            "status": plan.status.value,
            "steps_count": len(plan.steps),
            "created_at": plan.created_at.isoformat(),
            "confidence_score": plan.confidence_score
        }

    async def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """更新目标规划"""
        if plan_id not in self.active_plans:
            return False

        try:
            plan = self.active_plans[plan_id]
            for key, value in updates.items():
                if hasattr(plan, key):
                    setattr(plan, key, value)

            return True

        except Exception as e:
            logger.error(f"更新目标规划失败: {e}")
            return False

class XiaonuoEnhancedPlanningSystem:
    """小诺增强规划系统主类"""

    def __init__(self):
        self.registry = get_planner_registry()
        self.bridge = get_integration_bridge()
        self.coordinator = get_planner_coordinator()
        self.performance_metrics = {
            "total_requests": 0,
            "successful_plans": 0,
            "failed_plans": 0,
            "average_creation_time": 0.0,
            "active_plans": 0
        }
        self._initialize_system()

    def _initialize_system(self):
        """初始化系统"""
        print("🌸 初始化小诺增强规划系统...")

        # 注册增强规划器
        task_planner = EnhancedTaskPlanner()
        goal_manager = EnhancedGoalManager()

        self.registry.register_planner(task_planner)
        self.registry.register_planner(goal_manager)

        # 注册集成适配器
        self._register_integration_adapters()

        print("✅ 增强规划系统初始化完成")

    def _register_integration_adapters(self):
        """注册集成适配器"""
        # 通用任务适配器
        def task_adapter(data: Dict[str, Any]) -> PlanningRequest:
            return PlanningRequest(
                type=PlannerType.TASK_PLANNER,
                title=data.get("title", ""),
                description=data.get("description", ""),
                context=data.get("context", {}),
                requirements=data.get("requirements", []),
                assigned_agent=data.get("assigned_agent"),
                priority=Priority(data.get("priority", Priority.MEDIUM.value))
            )

        # 目标管理适配器
        def goal_adapter(data: Dict[str, Any]) -> PlanningRequest:
            return PlanningRequest(
                type=PlannerType.GOAL_MANAGER,
                title=data.get("title", ""),
                description=data.get("description", ""),
                context=data.get("context", {}),
                assigned_agent=data.get("assigned_agent"),
                priority=Priority(data.get("priority", Priority.MEDIUM.value)),
                deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None
            )

        self.bridge.register_integration_adapter("task", PlannerType.TASK_PLANNER, task_adapter)
        self.bridge.register_integration_adapter("goal", PlannerType.GOAL_MANAGER, goal_adapter)

    async def create_task_plan(self, title: str, description: str,
                             assigned_agent: str = "xiaonuo",
                             context: Dict | None = None) -> PlanningResult:
        """创建任务规划"""
        request = PlanningRequest(
            type=PlannerType.TASK_PLANNER,
            title=title,
            description=description,
            assigned_agent=assigned_agent,
            context=context or {},
            priority=Priority.MEDIUM
        )

        start_time = time.time()
        result = await self.registry.submit_request(request)
        creation_time = time.time() - start_time

        # 更新性能指标
        self._update_metrics(result, creation_time)

        return result

    async def create_goal_plan(self, title: str, description: str,
                             deadline: datetime | None = None,
                             assigned_agent: str = "xiaonuo",
                             context: Dict | None = None) -> PlanningResult:
        """创建目标规划"""
        request = PlanningRequest(
            type=PlannerType.GOAL_MANAGER,
            title=title,
            description=description,
            deadline=deadline,
            assigned_agent=assigned_agent,
            context=context or {},
            priority=Priority.MEDIUM
        )

        start_time = time.time()
        result = await self.registry.submit_request(request)
        creation_time = time.time() - start_time

        # 更新性能指标
        self._update_metrics(result, creation_time)

        return result

    async def execute_plan(self, plan_id: str) -> bool:
        """执行规划"""
        # 从缓存中获取规划
        result = await self.registry.get_result(plan_id)
        if not result:
            return False

        planner = self.registry.get_planner(result.planner_type)
        if planner:
            return await planner.execute_plan(result.plan_id)
        return False

    async def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """获取规划状态"""
        result = await self.registry.get_result(plan_id)
        if not result:
            return {"error": "规划不存在"}

        planner = self.registry.get_planner(result.planner_type)
        if planner:
            return await planner.get_plan_status(result.plan_id)
        return {"error": "规划器不可用"}

    async def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """更新规划"""
        result = await self.registry.get_result(plan_id)
        if not result:
            return False

        planner = self.registry.get_planner(result.planner_type)
        if planner:
            return await planner.update_plan(result.plan_id, updates)
        return False

    def _update_metrics(self, result: PlanningResult, creation_time: float):
        """更新性能指标"""
        self.performance_metrics["total_requests"] += 1
        if result.success:
            self.performance_metrics["successful_plans"] += 1
        else:
            self.performance_metrics["failed_plans"] += 1

        # 更新平均创建时间
        total = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_creation_time"]
        self.performance_metrics["average_creation_time"] = (
            (current_avg * (total - 1) + creation_time) / total
        )

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "registry_status": self.registry.get_status(),
            "performance_metrics": self.performance_metrics,
            "registered_planners": [
                planner.get_planner_info() for planner in self.registry.planners.values()
            ]
        }

    async def demo_planning_system(self):
        """演示规划系统"""
        print("🌟 小诺增强规划系统演示")
        print("=" * 50)

        # 演示任务规划
        print("\n📋 创建任务规划...")
        task_result = await self.create_task_plan(
            title="优化系统性能",
            description="分析和优化Athena工作平台的整体性能",
            assigned_agent="xiaonuo",
            context={"optimization_areas": ["响应时间", "资源利用率", "并发处理"]}
        )

        if task_result.success:
            print(f"✅ 任务规划创建成功: {task_result.plan_id}")
            print(f"📊 步骤数量: {len(task_result.steps)}")
            print(f"⏱️ 预估时间: {task_result.estimated_duration}")
        else:
            print(f"❌ 任务规划创建失败: {task_result.feedback}")

        # 演示目标规划
        print("\n🎯 创建目标规划...")
        goal_result = await self.create_goal_plan(
            title="完成专利检索系统优化",
            description="在3周内完成专利检索系统的性能优化和功能增强",
            deadline=datetime.now() + timedelta(weeks=3),
            assigned_agent="xiaona"
        )

        if goal_result.success:
            print(f"✅ 目标规划创建成功: {goal_result.plan_id}")
            print(f"📊 步骤数量: {len(goal_result.steps)}")
            print(f"⏱️ 预估时间: {goal_result.estimated_duration}")
        else:
            print(f"❌ 目标规划创建失败: {goal_result.feedback}")

        # 显示系统状态
        print("\n📈 系统状态:")
        status = self.get_system_status()
        print(f"总请求数: {status['performance_metrics']['total_requests']}")
        print(f"成功率: {status['performance_metrics']['successful_plans']}/{status['performance_metrics']['total_requests']}")
        print(f"平均创建时间: {status['performance_metrics']['average_creation_time']:.3f}秒")

async def main():
    """主函数"""
    planning_system = XiaonuoEnhancedPlanningSystem()
    await planning_system.demo_planning_system()

if __name__ == "__main__":
    asyncio.run(main())