"""
统一Agent系统测试

Author: Athena Team
Version: 1.0.0
Date: 2026-04-24
"""

import asyncio

from core.unified_agents.base import (
    AgentRequest,
    AgentResponse,
    AgentStatus,
    HealthStatus,
    MessageConverter,
    ResponseMessage,
    TaskMessage,
)
from core.unified_agents.adapters import (
    AdapterFactory,
    LegacyAgentAdapter,
)
from core.unified_agents.config import UnifiedAgentConfig
from core.unified_agents.base_agent import UnifiedBaseAgent


# ============ 测试Agent ============


class TestAgent(UnifiedBaseAgent):
    """测试用Agent"""

    def __init__(self, config: UnifiedAgentConfig):
        super().__init__(config)
        self._initialized = False
        self._shutdown_called = False

    @property
    def name(self) -> str:
        return "test-agent"

    async def initialize(self) -> None:
        self._initialized = True
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        if request.action == "error":
            raise ValueError("测试错误")
        return AgentResponse.success_response(
            request_id=request.request_id,
            data={"action": request.action, "params": request.parameters}
        )

    async def shutdown(self) -> None:
        self._shutdown_called = True
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=self._status,
            message="测试Agent健康"
        )


# ============ 测试传统Agent ============


class TestLegacyAgent:
    """测试用传统Agent"""

    def __init__(self):
        self.name = "legacy-test-agent"
        self.role = "legacy"
        self.capabilities = ["test"]

    def process(self, input_text: str, **kwargs) -> str:
        return f"处理: {input_text}"

    def get_capabilities(self) -> list:
        return self.capabilities


# ============ 测试函数 ============


async def test_agent_lifecycle():
    """测试Agent生命周期"""
    config = UnifiedAgentConfig.create_minimal("test-agent", "tester")
    agent = TestAgent(config)

    # 初始状态
    assert agent.status == AgentStatus.INITIALIZING

    # 初始化
    await agent.initialize()
    assert agent._initialized is True
    assert agent.status == AgentStatus.READY
    assert agent.is_ready is True

    # 健康检查
    health = await agent.health_check()
    assert health.is_healthy() is True

    # 关闭
    await agent.shutdown()
    assert agent._shutdown_called is True
    assert agent.status == AgentStatus.SHUTDOWN

    print("✓ 生命周期测试通过")


async def test_agent_process():
    """测试Agent处理请求"""
    config = UnifiedAgentConfig.create_minimal("test-agent", "tester")
    agent = TestAgent(config)
    await agent.initialize()

    # 正常请求
    request = AgentRequest(
        request_id="test-001",
        action="test_action",
        parameters={"key": "value"}
    )

    response = await agent.process(request)
    assert response.success is True
    assert response.data["action"] == "test_action"
    assert response.data["params"]["key"] == "value"

    # 错误请求
    error_request = AgentRequest(
        request_id="test-002",
        action="error",
        parameters={}
    )

    error_response = await agent.process(error_request)
    assert error_response.success is False
    assert "测试错误" in error_response.error

    await agent.shutdown()
    print("✓ 处理请求测试通过")


async def test_agent_stats():
    """测试性能统计"""
    config = UnifiedAgentConfig.create_minimal("test-agent", "tester")
    agent = TestAgent(config)
    await agent.initialize()

    # 执行一些请求
    for i in range(5):
        request = AgentRequest(
            request_id=f"test-{i}",
            action="test",
            parameters={}
        )
        await agent.safe_process(request)

    stats = agent.get_stats()
    assert stats["total_requests"] == 5
    assert stats["successful_requests"] == 5
    assert stats["failed_requests"] == 0
    assert stats["avg_processing_time_ms"] > 0

    await agent.shutdown()
    print("✓ 性能统计测试通过")


