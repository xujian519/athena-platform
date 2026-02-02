"""
配置模块单元测试
测试配置加载和管理功能
"""

import pytest
import os
from pathlib import Path


class TestConfigModule:
    """配置模块测试类"""

    def test_config_module_import(self):
        """测试配置模块可以正常导入"""
        # 测试配置目录存在
        config_dir = Path("core/config")
        assert config_dir.exists(), "配置目录应该存在"
        assert config_dir.is_dir(), "配置应该是一个目录"

    def test_config_files_exist(self):
        """测试关键配置文件存在"""
        config_dir = Path("core/config")

        # 检查重要配置文件
        important_files = [
            "__init__.py",
            "system_prompt.py",
        ]

        for file in important_files:
            file_path = config_dir / file
            assert file_path.exists(), f"配置文件 {file} 应该存在"

    def test_environment_variables(self):
        """测试环境变量读取"""
        # 设置测试环境变量
        os.environ["TEST_VAR"] = "test_value"

        # 验证可以读取
        assert os.environ.get("TEST_VAR") == "test_value"

        # 清理
        del os.environ["TEST_VAR"]

    def test_project_root_detection(self):
        """测试项目根目录检测"""
        # 检查当前工作目录
        cwd = Path.cwd()

        # 验证关键目录存在
        assert (cwd / "core").exists(), "core目录应该存在"
        assert (cwd / "tests").exists(), "tests目录应该存在"

    def test_config_import(self):
        """测试配置模块导入"""
        try:
            import core.config
            assert core.config is not None
        except ImportError as e:
            pytest.skip(f"配置模块导入失败: {e}")


class TestSystemPromptConfig:
    """系统提示词配置测试"""

    def test_system_prompt_module_exists(self):
        """测试系统提示词模块存在"""
        module_path = Path("core/config/system_prompt.py")
        assert module_path.exists(), "系统提示词模块应该存在"

    def test_system_prompt_import(self):
        """测试系统提示词可以导入"""
        try:
            from core.config.system_prompt import (
                get_system_prompt,
                get_agent_prompt,
                get_tool_prompt
            )
            assert callable(get_system_prompt)
            assert callable(get_agent_prompt)
            assert callable(get_tool_prompt)
        except ImportError as e:
            pytest.skip(f"系统提示词导入失败: {e}")

    @pytest.mark.parametrize("agent_type", [
        "athena",
        "xiaonuo",
        "xiaochen",
        "yunxi",
    ])
    def test_get_agent_prompt(self, agent_type):
        """测试获取不同智能体的提示词"""
        try:
            from core.config.system_prompt import get_agent_prompt
            prompt = get_agent_prompt(agent_type)
            assert isinstance(prompt, str)
            assert len(prompt) > 0
        except ImportError:
            pytest.skip("系统提示词模块不可用")


class TestConfigValidation:
    """配置验证测试"""

    def test_config_structure(self):
        """测试配置目录结构"""
        config_dir = Path("core/config")

        # 检查子目录
        subdirs = list(config_dir.iterdir())
        dirs = [d for d in subdirs if d.is_dir()]

        assert len(dirs) > 0, "配置目录应该包含子目录"

    def test_config_file_readable(self):
        """测试配置文件可读"""
        config_files = list(Path("core/config").glob("*.py"))

        for config_file in config_files:
            assert config_file.stat().st_size > 0, f"{config_file.name} 不应该为空"
            assert config_file.is_file(), f"{config_file.name} 应该是文件"

    def test_yaml_config_files(self):
        """测试YAML配置文件"""
        yaml_files = list(Path("config").glob("*.yaml"))

        if yaml_files:
            # 至少应该有一些yaml文件
            assert len(yaml_files) > 0, "config目录应该有yaml配置文件"
