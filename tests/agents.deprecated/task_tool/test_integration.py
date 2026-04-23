"""TaskTool-ToolManager集成测试

测试TaskTool与ToolManager系统的集成功能。
"""


import pytest

from core.framework.agents.task_tool.task_tool import TaskTool
from core.framework.agents.task_tool.tool_manager_adapter import TaskToolAdapter
from core.tools.base import ToolRegistry
from core.tools.tool_manager import ToolManager


class TestTaskToolIntegration:
    """TaskTool集成测试套件"""

    @pytest.fixture
    def task_tool(self):
        """创建TaskTool实例"""
        return TaskTool()

    @pytest.fixture
    def tool_manager(self):
        """创建ToolManager实例"""
        registry = ToolRegistry()
        return ToolManager(registry)

    @pytest.fixture
    def adapter(self, task_tool, tool_manager):
        """创建TaskToolAdapter实例"""
        return TaskToolAdapter(
            task_tool=task_tool,
            tool_manager=tool_manager,
        )

    def test_tool_definition_conversion(self, task_tool):
        """测试TaskTool转换为ToolDefinition"""
        tool_def = task_tool.to_tool_definition()

        assert tool_def.tool_id == "task-tool"
        assert tool_def.name == "Task Tool"
        assert tool_def.implementation_type == "function"
        assert tool_def.handler is not None
        assert "prompt" in tool_def.required_params
        assert "background" in tool_def.optional_params

    def test_adapter_registration(self, adapter):
        """测试适配器注册TaskTool"""
        result = adapter.register()

        assert result is True

        tool_def = adapter.registry.get_tool("task-tool")
        assert tool_def is not None
        assert tool_def.tool_id == "task-tool"

        task_group = adapter.tool_manager.get_group("task-tools")
        assert task_group is not None
        assert task_group.definition.name == "task-tools"

    def test_tool_group_activation(self, adapter):
        """测试工具组激活"""
        adapter.register()

        result = adapter.tool_manager.activate_group("task-tools")
        assert result is True
        assert adapter.tool_manager.active_group == "task-tools"

    def test_task_execution_via_adapter(self, adapter):
        """测试通过适配器执行任务"""
        result = adapter.execute_task(
            prompt="测试任务",
            tools=["tool1", "tool2"],
            background=False,
        )

        assert "task_id" in result
        assert "status" in result
        assert "agent_id" in result

    def test_background_task_execution(self, adapter):
        """测试后台任务执行"""
        result = adapter.execute_task(
            prompt="后台任务",
            tools=[],
            background=True,
        )

        assert "task_id" in result
        assert result["status"] in ["submitted", "completed"]

    def test_model_selection(self, adapter):
        """测试模型选择"""
        result = adapter.execute_task(
            prompt="分析任务",
            tools=[],
            model="sonnet",
        )

        assert result["model"] is not None

    def test_agent_type_selection(self, adapter):
        """测试代理类型选择"""
        result = adapter.execute_task(
            prompt="法律分析",
            tools=[],
            agent_type="legal",
        )

        assert result["agent_id"] is not None
        assert "legal" in result["agent_id"]

    @pytest.mark.asyncio
    async def test_tool_group_auto_activation(self, adapter):
        """测试工具组自动激活"""
        adapter.register()

        group_name = await adapter.tool_manager.auto_activate_group_for_task(
            task_description="执行一个子代理任务",
            task_type="task_execution",
        )

        assert group_name == "task-tools"

    def test_invalid_input_handling(self, task_tool):
        """测试无效输入处理"""
        with pytest.raises(ValueError, match="Prompt不能为空"):
            task_tool.execute(prompt="", tools=[])

        with pytest.raises(ValueError, match="Tools必须是列表"):
            task_tool.execute(prompt="test", tools="invalid")
