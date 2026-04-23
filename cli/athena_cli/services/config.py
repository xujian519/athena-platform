"""
配置管理模块
Configuration Management Module

管理CLI配置和认证信息
"""

import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AthenaConfig(BaseModel):
    """Athena CLI配置"""

    # API配置
    api_endpoint: str = "http://localhost:8005"
    api_key: Optional[str] = None

    # 默认设置
    default_limit: int = 10
    output_format: str = "table"
    timeout: float = 30.0

    # 高级设置
    verbose: bool = False
    debug: bool = False

    class Config:
        env_prefix = "ATHENA"
        env_file = ".env"


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config_dir = Path.home() / ".athena"
        self.config_file = self.config_dir / "config.yaml"

    def load_config(self) -> AthenaConfig:
        """
        加载配置

        Returns:
            配置对象
        """
        if not self.config_file.exists():
            # 创建默认配置
            return AthenaConfig()

        with open(self.config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return AthenaConfig(**data)

    def save_config(self, config: AthenaConfig):
        """
        保存配置

        Args:
            config: 配置对象
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, "w", encoding="utf-8") as f:
            # 隐藏敏感信息
            data = config.model_dump()
            if data.get("api_key"):
                data["api_key"] = "******"

            yaml.dump(data, f, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        config = self.load_config()
        return getattr(config, key, default)

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        config = self.load_config()
        setattr(config, key, value)
        self.save_config(config)

    def unset(self, key: str):
        """
        删除配置值

        Args:
            key: 配置键
        """
        config = self.load_config()
        if hasattr(config, key):
            delattr(config, key)
            self.save_config(config)

    def list_all(self) -> Dict[str, Any]:
        """
        列出所有配置

        Returns:
            所有配置项
        """
        config = self.load_config()
        return config.model_dump()


# 全局配置管理器实例
config_manager = ConfigManager()
