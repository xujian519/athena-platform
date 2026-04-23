#!/usr/bin/env python3
"""
Plugins系统Hook集成测试

测试Hook系统与Plugins系统的集成。

Author: Athena平台团队
创建时间: 2026-04-20
"""

import pytest
from core.plugins.types import (
    PluginDefinition,
    PluginMetadata,
    PluginStatus,
    PluginType,
)

from core.hooks.base import HookContext, HookFunction, HookType
from core.hooks.integrations import (
    create_plugin_hook_integration,
    wrap_plugin_loader_with_hooks,
)


class MockPluginLoader:
    """模拟插件加载器"""

    def __init__(self):
        self.loaded_plugins = []

    def load_from_file(self, file_path: str):
        """从文件加载插件"""
        plugin = PluginDefinition(
            id=f"plugin_{len(self.loaded_plugins)}",
            name=f"Plugin {len(self.loaded_plugins)}",
            type=PluginType.TOOL,
            status=PluginStatus.LOADED,
            metadata=PluginMetadata(version="1.0.0"),
        )
        self.loaded_plugins.append(plugin)
        return plugin

    def load_from_directory(self, directory: str, recursive: bool = False):
        """从目录加载插件"""
        plugins = [
            self.load_from_file(f"{directory}/plugin1.yaml"),
            self.load_from_file(f"{directory}/plugin2.yaml"),
        ]
        return plugins


