#!/usr/bin/env python3
"""
UnifiedPatentWriter单元测试

测试统一专利撰写代理的所有功能。
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from core.framework.agents.xiaona.unified_patent_writer import (
    UnifiedPatentWriter,
    get_unified_patent_writer,
)
from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


# ========== Fixtures ==========

@pytest.fixture
def mock_llm_client():
    """Mock LLM客户端"""
    client = AsyncMock()
    client.generate = AsyncMock(return_value="模拟的LLM响应")
    return client


@pytest.fixture
def mock_drafting_module():
    """Mock专利撰写模块"""
    module = AsyncMock()
    module.analyze_disclosure = AsyncMock(return_value={"status": "success", "analysis": "分析结果"})
    module.assess_patentability = AsyncMock(return_value={"status": "success", "patentable": True})
    module.draft_specification = AsyncMock(return_value={"status": "success", "specification": "说明书内容"})
    module.draft_claims = AsyncMock(return_value={"status": "success", "claims": "权利要求书内容"})
    module.optimize_protection_scope = AsyncMock(return_value={"status": "success", "optimized": True})
    module.review_adequacy = AsyncMock(return_value={"status": "success", "adequate": True})
    module.detect_common_errors = AsyncMock(return_value={"status": "success", "errors": []})
    return module


@pytest.fixture
def mock_response_module():
    """Mock审查答复模块"""
    module = AsyncMock()
    module.draft_response = AsyncMock(return_value={"status": "success", "response": "答复内容"})
    module.draft_invalidation = AsyncMock(return_value={"status": "success", "invalidation": "无效宣告内容"})
    return module


@pytest.fixture
def mock_orchestration_module():
    """Mock任务编排模块"""
    module = AsyncMock()
    module.draft_full_application = AsyncMock(return_value={"status": "success", "application": "完整申请"})
    module.orchestrate_response = AsyncMock(return_value={"status": "success", "orchestrated": True})
    return module


@pytest.fixture
def mock_utility_module():
    """Mock通用工具模块"""
    module = Mock()
    module.format_document = Mock(return_value="格式化后的文档")
    module.calculate_quality_score = Mock(return_value=Mock(
        completeness=0.9,
        standardization=0.85,
        logic=0.88,
        overall=0.87
    ))
    return module


@pytest.fixture
def writer(mock_drafting_module, mock_response_module, mock_orchestration_module, mock_utility_module):
    """创建UnifiedPatentWriter实例并mock其子模块"""
    with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule', return_value=mock_drafting_module), \
         patch('core.framework.agents.xiaona.modules.response_module.ResponseModule', return_value=mock_response_module), \
         patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule', return_value=mock_orchestration_module), \
         patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule', return_value=mock_utility_module):
        writer = UnifiedPatentWriter()
        # 替换模块引用
        writer.drafting_module = mock_drafting_module
        writer.response_module = mock_response_module
        writer.orchestration_module = mock_orchestration_module
        writer.utility_module = mock_utility_module
        yield writer


@pytest.fixture
def sample_disclosure_data():
    """示例技术交底书数据"""
    return {
        "title": "测试发明",
        "technical_field": "测试技术领域",
        "background": "背景技术描述",
        "summary": "发明内容",
        "description": "具体实施方式",
    }


@pytest.fixture
def sample_context():
    """示例执行上下文"""
    return AgentExecutionContext(
        session_id="test_session",
        task_id="test_task",
        input_data={
            "task_type": "analyze_disclosure",
            "data": {"title": "测试发明"},
        },
        config={},
        metadata={},
    )


# ========== 初始化测试 ==========

class TestUnifiedPatentWriterInit:
    """测试UnifiedPatentWriter初始化"""

    def test_init_with_defaults(self):
        """测试默认初始化"""
        with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
             patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
             patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
             patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
            writer = UnifiedPatentWriter()
            assert writer.agent_id == "unified_patent_writer"
            assert writer.status == AgentStatus.IDLE

    def test_init_with_config(self):
        """测试带配置初始化"""
        config = {"timeout": 120}
        with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
             patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
             patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
             patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
            writer = UnifiedPatentWriter(config=config)
            assert writer.config == config

    def test_registers_all_capabilities(self):
        """测试注册所有能力"""
        with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
             patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
             patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
             patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
            writer = UnifiedPatentWriter()
            capabilities = writer.get_capabilities()
            # 应该有13个能力（7个撰写 + 2个答复 + 2个编排 + 2个工具）
            assert len(capabilities) == 13

    def test_capability_names(self):
        """测试能力名称"""
        with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
             patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
             patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
             patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
            writer = UnifiedPatentWriter()
            capability_names = [c.name for c in writer.get_capabilities()]

            # 验证关键能力存在
            assert "analyze_disclosure" in capability_names
            assert "draft_claims" in capability_names
            assert "draft_specification" in capability_names
            assert "draft_response" in capability_names
            assert "draft_invalidation" in capability_names
            assert "draft_full_application" in capability_names
            assert "format_document" in capability_names


# ========== 系统提示词测试 ==========

class TestSystemPrompt:
    """测试系统提示词"""

    def test_get_system_prompt(self, writer):
        """测试获取系统提示词"""
        prompt = writer.get_system_prompt()
        assert "小娜·撰写者" in prompt
        assert "专利文书撰写专家" in prompt
        assert "权利要求书撰写" in prompt
        assert "说明书撰写" in prompt
        assert "审查意见答复" in prompt


# ========== 执行测试 ==========

class TestExecute:
    """测试execute方法"""

    @pytest.mark.asyncio
    async def test_execute_success(self, writer, sample_context):
        """测试成功执行"""
        result = await writer.execute(sample_context)

        assert isinstance(result, AgentExecutionResult)
        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_execute_without_task_type(self, writer):
        """测试缺少task_type"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={},  # 缺少task_type
            config={},
            metadata={},
        )
        result = await writer.execute(context)

        assert result.status == AgentStatus.ERROR
        assert "缺少task_type参数" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_invalid_input(self, writer):
        """测试无效输入"""
        context = AgentExecutionContext(
            session_id="",  # 无效session_id
            task_id="test",
            input_data={"task_type": "test"},
            config={},
            metadata={},
        )
        result = await writer.execute(context)

        assert result.status == AgentStatus.ERROR
        assert "输入验证失败" in result.error_message


