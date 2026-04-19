#!/usr/bin/env python3
"""
智能任务规划器单元测试
Unit Tests for Agentic Task Planner
"""

import asyncio

# 添加项目路径
import sys
import unittest

sys.path.append('/Users/xujian/Athena工作平台')

from core.cognition.agentic_task_planner import (
    AgenticTaskPlanner,
    ExecutionPlan,
    TaskStatus,
    TaskStep,
)


class TestAgenticTaskPlanner(unittest.TestCase):
    """智能任务规划器测试类"""

    def setUp(self):
        """测试设置"""
        self.planner = AgenticTaskPlanner()

    def test_planner_initialization(self):
        """测试规划器初始化"""
        self.assertIsInstance(self.planner, AgenticTaskPlanner)
        self.assertIsNotNone(self.planner.agent_capabilities)
        self.assertIsNotNone(self.planner.execution_templates)
        self.assertIsNotNone(self.planner.performance_analytics)

    def test_create_execution_plan_simple_task(self):
        """测试创建简单任务执行计划"""
        goal = "分析系统性能"
        context = {"priority": "medium", "deadline": "1 day"}

        plan = self.planner.create_execution_plan(goal, context)

        self.assertIsInstance(plan, ExecutionPlan)
        self.assertEqual(plan.goal, goal)
        self.assertEqual(len(plan.steps), 3)  # 简单任务预期3个步骤
        self.assertEqual(plan.status, TaskStatus.PENDING)
        self.assertGreater(plan.estimated_total_time, 0)

    def test_create_execution_plan_complex_task(self):
        """测试创建复杂任务执行计划"""
        goal = "设计和实现新的存储架构"
        context = {"priority": "high", "deadline": "2 weeks"}

        plan = self.planner.create_execution_plan(goal, context)

        self.assertIsInstance(plan, ExecutionPlan)
        self.assertEqual(plan.goal, goal)
        self.assertGreater(len(plan.steps), 5)  # 复杂任务预期更多步骤
        self.assertGreater(plan.estimated_total_time, 300)  # 预期超过5分钟

    def test_task_step_creation(self):
        """测试任务步骤创建"""
        step = TaskStep(
            id="test_step_1",
            description="测试步骤",
            agent="xiaonuo",
            estimated_time=60,
            required_resources=["test_resource"]
        )

        self.assertEqual(step.id, "test_step_1")
        self.assertEqual(step.description, "测试步骤")
        self.assertEqual(step.agent, "xiaonuo")
        self.assertEqual(step.estimated_time, 60)
        self.assertIn("test_resource", step.required_resources)

    def test_agent_capabilities_initialization(self):
        """测试智能体能力初始化"""
        capabilities = self.planner.agent_capabilities

        self.assertIn("xiaonuo", capabilities)
        self.assertIn("xiaona", capabilities)
        self.assertIn("yunxi", capabilities)
        self.assertIn("xiaochen", capabilities)

        # 检查小诺的能力
        xiaonuo_caps = capabilities["xiaonuo"]
        self.assertIn("specialties", xiaonuo_caps)
        self.assertIn("max_concurrent_tasks", xiaonuo_caps)
        self.assertIn("preferred_task_types", xiaonuo_caps)

    def test_task_type_identification(self):
        """测试任务类型识别"""
        # 分析任务
        analysis_plan = self.planner.create_execution_plan(
            "分析系统性能瓶颈",
            {}
        )
        self.assertIsNotNone(analysis_plan)

        # 优化任务
        optimization_plan = self.planner.create_execution_plan(
            "优化数据库查询性能",
            {}
        )
        self.assertIsNotNone(optimization_plan)

        # 技术任务
        technical_plan = self.planner.create_execution_plan(
            "实现新的API接口",
            {}
        )
        self.assertIsNotNone(technical_plan)

    def test_step_dependency_handling(self):
        """测试步骤依赖处理"""
        goal = "执行有依赖关系的复杂任务"
        context = {"has_dependencies": True}

        plan = self.planner.create_execution_plan(goal, context)

        # 检查步骤是否有依赖关系
        for step in plan.steps:
            if hasattr(step, 'dependencies'):
                # 验证依赖关系的有效性
                for dep_id in step.dependencies:
                    dep_step = next((s for s in plan.steps if s.id == dep_id), None)
                    self.assertIsNotNone(dep_step, f"依赖步骤 {dep_id} 不存在")

    def test_resource_allocation(self):
        """测试资源分配"""
        goal = "需要特定资源的任务"
        context = {"required_resources": ["database", "api_access"]}

        plan = self.planner.create_execution_plan(goal, context)

        # 检查资源是否分配到相关步骤
        total_resources = []
        for step in plan.steps:
            total_resources.extend(step.required_resources)

        # 验证所需资源都已分配
        for resource in context["required_resources"]:
            self.assertIn(resource, total_resources)

    def test_priority_assignment(self):
        """测试优先级分配"""
        # 高优先级任务
        high_priority_plan = self.planner.create_execution_plan(
            "紧急系统故障修复",
            {"priority": "critical"}
        )

        # 低优先级任务
        low_priority_plan = self.planner.create_execution_plan(
            "日常性能监控",
            {"priority": "low"}
        )

        # 高优先级任务应该有更严格的步骤和更短的时间估算
        self.assertLessEqual(
            high_priority_plan.estimated_total_time,
            low_priority_plan.estimated_total_time * 2  # 允许一定误差
        )

    def test_performance_tracking(self):
        """测试性能跟踪"""
        # 创建多个计划以生成性能数据
        goals = [
            "任务1", "任务2", "任务3"
        ]

        for goal in goals:
            self.planner.create_execution_plan(goal, {})

        # 检查性能分析是否记录了数据
        performance_data = self.planner.performance_analytics.get_performance_data()
        self.assertIsNotNone(performance_data)

