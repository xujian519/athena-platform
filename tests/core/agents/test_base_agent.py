#!/usr/bin/env python3
"""
BaseAgent单元测试

测试BaseAgent的所有核心功能，确保覆盖率>80%

测试范围:
- Agent初始化
- 对话历史管理
- 记忆管理
- 能力管理
- 输入验证
- 配置验证
- Gateway通信
- 工具类
- 响应类
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.agents.base_agent import (
    BaseAgent,
    AgentUtils,
    AgentResponse,
)


# ==================== 测试Agent实现 ====================

class MockAgent(BaseAgent):
    """Mock Agent用于测试抽象类"""

    def __init__(self, name: str = "test_agent", role: str = "test", **kwargs):
        super().__init__(name=name, role=role, **kwargs)

    def process(self, input_text: str, **kwargs) -> str:
        """处理输入（简单实现）"""
        return f"Processed: {input_text}"


class MockAgentWithGateway(BaseAgent):
    """Mock Agent with Gateway support"""

    def __init__(self, name: str = "test_agent", role: str = "test", **kwargs):
        super().__init__(name=name, role=role, enable_gateway=True, **kwargs)

    def process(self, input_text: str, **kwargs) -> str:
        """处理输入"""
        return f"Processed: {input_text}"


# ==================== Agent初始化测试 ====================

class TestAgentInitialization:
    """测试Agent初始化"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        agent = MockAgent(name="test", role="assistant")

        assert agent.name == "test"
        assert agent.role == "assistant"
        assert agent.model == "gpt-4"
        assert agent.temperature == 0.7
        assert agent.max_tokens == 2000

    def test_initialization_with_custom_params(self):
        """测试自定义参数初始化"""
        agent = MockAgent(
            name="custom",
            role="expert",
            model="claude-sonnet-4-6",
            temperature=0.5,
            max_tokens=4096
        )

        assert agent.model == "claude-sonnet-4-6"
        assert agent.temperature == 0.5
        assert agent.max_tokens == 4096

    def test_initialization_attributes(self):
        """测试初始化后的属性"""
        agent = MockAgent(name="test", role="assistant")

        # 对话历史应为空
        assert agent.conversation_history == []
        # 能力列表应为空
        assert agent.capabilities == []
        # 记忆字典应为空
        assert agent.memory == {}
        # Gateway客户端初始为None
        assert agent._gateway_client is None

    def test_determine_agent_type_xiaona(self):
        """测试小娜Agent类型识别"""
        agent = MockAgent(name="xiaona", role="legal_expert")

        # Gateway可能不可用
        if agent._agent_type:
            assert "XIAONA" in str(agent._agent_type)

    def test_determine_agent_type_xiaonuo(self):
        """测试小诺Agent类型识别"""
        agent = MockAgent(name="xiaonuo", role="coordinator")

        if agent._agent_type:
            assert "XIAONUO" in str(agent._agent_type)

    def test_determine_agent_type_yunxi(self):
        """测试云熙Agent类型识别"""
        agent = MockAgent(name="yunxi", role="ip_manager")

        if agent._agent_type:
            assert "YUNXI" in str(agent._agent_type)


# ==================== 对话历史管理测试 ====================