async def test_message_conversion():
    """测试消息格式转换"""
    # 传统任务消息
    task_msg = TaskMessage(
        sender_id="user",
        recipient_id="agent",
        task_type="process",
        content={"input": "test"},
        task_id="task-001"
    )

    # 转换为新请求格式
    new_request = MessageConverter.task_to_request(task_msg)
    assert new_request.request_id == "task-001"
    assert new_request.action == "process"
    assert new_request.parameters == {"input": "test"}

    # 转换回传统格式
    task_msg_2 = MessageConverter.request_to_task(new_request, "agent")
    assert task_msg_2.task_id == "task-001"
    assert task_msg_2.task_type == "process"
    assert task_msg_2.content == {"input": "test"}

    print("✓ 消息转换测试通过")


async def test_legacy_adapter():
    """测试传统Agent适配器"""
    legacy = TestLegacyAgent()

    # 创建适配器
    config = UnifiedAgentConfig.create_minimal("legacy-test-agent", "legacy")
    adapter = LegacyAgentAdapter(legacy, config)

    # 初始化
    await adapter.initialize()
    assert adapter.name == "legacy-test-agent"
    assert adapter.is_ready is True

    # 处理请求
    request = AgentRequest(
        request_id="test-legacy",
        action="process",
        parameters={"input": "hello"}
    )

    response = await adapter.process(request)
    assert response.success is True

    # 健康检查
    health = await adapter.health_check()
    assert health.is_healthy() is True

    await adapter.shutdown()
    print("✓ 适配器测试通过")


async def test_adapter_factory():
    """测试适配器工厂"""
    legacy = TestLegacyAgent()

    # 使用工厂创建适配器
    adapter = AdapterFactory.create_adapter(legacy)
    assert isinstance(adapter, UnifiedBaseAgent)

    # 检查类型判断
    assert AdapterFactory.is_legacy_agent(legacy) is True
    assert AdapterFactory.is_unified_agent(adapter) is True
    assert AdapterFactory.is_unified_agent(legacy) is False

    print("✓ 适配器工厂测试通过")


async def test_config_validation():
    """测试配置验证"""
    # 有效配置
    valid_config = UnifiedAgentConfig.create_minimal("test", "tester")
    is_valid, errors = valid_config.validate()
    assert is_valid is True
    assert len(errors) == 0

    # 无效配置
    invalid_config = UnifiedAgentConfig(
        name="",
        role="",
        temperature=2.0,  # 超出范围
        max_tokens=-1     # 负数
    )
    is_valid, errors = invalid_config.validate()
    assert is_valid is False
    assert len(errors) > 0

    print("✓ 配置验证测试通过")


async def test_config_builder():
    """测试配置构建器"""
    from core.unified_agents import UnifiedAgentConfigBuilder

    config = (UnifiedAgentConfigBuilder()
              .name("builder-test")
              .role("builder")
              .model("gpt-4")
              .temperature(0.5)
              .build())

    assert config.name == "builder-test"
    assert config.role == "builder"
    assert config.model == "gpt-4"
    assert config.temperature == 0.5

    print("✓ 配置构建器测试通过")


async def test_safe_process():
    """测试安全处理包装"""
    config = UnifiedAgentConfig.create_minimal("test-agent", "tester")
    agent = TestAgent(config)
    await agent.initialize()

    # 正常请求
    request = AgentRequest(
        request_id="test-001",
        action="test",
        parameters={}
    )

    response = await agent.safe_process(request)
    assert response.success is True

    # 统计更新
    stats = agent.get_stats()
    assert stats["total_requests"] == 1
    assert stats["successful_requests"] == 1

    await agent.shutdown()
    print("✓ 安全处理测试通过")


# ============ 测试运行器 ============


async def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("统一Agent系统测试")
    print("=" * 50)

    await test_agent_lifecycle()
    await test_agent_process()
    await test_agent_stats()
    await test_message_conversion()
    await test_legacy_adapter()
    await test_adapter_factory()
    await test_config_validation()
    await test_config_builder()
    await test_safe_process()

    print("=" * 50)
    print("所有测试通过!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
