#!/usr/bin/env python3
"""
目标管理系统单元测试
Unit Tests for Goal Management System
"""

import asyncio

# 添加项目路径
import sys
import unittest
from datetime import datetime, timedelta

sys.path.append('/Users/xujian/Athena工作平台')

from core.management.goal_management_system import (
    Goal,
    GoalManagementSystem,
    GoalPriority,
    GoalStatus,
    ProgressMetric,
    ProgressReport,
    SubGoal,
)


class TestGoalManagementSystem(unittest.TestCase):
    """目标管理系统测试类"""

    def setUp(self):
        """测试设置"""
        self.goal_manager = GoalManagementSystem()

    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertIsInstance(self.goal_manager, GoalManagementSystem)
        self.assertIsNotNone(self.goal_manager.active_goals)
        self.assertIsNotNone(self.goal_manager.goal_templates)
        self.assertIsNotNone(self.goal_manager.monitoring_service)

    def test_create_simple_goal(self):
        """测试创建简单目标"""
        goal_definition = {
            'title': '学习Python编程',
            'description': '在3个月内掌握Python基础',
            'priority': 2
        }

        goal = self.goal_manager.create_goal(goal_definition)

        self.assertIsInstance(goal, Goal)
        self.assertEqual(goal.title, '学习Python编程')
        self.assertEqual(goal.description, '在3个月内掌握Python基础')
        self.assertEqual(goal.priority, GoalPriority.MEDIUM)
        self.assertEqual(goal.status, GoalStatus.ACTIVE)
        self.assertIsNotNone(goal.id)
        self.assertIsInstance(goal.created_at, datetime)

    def test_create_complex_goal(self):
        """测试创建复杂目标"""
        goal_definition = {
            'title': '完成大型项目开发',
            'description': '在6个月内完成一个完整的Web应用',
            'category': 'project',
            'priority': 3,
            'target_outcome': '功能完整的Web应用',
            'success_criteria': [
                '用户登录系统',
                '数据管理功能',
                '响应式设计',
                '性能优化'
            ],
            'metrics': [
                {'name': '功能完成度', 'target': 100, 'unit': '%'},
                {'name': '代码质量', 'target': 85, 'unit': '分'},
                {'name': '用户满意度', 'target': 90, 'unit': '%'}
            ],
            'deadline': datetime.now() + timedelta(days=180)
        }

        goal = self.goal_manager.create_goal(goal_definition)

        self.assertEqual(goal.category, 'project')
        self.assertEqual(goal.priority, GoalPriority.HIGH)
        self.assertEqual(len(goal.success_criteria), 4)
        self.assertEqual(len(goal.metrics), 3)
        self.assertIsNotNone(goal.deadline)

    def test_subgoal_creation(self):
        """测试子目标创建"""
        goal_definition = {
            'title': '学习编程',
            'description': '掌握编程技能',
            'priority': 2
        }

        goal = self.goal_manager.create_goal(goal_definition)

        # 验证自动生成的子目标
        self.assertGreater(len(goal.subgoals), 0)

        # 检查子目标结构
        for subgoal in goal.subgoals:
            self.assertIsInstance(subgoal, SubGoal)
            self.assertIsNotNone(subgoal.id)
            self.assertIsNotNone(subgoal.title)
            self.assertIsNotNone(subgoal.description)
            self.assertIsInstance(subgoal.completed, bool)
            self.assertIsInstance(subgoal.progress, (int, float))

    def test_progress_metrics(self):
        """测试进度指标"""
        goal_definition = {
            'title': '健身计划',
            'description': '提升身体素质',
            'metrics': [
                {'name': '体重减少', 'target': 10, 'unit': 'kg'},
                {'name': '跑步距离', 'target': 100, 'unit': 'km'},
                {'name': '锻炼天数', 'target': 30, 'unit': '天'}
            ]
        }

        goal = self.goal_manager.create_goal(goal_definition)

        self.assertEqual(len(goal.metrics), 3)

        # 检查指标结构
        for metric in goal.metrics:
            self.assertIsInstance(metric, ProgressMetric)
            self.assertIsNotNone(metric.name)
            self.assertIsInstance(metric.target, (int, float))
            self.assertIsNotNone(metric.unit)

    def test_goal_status_update(self):
        """测试目标状态更新"""
        goal_definition = {
            'title': '测试目标',
            'description': '用于测试状态更新',
            'priority': 1
        }

        goal = self.goal_manager.create_goal(goal_definition)
        self.assertEqual(goal.status, GoalStatus.ACTIVE)

        # 更新状态
        self.goal_manager.update_goal_status(goal.id, GoalStatus.COMPLETED)
        updated_goal = self.goal_manager.get_goal(goal.id)
        self.assertEqual(updated_goal.status, GoalStatus.COMPLETED)

    def test_subgoal_completion(self):
        """测试子目标完成"""
        goal_definition = {
            'title': '测试目标',
            'description': '用于测试子目标完成',
            'priority': 1
        }

        goal = self.goal_manager.create_goal(goal_definition)
        len(goal.subgoals)

        # 完成第一个子目标
        first_subgoal = goal.subgoals[0]
        self.goal_manager.complete_subgoal(goal.id, first_subgoal.id)

        updated_goal = self.goal_manager.get_goal(goal.id)
        completed_subgoal = next(
            (sg for sg in updated_goal.subgoals if sg.id == first_subgoal.id),
            None
        )

        self.assertTrue(completed_subgoal.completed)
        self.assertEqual(completed_subgoal.progress, 100)

    def test_progress_calculation(self):
        """测试进度计算"""
        goal_definition = {
            'title': '多步骤目标',
            'description': '测试进度计算',
            'priority': 2
        }

        goal = self.goal_manager.create_goal(goal_definition)

        # 初始进度应该是0
        initial_progress = self.goal_manager.calculate_goal_progress(goal.id)
        self.assertEqual(initial_progress, 0)

        # 完成一半的子目标
        subgoals = goal.subgoals
        half_count = len(subgoals) // 2

        for i in range(half_count):
            self.goal_manager.complete_subgoal(goal.id, subgoals[i].id)

        # 进度应该是50%
        updated_progress = self.goal_manager.calculate_goal_progress(goal.id)
        self.assertEqual(updated_progress, 50)

    def test_goal_search(self):
        """测试目标搜索"""
        # 创建多个目标
        goals_data = [
            {'title': '学习Python', 'description': 'Python编程学习', 'priority': 2},
            {'title': '健身计划', 'description': '身体锻炼计划', 'priority': 1},
            {'title': '读书计划', 'description': '阅读专业书籍', 'priority': 2},
            {'title': '项目开发', 'description': '完成软件项目', 'priority': 3}
        ]

        created_goals = []
        for goal_data in goals_data:
            goal = self.goal_manager.create_goal(goal_data)
            created_goals.append(goal)

        # 搜索测试
        python_goals = self.goal_manager.search_goals("Python")
        self.assertEqual(len(python_goals), 1)
        self.assertIn("Python", python_goals[0].title)

        high_priority_goals = self.goal_manager.search_goals("", priority=GoalPriority.HIGH)
        self.assertEqual(len(high_priority_goals), 1)
        self.assertEqual(high_priority_goals[0].priority, GoalPriority.HIGH)

    def test_goal_deadline_tracking(self):
        """测试目标截止时间跟踪"""
        future_deadline = datetime.now() + timedelta(days=30)
        datetime.now() - timedelta(days=1)

        goal_definition = {
            'title': '未来目标',
            'description': '有未来截止时间的目标',
            'priority': 2,
            'deadline': future_deadline
        }

        goal = self.goal_manager.create_goal(goal_definition)

        # 检查截止时间状态
        deadline_status = self.goal_manager.get_deadline_status(goal.id)
        self.assertEqual(deadline_status['status'], 'upcoming')
        self.assertEqual(deadline_status['days_left'], 30)

    def test_goal_category_management(self):
        """测试目标分类管理"""
        categories = ['learning', 'health', 'work', 'personal']
        created_goals = []

        # 创建不同类别的目标
        for category in categories:
            goal_data = {
                'title': f'{category}目标',
                'description': f'{category}相关的目标',
                'category': category,
                'priority': 2
            }
            goal = self.goal_manager.create_goal(goal_data)
            created_goals.append(goal)

        # 按类别获取目标
        for category in categories:
            category_goals = self.goal_manager.get_goals_by_category(category)
            self.assertEqual(len(category_goals), 1)
            self.assertEqual(category_goals[0].category, category)

