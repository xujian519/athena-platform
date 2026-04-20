#!/usr/bin/env python3
"""
插件注册表

管理所有插件的注册和查询。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .types import PluginDefinition, PluginStatus, PluginType

logger = logging.getLogger(__name__)


class PluginRegistry:
    """插件注册表

    存储和管理所有插件。
    """

    def __init__(self):
        """初始化注册表"""
        self._plugins: Dict[str, PluginDefinition] = {}
        logger.info("📦 插件注册表已初始化")

    def register(self, plugin: PluginDefinition) -> None:
        """注册插件

        Args:
            plugin: 插件定义

        Raises:
            ValueError: 插件ID已存在
        """
        if plugin.id in self._plugins:
            raise ValueError(f"Plugin {plugin.id} already registered")

        self._plugins[plugin.id] = plugin
        logger.info(f"✅ 插件已注册: {plugin.id} - {plugin.name}")

    def get_plugin(self, plugin_id: str) -> Optional[PluginDefinition]:
        """获取插件

        Args:
            plugin_id: 插件ID

        Returns:
            PluginDefinition | None: 插件定义，不存在返回None
        """
        return self._plugins.get(plugin_id)

    def unregister(self, plugin_id: str) -> bool:
        """注销插件

        Args:
            plugin_id: 插件ID

        Returns:
            bool: 是否成功注销
        """
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            logger.info(f"🗑️ 插件已注销: {plugin_id}")
            return True
        return False

    def activate(self, plugin_id: str) -> bool:
        """激活插件

        Args:
            plugin_id: 插件ID

        Returns:
            bool: 是否成功激活
        """
        plugin = self.get_plugin(plugin_id)
        if plugin and plugin.is_enabled():
            plugin.status = PluginStatus.ACTIVE
            logger.info(f"🟢 插件已激活: {plugin_id}")
            return True
        return False

    def deactivate(self, plugin_id: str) -> bool:
        """停用插件

        Args:
            plugin_id: 插件ID

        Returns:
            bool: 是否成功停用
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            plugin.status = PluginStatus.INACTIVE
            logger.info(f"⚪ 插件已停用: {plugin_id}")
            return True
        return False

    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        status: Optional[PluginStatus] = None,
        enabled_only: bool = False,
    ) -> List[PluginDefinition]:
        """列出插件

        Args:
            plugin_type: 插件类型（None表示所有）
            status: 插件状态（None表示所有）
            enabled_only: 是否只返回启用的插件

        Returns:
            list[PluginDefinition]: 插件列表
        """
        plugins = list(self._plugins.values())

        # 按类型过滤
        if plugin_type:
            plugins = [p for p in plugins if p.type == plugin_type]

        # 按状态过滤
        if status:
            plugins = [p for p in plugins if p.status == status]

        # 按启用状态过滤
        if enabled_only:
            plugins = [p for p in plugins if p.is_enabled()]

        # 按名称排序
        plugins.sort(key=lambda p: p.name)

        return plugins

    def find_plugins(
        self,
        name_pattern: str = "*",
        plugin_type: Optional[PluginType] = None,
    ) -> List[PluginDefinition]:
        """按模式查找插件

        Args:
            name_pattern: 名称模式（支持通配符*）
            plugin_type: 插件类型

        Returns:
            list[PluginDefinition]: 匹配的插件列表
        """
        plugins = self.list_plugins(plugin_type=plugin_type)

        # 按名称模式过滤
        if name_pattern != "*":
            pattern = name_pattern.lower().replace("*", "")
            plugins = [p for p in plugins if pattern in p.name.lower()]

        return plugins

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            dict: 统计信息
        """
        # 按类型统计
        by_type: Dict[str, int] = {}
        for plugin in self._plugins.values():
            ptype = plugin.type.value
            by_type[ptype] = by_type.get(ptype, 0) + 1

        # 按状态统计
        by_status: Dict[str, int] = {}
        for plugin in self._plugins.values():
            pstatus = plugin.status.value
            by_status[pstatus] = by_status.get(pstatus, 0) + 1

        return {
            "total_plugins": len(self._plugins),
            "by_type": by_type,
            "by_status": by_status,
        }


__all__ = [
    "PluginRegistry",
]
