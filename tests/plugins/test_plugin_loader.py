#!/usr/bin/env python3
"""
Plugins系统单元测试 - PluginLoader

测试PluginLoader的文件加载功能。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from core.plugins.loader import PluginLoader
from core.plugins.registry import PluginRegistry
from core.plugins.types import PluginDefinition, PluginType, PluginStatus


def test_load_from_file():
    """测试从文件加载插件"""
    # Arrange - 创建临时YAML文件
    plugin_data = {
        "id": "test_plugin",
        "name": "Test Plugin",
        "type": "tool",
        "entry_point": "test_module:TestClass",
        "metadata": {
            "author": "Athena Team",
            "version": "1.0.0",
            "tags": ["test"],
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(plugin_data, f)
        temp_path = Path(f.name)

    try:
        # Act
        loader = PluginLoader()
        plugin = loader.load_from_file(temp_path)

        # Assert
        assert plugin is not None
        assert plugin.id == "test_plugin"
        assert plugin.name == "Test Plugin"
        assert plugin.type == PluginType.TOOL
        assert plugin.entry_point == "test_module:TestClass"
        assert plugin.metadata.author == "Athena Team"
    finally:
        # Cleanup
        temp_path.unlink()


def test_load_from_file_not_found():
    """测试加载不存在的文件"""
    # Arrange
    loader = PluginLoader()

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="插件文件不存在"):
        loader.load_from_file("/nonexistent/file.yaml")


def test_load_from_file_missing_required_field():
    """测试缺少必需字段"""
    # Arrange - 创建缺少id的YAML
    plugin_data = {
        "name": "Test Plugin",
        "type": "tool",
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(plugin_data, f)
        temp_path = Path(f.name)

    try:
        # Act
        loader = PluginLoader()

        # Assert
        with pytest.raises(ValueError, match="缺少必需字段"):
            loader.load_from_file(temp_path)
    finally:
        # Cleanup
        temp_path.unlink()


def test_load_from_file_invalid_type():
    """测试无效的插件类型"""
    # Arrange - 创建无效类型
    plugin_data = {
        "id": "test_plugin",
        "name": "Test Plugin",
        "type": "invalid_type",
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(plugin_data, f)
        temp_path = Path(f.name)

    try:
        # Act
        loader = PluginLoader()

        # Assert
        with pytest.raises(ValueError, match="无效的插件类型"):
            loader.load_from_file(temp_path)
    finally:
        # Cleanup
        temp_path.unlink()


def test_load_from_directory():
    """测试从目录加载插件"""
    # Arrange - 创建临时目录和插件文件
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建3个插件文件
        for i in range(3):
            plugin_data = {
                "id": f"plugin_{i}",
                "name": f"Plugin {i}",
                "type": "tool",
            }

            plugin_file = temp_path / f"plugin_{i}.yaml"
            with open(plugin_file, "w") as f:
                yaml.dump(plugin_data, f)

        # Act
        loader = PluginLoader()
        plugins = loader.load_from_directory(temp_path, register=True)

        # Assert
        assert len(plugins) == 3
        assert loader.registry.get_plugin("plugin_0") is not None
        assert loader.registry.get_plugin("plugin_1") is not None
        assert loader.registry.get_plugin("plugin_2") is not None


def test_load_from_directory_recursive():
    """测试递归加载子目录"""
    # Arrange - 创建嵌套目录结构
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建子目录
        subdir = temp_path / "subdir"
        subdir.mkdir()

        # 创建主目录的插件
        plugin_data_1 = {
            "id": "main_plugin",
            "name": "Main Plugin",
            "type": "tool",
        }
        main_file = temp_path / "main.yaml"
        with open(main_file, "w") as f:
            yaml.dump(plugin_data_1, f)

        # 创建子目录的插件
        plugin_data_2 = {
            "id": "sub_plugin",
            "name": "Sub Plugin",
            "type": "agent",
        }
        sub_file = subdir / "sub.yaml"
        with open(sub_file, "w") as f:
            yaml.dump(plugin_data_2, f)

        # Act
        loader = PluginLoader()

        # 非递归 - 只加载主目录
        plugins_non_recursive = loader.load_from_directory(
            temp_path,
            recursive=False,
        )
        assert len(plugins_non_recursive) == 1

        # 递归 - 加载所有目录
        loader2 = PluginLoader()
        plugins_recursive = loader2.load_from_directory(
            temp_path,
            recursive=True,
        )
        assert len(plugins_recursive) == 2


def test_load_from_custom_registry():
    """测试使用自定义注册表"""
    # Arrange
    custom_registry = PluginRegistry()

    plugin_data = {
        "id": "custom_plugin",
        "name": "Custom Plugin",
        "type": "tool",
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(plugin_data, f)
        temp_path = Path(f.name)

    try:
        # Act
        loader = PluginLoader(registry=custom_registry)
        loader.load_from_directory(temp_path.parent, register=True)

        # Assert - 应该在自定义注册表中
        assert custom_registry.get_plugin("custom_plugin") is not None
        # 不应该在默认注册表中
        default_loader = PluginLoader()
        assert default_loader.registry.get_plugin("custom_plugin") is None
    finally:
        # Cleanup
        temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
