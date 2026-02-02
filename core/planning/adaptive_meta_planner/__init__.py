#!/usr/bin/env python3
"""
自适应元规划器 - 公共接口
Adaptive Meta Planner - Public Interface

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0

此模块提供自适应元规划器的公共接口导出。
重构后的模块位于 adaptive_meta_planner/ 目录下。
"""

# 导入常量
from .constants import (
    DEFAULT_SIMILARITY_THRESHOLD,
    MAX_WORKFLOW_PATTERNS,
    MIN_SIMILARITY_THRESHOLD,
    WORKFLOW_EXPIRY_DAYS,
)

# 导入核心类
from .core import AdaptiveMetaPlanner, get_adaptive_meta_planner, plan_adaptive
from .performance import PerformanceTracker
from .types import StrategyPerformance, WorkflowPattern
from .workflow_reuse import WorkflowReuseManager

# 导入异常类 (从父模块重新导出)
from ..exceptions import (
    ConfigurationError,
    PerformanceTrackingError,
    StrategySelectionError,
    TaskExecutionError,
    TaskValidationError,
    WorkflowExecutionError,
)

# 导出公共接口
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
    # 内部类 (供父模块使用)
    "PerformanceTracker",
    "WorkflowReuseManager",
    # 异常类
    "ConfigurationError",
    "PerformanceTrackingError",
    "StrategySelectionError",
    "TaskExecutionError",
    "TaskValidationError",
    "WorkflowExecutionError",
]
