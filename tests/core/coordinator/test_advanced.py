#!/usr/bin/env python3
"""Coordinator高级功能测试

测试:
- 任务依赖管理
- 任务超时处理
- 失败重试机制
- 任务链执行
- 调度策略
"""

from __future__ import annotations

import time
import pytest

from core.coordinator import (
    AdvancedCoordinator,
    Coordinator,
    CoordinatorConfig,
    AgentInfo,
    TaskDependency,
    TaskRetryConfig,
    RoundRobinStrategy,
    LeastLoadedStrategy,
    PriorityStrategy,
    WeightedStrategy,
    StrategyFactory,
    TaskAssignment,
)


class TestTaskDependency:
    """测试任务依赖管理"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    @pytest.fixture
    def advanced_coordinator(self, coordinator: Coordinator) -> AdvancedCoordinator:
        """创建高级Coordinator实例"""
        return AdvancedCoordinator(coordinator)

    def test_add_dependency(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试添加依赖"""
        dependency = TaskDependency(
            task_id="task-002",
            depends_on=["task-001"],
            wait_mode="all",
        )

        result = advanced_coordinator.add_dependency(dependency)
        assert result is True

    def test_check_dependencies_not_satisfied(
        self, advanced_coordinator: AdvancedCoordinator
    ) -> None:
        """测试依赖未满足"""
        dependency = TaskDependency(
            task_id="task-002",
            depends_on=["task-001"],
        )

        advanced_coordinator.add_dependency(dependency)

        result = advanced_coordinator.check_dependencies("task-002")
        assert result is False

    def test_check_dependencies_satisfied(
        self, advanced_coordinator: AdvancedCoordinator
    ) -> None:
        """测试依赖已满足"""
        dependency = TaskDependency(
            task_id="task-002",
            depends_on=["task-001"],
        )

        advanced_coordinator.add_dependency(dependency)
        advanced_coordinator.mark_task_completed("task-001")

        result = advanced_coordinator.check_dependencies("task-002")
        assert result is True

    def test_wait_mode_any(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试any等待模式"""
        dependency = TaskDependency(
            task_id="task-003",
            depends_on=["task-001", "task-002"],
            wait_mode="any",
        )

        advanced_coordinator.add_dependency(dependency)

        # 只完成一个依赖
        advanced_coordinator.mark_task_completed("task-001")

        result = advanced_coordinator.check_dependencies("task-003")
        assert result is True

    def test_get_pending_dependencies(
        self, advanced_coordinator: AdvancedCoordinator
    ) -> None:
        """测试获取待处理依赖"""
        dep1 = TaskDependency(task_id="task-002", depends_on=["task-001"])
        dep2 = TaskDependency(task_id="task-003", depends_on=["task-002"])

        advanced_coordinator.add_dependency(dep1)
        advanced_coordinator.add_dependency(dep2)

        pending = advanced_coordinator.get_pending_dependencies()
        assert len(pending) == 2


class TestRetryMechanism:
    """测试重试机制"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    @pytest.fixture
    def advanced_coordinator(self, coordinator: Coordinator) -> AdvancedCoordinator:
        """创建高级Coordinator实例"""
        return AdvancedCoordinator(coordinator)

    def test_set_retry_config(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试设置重试配置"""
        config = TaskRetryConfig(
            max_retries=5,
            retry_delay=2.0,
            backoff_factor=1.5,
        )

        advanced_coordinator.set_retry_config("task-001", config)

        # 验证配置已设置
        assert "task-001" in advanced_coordinator._retry_configs

    def test_schedule_retry(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试安排重试"""
        config = TaskRetryConfig(max_retries=3)
        advanced_coordinator.set_retry_config("task-001", config)

        assignment = TaskAssignment(
            task_id="task-001",
            agent_id="agent-001",
            task_type="test",
        )

        result = advanced_coordinator.schedule_retry(assignment)
        assert result is True

        # 验证重试次数
        assert assignment.metadata.get("retry_count") == 1

    def test_max_retries_exceeded(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试超过最大重试次数"""
        config = TaskRetryConfig(max_retries=2)
        advanced_coordinator.set_retry_config("task-001", config)

        assignment = TaskAssignment(
            task_id="task-001",
            agent_id="agent-001",
            task_type="test",
        )
        assignment.metadata["retry_count"] = 2  # 已达到最大重试次数

        result = advanced_coordinator.schedule_retry(assignment)
        assert result is False

    def test_get_ready_retries(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试获取可重试任务"""
        config = TaskRetryConfig(max_retries=3, retry_delay=0.1)
        advanced_coordinator.set_retry_config("task-001", config)

        assignment = TaskAssignment(
            task_id="task-001",
            agent_id="agent-001",
            task_type="test",
        )

        advanced_coordinator.schedule_retry(assignment)

        # 等待延迟时间
        time.sleep(0.2)

        ready = advanced_coordinator.get_ready_retries()
        assert len(ready) == 1
        assert ready[0].task_id == "task-001"


class TestTimeoutHandling:
    """测试超时处理"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    @pytest.fixture
    def advanced_coordinator(self, coordinator: Coordinator) -> AdvancedCoordinator:
        """创建高级Coordinator实例"""
        return AdvancedCoordinator(coordinator)

    def test_set_timeout(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试设置超时"""
        advanced_coordinator.set_timeout("task-001", 60)

        assert "task-001" in advanced_coordinator._timeout_tasks

    def test_check_timeouts(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试检查超时"""
        # 设置一个很短的超时
        advanced_coordinator.set_timeout("task-001", 0)

        # 等待超时
        time.sleep(0.1)

        timeout_tasks = advanced_coordinator.check_timeouts()
        assert "task-001" in timeout_tasks

    def test_get_timeout_task_count(
        self, advanced_coordinator: AdvancedCoordinator
    ) -> None:
        """测试获取超时任务数量"""
        advanced_coordinator.set_timeout("task-001", 60)
        advanced_coordinator.set_timeout("task-002", 60)

        count = advanced_coordinator.get_timeout_task_count()
        assert count == 2


class TestTaskChain:
    """测试任务链"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    @pytest.fixture
    def advanced_coordinator(self, coordinator: Coordinator) -> AdvancedCoordinator:
        """创建高级Coordinator实例"""
        return AdvancedCoordinator(coordinator)

    def test_create_task_chain(self, advanced_coordinator: AdvancedCoordinator) -> None:
        """测试创建任务链"""
        tasks = [
            {"task_id": "task-001", "task_type": "type_a"},
            {"task_id": "task-002", "task_type": "type_b"},
            {"task_id": "task-003", "task_type": "type_c"},
        ]

        task_ids = advanced_coordinator.create_task_chain(tasks)

        assert task_ids == ["task-001", "task-002", "task-003"]

        # 验证依赖关系
        assert len(advanced_coordinator.get_pending_dependencies()) == 2

    def test_task_chain_execution(
        self, advanced_coordinator: AdvancedCoordinator
    ) -> None:
        """测试任务链执行"""
        tasks = [
            {"task_id": "task-001", "task_type": "type_a"},
            {"task_id": "task-002", "task_type": "type_b"},
        ]

        advanced_coordinator.create_task_chain(tasks)

        # 第一个任务应该可以执行
        assert advanced_coordinator.check_dependencies("task-001") is True

        # 第二个任务需要等待第一个完成
        assert advanced_coordinator.check_dependencies("task-002") is False

        # 完成第一个任务
        advanced_coordinator.mark_task_completed("task-001")

        # 现在第二个任务可以执行了
        assert advanced_coordinator.check_dependencies("task-002") is True


class TestSchedulingStrategies:
    """测试调度策略"""

    def test_round_robin_strategy(self) -> None:
        """测试轮询策略"""
        strategy = RoundRobinStrategy()

        agents = [
            AgentInfo(agent_id="agent-001", name="Agent 1", capabilities=["test"]),
            AgentInfo(agent_id="agent-002", name="Agent 2", capabilities=["test"]),
            AgentInfo(agent_id="agent-003", name="Agent 3", capabilities=["test"]),
        ]

        task = TaskAssignment(
            task_id="task-001",
            agent_id="",
            task_type="test",
        )

        selected = []
        for _ in range(5):
            agent = strategy.select_agent(agents, task)
            if agent:
                selected.append(agent.agent_id)

        # 验证轮询顺序
        assert selected[0] == "agent-001"
        assert selected[1] == "agent-002"
        assert selected[2] == "agent-003"
        assert selected[3] == "agent-001"

    def test_least_loaded_strategy(self) -> None:
        """测试最少负载策略"""
        strategy = LeastLoadedStrategy()

        agents = [
            AgentInfo(
                agent_id="agent-001",
                name="Agent 1",
                capabilities=["test"],
                current_tasks=3,
            ),
            AgentInfo(
                agent_id="agent-002",
                name="Agent 2",
                capabilities=["test"],
                current_tasks=1,
            ),
            AgentInfo(
                agent_id="agent-003",
                name="Agent 3",
                capabilities=["test"],
                current_tasks=2,
            ),
        ]

        task = TaskAssignment(
            task_id="task-001",
            agent_id="",
            task_type="test",
        )

        agent = strategy.select_agent(agents, task)
        assert agent is not None
        assert agent.agent_id == "agent-002"  # 负载最少的

    def test_priority_strategy(self) -> None:
        """测试优先级策略"""
        strategy = PriorityStrategy()

        agents = [
            AgentInfo(
                agent_id="agent-001",
                name="Agent 1",
                capabilities=["test"],
                priority=5,
            ),
            AgentInfo(
                agent_id="agent-002",
                name="Agent 2",
                capabilities=["test"],
                priority=10,
            ),
            AgentInfo(
                agent_id="agent-003",
                name="Agent 3",
                capabilities=["test"],
                priority=7,
            ),
        ]

        task = TaskAssignment(
            task_id="task-001",
            agent_id="",
            task_type="test",
        )

        agent = strategy.select_agent(agents, task)
        assert agent is not None
        assert agent.agent_id == "agent-002"  # 优先级最高的

    def test_weighted_strategy(self) -> None:
        """测试加权策略"""
        strategy = WeightedStrategy(weight_key="weight")

        agents = [
            AgentInfo(
                agent_id="agent-001",
                name="Agent 1",
                capabilities=["test"],
                metadata={"weight": 1.0},
            ),
            AgentInfo(
                agent_id="agent-002",
                name="Agent 2",
                capabilities=["test"],
                metadata={"weight": 3.0},
            ),
            AgentInfo(
                agent_id="agent-003",
                name="Agent 3",
                capabilities=["test"],
                metadata={"weight": 2.0},
            ),
        ]

        task = TaskAssignment(
            task_id="task-001",
            agent_id="",
            task_type="test",
        )

        agent = strategy.select_agent(agents, task)
        assert agent is not None
        assert agent.agent_id == "agent-002"  # 权重最高的


class TestStrategyFactory:
    """测试策略工厂"""

    def test_create_strategy(self) -> None:
        """测试创建策略"""
        strategy = StrategyFactory.create_strategy("round_robin")
        assert isinstance(strategy, RoundRobinStrategy)

        strategy = StrategyFactory.create_strategy("least_loaded")
        assert isinstance(strategy, LeastLoadedStrategy)

        strategy = StrategyFactory.create_strategy("priority")
        assert isinstance(strategy, PriorityStrategy)

    def test_create_strategy_with_params(self) -> None:
        """测试创建带参数的策略"""
        strategy = StrategyFactory.create_strategy(
            "weighted", weight_key="custom_weight"
        )
        assert isinstance(strategy, WeightedStrategy)

    def test_unknown_strategy(self) -> None:
        """测试未知策略"""
        with pytest.raises(ValueError):
            StrategyFactory.create_strategy("unknown")

    def test_register_custom_strategy(self) -> None:
        """测试注册自定义策略"""
        from core.coordinator.scheduler import SchedulingStrategy

        class CustomStrategy(SchedulingStrategy):
            def select_agent(self, agents, task):
                return agents[0] if agents else None

            def get_name(self):
                return "custom"

        StrategyFactory.register_strategy("custom", CustomStrategy)

        strategy = StrategyFactory.create_strategy("custom")
        assert isinstance(strategy, CustomStrategy)

    def test_get_available_strategies(self) -> None:
        """测试获取可用策略"""
        strategies = StrategyFactory.get_available_strategies()

        assert "round_robin" in strategies
        assert "least_loaded" in strategies
        assert "priority" in strategies
        assert "weighted" in strategies
