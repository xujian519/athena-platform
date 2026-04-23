"""
RetrieverAgent单元测试

完整的测试套件，包括单元测试、集成测试和性能测试。
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import asyncio

from core.agents.xiaona.retriever_agent import RetrieverAgent
from core.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


# ==================== 单元测试 ====================

class TestRetrieverAgentInit:
    """测试RetrieverAgent初始化"""

    def test_init_basic(self):
        """测试基本初始化"""
        agent = RetrieverAgent(agent_id="test_retriever")

        assert agent.agent_id == "test_retriever"
        assert agent.status == AgentStatus.IDLE
        assert len(agent.get_capabilities()) == 3

    def test_capabilities_registered(self):
        """测试能力注册"""
        agent = RetrieverAgent(agent_id="test_retriever")

        capabilities = agent.get_capabilities()

        # 验证能力数量
        assert len(capabilities) == 3

        # 验证能力名称
        capability_names = [cap.name for cap in capabilities]
        assert "patent_search" in capability_names
        assert "keyword_expansion" in capability_names
        assert "document_filtering" in capability_names

    def test_system_prompt(self):
        """测试系统提示词"""
        agent = RetrieverAgent(agent_id="test_retriever")

        prompt = agent.get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "检索" in prompt or "search" in prompt.lower()


class TestRetrieverAgentExecute:
    """测试RetrieverAgent执行"""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试成功执行"""
        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "检索自动驾驶相关专利",
                "operation": "patent_search",
            },
            config={
                "databases": ["cnipa"],
                "limit": 10,
            },
            metadata={},
        )

        # Mock LLM和工具
        with patch.object(agent, 'llm_manager') as mock_llm, \
             patch.object(agent, 'tool_registry') as mock_registry:

            # Mock LLM响应
            mock_llm.generate = AsyncMock(return_value='{"core_keywords": ["自动驾驶", "车辆", "控制"]}')

            # Mock工具响应
            mock_tool = AsyncMock()
            mock_tool.function = AsyncMock(return_value={
                "patents": [
                    {"patent_id": "CN123456", "title": "自动驾驶车辆"},
                ]
            })
            mock_registry.get = Mock(return_value=mock_tool)

            # 执行
            result = await agent.execute(context)

            # 验证结果
            assert result.status == AgentStatus.COMPLETED
            assert result.output_data is not None
            assert "keywords" in result.output_data
            assert "patents" in result.output_data

    @pytest.mark.asyncio
    async def test_execute_with_previous_results(self):
        """测试使用前序Agent的结果"""
        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "检索专利",
                "previous_results": {
                    "xiaona_planner": {
                        "keywords": ["自动驾驶", "车辆控制"]
                    }
                },
            },
            config={},
            metadata={},
        )

        # Mock工具
        with patch.object(agent, 'tool_registry') as mock_registry:
            mock_tool = AsyncMock()
            mock_tool.function = AsyncMock(return_value={"patents": []})
            mock_registry.get = Mock(return_value=mock_tool)

            # 执行
            result = await agent.execute(context)

            # 验证：应该使用planner提供的关键词
            assert result.status == AgentStatus.COMPLETED
            # 应该不调用LLM（因为已有planner的结果）

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        """测试执行失败"""
        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "检索专利",
            },
            config={
                "databases": ["invalid_db"],  # 无效数据库
            },
            metadata={},
        )

        # Mock工具抛出异常
        with patch.object(agent, 'tool_registry') as mock_registry:
            mock_tool = AsyncMock()
            mock_tool.function = AsyncMock(
                side_effect=Exception("数据库连接失败")
            )
            mock_registry.get = Mock(return_value=mock_tool)

            # 执行
            result = await agent.execute(context)

            # 验证错误处理
            assert result.status == AgentStatus.ERROR
            assert result.error_message is not None


class TestRetrieverAgentMethods:
    """测试RetrieverAgent的各个方法"""

    @pytest.mark.asyncio
    async def test_expand_keywords(self):
        """测试关键词扩展"""
        agent = RetrieverAgent(agent_id="test_retriever")

        # Mock LLM
        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value='{"core_keywords": ["关键词1", "关键词2"], "extended_keywords": ["扩展1"]}'
            )

            # 执行
            keywords = await agent._expand_keywords(
                "自动驾驶车辆控制",
                {}
            )

            # 验证
            assert len(keywords) >= 2
            assert "关键词1" in keywords or "关键词2" in keywords

    @pytest.mark.asyncio
    async def test_build_search_queries(self):
        """测试构建检索式"""
        agent = RetrieverAgent(agent_id="test_retriever")

        keywords = ["自动驾驶", "车辆", "控制"]
        queries = await agent._build_search_queries(keywords)

        # 验证
        assert len(queries) >= 1
        assert all(isinstance(q, str) for q in queries)

    @pytest.mark.asyncio
    async def test_filter_and_rank_results(self):
        """测试结果筛选和排序"""
        agent = RetrieverAgent(agent_id="test_retriever")

        results = [
            {"patent_id": "CN001", "title": "专利1", "relevance_score": 0.9},
            {"patent_id": "CN002", "title": "专利2", "relevance_score": 0.7},
            {"patent_id": "CN003", "title": "专利3", "relevance_score": 0.8},
        ]

        filtered = await agent._filter_and_rank_results(
            results,
            {"limit": 2}
        )

        # 验证
        assert len(filtered) <= 2
        # 应该按相关性排序
        if len(filtered) >= 2:
            assert filtered[0]["relevance_score"] >= filtered[1]["relevance_score"]


