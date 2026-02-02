#!/usr/bin/env python3
"""
统一配置管理器
提供配置的加载、验证和管理功能
"""

import os
import json
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器类"""

    _instance = None
    _config_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent.parent.parent / "config"
        self.config = {}
        self.load_all_configs()

    def load_all_configs(self):
        """加载所有配置文件"""
        # 加载主配置
        main_config = self.config_dir / "config.json"
        if main_config.exists():
            self.config.update(self._load_json_file(main_config))

        # 加载环境特定配置
        env = self.get_environment()
        env_config = self.config_dir / f"config.{env}.json"
        if env_config.exists():
            self.config.update(self._load_json_file(env_config))

        # 加载YAML配置
        yaml_configs = list(self.config_dir.glob("*.yml")) + list(self.config_dir.glob("*.yaml"))
        for yaml_file in yaml_configs:
            yaml_config = self._load_yaml_file(yaml_file)
            if yaml_config:
                self.config.update(yaml_config)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_database_config(self) -> Dict:
        """获取数据库配置"""
        return self.get('database', {})

    def get_service_config(self, service_name: str) -> Dict:
        """获取服务配置"""
        services = self.get('services', {})
        return services.get(service_name, {})

    def get_environment(self) -> str:
        """获取当前环境"""
        return os.getenv('ATHENA_ENV', 'development')

    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.get_environment() == 'production'

    def reload(self):
        """重新加载配置"""
        self.config.clear()
        self.load_all_configs()

    @staticmethod
    def _load_json_file(file_path: Path) -> Dict:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败 {file_path}: {e}")
            return {}

    @staticmethod
    def _load_yaml_file(file_path: Path) -> Dict:
        """加载YAML文件"""
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            print(f"YAML库未安装，跳过 {file_path}")
            return {}
        except Exception as e:
            print(f"加载YAML文件失败 {file_path}: {e}")
            return {}

    @staticmethod
    def instance():
        """获取单例实例"""
        if ConfigManager._instance is None:
            ConfigManager._instance = ConfigManager()
        return ConfigManager._instance

    @classmethod
    def get_config(cls, key: str, default: Any = None) -> Any:
        """便捷方法：获取配置"""
        return cls.instance().get(key, default)

    @classmethod
    def reload_config(cls):
        """便捷方法：重新加载配置"""
        cls.instance().reload()


# 全局配置实例
config = ConfigManager.instance()