#!/usr/bin/env python3
from __future__ import annotations
"""
优化版执行模块 - 公共接口
Optimized Execution Module - Public Interface

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

本模块提供智能任务调度和资源动态分配功能。
"""

from .execution_module import OptimizedExecutionModule
from .load_balancer import LoadBalancer
from .resource_monitor import ResourceMonitor
from .scheduler import IntelligentScheduler
from .task_queue import TaskPriorityQueue
from .types import (
    ResourceRequirement,
    ResourceType,
    ResourceUsage,
    Task,
    TaskPriority,
    TaskStatus,
)

__all__ = [
    # 类型定义
    "TaskPriority",
    "TaskStatus",
    "ResourceType",
    "Task",
    "ResourceRequirement",
    "ResourceUsage",
    # 核心类
    "TaskPriorityQueue",
    "IntelligentScheduler",
    "ResourceMonitor",
    "LoadBalancer",
    "OptimizedExecutionModule",
]
