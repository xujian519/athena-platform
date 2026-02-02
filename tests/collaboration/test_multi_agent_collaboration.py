#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多智能体协作框架测试
Multi-Agent Collaboration Framework Tests

测试多智能体协作框架的核心功能
"""

import unittest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from core.collaboration import (
    Agent, AgentCapability, Task, TaskStatus, Priority,
    MultiAgentCollaborationFramework, Message, MessageType
)
from core.collaboration.collaboration_patterns import (
    SequentialCollaborationPattern,
    ParallelCollaborationPattern,
    HierarchicalCollaborationPattern,
    ConsensusCollaborationPattern
)


class TestAgentCapability(unittest.TestCase):
    """测试智能体能力"""

    def test_agent_capability_creation(self):
        """测试能力创建"""
        capability = AgentCapability(
            name="test_capability",
            description="测试能力",
            max_concurrent_tasks=3,
            estimated_duration=timedelta(minutes=30)
        )

        self.assertEqual(capability.name, "test_capability")
        self.assertEqual(capability.max_concurrent_tasks, 3)
        self.assertEqual(capability.estimated_duration, timedelta(minutes=30))

    def test_agent_capability_dependencies(self):
        """测试能力依赖"""
        capability = AgentCapability(
            name="advanced_capability",
            description="高级能力",
            dependencies={"basic_capability"}
        )

        self.assertIn("basic_capability", capability.dependencies)
        self.assertEqual(len(capability.dependencies), 1)


class TestAgent(unittest.TestCase):
    """测试智能体"""

    def setUp(self):
        """设置测试环境"""
        self.capability = AgentCapability(
            name="test_capability",
            description="测试能力",
            max_concurrent_tasks=3
        )

        self.agent = Agent(
            id="test_agent_001",
            name="测试智能体",
            capabilities=[self.capability],
            max_load=5
        )

    def test_agent_creation(self):
        """测试智能体创建"""
        self.assertEqual(self.agent.id, "test_agent_001")
        self.assertEqual(self.agent.name, "测试智能体")
        self.assertEqual(len(self.agent.capabilities), 1)
        self.assertEqual(self.agent.status.value, "idle")
        self.assertEqual(self.agent.current_load, 0)

    def test_can_handle_task(self):
        """测试任务处理能力检查"""
        # 测试匹配的任务
        task_requirements = {"capabilities": ["test_capability"]}
        self.assertTrue(self.agent.can_handle_task(task_requirements))

        # 测试不匹配的任务
        task_requirements = {"capabilities": ["unknown_capability"]}
        self.assertFalse(self.agent.can_handle_task(task_requirements))

    def test_load_management(self):
        """测试负载管理"""
        # 智能体初始负载为0，最大负载为5
        self.assertEqual(self.agent.current_load, 0)
        self.assertEqual(self.agent.max_load, 5)

        # 增加负载
        self.agent.current_load = 3
        self.assertFalse(self.agent.can_handle_task({"capabilities": ["test_capability"]}))

        # 负载达到最大值
        self.agent.current_load = 5
        self.assertFalse(self.agent.can_handle_task({"capabilities": ["test_capability"]}))

    def test_suitability_score(self):
        """测试适合度分数计算"""
        task_requirements = {"capabilities": ["test_capability"]}
        score = self.agent.calculate_suitability_score(task_requirements)

        # 分数应该在0-1之间
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

        # 对于空闲智能体，分数应该较高
        self.assertGreater(score, 0.5)


class TestTask(unittest.TestCase):
    """测试任务"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(
            title="测试任务",
            description="这是一个测试任务",
            required_capabilities=["test_capability"],
            priority=Priority.HIGH
        )

        self.assertEqual(task.title, "测试任务")
        self.assertEqual(task.description, "这是一个测试任务")
        self.assertEqual(task.required_capabilities, ["test_capability"])
        self.assertEqual(task.priority, Priority.HIGH)
        self.assertEqual(task.status, TaskStatus.PENDING)

    def test_task_dependencies(self):
        """测试任务依赖"""
        task = Task(title="主任务")

        # 添加依赖
        task.add_dependency("task_001")
        task.add_dependency("task_002")

        self.assertEqual(len(task.dependencies), 2)
        self.assertIn("task_001", task.dependencies)
        self.assertIn("task_002", task.dependencies)

    def test_task_assignment(self):
        """测试任务分配"""
        task = Task(title="分配测试任务")

        # 分配智能体
        task.assign_agent("agent_001")
        task.assign_agent("agent_002")

        self.assertEqual(len(task.assigned_agents), 2)
        self.assertIn("agent_001", task.assigned_agents)
        self.assertIn("agent_002", task.assigned_agents)

    def test_task_progress(self):
        """测试任务进度"""
        task = Task(title="进度测试任务")

        # 更新进度
        task.update_progress(0.5)
        self.assertEqual(task.progress, 0.5)
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)

        # 完成任务
        task.update_progress(1.0)
        self.assertEqual(task.progress, 1.0)
        self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_task_can_start(self):
        """测试任务开始条件"""
        task = Task(title="依赖测试任务")
        task.add_dependency("task_001")

        # 依赖未完成时不能开始
        completed_tasks = set()
        self.assertFalse(task.can_start(completed_tasks))

        # 依赖完成后可以开始
        completed_tasks.add("task_001")
        self.assertTrue(task.can_start(completed_tasks))


