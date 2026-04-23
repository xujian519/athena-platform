#!/usr/bin/env python3
"""
Plugins系统Hook集成

将增强的Hook系统集成到Plugins系统。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

import logging
from typing import Any

from core.hooks.base import HookContext, HookRegistry, HookType
from core.hooks.enhanced import HookLifecycleManager, HookResult
from core.plugins.types import PluginDefinition, PluginStatus, PluginType

logger = logging.getLogger(__name__)


# 扩展HookType以支持Plugins系统
class PluginHookType:
    """Plugins系统专用Hook类型"""

    PRE_PLUGIN_LOAD = "pre_plugin_load"
    POST_PLUGIN_LOAD = "post_plugin_load"
    PRE_PLUGIN_UNLOAD = "pre_plugin_unload"
    POST_PLUGIN_UNLOAD = "post_plugin_unload"
    PRE_PLUGIN_ACTIVATE = "pre_plugin_activate"
    POST_PLUGIN_ACTIVATE = "post_plugin_activate"
    PRE_PLUGIN_DEACTIVATE = "pre_plugin_deactivate"
    POST_PLUGIN_DEACTIVATE = "post_plugin_deactivate"
    PLUGIN_ERROR = "plugin_error"


class PluginHookIntegration:
    """Plugins系统Hook集成

    为Plugins系统提供Hook支持。
    """

    def __init__(
        self,
        registry: HookRegistry | None = None,
        enable_lifecycle: bool = True,
    ):
        """初始化集成

        Args:
            registry: Hook注册表
            enable_lifecycle: 是否启用生命周期管理
        """
        self._registry = registry or HookRegistry()
        self._lifecycle = HookLifecycleManager(self._registry) if enable_lifecycle else None

        logger.info("🔗 Plugins系统Hook集成已初始化")

    @property
    def registry(self) -> HookRegistry:
        """获取Hook注册表"""
        return self._registry

    @property
    def lifecycle(self) -> HookLifecycleManager | None:
        """获取生命周期管理器"""
        return self._lifecycle

    async def before_plugin_load(
        self, plugin_path: str, metadata: Optional[dict[str, Any]] = None
    ) -> HookResult:
        """插件加载前Hook

        Args:
            plugin_path: 插件路径
            metadata: 元数据

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.PRE_TASK_START,
            data={
                "plugin_path": plugin_path,
                "metadata": metadata or {},
            },
        )

        results = await self._registry.trigger(HookType.PRE_TASK_START, context)

        return HookResult(
            success=True,
            data=results,
        )

    async def after_plugin_load(
        self, plugin: PluginDefinition, success: bool = True, error: Optional[str] = None
    ) -> HookResult:
        """插件加载后Hook

        Args:
            plugin: 插件定义
            success: 是否成功
            error: 错误信息

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.POST_TASK_COMPLETE,
            data={
                "plugin": plugin,
                "plugin_id": plugin.id,
                "plugin_name": plugin.name,
                "plugin_type": plugin.type.value,
                "success": success,
                "error": error,
            },
        )

        results = await self._registry.trigger(HookType.POST_TASK_COMPLETE, context)

        return HookResult(
            success=success,
            data=results,
            error=error,
        )

    async def before_plugin_activate(
        self, plugin: PluginDefinition
    ) -> HookResult:
        """插件激活前Hook

        Args:
            plugin: 插件定义

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.PRE_TASK_START,
            data={
                "plugin": plugin,
                "plugin_id": plugin.id,
                "plugin_name": plugin.name,
            },
        )

        results = await self._registry.trigger(HookType.PRE_TASK_START, context)

        return HookResult(
            success=True,
            data=results,
        )

    async def after_plugin_activate(
        self, plugin: PluginDefinition, success: bool = True
    ) -> HookResult:
        """插件激活后Hook

        Args:
            plugin: 插件定义
            success: 是否成功

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.POST_TASK_COMPLETE,
            data={
                "plugin": plugin,
                "plugin_id": plugin.id,
                "plugin_name": plugin.name,
                "success": success,
            },
        )

        results = await self._registry.trigger(HookType.POST_TASK_COMPLETE, context)

        return HookResult(
            success=success,
            data=results,
        )

    async def before_plugin_deactivate(
        self, plugin: PluginDefinition
    ) -> HookResult:
        """插件停用前Hook

        Args:
            plugin: 插件定义

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.PRE_TASK_START,
            data={
                "plugin": plugin,
                "plugin_id": plugin.id,
                "plugin_name": plugin.name,
            },
        )

        results = await self._registry.trigger(HookType.PRE_TASK_START, context)

        return HookResult(
            success=True,
            data=results,
        )

    async def after_plugin_deactivate(
        self, plugin: PluginDefinition, success: bool = True
    ) -> HookResult:
        """插件停用后Hook

        Args:
            plugin: 插件定义
            success: 是否成功

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.POST_TASK_COMPLETE,
            data={
                "plugin": plugin,
                "plugin_id": plugin.id,
                "plugin_name": plugin.name,
                "success": success,
            },
        )

        results = await self._registry.trigger(HookType.POST_TASK_COMPLETE, context)

        return HookResult(
            success=success,
            data=results,
        )

    async def before_plugin_unload(
        self, plugin: PluginDefinition
    ) -> HookResult:
        """插件卸载前Hook

        Args:
            plugin: 插件定义

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.PRE_TASK_START,
            data={
                "plugin": plugin,
                "plugin_id": plugin.id,
                "plugin_name": plugin.name,
            },
        )

        results = await self._registry.trigger(HookType.PRE_TASK_START, context)

        return HookResult(
            success=True,
            data=results,
        )

    async def after_plugin_unload(
        self, plugin_id: str, success: bool = True
    ) -> HookResult:
        """插件卸载后Hook

        Args:
            plugin_id: 插件ID
            success: 是否成功

        Returns:
            HookResult: Hook执行结果
        """
        context = HookContext(
            hook_type=HookType.POST_TASK_COMPLETE,
            data={
                "plugin_id": plugin_id,
                "success": success,
            },
        )

        results = await self._registry.trigger(HookType.POST_TASK_COMPLETE, context)

        return HookResult(
            success=success,
            data=results,
        )

    async def on_plugin_error(
        self, plugin: PluginDefinition | None, error: Exception, context: dict[str, Any]
    ) -> HookResult:
        """插件错误Hook

        Args:
            plugin: 插件定义
            error: 异常
            context: 上下文信息

        Returns:
            HookResult: Hook执行结果
        """
        hook_context = HookContext(
            hook_type=HookType.ON_ERROR,
            data={
                "plugin": plugin,
                "plugin_id": plugin.id if plugin else None,
                "plugin_name": plugin.name if plugin else None,
                "error": str(error),
                "error_type": type(error).__name__,
                "context": context,
            },
        )

        results = await self._registry.trigger(HookType.ON_ERROR, hook_context)

        return HookResult(
            success=False,
            data=results,
            error=str(error),
        )


