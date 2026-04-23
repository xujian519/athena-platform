"""
统一专利撰写代理（UnifiedPatentWriter）单元测试

测试内容：
1. 初始化测试
2. 能力注册测试
3. 系统提示词测试
4. 基本功能测试（使用mock）
"""

import pytest
from typing import Dict, List, Optional, Any

from unittest.mock import AsyncMock, MagicMock, patch

from core.framework.agents.xiaona.unified_patent_writer import UnifiedPatentWriter
from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


class TestUnifiedPatentWriterInitialization:
    """统一撰写代理初始化测试"""

    def test_unified_writer_initialization(self):
        """测试统一撰写代理初始化"""
        writer = UnifiedPatentWriter()
        assert writer.agent_id == "unified_patent_writer"
        assert writer.status == AgentStatus.IDLE

    def test_unified_writer_config_initialization(self):
        """测试带配置的初始化"""
        config = {"test_config": "value"}
        writer = UnifiedPatentWriter(config=config)
        assert writer.config == config


class TestUnifiedPatentWriterCapabilities:
    """统一撰写代理能力注册测试"""

    def test_unified_writer_capabilities_count(self):
        """测试能力数量"""
        writer = UnifiedPatentWriter()
        capabilities = writer.get_capabilities()

        # 应该有13个能力（7个撰写 + 2个答复 + 2个编排 + 2个工具）
        assert len(capabilities) >= 10

    def test_unified_writer_drafting_capabilities(self):
        """测试撰写模块能力"""
        writer = UnifiedPatentWriter()
        capabilities = writer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "analyze_disclosure" in capability_names
        assert "assess_patentability" in capability_names
        assert "draft_specification" in capability_names
        assert "draft_claims" in capability_names

    def test_unified_writer_response_capabilities(self):
        """测试答复模块能力"""
        writer = UnifiedPatentWriter()
        capabilities = writer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "draft_response" in capability_names
        assert "draft_invalidation" in capability_names

    def test_unified_writer_orchestration_capabilities(self):
        """测试编排模块能力"""
        writer = UnifiedPatentWriter()
        capabilities = writer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "draft_full_application" in capability_names
        assert "orchestrate_response" in capability_names

    def test_unified_writer_utility_capabilities(self):
        """测试工具模块能力"""
        writer = UnifiedPatentWriter()
        capabilities = writer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "format_document" in capability_names
        assert "calculate_quality_score" in capability_names


