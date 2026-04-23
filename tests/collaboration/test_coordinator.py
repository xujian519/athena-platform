"""
Coordinator模式测试

测试Coordinator的核心功能。
"""


import pytest

from core.framework.collaboration.coordinator import Coordinator
from core.framework.collaboration.coordinator.types import (
    AgentInfo,
    AgentStatus,
    TaskInfo,
    TaskPriority,
)


class TestCoordinator:
    """Coordinator核心功能测试"""

    @pytest.fixture
    async def coordinator(self):
        """创建Coordinator实例"""
        coord = Coordinator("test_coordinator")
        await coord.start()
        yield coord
        await coord.stop()

    @pytest.fixture
    def sample_agent(self):
        """创建示例Agent"""
        return AgentInfo(
            agent_id="agent_1",
            name="Test Agent",
            status=AgentStatus.IDLE,
            capabilities=["test_task", "analysis"],
        )

    @pytest.fixture
    def sample_task(self):
        """创建示例任务"""
        return TaskInfo(
            task_id="task_1",
            task_type="test_task",
            priority=TaskPriority.HIGH,
            payload={"data": "test"},
        )

    def test_coordinator_initialization(self):
        """测试Coordinator初始化"""
        coord = Coordinator("test_coordinator")
        assert coord.coordinator_id == "test_coordinator"
        assert not coord._running
        assert len(coord._agents) == 0
        assert len(coord._tasks) == 0

    @pytest.mark.asyncio
    async def test_coordinator_start_stop(self, coordinator):
        """测试启动和停止"""
        assert coordinator._running is True

        await coordinator.stop()
        assert coordinator._running is False

    @pytest.mark.asyncio
    async def test_register_agent(self, coordinator, sample_agent):
        """测试Agent注册"""
        result = coordinator.register_agent(sample_agent)
        assert result is True
        assert sample_agent.agent_id in coordinator._agents
        assert coordinator.get_agent(sample_agent.agent_id) == sample_agent

    @pytest.mark.asyncio
    async def test_register_duplicate_agent(self, coordinator, sample_agent):
        """测试重复注册Agent"""
        coordinator.register_agent(sample_agent)
        result = coordinator.register_agent(sample_agent)
        assert result is False

    @pytest.mark.asyncio
    async def test_unregister_agent(self, coordinator, sample_agent):
        """测试Agent注销"""
        coordinator.register_agent(sample_agent)
        result = coordinator.unregister_agent(sample_agent.agent_id)
        assert result is True
        assert sample_agent.agent_id not in coordinator._agents

    @pytest.mark.asyncio
    async def test_list_agents(self, coordinator):
        """测试列出Agent"""
        agent1 = AgentInfo(
            agent_id="agent_1",
            name="Agent 1",
            status=AgentStatus.IDLE,
            capabilities=["test"],
        )
        agent2 = AgentInfo(
            agent_id="agent_2",
            name="Agent 2",
            status=AgentStatus.BUSY,
            capabilities=["test"],
        )

        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

        all_agents = coordinator.list_agents()
        assert len(all_agents) == 2

        idle_agents = coordinator.list_agents(status=AgentStatus.IDLE)
        assert len(idle_agents) == 1
        assert idle_agents[0].agent_id == "agent_1"

    @pytest.mark.asyncio
    async def test_submit_task_success(self, coordinator, sample_agent, sample_task):
        """测试任务提交成功"""
        coordinator.register_agent(sample_agent)

        result = await coordinator.submit_task(sample_task)

        assert result.success is True
        assert result.assigned_agent == "agent_1"
        assert sample_task.task_id in coordinator._tasks
        assert sample_task.assigned_to == "agent_1"

    @pytest.mark.asyncio
    async def test_submit_task_no_agent(self, coordinator, sample_task):
        """测试任务提交失败（无可用Agent）"""
        result = await coordinator.submit_task(sample_task)

        assert result.success is False
        assert "No available agents" in result.reason

    @pytest.mark.asyncio
    async def test_submit_task_dependencies_not_satisfied(self, coordinator, sample_agent):
        """测试任务提交失败（依赖未满足）"""
        coordinator.register_agent(sample_agent)

        task_with_deps = TaskInfo(
            task_id="task_2",
            task_type="test_task",
            dependencies=["task_nonexistent"],
        )

        result = await coordinator.submit_task(task_with_deps)

        assert result.success is False
        assert "dependencies not satisfied" in result.reason

    @pytest.mark.asyncio
    async def test_complete_task(self, coordinator, sample_agent, sample_task):
        """测试任务完成"""
        coordinator.register_agent(sample_agent)
        await coordinator.submit_task(sample_task)

        result = await coordinator.complete_task(
            task_id=sample_task.task_id,
            agent_id=sample_agent.agent_id,
            result={"status": "success"}
        )

        assert result is True
        assert sample_task.task_id in coordinator._completed_tasks
        assert sample_task.status == "completed"
        assert sample_task.task_id not in sample_agent.current_tasks

    @pytest.mark.asyncio
    async def test_task_triggers_dependent_tasks(self, coordinator, sample_agent):
        """测试任务完成后触发依赖任务"""
        coordinator.register_agent(sample_agent)

        task1 = TaskInfo(
            task_id="task_1",
            task_type="test_task",
        )

        task2 = TaskInfo(
            task_id="task_2",
            task_type="test_task",
            dependencies=["task_1"],
        )

        await coordinator.submit_task(task1)
        await coordinator.submit_task(task2)

        # 完成task1
        await coordinator.complete_task(
            task_id="task_1",
            agent_id=sample_agent.agent_id
        )

        # task2应该被自动调度
        assert task2.assigned_to == sample_agent.agent_id

    @pytest.mark.asyncio
    async def test_get_statistics(self, coordinator, sample_agent):
        """测试获取统计信息"""
        coordinator.register_agent(sample_agent)

        task = TaskInfo(task_id="task_1", task_type="test_task")
        await coordinator.submit_task(task)

        await coordinator.complete_task(
            task_id="task_1",
            agent_id=sample_agent.agent_id
        )

        stats = coordinator.get_statistics()

        assert stats["total_agents"] == 1
        assert stats["total_tasks"] == 1
        assert stats["completed_tasks"] == 1
        assert stats["running"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
