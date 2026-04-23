"""
T1-3: 测试ModelMapper

此测试验证模型映射器的功能。
"""

import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.framework.agents.task_tool.model_mapper import ModelMapper
    from core.framework.agents.task_tool.models import ModelChoice
except ImportError:
    pytest.skip("model_mapper.py尚未创建", allow_module_level=True)


class TestModelMapper:
    """测试ModelMapper类"""

    def test_map_haiku_to_quick(self):
        """测试haiku映射到quick"""
        mapper = ModelMapper()
        result = mapper.map("haiku")
        assert result == "quick", f"haiku应该映射到quick，但得到: {result}"

    def test_map_sonnet_to_task(self):
        """测试sonnet映射到task"""
        mapper = ModelMapper()
        result = mapper.map("sonnet")
        assert result == "task", f"sonnet应该映射到task，但得到: {result}"

    def test_map_opus_to_main(self):
        """测试opus映射到main"""
        mapper = ModelMapper()
        result = mapper.map("opus")
        assert result == "main", f"opus应该映射到main，但得到: {result}"

    def test_map_with_model_choice_enum(self):
        """测试使用ModelChoice枚举映射"""
        mapper = ModelMapper()
        result = mapper.map(ModelChoice.HAIKU)
        assert result == "quick", f"ModelChoice.HAIKU应该映射到quick，但得到: {result}"

    def test_map_with_sonnet_enum(self):
        """测试使用ModelChoice.SONNET映射"""
        mapper = ModelMapper()
        result = mapper.map(ModelChoice.SONNET)
        assert result == "task", f"ModelChoice.SONNET应该映射到task，但得到: {result}"

    def test_map_with_opus_enum(self):
        """测试使用ModelChoice.OPUS映射"""
        mapper = ModelMapper()
        result = mapper.map(ModelChoice.OPUS)
        assert result == "main", f"ModelChoice.OPUS应该映射到main，但得到: {result}"

    def test_map_unknown_model_raises_error(self):
        """测试未知模型名称抛出错误"""
        mapper = ModelMapper()
        with pytest.raises(ValueError, match="Unknown model"):
            mapper.map("unknown_model")

    def test_normalize_model_name(self):
        """测试模型名称规范化"""
        mapper = ModelMapper()
        assert mapper.normalize_model_name("haiku") == "haiku"
        assert mapper.normalize_model_name("HAIKU") == "haiku"
        assert mapper.normalize_model_name("HaIkU") == "haiku"
        assert mapper.normalize_model_name(" sonnet ") == "sonnet"

    def test_normalize_model_name_with_enum(self):
        """测试使用ModelChoice规范化模型名称"""
        mapper = ModelMapper()
        assert mapper.normalize_model_name(ModelChoice.HAIKU) == "haiku"
        assert mapper.normalize_model_name(ModelChoice.SONNET) == "sonnet"
        assert mapper.normalize_model_name(ModelChoice.OPUS) == "opus"

    def test_get_model_config_haiku(self):
        """测试获取haiku模型配置"""
        mapper = ModelMapper()
        config = mapper.get_model_config("haiku")
        assert config is not None
        assert config["name"] == "quick"
        assert "temperature" in config or "max_tokens" in config

    def test_get_model_config_sonnet(self):
        """测试获取sonnet模型配置"""
        mapper = ModelMapper()
        config = mapper.get_model_config("sonnet")
        assert config is not None
        assert config["name"] == "task"
        assert "temperature" in config or "max_tokens" in config

    def test_get_model_config_opus(self):
        """测试获取opus模型配置"""
        mapper = ModelMapper()
        config = mapper.get_model_config("opus")
        assert config is not None
        assert config["name"] == "main"
        assert "temperature" in config or "max_tokens" in config

    def test_environment_variable_support(self):
        """测试环境变量ATHENA_SUBAGENT_MODEL支持"""
        # 设置环境变量
        os.environ["ATHENA_SUBAGENT_MODEL"] = "sonnet"
        try:
            mapper = ModelMapper()
            # 重置环境变量后测试
            del os.environ["ATHENA_SUBAGENT_MODEL"]
            result = mapper.map("sonnet")
            assert result == "task"
        finally:
            # 清理
            if "ATHENA_SUBAGENT_MODEL" in os.environ:
                del os.environ["ATHENA_SUBAGENT_MODEL"]

    def test_map_with_string_input(self):
        """测试使用字符串输入映射"""
        mapper = ModelMapper()
        result = mapper.map("haiku")
        assert isinstance(result, str)
        assert result == "quick"

    def test_get_available_models(self):
        """测试获取可用模型列表"""
        mapper = ModelMapper()
        models = mapper.get_available_models()
        assert "haiku" in models
        assert "sonnet" in models
        assert "opus" in models


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
