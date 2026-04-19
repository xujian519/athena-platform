#!/usr/bin/env python3
from __future__ import annotations
"""
感知模块配置管理器
Perception Module Configuration Manager

提供统一的配置加载、验证和管理功能。

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .types import CacheConfig, PerceptionConfig

logger = logging.getLogger(__name__)


class PerceptionConfigManager:
    """感知模块配置管理器

    提供统一的配置管理功能,支持:
    1. 从文件加载配置
    2. 从环境变量加载配置
    3. 配置验证
    4. 默认配置
    """

    # 单例实例
    _instance: "PerceptionConfigManager | None" = None
    _initialized: bool = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化配置管理器"""
        if self._initialized:
            return

        # 配置文件路径
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "perception_config.json"

        # 配置对象
        self.perception_config: PerceptionConfig | None = None
        self.cache_config: CacheConfig | None = None

        # 加载配置
        self._load_configs()

        self._initialized = True
        logger.info("✅ 感知模块配置管理器初始化完成")

    def _get_config_dir(self) -> Path:
        """获取配置目录

        优先级:
        1. 环境变量 PERCEPTION_CONFIG_DIR
        2. 项目根目录下的 config/perception/
        3. 当前目录下的 config/
        """
        # 1. 尝试环境变量
        env_dir = os.getenv("PERCEPTION_CONFIG_DIR")
        if env_dir:
            return Path(env_dir)

        # 2. 尝试项目根目录
        current_dir = Path(__file__).parent
        for _ in range(5):  # 最多向上查找5层
            if (current_dir / "pyproject.toml").exists():
                config_dir = current_dir / "config" / "perception"
                if config_dir.exists():
                    return config_dir
            current_dir = current_dir.parent

        # 3. 使用当前目录下的config
        return Path("config")

    def _load_configs(self) -> None:
        """加载配置"""
        # 加载感知配置
        self.perception_config = self._load_perception_config()

        # 加载缓存配置
        self.cache_config = self._load_cache_config()

    def _load_perception_config(self) -> PerceptionConfig:
        """加载感知配置"""
        # 尝试从文件加载
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    data = json.load(f)
                    perception_data = data.get("perception", {})
                    if perception_data:
                        return self._deserialize_config(perception_data, PerceptionConfig)
            except Exception as e:
                logger.warning(f"从文件加载感知配置失败: {e},使用默认配置")

        # 尝试从环境变量加载
        env_config = self._load_from_env()
        if env_config:
            return PerceptionConfig(**env_config)

        # 使用默认配置
        return PerceptionConfig()

    def _load_cache_config(self) -> CacheConfig:
        """加载缓存配置"""
        # 尝试从文件加载
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    data = json.load(f)
                    cache_data = data.get("cache", {})
                    if cache_data:
                        return self._deserialize_config(cache_data, CacheConfig)
            except Exception as e:
                logger.warning(f"从文件加载缓存配置失败: {e},使用默认配置")

        # 使用默认配置
        return CacheConfig()

    def _load_from_env(self) -> dict[str, Any] | None:
        """从环境变量加载配置

        支持的环境变量:
        - PERCEPTION_MULTIMODAL: 是否启用多模态
        - PERCEPTION_MAX_FILE_SIZE: 最大文件大小(字节)
        - PERCEPTION_OCR_LANGUAGES: OCR语言列表(逗号分隔)
        """
        config = {}

        # 多模态支持
        multimodal = os.getenv("PERCEPTION_MULTIMODAL")
        if multimodal is not None:
            config["enable_multimodal"] = multimodal.lower() in ("true", "1", "yes")

        # 最大文件大小
        max_size = os.getenv("PERCEPTION_MAX_FILE_SIZE")
        if max_size:
            try:
                config["max_file_size"] = int(max_size)
            except ValueError:
                logger.warning(f"无效的PERCEPTION_MAX_FILE_SIZE: {max_size}")

        # OCR语言
        languages = os.getenv("PERCEPTION_OCR_LANGUAGES")
        if languages:
            config["ocr_languages"] = [lang.strip() for lang in languages.split(",")]

        return config if config else None

    def _serialize_config(self, config_obj: Any) -> dict[str, Any]:
        """序列化配置对象，处理timedelta等特殊类型

        Args:
            config_obj: 配置对象

        Returns:
            可序列化的字典
        """
        from datetime import timedelta

        config_dict = asdict(config_obj) if config_obj else {}

        # 递归处理timedelta对象
        def process_value(value: Any) -> Any:
            if isinstance(value, timedelta):
                return {
                    "_type": "timedelta",
                    "total_seconds": value.total_seconds()
                }
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            return value

        return {k: process_value(v) for k, v in config_dict.items()}

    def _deserialize_config(self, config_dict: dict[str, Any], config_class: type) -> Any:
        """反序列化配置对象，处理timedelta等特殊类型

        Args:
            config_dict: 配置字典
            config_class: 配置类

        Returns:
            配置对象
        """
        from datetime import timedelta

        def process_value(value: Any) -> Any:
            if isinstance(value, dict) and value.get("_type") == "timedelta":
                return timedelta(seconds=value["total_seconds"])
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            return value

        processed_dict = {k: process_value(v) for k, v in config_dict.items()}
        return config_class(**processed_dict)

    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # 构建配置数据（处理特殊类型）
            config_data = {
                "perception": self._serialize_config(self.perception_config) if self.perception_config else {},
                "cache": self._serialize_config(self.cache_config) if self.cache_config else {},
            }

            # 保存到文件
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存到: {self.config_file}")

        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    def get_perception_config(self) -> PerceptionConfig:
        """获取感知配置"""
        if self.perception_config is None:
            self.perception_config = PerceptionConfig()
        return self.perception_config

    def get_cache_config(self) -> CacheConfig:
        """获取缓存配置"""
        if self.cache_config is None:
            self.cache_config = CacheConfig()
        return self.cache_config

    def update_perception_config(self, **kwargs) -> None:
        """更新感知配置

        Args:
            **kwargs: 要更新的配置项
        """
        if self.perception_config is None:
            self.perception_config = PerceptionConfig()

        # 更新配置
        for key, value in kwargs.items():
            if hasattr(self.perception_config, key):
                setattr(self.perception_config, key, value)
            else:
                logger.warning(f"未知的配置项: {key}")

        # 验证配置
        try:
            self.perception_config.validate()
            logger.info("感知配置已更新并验证通过")
        except Exception as e:
            logger.error(f"配置验证失败: {e}")

    def update_cache_config(self, **kwargs) -> None:
        """更新缓存配置

        Args:
            **kwargs: 要更新的配置项
        """
        if self.cache_config is None:
            self.cache_config = CacheConfig()

        # 更新配置
        for key, value in kwargs.items():
            if hasattr(self.cache_config, key):
                setattr(self.cache_config, key, value)
            else:
                logger.warning(f"未知的缓存配置项: {key}")

        # 验证配置
        try:
            self.cache_config.validate()
            logger.info("缓存配置已更新并验证通过")
        except Exception as e:
            logger.error(f"缓存配置验证失败: {e}")

    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self.perception_config = PerceptionConfig()
        self.cache_config = CacheConfig()
        logger.info("配置已重置为默认值")

    def get_config_dict(self) -> dict[str, Any]:
        """获取配置字典"""
        return {
            "perception": asdict(self.perception_config) if self.perception_config else {},
            "cache": asdict(self.cache_config) if self.cache_config else {},
            "config_file": str(self.config_file),
            "config_dir": str(self.config_dir),
        }


# 全局配置管理器实例
_config_manager: PerceptionConfigManager | None = None


def get_config_manager() -> PerceptionConfigManager:
    """获取全局配置管理器实例

    Returns:
        PerceptionConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = PerceptionConfigManager()
    return _config_manager


__all__ = ["PerceptionConfigManager", "get_config_manager"]
