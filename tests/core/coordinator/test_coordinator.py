#!/usr/bin/env python3
"""Coordinator模式测试

测试Coordinator模式的核心功能:
- Agent注册和注销
- 任务分配和负载均衡
- 优先级调度
- Agent间通信协调
- 冲突解决机制
- 状态同步管理
"""

import pytest
from core.coordinator.base import (
    AgentInfo,
    AgentStatus,
    ConflictInfo,
    ConflictResolutionStrategy,
    ConflictType,
    Coordinator,
    CoordinatorConfig,
    Message,
    MessagePriority,
    TaskAssignment,
)


class TestCoordinatorConfig:
    """测试Coordinator配置"""

    def test_default_config(self) -> None:
        """测试默认配置"""
        config = CoordinatorConfig()

        assert config.max_concurrent_tasks == 10
        assert config.task_timeout == 300
        assert config.heartbeat_interval == 30
        assert config.enable_load_balancing is True
        assert config.enable_conflict_detection is True
        assert config.enable_state_sync is True

    def test_custom_config(self) -> None:
        """测试自定义配置"""
        config = CoordinatorConfig(
            max_concurrent_tasks=20,
            task_timeout=600,
            heartbeat_interval=60,
            enable_load_balancing=False,
            enable_conflict_detection=False,
            enable_state_sync=False,
        )

        assert config.max_concurrent_tasks == 20
        assert config.task_timeout == 600
        assert config.heartbeat_interval == 60
        assert config.enable_load_balancing is False
        assert config.enable_conflict_detection is False
        assert config.enable_state_sync is False


class TestAgentInfo:
    """测试Agent信息"""

    def test_agent_info_creation(self) -> None:
        """测试Agent信息创建"""
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["task_a", "task_b"],
            max_concurrent_tasks=5,
            status=AgentStatus.IDLE,
        )

        assert agent.agent_id == "agent-001"
        assert agent.name == "测试Agent"
        assert agent.capabilities == ["task_a", "task_b"]
        assert agent.max_concurrent_tasks == 5
        assert agent.status == AgentStatus.IDLE
        assert agent.current_tasks == 0
        assert agent.completed_tasks == 0

    def test_agent_status_transitions(self) -> None:
        """测试Agent状态转换"""
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["task_a"],
        )

        # IDLE -> BUSY
        agent.status = AgentStatus.BUSY
        assert agent.status == AgentStatus.BUSY

        # BUSY -> IDLE
        agent.status = AgentStatus.IDLE
        assert agent.status == AgentStatus.IDLE

        # IDLE -> OFFLINE
        agent.status = AgentStatus.OFFLINE
        assert agent.status == AgentStatus.OFFLINE

    def test_agent_can_handle_task(self) -> None:
        """测试Agent是否能处理任务"""
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["task_a", "task_b"],
            max_concurrent_tasks=2,
        )

        # 可以处理
        assert agent.can_handle_task("task_a") is True
        assert agent.can_handle_task("task_b") is True

        # 不能处理
        assert agent.can_handle_task("task_c") is False

        # 达到并发上限
        agent.current_tasks = 2
        assert agent.can_handle_task("task_a") is False


class TestMessage:
    """测试消息系统"""

    def test_message_creation(self) -> None:
        """测试消息创建"""
        msg = Message(
            message_id="msg-001",
            sender="agent-001",
            receiver="agent-002",
            content="测试消息",
            priority=MessagePriority.NORMAL,
        )

        assert msg.message_id == "msg-001"
        assert msg.sender == "agent-001"
        assert msg.receiver == "agent-002"
        assert msg.content == "测试消息"
        assert msg.priority == MessagePriority.NORMAL
        assert msg.timestamp is not None

    def test_message_priority_ordering(self) -> None:
        """测试消息优先级排序"""
        high = MessagePriority.HIGH
        normal = MessagePriority.NORMAL
        low = MessagePriority.LOW

        assert high.value > normal.value
        assert normal.value > low.value


class TestTaskAssignment:
    """测试任务分配"""

    def test_task_assignment_creation(self) -> None:
        """测试任务分配创建"""
        assignment = TaskAssignment(
            task_id="task-001",
            agent_id="agent-001",
            task_type="task_a",
            priority=1,
            payload={"data": "test"},
        )

        assert assignment.task_id == "task-001"
        assert assignment.agent_id == "agent-001"
        assert assignment.task_type == "task_a"
        assert assignment.priority == 1
        assert assignment.payload == {"data": "test"}
        assert assignment.status == "pending"
        assert assignment.created_at is not None


