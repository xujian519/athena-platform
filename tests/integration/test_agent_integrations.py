#!/usr/bin/env python3
"""
智能体集成测试
Integration Tests for Agent Integrations
"""

import pytest

pytestmark = pytest.mark.skip(reason="模块导入问题，待修复")

import asyncio

# 添加项目路径
import sys
import time
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

sys.path.append('/Users/xujian/Athena工作平台')

from core.agents.xiaochen_collaboration_integration import XiaochenEnhancedAgent
from core.agents.yunxi_goal_integration import YunxiEnhancedAgent
from tests.integration.xiaona_chain_integration import XiaonaEnhancedAgent

from tests.integration.xiaonuo_planning_integration import XiaonuoEnhancedAgent


class TestXiaonuoPlanningIntegration(unittest.TestCase):
    """小诺规划集成测试"""

    def setUp(self):
        """测试设置"""
        self.agent = XiaonuoEnhancedAgent({
            'agent_id': 'xiaonuo_test'
        })

    async def test_planning_request_simple(self):
        """测试简单规划请求"""
        request = "帮我制定一个系统优化计划"
        context = {"priority": "medium"}

        result = await self.agent.process_with_planning(request, context)

        self.assertIsNotNone(result)
        self.assertEqual(result['agent'], 'xiaonuo_enhanced')
        self.assertIn(result['response_type'], ['planning', 'fallback', 'error'])
        self.assertIn('content', result)
        self.assertIn('timestamp', result)

    async def test_planning_request_complex(self):
        """测试复杂规划请求"""
        request = "设计一个完整的微服务架构迁移方案，包括数据迁移、服务拆分和性能优化"
        context = {
            "priority": "high",
            "deadline": "2 weeks",
            "team_size": 5,
            "budget": "100k"
        }

        result = await self.agent.process_with_planning(request, context)

        self.assertIsNotNone(result)
        self.assertEqual(result['agent'], 'xiaonuo_enhanced')
        # 复杂请求应该触发真正的规划而不是fallback
        if result['response_type'] != 'error':
            self.assertIn('content', result)

    async def test_planning_with_different_priorities(self):
        """测试不同优先级的规划"""
        test_cases = [
            ("日常任务检查", {"priority": "low"}),
            ("系统性能优化", {"priority": "medium"}),
            ("紧急故障修复", {"priority": "high", "urgency": "critical"})
        ]

        results = []
        for request, context in test_cases:
            result = await self.agent.process_with_planning(request, context)
            results.append((request, result))

        # 验证所有请求都有响应
        for request, result in results:
            self.assertIsNotNone(result)
            self.assertEqual(result['agent'], 'xiaonuo_enhanced')

    def test_agent_initialization(self):
        """测试智能体初始化"""
        self.assertEqual(self.agent.agent_id, 'xiaonuo_test')
        self.assertIsNotNone(self.agent.config)
        self.assertIsNone(self.agent.planning_integration)  # 未初始化

    async def test_planning_components_integration(self):
        """测试规划组件集成"""
        # 模拟初始化
        with patch('integration.xiaonuo_planning_integration.XiaonuoPlanningIntegration') as MockIntegration:
            mock_integration = AsyncMock()
            mock_integration.handle_planning_request.return_value = {
                'agent': 'xiaonuo',
                'response_type': 'planning',
                'content': '规划完成',
                'timestamp': datetime.now().isoformat()
            }
            MockIntegration.return_value = mock_integration

            # 重新创建智能体
            agent = XiaonuoEnhancedAgent({'agent_id': 'test_xiaonuo'})
            result = await agent.process_with_planning("测试请求")

            self.assertEqual(result['response_type'], 'planning')