class TestMessage(unittest.TestCase):
    """测试消息"""

    def test_message_creation(self):
        """测试消息创建"""
        message = Message(
            sender_id="agent_001",
            receiver_id="agent_002",
            message_type=MessageType.TASK_REQUEST,
            content={"action": "test", "data": "test_data"},
            priority=Priority.HIGH
        )

        self.assertEqual(message.sender_id, "agent_001")
        self.assertEqual(message.receiver_id, "agent_002")
        self.assertEqual(message.message_type, MessageType.TASK_REQUEST)
        self.assertEqual(message.content["action"], "test")
        self.assertEqual(message.priority, Priority.HIGH)

    def test_message_response_requirement(self):
        """测试消息响应要求"""
        message = Message(
            sender_id="agent_001",
            receiver_id="agent_002",
            message_type=MessageType.TASK_REQUEST,
            requires_response=True
        )

        self.assertTrue(message.requires_response)
        self.assertIsNotNone(message.correlation_id)  # 应该自动生成关联ID


class TestMultiAgentCollaborationFramework(unittest.TestCase):
    """测试多智能体协作框架"""

    def setUp(self):
        """设置测试环境"""
        self.framework = MultiAgentCollaborationFramework()

        # 创建测试智能体
        self.agent1 = Agent(
            id="agent_001",
            name="智能体1",
            capabilities=[
                AgentCapability(name="capability1", description="能力1"),
                AgentCapability(name="capability2", description="能力2")
            ]
        )

        self.agent2 = Agent(
            id="agent_002",
            name="智能体2",
            capabilities=[
                AgentCapability(name="capability1", description="能力1"),
                AgentCapability(name="capability3", description="能力3")
            ]
        )

    def test_framework_initialization(self):
        """测试框架初始化"""
        self.assertIsNotNone(self.framework.agents)
        self.assertIsNotNone(self.framework.tasks)
        self.assertIsNotNone(self.framework.message_broker)
        self.assertIsNotNone(self.framework.resource_manager)

    def test_agent_registration(self):
        """测试智能体注册"""
        # 注册智能体
        result = self.framework.register_agent(self.agent1)
        self.assertTrue(result)
        self.assertIn("agent_001", self.framework.agents)

        # 重复注册应该失败
        result = self.framework.register_agent(self.agent1)
        self.assertFalse(result)

    def test_agent_unregistration(self):
        """测试智能体注销"""
        # 先注册
        self.framework.register_agent(self.agent1)

        # 注销
        result = self.framework.unregister_agent("agent_001")
        self.assertTrue(result)
        self.assertNotIn("agent_001", self.framework.agents)

        # 注销不存在的智能体应该失败
        result = self.framework.unregister_agent("nonexistent")
        self.assertFalse(result)

    def test_task_creation(self):
        """测试任务创建"""
        task_definition = {
            "title": "测试协作任务",
            "description": "这是一个测试协作任务",
            "required_capabilities": ["capability1"],
            "priority": 2
        }

        task = self.framework.create_task(task_definition)

        self.assertIsNotNone(task)
        self.assertEqual(task.title, "测试协作任务")
        self.assertEqual(task.required_capabilities, ["capability1"])
        self.assertIn(task.id, self.framework.tasks)

    def test_task_assignment(self):
        """测试任务分配"""
        # 注册智能体
        self.framework.register_agent(self.agent1)
        self.framework.register_agent(self.agent2)

        # 创建任务
        task_definition = {
            "title": "分配测试任务",
            "required_capabilities": ["capability1"]
        }
        task = self.framework.create_task(task_definition)

        # 分配任务
        result = self.framework.assign_task(task.id, ["agent_001", "agent_002"])
        self.assertTrue(result)

        # 检查任务状态
        assigned_task = self.framework.tasks[task.id]
        self.assertEqual(assigned_task.status, TaskStatus.ASSIGNED)
        self.assertIn("agent_001", assigned_task.assigned_agents)
        self.assertIn("agent_002", assigned_task.assigned_agents)

    def test_find_suitable_agents(self):
        """测试查找合适的智能体"""
        # 注册智能体
        self.framework.register_agent(self.agent1)
        self.framework.register_agent(self.agent2)

        # 查找合适的智能体
        task_requirements = {"capabilities": ["capability1"]}
        suitable_agents = self.framework.find_suitable_agents(task_requirements)

        # 应该找到两个智能体都有capability1
        self.assertEqual(len(suitable_agents), 2)

        # 查找只有agent1有的能力
        task_requirements = {"capabilities": ["capability2"]}
        suitable_agents = self.framework.find_suitable_agents(task_requirements)

        # 应该只找到agent1
        self.assertEqual(len(suitable_agents), 1)
        self.assertEqual(suitable_agents[0][0], "agent_001")

    def test_framework_status(self):
        """测试框架状态"""
        # 注册智能体和创建任务
        self.framework.register_agent(self.agent1)
        self.framework.register_agent(self.agent2)

        task_definition = {"title": "状态测试任务"}
        self.framework.create_task(task_definition)

        # 获取状态
        status = self.framework.get_framework_status()

        self.assertIn("agents", status)
        self.assertIn("tasks", status)
        self.assertIn("sessions", status)
        self.assertIn("resources", status)

        self.assertEqual(status["agents"]["total"], 2)
        self.assertEqual(status["tasks"]["total"], 1)


