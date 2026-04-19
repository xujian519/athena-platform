#!/usr/bin/env python3
"""
核心管理模块
智能体管理组件
"""

from __future__ import annotations
from .goal_management_system import (
    Goal,
    GoalManagementSystem,
    GoalPriority,
    GoalStatus,
    ProgressMetric,
    ProgressReport,
    SubGoal,
)

__all__ = [
    "Goal",
    "GoalManagementSystem",
    "GoalPriority",
    "GoalStatus",
    "ProgressMetric",
    "ProgressReport",
    "SubGoal",
]

__version__ = "1.0.0"
__author__ = "Athena Platform Team"
