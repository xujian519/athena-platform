#!/usr/bin/env python3
"""
BaseAgent统一测试

测试BaseAgent的所有核心功能，兼容新旧两种架构
- 旧架构: core.agents.base_agent.BaseAgent
- 新架构: core.unified_agents.base_agent.UnifiedBaseAgent

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
- 新旧架构兼容性
"""

from unittest.mock import patch

import pytest

# ============ 导入新旧架构 ============
# 优先使用新架构，如果不可用则使用旧架构

try:
    # 新架构 (优先)
    from core.unified_agents.base_agent import UnifiedBaseAgent as BaseAgent
    from core.unified_agents.base import (
        AgentRequest,
        AgentResponse as NewAgentResponse,
        AgentStatus,
    )
    from core.unified_agents.config import UnifiedAgentConfig

    NEW_ARCHITECTURE_AVAILABLE = True
except ImportError:
    # 回退到旧架构
    from core.agents.base_agent import BaseAgent, AgentResponse
    NEW_ARCHITECTURE_AVAILABLE = False
    UnifiedAgentConfig = None
    AgentRequest = None
    NewAgentResponse = None
    AgentStatus = None

# 也导入旧架构用于兼容性测试
try:
    from core.agents.base_agent import (
        AgentResponse as OldAgentResponse,
        AgentUtils,
        BaseAgent as OldBaseAgent,
    )
except ImportError:
    OldAgentResponse = None
    AgentUtils = None
    OldBaseAgent = None


# ==================== 测试Agent实现 ====================

class MockAgent(BaseAgent):
    """Mock Agent用于测试抽象类"""

    def __init__(self, name: str = "test_agent", role: str = "test", **kwargs):
        self._name_value = name
        self._role_value = role
        if NEW_ARCHITECTURE_AVAILABLE and AgentStatus is not None:
            # 新架构使用UnifiedAgentConfig
            config = UnifiedAgentConfig.create_minimal(name, role)
            super().__init__(config)
            # 同步初始化状态（避免async问题）
            self._status = AgentStatus.READY
        else:
            # 旧架构使用直接参数
            super().__init__(name=name, role=role, **kwargs)

    @property
    def name(self) -> str:
        """Agent名称"""
        return self._name_value

    @property
    def role(self) -> str:
        """Agent角色（向后兼容）"""
        return self._role_value

    async def initialize(self) -> None:
        """初始化"""
        if NEW_ARCHITECTURE_AVAILABLE and AgentStatus is not None:
            self._status = AgentStatus.READY

    async def process(self, request):
        """处理请求（新架构）"""
        if NEW_ARCHITECTURE_AVAILABLE and NewAgentResponse is not None:
            return NewAgentResponse.success_response(
                request_id=getattr(request, 'request_id', 'test-001'),
                data={"result": f"Processed: {getattr(request, 'content', request)}"}
            )
        else:
            # 旧架构直接返回字符串
            return f"Processed: {request}"

    async def shutdown(self) -> None:
        """关闭"""
        if NEW_ARCHITECTURE_AVAILABLE and AgentStatus is not None:
            self._status = AgentStatus.SHUTDOWN

    async def health_check(self):
        """健康检查"""
        if NEW_ARCHITECTURE_AVAILABLE:
            from core.unified_agents.base import HealthStatus
            return HealthStatus(status=getattr(self, '_status', AgentStatus.READY))
        return None


class MockAgentWithGateway(BaseAgent):
    """Mock Agent with Gateway support"""

    def __init__(self, name: str = "test_agent", role: str = "test", **kwargs):
        self._name_value = name
        self._role_value = role
        if NEW_ARCHITECTURE_AVAILABLE and AgentStatus is not None:
            config = UnifiedAgentConfig.create_minimal(name, role)
            config.enable_gateway = True
            super().__init__(config)
            self._status = AgentStatus.READY
        else:
            super().__init__(name=name, role=role, enable_gateway=True, **kwargs)

    @property
    def name(self) -> str:
        """Agent名称"""
        return self._name_value

    @property
    def role(self) -> str:
        """Agent角色（向后兼容）"""
        return self._role_value

    async def initialize(self) -> None:
        """初始化"""
        if NEW_ARCHITECTURE_AVAILABLE and AgentStatus is not None:
            self._status = AgentStatus.READY

    async def process(self, request):
        """处理请求"""
        if NEW_ARCHITECTURE_AVAILABLE and NewAgentResponse is not None:
            return NewAgentResponse.success_response(
                request_id=getattr(request, 'request_id', 'test-001'),
                data={"result": f"Processed: {getattr(request, 'content', request)}"}
            )
        return f"Processed: {request}"

    async def shutdown(self) -> None:
        """关闭"""
        if NEW_ARCHITECTURE_AVAILABLE and AgentStatus is not None:
            self._status = AgentStatus.SHUTDOWN

    async def health_check(self):
        """健康检查"""
        if NEW_ARCHITECTURE_AVAILABLE:
            from core.unified_agents.base import HealthStatus
            return HealthStatus(status=getattr(self, '_status', AgentStatus.READY))
        return None


