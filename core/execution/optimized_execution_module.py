#!/usr/bin/env python3
"""
优化版执行模块 - 向后兼容重定向
Optimized Execution Module - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.execution.optimized_execution_module (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.execution.optimized_execution_module import (
        OptimizedExecutionModule,
        Task,
        TaskPriority,
        TaskStatus,
        ResourceType,
        TaskPriorityQueue,
        IntelligentScheduler,
        ResourceMonitor,
        LoadBalancer,
        ResourceRequirement,
        ResourceUsage,
    )

新导入方式:
    from core.execution.optimized_execution_module import (
        OptimizedExecutionModule,
        Task,
        TaskPriority,
        TaskStatus,
        ResourceType,
        TaskPriorityQueue,
        IntelligentScheduler,
        ResourceMonitor,
        LoadBalancer,
        ResourceRequirement,
        ResourceUsage,
    )

⚠️  注意: 导入语句保持不变，但代码现在从模块化目录加载。
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

import warnings

# 导入重构后的模块
from .optimized_execution_module import (
    IntelligentScheduler,
    LoadBalancer,
    OptimizedExecutionModule,
    ResourceMonitor,
    ResourceRequirement,
    ResourceUsage,
    Task,
    TaskPriority,
    TaskPriorityQueue,
    TaskStatus,
)

# 发出弃用警告
warnings.warn(
    "optimized_execution_module.py 已重构为模块化目录 "
    "core.execution.optimized_execution_module/。"
    "导入接口保持不变，代码现在从模块化目录加载。"
    "详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
__all__ = [
    "IntelligentScheduler",
    "LoadBalancer",
    "OptimizedExecutionModule",
    "ResourceMonitor",
    "ResourceRequirement",
    "ResourceUsage",
    "Task",
    "TaskPriority",
    "TaskPriorityQueue",
    "TaskStatus",
]
