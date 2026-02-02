#!/usr/bin/env python3
"""
系统管理器 - 公共接口
System Manager - Public Interface

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

支持模块热加载、动态依赖管理、服务注册和健康检查。
"""

from .config_manager import ConfigurationManager
from .dependency_graph import DependencyGraph
from .manager import BaseModule, SystemManager
from .module_loader import ModuleLoader
from .service_registry import ServiceRegistry
from .types import (
    DependencyType,
    HealthStatus,
    ModuleInstance,
    ModuleMetadata,
    ModuleState,
)

# 导出公共接口
__all__ = [
    # 类型
    "ModuleState",
    "DependencyType",
    "HealthStatus",
    "ModuleMetadata",
    "ModuleInstance",
    # 核心类
    "BaseModule",
    "ConfigurationManager",
    "DependencyGraph",
    "ModuleLoader",
    "ServiceRegistry",
    "SystemManager",
]