class TestConversationHistory:
    """测试对话历史管理"""

    def test_add_to_history(self):
        """测试添加到历史"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_to_history("user", "Hello")
        agent.add_to_history("assistant", "Hi there")

        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[0] == {"role": "user", "content": "Hello"}
        assert agent.conversation_history[1] == {"role": "assistant", "content": "Hi there"}

    def test_clear_history(self):
        """测试清空历史"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_to_history("user", "Hello")
        agent.add_to_history("assistant", "Hi")

        assert len(agent.conversation_history) == 2

        agent.clear_history()

        assert agent.conversation_history == []

    def test_get_history(self):
        """测试获取历史副本"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_to_history("user", "Test")

        history = agent.get_history()

        assert len(history) == 1
        # 确保返回的是副本
        history.append({"role": "test", "content": "test"})

        assert len(agent.conversation_history) == 1  # 原始历史未改变


# ==================== 记忆管理测试 ====================

class TestMemoryManagement:
    """测试记忆管理"""

    def test_remember(self):
        """测试记住信息"""
        agent = MockAgent(name="test", role="assistant")

        agent.remember("user_name", "Alice")
        agent.remember("user_age", 30)

        assert agent.memory["user_name"] == "Alice"
        assert agent.memory["user_age"] == 30
        assert len(agent.memory) == 2

    def test_recall(self):
        """测试回忆信息"""
        agent = MockAgent(name="test", role="assistant")

        agent.remember("fact", "Python is awesome")

        result = agent.recall("fact")

        assert result == "Python is awesome"

    def test_recall_nonexistent(self):
        """测试回忆不存在的键"""
        agent = MockAgent(name="test", role="assistant")

        result = agent.recall("nonexistent")

        assert result is None

    def test_forget(self):
        """测试忘记信息"""
        agent = MockAgent(name="test", role="assistant")

        agent.remember("temp", "temporary data")

        assert "temp" in agent.memory

        result = agent.forget("temp")

        assert result is True
        assert "temp" not in agent.memory

    def test_forget_nonexistent(self):
        """测试忘记不存在的键"""
        agent = MockAgent(name="test", role="assistant")

        result = agent.forget("nonexistent")

        assert result is False


# ==================== 能力管理测试 ====================

class TestCapabilityManagement:
    """测试能力管理"""

    def test_add_capability(self):
        """测试添加能力"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_capability("patent_analysis")
        agent.add_capability("legal_research")

        assert "patent_analysis" in agent.capabilities
        assert "legal_research" in agent.capabilities
        assert len(agent.capabilities) == 2

    def test_add_duplicate_capability(self):
        """测试添加重复能力"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_capability("analysis")
        agent.add_capability("analysis")  # 重复

        # 重复能力不会被添加
        assert agent.capabilities.count("analysis") == 1
        assert len(agent.capabilities) == 1

    def test_has_capability(self):
        """测试检查能力"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_capability("test_capability")

        assert agent.has_capability("test_capability") is True
        assert agent.has_capability("nonexistent") is False

    def test_get_capabilities(self):
        """测试获取能力列表"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_capability("cap1")
        agent.add_capability("cap2")

        capabilities = agent.get_capabilities()

        assert "cap1" in capabilities
        assert "cap2" in capabilities
        # 确保返回的是副本
        capabilities.append("cap3")

        assert "cap3" not in agent.capabilities


# ==================== 输入验证测试 ====================

class TestInputValidation:
    """测试输入验证"""

    def test_validate_input_valid(self):
        """测试有效输入"""
        agent = MockAgent(name="test", role="assistant")

        assert agent.validate_input("Hello") is True
        assert agent.validate_input("  Test  ") is True

    def test_validate_input_empty(self):
        """测试空输入"""
        agent = MockAgent(name="test", role="assistant")

        assert agent.validate_input("") is False
        assert agent.validate_input("   ") is False
        assert agent.validate_input(None) is False

    def test_validate_config_valid(self):
        """测试有效配置"""
        agent = MockAgent(
            name="test",
            role="assistant",
            temperature=0.5,
            max_tokens=1000
        )

        assert agent.validate_config() is True

    def test_validate_config_invalid_temperature(self):
        """测试无效温度"""
        agent = MockAgent(
            name="test",
            role="assistant",
            temperature=-0.1  # 无效
        )

        assert agent.validate_config() is False

    def test_validate_config_invalid_max_tokens(self):
        """测试无效max_tokens"""
        agent = MockAgent(
            name="test",
            role="assistant",
            max_tokens=0  # 无效
        )

        assert agent.validate_config() is False

    def test_validate_config_empty_name(self):
        """测试空名称"""
        agent = MockAgent(
            name="",  # 无效
            role="assistant"
        )

        assert agent.validate_config() is False


# ==================== 信息获取测试 ====================

class TestAgentInfo:
    """测试Agent信息获取"""

    def test_get_info(self):
        """测试获取信息"""
        agent = MockAgent(
            name="test_agent",
            role="expert",
            model="gpt-4",
            temperature=0.8,
            max_tokens=3000
        )

        # 添加一些数据
        agent.add_capability("test_cap")
        agent.add_to_history("user", "Hello")
        agent.remember("key", "value")

        info = agent.get_info()

        assert info["name"] == "test_agent"
        assert info["role"] == "expert"
        assert info["model"] == "gpt-4"
        assert info["temperature"] == 0.8
        assert info["max_tokens"] == 3000
        assert "test_cap" in info["capabilities"]
        assert info["history_length"] == 1
        assert info["memory_size"] == 1

    def test_string_representation(self):
        """测试字符串表示"""
        agent = MockAgent(name="test", role="assistant")

        assert str(agent) == "BaseAgent(name=test, role=assistant)"
        assert repr(agent) == "BaseAgent(name=test, role=assistant)"


# ==================== Gateway通信测试 ====================

class TestGatewayCommunication:
    """测试Gateway通信"""

    @pytest.mark.asyncio
    async def test_connect_gateway_unavailable(self):
        """测试Gateway不可用时连接"""
        agent = MockAgentWithGateway(name="test", role="assistant")

        # Patch GATEWAY_AVAILABLE to False
        with patch('core.agents.base_agent.GATEWAY_AVAILABLE', False):
            result = await agent.connect_gateway()
            assert result is False

    @pytest.mark.asyncio
    async def test_connect_gateway_disabled(self):
        """测试Gateway禁用时连接"""
        agent = MockAgent(name="test", role="assistant", enable_gateway=False)

        result = await agent.connect_gateway()
        assert result is False

    @pytest.mark.asyncio
    async def test_gateway_connected_property(self):
        """测试Gateway连接状态属性"""
        agent = MockAgentWithGateway(name="test", role="assistant")

        # 未连接时
        assert agent.gateway_connected is False

    @pytest.mark.asyncio
    async def test_gateway_session_id_property(self):
        """测试Gateway会话ID属性"""
        agent = MockAgentWithGateway(name="test", role="assistant")

        # 未连接时返回空字符串
        assert agent.gateway_session_id == ""

    @pytest.mark.asyncio
    async def test_send_to_agent_not_connected(self):
        """测试未连接时发送消息"""
        agent = MockAgentWithGateway(name="test", role="assistant")

        result = await agent.send_to_agent("xiaona", "test_task")

        assert result is None

    @pytest.mark.asyncio
    async def test_broadcast_not_connected(self):
        """测试未连接时广播"""
        agent = MockAgentWithGateway(name="test", role="assistant")

        result = await agent.broadcast({"message": "test"})

        assert result is False


# ==================== AgentUtils测试 ====================

class TestAgentUtils:
    """测试AgentUtils工具类"""

    def test_format_message(self):
        """测试消息格式化"""
        message = AgentUtils.format_message("user", "Hello")

        assert message == {"role": "user", "content": "Hello"}

    def test_truncate_text_short(self):
        """测试截断短文本"""
        text = "Short text"
        result = AgentUtils.truncate_text(text, max_length=100)

        assert result == text

    def test_truncate_text_long(self):
        """测试截断长文本"""
        text = "A" * 2000
        result = AgentUtils.truncate_text(text, max_length=1000)

        # 长度应该是1003 (1000个A + "...")
        assert len(result) == 1003
        assert result.endswith("...")

    def test_extract_code(self):
        """测试代码提取"""
        text = """
        Some text
        ```python
        def hello():
            print("world")
        ```
        More text
        """

        codes = AgentUtils.extract_code(text)

        assert len(codes) == 1
        assert "def hello():" in codes[0]

    def test_extract_code_multiple(self):
        """测试提取多个代码块"""
        text = """
        ```python
        code1
        ```
        ```javascript
        code2
        ```
        """

        codes = AgentUtils.extract_code(text)

        assert len(codes) == 2

    def test_sanitize_input(self):
        """测试输入清理"""
        text = "  Hello    World  \t\n"
        result = AgentUtils.sanitize_input(text)

        assert result == "Hello World"

    def test_sanitize_input_control_chars(self):
        """测试控制字符清理"""
        text = "Hello\x00\x1fWorld"
        result = AgentUtils.sanitize_input(text)

        assert "\x00" not in result
        assert "\x1f" not in result


# ==================== AgentResponse测试 ====================

class TestAgentResponse:
    """测试AgentResponse响应类"""

    def test_create_response(self):
        """测试创建响应"""
        response = AgentResponse(
            content="Test response",
            success=True,
            metadata={"key": "value"}
        )

        assert response.content == "Test response"
        assert response.success is True
        assert response.metadata["key"] == "value"

    def test_to_dict(self):
        """测试转换为字典"""
        response = AgentResponse(
            content="Test",
            success=True,
            metadata={"test": "data"}
        )

        result = response.to_dict()

        assert result["content"] == "Test"
        assert result["success"] is True
        assert result["metadata"]["test"] == "data"

    def test_error_response(self):
        """测试创建错误响应"""
        response = AgentResponse.error("Something went wrong")

        assert response.content == "Something went wrong"
        assert response.success is False
        assert response.metadata["error"] is True

    def test_success_response(self):
        """测试创建成功响应"""
        response = AgentResponse.success_response(
            "Done!",
            extra="info"
        )

        assert response.content == "Done!"
        assert response.success is True
        assert response.metadata["extra"] == "info"

    def test_response_with_none_success(self):
        """测试success为None时的响应"""
        response = AgentResponse(content="Test", success=None)

        assert response.content == "Test"
        assert response.success is None

    def test_response_with_empty_metadata(self):
        """测试空元数据"""
        response = AgentResponse(content="Test", metadata=None)

        assert response.metadata == {}


# ==================== Process方法测试 ====================

class TestAgentProcess:
    """测试Agent处理逻辑"""

    def test_process_basic(self):
        """测试基本处理"""
        agent = MockAgent(name="test", role="assistant")

        result = agent.process("Hello")

        assert result == "Processed: Hello"

    def test_process_with_kwargs(self):
        """测试带参数的处理"""
        agent = MockAgent(name="test", role="assistant")

        result = agent.process("Hello", temperature=0.5)

        assert "Processed: Hello" in result


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """测试边界情况"""

    def test_empty_history_after_clear(self):
        """测试清空后历史为空"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_to_history("user", "Test")
        agent.clear_history()

        assert len(agent.get_history()) == 0

    def test_memory_with_complex_value(self):
        """测试记忆复杂数据"""
        agent = MockAgent(name="test", role="assistant")

        complex_data = {"list": [1, 2, 3], "dict": {"key": "value"}}
        agent.remember("complex", complex_data)

        result = agent.recall("complex")

        assert result == complex_data

    def test_capability_case_sensitivity(self):
        """测试能力区分大小写"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_capability("Python")

        assert agent.has_capability("Python") is True
        assert agent.has_capability("python") is False

    def test_multiple_add_to_history(self):
        """测试多次添加历史"""
        agent = MockAgent(name="test", role="assistant")

        for i in range(100):
            agent.add_to_history("user", f"Message {i}")

        assert len(agent.conversation_history) == 100
        assert agent.conversation_history[-1]["content"] == "Message 99"

    def test_get_history_does_not_modify_original(self):
        """测试获取历史不影响原始数据"""
        agent = MockAgent(name="test", role="assistant")

        agent.add_to_history("user", "Original")

        history = agent.get_history()
        history.append({"role": "system", "content": "Modified"})

        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0]["role"] == "user"


# ==================== 性能测试 ====================

class TestPerformance:
    """测试性能指标"""

    def test_memory_retrieval_speed(self):
        """测试记忆检索速度"""
        import time

        agent = MockAgent(name="test", role="assistant")

        # 添加100个记忆项
        for i in range(100):
            agent.remember(f"key_{i}", f"value_{i}")

        # 测试检索速度
        start = time.time()
        for i in range(100):
            agent.recall(f"key_{i}")
        elapsed = time.time() - start

        # 应该非常快 (< 0.1秒)
        assert elapsed < 0.1

    def test_capability_check_speed(self):
        """测试能力检查速度"""
        import time

        agent = MockAgent(name="test", role="assistant")

        # 添加50个能力
        for i in range(50):
            agent.add_capability(f"capability_{i}")

        # 测试检查速度
        start = time.time()
        for i in range(50):
            agent.has_capability(f"capability_{i}")
        elapsed = time.time() - start

        # 应该很快 (< 0.01秒)
        assert elapsed < 0.01
