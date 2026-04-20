#!/usr/bin/env python3
"""Coordinator模式集成测试

测试Coordinator与P0/P1系统的集成:
- 与Skills系统集成
- 与任务管理器集成
- 端到端工作流测试
"""

from __future__ import annotations

import pytest

from core.coordinator import (
    Coordinator,
    CoordinatorConfig,
    AgentInfo,
    AdvancedCoordinator,
    TaskDependency,
    RoundRobinStrategy,
)
from core.tasks.manager import TaskManager, TaskPriority
from core.skills.manager import SkillManager
from core.skills.base import Skill, SkillMetadata, SkillResult


class MockAgent:
    """模拟Agent类"""

    def __init__(self, agent_id: str, capabilities: list[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.completed_tasks: list[str] = []

    def execute_task(self, task_id: str, payload: dict) -> dict:
        """模拟执行任务"""
        self.completed_tasks.append(task_id)
        return {"status": "success", "agent_id": self.agent_id}


class TestSkillsIntegration:
    """测试与Skills系统的集成"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    def test_register_skill_as_capability(self, coordinator: Coordinator) -> None:
        """测试将技能注册为Agent能力"""
        # 创建具有技能的Agent
        agent = AgentInfo(
            agent_id="skill-agent",
            name="技能Agent",
            capabilities=["patent_search", "patent_analyze"],
        )

        coordinator.register_agent(agent)

        # 验证Agent可以处理技能任务
        assert coordinator.get_agents_by_capability("patent_search")
        assert coordinator.get_agents_by_capability("patent_analyze")


class TestTaskManagerIntegration:
    """测试与任务管理器的集成"""

    @pytest.fixture
    def task_manager(self) -> TaskManager:
        """创建任务管理器实例"""
        return TaskManager()

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    def test_submit_task_from_manager(
        self, task_manager: TaskManager, coordinator: Coordinator
    ) -> None:
        """测试从任务管理器提交任务到Coordinator"""
        # 注册Agent
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["test_task"],
        )
        coordinator.register_agent(agent)

        # 从任务管理器创建任务
        task = task_manager.create_task(
            title="测试任务",
            description="这是一个测试任务",
            priority=TaskPriority.HIGH,
            assigned_to="agent-001",
        )

        # 将任务提交到Coordinator
        assignment = coordinator.submit_task(
            task_id=task.id,
            task_type="test_task",
            payload={"description": task.description},
            priority=task.priority.value,
        )

        assert assignment is not None
        assert assignment.task_id == task.id


class TestEndToEndWorkflow:
    """测试端到端工作流"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        config = CoordinatorConfig(
            max_concurrent_tasks=10,
            enable_load_balancing=True,
            enable_conflict_detection=True,
            enable_state_sync=True,
        )
        return Coordinator(config=config)

    @pytest.fixture
    def advanced_coordinator(self, coordinator: Coordinator) -> AdvancedCoordinator:
        """创建高级Coordinator实例"""
        return AdvancedCoordinator(coordinator)

    def test_complete_workflow(
        self, coordinator: Coordinator, advanced_coordinator: AdvancedCoordinator
    ) -> None:
        """测试完整工作流"""
        # 1. 注册多个Agent
        agents = [
            AgentInfo(
                agent_id="agent-001",
                name="检索Agent",
                capabilities=["search"],
                max_concurrent_tasks=3,
            ),
            AgentInfo(
                agent_id="agent-002",
                name="分析Agent",
                capabilities=["analyze"],
                max_concurrent_tasks=2,
            ),
            AgentInfo(
                agent_id="agent-003",
                name="写作Agent",
                capabilities=["write"],
                max_concurrent_tasks=2,
            ),
        ]

        for agent in agents:
            coordinator.register_agent(agent)

        # 2. 创建任务链
        tasks = [
            {"task_id": "task-search", "task_type": "search"},
            {"task_id": "task-analyze", "task_type": "analyze"},
            {"task_id": "task-write", "task_type": "write"},
        ]

        task_ids = advanced_coordinator.create_task_chain(tasks)

        # 3. 提交第一个任务
        assignment = coordinator.submit_task(
            task_id=task_ids[0],
            task_type="search",
            payload={"query": "测试查询"},
        )

        assert assignment is not None
        assert assignment.agent_id == "agent-001"

        # 4. 完成第一个任务
        coordinator.complete_task(
            task_id=task_ids[0],
            agent_id="agent-001",
            result={"count": 10},
        )

        # 5. 标记任务完成（触发依赖检查）
        advanced_coordinator.mark_task_completed(task_ids[0])

        # 6. 验证第二个任务现在可以执行
        assert advanced_coordinator.check_dependencies(task_ids[1]) is True

    def test_multi_agent_parallel_workflow(
        self, coordinator: Coordinator
    ) -> None:
        """测试多Agent并行工作流"""
        # 注册多个相同能力的Agent
        for i in range(3):
            agent = AgentInfo(
                agent_id=f"agent-{i:03d}",
                name=f"Agent {i}",
                capabilities=["parallel_task"],
                max_concurrent_tasks=2,
            )
            coordinator.register_agent(agent)

        # 并行提交多个任务
        task_ids = []
        for i in range(6):
            assignment = coordinator.submit_task(
                task_id=f"parallel-task-{i}",
                task_type="parallel_task",
                payload={"index": i},
            )
            if assignment:
                task_ids.append(assignment.task_id)

        # 验证负载均衡
        agent_000 = coordinator.get_agent("agent-000")
        agent_001 = coordinator.get_agent("agent-001")
        agent_002 = coordinator.get_agent("agent-002")

        # 每个Agent应该有相近数量的任务
        current_tasks = [
            agent_000.current_tasks if agent_000 else 0,
            agent_001.current_tasks if agent_001 else 0,
            agent_002.current_tasks if agent_002 else 0,
        ]

        # 负载应该相对均衡（差异不超过1）
        assert max(current_tasks) - min(current_tasks) <= 1

    def test_conflict_detection_and_resolution(
        self, coordinator: Coordinator
    ) -> None:
        """测试冲突检测和解决"""
        from core.coordinator import ConflictType, ConflictResolutionStrategy

        # 注册Agent
        agent1 = AgentInfo(
            agent_id="agent-001",
            name="Agent 1",
            capabilities=["task"],
            priority=10,
        )
        agent2 = AgentInfo(
            agent_id="agent-002",
            name="Agent 2",
            capabilities=["task"],
            priority=5,
        )

        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

        # 检测冲突
        conflict = coordinator.detect_conflict(
            conflict_type=ConflictType.RESOURCE,
            agents=["agent-001", "agent-002"],
            resource_id="resource-001",
            description="资源冲突",
        )

        assert conflict is not None
        assert conflict.conflict_type == ConflictType.RESOURCE

        # 解决冲突
        result = coordinator.resolve_conflict(
            conflict.conflict_id,
            ConflictResolutionStrategy.PRIORITY,
        )

        assert result is True
        assert conflict.status == "resolved"


class TestCoordinatorPersistence:
    """测试Coordinator持久化"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    def test_state_export(self, coordinator: Coordinator) -> None:
        """测试状态导出"""
        # 注册Agent
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["test"],
        )
        coordinator.register_agent(agent)

        # 提交任务
        coordinator.submit_task("task-001", "test", {})

        # 导出状态
        state = coordinator.get_state()

        assert state["total_agents"] == 1
        assert state["total_tasks"] == 1

    def test_metrics_tracking(self, coordinator: Coordinator) -> None:
        """测试指标跟踪"""
        # 注册Agent
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["test"],
        )
        coordinator.register_agent(agent)

        # 执行多个任务
        for i in range(5):
            task_id = f"task-{i:03d}"
            coordinator.submit_task(task_id, "test", {})
            coordinator.complete_task(task_id, "agent-001", {"status": "ok"})

        # 检查指标
        metrics = coordinator.get_metrics()

        assert metrics["total_tasks_submitted"] == 5
        assert metrics["total_tasks_completed"] == 5


class TestCustomSchedulingStrategy:
    """测试自定义调度策略"""

    def test_custom_strategy_registration(self) -> None:
        """测试自定义策略注册"""
        from core.coordinator.scheduler import SchedulingStrategy

        class CustomStrategy(SchedulingStrategy):
            """自定义调度策略"""

            def select_agent(self, agents, task):
                # 选择ID字母序最靠前的Agent
                if not agents:
                    return None
                return min(agents, key=lambda a: a.agent_id)

            def get_name(self):
                return "custom"

        # 注册策略
        from core.coordinator import StrategyFactory

        StrategyFactory.register_strategy("custom", CustomStrategy)

        # 创建策略
        strategy = StrategyFactory.create_strategy("custom")

        assert isinstance(strategy, CustomStrategy)
        assert strategy.get_name() == "custom"
