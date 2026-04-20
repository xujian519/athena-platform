#!/usr/bin/env python3
"""
Plugins系统单元测试 - PluginRegistry

测试PluginRegistry的核心功能。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import pytest

from core.plugins.types import (
    PluginDefinition,
    PluginStatus,
    PluginType,
    PluginMetadata,
)


def test_register_plugin():
    """测试插件注册"""
    # Arrange
    from core.plugins.registry import PluginRegistry

    registry = PluginRegistry()
    plugin = PluginDefinition(
        id="test_plugin",
        name="Test Plugin",
        type=PluginType.TOOL,
        metadata=PluginMetadata(
            author="Athena Team",
            version="1.0.0",
        ),
    )

    # Act
    registry.register(plugin)

    # Assert
    retrieved = registry.get_plugin("test_plugin")
    assert retrieved is not None
    assert retrieved.id == "test_plugin"
    assert retrieved.name == "Test Plugin"
    assert retrieved.type == PluginType.TOOL


def test_register_duplicate_plugin_raises_error():
    """测试注册重复插件应抛出错误"""
    from core.plugins.registry import PluginRegistry

    registry = PluginRegistry()

    plugin1 = PluginDefinition(
        id="dup_plugin",
        name="Duplicate Plugin",
        type=PluginType.TOOL,
    )

    plugin2 = PluginDefinition(
        id="dup_plugin",
        name="Duplicate Plugin 2",
        type=PluginType.AGENT,
    )

    registry.register(plugin1)

    # Act & Assert
    with pytest.raises(ValueError, match="already registered"):
        registry.register(plugin2)


def test_get_nonexistent_plugin():
    """测试获取不存在的插件"""
    from core.plugins.registry import PluginRegistry

    registry = PluginRegistry()

    # Act
    result = registry.get_plugin("nonexistent_plugin")

    # Assert
    assert result is None


def test_list_plugins_by_type():
    """测试按类型列出插件"""
    from core.plugins.registry import PluginRegistry

    # Arrange
    registry = PluginRegistry()

    plugin1 = PluginDefinition(
        id="tool_plugin_1",
        name="Tool Plugin 1",
        type=PluginType.TOOL,
    )

    plugin2 = PluginDefinition(
        id="agent_plugin_1",
        name="Agent Plugin 1",
        type=PluginType.AGENT,
    )

    plugin3 = PluginDefinition(
        id="tool_plugin_2",
        name="Tool Plugin 2",
        type=PluginType.TOOL,
    )

    # Act
    registry.register(plugin1)
    registry.register(plugin2)
    registry.register(plugin3)

    tool_plugins = registry.list_plugins(plugin_type=PluginType.TOOL)
    all_plugins = registry.list_plugins()

    # Assert
    assert len(tool_plugins) == 2
    assert tool_plugins[0].id == "tool_plugin_1"
    assert tool_plugins[1].id == "tool_plugin_2"
    assert len(all_plugins) == 3


def test_list_plugins_by_status():
    """测试按状态列出插件"""
    from core.plugins.registry import PluginRegistry

    # Arrange
    registry = PluginRegistry()

    plugin1 = PluginDefinition(
        id="active_plugin",
        name="Active Plugin",
        type=PluginType.TOOL,
        status=PluginStatus.ACTIVE,
    )

    plugin2 = PluginDefinition(
        id="inactive_plugin",
        name="Inactive Plugin",
        type=PluginType.TOOL,
        status=PluginStatus.INACTIVE,
    )

    registry.register(plugin1)
    registry.register(plugin2)

    # Act
    active_plugins = registry.list_plugins(status=PluginStatus.ACTIVE)

    # Assert
    assert len(active_plugins) == 1
    assert active_plugins[0].id == "active_plugin"


def test_unregister_plugin():
    """测试注销插件"""
    from core.plugins.registry import PluginRegistry

    # Arrange
    registry = PluginRegistry()
    plugin = PluginDefinition(
        id="temp_plugin",
        name="Temporary Plugin",
        type=PluginType.TOOL,
    )
    registry.register(plugin)

    # Act
    result = registry.unregister("temp_plugin")

    # Assert
    assert result is True
    assert registry.get_plugin("temp_plugin") is None


def test_activate_plugin():
    """测试激活插件"""
    from core.plugins.registry import PluginRegistry

    # Arrange
    registry = PluginRegistry()
    plugin = PluginDefinition(
        id="test_plugin",
        name="Test Plugin",
        type=PluginType.TOOL,
        status=PluginStatus.LOADED,
    )
    registry.register(plugin)

    # Act
    result = registry.activate("test_plugin")

    # Assert
    assert result is True
    activated_plugin = registry.get_plugin("test_plugin")
    assert activated_plugin.status == PluginStatus.ACTIVE


def test_deactivate_plugin():
    """测试停用插件"""
    from core.plugins.registry import PluginRegistry

    # Arrange
    registry = PluginRegistry()
    plugin = PluginDefinition(
        id="test_plugin",
        name="Test Plugin",
        type=PluginType.TOOL,
        status=PluginStatus.ACTIVE,
    )
    registry.register(plugin)

    # Act
    result = registry.deactivate("test_plugin")

    # Assert
    assert result is True
    deactivated_plugin = registry.get_plugin("test_plugin")
    assert deactivated_plugin.status == PluginStatus.INACTIVE


def test_get_stats():
    """测试获取插件统计信息"""
    from core.plugins.registry import PluginRegistry

    # Arrange
    registry = PluginRegistry()

    for i in range(3):
        plugin = PluginDefinition(
            id=f"plugin_{i}",
            name=f"Plugin {i}",
            type=PluginType.TOOL,
        )
        registry.register(plugin)

    # Act
    stats = registry.get_stats()

    # Assert
    assert stats["total_plugins"] == 3
    assert stats["by_type"][PluginType.TOOL.value] == 3


def test_find_plugins_by_name():
    """测试按名称查找插件"""
    from core.plugins.registry import PluginRegistry

    # Arrange
    registry = PluginRegistry()

    plugin1 = PluginDefinition(
        id="patent_plugin",
        name="Patent Analysis Plugin",
        type=PluginType.TOOL,
    )

    plugin2 = PluginDefinition(
        id="case_plugin",
        name="Case Analysis Plugin",
        type=PluginType.AGENT,
    )

    registry.register(plugin1)
    registry.register(plugin2)

    # Act
    results = registry.find_plugins(name_pattern="*analysis")

    # Assert
    assert len(results) == 2
    assert all("analysis" in p.name.lower() for p in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
