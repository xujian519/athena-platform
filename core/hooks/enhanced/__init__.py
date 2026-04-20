#!/usr/bin/env python3
"""
Hook系统增强模块

提供增强的Hook功能，包括生命周期管理、链式处理、性能监控和调试。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

from .chain import HookChain, HookChainProcessor, HookMiddleware
from .debugger import HookDebugger
from .lifecycle import HookLifecycleManager
from .performance import HookPerformanceMonitor
from .types import (
    BenchmarkResult,
    HookDependency,
    HookMetrics,
    HookResult,
    HookState,
    HookStatus,
    PerformanceReport,
    TraceEntry,
)

__all__ = [
    # 生命周期管理
    "HookLifecycleManager",
    # 链式处理
    "HookMiddleware",
    "HookChain",
    "HookChainProcessor",
    # 性能监控
    "HookPerformanceMonitor",
    # 调试
    "HookDebugger",
    # 数据类型
    "HookState",
    "HookStatus",
    "HookResult",
    "HookMetrics",
    "PerformanceReport",
    "TraceEntry",
    "BenchmarkResult",
    "HookDependency",
]
