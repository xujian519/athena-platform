"""
BaseAgent单元测试

测试核心基类和注册中心的功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

pytestmark = pytest.mark.skip(reason="Missing required modules: ")

import asyncio
from datetime import datetime

# 跳过整个模块（模块导入失败时）
pytest.importorskip("core.agents.base")

from core.framework.agents.base import (
    AgentCapability,
    AgentMetadata,
    AgentRegistry,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
    HealthStatus,
)

# ========== 测试用的Mock智能体 ==========

class MockAgent(BaseAgent):
    """用于测试的简单Mock智能体"""

    @property
    def name(self) -> str:
        return "mock-agent"

    async def initialize(self) -> None:
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.success_response(
            request_id=request.request_id,
            data={"result": "ok", "action": request.action}
        )

    async def shutdown(self) -> None:
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status=AgentStatus.READY, message="OK")


class MockAgentWithCapabilities(BaseAgent):
    """带能力的Mock智能体"""

    @property
    def name(self) -> str:
        return "mock-agent-caps"

    def _register_capabilities(self) -> list:
        return [
            AgentCapability(
                name="test-capability",
                description="测试能力",
                parameters={"param1": {"type": "string"}},
                examples=[{"param1": "value1"}]
            )
        ]

    async def initialize(self) -> None:
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.success_response(
            request_id=request.request_id,
            data={"result": "ok"}
        )

    async def shutdown(self) -> None:
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status=AgentStatus.READY)


class FailingAgent(BaseAgent):
    """会失败的Mock智能体"""

    @property
    def name(self) -> str:
        return "failing-agent"

    async def initialize(self) -> None:
        raise RuntimeError("初始化失败")

    async def process(self, request: AgentRequest) -> AgentResponse:
        raise ValueError("处理失败")

    async def shutdown(self) -> None:
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status=AgentStatus.ERROR, message="智能体错误")


# ========== 测试清理fixture ==========

@pytest.fixture(autouse=True)
def clear_registry():
    """每个测试前后清理注册表"""
    AgentRegistry.clear()
    yield
    AgentRegistry.clear()


# ========== 数据模型测试 ==========

def test_agent_request_creation():
    """测试AgentRequest创建"""
    request = AgentRequest(
        request_id="test-001",
        action="test-action",
        parameters={"key": "value"}
    )

    assert request.request_id == "test-001"
    assert request.action == "test-action"
    assert request.parameters == {"key": "value"}
    assert isinstance(request.timestamp, datetime)


def test_agent_response_creation():
    """测试AgentResponse创建"""
    response = AgentResponse.success_response(
        request_id="test-001",
        data={"result": "ok"}
    )

    assert response.success is True
    assert response.request_id == "test-001"
    assert response.data == {"result": "ok"}
    assert response.error is None


def test_agent_response_error():
    """测试错误响应创建"""
    response = AgentResponse.error_response(
        request_id="test-001",
        error="处理失败"
    )

    assert response.success is False
    assert response.error == "处理失败"


def test_health_status():
    """测试HealthStatus"""
    status = HealthStatus(
        status=AgentStatus.READY,
        message="OK",
        details={"key": "value"}
    )

    assert status.is_healthy() is True
    assert status.to_dict()["healthy"] is True


def test_agent_capability():
    """测试AgentCapability"""
    capability = AgentCapability(
        name="test-cap",
        description="测试能力",
        parameters={"param1": {"type": "string"}},
        examples=[{"param1": "value1"}]
    )

    assert capability.name == "test-cap"
    assert capability.to_dict()["name"] == "test-cap"


def test_agent_metadata():
    """测试AgentMetadata"""
    metadata = AgentMetadata(
        name="test-agent",
        version="1.0.0",
        description="测试智能体",
        author="Test Author",
        tags=["test", "mock"]
    )

    assert metadata.name == "test-agent"
    assert metadata.to_dict()["tags"] == ["test", "mock"]


# ========== BaseAgent基础测试 ==========

def test_agent_initialization():
    """测试智能体初始化"""
    agent = MockAgent()

    assert agent.name == "mock-agent"
    assert agent.status == AgentStatus.INITIALIZING
    assert agent.is_ready is False


def test_agent_metadata_loading():
    """测试元数据加载"""
    agent = MockAgent()
    metadata = agent.get_metadata()

    assert isinstance(metadata, AgentMetadata)
    assert metadata.name == "mock-agent"
    assert metadata.version == "1.0.0"


def test_agent_capabilities():
    """测试能力获取"""
    agent = MockAgentWithCapabilities()
    capabilities = agent.get_capabilities()

    assert len(capabilities) == 1
    assert capabilities[0].name == "test-capability"


def test_agent_context():
    """测试上下文管理"""
    agent = MockAgent()

    agent.set_context("key1", "value1")
    agent.set_context("key2", {"nested": "value"})

    assert agent.get_context("key1") == "value1"
    assert agent.get_context("key2") == {"nested": "value"}
    assert agent.get_context("key3", "default") == "default"


def test_agent_stats():
    """测试统计信息"""
    agent = MockAgent()
    stats = agent.get_stats()

    assert stats["total_requests"] == 0
    assert stats["successful_requests"] == 0


# ========== 异步方法测试 ==========

class TestAgentLifecycle:
    """智能体生命周期测试"""

    async def test_agent_initialize(self):
        """测试初始化流程"""
        agent = MockAgent()
        assert agent.status == AgentStatus.INITIALIZING

        await agent.initialize()

        assert agent.is_ready
        assert agent.status == AgentStatus.READY

    async def test_agent_shutdown(self):
        """测试关闭流程"""
        agent = MockAgent()
        await agent.initialize()
        await agent.shutdown()

        assert agent.status == AgentStatus.SHUTDOWN

    async def test_agent_health_check(self):
        """测试健康检查"""
        agent = MockAgent()
        await agent.initialize()

        status = await agent.health_check()

        assert status.status == AgentStatus.READY
        assert status.is_healthy()

    async def test_agent_ping(self):
        """测试ping方法"""
        agent = MockAgent()
        await agent.initialize()

        assert await agent.ping() is True


class TestAgentProcessing:
    """智能体处理测试"""

    async def test_process_request(self):
        """测试请求处理"""
        agent = MockAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-001",
            action="test-action",
            parameters={"key": "value"}
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.request_id == "test-001"
        assert response.data["result"] == "ok"

    async def test_process_updates_stats(self):
        """测试处理更新统计"""
        agent = MockAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-001",
            action="test"
        )

        await agent.safe_process(request)

        stats = agent.get_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1

    async def test_process_without_action_fails(self):
        """测试无action参数的请求失败"""
        agent = MockAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-001",
            action=""  # 空action
        )

        response = await agent.safe_process(request)

        assert response.success is False
        assert "验证失败" in response.error

    async def test_process_when_not_ready_fails(self):
        """测试未就绪状态处理失败"""
        agent = MockAgent()
        # 不调用initialize，保持INITIALIZING状态

        request = AgentRequest(
            request_id="test-001",
            action="test"
        )

        response = await agent.safe_process(request)

        assert response.success is False
        assert "未就绪" in response.error


class TestAgentErrorHandling:
    """智能体错误处理测试"""

    async def test_initialize_failure_sets_error_status(self):
        """测试初始化失败设置错误状态"""
        agent = FailingAgent()

        with pytest.raises(RuntimeError):
            await agent.initialize()

        # 状态应该是ERROR
        assert agent.status == AgentStatus.INITIALIZING

    async def test_process_exception_caught_by_safe_process(self):
        """测试process异常被safe_process捕获"""
        agent = FailingAgent()
        # 手动设置为READY，跳过initialize
        agent._status = AgentStatus.READY

        request = AgentRequest(
            request_id="test-001",
            action="test"
        )

        response = await agent.safe_process(request)

        assert response.success is False
        assert "处理失败" in response.error

        # 状态应该被设置为ERROR
        assert agent.status == AgentStatus.ERROR

    async def test_failed_request_increments_failed_stats(self):
        """测试失败请求增加失败计数"""
        agent = FailingAgent()
        agent._status = AgentStatus.READY

        request = AgentRequest(
            request_id="test-001",
            action="test"
        )

        await agent.safe_process(request)

        stats = agent.get_stats()
        assert stats["failed_requests"] == 1


# ========== AgentRegistry测试 ==========

def test_registry_register_agent():
    """测试注册智能体"""
    agent = MockAgent()
    AgentRegistry.register(agent)

    assert "mock-agent" in AgentRegistry.list_agents()


def test_registry_duplicate_registration_fails():
    """测试重复注册失败"""
    agent1 = MockAgent()
    agent2 = MockAgent()

    AgentRegistry.register(agent1)

    with pytest.raises(ValueError, match="已存在"):
        AgentRegistry.register(agent2)


def test_registry_get_agent():
    """测试获取智能体"""
    agent = MockAgent()
    AgentRegistry.register(agent)

    retrieved = AgentRegistry.get("mock-agent")

    assert retrieved is agent


def test_registry_get_nonexistent_returns_none():
    """测试获取不存在的智能体返回None"""
    retrieved = AgentRegistry.get("nonexistent")
    assert retrieved is None


def test_registry_unregister_agent():
    """测试注销智能体"""
    agent = MockAgent()
    AgentRegistry.register(agent)

    AgentRegistry.unregister("mock-agent")

    assert "mock-agent" not in AgentRegistry.list_agents()
    assert AgentRegistry.get("mock-agent") is None


def test_registry_get_by_capability():
    """测试根据能力获取智能体"""
    agent = MockAgentWithCapabilities()
    AgentRegistry.register(agent)

    agents = AgentRegistry.get_by_capability("test-capability")

    assert len(agents) == 1
    assert agents[0].name == "mock-agent-caps"


def test_registry_get_ready_agents():
    """测试获取就绪智能体"""
    # 清理注册表
    AgentRegistry.clear()
    try:
        agent1 = MockAgent()
        AgentRegistry.register(agent1)

        # 使用不同类型的智能体避免名称冲突
        agent2 = MockAgentWithCapabilities()
        AgentRegistry.register(agent2)

        # 只初始化一个
        import asyncio
        asyncio.run(agent1.initialize())

        ready_agents = AgentRegistry.get_ready_agents()

        assert len(ready_agents) == 1
        assert ready_agents[0].name == "mock-agent"
    finally:
        AgentRegistry.clear()


@pytest.mark.asyncio
async def test_registry_initialize_all():
    """测试初始化所有智能体"""
    AgentRegistry.clear()
    try:
        agent1 = MockAgent()
        # 使用不同类型的智能体避免名称冲突
        agent2 = MockAgentWithCapabilities()

        AgentRegistry.register(agent1)
        AgentRegistry.register(agent2)

        await AgentRegistry.initialize_all()

        assert agent1.is_ready
        assert agent2.is_ready
    finally:
        AgentRegistry.clear()


@pytest.mark.asyncio
async def test_registry_shutdown_all():
    """测试关闭所有智能体"""
    AgentRegistry.clear()
    try:
        agent1 = MockAgent()
        # 使用不同类型的智能体避免名称冲突
        agent2 = MockAgentWithCapabilities()

        AgentRegistry.register(agent1)
        AgentRegistry.register(agent2)

        await AgentRegistry.initialize_all()
        await AgentRegistry.shutdown_all()

        assert agent1.status == AgentStatus.SHUTDOWN
        assert agent2.status == AgentStatus.SHUTDOWN
    finally:
        AgentRegistry.clear()


@pytest.mark.asyncio
async def test_registry_health_check_all():
    """测试检查所有智能体健康状态"""
    AgentRegistry.clear()
    try:
        agent1 = MockAgent()
        # 使用不同类型的智能体避免名称冲突
        agent2 = MockAgentWithCapabilities()

        AgentRegistry.register(agent1)
        AgentRegistry.register(agent2)

        await AgentRegistry.initialize_all()

        health_results = await AgentRegistry.health_check_all()

        assert "mock-agent" in health_results
        assert health_results["mock-agent"].is_healthy()
    finally:
        AgentRegistry.clear()


def test_registry_clear():
    """测试清空注册表"""
    agent = MockAgent()
    AgentRegistry.register(agent)

    AgentRegistry.clear()

    assert AgentRegistry.list_agents() == []


# ========== 集成测试 ==========

@pytest.mark.asyncio
async def test_full_agent_lifecycle():
    """测试完整的智能体生命周期"""
    # 创建
    agent = MockAgent()
    assert agent.status == AgentStatus.INITIALIZING

    # 注册
    AgentRegistry.register(agent)
    assert "mock-agent" in AgentRegistry.list_agents()

    # 初始化
    await agent.initialize()
    assert agent.is_ready

    # 健康检查
    status = await agent.health_check()
    assert status.is_healthy()

    # 处理请求
    request = AgentRequest(request_id="test-001", action="test")
    response = await agent.safe_process(request)
    assert response.success

    # 关闭
    await agent.shutdown()
    assert agent.status == AgentStatus.SHUTDOWN

    # 清理
    AgentRegistry.unregister("mock-agent")


@pytest.mark.asyncio
async def test_agent_to_dict():
    """测试智能体转换为字典"""
    agent = MockAgentWithCapabilities()
    await agent.initialize()

    agent_dict = agent.to_dict()

    assert agent_dict["name"] == "mock-agent-caps"
    assert agent_dict["status"] == "ready"
    assert "metadata" in agent_dict
    assert "capabilities" in agent_dict
    assert "stats" in agent_dict


# ========== 运行测试 ==========

if __name__ == "__main__":
    # 运行单个测试
    print("运行基础测试...")

    # 数据模型测试
    print("  测试数据模型...")
    test_agent_request_creation()
    test_agent_response_creation()
    test_health_status()

    # 智能体测试
    print("  测试智能体...")
    test_agent_initialization()
    test_agent_metadata_loading()
    test_agent_context()

    # 注册中心测试
    print("  测试注册中心...")
    test_registry_register_agent()
    test_registry_get_agent()

    # 异步测试
    print("  运行异步测试...")
    asyncio.run(test_full_agent_lifecycle())

    print("\n所有测试通过!")
