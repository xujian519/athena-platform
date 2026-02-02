"""
配置管理模块
提供统一的配置获取和管理功能
"""

from .environment import EnvironmentConfig
from .settings import Settings, settings

# 创建全局配置实例
config = settings

__all__ = ['EnvironmentConfig', 'Settings', 'settings', 'config']