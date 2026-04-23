"""
Swarm模式测试

测试Swarm状态管理和Agent功能。
"""


import pytest

from core.framework.collaboration.patterns.swarm_agent import SwarmAgent
from core.framework.collaboration.patterns.swarm_state import (
    AgentRole,
    SharedKnowledge,
    SwarmHealth,
    SwarmMetrics,
    SwarmState,
)


class TestSwarmState:
    """SwarmState功能测试"""

    @pytest.fixture
    async def swarm_state(self):
        """创建SwarmState实例"""
        state = SwarmState("test_swarm")
        yield state
        # 清理

    @pytest.mark.asyncio
    async def test_swarm_state_initialization(self):
        """测试SwarmState初始化"""
        state = SwarmState("test_swarm")
        assert state.swarm_id == "test_swarm"
        assert len(state._agents) == 0
        assert len(state._knowledge) == 0
        assert state._health == SwarmHealth.HEALTHY

    @pytest.mark.asyncio
    async def test_add_agent(self, swarm_state):
        """测试添加Agent"""
        await swarm_state.add_agent("agent_1", ["test", "analysis"])

        agent = await swarm_state.get_agent("agent_1")
        assert agent is not None
        assert agent.agent_id == "agent_1"
        assert agent.capabilities == ["test", "analysis"]
        assert agent.role == AgentRole.WORKER

    @pytest.mark.asyncio
    async def test_add_duplicate_agent(self, swarm_state):
        """测试添加重复Agent"""
        await swarm_state.add_agent("agent_1")
        await swarm_state.add_agent("agent_1")

        agents = await swarm_state.list_agents()
        assert len(agents) == 1

    @pytest.mark.asyncio
    async def test_remove_agent(self, swarm_state):
        """测试移除Agent"""
        await swarm_state.add_agent("agent_1")
        await swarm_state.remove_agent("agent_1")

        agent = await swarm_state.get_agent("agent_1")
        assert agent is None

    @pytest.mark.asyncio
    async def test_list_agents_by_role(self, swarm_state):
        """测试按角色列出Agent"""
        await swarm_state.add_agent("agent_1")
        await swarm_state.add_agent("agent_2")

        # 给agent_1分配COORDINATOR角色
        await swarm_state.assign_role("agent_1", AgentRole.COORDINATOR)

        coordinators = await swarm_state.list_agents(role=AgentRole.COORDINATOR)
        assert len(coordinators) == 1
        assert coordinators[0].agent_id == "agent_1"

    @pytest.mark.asyncio
    async def test_update_agent_load(self, swarm_state):
        """测试更新Agent负载"""
        await swarm_state.add_agent("agent_1")
        await swarm_state.update_agent_load("agent_1", 0.7)

        agent = await swarm_state.get_agent("agent_1")
        assert agent.load == 0.7

    @pytest.mark.asyncio
    async def test_assign_role(self, swarm_state):
        """测试分配角色"""
        await swarm_state.add_agent("agent_1")
        await swarm_state.assign_role("agent_1", AgentRole.COORDINATOR)

        agent = await swarm_state.get_agent("agent_1")
        assert agent.role == AgentRole.COORDINATOR

    @pytest.mark.asyncio
    async def test_add_knowledge(self, swarm_state):
        """测试添加共享知识"""
        knowledge = await swarm_state.add_knowledge(
            "test_knowledge",
            {"key1": "value1"}
        )

        assert knowledge.knowledge_id == "test_knowledge"
        assert knowledge.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_update_knowledge(self, swarm_state):
        """测试更新共享知识"""
        await swarm_state.add_knowledge("test_knowledge")
        await swarm_state.update_knowledge("test_knowledge", "key2", "value2", "agent_1")

        knowledge = await swarm_state.get_knowledge("test_knowledge")
        assert knowledge.get("key2") == "value2"
        assert "agent_1" in knowledge.contributors

    @pytest.mark.asyncio
    async def test_get_metrics(self, swarm_state):
        """测试获取指标"""
        await swarm_state.add_agent("agent_1")
        await swarm_state.add_agent("agent_2")

        metrics = await swarm_state.get_metrics()
        assert metrics.total_agents == 2
        assert metrics.active_agents == 2

    @pytest.mark.asyncio
    async def test_get_available_agents(self, swarm_state):
        """测试获取可用Agent"""
        await swarm_state.add_agent("agent_1", ["test"])
        await swarm_state.add_agent("agent_2", ["test"])

        # agent_2设置为高负载
        await swarm_state.update_agent_load("agent_2", 0.9)

        available = await swarm_state.get_available_agents()
        assert len(available) == 1
        assert available[0].agent_id == "agent_1"

    @pytest.mark.asyncio
    async def test_health_status(self, swarm_state):
        """测试健康状态"""
        # 初始状态（无Agent）应该是CRITICAL
        health = await swarm_state.get_health()
        assert health == SwarmHealth.CRITICAL

        # 添加Agent后应该是健康
        await swarm_state.add_agent("agent_1")
        health = await swarm_state.get_health()
        assert health == SwarmHealth.HEALTHY

        # 添加高负载Agent后应该是DEGRADED
        await swarm_state.update_agent_load("agent_1", 0.95)
        health = await swarm_state.get_health()
        assert health == SwarmHealth.DEGRADED