# ========== 路由测试 ==========

class TestRouting:
    """测试任务路由"""

    @pytest.mark.asyncio
    async def test_route_to_drafting_module_analyze_disclosure(self, writer, sample_disclosure_data):
        """测试路由到analyze_disclosure"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "analyze_disclosure",
                "data": sample_disclosure_data,
            },
            config={},
            metadata={},
        )

        result = await writer._route_to_module("analyze_disclosure", context)

        assert result["status"] == "success"
        assert "analysis" in result
        writer.drafting_module.analyze_disclosure.assert_called_once_with(sample_disclosure_data)

    @pytest.mark.asyncio
    async def test_route_to_drafting_module_draft_claims(self, writer, sample_disclosure_data):
        """测试路由到draft_claims"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "draft_claims",
                "data": sample_disclosure_data,
            },
            config={},
            metadata={},
        )

        result = await writer._route_to_module("draft_claims", context)

        assert result["status"] == "success"
        assert "claims" in result
        writer.drafting_module.draft_claims.assert_called_once_with(sample_disclosure_data)

    @pytest.mark.asyncio
    async def test_route_to_drafting_module_draft_specification(self, writer, sample_disclosure_data):
        """测试路由到draft_specification"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "draft_specification",
                "data": sample_disclosure_data,
            },
            config={},
            metadata={},
        )

        result = await writer._route_to_module("draft_specification", context)

        assert result["status"] == "success"
        assert "specification" in result
        writer.drafting_module.draft_specification.assert_called_once_with(sample_disclosure_data)

    @pytest.mark.asyncio
    async def test_route_to_response_module_draft_response(self, writer):
        """测试路由到draft_response"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "draft_response",
                "user_input": "审查意见内容",
                "previous_results": {},
                "model": "kimi-k2.5",
            },
            config={},
            metadata={},
        )

        result = await writer._route_to_module("draft_response", context)

        assert result["status"] == "success"
        assert "response" in result
        writer.response_module.draft_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_response_module_draft_invalidation(self, writer):
        """测试路由到draft_invalidation"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "draft_invalidation",
                "user_input": "无效宣告请求",
                "previous_results": {},
                "model": "kimi-k2.5",
            },
            config={},
            metadata={},
        )

        result = await writer._route_to_module("draft_invalidation", context)

        assert result["status"] == "success"
        assert "invalidation" in result
        writer.response_module.draft_invalidation.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_orchestration_module_draft_full_application(self, writer, sample_disclosure_data):
        """测试路由到draft_full_application"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "draft_full_application",
                "data": sample_disclosure_data,
                "progress_callback": None,
            },
            config={},
            metadata={},
        )

        result = await writer._route_to_module("draft_full_application", context)

        assert result["status"] == "success"
        assert "application" in result
        writer.orchestration_module.draft_full_application.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_utility_module_format_document(self, writer):
        """测试路由到format_document"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "format_document",
                "data": {
                    "document_type": "specification",
                    "content": "文档内容",
                },
            },
            config={},
            metadata={},
        )

        result = await writer._route_to_module("format_document", context)

        assert "formatted_document" in result
        writer.utility_module.format_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_utility_module_calculate_quality_score(self, writer):
        """测试路由到calculate_quality_score"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "calculate_quality_score",
                "data": {
                    "document_content": "文档内容",
                    "review_result": None,
                },
            },
            config={},
            metadata={},
        )

        result = await writer._route_to_module("calculate_quality_score", context)

        assert "quality_metrics" in result
        assert "completeness" in result["quality_metrics"]
        assert "standardization" in result["quality_metrics"]
        assert "logic" in result["quality_metrics"]
        assert "overall" in result["quality_metrics"]
        writer.utility_module.calculate_quality_score.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_invalid_task_type(self, writer):
        """测试无效任务类型"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "invalid_task",
                "data": {},
            },
            config={},
            metadata={},
        )

        with pytest.raises(ValueError, match="不支持的任务类型"):
            await writer._route_to_module("invalid_task", context)


# ========== 便捷方法测试 ==========

class TestConvenienceMethods:
    """测试便捷方法"""

    @pytest.mark.asyncio
    async def test_analyze_disclosure(self, writer, sample_disclosure_data):
        """测试analyze_disclosure便捷方法"""
        result = await writer.analyze_disclosure(sample_disclosure_data)

        assert result is not None
        assert "analysis" in result or "status" in result

    @pytest.mark.asyncio
    async def test_draft_full_application_convenience(self, writer, sample_disclosure_data):
        """测试draft_full_application便捷方法"""
        result = await writer.draft_full_application(sample_disclosure_data)

        assert result is not None
        assert "application" in result or "status" in result

    @pytest.mark.asyncio
    async def test_draft_office_action_response(self, writer):
        """测试draft_office_action_response便捷方法"""
        office_action = {"patent_number": "CN123456", "opinion": "缺乏创造性"}
        result = await writer.draft_office_action_response(office_action)

        assert result is not None
        assert "response" in result or "status" in result


# ========== 工厂函数测试 ==========

class TestFactoryFunctions:
    """测试工厂函数"""

    def test_create_unified_patent_writer(self):
        """测试创建实例"""
        with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
             patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
             patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
             patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
            writer = UnifiedPatentWriter.create_unified_patent_writer()
            assert isinstance(writer, UnifiedPatentWriter)

    def test_create_unified_patent_writer_with_config(self):
        """测试带配置创建实例"""
        config = {"test": "value"}
        with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
             patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
             patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
             patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
            writer = UnifiedPatentWriter.create_unified_patent_writer(config=config)
            assert writer.config == config

    def test_get_unified_patent_writer_singleton(self):
        """测试单例模式"""
        with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
             patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
             patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
             patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
            writer1 = get_unified_patent_writer()
            writer2 = get_unified_patent_writer()
            assert writer1 is writer2


# ========== 错误处理测试 ==========

class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, writer):
        """测试执行异常处理"""
        # 模拟模块抛出异常
        writer.drafting_module.analyze_disclosure.side_effect = Exception("模拟异常")

        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "analyze_disclosure",
                "data": {},
            },
            config={},
            metadata={},
        )

        result = await writer.execute(context)

        assert result.status == AgentStatus.ERROR
        assert "模拟异常" in result.error_message


# ========== LLM客户端测试 ==========

class TestLLMClient:
    """测试LLM客户端获取"""

    def test_get_llm_client_success(self):
        """测试成功获取LLM客户端"""
        with patch('core.ai.llm.adapters.cloud_adapter.CloudLLMAdapter') as mock_adapter:
            mock_instance = Mock()
            mock_adapter.return_value = mock_instance

            with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
                 patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
                 patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
                 patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
                writer = UnifiedPatentWriter()
                client = writer._get_llm_client()
                assert client is not None

    def test_get_llm_client_fallback(self):
        """测试LLM客户端获取失败时的降级"""
        with patch('core.ai.llm.adapters.cloud_adapter.CloudLLMAdapter', side_effect=ImportError("No module")):
            with patch('core.framework.agents.xiaona.modules.drafting_module.PatentDraftingModule'), \
                 patch('core.framework.agents.xiaona.modules.response_module.ResponseModule'), \
                 patch('core.framework.agents.xiaona.modules.orchestration_module.OrchestrationModule'), \
                 patch('core.framework.agents.xiaona.modules.utility_module.UtilityModule'):
                writer = UnifiedPatentWriter()
                client = writer._get_llm_client()
                assert client is None


# ========== 边界条件测试 ==========

class TestEdgeCases:
    """测试边界条件"""

    @pytest.mark.asyncio
    async def test_empty_data(self, writer):
        """测试空数据"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "analyze_disclosure",
                "data": {},
            },
            config={},
            metadata={},
        )

        result = await writer.execute(context)
        # 应该优雅地处理空数据
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]

    @pytest.mark.asyncio
    async def test_none_data(self, writer):
        """测试None数据"""
        context = AgentExecutionContext(
            session_id="test",
            task_id="test",
            input_data={
                "task_type": "analyze_disclosure",
                "data": None,
            },
            config={},
            metadata={},
        )

        result = await writer.execute(context)
        # 应该优雅地处理None数据
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