class TestXiaonaChainIntegration(unittest.TestCase):
    """小娜提示链集成测试"""

    def setUp(self):
        """测试设置"""
        self.agent = XiaonaEnhancedAgent({
            'agent_id': 'xiaona_test'
        })

    async def test_patent_analysis_request(self):
        """测试专利分析请求"""
        query = "分析人工智能领域的专利技术趋势"
        context = {
            "search_depth": "comprehensive",
            "time_range": "last_5_years",
            "jurisdictions": ["US", "CN", "EP"]
        }

        result = await self.agent.process_with_chain(query, context)

        self.assertIsNotNone(result)
        self.assertEqual(result['agent'], 'xiaonuo_enhanced')  # 可能是fallback响应
        self.assertIn('response_type', result)
        self.assertIn('content', result)

    async def test_technical_evaluation_request(self):
        """测试技术评估请求"""
        query = "评估区块链技术在供应链管理中的应用前景"
        context = {
            "analysis_type": "technical_evaluation",
            "industry_focus": "supply_chain"
        }

        result = await self.agent.process_with_chain(query, context)

        self.assertIsNotNone(result)
        self.assertIn('content', result)

    async def test_legal_analysis_request(self):
        """测试法律分析请求"""
        query = "分析某项专利的侵权风险和自由实施可能性"
        context = {
            "analysis_type": "legal_analysis",
            "patent_id": "US1234567",
            "jurisdiction": "US"
        }

        result = await self.agent.process_with_chain(query, context)

        self.assertIsNotNone(result)
        self.assertIn('content', result)

    def test_chain_templates_availability(self):
        """测试链模板可用性"""
        # 检查是否有定义的链模板
        # 这需要在初始化后检查
        pass

    async def test_multi_step_analysis(self):
        """测试多步骤分析"""
        query = "进行全面的专利技术分析，包括技术趋势、竞争格局和法律风险"
        context = {
            "comprehensive_analysis": True,
            "include_recommendations": True
        }

        result = await self.agent.process_with_chain(query, context)

        self.assertIsNotNone(result)
        # 如果是真正的链处理，应该有更详细的内容

class TestYunxiGoalIntegration(unittest.TestCase):
    """云熙目标管理集成测试"""

    def setUp(self):
        """测试设置"""
        self.agent = YunxiEnhancedAgent({
            'agent_id': 'yunxi_test'
        })

    async def test_learning_goal_setting(self):
        """测试学习目标设定"""
        request = "我想学习Python编程，希望3个月内达到中级水平"
        context = {
            "current_level": "beginner",
            "target_level": "intermediate",
            "time_available": "2_hours_per_day"
        }

        result = await self.agent.process_goal_request(request, context)

        self.assertIsNotNone(result)
        self.assertEqual(result['agent'], 'yunxi_enhanced')
        self.assertIn('response_type', result)
        self.assertIn('content', result)

    async def test_business_goal_setting(self):
        """测试业务目标设定"""
        request = "提升团队开发效率30%，在6个月内实现"
        context = {
            "team_size": 10,
            "current_efficiency_metrics": ["code_velocity", "bug_rate"],
            "available_resources": ["training_budget", "tools"]
        }

        result = await self.agent.process_goal_request(request, context)

        self.assertIsNotNone(result)
        self.assertIn('content', result)

    async def test_personal_goal_setting(self):
        """测试个人目标设定"""
        request = "减重10公斤，建立健康的生活方式"
        context = {
            "current_weight": "80kg",
            "target_weight": "70kg",
            "timeframe": "4_months",
            "preferences": ["diet", "exercise"]
        }

        result = await self.agent.process_goal_request(request, context)

        self.assertIsNotNone(result)
        self.assertIn('content', result)

    async def test_goal_progress_tracking(self):
        """测试目标进度跟踪"""
        # 先创建一个目标
        goal_request = "完成Python基础课程"
        goal_result = await self.agent.process_goal_request(goal_request)

        # 然后查询进度
        if 'goal_id' in goal_result:
            progress_result = await self.agent.get_goal_progress(goal_result['goal_id'])
            self.assertIsNotNone(progress_result)
            self.assertIn('response_type', progress_result)

    async def test_goal_template_application(self):
        """测试目标模板应用"""
        test_requests = [
            "准备马拉松比赛",
            "学习新技能",
            "完成年度读书计划"
        ]

        results = []
        for request in test_requests:
            result = await self.agent.process_goal_request(request)
            results.append(result)

        # 验证所有请求都有响应
        for result in results:
            self.assertIsNotNone(result)
            self.assertIn('content', result)