class TestConflictInfo:
    """测试冲突信息"""

    def test_conflict_info_creation(self) -> None:
        """测试冲突信息创建"""
        conflict = ConflictInfo(
            conflict_id="conflict-001",
            conflict_type=ConflictType.RESOURCE,
            agents=["agent-001", "agent-002"],
            resource_id="resource-001",
            description="资源冲突",
        )

        assert conflict.conflict_id == "conflict-001"
        assert conflict.conflict_type == ConflictType.RESOURCE
        assert conflict.agents == ["agent-001", "agent-002"]
        assert conflict.resource_id == "resource-001"
        assert conflict.description == "资源冲突"
        assert conflict.status == "detected"
        assert conflict.resolution_strategy is None

    def test_conflict_resolution_strategies(self) -> None:
        """测试冲突解决策略"""
        # 资源冲突使用优先级策略
        conflict = ConflictInfo(
            conflict_id="conflict-001",
            conflict_type=ConflictType.RESOURCE,
            agents=["agent-001", "agent-002"],
            resource_id="resource-001",
        )

        conflict.resolution_strategy = ConflictResolutionStrategy.PRIORITY
        assert conflict.resolution_strategy == ConflictResolutionStrategy.PRIORITY

        # 数据冲突使用协商策略
        data_conflict = ConflictInfo(
            conflict_id="conflict-002",
            conflict_type=ConflictType.DATA,
            agents=["agent-001", "agent-002"],
        )

        data_conflict.resolution_strategy = ConflictResolutionStrategy.NEGOTIATE
        assert data_conflict.resolution_strategy == ConflictResolutionStrategy.NEGOTIATE


