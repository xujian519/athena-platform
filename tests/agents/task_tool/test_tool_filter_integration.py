"""ToolFilter集成测试

测试ToolFilter和SubagentRegistry与TaskTool的集成功能。
"""

import pytest

from core.agents.task_tool.task_tool import TaskTool


class TestToolFilterIntegration:
    """ToolFilter集成测试套件"""

    @pytest.fixture
    def task_tool(self):
        """创建TaskTool实例"""
        return TaskTool()

    def test_tool_filter_initialization(self, task_tool):
        """测试ToolFilter初始化"""
        assert task_tool.tool_filter is not None
        assert task_tool.subagent_registry is not None

    def test_subagent_registry_initialization(self, task_tool):
        """测试SubagentRegistry初始化"""
        assert task_tool.subagent_registry.get_agent_count() == 4

    def test_sync_execution_with_filtering(self, task_tool):
        """测试同步执行时的工具过滤"""
        result = task_tool.execute(
            prompt="专利分析任务",
            tools=[
                "patent_search",
                "code_analyzer",
                "knowledge_graph",
                "web_search",
            ],
            agent_type="patent-analyst",
            background=False,
        )

        assert "task_id" in result
        assert "status" in result
        assert "filtered_tools" in result

        filtered = result["filtered_tools"]
        assert len(filtered) <= 4

    def test_background_execution_with_filtering(self, task_tool):
        """测试后台执行时的工具过滤"""
        result = task_tool.execute(
            prompt="专利检索任务",
            tools=[
                "patent_search",
                "web_search",
                "knowledge_graph",
            ],
            agent_type="patent-searcher",
            background=True,
        )

        assert "task_id" in result
        assert "filtered_tools" in result
        assert result["status"] == "submitted"

    def test_model_selection_via_registry(self, task_tool):
        """测试通过注册表选择模型"""
        result = task_tool.execute(
            prompt="法律分析",
            tools=[],
            agent_type="legal-researcher",
            background=False,
        )

        assert "model" in result

    def test_unknown_agent_type_handling(self, task_tool):
        """测试未知代理类型的处理"""
        result = task_tool.execute(
            prompt="未知代理任务",
            tools=[],
            agent_type="unknown-agent",
            background=False,
        )

        assert "task_id" in result
        assert "model" in result

    def test_tool_wildcard_filtering(self, task_tool):
        """测试通配符工具过滤"""
        result = task_tool.execute(
            prompt="通配符测试",
            tools=[
                "patent_search",
                "patent_analyzer",
                "web_search",
            ],
            agent_type="patent-analyst",
            background=False,
        )

        assert "filtered_tools" in result
        filtered = result["filtered_tools"]

        allowed_tools = task_tool.subagent_registry.get_agent("patent-analyst").allowed_tools
        for tool in filtered:
            assert tool in allowed_tools or tool in allowed_tools

    def test_model_override(self, task_tool):
        """测试模型覆盖"""
        result = task_tool.execute(
            prompt="模型覆盖测试",
            tools=[],
            model="haiku",
            agent_type="patent-analyst",
            background=False,
        )

        assert result["model"] is not None
