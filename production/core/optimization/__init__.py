#!/usr/bin/env python3
"""
优化模块
Optimization Module

提供从小诺优化管理器的统一导出。

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0
"""

from __future__ import annotations
from .xiaonuo_optimization_manager import (
    OptimizationConfig,
    OptimizationResult,
    XiaonuoOptimizationManager,
    get_optimization_manager,
)

__all__ = [
    "OptimizationConfig",
    "OptimizationResult",
    "XiaonuoOptimizationManager",
    "get_optimization_manager",
]

__version__ = "1.0.0"
