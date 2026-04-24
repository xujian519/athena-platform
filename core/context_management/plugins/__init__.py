#!/usr/bin/env python3
"""
上下文插件系统 - Phase 2.3动态加载机制

Context Plugin System - 灵活的插件机制，支持动态加载和热插拔

核心组件:
- ContextPluginRegistry: 插件注册表
- PluginLoader: 插件加载器
- PluginConfig: 插件配置管理
- CompressionPlugin: 上下文压缩插件
- ValidationPlugin: 上下文验证插件
- MetricsPlugin: 性能指标收集插件

特性:
- 动态加载: 运行时加载/卸载插件
- 依赖检查: 自动检查插件依赖关系
- 热重载: 配置变更时自动重载
- 生命周期管理: initialize -> execute -> shutdown
- 线程安全: 异步锁保护共享状态

作者: Athena平台团队
创建时间: 2026-04-24
版本: v2.3.0 "插件机制"
"""

from .registry import ContextPluginRegistry
from .loader import PluginLoader, PluginConfig
from .compression_plugin import CompressionPlugin
from .validation_plugin import ValidationPlugin
from .metrics_plugin import MetricsPlugin

__all__ = [
    "ContextPluginRegistry",
    "PluginLoader",
    "PluginConfig",
    "CompressionPlugin",
    "ValidationPlugin",
    "MetricsPlugin",
]
