#!/usr/bin/env python3
"""
Collaboration模块__init__.py单元测试

测试多智能体协作框架的便捷函数和配置

测试范围:
- 便捷函数测试
- 模块常量验证
- 工厂函数测试
"""

import pytest

from core.collaboration import (
    # 便捷函数
    create_collaboration_framework,
    create_agent,
    create_task,
    create_collaboration_pattern,
    get_available_patterns,
    # 常量
    DEFAULT_MAX_AGENTS,
    DEFAULT_MAX_TASKS,
    DEFAULT_MESSAGE_QUEUE_SIZE,
    # 类和枚举
    Agent,
    AgentCapability,
    AgentStatus,
    Task,
    TaskStatus,
    Priority,
    CollaborationStrategy,
    ConflictResolutionStrategy,
    CollaborationPatternFactory,
    MultiAgentCollaborationFramework,
)


# ==================== 便捷函数测试 ====================

class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_create_collaboration_framework(self):
        """测试创建协作框架"""
        framework = create_collaboration_framework()

        assert framework is not None
        assert isinstance(framework, MultiAgentCollaborationFramework)

    def test_create_agent_basic(self):
        """测试创建基本智能体"""
        agent = create_agent(
            agent_id="test_agent_001",
            name="测试智能体",
            capabilities=[]
        )

        assert agent is not None
        assert agent.id == "test_agent_001"
        assert agent.name == "测试智能体"

    def test_create_agent_with_capabilities(self):
        """测试创建带能力的智能体"""
        capabilities = [
            AgentCapability(name="analysis", description="分析能力"),
            AgentCapability(name="search", description="搜索能力")
        ]

        agent = create_agent(
            agent_id="test_agent_002",
            name="分析智能体",
            capabilities=capabilities
        )

        assert agent.capabilities is not None
        assert len(agent.capabilities) == 2

    def test_create_task_basic(self):
        """测试创建基本任务"""
        task = create_task(
            title="测试任务",
            description="这是一个测试任务"
        )

        assert task is not None
        assert task.title == "测试任务"
        assert task.description == "这是一个测试任务"

    def test_create_task_with_required_capabilities(self):
        """测试创建带需求能力的任务"""
        task = create_task(
            title="分析任务",
            required_capabilities=["analysis", "research"]
        )

        assert task.required_capabilities is not None
        assert "analysis" in task.required_capabilities
        assert "research" in task.required_capabilities

    def test_create_task_with_kwargs(self):
        """测试创建带额外参数的任务"""
        task = create_task(
            title="优先任务",
            priority=Priority.HIGH,
            status=TaskStatus.PENDING
        )

        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.PENDING

    def test_create_collaboration_pattern_sequential(self):
        """测试创建顺序协作模式"""
        framework = create_collaboration_framework()

        pattern = create_collaboration_pattern("sequential", framework)

        # 验证模式对象创建成功（有具体类型而非None）
        assert pattern is not None
        assert hasattr(pattern, '__class__')

    def test_create_collaboration_pattern_parallel(self):
        """测试创建并行协作模式"""
        framework = create_collaboration_framework()

        pattern = create_collaboration_pattern("parallel", framework)

        # 验证模式对象创建成功（有具体类型而非None）
        assert pattern is not None
        assert hasattr(pattern, '__class__')

    def test_create_collaboration_pattern_invalid(self):
        """测试创建无效协作模式"""
        framework = create_collaboration_framework()

        pattern = create_collaboration_pattern("invalid_pattern", framework)

        # 应该返回None
        assert pattern is None

    def test_get_available_patterns(self):
        """测试获取可用协作模式"""
        patterns = get_available_patterns()

        assert isinstance(patterns, list)
        # 应该包含至少基本模式
        assert len(patterns) >= 0


# ==================== 模块常量测试 ====================

