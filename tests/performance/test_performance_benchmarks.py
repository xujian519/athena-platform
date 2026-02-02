#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试
Performance Benchmark Tests
"""

import asyncio
import time
import psutil
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
from pathlib import Path

# 添加项目路径
import sys
sys.path.append('/Users/xujian/Athena工作平台')

from core.cognition.agentic_task_planner import AgenticTaskPlanner
from core.cognition.prompt_chain_processor import PromptChainProcessor
from core.management.goal_management_system import GoalManagementSystem
from integration.xiaonuo_planning_integration import XiaonuoEnhancedAgent
from integration.xiaona_chain_integration import XiaonaEnhancedAgent
from integration.yunxi_goal_integration import YunxiEnhancedAgent
from integration.xiaochen_collaboration_integration import XiaochenEnhancedAgent

class PerformanceBenchmark:
    """性能基准测试工具"""

    def __init__(self):
        self.results = {}
        self.baseline_file = Path('/Users/xujian/Athena工作平台/tests/data/performance_baseline.json')
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> Dict[str, Any]:
        """加载性能基准"""
        if self.baseline_file.exists():
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._create_default_baseline()

    def _create_default_baseline(self) -> Dict[str, Any]:
        """创建默认性能基准"""
        return {
            "task_planner": {
                "create_plan": {"max_time": 1.0, "min_success_rate": 0.95},
                "execute_plan": {"max_time": 2.0, "min_success_rate": 0.90},
                "memory_usage": {"max_mb": 50}
            },
            "prompt_chain": {
                "create_chain": {"max_time": 0.5, "min_success_rate": 0.95},
                "execute_chain": {"max_time": 3.0, "min_success_rate": 0.85},
                "memory_usage": {"max_mb": 30}
            },
            "goal_manager": {
                "create_goal": {"max_time": 0.3, "min_success_rate": 0.95},
                "update_progress": {"max_time": 0.1, "min_success_rate": 0.95},
                "memory_usage": {"max_mb": 20}
            },
            "agent_integrations": {
                "response_time": {"max_time": 1.5, "min_success_rate": 0.90},
                "concurrent_load": {"max_time_per_request": 2.0, "min_success_rate": 0.80},
                "memory_usage": {"max_mb": 100}
            }
        }

    def save_baseline(self):
        """保存性能基准"""
        with open(self.baseline_file, 'w', encoding='utf-8') as f:
            json.dump(self.baseline, f, indent=2, ensure_ascii=False)

    def record_metric(self, component: str, operation: str, value: float, unit: str = "seconds"):
        """记录性能指标"""
        if component not in self.results:
            self.results[component] = {}
        if operation not in self.results[component]:
            self.results[component][operation] = []

        self.results[component][operation].append({
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        })

    def compare_with_baseline(self, component: str, operation: str, actual_value: float) -> Dict[str, Any]:
        """与基准比较"""
        if component not in self.baseline or operation not in self.baseline[component]:
            return {"status": "no_baseline", "message": "无基准数据"}

        baseline_data = self.baseline[component][operation]

        if "max_time" in baseline_data:
            if actual_value <= baseline_data["max_time"]:
                return {"status": "passed", "message": f"性能符合基准 (≤{baseline_data['max_time']}s)"}
            else:
                return {
                    "status": "failed",
                    "message": f"性能超出基准 (>{baseline_data['max_time']}s)",
                    "violation": actual_value - baseline_data["max_time"]
                }

        return {"status": "unknown", "message": "未知基准类型"}

class TaskPlannerPerformanceTest(unittest.TestCase):
    """任务规划器性能测试"""

    def setUp(self):
        """测试设置"""
        self.planner = AgenticTaskPlanner()
        self.benchmark = PerformanceBenchmark()
        self.process = psutil.Process()

    def test_create_plan_performance(self):
        """测试创建计划性能"""
        test_cases = [
            ("简单任务", "分析系统性能", {}),
            ("中等任务", "设计和实现新功能模块", {"complexity": "medium"}),
            ("复杂任务", "完整的系统架构重构", {"complexity": "high", "scope": "enterprise"})
        ]

        results = []

        for task_name, goal, context in test_cases:
            # 预热
            self.planner.create_execution_plan("预热任务", {})

            # 测试创建计划
            start_time = time.time()
            start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

            plan = self.planner.create_execution_plan(goal, context)

            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

            execution_time = end_time - start_time
            memory_increase = end_memory - start_memory

            # 记录指标
            self.benchmark.record_metric("task_planner", "create_plan", execution_time)
            self.benchmark.record_metric("task_planner", "create_plan_memory", memory_increase, "MB")

            # 与基准比较
            comparison = self.benchmark.compare_with_baseline("task_planner", "create_plan", execution_time)

            results.append({
                "task": task_name,
                "execution_time": execution_time,
                "memory_increase": memory_increase,
                "plan_steps": len(plan.steps) if plan else 0,
                "benchmark_status": comparison["status"]
            })

            print(f"✅ {task_name}: {execution_time:.3f}s (基准: {comparison['message']})")

        # 验证性能指标
        for result in results:
            if result["benchmark_status"] == "failed":
                self.fail(f"性能测试失败: {result['task']}")

    def test_batch_planning_performance(self):
        """测试批量规划性能"""
        batch_sizes = [10, 50, 100]
        results = []

        for batch_size in batch_sizes:
            goals = [f"批量测试任务 {i}" for i in range(batch_size)]

            start_time = time.time()
            start_memory = self.process.memory_info().rss / 1024 / 1024

            plans = []
            for goal in goals:
                plan = self.planner.create_execution_plan(goal, {})
                plans.append(plan)

            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024

            total_time = end_time - start_time
            avg_time = total_time / batch_size
            memory_increase = end_memory - start_memory

            results.append({
                "batch_size": batch_size,
                "total_time": total_time,
                "avg_time": avg_time,
                "memory_increase": memory_increase
            })

            print(f"📊 批量大小 {batch_size}: 平均 {avg_time:.3f}s/任务")

        # 验证性能不会随批量大小线性增长
        if len(results) >= 2:
            first_avg = results[0]["avg_time"]
            last_avg = results[-1]["avg_time"]
            # 平均时间增长不应超过3倍
            self.assertLess(last_avg / first_avg, 3.0, "批量性能衰减过快")

    def test_concurrent_planning_performance(self):
        """测试并发规划性能"""
        async def test_concurrent():
            concurrent_count = 10
            goals = [f"并发测试任务 {i}" for i in range(concurrent_count)]

            start_time = time.time()

            tasks = [
                asyncio.to_thread(self.planner.create_execution_plan, goal, {})
                for goal in goals
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / concurrent_count

            successful_plans = sum(1 for r in results if not isinstance(r, Exception))

            print(f"🔄 并发规划: {successful_plans}/{concurrent_count} 成功, 平均 {avg_time:.3f}s/任务")

            # 验证并发性能
            self.assertGreaterEqual(successful_plans, concurrent_count * 0.9, "并发成功率过低")
            self.assertLess(avg_time, 2.0, "并发平均时间过长")

            return total_time, avg_time

        # 运行异步测试
        total_time, avg_time = asyncio.run(test_concurrent())

        # 记录指标
        self.benchmark.record_metric("task_planner", "concurrent_planning", total_time)
        self.benchmark.record_metric("task_planner", "concurrent_avg", avg_time)

class PromptChainPerformanceTest(unittest.TestCase):
    """提示链处理器性能测试"""

    def setUp(self):
        """测试设置"""
        self.processor = PromptChainProcessor()
        self.benchmark = PerformanceBenchmark()
        self.process = psutil.Process()

    def test_chain_creation_performance(self):
        """测试链创建性能"""
        chain_types = ["simple", "analysis", "evaluation"]
        test_data = {"query": "性能测试查询"}

        results = []

        for chain_type in chain_types:
            # 预热
            try:
                self.processor.create_chain("warmup", test_data)
            except:
                pass  # 忽略预热错误

            start_time = time.time()
            start_memory = self.process.memory_info().rss / 1024 / 1024

            try:
                chain_id = self.processor.create_chain(chain_type, test_data)
                success = True
            except Exception as e:
                chain_id = None
                success = False
                print(f"⚠️ 链创建失败: {e}")

            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024

            execution_time = end_time - start_time
            memory_increase = end_memory - start_memory

            results.append({
                "chain_type": chain_type,
                "execution_time": execution_time,
                "memory_increase": memory_increase,
                "success": success,
                "chain_id": chain_id
            })

            print(f"✅ {chain_type}链创建: {execution_time:.3f}s")

        # 验证性能指标
        for result in results:
            if result["success"]:
                comparison = self.benchmark.compare_with_baseline("prompt_chain", "create_chain", result["execution_time"])
                if comparison["status"] == "failed":
                    self.fail(f"提示链性能测试失败: {result['chain_type']}")

    def test_chain_execution_simulation(self):
        """测试链执行模拟性能"""
        chain_steps_count = [3, 5, 10]
        results = []

        for steps_count in chain_steps_count:
            start_time = time.time()
            start_memory = self.process.memory_info().rss / 1024 / 1024

            # 模拟链执行
            execution_result = self._simulate_chain_execution(steps_count)

            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024

            execution_time = end_time - start_time
            memory_increase = end_memory - start_memory

            results.append({
                "steps_count": steps_count,
                "execution_time": execution_time,
                "memory_increase": memory_increase,
                "success": execution_result["success"]
            })

            print(f"⚡ {steps_count}步链执行: {execution_time:.3f}s")

        # 验证执行时间与步骤数的关系
        if len(results) >= 2:
            # 执行时间增长应该是线性的，但不应该超过比例
            first_result = results[0]
            last_result = results[-1]
            time_ratio = last_result["execution_time"] / first_result["execution_time"]
            step_ratio = last_result["steps_count"] / first_result["steps_count"]

            # 时间增长不应超过步骤数增长的1.5倍
            self.assertLess(time_ratio / step_ratio, 1.5, "链执行时间增长过快")

    def _simulate_chain_execution(self, steps_count: int) -> Dict[str, Any]:
        """模拟链执行"""
        try:
            # 模拟每个步骤的执行
            for i in range(steps_count):
                time.sleep(0.01)  # 模拟10ms处理时间

            return {"success": True, "steps_executed": steps_count}
        except Exception as e:
            return {"success": False, "error": str(e)}

class GoalManagerPerformanceTest(unittest.TestCase):
    """目标管理器性能测试"""

    def setUp(self):
        """测试设置"""
        self.goal_manager = GoalManagementSystem()
        self.benchmark = PerformanceBenchmark()
        self.process = psutil.Process()

    def test_goal_creation_performance(self):
        """测试目标创建性能"""
        goal_templates = [
            {
                "title": "学习目标",
                "description": "学习新技能",
                "priority": 2,
                "category": "learning"
            },
            {
                "title": "项目目标",
                "description": "完成项目开发",
                "priority": 3,
                "category": "project",
                "deadline": datetime.now() + timedelta(days=90)
            },
            {
                "title": "健康目标",
                "description": "改善身体健康",
                "priority": 2,
                "category": "health",
                "metrics": [
                    {"name": "运动天数", "target": 30, "unit": "天"},
                    {"name": "体重减少", "target": 5, "unit": "kg"}
                ]
            }
        ]

        results = []

        for i, template in enumerate(goal_templates):
            start_time = time.time()
            start_memory = self.process.memory_info().rss / 1024 / 1024

            goal = self.goal_manager.create_goal(template)

            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024

            execution_time = end_time - start_time
            memory_increase = end_memory - start_memory

            results.append({
                "template_index": i,
                "execution_time": execution_time,
                "memory_increase": memory_increase,
                "subgoals_count": len(goal.subgoals) if goal else 0,
                "metrics_count": len(goal.metrics) if goal else 0
            })

            print(f"🎯 目标{i+1}创建: {execution_time:.3f}s, {len(goal.subgoals) if goal else 0}个子目标")

        # 验证性能指标
        for result in results:
            comparison = self.benchmark.compare_with_baseline("goal_manager", "create_goal", result["execution_time"])
            if comparison["status"] == "failed":
                self.fail(f"目标管理器性能测试失败: 模板{result['template_index']}")

    def test_progress_update_performance(self):
        """测试进度更新性能"""
        # 创建测试目标
        goal = self.goal_manager.create_goal({
            "title": "性能测试目标",
            "description": "用于测试进度更新性能",
            "priority": 2
        })

        update_counts = [10, 50, 100]
        results = []

        for update_count in update_counts:
            start_time = time.time()

            # 执行多次进度更新
            for i in range(update_count):
                if goal.subgoals:
                    # 随机选择一个子目标更新
                    import random
                    subgoal = random.choice(goal.subgoals)
                    # 模拟进度更新
                    subgoal.progress = min(100, subgoal.progress + 10)

            end_time = time.time()
            avg_time = (end_time - start_time) / update_count

            results.append({
                "update_count": update_count,
                "total_time": end_time - start_time,
                "avg_time": avg_time
            })

            print(f"📈 {update_count}次进度更新: 平均 {avg_time:.4f}s/次")

        # 验证更新性能
        for result in results:
            comparison = self.benchmark.compare_with_baseline("goal_manager", "update_progress", result["avg_time"])
            if comparison["status"] == "failed":
                self.fail(f"进度更新性能测试失败: {result['update_count']}次更新")

    def test_goal_search_performance(self):
        """测试目标搜索性能"""
        # 创建大量目标
        goal_count = 100
        goals = []
        for i in range(goal_count):
            goal_data = {
                "title": f"搜索测试目标 {i}",
                "description": f"用于测试搜索性能的目标 {i}",
                "category": ["learning", "work", "personal", "health"][i % 4],
                "priority": (i % 4) + 1
            }
            goal = self.goal_manager.create_goal(goal_data)
            goals.append(goal)

        # 测试不同类型的搜索
        search_tests = [
            ("按标题搜索", lambda: self.goal_manager.search_goals("搜索测试目标 50")),
            ("按类别搜索", lambda: self.goal_manager.get_goals_by_category("learning")),
            ("按优先级搜索", lambda: self.goal_manager.search_goals("", priority=2))
        ]

        results = []

        for search_name, search_func in search_tests:
            start_time = time.time()
            search_results = search_func()
            end_time = time.time()

            execution_time = end_time - start_time
            result_count = len(search_results) if isinstance(search_results, list) else 1

            results.append({
                "search_type": search_name,
                "execution_time": execution_time,
                "result_count": result_count
            })

            print(f"🔍 {search_name}: {execution_time:.4f}s, {result_count}个结果")

        # 验证搜索性能
        for result in results:
            self.assertLess(result["execution_time"], 0.1, f"搜索性能过慢: {result['search_type']}")

class AgentIntegrationPerformanceTest(unittest.TestCase):
    """智能体集成性能测试"""

    def setUp(self):
        """测试设置"""
        self.benchmark = PerformanceBenchmark()
        self.process = psutil.Process()

        # 创建测试智能体
        self.agents = {
            'xiaonuo': XiaonuoEnhancedAgent({'agent_id': 'perf_xiaonuo'}),
            'xiaona': XiaonaEnhancedAgent({'agent_id': 'perf_xiaona'}),
            'yunxi': YunxiEnhancedAgent({'agent_id': 'perf_yunxi'}),
            'xiaochen': XiaochenEnhancedAgent({'agent_id': 'perf_xiaochen'})
        }

    async def test_agent_response_time_performance(self):
        """测试智能体响应时间性能"""
        test_requests = {
            'xiaonuo': [
                "制定简单的学习计划",
                "分析系统性能问题",
                "设计复杂的技术架构"
            ],
            'xiaona': [
                "搜索AI相关专利",
                "分析技术专利布局",
                "评估专利侵权风险"
            ],
            'yunxi': [
                "设定学习Python的目标",
                "制定健身计划",
                "创建项目管理目标"
            ],
            'xiaochen': [
                "协调两人协作任务",
                "组织团队项目",
                "管理复杂的多智能体项目"
            ]
        }

        results = []

        for agent_name, agent in self.agents.items():
            agent_results = []
            requests = test_requests[agent_name]

            for request in requests:
                start_time = time.time()
                start_memory = self.process.memory_info().rss / 1024 / 1024

                try:
                    if agent_name == 'xiaonuo':
                        result = await agent.process_with_planning(request)
                    elif agent_name == 'xiaona':
                        result = await agent.process_with_chain(request)
                    elif agent_name == 'yunxi':
                        result = await agent.process_goal_request(request)
                    elif agent_name == 'xiaochen':
                        result = await agent.process_collaboration_request(request)

                    success = True
                except Exception as e:
                    result = str(e)
                    success = False

                end_time = time.time()
                end_memory = self.process.memory_info().rss / 1024 / 1024

                execution_time = end_time - start_time
                memory_increase = end_memory - start_memory

                agent_results.append({
                    "request": request,
                    "execution_time": execution_time,
                    "memory_increase": memory_increase,
                    "success": success
                })

                # 记录指标
                self.benchmark.record_metric("agent_integrations", "response_time", execution_time)

            # 计算智能体的平均性能
            avg_time = sum(r["execution_time"] for r in agent_results) / len(agent_results)
            success_rate = sum(1 for r in agent_results if r["success"]) / len(agent_results)

            results.append({
                "agent": agent_name,
                "avg_response_time": avg_time,
                "success_rate": success_rate,
                "total_memory_increase": sum(r["memory_increase"] for r in agent_results)
            })

            print(f"🤖 {agent_name}: 平均响应时间 {avg_time:.3f}s, 成功率 {success_rate:.1%}")

        # 验证性能指标
        for result in results:
            comparison = self.benchmark.compare_with_baseline("agent_integrations", "response_time", result["avg_response_time"])
            if comparison["status"] == "failed":
                self.fail(f"智能体响应时间性能测试失败: {result['agent']}")

            # 成功率应该大于90%
            self.assertGreaterEqual(result["success_rate"], 0.9, f"智能体成功率过低: {result['agent']}")

    async def test_concurrent_agent_performance(self):
        """测试并发智能体性能"""
        concurrent_requests = 20
        agent_names = list(self.agents.keys())

        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024

        # 创建并发任务
        tasks = []
        for i in range(concurrent_requests):
            agent_name = agent_names[i % len(agent_names)]
            agent = self.agents[agent_name]
            request = f"并发测试请求 {i}"

            if agent_name == 'xiaonuo':
                task = agent.process_with_planning(request)
            elif agent_name == 'xiaona':
                task = agent.process_with_chain(request)
            elif agent_name == 'yunxi':
                task = agent.process_goal_request(request)
            elif agent_name == 'xiaochen':
                task = agent.process_collaboration_request(request)

            tasks.append(task)

        # 执行并发任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024

        total_time = end_time - start_time
        avg_time_per_request = total_time / concurrent_requests
        memory_increase = end_memory - start_memory

        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        success_rate = successful_requests / concurrent_requests

        print(f"🔄 并发测试: {successful_requests}/{concurrent_requests} 成功")
        print(f"⏱️ 总时间: {total_time:.3f}s, 平均: {avg_time_per_request:.3f}s/请求")
        print(f"💾 内存增长: {memory_increase:.1f}MB")

        # 验证并发性能
        comparison = self.benchmark.compare_with_baseline("agent_integrations", "concurrent_load", avg_time_per_request)
        if comparison["status"] == "failed":
            self.fail("并发智能体性能测试失败")

        self.assertGreaterEqual(success_rate, 0.8, "并发成功率过低")
        self.assertLess(avg_time_per_request, 2.0, "并发平均响应时间过长")

class MemoryUsageTest(unittest.TestCase):
    """内存使用测试"""

    def setUp(self):
        """测试设置"""
        self.process = psutil.Process()
        self.benchmark = PerformanceBenchmark()

    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        components = [
            ("任务规划器", lambda: AgenticTaskPlanner()),
            ("提示链处理器", lambda: PromptChainProcessor()),
            ("目标管理器", lambda: GoalManagementSystem())
        ]

        for component_name, component_factory in components:
            initial_memory = self.process.memory_info().rss / 1024 / 1024

            # 创建和销毁组件多次
            for i in range(10):
                component = component_factory()

                # 执行一些操作
                if hasattr(component, 'create_execution_plan'):
                    component.create_execution_plan("测试", {})
                elif hasattr(component, 'create_chain'):
                    try:
                        component.create_chain("test", {})
                    except:
                        pass
                elif hasattr(component, 'create_goal'):
                    component.create_goal({"title": "测试", "priority": 1})

                # 删除组件
                del component

            final_memory = self.process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory

            print(f"🧠 {component_name} 内存变化: {memory_increase:+.1f}MB")

            # 内存增长应该小于50MB
            self.assertLess(memory_increase, 50, f"{component_name}可能存在内存泄漏")

    def test_large_dataset_memory_usage(self):
        """测试大数据集内存使用"""
        # 测试处理大量数据时的内存使用
        goal_manager = GoalManagementSystem()
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        # 创建大量目标
        large_goal_count = 1000
        for i in range(large_goal_count):
            goal_data = {
                "title": f"大数据集测试目标 {i}",
                "description": f"描述 {i} " * 100,  # 长描述
                "priority": (i % 4) + 1,
                "metrics": [
                    {"name": f"指标{j}", "target": j * 10, "unit": "单位"}
                    for j in range(5)
                ]
            }
            goal_manager.create_goal(goal_data)

            if i % 100 == 0:
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"📊 创建{i}个目标后，内存增长: {memory_increase:.1f}MB")

        final_memory = self.process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory
        avg_memory_per_goal = total_memory_increase / large_goal_count

        print(f"📈 总内存增长: {total_memory_increase:.1f}MB")
        print(f"📊 平均每个目标: {avg_memory_per_goal:.3f}MB")

        # 验证内存使用合理
        self.assertLess(total_memory_increase, 500, "大数据集内存使用过多")
        self.assertLess(avg_memory_per_goal, 0.5, "单个目标内存使用过多")

class PerformanceReportGenerator:
    """性能报告生成器"""

    def __init__(self):
        self.results = {}
        self.benchmark = PerformanceBenchmark()

    def add_test_result(self, test_class: str, test_name: str, metrics: Dict[str, Any]):
        """添加测试结果"""
        if test_class not in self.results:
            self.results[test_class] = {}
        self.results[test_class][test_name] = metrics

    def generate_report(self) -> str:
        """生成性能报告"""
        report_lines = [
            "# 智能体设计模式性能测试报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 测试概览",
            ""
        ]

        # 统计概览
        total_tests = sum(len(class_tests) for class_tests in self.results.values())
        passed_tests = 0

        for test_class, class_tests in self.results.items():
            for test_name, metrics in class_tests.items():
                if metrics.get('status', 'unknown') == 'passed':
                    passed_tests += 1

        report_lines.extend([
            f"- 总测试数: {total_tests}",
            f"- 通过测试: {passed_tests}",
            f"- 失败测试: {total_tests - passed_tests}",
            f"- 通过率: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "- 通过率: 0%",
            ""
        ])

        # 详细结果
        report_lines.append("## 详细测试结果")
        report_lines.append("")

        for test_class, class_tests in self.results.items():
            report_lines.append(f"### {test_class}")
            report_lines.append("")

            for test_name, metrics in class_tests.items():
                status = metrics.get('status', 'unknown')
                status_icon = "✅" if status == 'passed' else "❌"

                report_lines.append(f"#### {status_icon} {test_name}")

                # 添加关键指标
                if 'execution_time' in metrics:
                    report_lines.append(f"- 执行时间: {metrics['execution_time']:.3f}s")
                if 'memory_usage' in metrics:
                    report_lines.append(f"- 内存使用: {metrics['memory_usage']:.1f}MB")
                if 'success_rate' in metrics:
                    report_lines.append(f"- 成功率: {metrics['success_rate']:.1%}")
                if 'benchmark_comparison' in metrics:
                    report_lines.append(f"- 基准对比: {metrics['benchmark_comparison']}")

                report_lines.append("")

        # 性能建议
        report_lines.extend([
            "## 性能建议",
            "",
            "基于测试结果，以下是一些性能优化建议：",
            "",
            "1. **缓存优化**: 对频繁调用的功能实现缓存机制",
            "2. **异步处理**: 将耗时操作改为异步处理",
            "3. **内存管理**: 定期清理不再使用的对象和数据",
            "4. **批量操作**: 对批量操作进行优化，减少重复计算",
            "5. **连接池**: 对外部服务调用使用连接池",
            "",
            "---",
            f"*报告由智能体设计模式测试框架生成*"
        ])

        return "\n".join(report_lines)

    def save_report(self, filename: str):
        """保存报告到文件"""
        report_content = self.generate_report()

        report_dir = Path('/Users/xujian/Athena工作平台/tests/reports')
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / filename
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"📊 性能报告已保存: {report_file}")
        return str(report_file)

# 主测试运行器
class PerformanceTestRunner:
    """性能测试运行器"""

    def __init__(self):
        self.report_generator = PerformanceReportGenerator()

    async def run_all_performance_tests(self):
        """运行所有性能测试"""
        print("🚀 开始运行性能测试")
        print("=" * 50)

        # 运行各类性能测试
        test_suites = [
            TaskPlannerPerformanceTest(),
            PromptChainPerformanceTest(),
            GoalManagerPerformanceTest(),
            MemoryUsageTest()
        ]

        for test_suite in test_suites:
            print(f"\n🧪 运行 {test_suite.__class__.__name__}")
            print("-" * 30)

            # 运行测试套件中的所有测试
            suite = unittest.TestLoader().loadTestsFromTestCase(test_suite.__class__)
            runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
            result = runner.run(suite)

            # 记录结果
            self.report_generator.add_test_result(
                test_suite.__class__.__name__,
                "整体测试",
                {
                    "status": "passed" if result.wasSuccessful() else "failed",
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors)
                }
            )

        # 运行异步测试
        print(f"\n🔄 运行异步性能测试")
        print("-" * 30)

        agent_test = AgentIntegrationPerformanceTest()
        await agent_test.test_agent_response_time_performance()
        await agent_test.test_concurrent_agent_performance()

        # 生成报告
        print(f"\n📊 生成性能报告")
        print("-" * 30)

        report_file = self.report_generator.save_report(
            f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )

        print(f"\n🎉 性能测试完成！")
        print(f"📄 详细报告: {report_file}")

if __name__ == '__main__':
    import os
import sys

    # 运行性能测试
    runner = PerformanceTestRunner()
    asyncio.run(runner.run_all_performance_tests())