class TestSequentialCollaborationPattern(unittest.TestCase):
    """测试串行协作模式"""

    def setUp(self):
        """设置测试环境"""
        self.framework = MultiAgentCollaborationFramework()
        self.pattern = SequentialCollaborationPattern(self.framework)

    def test_pattern_initialization(self):
        """测试模式初始化"""
        self.assertEqual(self.pattern.pattern_name, "串行协作")
        self.assertIsNotNone(self.pattern.active_sessions)

    def test_participant_sorting(self):
        """测试参与者排序"""
        # 创建不同能力的智能体
        agent1 = Agent(
            id="agent_high",
            name="高优先级智能体",
            capabilities=[AgentCapability(name="capability1", description="能力1")]
        )
        agent2 = Agent(
            id="agent_low",
            name="低优先级智能体",
            capabilities=[AgentCapability(name="capability1", description="能力1")]
        )

        # 设置不同负载
        agent1.current_load = 1
        agent2.current_load = 3

        self.framework.register_agent(agent1)
        self.framework.register_agent(agent2)

        # 创建任务
        task = Task(
            title="排序测试任务",
            required_capabilities=["capability1"]
        )

        # 测试排序
        sorted_participants = self.pattern._sort_participants(
            ["agent_low", "agent_high"], task
        )

        # 高优先级智能体应该排在前面
        self.assertEqual(sorted_participants[0], "agent_high")


