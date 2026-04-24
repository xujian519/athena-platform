"""
统一注册中心 (UnifiedRegistryCenter)

四层架构：
1. 基础接口层 (base.py) - 定义核心抽象接口
2. 统一实现层 (unified.py) - 提供线程安全的统一实现
3. 专用注册表层 (agent_registry.py等) - 特定领域的注册表
4. 兼容适配层 (adapters/) - 向后兼容的适配器

实施目标 (BEAD-105):
- 整合3个重复的Agent注册表
- 提供统一的注册、查询、健康检查接口
- 支持事件通知和性能监控
- 保持向后兼容性

作者: 徐健 (xujian519@gmail.com)
创建时间: 2026-04-24
"""

from core.registry_center.base import BaseRegistry, RegistryEvent, RegistryEventType
from core.registry_center.unified import UnifiedRegistryCenter
from core.registry_center.agent_registry import UnifiedAgentRegistry

__all__ = [
    # 基础接口
    "BaseRegistry",
    "RegistryEvent",
    "RegistryEventType",

    # 统一实现
    "UnifiedRegistryCenter",

    # 专用注册表
    "UnifiedAgentRegistry",

    # 便捷访问
    "get_registry_center",
    "get_agent_registry",
]


def get_registry_center() -> UnifiedRegistryCenter:
    """获取全局统一注册中心单例"""
    return UnifiedRegistryCenter.get_instance()


def get_agent_registry() -> UnifiedAgentRegistry:
    """获取统一Agent注册表单例"""
    return UnifiedAgentRegistry.get_instance()
