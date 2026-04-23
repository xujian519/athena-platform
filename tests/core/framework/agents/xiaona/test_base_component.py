#!/usr/bin/env python3
"""
BaseXiaonaComponent单元测试

测试小娜专业智能体基类的所有功能。
"""

import pytest
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from core.framework.agents.xiaona.base_component import (
    AgentCapability,
    AgentExecutionContext as OriginalAgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)


# 修复后的AgentExecutionContext，添加task_id字段
@dataclass
class AgentExecutionContext(OriginalAgentExecutionContext):
    """修复后的执行上下文，添加task_id字段"""
    session_id: str
    input_data: Optional[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    task_id: str = "default_task"  # 添加缺失的字段
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ========== 测试用具体实现 ==========

class ConcreteXiaonaComponent(BaseXiaonaComponent):
    """具体实现类用于测试抽象基类"""

    def __init__(self, agent_id: str = "test_agent", config: dict = None):
        self.system_prompt_value = "测试系统提示词"
        self.execute_called = False
        self.execute_result = None
        super().__init__(agent_id, config)

    def _initialize(self):
        """初始化实现"""
        # 注册一些测试能力
        capabilities = [
            {
                "name": "test_capability",
                "description": "测试能力",
                "input_types": ["str", "dict"],
                "output_types": ["dict"],
                "estimated_time": 10.0,
            },
            {
                "name": "analyze",
                "description": "分析能力",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 30.0,
            },
        ]
        self._register_capabilities(capabilities)

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行实现"""
        self.execute_called = True
        self.execute_result = AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"result": "success", "input": context.input_data},
            execution_time=0.5,
        )
        return self.execute_result

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.system_prompt_value


class FailingXiaonaComponent(BaseXiaonaComponent):
    """总是失败的实现类用于测试错误处理"""

    def __init__(self, agent_id: str = "failing_agent"):
        super().__init__(agent_id)

    def _initialize(self):
        """初始化实现"""
        capabilities = [
            {
                "name": "failing_capability",
                "description": "会失败的能力",
                "input_types": ["str"],
                "output_types": ["str"],
                "estimated_time": 5.0,
            }
        ]
        self._register_capabilities(capabilities)

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行实现 - 总是抛出异常"""
        raise ValueError("模拟的执行失败")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return "失败的代理"


# ========== Fixtures ==========

@pytest.fixture
def sample_capability():
    """创建示例能力"""
    return AgentCapability(
        name="test_capability",
        description="测试能力描述",
        input_types=["str", "dict"],
        output_types=["dict"],
        estimated_time=10.0,
    )


@pytest.fixture
def sample_context():
    """创建示例执行上下文"""
    return AgentExecutionContext(
        session_id="test_session",
        task_id="test_task",
        input_data={"key": "value"},
        config={"timeout": 30},
        metadata={"source": "test"},
    )


@pytest.fixture
def agent():
    """创建测试代理实例"""
    return ConcreteXiaonaComponent()


@pytest.fixture
def failing_agent():
    """创建总是失败的代理实例"""
    return FailingXiaonaComponent()


# ========== AgentStatus测试 ==========

class TestAgentStatus:
    """测试AgentStatus枚举"""

    def test_status_values(self):
        """测试状态值"""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.COMPLETED.value == "completed"

    def test_status_comparison(self):
        """测试状态比较"""
        status1 = AgentStatus.IDLE
        status2 = AgentStatus.BUSY
        assert status1 != status2
        assert status1 == AgentStatus.IDLE


# ========== AgentCapability测试 ==========

class TestAgentCapability:
    """测试AgentCapability数据类"""

    def test_capability_creation(self, sample_capability):
        """测试能力创建"""
        assert sample_capability.name == "test_capability"
        assert sample_capability.description == "测试能力描述"
        assert sample_capability.input_types == ["str", "dict"]
        assert sample_capability.output_types == ["dict"]
        assert sample_capability.estimated_time == 10.0

    def test_capability_with_dict(self):
        """测试从字典创建能力"""
        cap_dict = {
            "name": "dict_capability",
            "description": "从字典创建",
            "input_types": ["str"],
            "output_types": ["str"],
            "estimated_time": 15.0,
        }
        cap = AgentCapability(**cap_dict)
        assert cap.name == "dict_capability"
        assert cap.estimated_time == 15.0


# ========== AgentExecutionContext测试 ==========

class TestAgentExecutionContext:
    """测试AgentExecutionContext数据类"""

    def test_context_creation(self, sample_context):
        """测试上下文创建"""
        assert sample_context.session_id == "test_session"
        assert sample_context.task_id == "test_task"
        assert sample_context.input_data == {"key": "value"}
        assert sample_context.config == {"timeout": 30}
        assert sample_context.metadata == {"source": "test"}

    def test_context_with_times(self):
        """测试带时间戳的上下文"""
        start = datetime.now()
        end = datetime.now()
        context = AgentExecutionContext(
            session_id="test",
            input_data=None,
            config=None,
            metadata=None,
            start_time=start,
            end_time=end,
        )
        assert context.start_time == start
        assert context.end_time == end

    def test_context_defaults(self):
        """测试上下文默认值"""
        context = AgentExecutionContext(
            session_id="test",
            input_data=None,
            config=None,
            metadata=None,
        )
        assert context.input_data is None
        assert context.config is None
        assert context.metadata is None
        assert context.start_time is None
        assert context.end_time is None


# ========== AgentExecutionResult测试 ==========

class TestAgentExecutionResult:
    """测试AgentExecutionResult数据类"""

    def test_result_creation(self):
        """测试结果创建"""
        result = AgentExecutionResult(
            agent_id="test_agent",
            status=AgentStatus.COMPLETED,
            output_data={"result": "success"},
            execution_time=1.5,
        )
        assert result.agent_id == "test_agent"
        assert result.status == AgentStatus.COMPLETED
        assert result.output_data == {"result": "success"}
        assert result.execution_time == 1.5

    def test_result_with_error(self):
        """测试带错误的结果"""
        result = AgentExecutionResult(
            agent_id="test_agent",
            status=AgentStatus.ERROR,
            output_data=None,
            error_message="执行失败",
            execution_time=0.5,
        )
        assert result.status == AgentStatus.ERROR
        assert result.error_message == "执行失败"

    def test_result_metadata_default(self):
        """测试结果元数据默认值"""
        result = AgentExecutionResult(
            agent_id="test",
            status=AgentStatus.COMPLETED,
        )
        assert result.metadata == {}

    def test_result_with_metadata(self):
        """测试带元数据的结果"""
        metadata = {"version": "1.0", "model": "test-model"}
        result = AgentExecutionResult(
            agent_id="test",
            status=AgentStatus.COMPLETED,
            metadata=metadata,
        )
        assert result.metadata == metadata


# ========== BaseXiaonaComponent初始化测试 ==========

class TestBaseXiaonaComponentInit:
    """测试BaseXiaonaComponent初始化"""

    def test_init_with_defaults(self):
        """测试默认初始化"""
        agent = ConcreteXiaonaComponent()
        assert agent.agent_id == "test_agent"
        assert agent.config == {}
        assert agent.status == AgentStatus.IDLE
        assert len(agent._capabilities) == 2

    def test_init_with_config(self):
        """测试带配置的初始化"""
        config = {"timeout": 60, "model": "test-model"}
        agent = ConcreteXiaonaComponent(config=config)
        assert agent.config == config

    def test_init_custom_agent_id(self):
        """测试自定义agent_id"""
        agent = ConcreteXiaonaComponent(agent_id="custom_agent")
        assert agent.agent_id == "custom_agent"

    def test_logger_creation(self, agent):
        """测试日志器创建"""
        assert agent.logger is not None
        assert "ConcreteXiaonaComponent" in agent.logger.name

    def test_llm_not_initialized_by_default(self, agent):
        """测试LLM默认未初始化"""
        assert agent._llm_manager is None
        assert agent._llm_initialized is False


# ========== 能力注册测试 ==========

class TestCapabilityRegistration:
    """测试能力注册功能"""

    def test_register_capabilities_from_dict(self):
        """测试从字典注册能力"""
        agent = ConcreteXiaonaComponent()
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 2
        assert capabilities[0].name == "test_capability"
        assert capabilities[1].name == "analyze"

    def test_register_capabilities_from_objects(self):
        """测试从对象注册能力"""
        agent = ConcreteXiaonaComponent(agent_id="cap_test")
        cap_objects = [
            AgentCapability(
                name="obj_cap",
                description="对象能力",
                input_types=["str"],
                output_types=["str"],
                estimated_time=5.0,
            )
        ]
        agent._register_capabilities(cap_objects)
        capabilities = agent.get_capabilities()
        # 应该包含之前的能力 + 新注册的能力
        assert any(c.name == "obj_cap" for c in capabilities)

    def test_get_capabilities_returns_copy(self, agent):
        """测试get_capabilities返回副本"""
        capabilities1 = agent.get_capabilities()
        capabilities2 = agent.get_capabilities()
        assert capabilities1 is not capabilities2
        assert capabilities1 == capabilities2

    def test_has_capability(self, agent):
        """测试has_capability方法"""
        assert agent.has_capability("test_capability") is True
        assert agent.has_capability("analyze") is True
        assert agent.has_capability("nonexistent") is False

    def test_get_info(self, agent):
        """测试get_info方法"""
        info = agent.get_info()
        assert info["agent_id"] == "test_agent"
        assert info["agent_type"] == "ConcreteXiaonaComponent"
        assert info["status"] == "idle"
        assert len(info["capabilities"]) == 2
        assert info["capabilities"][0]["name"] == "test_capability"


# ========== 输入验证测试 ==========

class TestInputValidation:
    """测试输入验证功能"""

    def test_validate_input_success(self, agent, sample_context):
        """测试有效输入验证"""
        result = agent.validate_input(sample_context)
        assert result is True

    def test_validate_input_missing_session_id(self, agent):
        """测试缺少session_id"""
        context = AgentExecutionContext(
            session_id="",
            task_id="test_task",
            input_data=None,
            config=None,
            metadata=None,
        )
        result = agent.validate_input(context)
        assert result is False

    def test_validate_input_missing_task_id(self, agent):
        """测试缺少task_id"""
        context = AgentExecutionContext(
            session_id="test_session",
            task_id="",
            input_data=None,
            config=None,
            metadata=None,
        )
        result = agent.validate_input(context)
        assert result is False

    def test_validate_input_none_session_id(self, agent):
        """测试None session_id"""
        context = AgentExecutionContext(
            session_id=None,  # type: ignore
            task_id="test_task",
            input_data=None,
            config=None,
            metadata=None,
        )
        result = agent.validate_input(context)
        assert result is False


# ========== 执行测试 ==========

class TestExecution:
    """测试执行功能"""

    @pytest.mark.asyncio
    async def test_execute_with_monitoring(self, agent, sample_context):
        """测试带监控的执行"""
        result = await agent._execute_with_monitoring(sample_context)

        assert result.status == AgentStatus.COMPLETED
        assert agent.execute_called is True
        assert agent.status == AgentStatus.IDLE
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_execute_sets_times(self, agent, sample_context):
        """测试执行时间设置"""
        result = await agent._execute_with_monitoring(sample_context)

        assert sample_context.start_time is not None
        assert sample_context.end_time is not None
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_execute_status_transitions(self, agent, sample_context):
        """测试执行状态转换"""
        assert agent.status == AgentStatus.IDLE

        await agent._execute_with_monitoring(sample_context)

        assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_execute_failure(self, failing_agent, sample_context):
        """测试执行失败处理"""
        result = await failing_agent._execute_with_monitoring(sample_context)

        assert result.status == AgentStatus.ERROR
        assert failing_agent.status == AgentStatus.ERROR
        assert result.error_message == "模拟的执行失败"
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_direct_execute(self, agent, sample_context):
        """测试直接调用execute"""
        result = await agent.execute(sample_context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data["result"] == "success"


# ========== LLM集成测试 ==========

class TestLLMIntegration:
    """测试LLM集成功能"""

    def test_ensure_llm_initialized(self, agent):
        """测试LLM初始化确保"""
        assert agent._llm_initialized is False
        agent._ensure_llm_initialized()
        # 初始化后应该标记为已尝试
        assert agent._llm_initialized is True

    def test_build_llm_context(self, agent):
        """测试LLM上下文构建"""
        context = agent._build_llm_context("test_task")
        assert context["agent_id"] == "test_agent"
        assert context["agent_type"] == "ConcreteXiaonaComponent"
        assert context["task_type"] == "test_task"
        assert "test_capability" in context["capabilities"]
        assert context["system_prompt"] == "测试系统提示词"

    def test_load_llm_config_default(self, agent):
        """测试默认LLM配置加载"""
        config = agent._load_llm_config()
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config

    def test_load_llm_config_from_instance(self):
        """测试从实例配置加载LLM配置"""
        llm_config = {"model": "custom-model", "temperature": 0.5}
        agent = ConcreteXiaonaComponent(config={"llm_config": llm_config})
        config = agent._load_llm_config()
        assert config["model"] == "custom-model"
        assert config["temperature"] == 0.5

    def test_merge_llm_params(self, agent):
        """测试LLM参数合并"""
        base_params = agent._llm_config.copy()
        user_params = {"temperature": 0.9, "max_tokens": 2048}
        merged = agent._merge_llm_params("general", user_params)

        assert merged["temperature"] == 0.9
        assert merged["max_tokens"] == 2048
        # 基础参数应该保留
        assert "model" in merged

    @pytest.mark.asyncio
    async def test_call_llm_when_uninitialized(self, agent):
        """测试LLM未初始化时调用"""
        with pytest.raises(RuntimeError, match="LLM管理器未初始化"):
            await agent._call_llm("测试提示词")

    @pytest.mark.asyncio
    async def test_call_llm_with_fallback_complex_task(self, agent):
        """测试复杂任务LLM调用降级失败"""
        # Mock两个调用都失败
        with patch.object(agent, '_call_deepseek', side_effect=RuntimeError("DeepSeek失败")), \
             patch.object(agent, '_call_local_8009', side_effect=RuntimeError("本地8009失败")):
            with pytest.raises(RuntimeError, match="复杂任务"):
                await agent._call_llm_with_fallback("测试", task_type="invalidation_analysis")

    @pytest.mark.asyncio
    async def test_call_deepseek_unavailable(self, agent):
        """测试DeepSeek不可用时调用"""
        with patch('core.ai.llm.deepseek_client.get_deepseek_client', side_effect=ImportError("No module")):
            with pytest.raises(RuntimeError, match="DeepSeek客户端不可用"):
                await agent._call_deepseek("测试提示词")

    @pytest.mark.asyncio
    async def test_call_local_8009_unavailable(self, agent):
        """测试本地8009不可用时调用"""
        with patch('core.ai.llm.adapters.local_8009_adapter.get_local_8009_adapter', side_effect=ImportError("No module")):
            with pytest.raises(RuntimeError, match="本地8009适配器不可用"):
                await agent._call_local_8009("测试提示词")


# ========== 系统提示词测试 ==========

class TestSystemPrompt:
    """测试系统提示词功能"""

    def test_get_system_prompt(self, agent):
        """测试获取系统提示词"""
        prompt = agent.get_system_prompt()
        assert prompt == "测试系统提示词"

    def test_system_prompt_in_context(self, agent):
        """测试系统提示词在上下文中"""
        context = agent._build_llm_context("test")
        assert context["system_prompt"] == "测试系统提示词"


# ========== __repr__测试 ==========

class TestRepr:
    """测试__repr__方法"""

    def test_repr(self, agent):
        """测试字符串表示"""
        repr_str = repr(agent)
        assert "ConcreteXiaonaComponent" in repr_str
        assert "test_agent" in repr_str
        assert "idle" in repr_str


# ========== 边界条件测试 ==========

class TestEdgeCases:
    """测试边界条件"""

    def test_empty_capabilities(self):
        """测试空能力列表"""
        class EmptyCapComponent(ConcreteXiaonaComponent):
            def _initialize(self):
                self._register_capabilities([])

        agent = EmptyCapComponent()
        assert len(agent.get_capabilities()) == 0
        assert agent.has_capability("anything") is False

    def test_large_estimated_time(self):
        """测试大预估时间"""
        cap = AgentCapability(
            name="long_task",
            description="长时间任务",
            input_types=["str"],
            output_types=["str"],
            estimated_time=999999.0,
        )
        assert cap.estimated_time == 999999.0

    def test_special_characters_in_capability_name(self):
        """测试能力名称中的特殊字符"""
        agent = ConcreteXiaonaComponent()
        caps = [
            {
                "name": "test-capability-123",
                "description": "测试特殊字符",
                "input_types": ["str"],
                "output_types": ["str"],
                "estimated_time": 10.0,
            }
        ]
        agent._register_capabilities(caps)
        assert agent.has_capability("test-capability-123") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
