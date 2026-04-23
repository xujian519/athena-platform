#!/usr/bin/env python3
"""
插件加载器

从文件系统加载插件定义。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

import yaml

from .registry import PluginRegistry
from .types import PluginDefinition, PluginType, PluginMetadata, PluginStatus

logger = logging.getLogger(__name__)


class PluginLoader:
    """插件加载器

    从文件系统加载插件定义并注册到注册表。
    """

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """初始化加载器

        Args:
            registry: 插件注册表，默认创建新的
        """
        self.registry = registry or PluginRegistry()
        logger.info("📦 插件加载器已初始化")

    def load_from_file(self, file_path: str | Path) -> Optional[PluginDefinition]:
        """从文件加载插件

        Args:
            file_path: 文件路径（.yaml或.yml）

        Returns:
            PluginDefinition | None: 插件定义，失败返回None

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"插件文件不存在: {file_path}")

        # 读取YAML文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析错误: {e}")

        # 解析插件定义
        plugin = self._parse_plugin_definition(data, file_path)

        logger.info(f"✅ 从文件加载插件: {plugin.id} - {plugin.name}")
        return plugin

    def load_from_directory(
        self,
        directory: str | Path,
        recursive: bool = False,
        register: bool = True,
    ) -> List[PluginDefinition]:
        """从目录加载插件

        Args:
            directory: 目录路径
            recursive: 是否递归加载子目录
            register: 是否自动注册到注册表

        Returns:
            list[PluginDefinition]: 加载的插件列表
        """
        directory = Path(directory)
        plugins = []

        if not directory.exists():
            logger.warning(f"⚠️ 插件目录不存在: {directory}")
            return plugins

        # 查找所有YAML文件
        pattern = "**/*.yaml" if recursive else "*.yaml"
        yaml_files = list(directory.glob(pattern))
        yaml_files.extend(directory.glob(pattern.replace("yaml", "yml")))

        logger.info(f"📂 在目录中找到 {len(yaml_files)} 个插件文件: {directory}")

        # 加载每个文件
        for yaml_file in yaml_files:
            try:
                plugin = self.load_from_file(yaml_file)
                plugins.append(plugin)

                # 自动注册
                if register:
                    self.registry.register(plugin)
            except Exception as e:
                logger.error(f"❌ 加载插件失败 {yaml_file}: {e}")

        logger.info(f"✅ 成功加载 {len(plugins)} 个插件")
        return plugins

    def load_plugin_module(self, plugin: PluginDefinition) -> Any:
        """加载插件模块

        Args:
            plugin: 插件定义

        Returns:
            Any: 插件模块实例

        Raises:
            ImportError: 模块加载失败
            AttributeError: 入口点不存在
        """
        if not plugin.entry_point:
            raise ValueError(f"插件 {plugin.id} 没有入口点")

        try:
            # 解析入口点（如 module.submodule:ClassName）
            if ":" in plugin.entry_point:
                module_path, class_name = plugin.entry_point.split(":")
                module = importlib.import_module(module_path)
                plugin_class = getattr(module, class_name)
                return plugin_class()
            else:
                # 只导入模块
                return importlib.import_module(plugin.entry_point)
        except ImportError as e:
            logger.error(f"❌ 导入插件模块失败 {plugin.id}: {e}")
            raise
        except AttributeError as e:
            logger.error(f"❌ 入口点不存在 {plugin.id}: {e}")
            raise

    def _parse_plugin_definition(
        self,
        data: dict,
        file_path: Path,
    ) -> PluginDefinition:
        """解析插件定义

        Args:
            data: YAML数据
            file_path: 文件路径

        Returns:
            PluginDefinition: 插件定义

        Raises:
            ValueError: 数据格式错误
        """
        # 验证必需字段
        required_fields = ["id", "name", "type"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")

        # 解析类型
        try:
            plugin_type = PluginType(data["type"])
        except ValueError:
            valid_types = [t.value for t in PluginType]
            raise ValueError(
                f"无效的插件类型 '{data['type']}'，"
                f"有效值为: {valid_types}"
            )

        # 解析状态（可选）
        status = PluginStatus.LOADED
        if "status" in data:
            try:
                status = PluginStatus(data["status"])
            except ValueError:
                logger.warning(f"无效的状态 '{data['status']}'，使用默认值")

        # 解析元数据
        metadata_data = data.get("metadata", {})
        metadata = PluginMetadata(
            author=metadata_data.get("author"),
            version=metadata_data.get("version", "1.0.0"),
            description=metadata_data.get("description", ""),
            tags=metadata_data.get("tags", []),
            license=metadata_data.get("license", "MIT"),
            homepage=metadata_data.get("homepage", ""),
            repository=metadata_data.get("repository", ""),
            dependencies=metadata_data.get("dependencies", []),
            python_version=metadata_data.get("python_version", "3.9+"),
            athena_version=metadata_data.get("athena_version", "1.0.0"),
        )

        # 创建插件定义
        plugin = PluginDefinition(
            id=data["id"],
            name=data["name"],
            type=plugin_type,
            status=status,
            metadata=metadata,
            entry_point=data.get("entry_point", ""),
            config=data.get("config", {}),
            enabled=data.get("enabled", True),
            skills=data.get("skills", []),
            path=str(file_path),
        )

        return plugin


__all__ = [
    "PluginLoader",
]
