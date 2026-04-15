"""
T1-1: 测试任务工具模块目录结构创建

此测试验证所有必要的目录和__init__.py文件是否被正确创建。
"""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestDirectoryStructure:
    """测试目录结构是否正确创建"""

    def test_task_tool_directory_exists(self):
        """测试core/agents/task_tool目录是否存在"""
        task_tool_dir = project_root / "core" / "agents" / "task_tool"
        assert task_tool_dir.exists(), f"目录 {task_tool_dir} 不存在"
        assert task_tool_dir.is_dir(), f"{task_tool_dir} 不是目录"

    def test_task_directory_exists(self):
        """测试core/task目录是否存在"""
        task_dir = project_root / "core" / "task"
        assert task_dir.exists(), f"目录 {task_dir} 不存在"
        assert task_dir.is_dir(), f"{task_dir} 不是目录"

    def test_agents_task_tool_test_directory_exists(self):
        """测试tests/agents/task_tool目录是否存在"""
        test_dir = project_root / "tests" / "agents" / "task_tool"
        assert test_dir.exists(), f"目录 {test_dir} 不存在"
        assert test_dir.is_dir(), f"{test_dir} 不是目录"

    def test_task_test_directory_exists(self):
        """测试tests/task目录是否存在"""
        test_dir = project_root / "tests" / "task"
        assert test_dir.exists(), f"目录 {test_dir} 不存在"
        assert test_dir.is_dir(), f"{test_dir} 不是目录"

    def test_task_tool_init_file_exists(self):
        """测试core/agents/task_tool/__init__.py是否存在"""
        init_file = project_root / "core" / "agents" / "task_tool" / "__init__.py"
        assert init_file.exists(), f"文件 {init_file} 不存在"
        assert init_file.is_file(), f"{init_file} 不是文件"

    def test_task_init_file_exists(self):
        """测试core/task/__init__.py是否存在"""
        init_file = project_root / "core" / "task" / "__init__.py"
        assert init_file.exists(), f"文件 {init_file} 不存在"
        assert init_file.is_file(), f"{init_file} 不是文件"

    def test_agents_task_tool_test_init_file_exists(self):
        """测试tests/agents/task_tool/__init__.py是否存在"""
        init_file = project_root / "tests" / "agents" / "task_tool" / "__init__.py"
        assert init_file.exists(), f"文件 {init_file} 不存在"
        assert init_file.is_file(), f"{init_file} 不是文件"

    def test_task_test_init_file_exists(self):
        """测试tests/task/__init__.py是否存在"""
        init_file = project_root / "tests" / "task" / "__init__.py"
        assert init_file.exists(), f"文件 {init_file} 不存在"
        assert init_file.is_file(), f"{init_file} 不是文件"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
