#!/usr/bin/env python3
"""
插件注册表 - Phase 2.3插件机制

Plugin Registry - 管理所有已注册的上下文插件

核心功能:
- 插件注册与注销
- 插件查询与检索
- 依赖关系检查
- 插件状态管理

作者: Athena平台团队
创建时间: 2026-04-24
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from ..interfaces import IContextPlugin
from ..base_context import BaseContext

logger = logging.getLogger(__name__)


class PluginAlreadyRegisteredError(Exception):
    """插件已注册异常"""
    pass


class PluginNotFoundError(Exception):
    """插件未找到异常"""
    pass


class CircularDependencyError(Exception):
    """循环依赖异常"""
    pass


class DependencyNotFoundError(Exception):
    """依赖未找到异常"""
    pass


class ContextPluginRegistry:
    """
    上下文插件注册表

    管理所有已注册的插件，提供：
    - 插件注册（register）
    - 插件加载（load）
    - 插件卸载（unload）
    - 依赖检查（check_dependencies）
    """

    def __init__(self):
        """初始化插件注册表"""
        self._plugins: dict[str, IContextPlugin] = {}
        self._plugin_configs: dict[str, dict[str, Any]] = {}
        self._active_plugins: set[str] = set()
        self._lock = asyncio.Lock()

        logger.info("✅ 插件注册表初始化完成")

    async def register(
        self,
        plugin: IContextPlugin,
        config: Optional[Dict[str, Any]] = None,
        auto_initialize: bool = True,
    ) -> bool:
        """
        注册插件

        Args:
            plugin: 插件实例
            config: 插件配置（可选）
            auto_initialize: 是否自动初始化

        Returns:
            bool: 注册成功返回True

        Raises:
            PluginAlreadyRegisteredError: 插件已注册
        """
        async with self._lock:
            plugin_name = plugin.plugin_name

            if plugin_name in self._plugins:
                raise PluginAlreadyRegisteredError(f"插件已注册: {plugin_name}")

            # 检查依赖
            await self._check_dependencies(plugin)

            # 存储插件和配置
            self._plugins[plugin_name] = plugin
            self._plugin_configs[plugin_name] = config or {}

            # 自动初始化
            if auto_initialize:
                await plugin.initialize(self._plugin_configs[plugin_name])
                self._active_plugins.add(plugin_name)

            logger.info(
                f"✅ 插件注册成功: {plugin_name} v{plugin.plugin_version} "
                f"(依赖: {plugin.dependencies})"
            )
            return True

    async def load(self, plugin_name: str) -> IContextPlugin:
        """
        加载插件（初始化并激活）

        Args:
            plugin_name: 插件名称

        Returns:
            IContextPlugin: 插件实例

        Raises:
            PluginNotFoundError: 插件未注册
        """
        async with self._lock:
            if plugin_name not in self._plugins:
                raise PluginNotFoundError(f"插件未注册: {plugin_name}")

            plugin = self._plugins[plugin_name]

            if plugin_name not in self._active_plugins:
                await plugin.initialize(self._plugin_configs[plugin_name])
                self._active_plugins.add(plugin_name)
                logger.info(f"🔄 插件加载: {plugin_name}")

            return plugin

    async def unload(self, plugin_name: str) -> bool:
        """
        卸载插件（关闭并停用）

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 卸载成功返回True

        Raises:
            PluginNotFoundError: 插件未注册
        """
        async with self._lock:
            if plugin_name not in self._plugins:
                raise PluginNotFoundError(f"插件未注册: {plugin_name}")

            plugin = self._plugins[plugin_name]

            if plugin_name in self._active_plugins:
                await plugin.shutdown()
                self._active_plugins.discard(plugin_name)

            # 从注册表中移除
            del self._plugins[plugin_name]
            logger.info(f"🔌 插件卸载: {plugin_name}")

            return True

    async def reload(self, plugin_name: str, new_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        重新加载插件

        Args:
            plugin_name: 插件名称
            new_config: 新配置（可选）

        Returns:
            bool: 重载成功返回True
        """
        async with self._lock:
            if plugin_name not in self._plugins:
                raise PluginNotFoundError(f"插件未注册: {plugin_name}")

            plugin = self._plugins[plugin_name]

            # 如果插件是激活的，先关闭
            if plugin_name in self._active_plugins:
                await plugin.shutdown()
                self._active_plugins.discard(plugin_name)

            # 更新配置
            if new_config is not None:
                self._plugin_configs[plugin_name] = new_config

            # 重新初始化
            await plugin.initialize(self._plugin_configs[plugin_name])
            self._active_plugins.add(plugin_name)

            logger.info(f"🔄 插件重载: {plugin_name}")
            return True

    def get(self, plugin_name: str) -> Optional[IContextPlugin]:
        """
        获取插件实例

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[IContextPlugin]: 插件实例或None
        """
        return self._plugins.get(plugin_name)

    def is_active(self, plugin_name: str) -> bool:
        """
        检查插件是否激活

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 激活返回True
        """
        return plugin_name in self._active_plugins

    def list_all(self) -> List[str]:
        """
        列出所有已注册插件

        Returns:
            list[str]: 插件名称列表
        """
        return list(self._plugins.keys())

    def list_active(self) -> List[str]:
        """
        列出所有激活插件

        Returns:
            list[str]: 激活插件名称列表
        """
        return list(self._active_plugins)

    async def check_dependencies(self, plugin_name: str) -> dict[str, bool]:
        """
        检查插件依赖是否满足

        Args:
            plugin_name: 插件名称

        Returns:
            dict[str, bool]: 依赖名称到满足状态的映射
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            raise PluginNotFoundError(f"插件未注册: {plugin_name}")

        result = {}
        for dep in plugin.dependencies:
            result[dep] = dep in self._plugins and dep in self._active_plugins

        return result

    async def _check_dependencies(self, plugin: IContextPlugin) -> None:
        """
        内部依赖检查（检查循环依赖）

        Args:
            plugin: 待检查的插件

        Raises:
            CircularDependencyError: 存在循环依赖
            DependencyNotFoundError: 依赖未找到
        """
        visited: set[str] = set()
        path: List[str] = []

        async def dfs(current_plugin: IContextPlugin) -> None:
            plugin_name = current_plugin.plugin_name

            if plugin_name in path:
                cycle = " -> ".join(path + [plugin_name])
                raise CircularDependencyError(f"检测到循环依赖: {cycle}")

            if plugin_name in visited:
                return

            path.append(plugin_name)
            visited.add(plugin_name)

            for dep_name in current_plugin.dependencies:
                if dep_name not in self._plugins:
                    raise DependencyNotFoundError(
                        f"依赖未找到: {plugin_name} -> {dep_name}"
                    )
                await dfs(self._plugins[dep_name])

            path.pop()

        await dfs(plugin)

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        获取插件信息

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[Dict[str, Any]]: 插件信息字典
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            return None

        return {
            "name": plugin.plugin_name,
            "version": plugin.plugin_version,
            "dependencies": plugin.dependencies,
            "active": plugin_name in self._active_plugins,
            "config": self._plugin_configs.get(plugin_name, {}),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取注册表统计信息

        Returns:
            dict[str, Any]: 统计信息
        """
        return {
            "total_plugins": len(self._plugins),
            "active_plugins": len(self._active_plugins),
            "inactive_plugins": len(self._plugins) - len(self._active_plugins),
            "plugin_list": self.list_all(),
        }

    async def shutdown_all(self) -> None:
        """关闭所有激活的插件"""
        for plugin_name in list(self._active_plugins):
            await self.unload(plugin_name)

        logger.info("🔌 所有插件已关闭")


__all__ = [
    "ContextPluginRegistry",
    "PluginAlreadyRegisteredError",
    "PluginNotFoundError",
    "CircularDependencyError",
    "DependencyNotFoundError",
]