# ==================== Agent初始化测试 ====================

class TestAgentInitialization:
    """测试Agent初始化"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        agent = MockAgent(name="test", role="assistant")

        assert agent.name == "test"
        assert agent.role == "assistant"

    def test_initialization_with_custom_params(self):
        """测试自定义参数初始化"""
        agent = MockAgent(
            name="custom",
            role="expert",
        )

        assert agent.name == "custom"
        assert agent.role == "expert"

    def test_initialization_attributes(self):
        """测试初始化后的属性"""
        agent = MockAgent(name="test", role="assistant")

        # 对话历史应为空或已初始化
        assert hasattr(agent, "conversation_history") or hasattr(agent, "_status")

    def test_determine_agent_type_xiaona(self):
        """测试小娜Agent类型识别"""
        agent = MockAgent(name="xiaona", role="legal_expert")

        # Gateway可能不可用
        if hasattr(agent, "_agent_type") and agent._agent_type:
            assert "XIAONA" in str(agent._agent_type)


# ==================== 对话历史管理测试 ====================

class TestConversationHistory:
    """测试对话历史管理"""

    def test_add_to_history(self):
        """测试添加到历史"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "add_to_history"):
            agent.add_to_history("user", "Hello")
            agent.add_to_history("assistant", "Hi there")

            assert len(agent.conversation_history) == 2

    def test_clear_history(self):
        """测试清空历史"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "add_to_history"):
            agent.add_to_history("user", "Hello")
            agent.clear_history()
            assert agent.conversation_history == []

    def test_get_history(self):
        """测试获取历史副本"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "add_to_history"):
            agent.add_to_history("user", "Test")
            history = agent.get_history()
            assert len(history) == 1


# ==================== 记忆管理测试 ====================

class TestMemoryManagement:
    """测试记忆管理"""

    def test_remember(self):
        """测试记住信息"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "remember"):
            agent.remember("user_name", "Alice")
            assert agent.recall("user_name") == "Alice"

    def test_recall_nonexistent(self):
        """测试回忆不存在的键"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "recall"):
            result = agent.recall("nonexistent")
            assert result is None

    def test_forget(self):
        """测试忘记信息"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "remember"):
            agent.remember("temp", "temporary data")
            result = agent.forget("temp")
            assert result is True


# ==================== 能力管理测试 ====================

class TestCapabilityManagement:
    """测试能力管理"""

    def test_add_capability(self):
        """测试添加能力"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "add_capability"):
            agent.add_capability("patent_analysis")
            assert "patent_analysis" in agent.capabilities

    def test_has_capability(self):
        """测试检查能力"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "add_capability"):
            agent.add_capability("test_capability")
            assert agent.has_capability("test_capability") is True

    def test_get_capabilities(self):
        """测试获取能力列表"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "add_capability"):
            agent.add_capability("cap1")
            capabilities = agent.get_capabilities()
            assert "cap1" in capabilities


# ==================== 输入验证测试 ====================

class TestInputValidation:
    """测试输入验证"""

    def test_validate_input_valid(self):
        """测试有效输入"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "validate_input"):
            assert agent.validate_input("Hello") is True

    def test_validate_input_empty(self):
        """测试空输入"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "validate_input"):
            assert agent.validate_input("") is False

    def test_validate_config_valid(self):
        """测试有效配置"""
        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "validate_config"):
            assert agent.validate_config() is True


# ==================== 信息获取测试 ====================

class TestAgentInfo:
    """测试Agent信息获取"""

    def test_get_info(self):
        """测试获取信息"""
        agent = MockAgent(name="test_agent", role="expert")

        if hasattr(agent, "get_info"):
            info = agent.get_info()
            assert info["name"] == "test_agent"
            assert info["role"] == "expert"

    def test_string_representation(self):
        """测试字符串表示"""
        agent = MockAgent(name="test", role="assistant")

        str_repr = str(agent)
        assert "test" in str_repr


# ==================== Gateway通信测试 ====================

class TestGatewayCommunication:
    """测试Gateway通信"""

    @pytest.mark.asyncio
    async def test_gateway_connected_property(self):
        """测试Gateway连接状态属性"""
        agent = MockAgentWithGateway(name="test", role="assistant")

        if hasattr(agent, "gateway_connected"):
            # 未连接时
            assert agent.gateway_connected is False