class TestUnifiedPatentWriterSystemPrompt:
    """统一撰写代理系统提示词测试"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        writer = UnifiedPatentWriter()
        prompt = writer.get_system_prompt()

        assert "小娜·撰写者" in prompt
        assert "专利撰写" in prompt
        assert "权利要求书" in prompt
        assert "说明书" in prompt

    def test_system_prompt_constant(self):
        """测试系统提示词常量"""
        prompt = UnifiedPatentWriter.SYSTEM_PROMPT

        assert "权利要求书撰写" in prompt
        assert "说明书撰写" in prompt
        assert "审查意见答复" in prompt


class TestUnifiedPatentWriterExecute:
    """统一撰写代理基本功能测试"""

    @pytest.mark.asyncio
    async def test_execute_analyze_disclosure(self):
        """测试分析交底书任务"""
        writer = UnifiedPatentWriter()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "task_type": "analyze_disclosure",
                "data": {"title": "测试发明", "field": "测试领域"}
            },
            config={},
            metadata={}
        )

        # Mock drafting module
        with patch.object(writer, 'drafting_module') as mock_module:
            mock_module.analyze_disclosure = AsyncMock(return_value={"status": "completed"})
            result = await writer.execute(context)

        assert isinstance(result, AgentExecutionResult)
        assert result.agent_id == "unified_patent_writer"

    @pytest.mark.asyncio
    async def test_execute_draft_claims(self):
        """测试撰写权利要求任务"""
        writer = UnifiedPatentWriter()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "task_type": "draft_claims",
                "data": {"invention_content": "测试发明内容"}
            },
            config={},
            metadata={}
        )

        with patch.object(writer, 'drafting_module') as mock_module:
            mock_module.draft_claims = AsyncMock(return_value={"claims": []})
            result = await writer.execute(context)

        assert result.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_format_document(self):
        """测试格式化文档任务"""
        writer = UnifiedPatentWriter()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "task_type": "format_document",
                "data": {
                    "document_type": "claims",
                    "content": "1. 一种测试装置..."
                }
            },
            config={},
            metadata={}
        )

        with patch.object(writer, 'utility_module') as mock_module:
            mock_module.format_document = MagicMock(return_value="格式化后的文档")
            result = await writer.execute(context)

        assert result.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_with_missing_task_type(self):
        """测试缺少任务类型的错误处理"""
        writer = UnifiedPatentWriter()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={},
            config={},
            metadata={}
        )

        result = await writer.execute(context)

        assert result.status == AgentStatus.ERROR
        assert "缺少task_type" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_with_invalid_task_type(self):
        """测试无效任务类型的错误处理"""
        writer = UnifiedPatentWriter()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={"task_type": "invalid_task"},
            config={},
            metadata={}
        )

        result = await writer.execute(context)

        assert result.status == AgentStatus.ERROR


class TestUnifiedPatentWriterConvenienceMethods:
    """统一撰写代理便捷方法测试"""

    @pytest.mark.asyncio
    async def test_analyze_disclosure_convenience_method(self):
        """测试分析交底书便捷方法"""
        writer = UnifiedPatentWriter()

        with patch.object(writer, 'drafting_module') as mock_module:
            mock_module.analyze_disclosure = AsyncMock(return_value={"status": "ok"})

            result = await writer.analyze_disclosure({"title": "测试"})

            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_draft_full_application_convenience_method(self):
        """测试完整撰写便捷方法"""
        writer = UnifiedPatentWriter()

        with patch.object(writer, 'orchestration_module') as mock_module:
            mock_module.draft_full_application = AsyncMock(return_value={"application": "completed"})

            result = await writer.draft_full_application({"title": "测试"})

            assert result["application"] == "completed"


class TestUnifiedPatentWriterRouting:
    """统一撰写代理路由测试"""

    @pytest.mark.asyncio
    async def test_route_to_drafting_module(self):
        """测试路由到撰写模块"""
        writer = UnifiedPatentWriter()

        with patch.object(writer, 'drafting_module') as mock_module:
            mock_module.analyze_disclosure = AsyncMock(return_value={"result": "ok"})

            context = AgentExecutionContext(
                session_id="test_session",
                task_id="test_task",
                input_data={"data": {}},
                config={},
                metadata={}
            )

            result = await writer._route_to_drafting_module("analyze_disclosure", context)

            assert result["result"] == "ok"

    @pytest.mark.asyncio
    async def test_route_to_response_module(self):
        """测试路由到答复模块"""
        writer = UnifiedPatentWriter()

        with patch.object(writer, 'response_module') as mock_module:
            mock_module.draft_response = AsyncMock(return_value={"response": "drafted"})

            context = AgentExecutionContext(
                session_id="test_session",
                task_id="test_task",
                input_data={
                    "user_input": "测试",
                    "previous_results": {},
                    "model": "test_model"
                },
                config={},
                metadata={}
            )

            result = await writer._route_to_response_module("draft_response", context)

            assert result["response"] == "drafted"

    @pytest.mark.asyncio
    async def test_route_to_utility_module(self):
        """测试路由到工具模块"""
        writer = UnifiedPatentWriter()

        with patch.object(writer, 'utility_module') as mock_module:
            mock_module.format_document = MagicMock(return_value="formatted")

            context = AgentExecutionContext(
                session_id="test_session",
                task_id="test_task",
                input_data={
                    "data": {
                        "document_type": "claims",
                        "content": "测试内容"
                    }
                },
                config={},
                metadata={}
            )

            result = await writer._route_to_utility_module("format_document", context)

            assert result["formatted_document"] == "formatted"


class TestUnifiedPatentWriterInfo:
    """统一撰写代理信息测试"""

    def test_get_info(self):
        """测试获取代理信息"""
        writer = UnifiedPatentWriter()
        info = writer.get_info()

        assert info["agent_id"] == "unified_patent_writer"
        assert info["agent_type"] == "UnifiedPatentWriter"
        assert "capabilities" in info

    def test_repr(self):
        """测试代理字符串表示"""
        writer = UnifiedPatentWriter()
        repr_str = repr(writer)

        assert "UnifiedPatentWriter" in repr_str


class TestUnifiedPatentWriterFactory:
    """统一撰写代理工厂测试"""

    def test_create_unified_patent_writer(self):
        """测试创建实例"""
        writer = UnifiedPatentWriter.create_unified_patent_writer()

        assert isinstance(writer, UnifiedPatentWriter)
        assert writer.agent_id == "unified_patent_writer"

    def test_get_unified_patent_writer_singleton(self):
        """测试单例获取"""
        writer1 = UnifiedPatentWriter.get_unified_patent_writer()
        writer2 = UnifiedPatentWriter.get_unified_patent_writer()

        assert writer1 is writer2