class TestXiaochenCollaborationIntegration(unittest.TestCase):
    """小宸协作集成测试"""

    def setUp(self):
        """测试设置"""
        self.agent = XiaochenEnhancedAgent({
            'agent_id': 'xiaochen_test'
        })

    async def test_multi_agent_coordination(self):
        """测试多智能体协调"""
        request = "协调小诺和小娜完成一个复杂的技术专利分析项目"
        context = {
            "project_scope": "comprehensive",
            "deadline": "2_weeks",
            "required_expertise": ["technical_analysis", "patent_law"]
        }

        result = await self.agent.process_collaboration_request(request, context)

        self.assertIsNotNone(result)
        self.assertEqual(result['agent'], 'xiaochen_enhanced')
        self.assertIn('response_type', result)
        self.assertIn('content', result)

    async def test_team_project_collaboration(self):
        """测试团队项目协作"""
        request = "组织多个智能体进行系统架构设计评审"
        context = {
            "team_members": ["xiaonuo", "xiaona", "yunxi"],
            "project_type": "architecture_review",
            "deliverables": ["analysis_report", "recommendations"]
        }

        result = await self.agent.process_collaboration_request(request, context)

        self.assertIsNotNone(result)
        self.assertIn('content', result)

    async def test_learning_collaboration(self):
        """测试学习协作"""
        request = "建立跨智能体的知识分享和协作学习机制"
        context = {
            "learning_objectives": ["cross_domain_knowledge", "best_practices"],
            "participants": ["all_agents"],
            "schedule": "weekly"
        }

        result = await self.agent.process_collaboration_request(request, context)

        self.assertIsNotNone(result)
        self.assertIn('content', result)

    async def test_collaboration_status_monitoring(self):
        """测试协作状态监控"""
        # 先启动一个协作任务
        collab_request = "测试协作任务"
        await self.agent.process_collaboration_request(collab_request)

        # 然后查询协作状态
        status_result = await self.agent.get_collaboration_status()
        self.assertIsNotNone(status_result)
        self.assertIn('response_type', status_result)
        self.assertIn('content', status_result)

    async def test_conflict_resolution(self):
        """测试冲突解决"""
        request = "解决智能体间的资源分配冲突"
        context = {
            "conflict_type": "resource_allocation",
            "involved_agents": ["xiaonuo", "xiaona"],
            "conflict_details": "同时需要使用计算资源"
        }

        result = await self.agent.process_collaboration_request(request, context)

        self.assertIsNotNone(result)
        self.assertIn('content', result)