class TestExecutionPlanExecution(unittest.TestCase):
    """执行计划执行测试"""

    def setUp(self):
        """测试设置"""
        self.planner = AgenticTaskPlanner()

    async def test_plan_execution_simulation(self):
        """测试计划执行模拟"""
        goal = "模拟执行测试计划"
        context = {"simulation_mode": True}

        plan = self.planner.create_execution_plan(goal, context)

        # 模拟执行计划
        execution_result = await self._simulate_plan_execution(plan)

        self.assertIsNotNone(execution_result)
        self.assertIn('success', execution_result)
        self.assertIn('completed_steps', execution_result)

    async def _simulate_plan_execution(self, plan: ExecutionPlan) -> dict:
        """模拟执行计划"""
        completed_steps = []
        total_time = 0

        for step in plan.steps:
            # 模拟步骤执行时间
            await asyncio.sleep(0.1)  # 模拟100ms执行时间
            total_time += 0.1

            # 模拟步骤完成
            completed_steps.append({
                'step_id': step.id,
                'success': True,
                'execution_time': 0.1
            })

        return {
            'success': True,
            'completed_steps': len(completed_steps),
            'total_steps': len(plan.steps),
            'actual_time': total_time
        }

    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效输入
        with self.assertRaises((ValueError, TypeError)):
            self.planner.create_execution_plan("", {})  # 空目标

        with self.assertRaises((ValueError, TypeError)):
            self.planner.create_execution_plan(None, {})  # None目标

    def test_plan_serialization(self):
        """测试计划序列化"""
        goal = "序列化测试计划"
        context = {"test": "serialization"}

        plan = self.planner.create_execution_plan(goal, context)

        # 转换为字典
        plan_dict = {
            'id': plan.id,
            'goal': plan.goal,
            'context': plan.context,
            'steps_count': len(plan.steps),
            'estimated_time': plan.estimated_total_time,
            'status': plan.status.value
        }

        # 验证字典包含必要信息
        self.assertIn('id', plan_dict)
        self.assertIn('goal', plan_dict)
        self.assertIn('steps_count', plan_dict)
        self.assertEqual(plan_dict['goal'], goal)

# 异步测试类
class TestAsyncTaskPlanner(unittest.IsolatedAsyncioTestCase):
    """异步任务规划器测试"""

    async def asyncSetUp(self):
        """异步测试设置"""
        self.planner = AgenticTaskPlanner()

    async def test_async_plan_creation(self):
        """测试异步计划创建"""
        goal = "异步测试任务"
        context = {"async_mode": True}

        # 在异步环境中创建计划
        plan = await asyncio.to_thread(
            self.planner.create_execution_plan, goal, context
        )

        self.assertIsNotNone(plan)
        self.assertEqual(plan.goal, goal)

    async def test_concurrent_plan_creation(self):
        """测试并发计划创建"""
        goals = [f"并发任务{i}" for i in range(5)]

        # 并发创建多个计划
        tasks = [
            asyncio.to_thread(self.planner.create_execution_plan, goal, {})
            for goal in goals
        ]

        plans = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有计划都成功创建
        for i, plan in enumerate(plans):
            self.assertFalse(isinstance(plan, Exception), f"任务{i}创建失败")
            self.assertEqual(plan.goal, goals[i])

# 性能测试
class TestTaskPlannerPerformance(unittest.TestCase):
    """任务规划器性能测试"""

    def setUp(self):
        """测试设置"""
        self.planner = AgenticTaskPlanner()

    def test_planning_performance(self):
        """测试规划性能"""
        import time

        goals = [f"性能测试任务{i}" for i in range(10)]
        start_time = time.time()

        # 连续创建多个计划
        for goal in goals:
            self.planner.create_execution_plan(goal, {})

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(goals)

        # 性能要求：每个规划任务应在1秒内完成
        self.assertLess(avg_time, 1.0, "平均规划时间超过1秒")

    def test_memory_usage(self):
        """测试内存使用"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 创建大量计划
        for i in range(100):
            self.planner.create_execution_plan(f"内存测试任务{i}", {})

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内（比如小于100MB）
        self.assertLess(memory_increase, 100, "内存使用增长过多")

# 边界测试
class TestTaskPlannerEdgeCases(unittest.TestCase):
    """任务规划器边界测试"""

    def setUp(self):
        """测试设置"""
        self.planner = AgenticTaskPlanner()

    def test_very_long_goal(self):
        """测试非常长的目标"""
        long_goal = "测试" * 1000  # 3000字符的目标

        plan = self.planner.create_execution_plan(long_goal, {})

        self.assertIsNotNone(plan)
        self.assertEqual(len(plan.steps), 3)  # 应该使用默认步骤数

    def test_very_complex_context(self):
        """测试非常复杂的上下文"""
        complex_context = {
            "parameters": {f"param{i}": f"value{i}" for i in range(100)},
            "nested": {
                "level1": {
                    "level2": {
                        "level3": {"deep_data": "test"}
                    }
                }
            }
        }

        plan = self.planner.create_execution_plan("复杂上下文测试", complex_context)

        self.assertIsNotNone(plan)
        self.assertIsInstance(plan.context, dict)

    def test_unicode_content(self):
        """测试Unicode内容"""
        unicode_goal = "测试Unicode内容 🚀 ñiño Café Müller 中文"

        plan = self.planner.create_execution_plan(unicode_goal, {})

        self.assertIsNotNone(plan)
        self.assertEqual(plan.goal, unicode_goal)

if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)
