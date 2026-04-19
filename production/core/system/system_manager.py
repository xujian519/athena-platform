#!/usr/bin/env python3
"""
系统管理器 - 向后兼容重定向
System Manager - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 core.system.system_manager/
原文件已备份为 system_manager.py.bak

请使用新导入:
    from core.system.system_manager import SystemManager

此文件仅用于向后兼容,将在未来版本中移除。
"""

import warnings

from .system_manager import (
    ConfigurationManager,
    DependencyGraph,
    DependencyType,
    HealthStatus,
    ModuleInstance,
    ModuleLoader,
    ModuleMetadata,
    ModuleState,
    ServiceRegistry,
    SystemManager,
)

# 触发弃用警告
warnings.warn(
    "system_manager.py 已重构为模块化目录 core.system.system_manager/。\n"
    "请使用新导入: from core.system.system_manager import SystemManager\n"
    "原文件已备份为 system_manager.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "ConfigurationManager",
    "DependencyGraph",
    "DependencyType",
    "HealthStatus",
    "ModuleInstance",
    "ModuleLoader",
    "ModuleMetadata",
    "ModuleState",
    "ServiceRegistry",
    "SystemManager",
]
