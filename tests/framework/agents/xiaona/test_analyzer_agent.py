"""
分析代理（AnalyzerAgent）单元测试

测试内容：
1. 初始化测试
2. 能力注册测试
3. 系统提示词测试
4. 基本功能测试（使用mock）
"""

import pytest
from typing import Dict, List, Optional, Any

from unittest.mock import patch

from core.framework.agents.xiaona.analyzer_agent import AnalyzerAgent
from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


class TestAnalyzerAgentInitialization:
    """分析代理初始化测试"""

    def test_analyzer_initialization(self):
        """测试分析代理初始化"""
        agent = AnalyzerAgent()
        assert agent.agent_id == "analyzer_agent"
        assert agent.status == AgentStatus.IDLE

    def test_analyzer_llm_manager_initialized(self):
        """测试LLM管理器初始化"""
        agent = AnalyzerAgent()
        assert agent.llm_manager is not None


class TestAnalyzerAgentCapabilities:
    """分析代理能力注册测试"""

    def test_analyzer_capabilities(self):
        """测试能力注册"""
        agent = AnalyzerAgent()
        capabilities = agent.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "feature_extraction" in capability_names
        assert "novelty_analysis" in capability_names
        assert "creativity_analysis" in capability_names
        assert "infringement_analysis" in capability_names

    def test_analyzer_capability_details(self):
        """测试能力详情"""
        agent = AnalyzerAgent()
        capabilities = agent.get_capabilities()

        # 检查feature_extraction能力
        feature_extraction = next((c for c in capabilities if c.name == "feature_extraction"), None)
        assert feature_extraction is not None
        assert feature_extraction.description == "技术特征提取"
        assert "专利文本" in feature_extraction.input_types

    def test_analyzer_has_capability(self):
        """测试能力检查方法"""
        agent = AnalyzerAgent()
        assert agent.has_capability("feature_extraction")
        assert agent.has_capability("novelty_analysis")
        assert not agent.has_capability("nonexistent_capability")


class TestAnalyzerAgentSystemPrompt:
    """分析代理系统提示词测试"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        agent = AnalyzerAgent()
        prompt = agent.get_system_prompt()

        assert "小娜·分析者" in prompt
        assert "技术特征提取" in prompt
        assert "新颖性分析" in prompt
        assert "创造性分析" in prompt
        assert "侵权分析" in prompt

    def test_system_prompt_contains_principles(self):
        """测试系统提示词包含工作原则"""
        agent = AnalyzerAgent()
        prompt = agent.get_system_prompt()

        assert "客观性" in prompt
        assert "全面性" in prompt
        assert "逻辑性" in prompt
        assert "法律性" in prompt


class TestAnalyzerAgentExecute:
    """分析代理基本功能测试"""

    @pytest.mark.asyncio
    async def test_execute_novelty_analysis(self):
        """测试新颖性分析执行"""
        agent = AnalyzerAgent()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={"user_input": "测试专利"},
            config={"analysis_type": "novelty"},
            metadata={}
        )

        # Mock LLM调用
        with patch.object(agent, '_extract_features', return_value={"features": {}}):
            result = await agent.execute(context)

        assert isinstance(result, AgentExecutionResult)
        assert result.agent_id == "analyzer_agent"

    @pytest.mark.asyncio
    async def test_execute_creativity_analysis(self):
        """测试创造性分析执行"""
        agent = AnalyzerAgent()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={"user_input": "测试专利"},
            config={"analysis_type": "creativity"},
            metadata={}
        )

        with patch.object(agent, '_extract_features', return_value={"features": {}}):
            result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_infringement_analysis(self):
        """测试侵权分析执行"""
        agent = AnalyzerAgent()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={"user_input": "测试专利"},
            config={"analysis_type": "infringement", "accused_product": "测试产品"},
            metadata={}
        )

        with patch.object(agent, '_extract_features', return_value={"features": {}}):
            result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_with_error(self):
        """测试错误处理"""
        agent = AnalyzerAgent()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={"user_input": "测试"},
            config={"analysis_type": "novelty"},
            metadata={}
        )

        # Mock异常
        with patch.object(agent, '_extract_features', side_effect=Exception("测试异常")):
            result = await agent.execute(context)

        assert result.status == AgentStatus.ERROR
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_extract_features(self):
        """测试技术特征提取"""
        agent = AnalyzerAgent()

        with patch.object(agent.llm_manager, 'generate', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"technical_field": "测试领域", "technical_problem": "测试问题", "essential_features": [], "additional_features": []}'

            result = await agent._extract_features("测试专利文本", None)

            assert "features" in result
            assert "raw_text" in result

    @pytest.mark.asyncio
    async def test_analyze_novelty(self):
        """测试新颖性分析"""
        agent = AnalyzerAgent()

        with patch.object(agent, '_extract_features', return_value={"features": {"essential_features": []}}):
            with patch.object(agent.llm_manager, 'generate', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = '{"feature_comparison": [], "novelty_conclusion": "具备新颖性", "novelty_basis": "测试依据"}'

                result = await agent._analyze_novelty("测试输入", None)

                assert result["analysis_type"] == "novelty"
                assert "features" in result
                assert "analysis" in result


class TestAnalyzerAgentHelperMethods:
    """分析代理辅助方法测试"""

    def test_get_target_patent_from_user_input(self):
        """测试从用户输入获取目标专利"""
        agent = AnalyzerAgent()

        patent = agent._get_target_patent("专利文本", None)
        assert patent == "专利文本"

    def test_get_target_patent_from_previous_results(self):
        """测试从前面结果获取目标专利"""
        agent = AnalyzerAgent()

        previous_results = {"patent_text": "来自结果的专利"}
        patent = agent._get_target_patent("", previous_results)
        assert patent == "来自结果的专利"

    def test_get_reference_documents(self):
        """测试获取对比文件"""
        agent = AnalyzerAgent()

        previous_results = {
            "xiaona_retriever": {
                "patents": [
                    {"title": "对比文件1", "abstract": "摘要1"},
                    {"title": "对比文件2", "abstract": "摘要2"}
                ]
            }
        }

        docs = agent._get_reference_documents(previous_results)
        assert len(docs) == 2

    def test_get_reference_documents_empty(self):
        """测试获取空对比文件"""
        agent = AnalyzerAgent()

        docs = agent._get_reference_documents(None)
        assert docs == []

    def test_format_reference_docs(self):
        """测试格式化对比文件"""
        agent = AnalyzerAgent()

        docs = [
            {"title": "对比文件1", "abstract": "摘要1"},
            {"title": "对比文件2", "abstract": "摘要2"}
        ]

        formatted = agent._format_reference_docs(docs)

        assert "D1:" in formatted
        assert "对比文件1" in formatted
        assert "D2:" in formatted


class TestAnalyzerAgentInfo:
    """分析代理信息测试"""

    def test_get_info(self):
        """测试获取代理信息"""
        agent = AnalyzerAgent()
        info = agent.get_info()

        assert info["agent_id"] == "analyzer_agent"
        assert info["agent_type"] == "AnalyzerAgent"
        assert "capabilities" in info

    def test_repr(self):
        """测试代理字符串表示"""
        agent = AnalyzerAgent()
        repr_str = repr(agent)

        assert "AnalyzerAgent" in repr_str
