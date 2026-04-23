#!/usr/bin/env python3

"""
Swarm协作模式测试
Swarm Collaboration Pattern Tests

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

测试Swarm群体智能协作模式的各项功能。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.framework.collaboration.multi_agent_collaboration import (
    Message,
    MessageType,
    MultiAgentCollaborationFramework,
    Task,
)
from core.framework.collaboration.patterns.swarm import SwarmCollaborationPattern
from core.framework.collaboration.patterns.swarm_agent import (
    SwarmAgent,
    SwarmKnowledgeItem,
    SwarmSharedState,
    SwarmStatistics,
    SwarmTask,
    TaskStatus,
)
from core.framework.collaboration.patterns.swarm_state import (
    AgentRole as SwarmRole,
)
from core.framework.collaboration.patterns.swarm_state import (
    SwarmDecisionType,
    SwarmEmergencyType,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_framework():
    """创建模拟的协作框架"""
    framework = MagicMock(spec=MultiAgentCollaborationFramework)
    framework.message_broker = MagicMock()
    framework.message_broker.publish = AsyncMock()
    framework.message_broker.subscribe = MagicMock()
    framework.tasks = {}
    framework.agents = {}
    return framework


@pytest.fixture
def swarm_pattern(mock_framework):
    """创建Swarm协作模式实例"""
    # 传递mock_framework给SwarmCollaborationPattern
    return SwarmCollaborationPattern("test_swarm", mock_framework)


@pytest.fixture
def sample_task():
    """创建示例任务"""
    return SwarmTask(
        id="task_001",
        description="分析专利创造性",
        required_capabilities=["analyze", "search"],
    )


@pytest.fixture
def sample_agents():
    """创建示例Agent列表"""
    return ["agent_001", "agent_002", "agent_003", "agent_004", "agent_005"]


# ============================================================================
# SwarmAgent Tests
# ============================================================================


class TestSwarmAgent:
    """SwarmAgent单元测试"""

    def test_init_swarm_agent(self):
        """测试SwarmAgent初始化"""
        agent = SwarmAgent(
            agent_id="agent_001",
            capabilities=["search", "analyze", "write"],
            initial_role=SwarmRole.WORKER,
        )

        assert agent.agent_id == "agent_001"
        assert agent.capabilities == ["search", "analyze", "write"]
        assert agent.role == SwarmRole.WORKER
        assert agent.neighbors == []
        assert agent.is_active is True

    @pytest.mark.asyncio
    async def test_role_change(self):
        """测试角色变更"""
        agent = SwarmAgent(
            agent_id="agent_001",
            capabilities=["search"],
            initial_role=SwarmRole.WORKER,
        )

        await agent.change_role(SwarmRole.EXPLORER)
        assert agent.role == SwarmRole.EXPLORER

        # 验证角色历史
        assert SwarmRole.WORKER in agent.role_history

    def test_add_neighbor(self):
        """测试添加邻居"""
        agent = SwarmAgent(agent_id="agent_001", capabilities=[])

        agent.add_neighbor("agent_002")
        agent.add_neighbor("agent_003")

        assert "agent_002" in agent.neighbors
        assert "agent_003" in agent.neighbors
        assert len(agent.neighbors) == 2

    def test_remove_neighbor(self):
        """测试移除邻居"""
        agent = SwarmAgent(agent_id="agent_001", capabilities=[])
        agent.add_neighbor("agent_002")

        agent.remove_neighbor("agent_002")
        assert "agent_002" not in agent.neighbors

    def test_can_handle_task(self):
        """测试任务能力匹配"""
        agent = SwarmAgent(
            agent_id="agent_001",
            capabilities=["search", "analyze"],
        )

        SwarmTask(
            id="task_001",
            description="搜索专利",
            required_capabilities=["search"],
        )

        assert agent.can_handle_capability("search") is True
        assert agent.can_handle_capability("translate") is False

        # 测试can_handle_task方法
        task_requirements = {"required_capabilities": ["search"]}
        assert agent.can_handle_task(task_requirements) is True

        task_requirements2 = {"required_capabilities": ["translate"]}
        assert agent.can_handle_task(task_requirements2) is False

    @pytest.mark.asyncio
    async def test_update_load(self):
        """测试负载更新"""
        agent = SwarmAgent(agent_id="agent_001", capabilities=[])

        await agent.update_load(0.5)
        assert agent.current_load == 0.5

        await agent.update_load(0.3)
        assert agent.current_load == 0.3

    @pytest.mark.asyncio
    async def test_is_available(self):
        """测试可用性判断"""
        agent = SwarmAgent(agent_id="agent_001", capabilities=[])

        # 初始状态可用
        assert agent.is_available() is True

        # 高负载时不可用
        await agent.update_load(0.9)
        assert agent.is_available() is False

        # 非活跃状态不可用
        agent.current_load = 0.3
        agent.is_active = False
        assert agent.is_available() is False


# ============================================================================
# SwarmTask Tests
# ============================================================================


class TestSwarmTask:
    """SwarmTask单元测试"""

    def test_create_swarm_task(self):
        """测试创建Swarm任务"""
        task = SwarmTask(
            id="task_001",
            description="分析专利",
            required_capabilities=["analyze", "search"],
        )

        assert task.id == "task_001"
        assert task.description == "分析专利"
        assert task.required_capabilities == ["analyze", "search"]
        assert task.status == TaskStatus.PENDING
        assert task.assignees == []

    def test_add_subtask(self):
        """测试添加子任务"""
        parent = SwarmTask(id="parent", description="父任务", required_capabilities=[])

        child1 = SwarmTask(id="child1", description="子任务1", required_capabilities=[])
        child2 = SwarmTask(id="child2", description="子任务2", required_capabilities=[])

        parent.add_subtask(child1)
        parent.add_subtask(child2)

        assert len(parent.subtasks) == 2
        assert child1.parent_id == "parent"
        assert child2.parent_id == "parent"

    def test_assign_to_agent(self):
        """测试分配Agent"""
        task = SwarmTask(
            id="task_001",
            description="任务",
            required_capabilities=[],
        )

        task.assign_to("agent_001")
        assert "agent_001" in task.assignees
        assert task.status == TaskStatus.ASSIGNED

    def test_complete_task(self):
        """测试完成任务"""
        task = SwarmTask(
            id="task_001",
            description="任务",
            required_capabilities=[],
        )

        task.complete(result={"score": 0.95})
        assert task.status == TaskStatus.COMPLETED
        assert task.result == {"score": 0.95}

    def test_fail_task(self):
        """测试任务失败"""
        task = SwarmTask(
            id="task_001",
            description="任务",
            required_capabilities=[],
        )

        task.fail(error="资源不足")
        assert task.status == TaskStatus.FAILED
        assert task.error == "资源不足"


# ============================================================================
# SwarmSharedState Tests
# ============================================================================


class TestSwarmSharedState:
    """SwarmSharedState单元测试"""

    def test_init_shared_state(self):
        """测试初始化共享状态"""
        state = SwarmSharedState()

        assert state.member_states == {}
        assert state.emergency_flags == []
        assert isinstance(state.statistics, SwarmStatistics)

    def test_add_member_state(self):
        """测试添加成员状态"""
        state = SwarmSharedState()

        state.update_member_state("agent_001", {"role": "worker", "current_load": 0.5})

        assert "agent_001" in state.member_states
        # 成员状态是AgentState对象，需要访问属性
        assert state.member_states["agent_001"].role == SwarmRole.WORKER

    def test_add_knowledge(self):
        """测试添加知识"""
        state = SwarmSharedState()

        knowledge = SwarmKnowledgeItem(
            key="patent_info",
            value={"title": "测试专利"},
            source="agent_001",
            confidence=0.9,
        )

        state.add_knowledge(knowledge)

        # 知识通过get_knowledge访问
        retrieved = state.get_knowledge("patent_info")
        assert retrieved is not None
        assert retrieved.value["title"] == "测试专利"

    def test_get_knowledge(self):
        """测试获取知识"""
        state = SwarmSharedState()

        knowledge = SwarmKnowledgeItem(
            key="patent_info",
            value={"title": "测试专利"},
            source="agent_001",
            confidence=0.9,
        )

        state.add_knowledge(knowledge)
        retrieved = state.get_knowledge("patent_info")

        assert retrieved is not None
        assert retrieved.value["title"] == "测试专利"

    def test_emergency_flag(self):
        """测试紧急标志"""
        state = SwarmSharedState()

        assert state.is_emergency() is False

        state.add_emergency_flag("high_priority_task")
        assert state.is_emergency() is True
        assert "high_priority_task" in state.emergency_flags

        state.clear_emergency_flags()
        assert state.is_emergency() is False


# ============================================================================
# SwarmCollaborationPattern Tests
# ============================================================================


class TestSwarmCollaborationPattern:
    """SwarmCollaborationPattern集成测试"""

    @pytest.mark.asyncio
    async def test_initiate_collaboration(self, swarm_pattern, sample_task, sample_agents):
        """测试启动Swarm协作"""
        context = {
            "mode": "exploration",
            "decision_type": SwarmDecisionType.MAJORITY,
        }

        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context=context,
        )

        assert session_id is not None
        assert session_id in swarm_pattern.active_sessions

        session = swarm_pattern.active_sessions[session_id]
        assert session["task_id"] == sample_task.id
        assert session["participants"] == sample_agents
        assert session["mode"] == "exploration"

    @pytest.mark.asyncio
    async def test_add_member_dynamically(self, swarm_pattern, sample_task, sample_agents):
        """测试动态添加成员"""
        # 先启动协作
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents[:3],
            context={},
        )

        # 添加新成员
        success = await swarm_pattern.add_member(session_id, "agent_new")

        assert success is True

        session = swarm_pattern.active_sessions[session_id]
        # 检查agent是否在participants列表中（支持对象和字符串）
        found = any(
            p.agent_id == "agent_new" if hasattr(p, 'agent_id') else p == "agent_new"
            for p in session["participants"]
        )
        assert found, "agent_new should be in participants"
        assert "agent_new" in swarm_pattern.swarm_agents

    @pytest.mark.asyncio
    async def test_remove_member(self, swarm_pattern, sample_task, sample_agents):
        """测试移除成员"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        success = await swarm_pattern.remove_member(session_id, "agent_002")

        assert success is True

        session = swarm_pattern.active_sessions[session_id]
        assert "agent_002" not in session["participants"]
        assert "agent_002" not in swarm_pattern.swarm_agents

    @pytest.mark.asyncio
    async def test_coordinate_execution(self, swarm_pattern, sample_task, sample_agents):
        """测试协调执行"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        success = await swarm_pattern.coordinate_execution(session_id)

        assert success is True

    @pytest.mark.asyncio
    async def test_broadcast_message(self, swarm_pattern, sample_task, sample_agents):
        """测试广播消息"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        message = Message(
            sender_id="system",
            receiver_id="",
            message_type=MessageType.COORDINATION,
            content={
                "action": "role_change",
                "target_role": "explorer",
            },
        )

        await swarm_pattern.broadcast_message(session_id, message)

        # 验证消息已发布
        swarm_pattern.framework.message_broker.publish.assert_called()

    @pytest.mark.asyncio
    async def test_handle_proposal(self, swarm_pattern, sample_task, sample_agents):
        """测试处理提案"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={"decision_type": SwarmDecisionType.MAJORITY},
        )

        proposal = {
            "proposal_id": "prop_001",
            "proposer": "agent_001",
            "content": "使用BGE-M3模型",
            "type": "model_selection",
        }

        await swarm_pattern.handle_proposal(session_id, proposal)

        session = swarm_pattern.active_sessions[session_id]
        assert "prop_001" in session["proposals"]
        assert session["proposals"]["prop_001"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_handle_vote(self, swarm_pattern, sample_task, sample_agents):
        """测试处理投票"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        # 先添加提案
        proposal = {
            "proposal_id": "prop_001",
            "proposer": "agent_001",
            "content": "使用BGE-M3模型",
        }
        await swarm_pattern.handle_proposal(session_id, proposal)

        # 投票
        vote = {
            "proposal_id": "prop_001",
            "voter": "agent_002",
            "decision": "agree",
            "weight": 1.0,
        }

        await swarm_pattern.handle_vote(session_id, vote)

        session = swarm_pattern.active_sessions[session_id]
        assert len(session["proposals"]["prop_001"]["votes"]) == 1


