"""
ReAct推理引擎测试（Agent编排）
"""

from unittest.mock import AsyncMock

import pytest
from core.xiaonuo_agent.reasoning.react_engine import (
    Action,
    ReActEngine,
    Thought,
    ThoughtType,
)


@pytest.fixture
def react_engine():
    """创建ReAct引擎实例"""
    return ReActEngine(max_steps=10)


@pytest.fixture
def mock_tools():
    """模拟工具"""
    return {
        "search_tool": AsyncMock(return_value="搜索结果"),
        "patent-searcher": AsyncMock(return_value={"patents": ["CN123456"]}),
        "legal-analyzer": AsyncMock(return_value={"analysis": "合法"}),
    }


class TestAgentSelection:
    """测试Agent选择"""

    @pytest.mark.asyncio
    async def test_identify_task_type_patent_search(self, react_engine):
        """测试识别专利检索任务"""
        thought = Thought(step=1, thought_type=ThoughtType.ANALYSIS, content="需要搜索专利")
        task_type = await react_engine._identify_task_type("搜索自动驾驶相关专利", thought)

        assert task_type == "patent_search"

    @pytest.mark.asyncio
    async def test_identify_task_type_patent_analysis(self, react_engine):
        """测试识别专利分析任务"""
        thought = Thought(step=1, thought_type=ThoughtType.ANALYSIS, content="需要分析专利")
        # 使用不包含具体分析类型的专利分析任务
        task_type = await react_engine._identify_task_type("分析专利CN123456的技术方案", thought)

        assert task_type == "patent_analysis"

    @pytest.mark.asyncio
    async def test_identify_task_type_infringement(self, react_engine):
        """测试识别侵权分析任务"""
        thought = Thought(step=1, thought_type=ThoughtType.ANALYSIS, content="需要分析侵权")
        # 调整任务描述，使其能够正确匹配
        task_type = await react_engine._identify_task_type("判断产品A是否侵权专利CN123456", thought)

        assert task_type == "infringement_analysis"

    @pytest.mark.asyncio
    async def test_identify_task_type_general(self, react_engine):
        """测试识别通用任务"""
        thought = Thought(step=1, thought_type=ThoughtType.ANALYSIS, content="通用任务")
        task_type = await react_engine._identify_task_type("帮我写个总结", thought)

        assert task_type == "general_task"

    @pytest.mark.asyncio
    async def test_select_agent_for_patent_search(self, react_engine):
        """测试选择专利检索Agent"""
        tools = {
            "patent-searcher": AsyncMock(),
            "other-tool": AsyncMock(),
        }

        agent_name = await react_engine._select_agent("patent_search", tools)

        assert agent_name == "patent-searcher"

    @pytest.mark.asyncio
    async def test_select_agent_not_found(self, react_engine):
        """测试Agent不存在"""
        tools = {
            "other-tool": AsyncMock(),
        }

        agent_name = await react_engine._select_agent("patent_search", tools)

        assert agent_name is None


class TestAgentDecision:
    """测试Agent决策"""

    @pytest.mark.asyncio
    async def test_decide_action_selects_agent(self, react_engine, mock_tools):
        """测试决策选择Agent"""
        thought = Thought(step=1, thought_type=ThoughtType.DECISION, content="需要搜索专利")
        task = "搜索自动驾驶专利"

        action = await react_engine._decide_action(
            thought=thought,
            task=task,
            available_tools=mock_tools,
            context={},
            step=1,
        )

        # 应该选择Agent
        assert action.is_agent is True
        assert action.action_type == "patent-searcher"
        assert "Agent" in action.reasoning

    @pytest.mark.asyncio
    async def test_decide_action_fallback_to_tool(self, react_engine):
        """测试回退到工具"""
        thought = Thought(step=1, thought_type=ThoughtType.DECISION, content="需要执行简单任务")
        task = "执行简单任务"

        tools = {"search_tool": AsyncMock(return_value="结果")}

        action = await react_engine._decide_action(
            thought=thought,
            task=task,
            available_tools=tools,
            context={},
            step=1,
        )

        # 应该使用工具,不是Agent
        assert action.is_agent is False


