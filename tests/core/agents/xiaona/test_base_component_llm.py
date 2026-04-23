"""
基类组件LLM集成测试

测试范围:
- LLM管理器初始化
- _call_llm() 方法调用
- 降级机制测试
- 配置加载测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentStatus,
    AgentExecutionContext,
    AgentExecutionResult
)


class TestableBaseComponentWithLLM(BaseXiaonaComponent):
    """可测试的带LLM的基类组件"""

    def _initialize(self) -> None:
        """初始化测试组件"""
        self._register_capabilities([
            AgentCapability(
                name="test_capability",
                description="测试能力",
                input_types=["test_input"],
                output_types=["test_output"],
                estimated_time=1.0
            )
        ])

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行测试任务"""
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return "测试系统提示词"


class TestBaseComponentLLMIntegration:
    """基类组件LLM集成测试"""

    @pytest.fixture
    def component(self):
        """创建组件实例"""
        return TestableBaseComponentWithLLM(agent_id="test_component_llm")

    @pytest.fixture
    def mock_llm_manager(self):
        """创建模拟LLM管理器"""
        manager = Mock()
        manager.generate_async = AsyncMock(return_value=Mock(content="这是LLM生成的响应"))
        return manager

    # ========== LLM管理器初始化测试 ==========

    def test_ensure_llm_initialized_success(self, component, mock_llm_manager):
        """测试LLM管理器初始化成功"""
        # 创建一个同步的mock函数
        def sync_get_manager():
            return mock_llm_manager

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            # 第一次调用应该初始化
            component._ensure_llm_initialized()
            assert component._llm_initialized is True
            assert component._llm_manager == mock_llm_manager

            # 第二次调用不应该重复初始化
            component._ensure_llm_initialized()

    def test_ensure_llm_initialized_unavailable(self, component):
        """测试LLM模块不可用的情况"""
        with patch('core.agents.xiaona.base_component.LLM_AVAILABLE', False):
            component._ensure_llm_initialized()
            # 应该标记为已初始化（避免重复尝试）
            assert component._llm_initialized is True
            assert component._llm_manager is None

    def test_ensure_llm_initialization_failure(self, component):
        """测试LLM管理器初始化失败"""
        def failing_get_manager():
            raise Exception("初始化失败")

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', failing_get_manager):
            component._ensure_llm_initialized()
            # 应该标记为已初始化（避免重复尝试）
            assert component._llm_initialized is True
            assert component._llm_manager is None

    # ========== _call_llm() 方法测试 ==========

    @pytest.mark.asyncio
    async def test_call_llm_success(self, component, mock_llm_manager):
        """测试LLM调用成功"""
        def sync_get_manager():
            return mock_llm_manager

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            result = await component._call_llm("测试提示词", task_type="general")
            assert result == "这是LLM生成的响应"
            mock_llm_manager.generate_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_llm_not_initialized(self, component):
        """测试LLM管理器未初始化"""
        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', lambda: None):
            with pytest.raises(RuntimeError, match="LLM管理器未初始化"):
                await component._call_llm("测试提示词")

    # ========== 降级机制测试 ==========

    @pytest.mark.asyncio
    async def test_call_llm_with_fallback_success(self, component, mock_llm_manager):
        """测试降级机制成功"""
        def sync_get_manager():
            return mock_llm_manager

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            result = await component._call_llm_with_fallback(
                "主要提示词",
                task_type="general",
                fallback_prompt="降级提示词"
            )
            assert result == "这是LLM生成的响应"

    @pytest.mark.asyncio
    async def test_call_llm_with_fallback_trigger(self, component, mock_llm_manager):
        """测试降级机制被触发"""
        # 第一次调用失败，第二次调用成功
        mock_llm_manager.generate_async.side_effect = [
            Exception("主要调用失败"),
            Mock(content="这是LLM生成的响应")
        ]

        def sync_get_manager():
            return mock_llm_manager

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            result = await component._call_llm_with_fallback(
                "主要提示词",
                task_type="general",
                fallback_prompt="降级提示词"
            )
            assert result == "这是LLM生成的响应"
            assert mock_llm_manager.generate_async.call_count == 2

    @pytest.mark.asyncio
    async def test_call_llm_with_fallback_both_fail(self, component, mock_llm_manager):
        """测试降级机制也失败"""
        mock_llm_manager.generate_async.side_effect = Exception("LLM调用失败")

        def sync_get_manager():
            return mock_llm_manager

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            with pytest.raises(Exception, match="LLM调用失败"):
                await component._call_llm_with_fallback(
                    "主要提示词",
                    task_type="general",
                    fallback_prompt="降级提示词"
                )

    # ========== 配置加载测试 ==========

    def test_load_llm_config_from_instance(self, component):
        """测试从实例配置加载LLM配置"""
        component.config = {
            "llm_config": {
                "model": "custom-model",
                "temperature": 0.8
            }
        }

        config = component._load_llm_config()
        assert config["model"] == "custom-model"
        assert config["temperature"] == 0.8

    def test_load_llm_config_default(self, component):
        """测试使用默认LLM配置"""
        config = component._load_llm_config()
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config
        assert config["model"] == "claude-3-5-sonnet-20241022"

    # ========== 参数合并测试 ==========

    def test_merge_llm_params(self, component):
        """测试LLM参数合并"""
        # 先初始化LLM配置
        component._llm_config = {
            "model": "base-model",
            "temperature": 0.5,
            "max_tokens": 4096
        }

        merged = component._merge_llm_params("general", {"temperature": 0.9})

        # 基础配置应该保留（但可能被任务类型配置覆盖）
        assert "model" in merged
        assert "max_tokens" in merged

        # 用户参数应该覆盖
        assert merged["temperature"] == 0.9

    # ========== 上下文构建测试 ==========

    def test_build_llm_context(self, component):
        """测试LLM上下文构建"""
        context = component._build_llm_context("patent_analysis")

        assert context["agent_id"] == component.agent_id
        assert context["agent_type"] == "TestableBaseComponentWithLLM"
        assert context["task_type"] == "patent_analysis"
        assert "capabilities" in context
        assert "system_prompt" in context
        assert context["system_prompt"] == "测试系统提示词"

    # ========== 向后兼容性测试 ==========

    def test_backward_compatibility_no_llm(self):
        """测试不使用LLM的组件仍然可以工作"""
        class OldStyleComponent(BaseXiaonaComponent):
            def _initialize(self) -> None:
                pass

            async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.COMPLETED,
                    output_data={},
                    execution_time=0.0
                )

            def get_system_prompt(self) -> str:
                return "旧式组件"

        # 应该能够正常创建
        component = OldStyleComponent(agent_id="old_component")
        assert component.agent_id == "old_component"
        assert component.status == AgentStatus.IDLE

    # ========== 错误处理测试 ==========

    @pytest.mark.asyncio
    async def test_call_llm_handles_exceptions(self, component, mock_llm_manager):
        """测试LLM调用异常处理"""
        mock_llm_manager.generate_async.side_effect = RuntimeError("LLM服务不可用")

        def sync_get_manager():
            return mock_llm_manager

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            with pytest.raises(RuntimeError):  # 不限制错误消息，只要是RuntimeError即可
                await component._call_llm("测试提示词")

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_llm_workflow(self, component, mock_llm_manager):
        """测试完整的LLM工作流程"""
        def sync_get_manager():
            return mock_llm_manager

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            # 1. 初始化LLM
            component._ensure_llm_initialized()
            assert component._llm_initialized is True

            # 2. 加载配置
            config = component._load_llm_config()
            assert config is not None

            # 3. 调用LLM
            result = await component._call_llm("分析专利创造性", task_type="patent_analysis")
            assert result == "这是LLM生成的响应"

            # 4. 降级调用
            result2 = await component._call_llm_with_fallback(
                "分析专利创造性",
                task_type="patent_analysis",
                fallback_prompt="简单分析专利"
            )
            assert result2 == "这是LLM生成的响应"

    # ========== 性能测试 ==========

    @pytest.mark.asyncio
    async def test_llm_initialization_performance(self, component):
        """测试LLM初始化性能"""
        import time

        def sync_get_manager():
            return Mock()

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            start_time = time.time()
            component._ensure_llm_initialized()
            elapsed_time = time.time() - start_time

            # 初始化应该很快
            assert elapsed_time < 0.1

    @pytest.mark.asyncio
    async def test_repeated_ensure_llm_initialized(self, component, mock_llm_manager):
        """测试重复初始化不会重复调用"""
        call_count = [0]

        def sync_get_manager():
            call_count[0] += 1
            return mock_llm_manager

        with patch('core.agents.xiaona.base_component.get_unified_llm_manager', sync_get_manager):
            # 多次调用
            for _ in range(5):
                component._ensure_llm_initialized()

            # 应该只初始化一次
            assert call_count[0] == 1
