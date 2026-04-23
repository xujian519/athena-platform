"""
Coordinator调度器和负载均衡器测试

测试任务调度和负载均衡功能。
"""


import pytest

from core.framework.collaboration.coordinator.load_balancer import LoadBalancer
from core.framework.collaboration.coordinator.scheduler import TaskScheduler
from core.framework.collaboration.coordinator.types import (
    AgentInfo,
    AgentStatus,
    TaskInfo,
    TaskPriority,
)


class TestTaskScheduler:
    """TaskScheduler功能测试"""

    @pytest.fixture
    def scheduler(self):
        """创建调度器实例"""
        return TaskScheduler()

    @pytest.mark.asyncio
    async def test_submit_task(self, scheduler):
        """测试提交任务"""
        task = TaskInfo(
            task_id="task_1",
            task_type="test",
            priority=TaskPriority.HIGH,
        )

        result = await scheduler.submit(task)
        assert result is True
        assert await scheduler.get_queue_size() == 1

    @pytest.mark.asyncio
    async def test_submit_duplicate_task(self, scheduler):
        """测试提交重复任务"""
        task = TaskInfo(task_id="task_1", task_type="test")

        await scheduler.submit(task)
        result = await scheduler.submit(task)

        assert result is False
        assert await scheduler.get_queue_size() == 1

    @pytest.mark.asyncio
    async def test_get_next_task(self, scheduler):
        """测试获取下一个任务"""
        task1 = TaskInfo(
            task_id="task_1",
            task_type="test",
            priority=TaskPriority.HIGH,
        )
        task2 = TaskInfo(
            task_id="task_2",
            task_type="test",
            priority=TaskPriority.LOW,
        )

        await scheduler.submit(task1)
        await scheduler.submit(task2)

        # 应该先返回高优先级任务
        next_task = await scheduler.get_next_task()
        assert next_task.task_id == "task_1"

        # 再获取应该返回低优先级任务
        next_task = await scheduler.get_next_task()
        assert next_task.task_id == "task_2"

    @pytest.mark.asyncio
    async def test_peek_next_task(self, scheduler):
        """测试查看下一个任务"""
        task = TaskInfo(task_id="task_1", task_type="test")
        await scheduler.submit(task)

        peeked = await scheduler.peek_next_task()
        assert peeked.task_id == "task_1"

        # 再次查看应该还在队列中
        assert await scheduler.get_queue_size() == 1

    @pytest.mark.asyncio
    async def test_remove_task(self, scheduler):
        """测试移除任务"""
        task = TaskInfo(task_id="task_1", task_type="test")
        await scheduler.submit(task)

        result = await scheduler.remove_task("task_1")
        assert result is True

        # 队列应该为空
        assert await scheduler.get_queue_size() == 0

    @pytest.mark.asyncio
    async def test_get_queue_status(self, scheduler):
        """测试获取队列状态"""
        # 提交不同优先级的任务
        for i in range(3):
            await scheduler.submit(
                TaskInfo(
                    task_id=f"task_{i}",
                    task_type="test",
                    priority=TaskPriority.HIGH if i == 0 else TaskPriority.LOW,
                )
            )

        status = await scheduler.get_queue_status()
        assert status["total_pending"] == 3
        assert status["high"] == 1
        assert status["low"] == 2

    @pytest.mark.asyncio
    async def test_priority_ordering(self, scheduler):
        """测试优先级排序"""
        # 按相反顺序提交任务
        await scheduler.submit(
            TaskInfo(task_id="low", task_type="test", priority=TaskPriority.LOW)
        )
        await scheduler.submit(
            TaskInfo(task_id="critical", task_type="test", priority=TaskPriority.CRITICAL)
        )
        await scheduler.submit(
            TaskInfo(task_id="high", task_type="test", priority=TaskPriority.HIGH)
        )

        # 应该按优先级顺序返回：critical -> high -> low
        tasks = []
        while await scheduler.has_pending_tasks():
            task = await scheduler.get_next_task()
            if task:
                tasks.append(task.task_id)

        assert tasks == ["critical", "high", "low"]

    @pytest.mark.asyncio
    async def test_fifo_for_same_priority(self, scheduler):
        """测试相同优先级任务的FIFO顺序"""
        await scheduler.submit(
            TaskInfo(task_id="task_1", task_type="test", priority=TaskPriority.MEDIUM)
        )
        await scheduler.submit(
            TaskInfo(task_id="task_2", task_type="test", priority=TaskPriority.MEDIUM)
        )
        await scheduler.submit(
            TaskInfo(task_id="task_3", task_type="test", priority=TaskPriority.MEDIUM)
        )

        tasks = []
        while await scheduler.has_pending_tasks():
            task = await scheduler.get_next_task()
            if task:
                tasks.append(task.task_id)

        assert tasks == ["task_1", "task_2", "task_3"]