class TestCoordinatorAgentManagement:
    """测试Coordinator Agent管理"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        config = CoordinatorConfig(
            max_concurrent_tasks=5,
            task_timeout=60,
        )
        return Coordinator(config=config)

    def test_register_agent(self, coordinator: Coordinator) -> None:
        """测试注册Agent"""
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["task_a", "task_b"],
        )

        result = coordinator.register_agent(agent)
        assert result is True

        # 验证Agent已注册
        registered = coordinator.get_agent("agent-001")
        assert registered is not None
        assert registered.agent_id == "agent-001"

    def test_register_duplicate_agent(self, coordinator: Coordinator) -> None:
        """测试注册重复Agent"""
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["task_a"],
        )

        coordinator.register_agent(agent)

        # 尝试再次注册
        result = coordinator.register_agent(agent)
        assert result is False

    def test_unregister_agent(self, coordinator: Coordinator) -> None:
        """测试注销Agent"""
        agent = AgentInfo(
            agent_id="agent-001",
            name="测试Agent",
            capabilities=["task_a"],
        )

        coordinator.register_agent(agent)
        result = coordinator.unregister_agent("agent-001")
        assert result is True

        # 验证Agent已注销
        registered = coordinator.get_agent("agent-001")
        assert registered is None

    def test_unregister_nonexistent_agent(self, coordinator: Coordinator) -> None:
        """测试注销不存在的Agent"""
        result = coordinator.unregister_agent("nonexistent")
        assert result is False

    def test_list_agents(self, coordinator: Coordinator) -> None:
        """测试列出所有Agent"""
        agent1 = AgentInfo(
            agent_id="agent-001",
            name="Agent 1",
            capabilities=["task_a"],
        )
        agent2 = AgentInfo(
            agent_id="agent-002",
            name="Agent 2",
            capabilities=["task_b"],
        )

        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

        agents = coordinator.list_agents()
        assert len(agents) == 2

    def test_get_agents_by_capability(self, coordinator: Coordinator) -> None:
        """测试按能力获取Agent"""
        agent1 = AgentInfo(
            agent_id="agent-001",
            name="Agent 1",
            capabilities=["task_a", "task_b"],
        )
        agent2 = AgentInfo(
            agent_id="agent-002",
            name="Agent 2",
            capabilities=["task_a"],
        )
        agent3 = AgentInfo(
            agent_id="agent-003",
            name="Agent 3",
            capabilities=["task_c"],
        )

        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)
        coordinator.register_agent(agent3)

        # 获取能处理task_a的Agent
        agents = coordinator.get_agents_by_capability("task_a")
        assert len(agents) == 2
        agent_ids = {a.agent_id for a in agents}
        assert agent_ids == {"agent-001", "agent-002"}


class TestCoordinatorTaskManagement:
    """测试Coordinator任务管理"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        config = CoordinatorConfig(
            max_concurrent_tasks=5,
            task_timeout=60,
        )
        return Coordinator(config=config)

    @pytest.fixture
    def registered_agents(self, coordinator: Coordinator) -> None:
        """注册测试Agent"""
        agent1 = AgentInfo(
            agent_id="agent-001",
            name="Agent 1",
            capabilities=["task_a", "task_b"],
            max_concurrent_tasks=2,
        )
        agent2 = AgentInfo(
            agent_id="agent-002",
            name="Agent 2",
            capabilities=["task_a", "task_c"],
            max_concurrent_tasks=2,
        )

        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

    def test_submit_task(self, coordinator: Coordinator, registered_agents: None) -> None:
        """测试提交任务"""
        assignment = coordinator.submit_task(
            task_id="task-001",
            task_type="task_a",
            payload={"data": "test"},
            priority=1,
        )

        assert assignment is not None
        assert assignment.task_id == "task-001"
        assert assignment.task_type == "task_a"
        assert assignment.status == "pending"

    def test_submit_task_without_capable_agent(
        self, coordinator: Coordinator, registered_agents: None
    ) -> None:
        """测试提交无Agent能处理的任务"""
        assignment = coordinator.submit_task(
            task_id="task-001",
            task_type="task_x",  # 没有Agent支持
            payload={"data": "test"},
        )

        assert assignment is None

    def test_get_task_assignment(
        self, coordinator: Coordinator, registered_agents: None
    ) -> None:
        """测试获取任务分配"""
        coordinator.submit_task(
            task_id="task-001",
            task_type="task_a",
            payload={"data": "test"},
        )

        assignment = coordinator.get_task_assignment("task-001")
        assert assignment is not None
        assert assignment.task_id == "task-001"

    def test_complete_task(
        self, coordinator: Coordinator, registered_agents: None
    ) -> None:
        """测试完成任务"""
        coordinator.submit_task(
            task_id="task-001",
            task_type="task_a",
            payload={"data": "test"},
        )

        result = coordinator.complete_task(
            task_id="task-001",
            agent_id="agent-001",
            result={"status": "success"},
        )

        assert result is True

        # 验证Agent状态更新
        agent = coordinator.get_agent("agent-001")
        assert agent is not None
        assert agent.current_tasks == 0
        assert agent.completed_tasks == 1

    def test_fail_task(
        self, coordinator: Coordinator, registered_agents: None
    ) -> None:
        """测试任务失败"""
        coordinator.submit_task(
            task_id="task-001",
            task_type="task_a",
            payload={"data": "test"},
        )

        result = coordinator.fail_task(
            task_id="task-001",
            agent_id="agent-001",
            error="处理失败",
        )

        assert result is True

        # 验证任务状态
        assignment = coordinator.get_task_assignment("task-001")
        assert assignment is not None
        assert assignment.status == "failed"


