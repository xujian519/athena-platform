#!/usr/bin/env python3
"""
插件加载器 - Phase 2.3插件机制

Plugin Loader - 从配置文件动态加载插件

核心功能:
- 从YAML配置文件加载插件
- 动态导入插件模块
- 插件生命周期管理
- 热加载支持

作者: Athena平台团队
创建时间: 2026-04-24
"""

import asyncio
import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .registry import ContextPluginRegistry, PluginNotFoundError

logger = logging.getLogger(__name__)


class PluginConfig:
    """
    插件配置类

    表示单个插件的配置信息。
    """

    def __init__(
        self,
        name: str,
        module_path: str,
        class_name: Optional[str] = None,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
        priority: int = 100,
    ):
        """
        初始化插件配置

        Args:
            name: 插件名称
            module_path: 模块路径（如 "core.context_management.plugins.compression_plugin"）
            class_name: 类名（可选，默认使用插件名称）
            enabled: 是否启用
            config: 插件配置参数
            priority: 加载优先级（数值越小越优先）
        """
        self.name = name
        self.module_path = module_path
        self.class_name = class_name or f"{name.capitalize()}Plugin"
        self.enabled = enabled
        self.config = config or {}
        self.priority = priority

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "module_path": self.module_path,
            "class_name": self.class_name,
            "enabled": self.enabled,
            "config": self.config,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginConfig":
        """从字典创建"""
        return cls(
            name=data["name"],
            module_path=data["module_path"],
            class_name=data.get("class_name"),
            enabled=data.get("enabled", True),
            config=data.get("config", {}),
            priority=data.get("priority", 100),
        )

    def __repr__(self) -> str:
        return f"PluginConfig(name={self.name}, enabled={self.enabled}, priority={self.priority})"