class TestPluginHookIntegration:
    """测试Plugins Hook集成"""

    @pytest.fixture
    def integration(self):
        """创建Hook集成"""
        return create_plugin_hook_integration()

    @pytest.mark.asyncio
    async def test_before_plugin_load(self, integration):
        """测试插件加载前Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("before_load")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.PRE_TASK_START, test_hook
        )

        # 触发Hook
        result = await integration.before_plugin_load("/path/to/plugin")

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_after_plugin_load(self, integration):
        """测试插件加载后Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("after_load")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.POST_TASK_COMPLETE, test_hook
        )

        # 创建模拟插件
        plugin = PluginDefinition(
            id="test_plugin",
            name="Test Plugin",
            type=PluginType.TOOL,
            metadata=PluginMetadata(version="1.0.0"),
        )

        # 触发Hook
        result = await integration.after_plugin_load(plugin, success=True)

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_before_plugin_activate(self, integration):
        """测试插件激活前Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("before_activate")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.PRE_TASK_START, test_hook
        )

        plugin = PluginDefinition(
            id="test_plugin",
            name="Test Plugin",
            type=PluginType.TOOL,
        )

        result = await integration.before_plugin_activate(plugin)

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_after_plugin_activate(self, integration):
        """测试插件激活后Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("after_activate")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.POST_TASK_COMPLETE, test_hook
        )

        plugin = PluginDefinition(
            id="test_plugin",
            name="Test Plugin",
            type=PluginType.TOOL,
        )

        result = await integration.after_plugin_activate(plugin, success=True)

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_before_plugin_deactivate(self, integration):
        """测试插件停用前Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("before_deactivate")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.PRE_TASK_START, test_hook
        )

        plugin = PluginDefinition(
            id="test_plugin",
            name="Test Plugin",
            type=PluginType.TOOL,
        )

        result = await integration.before_plugin_deactivate(plugin)

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_after_plugin_deactivate(self, integration):
        """测试插件停用后Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("after_deactivate")
            return "ok"

        integration.registry.register_function(
            "test_hook", HookType.POST_TASK_COMPLETE, test_hook
        )

        plugin = PluginDefinition(
            id="test_plugin",
            name="Test Plugin",
            type=PluginType.TOOL,
        )

        result = await integration.after_plugin_deactivate(plugin, success=True)

        assert result.success is True
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_on_plugin_error(self, integration):
        """测试插件错误Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append("error")
            return "ok"

        integration.registry.register_function("test_hook", HookType.ON_ERROR, test_hook)

        plugin = PluginDefinition(
            id="test_plugin",
            name="Test Plugin",
            type=PluginType.TOOL,
        )

        result = await integration.on_plugin_error(
            plugin, ValueError("Test error"), {"context": "data"}
        )

        assert result.success is False
        assert result.error == "Test error"
        assert len(executed) == 1


class TestPluginLoaderWithHooks:
    """测试带Hook的插件加载器"""

    @pytest.fixture
    def integration(self):
        """创建Hook集成"""
        return create_plugin_hook_integration()

    @pytest.fixture
    def loader(self):
        """创建模拟加载器"""
        return MockPluginLoader()

    @pytest.mark.asyncio
    async def test_load_from_file_with_hooks(self, integration, loader):
        """测试带Hook的文件加载"""

        executed = []

        # 注册Hook
        async def before_hook(context: HookContext):
            executed.append("before")
            return "ok"

        async def after_hook(context: HookContext):
            executed.append("after")
            return "ok"

        integration.registry.register_function("before", HookType.PRE_TASK_START, before_hook)
        integration.registry.register_function("after", HookType.POST_TASK_COMPLETE, after_hook)

        # 包装加载器
        wrapped_loader = wrap_plugin_loader_with_hooks(loader, integration)

        # 加载插件
        plugin = await wrapped_loader.load_from_file("/path/to/plugin.yaml")

        assert plugin is not None
        assert plugin.id == "plugin_0"
        assert "before" in executed
        assert "after" in executed

    @pytest.mark.asyncio
    async def test_load_from_directory_with_hooks(self, integration, loader):
        """测试带Hook的目录加载"""

        executed = []

        # 注册Hook
        async def before_hook(context: HookContext):
            executed.append("before_dir")
            return "ok"

        async def after_hook(context: HookContext):
            executed.append("after_dir")
            return "ok"

        integration.registry.register_function("before", HookType.PRE_TASK_START, before_hook)
        integration.registry.register_function("after", HookType.POST_TASK_COMPLETE, after_hook)

        # 包装加载器
        wrapped_loader = wrap_plugin_loader_with_hooks(loader, integration)

        # 加载插件
        plugins = await wrapped_loader.load_from_directory("/path/to/plugins")

        assert len(plugins) == 2
        assert "before_dir" in executed
        assert len([e for e in executed if e == "after_dir"]) == 2  # 每个插件触发一次

    @pytest.mark.asyncio
    async def test_load_with_error_hook(self, integration):
        """测试加载错误时的Hook"""

        class FailingLoader:
            def load_from_file(self, file_path: str):
                raise ValueError("Plugin load failed")

        executed = []

        # 注册错误Hook
        async def error_hook(context: HookContext):
            executed.append("error")
            return "ok"

        integration.registry.register_function("error", HookType.ON_ERROR, error_hook)

        # 包装加载器
        wrapped_loader = wrap_plugin_loader_with_hooks(FailingLoader(), integration)

        # 加载插件（应该抛出异常）
        with pytest.raises(ValueError, match="Plugin load failed"):
            await wrapped_loader.load_from_file("/path/to/plugin.yaml")

        # 验证错误Hook被触发
        assert "error" in executed


class TestPluginHookLifecycle:
    """测试Plugins Hook生命周期管理"""

    @pytest.mark.asyncio
    async def test_hook_lifecycle_with_plugins(self):
        """测试Hook生命周期与Plugins的集成"""

        # 创建带生命周期的集成
        integration = create_plugin_hook_integration(enable_lifecycle=True)

        # 注册Hook
        async def test_hook(context: HookContext):
            return "ok"

        hook = HookFunction(
            name="plugin_hook",
            hook_type=HookType.PRE_TASK_START,
            func=test_hook,
        )

        await integration.lifecycle.register(hook)

        # 验证状态
        assert integration.lifecycle.get_state("plugin_hook") is not None

        # 停用Hook
        await integration.lifecycle.deactivate("plugin_hook")

        # 验证状态
        from core.hooks.enhanced.types import HookState

        assert integration.lifecycle.get_state("plugin_hook") == HookState.INACTIVE


__all__ = [
    "TestPluginHookIntegration",
    "TestPluginLoaderWithHooks",
    "TestPluginHookLifecycle",
]