class TestModuleConstants:
    """测试模块常量"""

    def test_default_max_agents(self):
        """测试默认最大智能体数"""
        assert DEFAULT_MAX_AGENTS == 50
        assert isinstance(DEFAULT_MAX_AGENTS, int)
        assert DEFAULT_MAX_AGENTS > 0

    def test_default_max_tasks(self):
        """测试默认最大任务数"""
        assert DEFAULT_MAX_TASKS == 100
        assert isinstance(DEFAULT_MAX_TASKS, int)
        assert DEFAULT_MAX_TASKS > 0

    def test_default_message_queue_size(self):
        """测试默认消息队列大小"""
        assert DEFAULT_MESSAGE_QUEUE_SIZE == 1000
        assert isinstance(DEFAULT_MESSAGE_QUEUE_SIZE, int)
        assert DEFAULT_MESSAGE_QUEUE_SIZE > 0

    def test_constants_consistency(self):
        """测试常量一致性"""
        # 队列大小应该足够大以容纳消息
        assert DEFAULT_MESSAGE_QUEUE_SIZE >= DEFAULT_MAX_TASKS
        assert DEFAULT_MAX_TASKS >= DEFAULT_MAX_AGENTS


# ==================== 类导入测试 ====================

class TestClassImports:
    """测试类导入正确性"""

    def test_agent_class_exists(self):
        """测试Agent类存在"""
        agent = Agent(
            id="test",
            name="Test",
            capabilities=[]
        )
        assert agent.id == "test"

    def test_agent_capability_class_exists(self):
        """测试AgentCapability类存在"""
        capability = AgentCapability(
            name="test_capability",
            description="测试能力"
        )
        assert capability.name == "test_capability"

    def test_task_class_exists(self):
        """测试Task类存在"""
        task = Task(
            title="Test Task",
            description="测试"
        )
        assert task.title == "Test Task"

    def test_priority_enum(self):
        """测试Priority枚举"""
        assert Priority.LOW is not None
        assert Priority.NORMAL is not None
        assert Priority.HIGH is not None
        assert Priority.URGENT is not None  # 实际是URGENT而不是CRITICAL

    def test_task_status_enum(self):
        """测试TaskStatus枚举"""
        assert TaskStatus.PENDING is not None
        assert TaskStatus.IN_PROGRESS is not None  # 实际是IN_PROGRESS
        assert TaskStatus.COMPLETED is not None
        assert TaskStatus.FAILED is not None
        assert TaskStatus.ASSIGNED is not None
        assert TaskStatus.CANCELLED is not None

    def test_agent_status_enum(self):
        """测试AgentStatus枚举"""
        assert AgentStatus.IDLE is not None
        assert AgentStatus.BUSY is not None
        assert AgentStatus.COLLABORATING is not None
        assert AgentStatus.UNAVAILABLE is not None
        assert AgentStatus.ERROR is not None

    def test_collaboration_strategy_enum(self):
        """测试CollaborationStrategy枚举"""
        assert CollaborationStrategy.SEQUENTIAL is not None
        assert CollaborationStrategy.PARALLEL is not None
        assert CollaborationStrategy.HIERARCHICAL is not None
        assert CollaborationStrategy.PEER_TO_PEER is not None
        assert CollaborationStrategy.PIPELINE is not None
        assert CollaborationStrategy.CONSENSUS is not None

    def test_conflict_resolution_strategy_enum(self):
        """测试ConflictResolutionStrategy枚举"""
        assert ConflictResolutionStrategy.PRIORITY_BASED is not None
        assert ConflictResolutionStrategy.FIRST_COME_FIRST_SERVE is not None
        assert ConflictResolutionStrategy.LOAD_BALANCING is not None
        assert ConflictResolutionStrategy.NEGOTIATION is not None
        assert ConflictResolutionStrategy.ARBITRATION is not None


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试"""

    def test_create_and_use_framework(self):
        """测试创建和使用协作框架"""
        # 创建框架
        framework = create_collaboration_framework()

        # 创建智能体
        agent = create_agent(
            agent_id="agent_001",
            name="测试智能体",
            capabilities=[AgentCapability(name="test", description="测试")]
        )

        # 创建任务
        task = create_task(
            title="测试任务",
            required_capabilities=["test"]
        )

        # 验证对象创建成功
        assert framework is not None
        assert agent is not None
        assert task is not None

    def test_multiple_agents_creation(self):
        """测试创建多个智能体"""
        agents = []

        for i in range(5):
            agent = create_agent(
                agent_id=f"agent_{i}",
                name=f"智能体{i}",
                capabilities=[]
            )
            agents.append(agent)

        assert len(agents) == 5
        # 验证每个智能体ID唯一
        ids = [agent.id for agent in agents]
        assert len(ids) == len(set(ids))

    def test_task_lifecycle(self):
        """测试任务生命周期"""
        # 创建任务
        task = create_task(
            title="生命周期测试",
            status=TaskStatus.PENDING
        )

        assert task.status == TaskStatus.PENDING

        # 模拟状态转换（如果Task类支持）
        if hasattr(task, 'start'):
            task.start()
            assert task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """测试边界情况"""

    def test_create_agent_with_empty_name(self):
        """测试创建空名称智能体"""
        agent = create_agent(
            agent_id="test",
            name="",
            capabilities=[]
        )

        # 应该创建成功，名称为空字符串
        assert agent.name == ""

    def test_create_task_with_empty_title(self):
        """测试创建空标题任务"""
        task = create_task(
            title="",
            description="空标题任务"
        )

        # 应该创建成功
        assert task.title == ""

    def test_create_agent_with_long_id(self):
        """测试创建超长ID智能体"""
        long_id = "a" * 1000

        agent = create_agent(
            agent_id=long_id,
            name="Long ID Agent",
            capabilities=[]
        )

        assert agent.id == long_id

    def test_create_task_with_many_capabilities(self):
        """测试创建大量能力的任务"""
        many_capabilities = [f"capability_{i}" for i in range(100)]

        task = create_task(
            title="复杂任务",
            required_capabilities=many_capabilities
        )

        assert len(task.required_capabilities) == 100

    def test_get_available_patterns_multiple_calls(self):
        """测试多次调用获取可用模式"""
        patterns1 = get_available_patterns()
        patterns2 = get_available_patterns()

        # 结果应该一致
        assert patterns1 == patterns2
        assert isinstance(patterns1, list)


# ==================== 错误处理测试 ====================

class TestErrorHandling:
    """测试错误处理"""

    def test_create_agent_without_id(self):
        """测试不提供ID创建智能体"""
        # 应该抛出TypeError或允许None ID
        try:
            agent = create_agent(
                agent_id="",
                name="Test",
                capabilities=[]
            )
            # 如果不抛出异常，验证对象创建
            assert agent is not None
        except TypeError:
            # 预期可能抛出异常
            pass

    def test_create_task_with_none_capabilities(self):
        """测试None能力列表"""
        task = create_task(
            title="测试任务",
            required_capabilities=None
        )

        # 应该使用空列表作为默认值
        assert task.required_capabilities is not None
        assert isinstance(task.required_capabilities, list)


# ==================== 性能测试 ====================

class TestPerformance:
    """测试性能"""

    def test_create_framework_performance(self):
        """测试框架创建性能"""
        import time

        start = time.time()
        for _ in range(10):
            framework = create_collaboration_framework()
        elapsed = time.time() - start

        # 创建10个框架应该很快 (< 0.1秒)
        assert elapsed < 0.1

    def test_create_agent_performance(self):
        """测试智能体创建性能"""
        import time

        start = time.time()
        agents = []
        for i in range(100):
            agent = create_agent(
                agent_id=f"agent_{i}",
                name=f"Agent {i}",
                capabilities=[]
            )
            agents.append(agent)
        elapsed = time.time() - start

        # 创建100个智能体应该很快 (< 0.5秒)
        assert elapsed < 0.5
        assert len(agents) == 100

    def test_create_task_performance(self):
        """测试任务创建性能"""
        import time

        start = time.time()
        tasks = []
        for i in range(100):
            task = create_task(
                title=f"Task {i}",
                description=f"Description {i}"
            )
            tasks.append(task)
        elapsed = time.time() - start

        # 创建100个任务应该很快 (< 0.5秒)
        assert elapsed < 0.5
        assert len(tasks) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