class PluginLoader:
    """
    插件加载器

    负责从配置文件动态加载和管理插件：
    - 解析YAML配置
    - 动态导入插件模块
    - 实例化插件对象
    - 管理插件生命周期
    """

    def __init__(self, registry: Optional[ContextPluginRegistry] = None):
        """
        初始化插件加载器

        Args:
            registry: 插件注册表（可选，默认创建新实例）
        """
        self._registry = registry or ContextPluginRegistry()
        self._configs: dict[str, PluginConfig] = {}
        self._watch_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

        logger.info("✅ 插件加载器初始化完成")

    @property
    def registry(self) -> ContextPluginRegistry:
        """获取插件注册表"""
        return self._registry

    async def load_from_yaml(
        self, config_path: Union[str, Path], auto_start: bool = True
    ) -> List[str]:
        """
        从YAML配置文件加载插件

        配置格式:
        ```yaml
        plugins:
          - name: compression
            module_path: core.context_management.plugins.compression_plugin
            class_name: CompressionPlugin
            enabled: true
            priority: 10
            config:
              ratio: 0.5

          - name: validation
            module_path: core.context_management.plugins.validation_plugin
            enabled: true
            priority: 20
        ```

        Args:
            config_path: 配置文件路径
            auto_start: 是否自动启动启用的插件

        Returns:
            List[str]: 成功加载的插件名称列表
        """
        config_path = Path(config_path)

        if not config_path.exists():
            logger.warning(f"⚠️ 配置文件不存在: {config_path}")
            return []

        # 解析YAML
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "plugins" not in data:
            logger.warning("⚠️ 配置文件中没有插件定义")
            return []

        # 加载插件配置
        loaded = []
        for plugin_data in data["plugins"]:
            config = PluginConfig.from_dict(plugin_data)
            self._configs[config.name] = config

            if config.enabled and auto_start:
                try:
                    await self.load_plugin(config)
                    loaded.append(config.name)
                except Exception as e:
                    logger.error(f"❌ 加载插件失败 {config.name}: {e}")

        logger.info(f"✅ 从配置文件加载了 {len(loaded)} 个插件")
        return loaded

    async def load_plugin(self, config: PluginConfig) -> bool:
        """
        加载单个插件

        Args:
            config: 插件配置

        Returns:
            bool: 加载成功返回True
        """
        # 动态导入模块
        try:
            module = importlib.import_module(config.module_path)
        except ImportError as e:
            logger.error(f"❌ 无法导入模块 {config.module_path}: {e}")
            return False

        # 获取插件类
        plugin_class = getattr(module, config.class_name, None)
        if not plugin_class:
            logger.error(f"❌ 类不存在: {config.class_name}")
            return False

        # 实例化插件
        try:
            plugin_instance = plugin_class()
        except Exception as e:
            logger.error(f"❌ 实例化插件失败 {config.name}: {e}")
            return False

        # 注册到注册表
        try:
            # 如果插件已注册，先卸载
            if config.name in self._registry._plugins:
                await self._registry.unload(config.name)
            await self._registry.register(
                plugin_instance,
                config=config.config,
                auto_initialize=True,
            )
            # 存储配置
            self._configs[config.name] = config
        except Exception as e:
            logger.error(f"❌ 注册插件失败 {config.name}: {e}")
            return False

        return True

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 卸载成功返回True
        """
        try:
            await self._registry.unload(plugin_name)
            # 从配置中删除
            if plugin_name in self._configs:
                del self._configs[plugin_name]
            return True
        except PluginNotFoundError:
            logger.warning(f"⚠️ 插件未找到: {plugin_name}")
            return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        重新加载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 重载成功返回True
        """
        config = self._configs.get(plugin_name)
        if not config:
            logger.warning(f"⚠️ 插件配置不存在: {plugin_name}")
            return False

        # 先从注册表卸载，但保留配置
        try:
            await self._registry.unload(plugin_name)
        except PluginNotFoundError:
            pass

        # 重新加载
        return await self.load_plugin(config)

    async def reload_all(self) -> dict[str, bool]:
        """
        重新加载所有插件

        Returns:
            dict[str, bool]: 插件名称到重载结果的映射
        """
        results = {}
        for plugin_name in list(self._configs.keys()):
            results[plugin_name] = await self.reload_plugin(plugin_name)

        return results

    async def hot_reload(self, config_path: Union[str, Path]) -> List[str]:
        """
        热加载：从配置文件重新加载所有插件

        与load_from_yaml的区别：
        - 先卸载所有现有插件
        - 然后重新加载

        Args:
            config_path: 配置文件路径

        Returns:
            List[str]: 成功加载的插件名称列表
        """
        # 卸载所有插件
        for plugin_name in list(self._configs.keys()):
            await self.unload_plugin(plugin_name)

        # 清空配置
        self._configs.clear()

        # 重新加载
        return await self.load_from_yaml(config_path, auto_start=True)

    def get_config(self, plugin_name: str) -> Optional[PluginConfig]:
        """
        获取插件配置

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[PluginConfig]: 插件配置或None
        """
        return self._configs.get(plugin_name)

    def list_configs(self) -> List[PluginConfig]:
        """
        列出所有插件配置

        Returns:
            List[PluginConfig]: 插件配置列表（按优先级排序）
        """
        return sorted(self._configs.values(), key=lambda x: x.priority)

    async def execute_plugin(
        self, plugin_name: str, context: Any, **kwargs
    ) -> Any:
        """
        执行插件

        Args:
            plugin_name: 插件名称
            context: 上下文对象
            **kwargs: 执行参数

        Returns:
            Any: 执行结果

        Raises:
            PluginNotFoundError: 插件未找到或未激活
        """
        plugin = self._registry.get(plugin_name)
        if not plugin:
            raise PluginNotFoundError(f"插件未找到: {plugin_name}")

        if not self._registry.is_active(plugin_name):
            await self._registry.load(plugin_name)

        return await plugin.execute(context, **kwargs)

    async def shutdown_all(self) -> None:
        """关闭所有插件"""
        await self._registry.shutdown_all()

        # 取消所有监听任务
        for task in self._watch_tasks.values():
            if not task.done():
                task.cancel()

        self._watch_tasks.clear()


__all__ = [
    "PluginLoader",
    "PluginConfig",
]