# ============================================================================
# Self-Organization Tests
# ============================================================================


class TestSelfOrganization:
    """自组织机制测试"""

    @pytest.mark.asyncio
    async def test_automatic_role_assignment(self, swarm_pattern, sample_task, sample_agents):
        """测试自动角色分配"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={"mode": "exploration"},
        )

        # 触发自组织
        await swarm_pattern._self_organize(session_id)

        swarm_pattern.active_sessions[session_id]

        # 验证角色已分配
        for agent_id in sample_agents:
            agent = swarm_pattern.swarm_agents.get(agent_id)
            assert agent is not None
            assert agent.role in SwarmRole

    @pytest.mark.asyncio
    async def test_role_balance(self, swarm_pattern, sample_task, sample_agents):
        """测试角色平衡"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        await swarm_pattern._self_organize(session_id)

        # 验证角色分布合理
        role_counts = {}
        for agent in swarm_pattern.swarm_agents.values():
            role_counts[agent.role] = role_counts.get(agent.role, 0) + 1

        # 至少有不同角色
        assert len(role_counts) >= 2

    @pytest.mark.asyncio
    async def test_adaptive_role_change(self, swarm_pattern, sample_task, sample_agents):
        """测试自适应角色变更"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={"mode": "analysis"},
        )

        # 初始角色分配
        await swarm_pattern._self_organize(session_id)

        # 模拟环境变化
        session = swarm_pattern.active_sessions[session_id]
        session["mode"] = "exploration"

        # 重新组织
        await swarm_pattern._self_organize(session_id)

        # 验证角色已调整
        # (具体验证取决于实现逻辑)


# ============================================================================
# Distributed Decision Tests
# ============================================================================


class TestDistributedDecision:
    """分布式决策测试"""

    @pytest.mark.asyncio
    async def test_majority_vote(self, swarm_pattern, sample_task, sample_agents):
        """测试多数决投票"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={"decision_type": SwarmDecisionType.MAJORITY},
        )

        proposal = {
            "proposal_id": "prop_001",
            "content": "使用方案A",
        }

        await swarm_pattern.handle_proposal(session_id, proposal)

        # 投票：3票同意，2票反对
        for i, agent_id in enumerate(sample_agents):
            vote = {
                "proposal_id": "prop_001",
                "voter": agent_id,
                "decision": "agree" if i < 3 else "disagree",
            }
            await swarm_pattern.handle_vote(session_id, vote)

        # 检查结果
        session = swarm_pattern.active_sessions[session_id]
        proposal_state = session["proposals"]["prop_001"]

        assert proposal_state["status"] == "approved"

    @pytest.mark.asyncio
    async def test_consensus_threshold(self, swarm_pattern, sample_task, sample_agents):
        """测试共识阈值"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={
                "decision_type": SwarmDecisionType.CONSENSUS,
                "consensus_threshold": 0.8,
            },
        )

        proposal = {
            "proposal_id": "prop_001",
            "content": "重要决策",
        }

        await swarm_pattern.handle_proposal(session_id, proposal)

        # 80%同意才算通过（5人需要4票）
        for i, agent_id in enumerate(sample_agents):
            vote = {
                "proposal_id": "prop_001",
                "voter": agent_id,
                "decision": "agree" if i < 3 else "disagree",  # 只有3票同意
            }
            await swarm_pattern.handle_vote(session_id, vote)

        session = swarm_pattern.active_sessions[session_id]
        proposal_state = session["proposals"]["prop_001"]

        # 3/5 = 60% < 80%，应该未通过
        assert proposal_state["status"] != "approved"


# ============================================================================
# Emergency Response Tests
# ============================================================================


class TestEmergencyResponse:
    """紧急响应测试"""

    @pytest.mark.asyncio
    async def test_emergency_detection(self, swarm_pattern, sample_task, sample_agents):
        """测试紧急情况检测"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        # 模拟高优先级任务
        await swarm_pattern.initiate_emergency_mode(
            session_id,
            SwarmEmergencyType.TASK_FAILURE,
        )

        session = swarm_pattern.active_sessions[session_id]
        assert session["emergency_mode"]["active"] is True
        assert session["emergency_mode"]["type"] == SwarmEmergencyType.TASK_FAILURE

    @pytest.mark.asyncio
    async def test_emergency_team_formation(self, swarm_pattern, sample_task, sample_agents):
        """测试应急小组组建"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        await swarm_pattern.initiate_emergency_mode(
            session_id,
            SwarmEmergencyType.AGENT_FAILURE,
        )

        session = swarm_pattern.active_sessions[session_id]
        assert "emergency_team" in session
        assert len(session["emergency_team"]) > 0

    @pytest.mark.asyncio
    async def test_emergency_recovery(self, swarm_pattern, sample_task, sample_agents):
        """测试紧急恢复"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        # 进入紧急模式
        await swarm_pattern.initiate_emergency_mode(
            session_id,
            SwarmEmergencyType.TIMEOUT,
        )

        # 处理紧急情况
        await swarm_pattern.handle_emergency(session_id, {"action": "resolve"})

        # 退出紧急模式
        await swarm_pattern.exit_emergency_mode(session_id)

        session = swarm_pattern.active_sessions[session_id]
        assert session["emergency_mode"]["active"] is False