class TestCoordinatorLoadBalancing:
    """测试Coordinator负载均衡"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例（启用负载均衡）"""
        config = CoordinatorConfig(
            max_concurrent_tasks=10,
            enable_load_balancing=True,
        )
        return Coordinator(config=config)

    @pytest.fixture
    def registered_agents(self, coordinator: Coordinator) -> None:
        """注册测试Agent"""
        agent1 = AgentInfo(
            agent_id="agent-001",
            name="Agent 1",
            capabilities=["task_a"],
            max_concurrent_tasks=5,
        )
        agent2 = AgentInfo(
            agent_id="agent-002",
            name="Agent 2",
            capabilities=["task_a"],
            max_concurrent_tasks=5,
        )

        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

    def test_round_robin_assignment(
        self, coordinator: Coordinator, registered_agents: None
    ) -> None:
        """测试轮询分配"""
        # 提交多个任务
        for i in range(4):
            coordinator.submit_task(
                task_id=f"task-{i:03d}",
                task_type="task_a",
                payload={"data": f"test-{i}"},
            )

        # 验证负载均衡
        agent1 = coordinator.get_agent("agent-001")
        agent2 = coordinator.get_agent("agent-002")

        # 两个Agent应该分配到相近数量的任务
        assert abs(agent1.current_tasks - agent2.current_tasks) <= 1

    def test_least_loaded_assignment(
        self, coordinator: Coordinator, registered_agents: None
    ) -> None:
        """测试最少负载分配"""
        # 先给agent-001分配一些任务
        agent1 = coordinator.get_agent("agent-001")
        if agent1:
            agent1.current_tasks = 3

        # 提交新任务应该分配给agent-002
        assignment = coordinator.submit_task(
            task_id="task-001",
            task_type="task_a",
            payload={"data": "test"},
        )

        assert assignment is not None
        assert assignment.agent_id == "agent-002"


class TestCoordinatorPriorityScheduling:
    """测试Coordinator优先级调度"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    @pytest.fixture
    def registered_agents(self, coordinator: Coordinator) -> None:
        """注册测试Agent"""
        agent = AgentInfo(
            agent_id="agent-001",
            name="Agent 1",
            capabilities=["task_a"],
            max_concurrent_tasks=5,
        )
        coordinator.register_agent(agent)

    def test_priority_ordering(
        self, coordinator: Coordinator, registered_agents: None
    ) -> None:
        """测试优先级排序"""
        # 提交不同优先级的任务
        coordinator.submit_task("task-001", "task_a", {}, priority=1)
        coordinator.submit_task("task-002", "task_a", {}, priority=3)
        coordinator.submit_task("task-003", "task_a", {}, priority=2)

        # 获取待处理任务
        pending = coordinator.get_pending_tasks()
        task_ids = [t.task_id for t in pending]

        # 高优先级任务应该在前
        assert task_ids[0] == "task-002"  # priority=3
        assert task_ids[1] == "task-003"  # priority=2
        assert task_ids[2] == "task-001"  # priority=1


class TestCoordinatorCommunication:
    """测试Coordinator通信协调"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    def test_send_message(self, coordinator: Coordinator) -> None:
        """测试发送消息"""
        # 注册Agent
        agent1 = AgentInfo(agent_id="agent-001", name="Agent 1", capabilities=[])
        agent2 = AgentInfo(agent_id="agent-002", name="Agent 2", capabilities=[])
        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

        # 发送消息
        result = coordinator.send_message(
            sender="agent-001",
            receiver="agent-002",
            content="测试消息",
            priority=MessagePriority.NORMAL,
        )

        assert result is True

    def test_broadcast_message(self, coordinator: Coordinator) -> None:
        """测试广播消息"""
        # 注册多个Agent（agent-000作为sender，agent-001/002/003作为接收者）
        for i in range(4):
            agent = AgentInfo(
                agent_id=f"agent-{i:03d}",
                name=f"Agent {i}",
                capabilities=[],
            )
            coordinator.register_agent(agent)

        # 广播消息
        count = coordinator.broadcast_message(
            sender="agent-000",
            content="广播消息",
            priority=MessagePriority.HIGH,
        )

        assert count == 3

    def test_get_pending_messages(self, coordinator: Coordinator) -> None:
        """测试获取待处理消息"""
        # 注册Agent
        agent1 = AgentInfo(agent_id="agent-001", name="Agent 1", capabilities=[])
        agent2 = AgentInfo(agent_id="agent-002", name="Agent 2", capabilities=[])
        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

        # 发送消息
        coordinator.send_message(
            sender="agent-001",
            receiver="agent-002",
            content="消息1",
        )
        coordinator.send_message(
            sender="agent-001",
            receiver="agent-002",
            content="消息2",
        )

        # 获取待处理消息
        messages = coordinator.get_pending_messages("agent-002")
        assert len(messages) == 2