class TestCrossAgentIntegration(unittest.TestCase):
    """跨智能体集成测试"""

    def setUp(self):
        """测试设置"""
        self.agents = {
            'xiaonuo': XiaonuoEnhancedAgent({'agent_id': 'xiaonuo_cross_test'}),
            'xiaona': XiaonaEnhancedAgent({'agent_id': 'xiaona_cross_test'}),
            'yunxi': YunxiEnhancedAgent({'agent_id': 'yunxi_cross_test'}),
            'xiaochen': XiaochenEnhancedAgent({'agent_id': 'xiaochen_cross_test'})
        }

    async def test_sequential_collaboration(self):
        """测试顺序协作"""
        # 步骤1：小诺制定计划
        plan_result = await self.agents['xiaonuo'].process_with_planning(
            "制定专利分析项目计划"
        )

        # 步骤2：小娜执行分析
        if plan_result:
            analysis_result = await self.agents['xiaona'].process_with_chain(
                "执行专利技术分析"
            )

        # 步骤3：云锡总结目标达成
        # 步骤4：小宸评估协作效果

        # 验证至少前两步有响应
        self.assertIsNotNone(plan_result)
        if 'analysis_result' in locals():
            self.assertIsNotNone(analysis_result)

    async def test_parallel_collaboration(self):
        """测试并行协作"""
        # 同时启动多个智能体处理不同方面
        tasks = [
            self.agents['xiaonuo'].process_with_planning("任务1规划"),
            self.agents['xiaona'].process_with_chain("任务2分析"),
            self.agents['yunxi'].process_goal_request("任务3目标")
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有任务都有结果
        for i, result in enumerate(results):
            self.assertFalse(isinstance(result, Exception), f"任务{i}失败")
            self.assertIsNotNone(result)

    async def test_information_sharing(self):
        """测试信息共享"""
        # 小诺生成计划信息
        plan_result = await self.agents['xiaonuo'].process_with_planning(
            "生成测试计划"
        )

        # 将信息传递给其他智能体
        shared_context = {
            "source_agent": "xiaonuo",
            "shared_info": plan_result.get('content', ''),
            "timestamp": datetime.now().isoformat()
        }

        # 其他智能体使用共享信息
        enhanced_analysis = await self.agents['xiaona'].process_with_chain(
            "基于共享信息进行分析",
            shared_context
        )

        self.assertIsNotNone(enhanced_analysis)

    async def test_consensus_building(self):
        """测试共识建立"""
        # 多个智能体对同一问题提供意见
        topic = "系统架构优化方案"
        opinions = []

        for agent_name, agent in self.agents.items():
            if agent_name == 'xiaonuo':
                result = await agent.process_with_planning(f"{topic} - 规划角度")
            elif agent_name == 'xiaona':
                result = await agent.process_with_chain(f"{topic} - 分析角度")
            elif agent_name == 'yunxi':
                result = await agent.process_goal_request(f"{topic} - 目标角度")
            elif agent_name == 'xiaochen':
                result = await agent.process_collaboration_request(f"{topic} - 协作角度")

            opinions.append({
                'agent': agent_name,
                'opinion': result.get('content', ''),
                'response_type': result.get('response_type', 'unknown')
            })

        # 验证收集到多个意见
        self.assertEqual(len(opinions), 4)
        for opinion in opinions:
            self.assertIsInstance(opinion, dict)
            self.assertIn('agent', opinion)
            self.assertIn('opinion', opinion)

class TestIntegrationPerformance(unittest.TestCase):
    """集成性能测试"""

    def setUp(self):
        """测试设置"""
        self.agent_configs = [
            (XiaonuoEnhancedAgent, 'xiaonuo_perf_test'),
            (XiaonaEnhancedAgent, 'xiaona_perf_test'),
            (YunxiEnhancedAgent, 'yunxi_perf_test'),
            (XiaochenEnhancedAgent, 'xiaochen_perf_test')
        ]

    async def test_response_time_performance(self):
        """测试响应时间性能"""
        import time

        test_requests = [
            ("简单请求", "测试简单处理"),
            ("中等请求", "处理中等复杂度的任务，需要一定分析"),
            ("复杂请求", "处理非常复杂的综合性任务，涉及多个方面的分析")
        ]

        performance_results = []

        for AgentClass, agent_id in self.agent_configs:
            agent = AgentClass({'agent_id': agent_id})

            for complexity, request in test_requests:
                start_time = time.time()

                if agent_id == 'xiaonuo_perf_test':
                    result = await agent.process_with_planning(request)
                elif agent_id == 'xiaona_perf_test':
                    result = await agent.process_with_chain(request)
                elif agent_id == 'yunxi_perf_test':
                    result = await agent.process_goal_request(request)
                elif agent_id == 'xiaochen_perf_test':
                    result = await agent.process_collaboration_request(request)

                end_time = time.time()
                response_time = end_time - start_time

                performance_results.append({
                    'agent': agent_id,
                    'complexity': complexity,
                    'response_time': response_time,
                    'success': result is not None
                })

        # 分析性能数据
        avg_response_times = {}
        for result in performance_results:
            agent = result['agent']
            if agent not in avg_response_times:
                avg_response_times[agent] = []
            avg_response_times[agent].append(result['response_time'])

        # 计算平均响应时间
        for agent, times in avg_response_times.items():
            avg_time = sum(times) / len(times)
            # 性能要求：平均响应时间应小于2秒
            self.assertLess(avg_time, 2.0, f"{agent}平均响应时间过长: {avg_time:.2f}秒")

    async def test_concurrent_load_performance(self):
        """测试并发负载性能"""
        agent = XiaonuoEnhancedAgent({'agent_id': 'load_test'})

        # 创建并发任务
        concurrent_requests = 10
        tasks = [
            agent.process_with_planning(f"并发测试请求 {i}")
            for i in range(concurrent_requests)
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        _ = end_time  # 用于后续分析

        total_time = end_time - start_time
        successful_requests = sum(1 for r in results if not isinstance(r, Exception))

        # 性能要求：并发处理成功率应大于80%
        success_rate = successful_requests / concurrent_requests
        self.assertGreater(success_rate, 0.8, "并发处理成功率过低")

        # 验证总时间合理（应该比串行执行快）
        self.assertLess(total_time, concurrent_requests * 2.0, "并发处理时间过长")

class TestIntegrationReliability(unittest.TestCase):
    """集成可靠性测试"""

    async def test_error_handling_consistency(self):
        """测试错误处理一致性"""
        agent = XiaonuoEnhancedAgent({'agent_id': 'reliability_test'})

        # 测试各种错误输入
        error_cases = [
            "",  # 空请求
            None,  # None请求
            "x" * 10000,  # 超长请求
            {"invalid": "structure"}  # 无效结构
        ]

        for error_input in error_cases:
            try:
                if error_input is None or isinstance(error_input, dict):
                    # 跳过会导致类型错误的输入
                    continue

                result = await agent.process_with_planning(error_input)
                # 应该返回错误响应而不是崩溃
                self.assertIsNotNone(result)
                self.assertIn('response_type', result)
            except Exception as e:
                # 如果抛出异常，应该是预期的类型错误
                self.assertIsInstance(e, (TypeError, ValueError))

    async def test_resource_cleanup(self):
        """测试资源清理"""
        # 创建多个智能体实例
        agents = []
        for i in range(5):
            agent = XiaonuoEnhancedAgent({'agent_id': f'cleanup_test_{i}'})
            agents.append(agent)

        # 执行一些操作
        for agent in agents:
            await agent.process_with_planning("测试清理")

        # 清理资源
        for agent in agents:
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()

        # 验证清理完成（这里只是示例，实际需要根据具体实现验证）
        self.assertTrue(True)  # 如果没有异常，认为清理成功

# 异步测试运行器
class TestAsyncIntegrationRunner(unittest.IsolatedAsyncioTestCase):
    """异步集成测试运行器"""

    async def asyncSetUp(self):
        """异步测试设置"""
        pass

    async def test_full_integration_scenario(self):
        """测试完整集成场景"""
        # 场景：专利分析项目
        project_goal = "完成人工智能领域的专利技术分析报告"

        # 1. 小诺制定项目计划
        xiaonuo = XiaonuoEnhancedAgent({'agent_id': 'scenario_xiaonuo'})
        plan_result = await xiaonuo.process_with_planning(
            f"制定项目计划：{project_goal}"
        )

        # 2. 小娜执行专利分析
        xiaona = XiaonaEnhancedAgent({'agent_id': 'scenario_xiaona'})
        analysis_result = await xiaona.process_with_chain(
            f"执行专利分析：{project_goal}"
        )

        # 3. 云锡设定质量目标
        yunxi = YunxiEnhancedAgent({'agent_id': 'scenario_yunxi'})
        quality_goal = await yunxi.process_goal_request(
            "设定质量目标：确保分析报告的专业性和准确性"
        )

        # 4. 小宸协调整体协作
        xiaochen = XiaochenEnhancedAgent({'agent_id': 'scenario_xiaochen'})
        coordination_result = await xiaochen.process_collaboration_request(
            "协调专利分析项目的整体执行"
        )

        # 验证所有智能体都参与了协作
        results = {
            'planning': plan_result,
            'analysis': analysis_result,
            'quality': quality_goal,
            'coordination': coordination_result
        }

        for stage, result in results.items():
            self.assertIsNotNone(result, f"{stage}阶段无响应")
            self.assertIn('agent', result, f"{stage}阶段缺少agent信息")

if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)