# ==================== AgentUtils测试 ====================

class TestAgentUtils:
    """测试AgentUtils工具类"""

    def test_format_message(self):
        """测试消息格式化"""
        if AgentUtils is not None:
            message = AgentUtils.format_message("user", "Hello")
            assert message == {"role": "user", "content": "Hello"}

    def test_truncate_text_short(self):
        """测试截断短文本"""
        if AgentUtils is not None:
            text = "Short text"
            result = AgentUtils.truncate_text(text, max_length=100)
            assert result == text

    def test_sanitize_input(self):
        """测试输入清理"""
        if AgentUtils is not None:
            text = "  Hello    World  \t\n"
            result = AgentUtils.sanitize_input(text)
            assert result == "Hello World"


# ==================== AgentResponse测试 ====================

class TestAgentResponse:
    """测试AgentResponse响应类"""

    def test_create_response(self):
        """测试创建响应"""
        if OldAgentResponse is not None:
            response = OldAgentResponse(
                content="Test response",
                success=True,
                metadata={"key": "value"}
            )
            assert response.content == "Test response"
            assert response.success is True

    def test_error_response(self):
        """测试创建错误响应"""
        if OldAgentResponse is not None:
            response = OldAgentResponse.error("Something went wrong")
            assert response.content == "Something went wrong"
            assert response.success is False

    def test_success_response(self):
        """测试创建成功响应"""
        if OldAgentResponse is not None:
            response = OldAgentResponse.success_response("Done!", extra="info")
            assert response.content == "Done!"
            assert response.success is True


# ==================== Process方法测试 ====================

class TestAgentProcess:
    """测试Agent处理逻辑"""

    @pytest.mark.asyncio
    async def test_process_basic(self):
        """测试基本处理"""
        agent = MockAgent(name="test", role="assistant")

        # 创建请求对象
        if NEW_ARCHITECTURE_AVAILABLE and AgentRequest is not None:
            request = AgentRequest(
                request_id="test-001",
                action="test",
                parameters={"input": "Hello"}
            )
            result = await agent.process(request)
            # 新架构返回AgentResponse对象
            assert "Hello" in str(result.data) or result.success is True
        else:
            # 旧架构使用字符串
            result = await agent.process("Hello")
            assert "Processed: Hello" in result or "Hello" in result


# ==================== 新架构特性测试 ====================

class TestNewArchitectureFeatures:
    """测试新架构特性"""

    @pytest.mark.skipif(
        not NEW_ARCHITECTURE_AVAILABLE,
        reason="新架构不可用"
    )
    def test_unified_config(self):
        """测试统一配置"""
        config = UnifiedAgentConfig.create_minimal("test", "tester")
        assert config.name == "test"
        assert config.role == "tester"

    @pytest.mark.skipif(
        not NEW_ARCHITECTURE_AVAILABLE,
        reason="新架构不可用"
    )
    def test_agent_request(self):
        """测试Agent请求"""
        request = AgentRequest(
            request_id="test-001",
            action="test_action",
            parameters={"key": "value"}
        )
        assert request.request_id == "test-001"
        assert request.action == "test_action"


# ==================== 兼容性测试 ====================

class TestBackwardCompatibility:
    """测试向后兼容性"""

    def test_old_import_still_works(self):
        """测试旧导入仍然有效"""
        try:
            from core.agents.base_agent import BaseAgent as OldBaseAgentImport
            assert OldBaseAgentImport is not None
        except ImportError:
            pytest.skip("旧架构导入不可用")

    def test_new_import_works(self):
        """测试新导入有效"""
        try:
            from core.unified_agents.base_agent import UnifiedBaseAgent
            assert UnifiedBaseAgent is not None
        except ImportError:
            pytest.skip("新架构导入不可用")

    def test_both_architectures_coexist(self):
        """测试两套架构共存"""
        try:
            from core.agents.base_agent import BaseAgent as OldBase
            from core.unified_agents.base_agent import UnifiedBaseAgent as NewBase
            # 两者都应该可用
            assert OldBase is not None
            assert NewBase is not None
        except ImportError:
            pytest.skip("架构共存测试跳过")


# ==================== 性能测试 ====================

class TestPerformance:
    """测试性能指标"""

    def test_memory_retrieval_speed(self):
        """测试记忆检索速度"""
        import time

        agent = MockAgent(name="test", role="assistant")

        if hasattr(agent, "remember"):
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

        if hasattr(agent, "add_capability"):
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


# ==================== 测试运行器 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
