#!/usr/bin/env python3
"""
插件数据类型定义

定义Plugins系统的核心数据结构。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """插件状态"""

    LOADED = "loaded"  # 已加载
    ACTIVE = "active"  # 激活中
    INACTIVE = "inactive"  # 未激活
    ERROR = "error"  # 错误状态
    UNLOADED = "unloaded"  # 已卸载


class PluginType(Enum):
    """插件类型"""

    AGENT = "agent"  # Agent插件
    TOOL = "tool"  # 工具插件
    MIDDLEWARE = "middleware"  # 中间件插件
    OBSERVER = "observer"  # 观察者插件
    EXECUTOR = "executor"  # 执行器插件


@dataclass
class PluginMetadata:
    """插件元数据"""

    author: Optional[str] = None
    version: str = "1.0.0"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    license: str = "MIT"
    homepage: str = ""
    repository: str = ""
    dependencies: list[str] = field(default_factory=list)
    python_version: str = "3.9+"
    athena_version: str = "1.0.0"


@dataclass
class PluginDefinition:
    """插件定义"""

    id: str  # 插件唯一标识
    name: str  # 插件名称
    type: PluginType  # 插件类型
    status: PluginStatus = PluginStatus.LOADED
    metadata: PluginMetadata | None = None
    entry_point: str = ""  # 入口点（如module.submodule:ClassName）
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    skills: list[str] = field(default_factory=list)  # 提供的技能列表
    path: Optional[str] = None  # 插件路径

    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = PluginMetadata()

    def is_active(self) -> bool:
        """检查插件是否激活"""
        return self.status == PluginStatus.ACTIVE

    def is_enabled(self) -> bool:
        """检查插件是否启用"""
        return self.enabled

    def can_load(self) -> bool:
        """检查插件是否可加载"""
        return self.enabled and self.status != PluginStatus.ERROR


__all__ = [
    "PluginStatus",
    "PluginType",
    "PluginMetadata",
    "PluginDefinition",
]