# ============================================================================
# State Synchronization Tests
# ============================================================================


class TestStateSynchronization:
    """状态同步测试"""

    @pytest.mark.asyncio
    async def test_gossip_protocol(self, swarm_pattern, sample_task, sample_agents):
        """测试Gossip协议"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        # 触发Gossip同步
        await swarm_pattern._gossip_sync(session_id)

        # 验证状态已传播
        session = swarm_pattern.active_sessions[session_id]
        assert session["sync_rounds"] > 0

    @pytest.mark.asyncio
    async def test_knowledge_sharing(self, swarm_pattern, sample_task, sample_agents):
        """测试知识共享"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        knowledge = SwarmKnowledgeItem(
            key="search_result",
            value={"patents": ["CN123", "CN456"]},
            source="agent_001",
            confidence=0.95,
        )

        await swarm_pattern.share_knowledge(session_id, knowledge)

        state = swarm_pattern.shared_states.get(session_id)
        assert state is not None
        assert "search_result" in state.knowledge_base

    @pytest.mark.asyncio
    async def test_state_conflict_resolution(self, swarm_pattern, sample_task, sample_agents):
        """测试状态冲突解决"""
        await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        # 模拟冲突
        state1 = {"version": 1, "value": "A"}
        state2 = {"version": 2, "value": "B"}

        resolved = await swarm_pattern._resolve_state_conflict(state1, state2)

        # 应该选择版本更高的
        assert resolved["version"] == 2