class TestProgressReport(unittest.TestCase):
    """进度报告测试"""

    def setUp(self):
        """测试设置"""
        self.goal_manager = GoalManagementSystem()

    def test_progress_report_generation(self):
        """测试进度报告生成"""
        goal_definition = {
            'title': '测试目标',
            'description': '用于生成进度报告',
            'priority': 2,
            'metrics': [
                {'name': '完成度', 'target': 100, 'unit': '%'},
                {'name': '质量分数', 'target': 90, 'unit': '分'}
            ]
        }

        goal = self.goal_manager.create_goal(goal_definition)

        # 生成进度报告
        report = self.goal_manager.generate_progress_report(goal.id)

        self.assertIsInstance(report, ProgressReport)
        self.assertEqual(report.goal_id, goal.id)
        self.assertIsInstance(report.overall_progress, (int, float))
        self.assertIsInstance(report.generated_at, datetime)

    def test_detailed_progress_analysis(self):
        """测试详细进度分析"""
        goal_definition = {
            'title': '复杂目标',
            'description': '用于详细进度分析',
            'priority': 2,
            'success_criteria': ['标准1', '标准2', '标准3'],
            'metrics': [
                {'name': '进度1', 'target': 100, 'unit': '%'},
                {'name': '进度2', 'target': 50, 'unit': '件'}
            ]
        }

        goal = self.goal_manager.create_goal(goal_definition)

        # 完成部分子目标
        if goal.subgoals:
            self.goal_manager.complete_subgoal(goal.id, goal.subgoals[0].id)

        # 生成详细报告
        detailed_report = self.goal_manager.generate_detailed_progress_report(goal.id)

        self.assertIn('subgoals_progress', detailed_report)
        self.assertIn('metrics_progress', detailed_report)
        self.assertIn('success_criteria_status', detailed_report)

    def test_progress_trends(self):
        """测试进度趋势"""
        goal_definition = {
            'title': '趋势测试目标',
            'description': '用于测试进度趋势',
            'priority': 2
        }

        goal = self.goal_manager.create_goal(goal_definition)

        # 模拟历史进度数据
        self.goal_manager.record_progress_snapshot(goal.id, progress=25)
        self.goal_manager.record_progress_snapshot(goal.id, progress=50)
        self.goal_manager.record_progress_snapshot(goal.id, progress=75)

        # 获取进度趋势
        trends = self.goal_manager.get_progress_trends(goal.id)

        self.assertIn('historical_data', trends)
        self.assertIn('trend_analysis', trends)
        self.assertEqual(len(trends['historical_data']), 3)