class TestLoadBalancer:
    """LoadBalancer功能测试"""

    @pytest.fixture
    def load_balancer(self):
        """创建负载均衡器"""
        return LoadBalancer(strategy="least_loaded")

    @pytest.fixture
    def agents(self):
        """创建测试Agent列表"""
        return [
            AgentInfo(
                agent_id="agent_1",
                name="Agent 1",
                status=AgentStatus.IDLE,
                capabilities=["test", "analysis"],
                current_tasks=[],
            ),
            AgentInfo(
                agent_id="agent_2",
                name="Agent 2",
                status=AgentStatus.IDLE,
                capabilities=["test"],
                current_tasks=["task_1"],
            ),
            AgentInfo(
                agent_id="agent_3",
                name="Agent 3",
                status=AgentStatus.BUSY,
                capabilities=["test"],
                current_tasks=["task_2", "task_3"],
            ),
        ]

    @pytest.fixture
    def task(self):
        """创建测试任务"""
        return TaskInfo(
            task_id="task_new",
            task_type="test",
            priority=TaskPriority.HIGH,
        )

    def test_least_loaded_selection(self, load_balancer, agents, task):
        """测试最少负载选择"""
        # agent_1有0个任务，agent_2有1个任务，agent_3有2个任务
        selected = load_balancer.select_agent(task, agents)

        # 应该选择agent_1（负载最少）
        assert selected.agent_id == "agent_1"

    def test_round_robin_selection(self):
        """测试轮询选择"""
        load_balancer = LoadBalancer(strategy="round_robin")
        agents = [
            AgentInfo(agent_id=f"agent_{i}", name=f"Agent {i}")
            for i in range(3)
        ]
        task = TaskInfo(task_id="task_1", task_type="test")

        # 轮询选择
        selected_1 = load_balancer.select_agent(task, agents)
        selected_2 = load_balancer.select_agent(task, agents)
        selected_3 = load_balancer.select_agent(task, agents)

        assert selected_1.agent_id == "agent_0"
        assert selected_2.agent_id == "agent_1"
        assert selected_3.agent_id == "agent_2"

    def test_capability_based_selection(self):
        """测试基于能力的选择"""
        load_balancer = LoadBalancer(strategy="capability_based")
        agents = [
            AgentInfo(
                agent_id="agent_1",
                name="Agent 1",
                capabilities=["analysis"],
            ),
            AgentInfo(
                agent_id="agent_2",
                name="Agent 2",
                capabilities=["test", "analysis"],
            ),
        ]
        task = TaskInfo(
            task_id="task_1",
            task_type="test",
            required_capabilities=["test"],
        )

        selected = load_balancer.select_agent(task, agents)

        # 只有agent_2具备test能力
        assert selected is not None
        assert selected.agent_id == "agent_2"

    def test_capability_based_no_match(self):
        """测试基于能力选择时无匹配"""
        load_balancer = LoadBalancer(strategy="capability_based")
        agents = [
            AgentInfo(
                agent_id="agent_1",
                name="Agent 1",
                capabilities=["analysis"],
            ),
        ]
        task = TaskInfo(
            task_id="task_1",
            task_type="test",
            required_capabilities=["test"],
        )

        selected = load_balancer.select_agent(task, agents)

        # 没有Agent具备所需能力
        assert selected is None

    @pytest.mark.asyncio
    async def test_update_agent_performance(self, load_balancer):
        """测试更新Agent性能"""
        await load_balancer.update_agent_performance(
            agent_id="agent_1",
            task_id="task_1",
            execution_time=1.5,
            success=True,
        )

        stats = load_balancer.get_agent_stats("agent_1")
        assert stats is not None
        assert stats["total_tasks"] == 1
        assert stats["successful_tasks"] == 1
        assert stats["average_execution_time"] == 1.5

    @pytest.mark.asyncio
    async def test_performance_tracking(self, load_balancer):
        """测试性能跟踪"""
        # 记录多次执行
        await load_balancer.update_agent_performance(
            "agent_1", "task_1", 1.0, True
        )
        await load_balancer.update_agent_performance(
            "agent_1", "task_2", 2.0, True
        )
        await load_balancer.update_agent_performance(
            "agent_1", "task_3", 0.5, False
        )

        stats = load_balancer.get_agent_stats("agent_1")
        assert stats["total_tasks"] == 3
        assert stats["successful_tasks"] == 2
        assert stats["failed_tasks"] == 1
        assert stats["average_execution_time"] == (1.0 + 2.0 + 0.5) / 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
