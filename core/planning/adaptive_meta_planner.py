#!/usr/bin/env python3
"""
自适应元规划器 - 向后兼容重定向
Adaptive Meta Planner - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.planning.adaptive_meta_planner (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.planning.adaptive_meta_planner import AdaptiveMetaPlanner

新导入方式:
    from core.planning.adaptive_meta_planner import (
        AdaptiveMetaPlanner,
        get_adaptive_meta_planner,
        plan_adaptive,
        WorkflowReuseManager,
        PerformanceTracker,
    )

    # 使用便捷函数
    from core.planning.adaptive_meta_planner import plan_adaptive

    result = await plan_adaptive(task)
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

import warnings

# 导入重构后的模块
from .adaptive_meta_planner import (
    DEFAULT_SIMILARITY_THRESHOLD,
    MAX_WORKFLOW_PATTERNS,
    MIN_SIMILARITY_THRESHOLD,
    WORKFLOW_EXPIRY_DAYS,
    AdaptiveMetaPlanner,
    ConfigurationError,
    PerformanceTrackingError,
    StrategyPerformance,
    StrategySelectionError,
    TaskExecutionError,
    TaskValidationError,
    WorkflowExecutionError,
    WorkflowPattern,
    get_adaptive_meta_planner,
    plan_adaptive,
)

# 发出弃用警告
warnings.warn(
    "adaptive_meta_planner.py 已重构为模块化目录 core.planning.adaptive_meta_planner/。"
    "请更新您的导入语句。详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
__all__ = [
    # 常量
    "MIN_SIMILARITY_THRESHOLD",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "MAX_WORKFLOW_PATTERNS",
    "WORKFLOW_EXPIRY_DAYS",
    # 核心类
    "AdaptiveMetaPlanner",
    "get_adaptive_meta_planner",
    "plan_adaptive",
    # 数据模型
    "StrategyPerformance",
    "WorkflowPattern",
    # 异常类
    "ConfigurationError",
    "PerformanceTrackingError",
    "StrategySelectionError",
    "TaskExecutionError",
    "TaskValidationError",
    "WorkflowExecutionError",
]