class TestRetrieverAgentValidation:
    """测试输入验证"""

    def test_validate_input_valid(self):
        """测试有效输入"""
        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": "test"},
            config={},
            metadata={},
        )

        # 验证应该通过
        assert agent.validate_input(context) is True

    def test_validate_input_missing_session_id(self):
        """测试缺少session_id"""
        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="",  # 空session_id
            task_id="TASK_001",
            input_data={"user_input": "test"},
            config={},
            metadata={},
        )

        # 验证应该失败
        assert agent.validate_input(context) is False

    def test_validate_input_missing_task_id(self):
        """测试缺少task_id"""
        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="",  # 空task_id
            input_data={"user_input": "test"},
            config={},
            metadata={},
        )

        # 验证应该失败
        assert agent.validate_input(context) is False


# ==================== 集成测试 ====================

class TestRetrieverAgentIntegration:
    """测试RetrieverAgent与其他组件的集成"""

    @pytest.mark.asyncio
    async def test_with_llm_manager(self):
        """测试与LLM Manager的集成"""
        from core.llm.unified_llm_manager import UnifiedLLMManager

        agent = RetrieverAgent(agent_id="test_retriever")

        # 验证LLM Manager已初始化
        assert agent.llm_manager is not None
        assert isinstance(agent.llm_manager, UnifiedLLMManager)

    @pytest.mark.asyncio
    async def test_with_tool_registry(self):
        """测试与工具注册表的集成"""
        from core.tools.unified_registry import get_unified_registry

        agent = RetrieverAgent(agent_id="test_retriever")

        # 验证工具注册表已初始化
        assert agent.tool_registry is not None
        # 应该能够获取工具
        registry = get_unified_registry()


# ==================== 性能测试 ====================

class TestRetrieverAgentPerformance:
    """测试RetrieverAgent性能"""

    @pytest.mark.asyncio
    async def test_execution_time(self):
        """测试执行时间"""
        import time

        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": "test"},
            config={},
            metadata={},
        )

        # Mock所有依赖
        with patch.object(agent, 'llm_manager') as mock_llm, \
             patch.object(agent, 'tool_registry') as mock_registry:

            mock_llm.generate = AsyncMock(return_value='{"keywords": ["test"]}')
            mock_tool = AsyncMock()
            mock_tool.function = AsyncMock(return_value={"patents": []})
            mock_registry.get = Mock(return_value=mock_tool)

            # 测量执行时间
            start = time.time()
            result = await agent.execute(context)
            elapsed = time.time() - start

            # 验证
            assert result.status == AgentStatus.COMPLETED
            assert elapsed < 5.0  # 应该在5秒内完成（即使是Mock）

    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """测试并发执行"""
        agent = RetrieverAgent(agent_id="test_retriever")

        contexts = [
            AgentExecutionContext(
                session_id=f"SESSION_{i}",
                task_id=f"TASK_{i}",
                input_data={"user_input": f"test{i}"},
                config={},
                metadata={},
            )
            for i in range(10)
        ]

        # Mock所有依赖
        with patch.object(agent, 'llm_manager') as mock_llm, \
             patch.object(agent, 'tool_registry') as mock_registry:

            mock_llm.generate = AsyncMock(return_value='{"keywords": ["test"]}')
            mock_tool = AsyncMock()
            mock_tool.function = AsyncMock(return_value={"patents": []})
            mock_registry.get = Mock(return_value=mock_tool)

            # 并发执行
            import time
            start = time.time()
            results = await asyncio.gather(*[
                agent.execute(ctx) for ctx in contexts
            ])
            elapsed = time.time() - start

            # 验证所有任务都成功
            assert all(r.status == AgentStatus.COMPLETED for r in results)
            assert len(results) == 10

            print(f"\n并发执行10个任务耗时: {elapsed:.2f}秒")


# ==================== 边界测试 ====================

class TestRetrieverAgentEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """测试空输入"""
        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": ""},  # 空输入
            config={},
            metadata={},
        )

        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(return_value='{"keywords": []}')

            result = await agent.execute(context)

            # 应该优雅处理空输入
            assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]

    @pytest.mark.asyncio
    async def test_very_long_input(self):
        """测试超长输入"""
        agent = RetrieverAgent(agent_id="test_retriever")

        long_input = "测试" * 10000  # 30,000个字符

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": long_input},
            config={},
            metadata={},
        )

        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(return_value='{"keywords": ["test"]}')

            result = await agent.execute(context)

            # 应该能够处理
            assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]

    @pytest.mark.asyncio
    async def test_no_search_results(self):
        """测试无检索结果"""
        agent = RetrieverAgent(agent_id="test_retriever")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": "test"},
            config={},
            metadata={},
        )

        with patch.object(agent, 'tool_registry') as mock_registry:
            # 返回空结果
            mock_tool = AsyncMock()
            mock_tool.function = AsyncMock(return_value={"patents": []})
            mock_registry.get = Mock(return_value=mock_tool)

            with patch.object(agent, 'llm_manager') as mock_llm:
                mock_llm.generate = AsyncMock(return_value='{"keywords": ["test"]}')

                result = await agent.execute(context)

                # 应该优雅处理空结果
                assert result.status == AgentStatus.COMPLETED
                assert result.output_data["total_count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
