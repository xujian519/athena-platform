#!/usr/bin/env python3
"""
目标管理系统 - 向后兼容重定向
Goal Management System - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.management.goal_management_system (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.management.goal_management_system import (
        GoalStatus,
        GoalPriority,
        MetricType,
        Goal,
        SubGoal,
        ProgressMetric,
        ProgressReport,
        GoalManagementSystem,
        GoalManager,
        ProgressAnalyzer,
        GoalOptimizer,
        NotificationSystem,
    )

新导入方式:
    from core.management.goal_management_system import (
        GoalStatus,
        GoalPriority,
        MetricType,
        Goal,
        SubGoal,
        ProgressMetric,
        ProgressReport,
        GoalManagementSystem,
        GoalManager,
        ProgressAnalyzer,
        GoalOptimizer,
        NotificationSystem,
    )

⚠️  注意: 导入语句保持不变，但代码现在从模块化目录加载。
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

from __future__ import annotations
import warnings

# 导入重构后的模块
from .goal_management_system import (
    Goal,
    GoalDecomposer,
    GoalManagementSystem,
    GoalOptimizer,
    GoalPriority,
    GoalStatus,
    MetricType,
    NotificationSystem,
    ProgressAnalyzer,
    ProgressMetric,
    ProgressReport,
    SubGoal,
    main,
)

# 发出弃用警告
warnings.warn(
    "goal_management_system.py 已重构为模块化目录 "
    "core.management.goal_management_system/。"
    "导入接口保持不变，代码现在从模块化目录加载。"
    "详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
__all__ = [
    # 类型定义
    "GoalStatus",
    "GoalPriority",
    "MetricType",
    "Goal",
    "SubGoal",
    "ProgressMetric",
    "ProgressReport",
    # 主管理类
    "GoalManagementSystem",
    # 别名 (向后兼容)
    "GoalManager",
    # 分析器
    "ProgressAnalyzer",
    "GoalOptimizer",
    "NotificationSystem",
    # 分解器
    "GoalDecomposer",
    # 示例函数
    "main",
]

# 向后兼容别名
GoalManager = GoalManagementSystem
