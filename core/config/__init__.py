"""
配置模块

> 版本: v2.0
> 更新: 2026-04-21

统一配置管理系统
"""

from .unified_settings import Settings, get_settings, settings
from .config_adapter import ConfigAdapter, get_config

__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "ConfigAdapter",
    "get_config",
]
