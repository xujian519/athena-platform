"""
T1-2: 测试数据模型定义

此测试验证所有核心数据模型是否被正确定义。
"""

import sys
from enum import Enum
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.framework.agents.task_tool.models import (
        BackgroundTask,
        ModelChoice,
        TaskInput,
        TaskOutput,
        TaskRecord,
        TaskStatus,
    )
except ImportError:
    pytest.skip("models.py尚未创建", allow_module_level=True)


class TestTaskStatus:
    """测试TaskStatus枚举"""

    def test_task_status_is_enum(self):
        """测试TaskStatus是否为枚举类型"""
        assert issubclass(TaskStatus, Enum), "TaskStatus应该是Enum的子类"

    def test_task_status_has_required_values(self):
        """测试TaskStatus是否有必需的枚举值"""
        required_values = ["pending", "running", "completed", "failed", "cancelled"]
        actual_values = [status.value for status in TaskStatus]
        for value in required_values:
            assert value in actual_values, f"TaskStatus缺少枚举值: {value}"


class TestModelChoice:
    """测试ModelChoice枚举"""

    def test_model_choice_is_enum(self):
        """测试ModelChoice是否为枚举类型"""
        assert issubclass(ModelChoice, Enum), "ModelChoice应该是Enum的子类"

    def test_model_choice_has_required_values(self):
        """测试ModelChoice是否有必需的枚举值"""
        required_values = ["haiku", "sonnet", "opus"]
        actual_values = [model.value for model in ModelChoice]
        for value in required_values:
            assert value in actual_values, f"ModelChoice缺少枚举值: {value}"


class TestTaskInput:
    """测试TaskInput数据类"""

    def test_task_input_is_dataclass(self):
        """测试TaskInput是否为数据类"""
        assert hasattr(TaskInput, "__dataclass_fields__"), "TaskInput应该是dataclass"

    def test_task_input_has_prompt_field(self):
        """测试TaskInput是否有prompt字段"""
        assert "prompt" in TaskInput.__dataclass_fields__, "TaskInput应该有prompt字段"

    def test_task_input_has_tools_field(self):
        """测试TaskInput是否有tools字段"""
        assert "tools" in TaskInput.__dataclass_fields__, "TaskInput应该有tools字段"

    def test_task_input_prompt_is_string(self):
        """测试TaskInput的prompt字段类型"""
        task_input = TaskInput(prompt="test", tools=[])
        assert isinstance(task_input.prompt, str), "prompt字段应该是str类型"

    def test_task_input_tools_is_list(self):
        """测试TaskInput的tools字段类型"""
        task_input = TaskInput(prompt="test", tools=["tool1", "tool2"])
        assert isinstance(task_input.tools, list), "tools字段应该是list类型"


class TestTaskOutput:
    """测试TaskOutput数据类"""

    def test_task_output_is_dataclass(self):
        """测试TaskOutput是否为数据类"""
        assert hasattr(TaskOutput, "__dataclass_fields__"), "TaskOutput应该是dataclass"

    def test_task_output_has_content_field(self):
        """测试TaskOutput是否有content字段"""
        assert "content" in TaskOutput.__dataclass_fields__, "TaskOutput应该有content字段"

    def test_task_output_has_tool_uses_field(self):
        """测试TaskOutput是否有tool_uses字段"""
        assert "tool_uses" in TaskOutput.__dataclass_fields__, "TaskOutput应该有tool_uses字段"

    def test_task_output_has_duration_field(self):
        """测试TaskOutput是否有duration字段"""
        assert "duration" in TaskOutput.__dataclass_fields__, "TaskOutput应该有duration字段"

    def test_task_output_fields_types(self):
        """测试TaskOutput各字段的类型"""
        output = TaskOutput(content="test content", tool_uses=5, duration=1.5, success=True)
        assert isinstance(output.content, str), "content字段应该是str类型"
        assert isinstance(output.tool_uses, int), "tool_uses字段应该是int类型"
        assert isinstance(output.duration, float), "duration字段应该是float类型"
        assert isinstance(output.success, bool), "success字段应该是bool类型"


class TestTaskRecord:
    """测试TaskRecord数据类"""

    def test_task_record_is_dataclass(self):
        """测试TaskRecord是否为数据类"""
        assert hasattr(TaskRecord, "__dataclass_fields__"), "TaskRecord应该是dataclass"

    def test_task_record_has_required_fields(self):
        """测试TaskRecord是否有必需的字段"""
        required_fields = [
            "task_id",
            "agent_id",
            "model",
            "status",
            "input",
            "output",
            "created_at",
            "updated_at",
        ]
        for field in required_fields:
            assert field in TaskRecord.__dataclass_fields__, f"TaskRecord应该有{field}字段"

    def test_task_record_fields_types(self):
        """测试TaskRecord各字段的类型"""
        record = TaskRecord(
            task_id="test-id",
            agent_id="agent-1",
            model="haiku",
            status=TaskStatus.PENDING,
            input=TaskInput(prompt="test", tools=[]),
            output=None,
            created_at="2026-04-05T00:00:00Z",
            updated_at="2026-04-05T00:00:00Z",
        )
        assert isinstance(record.task_id, str), "task_id字段应该是str类型"
        assert isinstance(record.agent_id, str), "agent_id字段应该是str类型"
        assert isinstance(record.status, TaskStatus), "status字段应该是TaskStatus类型"


class TestBackgroundTask:
    """测试BackgroundTask数据类"""

    def test_background_task_is_dataclass(self):
        """测试BackgroundTask是否为数据类"""
        assert hasattr(BackgroundTask, "__dataclass_fields__"), "BackgroundTask应该是dataclass"

    def test_background_task_has_required_fields(self):
        """测试BackgroundTask是否有必需的字段"""
        required_fields = ["task_id", "status", "future", "agent_id", "created_at", "updated_at"]
        for field in required_fields:
            assert field in BackgroundTask.__dataclass_fields__, f"BackgroundTask应该有{field}字段"

    def test_background_task_status_is_task_status(self):
        """测试BackgroundTask的status字段类型"""
        assert (
            BackgroundTask.__dataclass_fields__["status"].type == TaskStatus
        ), "BackgroundTask的status字段应该是TaskStatus类型"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
