"""
AnalyzerAgent单元测试

完整的测试套件，包括单元测试、集成测试和性能测试。
"""

from unittest.mock import AsyncMock, patch

import pytest

from core.framework.agents.xiaona.analyzer_agent import AnalyzerAgent
from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentStatus,
)

# ==================== 单元测试 ====================

class TestAnalyzerAgentInit:
    """测试AnalyzerAgent初始化"""

    def test_init_basic(self):
        """测试基本初始化"""
        agent = AnalyzerAgent(agent_id="test_analyzer")

        assert agent.agent_id == "test_analyzer"
        assert agent.status == AgentStatus.IDLE
        assert len(agent.get_capabilities()) >= 1

    def test_capabilities_registered(self):
        """测试能力注册"""
        agent = AnalyzerAgent(agent_id="test_analyzer")

        capabilities = agent.get_capabilities()

        # 验证至少有一个能力
        assert len(capabilities) >= 1

        # 验证能力有必要的字段
        for cap in capabilities:
            assert cap.name
            assert cap.description
            assert cap.input_types
            assert cap.output_types

    def test_system_prompt(self):
        """测试系统提示词"""
        agent = AnalyzerAgent(agent_id="test_analyzer")

        prompt = agent.get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 100


class TestAnalyzerAgentExecute:
    """测试AnalyzerAgent执行"""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试成功执行"""
        agent = AnalyzerAgent(agent_id="test_analyzer")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "分析专利CN123456的创造性",
                "patent_id": "CN123456",
                "operation": "creativity_analysis",
            },
            config={},
            metadata={},
        )

        # Mock LLM
        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value='{"analysis": "具有创造性", "confidence": 0.85}'
            )

            # 执行
            result = await agent.execute(context)

            # 验证结果
            assert result.status == AgentStatus.COMPLETED
            assert result.output_data is not None

    @pytest.mark.asyncio
    async def test_execute_with_patent_data(self):
        """测试使用专利数据"""
        agent = AnalyzerAgent(agent_id="test_analyzer")

        patent_data = {
            "patent_id": "CN123456",
            "title": "自动驾驶车辆",
            "abstract": "本发明涉及...",
            "claims": ["1. 一种方法...", "2. 根据权利要求1..."],
        }

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "分析专利",
                "patent_data": patent_data,
                "previous_results": {},
            },
            config={},
            metadata={},
        )

        # Mock LLM
        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value='{"analysis": "分析结果"}'
            )

            # 执行
            result = await agent.execute(context)

            # 验证
            assert result.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        """测试执行失败"""
        agent = AnalyzerAgent(agent_id="test_analyzer")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "分析专利",
            },
            config={},
            metadata={},
        )

        # Mock LLM抛出异常
        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(
                side_effect=Exception("LLM调用失败")
            )

            # 执行
            result = await agent.execute(context)

            # 验证错误处理
            assert result.status == AgentStatus.ERROR
            assert result.error_message is not None


class TestAnalyzerAgentMethods:
    """测试AnalyzerAgent的各个方法"""

    @pytest.mark.asyncio
    async def test_extract_features(self):
        """测试技术特征提取"""
        agent = AnalyzerAgent(agent_id="test_analyzer")

        patent_text = "一种自动驾驶方法，包括：感知环境、规划路径、控制车辆。"

        # Mock LLM
        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value='''{
                    "technical_field": "自动驾驶",
                    "technical_problem": "车辆控制",
                    "essential_features": [
                        {"feature": "感知环境", "description": "使用传感器感知"},
                        {"feature": "规划路径", "description": "规划行驶路径"}
                    ],
                    "additional_features": []
                }'''
            )

            # 执行
            result = await agent._extract_features(patent_text, {})

            # 验证
            assert result is not None
            assert "features" in result
            assert "technical_field" in result["features"]

    @pytest.mark.asyncio
    async def test_analyze_novelty(self):
        """测试新颖性分析"""
        agent = AnalyzerAgent(agent_id="test_analyzer")

        patent_text = "一种自动驾驶方法"

        # Mock LLM
        with patch.object(agent, 'llm_manager') as mock_llm:
            # Mock特征提取
            mock_llm.generate = AsyncMock(
                return_value='''{
                    "feature_comparison": [
                        {"feature": "特征1", "disclosed_in": ["D1"], "novel": false},
                        {"feature": "特征2", "disclosed_in": [], "novel": true}
                    ],
                    "novelty_conclusion": "具备新颖性",
                    "novelty_basis": "特征2未被公开"
                }'''
            )

            # 执行
            result = await agent._analyze_novelty(patent_text, {})

            # 验证
            assert result is not None
            assert "analysis_type" in result
            assert result["analysis_type"] == "novelty"


# ==================== 集成测试 ====================

class TestAnalyzerAgentIntegration:
    """测试AnalyzerAgent与其他Agent的协作"""

    @pytest.mark.asyncio
    async def test_workflow_with_retriever(self):
        """测试与RetrieverAgent的协作"""
        from tests.agents.mocks.mock_agent import create_success_mock

        # 创建Mock RetrieverAgent
        retriever = create_success_mock(
            agent_id="retriever",
            result={
                "patents": [
                    {"patent_id": "CN001", "title": "对比文件1"},
                    {"patent_id": "CN002", "title": "对比文件2"},
                ]
            }
        )

        # 创建AnalyzerAgent
        analyzer = AnalyzerAgent(agent_id="analyzer")

        # 步骤1: 检索
        context1 = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": "检索并分析"},
            config={},
            metadata={},
        )
        result1 = await retriever.execute(context1)

        # 步骤2: 分析（使用检索结果）
        context2 = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_002",
            input_data={
                "user_input": "分析检索结果",
                "previous_results": {
                    "retriever": result1.output_data
                }
            },
            config={},
            metadata={},
        )

        # Mock LLM
        with patch.object(analyzer, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value='{"analysis": "分析完成"}'
            )

            result2 = await analyzer.execute(context2)

        # 验证工作流
        assert result1.status == AgentStatus.COMPLETED
        assert result2.status == AgentStatus.COMPLETED
        assert len(result1.output_data["patents"]) == 2


# ==================== 性能测试 ====================

class TestAnalyzerAgentPerformance:
    """测试AnalyzerAgent性能"""

    @pytest.mark.asyncio
    async def test_execution_time(self):
        """测试执行时间"""
        import time

        agent = AnalyzerAgent(agent_id="test_analyzer")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": "test"},
            config={},
            metadata={},
        )

        # Mock LLM
        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(return_value='{"analysis": "test"}')

            # 测量执行时间
            start = time.time()
            result = await agent.execute(context)
            elapsed = time.time() - start

            # 验证
            assert result.status == AgentStatus.COMPLETED
            assert elapsed < 5.0

            print(f"\nAnalyzerAgent执行时间: {elapsed:.2f}秒")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
