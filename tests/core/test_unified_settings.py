"""
统一配置管理测试

测试配置加载、验证和继承机制
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config.unified_settings import Settings, settings


class TestSettingsSingleton:
    """测试配置单例模式"""

    def test_singleton_same_instance(self):
        """测试单例返回相同实例"""
        settings1 = Settings.get_instance()
        settings2 = Settings.get_instance()
        assert settings1 is settings2

    def test_reset_instance(self):
        """测试重置单例"""
        Settings.reset_instance()
        new_settings = Settings.get_instance()
        assert new_settings is not None


class TestDatabaseConfig:
    """测试数据库配置"""

    def test_database_url_format(self):
        """测试数据库URL格式"""
        assert settings.database_url.startswith("postgresql://")
        assert "athena" in settings.database_url

    def test_database_url_components(self):
        """测试数据库URL组件"""
        assert settings.database_host == "localhost"
        assert settings.database_port == 5432
        assert settings.database_user == "athena"
        assert settings.database_name in ["athena", "athena_dev", "athena_test"]


class TestRedisConfig:
    """测试Redis配置"""

    def test_redis_url_format(self):
        """测试Redis URL格式"""
        assert settings.redis_url.startswith("redis://")

    def test_redis_config_components(self):
        """测试Redis配置组件"""
        assert settings.redis_host == "localhost"
        assert settings.redis_port == 6379
        assert settings.redis_db == 0


class TestLLMConfig:
    """测试LLM配置"""

    def test_llm_provider(self):
        """测试LLM提供商"""
        assert settings.llm_provider in ["openai", "anthropic", "deepseek", "glm", "ollama"]

    def test_llm_model(self):
        """测试LLM模型"""
        assert settings.llm_model is not None
        assert len(settings.llm_model) > 0

    def test_llm_temperature(self):
        """测试LLM温度"""
        assert 0.0 <= settings.llm_temperature <= 2.0


class TestConfigLoading:
    """测试配置加载"""

    def test_load_development_config(self):
        """测试加载开发环境配置"""
        dev_settings = Settings.load(environment="development")
        assert dev_settings.environment == "development"
        assert dev_settings.debug is True

    def test_load_test_config(self):
        """测试加载测试环境配置"""
        test_settings = Settings.load(environment="test")
        assert test_settings.environment == "test"
        assert test_settings.database_name == "athena_test"

    def test_load_production_config(self):
        """测试加载生产环境配置"""
        prod_settings = Settings.load(environment="production")
        assert prod_settings.environment == "production"
        assert prod_settings.debug is False

    def test_load_with_service(self):
        """测试加载服务配置"""
        gateway_settings = Settings.load(
            environment="development",
            service="gateway"
        )
        assert gateway_settings.gateway_port == 8005


class TestConfigValidation:
    """测试配置验证"""

    def test_invalid_llm_api_key(self):
        """测试无效的LLM API密钥"""
        with pytest.raises(ValueError, match="LLM API key"):
            Settings(llm_provider="anthropic", llm_api_key="short")

    def test_valid_llm_api_key(self):
        """测试有效的LLM API密钥"""
        # Ollama不需要API密钥
        settings_ollama = Settings(llm_provider="ollama", llm_api_key="")
        assert settings_ollama.llm_provider == "ollama"

        # 其他provider需要API密钥
        settings_with_key = Settings(
            llm_provider="anthropic",
            llm_api_key="sk-1234567890abcdef"
        )
        assert len(settings_with_key.llm_api_key) >= 10


class TestConfigExport:
    """测试配置导出"""

    def test_to_dict(self):
        """测试导出为字典"""
        config_dict = settings.to_dict()
        assert isinstance(config_dict, dict)
        assert "database_host" in config_dict
        assert "redis_host" in config_dict

    def test_model_dump(self):
        """测试Pydantic model_dump"""
        config_dict = settings.model_dump()
        assert isinstance(config_dict, dict)
        assert len(config_dict) > 0


class TestConfigDefaults:
    """测试配置默认值"""

    def test_default_environment(self):
        """测试默认环境"""
        assert settings.environment in ["development", "test", "production"]

    def test_default_database_port(self):
        """测试默认数据库端口"""
        assert settings.database_port == 5432

    def test_default_redis_port(self):
        """测试默认Redis端口"""
        assert settings.redis_port == 6379

    def test_default_gateway_port(self):
        """测试默认Gateway端口"""
        assert settings.gateway_port == 8005


class TestConfigFiles:
    """测试配置文件"""

    def test_base_config_exists(self):
        """测试基础配置文件存在"""
        base_dir = Path("config/base")
        assert base_dir.exists()

        required_files = [
            "database.yml",
            "redis.yml",
            "llm.yml",
            "gateway.yml",
            "agents.yml"
        ]

        for file in required_files:
            assert (base_dir / file).exists(), f"缺少基础配置: {file}"

    def test_environment_config_exists(self):
        """测试环境配置文件存在"""
        env_dir = Path("config/environments")
        assert env_dir.exists()

        required_files = [
            "development.yml",
            "test.yml",
            "production.yml"
        ]

        for file in required_files:
            assert (env_dir / file).exists(), f"缺少环境配置: {file}"

    def test_service_config_exists(self):
        """测试服务配置文件存在"""
        service_dir = Path("config/services")
        assert service_dir.exists()

        required_files = [
            "gateway.yml",
            "xiaona.yml",
            "xiaonuo.yml",
            "yunxi.yml"
        ]

        for file in required_files:
            assert (service_dir / file).exists(), f"缺少服务配置: {file}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
