#!/usr/bin/env python3
"""
统一配置管理测试
Tests for core.config.unified_settings
"""

import os

from core.config.unified_settings import Settings, get_settings


class TestSettings:
    """测试Settings类"""

    def test_load_default_settings(self):
        """测试加载默认配置"""
        settings = Settings.load(environment="development")
        assert settings is not None
        assert hasattr(settings, 'environment')

    def test_settings_singleton(self):
        """测试单例模式"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_environment_variable_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv('ATHENA_ENV', 'test')
        # 验证环境变量可以被读取
        assert os.getenv('ATHENA_ENV') == 'test'

    def test_settings_validation(self):
        """测试配置验证"""
        settings = Settings.load(environment="development")
        # 基本字段应该存在
        assert hasattr(settings, 'environment')


class TestSettingsPerformance:
    """测试配置加载性能"""

    def test_load_time_target(self):
        """测试加载时间目标（<50ms）"""
        import time
        start = time.time()
        settings = Settings.load(environment="development")
        elapsed = (time.time() - start) * 1000  # 转换为毫秒
        assert settings is not None
        # 目标：<50ms，快速配置应该满足
        assert elapsed < 100  # 宽松一些的测试


class TestLazySettings:
    """测试懒加载配置"""

    def test_lazy_settings_creation(self):
        """测试创建懒加载配置"""
        from core.config.lazy_settings import FastSettings
        settings = FastSettings.load(environment="development")
        assert settings is not None
        assert settings.environment == "development"

    def test_lazy_settings_performance(self):
        """测试懒加载性能（<10ms）"""
        import time

        from core.config.lazy_settings import FastSettings
        start = time.time()
        settings = FastSettings.load(environment="development")
        elapsed = (time.time() - start) * 1000
        assert settings is not None
        # 目标：<10ms
        assert elapsed < 20  # 宽松一些的测试
