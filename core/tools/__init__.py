from __future__ import annotations
"""
Athena工具分组管理系统

提供工具注册、分组、选择和性能管理功能。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.1.0 "Phase 1 - Tool Groups"
"""

from .base import (
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolPerformance,
    ToolPriority,
    ToolRegistry,
    get_global_registry,
)
from .selector import SelectionScore, SelectionStrategy, ToolSelector
from .tool_group import GroupActivationRule, ToolGroup, ToolGroupDef
from .tool_manager import ToolManager, ToolSelectionResult, get_tool_manager

# 导入自动注册模块（触发生产工具自动注册）
from . import auto_register  # noqa: F401

__all__ = [
    "ActivationRule",
    # 工具分组 (Phase 1)
    "GroupActivationRule",
    "SelectionScore",
    # 选择器
    "SelectionStrategy",
    "ToolCapability",
    # 基础类型
    "ToolCategory",
    "ToolDefinition",
    "ToolGroup",
    "ToolGroupDef",
    "ToolManager",
    "ToolPerformance",
    "ToolPriority",
    # 注册中心
    "ToolRegistry",
    "ToolSelectionResult",
    "ToolSelector",
    "get_global_registry",
    "get_tool_manager",
    # 工具组定义
    "groups",
]
