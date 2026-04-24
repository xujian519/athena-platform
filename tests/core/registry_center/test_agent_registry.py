"""
统一Agent注册表测试

测试UnifiedAgentRegistry的功能，验证3个原有注册表的整合。
"""

import pytest
import asyncio

from core.registry_center.agent_registry import (
    AgentInfo,
    AgentStatus,
    AgentType,
    UnifiedAgentRegistry,
    get_agent_registry,
)


class TestUnifiedAgentRegistry:
    """测试统一Agent注册表"""

    def setup_method(self):
        """测试前准备"""
        self.registry = get_agent_registry()
        self.registry.clear()

    def teardown_method(self):
        """测试后清理"""
        self.registry.clear()

    def test_register_and_unregister_agent(self):
        """测试Agent注册和注销"""
        agent_info = AgentInfo(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            name="测试Agent",
            description="这是一个测试Agent",
            capabilities=["搜索", "检索"],
        )

        # 注册Agent
        success = self.registry.register_agent(agent_info)
        assert success is True

        # 验证注册成功
        assert self.registry.exists("test_agent") is True
        assert self.registry.count() == 1

        # 注销Agent
        success = self.registry.unregister_agent("test_agent")
        assert success is True

        # 验证注销成功
        assert self.registry.exists("test_agent") is False

    def test_get_agent_info(self):
        """测试获取Agent信息"""
        agent_info = AgentInfo(
            agent_id="test_agent",
            agent_type=AgentType.ANALYSIS,
            name="分析Agent",
            description="分析测试",
        )

        self.registry.register_agent(agent_info)

        # 获取Agent信息
        retrieved = self.registry.get_agent_info("test_agent")
        assert retrieved is not None
        assert retrieved.agent_id == "test_agent"
        assert retrieved.name == "分析Agent"
        assert retrieved.agent_type == AgentType.ANALYSIS

    def test_find_agents_by_type(self):
        """测试按类型查找Agent"""
        # 注册不同类型的Agent
        agents = [
            AgentInfo(
                agent_id="searcher1",
                agent_type=AgentType.SEARCH,
                name="搜索器1",
                description="搜索",
            ),
            AgentInfo(
                agent_id="searcher2",
                agent_type=AgentType.SEARCH,
                name="搜索器2",
                description="搜索",
            ),
            AgentInfo(
                agent_id="analyzer1",
                agent_type=AgentType.ANALYSIS,
                name="分析器1",
                description="分析",
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 按类型查找
        search_agents = self.registry.find_agents_by_type(AgentType.SEARCH)
        analysis_agents = self.registry.find_agents_by_type(AgentType.ANALYSIS)

        assert len(search_agents) == 2
        assert len(analysis_agents) == 1

    def test_find_agents_by_type_with_status(self):
        """测试按类型和状态查找Agent"""
        # 注册Agent
        agent1 = AgentInfo(
            agent_id="agent1",
            agent_type=AgentType.SEARCH,
            name="Agent1",
            description="Test",
            status=AgentStatus.IDLE,
        )
        agent2 = AgentInfo(
            agent_id="agent2",
            agent_type=AgentType.SEARCH,
            name="Agent2",
            description="Test",
            status=AgentStatus.BUSY,
        )

        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)

        # 查找IDLE状态的Agent
        idle_agents = self.registry.find_agents_by_type(AgentType.SEARCH, AgentStatus.IDLE)
        assert len(idle_agents) == 1
        assert idle_agents[0].agent_id == "agent1"

    def test_find_available_agents(self):
        """测试查找可用Agent"""
        agents = [
            AgentInfo(
                agent_id="agent1",
                agent_type=AgentType.SEARCH,
                name="Agent1",
                description="Test",
                status=AgentStatus.IDLE,
            ),
            AgentInfo(
                agent_id="agent2",
                agent_type=AgentType.SEARCH,
                name="Agent2",
                description="Test",
                status=AgentStatus.BUSY,
            ),
            AgentInfo(
                agent_id="agent3",
                agent_type=AgentType.ANALYSIS,
                name="Agent3",
                description="Test",
                status=AgentStatus.IDLE,
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 查找所有可用Agent
        available = self.registry.find_available_agents()
        assert len(available) == 2

        # 按类型查找
        search_available = self.registry.find_available_agents(AgentType.SEARCH)
        assert len(search_available) == 1
        assert search_available[0].agent_id == "agent1"

    def test_find_agents_by_capability(self):
        """测试按能力查找Agent"""
        agents = [
            AgentInfo(
                agent_id="agent1",
                agent_type=AgentType.SEARCH,
                name="Agent1",
                description="Test",
                capabilities=["搜索", "检索", "分析"],
            ),
            AgentInfo(
                agent_id="agent2",
                agent_type=AgentType.ANALYSIS,
                name="Agent2",
                description="Test",
                capabilities=["分析", "评估"],
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 按能力查找
        search_agents = self.registry.find_agents_by_capability("搜索")
        analysis_agents = self.registry.find_agents_by_capability("分析")

        assert len(search_agents) == 1
        assert len(analysis_agents) == 2

    def test_find_agents_by_phase(self):
        """测试按阶段查找Agent"""
        agents = [
            AgentInfo(
                agent_id="agent1",
                agent_type=AgentType.XIAONA_COMPONENT,
                name="Agent1",
                description="Test",
                phase=1,
            ),
            AgentInfo(
                agent_id="agent2",
                agent_type=AgentType.XIAONA_COMPONENT,
                name="Agent2",
                description="Test",
                phase=1,
            ),
            AgentInfo(
                agent_id="agent3",
                agent_type=AgentType.XIAONA_COMPONENT,
                name="Agent3",
                description="Test",
                phase=2,
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 按阶段查找
        phase1_agents = self.registry.find_agents_by_phase(1)
        phase2_agents = self.registry.find_agents_by_phase(2)

        assert len(phase1_agents) == 2
        assert len(phase2_agents) == 1

    def test_get_best_agent(self):
        """测试获取最佳Agent"""
        agents = [
            AgentInfo(
                agent_id="agent1",
                agent_type=AgentType.SEARCH,
                name="Agent1",
                description="Test",
                status=AgentStatus.IDLE,
                capabilities=["搜索", "检索"],
                performance_metrics={"success_rate": 0.9},
            ),
            AgentInfo(
                agent_id="agent2",
                agent_type=AgentType.SEARCH,
                name="Agent2",
                description="Test",
                status=AgentStatus.IDLE,
                capabilities=["搜索"],
                performance_metrics={"success_rate": 0.8},
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 获取最佳Agent（无能力需求）
        best = self.registry.get_best_agent(AgentType.SEARCH)
        assert best is not None
        assert best.agent_id in ["agent1", "agent2"]

        # 获取最佳Agent（有能力需求）
        best_with_caps = self.registry.get_best_agent(
            AgentType.SEARCH, capabilities=["搜索", "检索"]
        )
        assert best_with_caps is not None
        assert best_with_caps.agent_id == "agent1"  # agent1有更高的匹配度

    def test_enable_disable_agent(self):
        """测试启用/禁用Agent"""
        agent_info = AgentInfo(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            name="Test",
            description="Test",
            enabled=True,
        )

        self.registry.register_agent(agent_info)

        # 禁用Agent
        self.registry.disable_agent("test_agent")
        retrieved = self.registry.get_agent_info("test_agent")
        assert retrieved.enabled is False

        # 启用Agent
        self.registry.enable_agent("test_agent")
        retrieved = self.registry.get_agent_info("test_agent")
        assert retrieved.enabled is True

    @pytest.mark.asyncio
    async def test_update_agent_status(self):
        """测试更新Agent状态"""
        agent_info = AgentInfo(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            name="Test",
            description="Test",
            status=AgentStatus.IDLE,
        )

        self.registry.register_agent(agent_info)

        # 更新状态
        await self.registry.update_agent_status(
            "test_agent", AgentStatus.BUSY, task_id="task123"
        )

        # 验证状态更新
        retrieved = self.registry.get_agent_info("test_agent")
        assert retrieved.status == AgentStatus.BUSY
        assert retrieved.current_task_id == "task123"

    @pytest.mark.asyncio
    async def test_update_heartbeat(self):
        """测试更新心跳"""
        agent_info = AgentInfo(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            name="Test",
            description="Test",
        )

        self.registry.register_agent(agent_info)

        # 更新心跳
        await self.registry.update_heartbeat("test_agent")

        # 验证心跳更新（通过健康检查）
        unhealthy = await self.registry.check_agent_health()
        assert "test_agent" not in unhealthy

    @pytest.mark.asyncio
    async def test_update_performance_metrics(self):
        """测试更新性能指标"""
        agent_info = AgentInfo(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            name="Test",
            description="Test",
        )

        self.registry.register_agent(agent_info)

        # 更新性能指标
        metrics = {"success_rate": 0.95, "avg_response_time": 0.5}
        await self.registry.update_performance_metrics("test_agent", metrics)

        # 验证指标更新
        retrieved = self.registry.get_agent_info("test_agent")
        assert retrieved.performance_metrics["success_rate"] == 0.95
        assert retrieved.performance_metrics["avg_response_time"] == 0.5

    def test_get_registry_stats(self):
        """测试获取统计信息"""
        agents = [
            AgentInfo(
                agent_id="agent1",
                agent_type=AgentType.SEARCH,
                name="Agent1",
                description="Test",
                status=AgentStatus.IDLE,
            ),
            AgentInfo(
                agent_id="agent2",
                agent_type=AgentType.SEARCH,
                name="Agent2",
                description="Test",
                status=AgentStatus.BUSY,
            ),
            AgentInfo(
                agent_id="agent3",
                agent_type=AgentType.ANALYSIS,
                name="Agent3",
                description="Test",
                status=AgentStatus.IDLE,
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 获取统计信息
        stats = self.registry.get_registry_stats()

        assert stats["total_agents"] == 3
        assert stats["agents_by_type"]["search"] == 2
        assert stats["agents_by_type"]["analysis"] == 1
        assert stats["agents_by_status"]["idle"] == 2
        assert stats["agents_by_status"]["busy"] == 1

    def test_list_all_agents(self):
        """测试列出所有Agent"""
        agents = [
            AgentInfo(
                agent_id="agent1",
                agent_type=AgentType.SEARCH,
                name="Agent1",
                description="Test",
            ),
            AgentInfo(
                agent_id="agent2",
                agent_type=AgentType.ANALYSIS,
                name="Agent2",
                description="Test",
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 列出所有Agent
        all_agents = self.registry.list_all_agents()
        assert len(all_agents) == 2

        # 验证返回的是字典格式
        assert isinstance(all_agents[0], dict)
        assert "agent_id" in all_agents[0]
        assert "name" in all_agents[0]

    def test_get_statistics(self):
        """测试获取统计信息"""
        agents = [
            AgentInfo(
                agent_id="agent1",
                agent_type=AgentType.XIAONA_COMPONENT,
                name="Agent1",
                description="Test",
                enabled=True,
                phase=1,
                capabilities=["搜索", "分析"],
            ),
            AgentInfo(
                agent_id="agent2",
                agent_type=AgentType.XIAONA_COMPONENT,
                name="Agent2",
                description="Test",
                enabled=False,
                phase=2,
                capabilities=["撰写"],
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 获取统计信息
        stats = self.registry.get_statistics()

        assert stats["total_agents"] == 2
        assert stats["enabled"] == 1
        assert stats["disabled"] == 1
        assert stats["total_capabilities"] == 3
        assert stats["phase_distribution"]["phase_1"] == 1
        assert stats["phase_distribution"]["phase_2"] == 1

    def test_list_capabilities(self):
        """测试列出所有能力"""
        agents = [
            AgentInfo(
                agent_id="agent1",
                agent_type=AgentType.SEARCH,
                name="Agent1",
                description="Test",
                capabilities=["搜索", "检索"],
            ),
            AgentInfo(
                agent_id="agent2",
                agent_type=AgentType.ANALYSIS,
                name="Agent2",
                description="Test",
                capabilities=["分析", "评估"],
            ),
        ]

        for agent in agents:
            self.registry.register_agent(agent)

        # 列出所有能力
        capabilities = self.registry.list_capabilities()

        assert len(capabilities) == 4
        assert "搜索" in capabilities
        assert "检索" in capabilities
        assert "分析" in capabilities
        assert "评估" in capabilities


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
