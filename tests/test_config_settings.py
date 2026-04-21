"""
配置管理工具单元测试
Unit Tests for Configuration Management
"""
import pytest
import os
import tempfile
from pathlib import Path
from core.config.settings import Settings, get_settings, reload_settings
from core.config.config_loader import (
    load_base_config,
    load_environment_config,
    load_full_config,
    create_settings_from_config
)
from core.config.validator import ConfigValidator, validate_settings


class TestSettings:
    """Settings类测试"""

    def test_settings_creation(self):
        """测试Settings创建"""
        settings = Settings()
        assert settings.environment == "development"
        assert settings.database_host == "localhost"
        assert settings.database_port == 5432

    def test_database_url_property(self):
        """测试database_url属性"""
        settings = Settings(
            database_host="localhost",
            database_port=5432,
            database_user="test",
            database_password="test123",
            database_name="testdb"
        )
        url = settings.database_url
        assert url == "postgresql://test:test123@localhost:5432/testdb"

    def test_redis_url_property(self):
        """测试redis_url属性"""
        settings = Settings(
            redis_host="localhost",
            redis_port=6379,
            redis_db=0,
            redis_password=""
        )
        url = settings.redis_url
        assert url == "redis://localhost:6379/0"

    def test_qdrant_url_property(self):
        """测试qdrant_url属性"""
        settings = Settings(
            qdrant_host="localhost",
            qdrant_port=6333,
            qdrant_https=False
        )
        url = settings.qdrant_url
        assert url == "http://localhost:6333"

    def test_singleton_pattern(self):
        """测试单例模式"""
        settings1 = Settings.get_instance()
        settings2 = Settings.get_instance()
        assert settings1 is settings2

    def test_settings_reset(self):
        """测试重置单例"""
        settings1 = Settings.get_instance()
        Settings.reset_instance()
        settings2 = Settings.get_instance()
        assert settings1 is not settings2

    def test_snapshot(self):
        """测试配置快照"""
        settings = Settings(environment="test")
        snapshot = settings.snapshot()
        assert snapshot["environment"] == "test"
        assert "database_host" in snapshot


class TestConfigLoader:
    """配置加载器测试"""

    def test_load_base_config(self):
        """测试加载基础配置"""
        config = load_base_config()
        assert isinstance(config, dict)
        # 如果配置文件存在，应该包含配置
        if Path("config/base").exists():
            assert len(config) > 0

    def test_load_environment_config(self):
        """测试加载环境配置"""
        config = load_environment_config("development")
        assert isinstance(config, dict)

    def test_load_full_config(self):
        """测试加载完整配置"""
        config = load_full_config("development")
        assert isinstance(config, dict)

    def test_create_settings_from_config(self):
        """测试从配置创建Settings"""
        settings = create_settings_from_config("development")
        assert isinstance(settings, Settings)
        assert settings.environment == "development"


class TestConfigValidator:
    """配置验证器测试"""

    def test_validate_valid_settings(self):
        """测试验证有效配置"""
        settings = Settings(
            environment="development",
            database_password="test12345",
            llm_api_key="test_api_key_123"
        )
        result = ConfigValidator.validate_settings(settings)
        assert result is True

    def test_validate_invalid_port(self):
        """测试无效端口号"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(database_port=99999)

    def test_validate_invalid_temperature(self):
        """测试无效温度参数"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(llm_temperature=5.0)

    def test_production_requires_api_key(self):
        """测试生产环境需要API密钥"""
        settings = Settings(
            environment="production",
            llm_api_key=""
        )
        result = ConfigValidator.validate_settings(settings)
        assert result is False


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 加载配置
        config = load_full_config("development")

        # 2. 创建Settings
        settings = create_settings_from_config("development")

        # 3. 验证配置
        is_valid = validate_settings(settings)

        assert isinstance(config, dict)
        assert isinstance(settings, Settings)
        # 如果环境配置有效，验证应该通过
        if settings.llm_api_key:
            assert is_valid is True

    def test_save_and_load_yaml(self):
        """测试保存和加载YAML"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "test_config.yml"

            # 创建配置
            settings = Settings(environment="test")

            # 保存配置
            settings.save_yaml(str(yaml_path))
            assert yaml_path.exists()

            # 加载配置
            loaded_settings = Settings.from_yaml(str(yaml_path))
            assert loaded_settings.environment == "test"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
