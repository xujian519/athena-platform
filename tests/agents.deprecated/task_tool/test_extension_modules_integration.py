"""扩展模块完整集成测试

测试TaskTool的所有扩展模块集成功能，包括SubagentRegistry、ForkContextBuilder、TaskScheduler和ToolFilter。
"""

import pytest

from core.framework.agents.fork_context_builder import ForkContext
from core.framework.agents.subagent_registry import SubagentRegistry
from core.framework.agents.task_tool.task_tool import TaskTool


class TestExtensionModulesIntegration:
    """扩展模块集成测试套件"""

    @pytest.fixture
    def task_tool(self):
        """创建TaskTool实例"""
        return TaskTool()

    def test_task_tool_initialization(self, task_tool):
        """测试TaskTool初始化，包含所有扩展模块"""
        assert task_tool.task_store is not None
        assert task_tool.model_mapper is not None
        assert task_tool.subagent_registry is not None
        assert task_tool.tool_filter is not None
        assert task_tool.fork_context_builder is not None

    def test_subagent_registry_integration(self, task_tool):
        """测试SubagentRegistry集成"""
        assert isinstance(task_tool.subagent_registry, SubagentRegistry)
        assert task_tool.subagent_registry.get_agent_count() == 4

        agent = task_tool.subagent_registry.get_agent("patent-analyst")
        assert agent is not None
        assert agent.agent_type == "patent-analyst"

    def test_fork_context_builder_integration(self, task_tool):
        """测试ForkContextBuilder集成"""
        assert task_tool.fork_context_builder is not None

        fork_ctx = task_tool.fork_context_builder.build(
            prompt="测试上下文",
            context={},
        )

        assert fork_ctx is not None
        assert isinstance(fork_ctx, ForkContext)

    def test_full_integration_with_subagent(self, task_tool):
        """测试与SubagentRegistry的完整集成"""
        result = task_tool.execute(
            prompt="专利分析任务",
            tools=["patent_search", "knowledge_graph"],
            agent_type="patent-analyst",
            background=False,
        )

        assert "task_id" in result
        assert "status" in result
        assert "filtered_tools" in result

    def test_full_integration_with_fork_context(self, task_tool):
        """测试与ForkContextBuilder的完整集成"""
        result = task_tool.execute(
            prompt="需要上下文的任务",
            tools=["web_search", "knowledge_graph"],
            fork_context={"parent_messages": []},
            agent_type="patent-searcher",
            background=False,
        )

        assert "task_id" in result
        assert "status" in result

    def test_full_background_execution(self, task_tool):
        """测试后台执行与所有扩展模块的集成"""
        result = task_tool.execute(
            prompt="后台任务",
            tools=["patent_search"],
            agent_type="patent-analyst",
            background=True,
        )

        assert "task_id" in result
        assert result["status"] == "submitted"

    def test_error_handling_invalid_agent_type(self, task_tool):
        """测试无效代理类型的错误处理"""
        result = task_tool.execute(
            prompt="测试任务",
            tools=[],
            agent_type="invalid-agent",
        )

        assert "task_id" in result
        assert "model" in result

    def test_tool_selection_override(self, task_tool):
        """测试模型覆盖与代理类型"""
        result = task_tool.execute(
            prompt="模型选择测试",
            tools=[],
            model="haiku",
            agent_type="patent-analyst",
        )

        assert "task_id" in result
        assert result["model"] is not None

    def test_multiple_extensions_interaction(self, task_tool):
        """测试多个扩展模块同时工作"""
        result = task_tool.execute(
            prompt="多模块集成测试",
            tools=["patent_search", "web_search"],
            fork_context={"parent_messages": []},
            agent_type="legal-researcher",
            model="sonnet",
        )

        assert "task_id" in result
        assert "status" in result
        assert "agent_id" in result
        assert "filtered_tools" in result
