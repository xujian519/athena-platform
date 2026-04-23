"""Fork上下文集成测试

测试ForkContextBuilder与TaskTool的集成功能。
"""


import pytest

from core.framework.agents.fork_context_builder import ForkContext
from core.framework.agents.task_tool.task_tool import TaskTool


class TestForkContextIntegration:
    """Fork上下文集成测试套件"""

    @pytest.fixture
    def task_tool(self):
        """创建TaskTool实例"""
        return TaskTool()

    def test_fork_context_builder_initialization(self, task_tool):
        """测试ForkContextBuilder初始化"""
        assert task_tool.fork_context_builder is not None

    def test_build_basic_fork_context(self, task_tool):
        """测试基本Fork上下文构建"""
        fork_ctx = task_tool.fork_context_builder.build(
            prompt="测试任务",
            context={},
        )

        assert fork_ctx is not None
        assert isinstance(fork_ctx, ForkContext)

    def test_fork_context_with_system_prompt(self, task_tool):
        """测试带有系统提示词的Fork上下文构建"""
        fork_ctx = task_tool.fork_context_builder.build(
            prompt="专利分析任务",
            context={"system_prompt": "你是一位专利分析师"},
        )

        assert fork_ctx is not None
        assert len(fork_ctx.system_prompt) > 0
        assert len(fork_ctx.prompt_messages) > 0

    def test_fork_context_serialization(self, task_tool):
        """测试Fork上下文序列化"""
        fork_ctx = task_tool.fork_context_builder.build(
            prompt="序列化测试",
            context={},
        )

        assert fork_ctx.to_dict() is not None
        json_str = fork_ctx.to_json()
        assert json_str is not None

        assert isinstance(json_str, str)

    def test_fork_context_deserialization(self, task_tool):
        """测试Fork上下文反序列化"""
        fork_ctx = task_tool.fork_context_builder.build(
            prompt="反序列化测试",
            context={},
        )

        fork_ctx_dict = fork_ctx.to_dict()
        json_str = fork_ctx.to_json()
        fork_ctx_from_dict = ForkContext.from_dict(fork_ctx_dict)
        fork_ctx_from_json = ForkContext.from_json(json_str)

        assert fork_ctx_from_dict.fork_context_messages == fork_ctx.fork_context_messages
        assert fork_ctx_from_json.fork_context_messages == fork_ctx.fork_context_messages

    def test_task_execution_with_fork_context(self, task_tool):
        """测试带有Fork上下文的任务执行"""
        result = task_tool.execute(
            prompt="需要Fork上下文的任务",
            tools=[],
            fork_context={"parent_messages": []},
        )

        assert "task_id" in result
        assert "status" in result

    def test_task_execution_without_fork_context(self, task_tool):
        """测试没有Fork上下文的任务执行"""
        result = task_tool.execute(
            prompt="普通任务",
            tools=[],
        )

        assert "task_id" in result
        assert "status" in result

    def test_fork_context_from_agent_config(self, task_tool):
        """测试从代理配置构建Fork上下文"""
        result = task_tool.execute(
            prompt="代理配置任务",
            tools=[],
            agent_type="patent-analyst",
        )

        assert "task_id" in result

    def test_fork_context_isolation(self, task_tool):
        """测试Fork上下文隔离"""
        ctx1 = task_tool.fork_context_builder.build(
            prompt="上下文1",
            context={"var": "value1"},
        )

        ctx2 = task_tool.fork_context_builder.build(
            prompt="上下文2",
            context={"var": "value2"},
        )

        assert ctx1.prompt_messages != ctx2.prompt_messages
        assert ctx1.to_dict() != ctx2.to_dict()

    def test_empty_fork_context_handling(self, task_tool):
        """测试空Fork上下文的处理"""
        result = task_tool.execute(
            prompt="空上下文测试",
            tools=[],
            fork_context=None,
        )

        assert "task_id" in result
        assert result["status"] == "completed"
