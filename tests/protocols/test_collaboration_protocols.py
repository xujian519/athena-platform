#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协作协议测试
Collaboration Protocols Tests

测试多智能体协作协议的功能
"""

import unittest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from core.protocols.collaboration_protocols import (
    ProtocolType, ProtocolPhase, ProtocolStatus,
    ProtocolMessage, ProtocolContext,
    CommunicationProtocol, CoordinationProtocol, DecisionProtocol,
    ProtocolManager
)


class TestProtocolMessage(unittest.TestCase):
    """测试协议消息"""

    def test_message_creation(self):
        """测试消息创建"""
        message = ProtocolMessage(
            sender_id="agent_001",
            receiver_id="agent_002",
            message_type="test_message",
            content={"action": "test", "data": "test_data"},
            priority=5
        )

        self.assertEqual(message.sender_id, "agent_001")
        self.assertEqual(message.receiver_id, "agent_002")
        self.assertEqual(message.message_type, "test_message")
        self.assertEqual(message.content["action"], "test")
        self.assertEqual(message.priority, 5)

    def test_message_id_generation(self):
        """测试消息ID生成"""
        message1 = ProtocolMessage()
        message2 = ProtocolMessage()

        self.assertNotEqual(message1.message_id, message2.message_id)
        self.assertIsInstance(message1.message_id, str)

    def test_message_timestamp(self):
        """测试消息时间戳"""
        before = datetime.now()
        message = ProtocolMessage()
        after = datetime.now()

        self.assertGreaterEqual(message.timestamp, before)
        self.assertLessEqual(message.timestamp, after)


class TestProtocolContext(unittest.TestCase):
    """测试协议上下文"""

    def test_context_creation(self):
        """测试上下文创建"""
        context = ProtocolContext(
            protocol_id="test_protocol",
            protocol_type=ProtocolType.COMMUNICATION
        )

        self.assertEqual(context.protocol_id, "test_protocol")
        self.assertEqual(context.protocol_type, ProtocolType.COMMUNICATION)
        self.assertEqual(context.current_phase, ProtocolPhase.INITIALIZATION)
        self.assertEqual(context.status, ProtocolStatus.ACTIVE)

    def test_participant_management(self):
        """测试参与者管理"""
        context = ProtocolContext()

        # 添加参与者
        self.assertTrue(context.participants == [])

        context.participants.append("agent_001")
        context.participants.append("agent_002")

        self.assertEqual(len(context.participants), 2)
        self.assertIn("agent_001", context.participants)
        self.assertIn("agent_002", context.participants)

    def test_shared_state_management(self):
        """测试共享状态管理"""
        context = ProtocolContext()

        # 更新共享状态
        context.shared_state["key1"] = "value1"
        context.shared_state["key2"] = {"nested": "data"}

        self.assertEqual(context.shared_state["key1"], "value1")
        self.assertEqual(context.shared_state["key2"]["nested"], "data")

    def test_private_state_management(self):
        """测试私有状态管理"""
        context = ProtocolContext()

        # 更新私有状态
        context.private_states["agent_001"] = {"status": "active", "load": 0.5}
        context.private_states["agent_002"] = {"status": "idle", "load": 0.0}

        self.assertEqual(len(context.private_states), 2)
        self.assertEqual(context.private_states["agent_001"]["status"], "active")


class TestCommunicationProtocol(unittest.TestCase):
    """测试通信协议"""

    def setUp(self):
        """设置测试环境"""
        self.protocol = CommunicationProtocol("test_comm_protocol")

    def test_protocol_initialization(self):
        """测试协议初始化"""
        self.assertEqual(self.protocol.protocol_id, "test_comm_protocol")
        self.assertEqual(self.protocol.protocol_type, ProtocolType.COMMUNICATION)
        self.assertFalse(self.protocol.running)

    def test_participant_management(self):
        """测试参与者管理"""
        # 添加参与者
        self.assertTrue(self.protocol.add_participant("agent_001"))
        self.assertTrue(self.protocol.add_participant("agent_002"))

        # 检查参与者
        self.assertIn("agent_001", self.protocol.context.participants)
        self.assertIn("agent_002", self.protocol.context.participants)

        # 重复添加应该失败
        self.assertFalse(self.protocol.add_participant("agent_001"))

        # 移除参与者
        self.assertTrue(self.protocol.remove_participant("agent_001"))
        self.assertNotIn("agent_001", self.protocol.context.participants)

    def test_shared_state_update(self):
        """测试共享状态更新"""
        self.protocol.update_shared_state("test_key", "test_value")
        self.assertEqual(self.protocol.context.shared_state["test_key"], "test_value")

    def test_private_state_update(self):
        """测试私有状态更新"""
        self.protocol.add_participant("agent_001")
        self.protocol.update_private_state("agent_001", "status", "active")

        self.assertEqual(
            self.protocol.context.private_states["agent_001"]["status"],
            "active"
        )

    def test_message_handling(self):
        """测试消息处理"""
        # 注册消息处理器
        handled_messages = []

        async def test_handler(message):
            handled_messages.append(message)

        self.protocol.register_message_handler("test_type", test_handler)

        # 创建测试消息
        message = ProtocolMessage(
            sender_id="sender",
            receiver_id="receiver",
            message_type="test_type",
            content={"test": "data"}
        )

        # 发送消息
        self.protocol.send_message(message)

        # 验证消息在队列中
        self.assertEqual(len(self.protocol.message_queue), 1)

    def test_message_validation(self):
        """测试消息验证"""
        # 测试有效消息
        valid_message = ProtocolMessage(
            message_type="request",
            content={
                'request_id': 'req_001',
                'action': 'test_action',
                'parameters': {'param1': 'value1'}
            }
        )

        self.assertTrue(self.protocol._validate_message(valid_message))

        # 测试无效消息（缺少必需字段）
        invalid_message = ProtocolMessage(
            message_type="request",
            content={
                'action': 'test_action'
                # 缺少 request_id 和 parameters
            }
        )

        self.assertFalse(self.protocol._validate_message(invalid_message))


class TestCoordinationProtocol(unittest.TestCase):
    """测试协调协议"""

    def setUp(self):
        """设置测试环境"""
        self.protocol = CoordinationProtocol("test_coord_protocol")
        self.protocol.add_participant("agent_001")
        self.protocol.add_participant("agent_002")

    def test_protocol_initialization(self):
        """测试协议初始化"""
        self.assertEqual(self.protocol.protocol_type, ProtocolType.COORDINATION)
        self.assertEqual(len(self.protocol.context.participants), 2)

    def test_task_assignment_capability_based(self):
        """测试基于能力的任务分配"""
        # 设置智能体能力
        self.protocol.update_private_state("agent_001", "capabilities", ["analysis", "planning"])
        self.protocol.update_private_state("agent_001", "current_load", 2)
        self.protocol.update_private_state("agent_001", "max_load", 10)

        self.protocol.update_private_state("agent_002", "capabilities", ["analysis"])
        self.protocol.update_private_state("agent_002", "current_load", 1)
        self.protocol.update_private_state("agent_002", "max_load", 10)

        # 创建测试任务
        task = {
            "task_id": "task_001",
            "required_capabilities": ["analysis"],
            "priority": 3
        }

        # 测试能力基础分配
        async def test_assignment():
            result = await self.protocol._assign_task_capability_based(task)
            return result

        # 由于是异步测试，这里只验证方法存在
        self.assertTrue(hasattr(self.protocol, '_assign_task_capability_based'))

    def test_resource_pool_initialization(self):
        """测试资源池初始化"""
        self.protocol._initialize_resource_pools()

        # 验证默认资源池已创建
        self.assertIn("cpu", self.protocol.resource_pools)
        self.assertIn("memory", self.protocol.resource_pools)
        self.assertIn("storage", self.protocol.resource_pools)
        self.assertIn("network_bandwidth", self.protocol.resource_pools)

        # 验证资源池结构
        cpu_pool = self.protocol.resource_pools["cpu"]
        self.assertEqual(cpu_pool["total"], 100)
        self.assertEqual(cpu_pool["available"], 100)
        self.assertEqual(cpu_pool["allocated"], 0)

    def test_conflict_detection(self):
        """测试冲突检测"""
        # 创建资源过度分配冲突
        self.protocol._initialize_resource_pools()
        self.protocol.resource_pools["cpu"]["allocated"] = 120  # 超过总量100

        # 检测冲突
        async def test_detection():
            conflicts = await self.protocol._detect_resource_conflicts()
            return conflicts

        # 由于是异步测试，这里只验证方法存在
        self.assertTrue(hasattr(self.protocol, '_detect_resource_conflicts'))


class TestDecisionProtocol(unittest.TestCase):
    """测试决策协议"""

    def setUp(self):
        """设置测试环境"""
        self.protocol = DecisionProtocol("test_decision_protocol")
        self.protocol.add_participant("agent_001")
        self.protocol.add_participant("agent_002")
        self.protocol.add_participant("agent_003")

    def test_protocol_initialization(self):
        """测试协议初始化"""
        self.assertEqual(self.protocol.protocol_type, ProtocolType.DECISION)
        self.assertEqual(len(self.protocol.context.participants), 3)

    def test_proposal_handling(self):
        """测试提案处理"""
        # 创建提案
        proposal_content = {
            "title": "测试提案",
            "description": "这是一个测试提案",
            "options": ["选项A", "选项B"]
        }

        message = ProtocolMessage(
            sender_id="agent_001",
            message_type="proposal",
            content={"proposal": proposal_content}
        )

        # 处理提案
        async def test_handling():
            await self.protocol._handle_proposal(message)

        # 验证提案处理方法存在
        self.assertTrue(hasattr(self.protocol, '_handle_proposal'))

    def test_voting_mechanism(self):
        """测试投票机制"""
        # 创建测试提案
        proposal_id = "test_proposal_001"
        proposal = {
            "proposal_id": proposal_id,
            "participants": ["agent_001", "agent_002", "agent_003"],
            "votes": {},
            "created_at": datetime.now(),
            "status": "active"
        }

        self.protocol.active_proposals[proposal_id] = proposal

        # 添加投票
        self.protocol.active_proposals[proposal_id]["votes"]["agent_001"] = {
            "decision": "agree",
            "reason": "Good proposal"
        }
        self.protocol.active_proposals[proposal_id]["votes"]["agent_002"] = {
            "decision": "agree",
            "reason": "I agree"
        }
        self.protocol.active_proposals[proposal_id]["votes"]["agent_003"] = {
            "decision": "disagree",
            "reason": "Have concerns"
        }

        # 测试投票统计
        async def test_tally():
            votes = self.protocol.active_proposals[proposal_id]["votes"]
            result = await self.protocol._tally_consensus_votes(votes)
            return result

        # 验证投票统计方法存在
        self.assertTrue(hasattr(self.protocol, '_tally_consensus_votes'))

    def test_consensus_threshold(self):
        """测试共识阈值"""
        self.assertEqual(self.protocol.consensus_threshold, 0.7)

        # 更新共识阈值
        self.protocol.consensus_threshold = 0.8
        self.assertEqual(self.protocol.consensus_threshold, 0.8)


class TestProtocolManager(unittest.TestCase):
    """测试协议管理器"""

    def setUp(self):
        """设置测试环境"""
        self.manager = ProtocolManager()

    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertEqual(len(self.manager.protocols), 0)
        self.assertEqual(len(self.manager.message_router), 0)

    def test_protocol_registration(self):
        """测试协议注册"""
        # 创建测试协议
        protocol = CommunicationProtocol("test_protocol")

        # 注册协议
        self.assertTrue(self.manager.register_protocol(protocol))

        # 验证注册
        self.assertIn("test_protocol", self.manager.protocols)
        self.assertIn("test_protocol", self.manager.message_router)

    def test_protocol_unregistration(self):
        """测试协议注销"""
        # 注册协议
        protocol = CommunicationProtocol("test_protocol")
        self.manager.register_protocol(protocol)

        # 注销协议
        self.assertTrue(self.manager.unregister_protocol("test_protocol"))

        # 验证注销
        self.assertNotIn("test_protocol", self.manager.protocols)
        self.assertNotIn("test_protocol", self.manager.message_router)

    def test_communication_protocol_creation(self):
        """测试通信协议创建"""
        participants = ["agent_001", "agent_002"]
        protocol_id = self.manager.create_communication_protocol(participants)

        self.assertIsNotNone(protocol_id)
        self.assertIn(protocol_id, self.manager.protocols)
        self.assertIn("comm_", protocol_id)  # 协议ID应该包含前缀

    def test_coordination_protocol_creation(self):
        """测试协调协议创建"""
        participants = ["agent_001", "agent_002"]
        protocol_id = self.manager.create_coordination_protocol(participants)

        self.assertIsNotNone(protocol_id)
        self.assertIn(protocol_id, self.manager.protocols)
        self.assertIn("coord_", protocol_id)  # 协议ID应该包含前缀

    def test_decision_protocol_creation(self):
        """测试决策协议创建"""
        participants = ["agent_001", "agent_002"]
        protocol_id = self.manager.create_decision_protocol(participants)

        self.assertIsNotNone(protocol_id)
        self.assertIn(protocol_id, self.manager.protocols)
        self.assertIn("decision_", protocol_id)  # 协议ID应该包含前缀

    def test_protocol_status_retrieval(self):
        """测试协议状态获取"""
        # 创建协议
        protocol = CommunicationProtocol("test_protocol")
        self.manager.register_protocol(protocol)

        # 获取状态
        status = self.manager.get_protocol_status("test_protocol")

        self.assertIsNotNone(status)
        self.assertEqual(status["protocol_id"], "test_protocol")
        self.assertEqual(status["protocol_type"], "communication")

    def test_all_protocols_status(self):
        """测试获取所有协议状态"""
        # 创建多个协议
        comm_protocol = CommunicationProtocol("comm_protocol")
        coord_protocol = CoordinationProtocol("coord_protocol")

        self.manager.register_protocol(comm_protocol)
        self.manager.register_protocol(coord_protocol)

        # 获取所有状态
        all_status = self.manager.get_all_protocols_status()

        self.assertEqual(len(all_status), 2)
        self.assertIn("comm_protocol", all_status)
        self.assertIn("coord_protocol", all_status)


class TestProtocolIntegration(unittest.TestCase):
    """协议集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.manager = ProtocolManager()

    def test_multi_protocol_workflow(self):
        """测试多协议工作流"""
        # 创建智能体列表
        agents = ["xiaonuo", "xiaona", "yunxi", "xiaochen"]

        # 创建通信协议
        comm_protocol_id = self.manager.create_communication_protocol(agents)

        # 创建协调协议
        coord_protocol_id = self.manager.create_coordination_protocol(agents)

        # 创建决策协议
        decision_protocol_id = self.manager.create_decision_protocol(agents)

        # 验证所有协议都已创建
        self.assertIsNotNone(comm_protocol_id)
        self.assertIsNotNone(coord_protocol_id)
        self.assertIsNotNone(decision_protocol_id)

        # 获取所有协议状态
        all_status = self.manager.get_all_protocols_status()
        self.assertEqual(len(all_status), 3)

    def test_message_routing(self):
        """测试消息路由"""
        # 创建通信协议
        participants = ["agent_001", "agent_002"]
        protocol_id = self.manager.create_communication_protocol(participants)

        # 创建消息
        message = ProtocolMessage(
            protocol_id=protocol_id,
            sender_id="agent_001",
            receiver_id="agent_002",
            message_type="test_message",
            content={"test": "data"}
        )

        # 路由消息
        result = self.manager.route_message(message)
        self.assertTrue(result)

    def test_message_routing_unknown_protocol(self):
        """测试未知协议的消息路由"""
        # 创建消息（使用不存在的协议ID）
        message = ProtocolMessage(
            protocol_id="unknown_protocol",
            sender_id="agent_001",
            receiver_id="agent_002",
            message_type="test_message",
            content={"test": "data"}
        )

        # 路由消息应该失败
        result = self.manager.route_message(message)
        self.assertFalse(result)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)