class PluginLoaderWithHooks:
    """带Hook的插件加载器

    包装插件加载，自动触发Hook。
    """

    def __init__(self, plugin_loader, hook_integration: PluginHookIntegration):
        """初始化加载器

        Args:
            plugin_loader: 原始插件加载器
            hook_integration: Hook集成
        """
        self._loader = plugin_loader
        self._hooks = hook_integration

    async def load_from_file(self, file_path: str):
        """从文件加载插件（带Hook）

        Args:
            file_path: 文件路径

        Returns:
            插件定义
        """
        # 加载前Hook
        await self._hooks.before_plugin_load(file_path)

        try:
            # 加载插件
            plugin = self._loader.load_from_file(file_path)

            # 加载后Hook
            await self._hooks.after_plugin_load(plugin, success=True)

            return plugin

        except Exception as e:
            # 错误Hook
            await self._hooks.on_plugin_error(None, e, {"file_path": file_path})

            # 重新抛出异常
            raise

    async def load_from_directory(self, directory: str, recursive: bool = False):
        """从目录加载插件（带Hook）

        Args:
            directory: 目录路径
            recursive: 是否递归

        Returns:
            插件列表
        """
        # 加载前Hook
        await self._hooks.before_plugin_load(directory)

        try:
            # 加载插件
            plugins = self._loader.load_from_directory(directory, recursive)

            # 加载后Hook
            for plugin in plugins:
                await self._hooks.after_plugin_load(plugin, success=True)

            return plugins

        except Exception as e:
            # 错误Hook
            await self._hooks.on_plugin_error(None, e, {"directory": directory})

            raise


# 便捷函数


def create_plugin_hook_integration(
    registry: HookRegistry | None = None,
    enable_lifecycle: bool = True,
) -> PluginHookIntegration:
    """创建Plugins系统Hook集成

    Args:
        registry: Hook注册表
        enable_lifecycle: 是否启用生命周期管理

    Returns:
        PluginHookIntegration: Hook集成实例
    """
    return PluginHookIntegration(
        registry=registry,
        enable_lifecycle=enable_lifecycle,
    )


def wrap_plugin_loader_with_hooks(
    plugin_loader, hook_integration: PluginHookIntegration
) -> PluginLoaderWithHooks:
    """包装插件加载器以支持Hook

    Args:
        plugin_loader: 原始插件加载器
        hook_integration: Hook集成

    Returns:
        PluginLoaderWithHooks: 带Hook的加载器
    """
    return PluginLoaderWithHooks(plugin_loader, hook_integration)


__all__ = [
    "PluginHookType",
    "PluginHookIntegration",
    "PluginLoaderWithHooks",
    "create_plugin_hook_integration",
    "wrap_plugin_loader_with_hooks",
]
