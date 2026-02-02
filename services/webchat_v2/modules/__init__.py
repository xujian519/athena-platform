#!/usr/bin/env python3
"""
平台模块
模块注册、调用和意图路由

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.0
"""

from .registry import (
    ModuleStatus,
    ModuleDefinition,
    InvokeRequest,
    InvokeResult,
    PlatformModuleRegistry,
)

from .invoker import PlatformModuleInvoker
from .router import XiaonuoIntentRouter

__all__ = [
    "ModuleStatus",
    "ModuleDefinition",
    "InvokeRequest",
    "InvokeResult",
    "PlatformModuleRegistry",
    "PlatformModuleInvoker",
    "XiaonuoIntentRouter",
]