class TestCoordinatorConflictResolution:
    """测试Coordinator冲突解决"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例（启用冲突检测）"""
        config = CoordinatorConfig(enable_conflict_detection=True)
        return Coordinator(config=config)

    def test_detect_resource_conflict(self, coordinator: Coordinator) -> None:
        """测试检测资源冲突"""
        # 注册Agent
        agent1 = AgentInfo(agent_id="agent-001", name="Agent 1", capabilities=[])
        agent2 = AgentInfo(agent_id="agent-002", name="Agent 2", capabilities=[])
        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

        # 创建资源冲突
        conflict = coordinator.detect_conflict(
            conflict_type=ConflictType.RESOURCE,
            agents=["agent-001", "agent-002"],
            resource_id="resource-001",
        )

        assert conflict is not None
        assert conflict.conflict_type == ConflictType.RESOURCE

    def test_resolve_conflict_with_priority(self, coordinator: Coordinator) -> None:
        """测试使用优先级解决冲突"""
        # 注册Agent（设置不同优先级）
        agent1 = AgentInfo(
            agent_id="agent-001",
            name="Agent 1",
            capabilities=[],
            priority=10,
        )
        agent2 = AgentInfo(
            agent_id="agent-002",
            name="Agent 2",
            capabilities=[],
            priority=5,
        )
        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

        # 创建并解决冲突
        conflict = coordinator.detect_conflict(
            conflict_type=ConflictType.RESOURCE,
            agents=["agent-001", "agent-002"],
            resource_id="resource-001",
        )

        if conflict:
            result = coordinator.resolve_conflict(
                conflict.conflict_id,
                strategy=ConflictResolutionStrategy.PRIORITY,
            )
            assert result is True

    def test_get_active_conflicts(self, coordinator: Coordinator) -> None:
        """测试获取活跃冲突"""
        # 注册Agent
        agent1 = AgentInfo(agent_id="agent-001", name="Agent 1", capabilities=[])
        agent2 = AgentInfo(agent_id="agent-002", name="Agent 2", capabilities=[])
        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)

        # 创建冲突
        coordinator.detect_conflict(
            conflict_type=ConflictType.RESOURCE,
            agents=["agent-001", "agent-002"],
            resource_id="resource-001",
        )

        # 获取活跃冲突
        conflicts = coordinator.get_active_conflicts()
        assert len(conflicts) == 1


class TestCoordinatorStateSync:
    """测试Coordinator状态同步"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例（启用状态同步）"""
        config = CoordinatorConfig(enable_state_sync=True)
        return Coordinator(config=config)

    def test_get_coordinator_state(self, coordinator: Coordinator) -> None:
        """测试获取Coordinator状态"""
        # 注册Agent
        agent = AgentInfo(agent_id="agent-001", name="Agent 1", capabilities=["task_a"])
        coordinator.register_agent(agent)

        # 获取状态
        state = coordinator.get_state()
        assert state["total_agents"] == 1
        assert state["active_agents"] == 1
        assert state["total_tasks"] == 0
        assert state["pending_tasks"] == 0

    def test_sync_agent_state(self, coordinator: Coordinator) -> None:
        """测试同步Agent状态"""
        # 注册Agent
        agent = AgentInfo(agent_id="agent-001", name="Agent 1", capabilities=["task_a"])
        coordinator.register_agent(agent)

        # 更新Agent状态
        coordinator.sync_agent_state("agent-001", {"custom_field": "value"})

        # 验证状态已同步
        updated_agent = coordinator.get_agent("agent-001")
        assert updated_agent is not None
        assert updated_agent.metadata.get("custom_field") == "value"


class TestCoordinatorMetrics:
    """测试Coordinator指标"""

    @pytest.fixture
    def coordinator(self) -> Coordinator:
        """创建Coordinator实例"""
        return Coordinator(config=CoordinatorConfig())

    def test_get_metrics(self, coordinator: Coordinator) -> None:
        """测试获取指标"""
        # 注册Agent
        agent = AgentInfo(agent_id="agent-001", name="Agent 1", capabilities=["task_a"])
        coordinator.register_agent(agent)

        # 提交并完成任务
        coordinator.submit_task("task-001", "task_a", {})
        coordinator.complete_task("task-001", "agent-001", {"status": "success"})

        # 获取指标
        metrics = coordinator.get_metrics()
        assert metrics["total_agents"] == 1
        assert metrics["total_tasks_submitted"] == 1
        assert metrics["total_tasks_completed"] == 1
        assert metrics["total_messages_sent"] == 0