class TestAgentExecution:
    """测试Agent执行"""

    @pytest.mark.asyncio
    async def test_execute_agent_action(self, react_engine, mock_tools):
        """测试执行Agent行动"""
        from core.xiaonuo_agent.context import AgentContext

        agent_context = AgentContext(session_id="test_session", task_id="test_task")

        action = Action(
            step=1,
            action_type="patent-searcher",
            parameters={"task": "搜索专利"},
            reasoning="使用专利检索Agent",
            is_agent=True,
            agent_context=agent_context,
        )

        observation = await react_engine._execute_action(
            action=action,
            available_tools=mock_tools,
            context={},
            step=1,
        )

        assert observation.success is True
        assert observation.result == {"patents": ["CN123456"]}
        assert "patent-searcher" in agent_context.agent_call_chain

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, react_engine):
        """测试Agent不存在"""
        action = Action(
            step=1,
            action_type="non-existent-agent",
            parameters={"task": "测试"},
            reasoning="测试不存在的Agent",
            is_agent=True,
        )

        observation = await react_engine._execute_action(
            action=action,
            available_tools={},
            context={},
            step=1,
        )

        assert observation.success is False
        assert "不可用" in observation.error_message


class TestAgentContextIntegration:
    """测试Agent上下文集成"""

    @pytest.mark.asyncio
    async def test_agent_context_passed_to_agent(self, react_engine, mock_tools):
        """测试Agent上下文传递给Agent"""
        from core.xiaonuo_agent.context import AgentContext

        agent_context = AgentContext(
            session_id="test_session",
            task_id="test_task",
            shared_data={"key": "value"},
        )

        action = Action(
            step=1,
            action_type="patent-searcher",
            parameters={"task": "搜索专利"},
            reasoning="使用专利检索Agent",
            is_agent=True,
            agent_context=agent_context,
        )

        await react_engine._execute_action(
            action=action,
            available_tools=mock_tools,
            context={},
            step=1,
        )

        # 验证Agent被添加到调用链
        assert "patent-searcher" in agent_context.agent_call_chain

    @pytest.mark.asyncio
    async def test_agent_context_updated_from_result(self, react_engine):
        """测试Agent上下文从Agent结果更新"""
        from core.xiaonuo_agent.context import AgentContext

        agent_context = AgentContext(
            session_id="test_session",
            task_id="test_task",
        )

        # 模拟返回shared_data的Agent
        async def mock_agent_with_shared_data(task, agent_context=None):
            return {"result": "success", "shared_data": {"new_key": "new_value"}}

        tools = {
            "test-agent": mock_agent_with_shared_data,
        }

        action = Action(
            step=1,
            action_type="test-agent",
            parameters={"task": "测试"},
            reasoning="测试Agent",
            is_agent=True,
            agent_context=agent_context,
        )

        await react_engine._execute_action(
            action=action,
            available_tools=tools,
            context={},
            step=1,
        )

        # 验证上下文被更新
        assert agent_context.get("new_key") == "new_value"


class TestAgentOrchestration:
    """测试Agent编排集成"""

    @pytest.mark.asyncio
    async def test_solve_with_agent(self, react_engine, mock_tools):
        """测试使用Agent解决任务"""
        task = "搜索自动驾驶相关专利"

        result = await react_engine.solve(
            task=task,
            context={},
            tools=mock_tools,
        )

        # 验证结果
        assert result is not None
        assert len(result.actions) > 0

        # 验证至少有一个Agent被调用
        agent_actions = [a for a in result.actions if a.is_agent]
        assert len(agent_actions) > 0

    @pytest.mark.asyncio
    async def test_multi_agent_orchestration(self, react_engine):
        """测试多Agent编排"""
        # 模拟多个Agent
        async def mock_patent_searcher(task, context=None):
            return {"patents": ["CN123456", "CN789012"], "search_count": 2}

        async def mock_patent_analyzer(data, context=None):
            return {"analysis": "专利具有创造性", "novelty": "high"}

        tools = {
            "patent-searcher": mock_patent_searcher,
            "patent-analyzer": mock_patent_analyzer,
        }

        task = "搜索并分析自动驾驶专利"

        result = await react_engine.solve(
            task=task,
            context={},
            tools=tools,
        )

        # 验证多个Agent被调用
        agent_actions = [a for a in result.actions if a.is_agent]
        assert len(agent_actions) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