class TestGoalTemplates(unittest.TestCase):
    """目标模板测试"""

    def setUp(self):
        """测试设置"""
        self.goal_manager = GoalManagementSystem()

    def test_learning_goal_template(self):
        """测试学习目标模板"""
        template_result = self.goal_manager.apply_goal_template(
            'learning',
            {'subject': 'Python编程', 'duration': '3个月'}
        )

        self.assertIn('title', template_result)
        self.assertIn('description', template_result)
        self.assertIn('subgoals', template_result)
        self.assertIn('metrics', template_result)
        self.assertIn('Python编程', template_result['title'])

    def test_fitness_goal_template(self):
        """测试健身目标模板"""
        template_result = self.goal_manager.apply_goal_template(
            'fitness',
            {'activity': '跑步', 'target': '10公里'}
        )

        self.assertIn('title', template_result)
        self.assertIn('跑步', template_result['title'])
        self.assertIn('10公里', template_result['title'])

    def test_project_goal_template(self):
        """测试项目目标模板"""
        template_result = self.goal_manager.apply_goal_template(
            'project',
            {'project_name': 'Web应用', 'technology': 'React'}
        )

        self.assertIn('title', template_result)
        self.assertIn('Web应用', template_result['title'])
        self.assertIn('success_criteria', template_result)

class TestGoalReminders(unittest.TestCase):
    """目标提醒测试"""

    def setUp(self):
        """测试设置"""
        self.goal_manager = GoalManagementSystem()

    def test_deadline_reminders(self):
        """测试截止时间提醒"""
        # 创建即将到期的目标
        near_deadline = datetime.now() + timedelta(days=3)
        goal_definition = {
            'title': '紧急目标',
            'description': '3天后到期',
            'priority': 3,
            'deadline': near_deadline
        }

        self.goal_manager.create_goal(goal_definition)

        # 检查提醒
        reminders = self.goal_manager.check_deadline_reminders()

        self.assertIsInstance(reminders, list)
        if reminders:  # 如果有提醒
            self.assertIn('goal_id', reminders[0])
            self.assertIn('message', reminders[0])

    def test_progress_reminders(self):
        """测试进度提醒"""
        goal_definition = {
            'title': '长期目标',
            'description': '需要定期检查进度',
            'priority': 2
        }

        goal = self.goal_manager.create_goal(goal_definition)

        # 记录进度快照（模拟过去的进度）
        old_date = datetime.now() - timedelta(days=10)
        self.goal_manager.record_progress_snapshot(goal.id, progress=20, timestamp=old_date)

        # 检查进度提醒
        progress_reminders = self.goal_manager.check_progress_reminders()

        self.assertIsInstance(progress_reminders, list)

