"""
T1-6, T1-7, T1-8: 测试TaskTool

此测试验证TaskTool的核心功能。
"""

import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.agents.task_tool.task_tool import TaskTool
    from core.task.task_store import TaskStore
except ImportError:
    pytest.skip("task_tool.py尚未创建", allow_module_level=True)


class TestTaskTool:
    """测试TaskTool类"""

    def test_init_creates_tool(self):
        """测试初始化创建工具"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"cold_db_path": f"{temp_dir}/test.db"}
            tool = TaskTool(config=config)
            assert tool is not None
            assert isinstance(tool, TaskTool)

    def test_validate_input(self):
        """测试输入验证"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"cold_db_path": f"{temp_dir}/test.db"}
            tool = TaskTool(config=config)

            # 有效输入
            tool._validate_input("test prompt", ["tool1"])

            # 无效提示词
            with pytest.raises(ValueError):
                tool._validate_input("", ["tool1"])

            # 无效工具列表
            with pytest.raises(ValueError):
                tool._validate_input("test", "tool1")

    def test_select_model(self):
        """测试模型选择"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"cold_db_path": f"{temp_dir}/test.db"}
            tool = TaskTool(config=config)

            # 指定模型
            model = tool._select_model("haiku", None)
            assert model == "quick"

            # 根据代理类型选择
            model = tool._select_model(None, "analysis")
            assert model == "task"

            model = tool._select_model(None, "search")
            assert model == "quick"

            model = tool._select_model(None, "legal")
            assert model == "main"

            # 默认选择
            model = tool._select_model(None, None)
            assert model == "task"

    def test_generate_agent_id(self):
        """测试代理ID生成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"cold_db_path": f"{temp_dir}/test.db"}
            tool = TaskTool(config=config)

            # 生成ID
            agent_id = tool._generate_agent_id("analysis")
            assert agent_id.startswith("analysis-")

            # 无类型
            agent_id = tool._generate_agent_id()
            assert agent_id.startswith("default-")

    def test_execute_sync(self):
        """测试同步执行"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"cold_db_path": f"{temp_dir}/test.db"}
            tool = TaskTool(config=config)

            result = tool.execute(
                prompt="test prompt",
                tools=["tool1"],
                background=False,
            )

            assert "task_id" in result
            assert "status" in result
            assert "agent_id" in result
            assert "model" in result

    def test_execute_with_model_selection(self):
        """测试带模型选择的执行"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"cold_db_path": f"{temp_dir}/test.db"}
            tool = TaskTool(config=config)

            result = tool.execute(
                prompt="test prompt",
                tools=["tool1"],
                model="haiku",
            )

            assert result["model"] == "quick"

    def test_execute_with_agent_type(self):
        """测试带代理类型的执行"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"cold_db_path": f"{temp_dir}/test.db"}
            tool = TaskTool(config=config)

            result = tool.execute(
                prompt="test prompt",
                tools=["tool1"],
                agent_type="search",
            )

            assert result["agent_id"].startswith("search-")
            assert result["model"] == "quick"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
