#!/usr/bin/env python3
from __future__ import annotations
"""
优化版执行模块 - 类型定义（重定向到统一类型）
Optimized Execution Module - Type Definitions (Redirect to Shared Types)

注意: 所有类型定义已迁移到 core/execution/shared_types.py
此文件仅作为向后兼容的重定向层。

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

# 从统一的 shared_types.py 导入所有类型定义
from ...shared_types import (
    ResourceRequirement,
    ResourceType,
    ResourceUsage,
    Task,
    TaskPriority,
    TaskQueue,
    TaskResult,
    TaskStatus,
)

__all__ = [
    "TaskPriority",
    "TaskStatus",
    "ResourceType",
    "Task",
    "ResourceRequirement",
    "ResourceUsage",
    "TaskQueue",
    "TaskResult",
]