# ============================================================================
# Conflict Handling Tests
# ============================================================================


class TestConflictHandling:
    """冲突处理测试"""

    @pytest.mark.asyncio
    async def test_task_conflict_resolution(self, swarm_pattern, sample_task, sample_agents):
        """测试任务冲突解决"""
        from core.framework.collaboration.collaboration_manager import Conflict

        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        conflicts = [
            Conflict(
                conflict_id="conflict_001",
                conflict_type="resource_contention",
                involved_agents=["agent_001", "agent_002"],
                description="争用同一资源",
            )
        ]

        resolved = await swarm_pattern.handle_conflicts(session_id, conflicts)

        assert resolved is True

    @pytest.mark.asyncio
    async def test_decision_conflict(self, swarm_pattern, sample_task, sample_agents):
        """测试决策冲突"""
        from core.framework.collaboration.collaboration_manager import Conflict

        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        conflicts = [
            Conflict(
                conflict_id="conflict_002",
                conflict_type="disagreement",
                involved_agents=sample_agents,
                description="意见不一致",
            )
        ]

        resolved = await swarm_pattern.handle_conflicts(session_id, conflicts)

        assert resolved is True


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_swarm(self, mock_framework):
        """测试大规模群体"""
        # 创建100个Agent
        large_agents = [f"agent_{i:03d}" for i in range(100)]

        swarm = SwarmCollaborationPattern(mock_framework)
        task = Task(id="large_task", title="大规模任务", description="", status=TaskStatus.PENDING)

        session_id = await swarm.initiate_collaboration(
            task=task,
            participants=large_agents,
            context={},
        )

        assert session_id is not None
        assert len(swarm.swarm_agents) == 100

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_message_throughput(self, swarm_pattern, sample_task, sample_agents):
        """测试消息吞吐量"""
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={},
        )

        # 发送100条消息
        start_time = datetime.now()

        for i in range(100):
            message = Message(
                sender_id="test",
                receiver_id="",
                message_type=MessageType.COORDINATION,
                content={"index": i},
            )
            await swarm_pattern.broadcast_message(session_id, message)

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # 100条消息应该在合理时间内完成（<5秒）
        assert elapsed < 5.0


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_swarm_workflow(self, swarm_pattern, sample_task, sample_agents):
        """测试完整的Swarm工作流"""
        # 1. 启动协作
        session_id = await swarm_pattern.initiate_collaboration(
            task=sample_task,
            participants=sample_agents,
            context={"mode": "exploration"},
        )
        assert session_id is not None

        # 2. 自组织
        await swarm_pattern._self_organize(session_id)

        # 3. 分配任务
        swarm_task = SwarmTask(
            id="swarm_task_001",
            description="搜索相关专利",
            required_capabilities=["search"],
        )
        await swarm_pattern.assign_swarm_task(session_id, swarm_task)

        # 4. 共享知识
        knowledge = SwarmKnowledgeItem(
            key="patent_found",
            value={"patent_id": "CN123456"},
            source="agent_001",
            confidence=0.9,
        )
        await swarm_pattern.share_knowledge(session_id, knowledge)

        # 5. 协调执行
        await swarm_pattern.coordinate_execution(session_id)

        # 6. 验证结果
        session = swarm_pattern.active_sessions[session_id]
        assert session["status"] in ["running", "completed"]