class TestSharedKnowledge:
    """SharedKnowledge功能测试"""

    def test_knowledge_initialization(self):
        """测试知识初始化"""
        knowledge = SharedKnowledge("test_knowledge")
        assert knowledge.knowledge_id == "test_knowledge"
        assert knowledge.version == 1
        assert len(knowledge.data) == 0

    def test_update_knowledge(self):
        """测试更新知识"""
        knowledge = SharedKnowledge("test_knowledge")
        knowledge.update("key1", "value1", "agent_1")

        assert knowledge.get("key1") == "value1"
        assert knowledge.version == 2
        assert "agent_1" in knowledge.contributors

    def test_merge_knowledge(self):
        """测试合并知识"""
        knowledge1 = SharedKnowledge("k1", {"a": 1})
        knowledge2 = SharedKnowledge("k2", {"b": 2})

        knowledge1.merge(knowledge2)

        assert knowledge1.get("a") == 1
        assert knowledge1.get("b") == 2


class TestSwarmAgent:
    """SwarmAgent功能测试"""

    @pytest.fixture
    def swarm_agent(self):
        """创建SwarmAgent实例"""
        return SwarmAgent(
            agent_id="agent_1",
            initial_role=AgentRole.WORKER,
            capabilities=["test", "analysis"],
        )

    @pytest.mark.asyncio
    async def test_agent_initialization(self, swarm_agent):
        """测试Agent初始化"""
        assert swarm_agent.agent_id == "agent_1"
        assert swarm_agent.get_role() == AgentRole.WORKER
        assert swarm_agent.get_capabilities() == ["test", "analysis"]

    @pytest.mark.asyncio
    async def test_execute_task(self, swarm_agent):
        """测试执行任务"""
        result = await swarm_agent.execute_task("task_1", {"data": "test"})

        assert result["task_id"] == "task_1"
        assert result["status"] == "completed"
        assert "task_1" in swarm_agent.get_task_history()

    @pytest.mark.asyncio
    async def test_change_role(self, swarm_agent):
        """测试改变角色"""
        await swarm_agent.change_role(AgentRole.COORDINATOR)

        assert swarm_agent.get_role() == AgentRole.COORDINATOR

    @pytest.mark.asyncio
    async def test_update_load(self, swarm_agent):
        """测试更新负载"""
        await swarm_agent.update_load(0.7)

        state = swarm_agent.get_state()
        assert state.load == 0.7

    @pytest.mark.asyncio
    async def test_is_available(self, swarm_agent):
        """测试可用性检查"""
        # 初始状态应该可用
        assert swarm_agent.is_available() is True

        # 设置高负载后不可用
        await swarm_agent.update_load(0.9)
        assert swarm_agent.is_available() is False


class TestSwarmMetrics:
    """SwarmMetrics功能测试"""

    def test_metrics_initialization(self):
        """测试指标初始化"""
        metrics = SwarmMetrics()
        assert metrics.total_agents == 0
        assert metrics.active_agents == 0
        assert metrics.average_load == 0.0

    def test_metrics_update(self):
        """测试指标更新"""
        metrics = SwarmMetrics()
        metrics.update(total_agents=5, active_agents=5)

        assert metrics.total_agents == 5
        assert metrics.active_agents == 5

    def test_metrics_to_dict(self):
        """测试转换为字典"""
        metrics = SwarmMetrics(total_agents=5)
        data = metrics.to_dict()

        assert data["total_agents"] == 5
        assert "last_update" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
