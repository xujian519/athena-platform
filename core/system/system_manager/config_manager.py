#!/usr/bin/env python3
from __future__ import annotations
"""
系统管理器 - 配置管理器
System Manager - Configuration Manager

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
from pathlib import Path
from threading import Lock
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """配置管理器

    管理全局配置和模块配置，支持配置热更新。
    """

    def __init__(self, config_path: str | Path | None = None):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path) if config_path else None
        self.global_config: dict[str, Any] = {}
        self.module_configs: dict[str, dict[str, Any]] = {}
        self.config_watchers: list[callable] = []
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)

    def load_global_config(self, config_path: str | Path | None = None) -> dict[str, Any]:
        """加载全局配置

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        if config_path:
            self.config_path = Path(config_path)

        if not self.config_path or not self.config_path.exists():
            self.logger.warning(f"配置文件不存在: {self.config_path}")
            self.global_config = {}
            return self.global_config

        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.global_config = yaml.safe_load(f) or {}

            self.logger.info(f"全局配置已加载: {self.config_path}")
            return self.global_config

        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            self.global_config = {}
            return self.global_config

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键(支持点号分隔的路径，如 'module.submodule.key')
            default: 默认值

        Returns:
            配置值
        """
        with self.lock:
            keys = key.split(".")
            value = self.global_config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

    def set_config(self, key: str, value: Any) -> bool:
        """设置配置值

        Args:
            key: 配置键(支持点号分隔的路径)
            value: 配置值

        Returns:
            是否设置成功
        """
        with self.lock:
            keys = key.split(".")
            config = self.global_config

            # 导航到父级
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 设置值
            config[keys[-1]] = value
            self.logger.debug(f"配置已设置: {key} = {value}")

            # 触发watchers
            for watcher in self.config_watchers:
                try:
                    watcher(key, value)
                except Exception as e:
                    self.logger.error(f"配置watcher执行失败: {e}")

            return True

    def get_module_config(
        self, module_id: str, key: str | None = None, default: Any = None
    ) -> Any:
        """获取模块配置

        Args:
            module_id: 模块ID
            key: 配置键(可选)
            default: 默认值

        Returns:
            配置值
        """
        with self.lock:
            if module_id not in self.module_configs:
                return default

            if key is None:
                return self.module_configs[module_id]

            keys = key.split(".")
            value = self.module_configs[module_id]

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

    def set_module_config(self, module_id: str, key: str, value: Any) -> bool:
        """设置模块配置

        Args:
            module_id: 模块ID
            key: 配置键
            value: 配置值

        Returns:
            是否设置成功
        """
        with self.lock:
            if module_id not in self.module_configs:
                self.module_configs[module_id] = {}

            keys = key.split(".")
            config = self.module_configs[module_id]

            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            config[keys[-1]] = value
            self.logger.debug(f"模块配置已设置: {module_id}.{key} = {value}")
            return True

    def watch_config(self, callback: callable):
        """监听配置变化

        Args:
            callback: 回调函数，接收 (key, value) 参数
        """
        self.config_watchers.append(callback)

    def save_config(self, config_path: str | Path | None = None) -> bool:
        """保存配置到文件

        Args:
            config_path: 配置文件路径

        Returns:
            是否保存成功
        """
        if config_path:
            self.config_path = Path(config_path)

        if not self.config_path:
            self.logger.error("配置文件路径未设置")
            return False

        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.global_config, f, default_flow_style=False, allow_unicode=True)

            self.logger.info(f"配置已保存: {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False


__all__ = ["ConfigurationManager"]
