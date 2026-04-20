from __future__ import annotations
"""
Athena Hook系统

提供事件驱动的Hook机制,支持自动化流程和自定义扩展。

Author: Athena平台团队
Created: 2026-01-20
Version: v2.0.0 (Enhanced)
"""

# 导入基础组件
from .base import HookContext, HookFunction, HookRegistry, HookType, get_global_registry, register_hook

# 导入工作流Hooks
from .workflow_hooks import WorkflowMemoryHooks, create_workflow_memory_hooks

# 导出增强组件（可选导入）
try:
    from .enhanced import (
        HookChain,
        HookChainProcessor,
        HookDebugger,
        HookLifecycleManager,
        HookMiddleware,
        HookPerformanceMonitor,
        HookState,
        HookStatus,
    )
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False


__all__ = [
    # 基础组件
    "HookContext",
    "HookFunction",
    "HookRegistry",
    "HookType",
    "get_global_registry",
    "register_hook",
    # 工作流Hooks
    "WorkflowMemoryHooks",
    "create_workflow_memory_hooks",
]

# 如果增强组件可用，也导出它们
if ENHANCED_AVAILABLE:
    __all__.extend(
        [
            # 增强组件
            "HookLifecycleManager",
            "HookChain",
            "HookChainProcessor",
            "HookMiddleware",
            "HookPerformanceMonitor",
            "HookDebugger",
            "HookState",
            "HookStatus",
            "ENHANCED_AVAILABLE",
        ]
    )