class TestParallelCollaborationPattern(unittest.TestCase):
    """测试并行协作模式"""

    def setUp(self):
        """设置测试环境"""
        self.framework = MultiAgentCollaborationFramework()
        self.pattern = ParallelCollaborationPattern(self.framework)

    def test_pattern_initialization(self):
        """测试模式初始化"""
        self.assertEqual(self.pattern.pattern_name, "并行协作")

    def test_agent_grouping_by_capability(self):
        """测试按能力分组智能体"""
        # 创建不同能力的智能体
        agent1 = Agent(
            id="agent_1",
            name="智能体1",
            capabilities=[AgentCapability(name="capability1", description="能力1")]
        )
        agent2 = Agent(
            id="agent_2",
            name="智能体2",
            capabilities=[AgentCapability(name="capability2", description="能力2")]
        )
        agent3 = Agent(
            id="agent_3",
            name="智能体3",
            capabilities=[AgentCapability(name="capability1", description="能力1")]
        )

        self.framework.register_agent(agent1)
        self.framework.register_agent(agent2)
        self.framework.register_agent(agent3)

        # 测试分组
        groups = self.pattern._group_agents_by_capability(["agent_1", "agent_2", "agent_3"])

        self.assertIn("capability1", groups)
        self.assertIn("capability2", groups)
        self.assertEqual(len(groups["capability1"]), 2)
        self.assertEqual(len(groups["capability2"]), 1)


class TestHierarchicalCollaborationPattern(unittest.TestCase):
    """测试层次协作模式"""

    def setUp(self):
        """设置测试环境"""
        self.framework = MultiAgentCollaborationFramework()
        self.pattern = HierarchicalCollaborationPattern(self.framework)

    def test_pattern_initialization(self):
        """测试模式初始化"""
        self.assertEqual(self.pattern.pattern_name, "层次协作")

    def test_role_identification(self):
        """测试角色识别"""
        # 创建协调者智能体
        coordinator = Agent(
            id="coordinator",
            name="协调者",
            capabilities=[AgentCapability(name="coordination", description="协调能力")],
            metadata={"role": "coordinator"}
        )

        # 创建工作者智能体
        worker1 = Agent(
            id="worker1",
            name="工作者1",
            capabilities=[AgentCapability(name="work", description="工作能力")],
            metadata={"role": "worker"}
        )
        worker2 = Agent(
            id="worker2",
            name="工作者2",
            capabilities=[AgentCapability(name="work", description="工作能力")],
            metadata={"role": "worker"}
        )

        # 测试角色识别
        coordinator_id, workers = self.pattern._identify_roles(["coordinator", "worker1", "worker2"])

        self.assertEqual(coordinator_id, "coordinator")
        self.assertEqual(len(workers), 2)
        self.assertIn("worker1", workers)
        self.assertIn("worker2", workers)


class TestConsensusCollaborationPattern(unittest.TestCase):
    """测试共识协作模式"""

    def setUp(self):
        """设置测试环境"""
        self.framework = MultiAgentCollaborationFramework()
        self.pattern = ConsensusCollaborationPattern(self.framework)

    def test_pattern_initialization(self):
        """测试模式初始化"""
        self.assertEqual(self.pattern.pattern_name, "共识协作")

    def test_vote_aggregation(self):
        """测试投票聚合"""
        # 模拟投票结果
        votes = {
            "agent1": {"decision": "agree", "proposal": "proposal1"},
            "agent2": {"decision": "agree", "proposal": "proposal1"},
            "agent3": {"decision": "disagree", "proposal": "proposal2"},
            "agent4": {"decision": "agree", "proposal": "proposal1"}
        }

        # 测试决策聚合
        decision = self.pattern._aggregate_votes_to_decision(votes)

        self.assertEqual(decision["decision"], "consensus_reached")
        self.assertEqual(decision["proposal"], "proposal1")
        self.assertEqual(decision["support_count"], 3)
        self.assertEqual(decision["total_participants"], 4)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)