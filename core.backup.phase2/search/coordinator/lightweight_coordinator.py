#!/usr/bin/env python3
"""
轻量协调器 - 向后兼容重定向
Lightweight Coordinator - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 lightweight_coordinator/
原文件已备份为 lightweight_coordinator.py.bak

请使用新导入:
    from core.search.coordinator.lightweight_coordinator import LightweightCoordinator

此文件仅用于向后兼容,将在未来版本中移除。
"""

import warnings

from .lightweight_coordinator import (
    Alert,
    AlertLevel,
    ConfigItem,
    ConfigType,
    HealthMonitor,
    HealthStatus,
    LightweightCoordinator,
    MetricPoint,
    MetricType,
)

# 触发弃用警告
warnings.warn(
    "lightweight_coordinator.py 已重构为模块化目录 lightweight_coordinator/。\n"
    "请使用新导入: from core.search.coordinator.lightweight_coordinator import LightweightCoordinator\n"
    "原文件已备份为 lightweight_coordinator.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "LightweightCoordinator",
    "HealthMonitor",
    "ConfigType",
    "MetricType",
    "AlertLevel",
    "ConfigItem",
    "MetricPoint",
    "HealthStatus",
    "Alert",
]