class TestGoalPerformance(unittest.TestCase):
    """目标绩效测试"""

    def setUp(self):
        """测试设置"""
        self.goal_manager = GoalManagementSystem()

    def test_goal_completion_rate(self):
        """测试目标完成率"""
        # 创建多个目标
        goals = []
        for i in range(10):
            goal_data = {
                'title': f'测试目标{i}',
                'description': f'测试目标{i}的描述',
                'priority': 2
            }
            goal = self.goal_manager.create_goal(goal_data)
            goals.append(goal)

        # 完成一半的目标
        for i in range(5):
            self.goal_manager.update_goal_status(goals[i].id, GoalStatus.COMPLETED)

        # 计算完成率
        completion_rate = self.goal_manager.calculate_completion_rate()
        self.assertEqual(completion_rate, 0.5)  # 50%完成率

    def test_goal_category_performance(self):
        """测试目标分类绩效"""
        categories = ['work', 'personal', 'learning']
        goals_by_category = {}

        # 为每个类别创建目标
        for category in categories:
            category_goals = []
            for i in range(3):
                goal_data = {
                    'title': f'{category}目标{i}',
                    'description': f'{category}相关的目标',
                    'category': category,
                    'priority': 2
                }
                goal = self.goal_manager.create_goal(goal_data)
                category_goals.append(goal)
            goals_by_category[category] = category_goals

        # 完成每个类别的一些目标
        for category, goals in goals_by_category.items():
            self.goal_manager.update_goal_status(goals[0].id, GoalStatus.COMPLETED)

        # 获取分类绩效
        category_performance = self.goal_manager.get_category_performance()

        for category in categories:
            self.assertIn(category, category_performance)
            self.assertIn('total_goals', category_performance[category])
            self.assertIn('completed_goals', category_performance[category])
            self.assertIn('completion_rate', category_performance[category])

# 异步测试类
class TestAsyncGoalManager(unittest.IsolatedAsyncioTestCase):
    """异步目标管理器测试"""

    async def asyncSetUp(self):
        """异步测试设置"""
        self.goal_manager = GoalManagementSystem()

    async def test_async_goal_creation(self):
        """测试异步目标创建"""
        goal_definition = {
            'title': '异步测试目标',
            'description': '用于异步测试',
            'priority': 2
        }

        goal = await asyncio.to_thread(
            self.goal_manager.create_goal, goal_definition
        )

        self.assertIsNotNone(goal)
        self.assertEqual(goal.title, '异步测试目标')

    async def test_async_progress_monitoring(self):
        """测试异步进度监控"""
        goal_definition = {
            'title': '监控测试目标',
            'description': '用于测试异步监控',
            'priority': 2
        }

        goal = await asyncio.to_thread(
            self.goal_manager.create_goal, goal_definition
        )

        # 模拟异步监控
        monitoring_result = await self._async_monitor_progress(goal.id)

        self.assertIsNotNone(monitoring_result)
        self.assertIn('goal_id', monitoring_result)

    async def _async_monitor_progress(self, goal_id):
        """异步监控进度"""
        await asyncio.sleep(0.1)  # 模拟监控延迟
        return {
            'goal_id': goal_id,
            'status': 'monitoring',
            'timestamp': datetime.now().isoformat()
        }

    async def test_concurrent_goal_operations(self):
        """测试并发目标操作"""
        # 创建多个目标
        goal_ids = []

        for i in range(5):
            goal_data = {
                'title': f'并发测试目标{i}',
                'description': f'并发测试{i}',
                'priority': 2
            }
            goal = await asyncio.to_thread(
                self.goal_manager.create_goal, goal_data
            )
            goal_ids.append(goal.id)

        # 并发更新状态
        update_tasks = [
            asyncio.to_thread(
                self.goal_manager.update_goal_status,
                goal_id,
                GoalStatus.IN_PROGRESS
            )
            for goal_id in goal_ids
        ]

        results = await asyncio.gather(*update_tasks, return_exceptions=True)

        # 验证所有操作都成功
        for result in results:
            self.assertFalse(isinstance(result, Exception), f"并发操作失败: {result}")

if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)
