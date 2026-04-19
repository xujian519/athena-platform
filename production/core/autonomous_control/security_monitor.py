#!/usr/bin/env python3
"""
安全监控 - 向后兼容重定向
Security Monitor - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 security_monitor/
原文件已备份为 security_monitor.py.bak

请使用新导入:
    from core.autonomous_control.security_monitor import SecurityMonitor

此文件仅用于向后兼容,将在未来版本中移除。
"""

import warnings

from .security_monitor import (
    AccessPattern,
    AlertType,
    ActionType,
    BehaviorProfile,
    SecurityEvent,
    SecurityLevel,
    SecurityMonitor,
)

# 触发弃用警告
warnings.warn(
    "security_monitor.py 已重构为模块化目录 security_monitor/。\n"
    "请使用新导入: from core.autonomous_control.security_monitor import SecurityMonitor\n"
    "原文件已备份为 security_monitor.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "SecurityMonitor",
    "SecurityLevel",
    "AlertType",
    "ActionType",
    "SecurityEvent",
    "AccessPattern",
    "BehaviorProfile",
]
