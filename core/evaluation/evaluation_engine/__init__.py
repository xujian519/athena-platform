#!/usr/bin/env python3
from __future__ import annotations
"""
评估引擎 - 公共接口
Evaluation Engine - Public Interface

作者: Athena平台团队
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.0.0

此模块提供评估引擎的公共接口导出。
"""

# 导入类型定义
# 导入核心类
from .engine import EvaluationEngine
from .metrics import MetricsCalculator
from .qa_checker import QualityAssuranceChecker
from .reflection import ReflectionEngine
from .types import (
    EvaluationCriteria,
    EvaluationLevel,
    EvaluationResult,
    EvaluationType,
    ReflectionRecord,
    ReflectionType,
)

# 导出公共接口
__all__ = [
    # 类型
    "EvaluationCriteria",
    "EvaluationLevel",
    "EvaluationResult",
    "EvaluationType",
    "ReflectionRecord",
    "ReflectionType",
    # 核心类
    "EvaluationEngine",
    "MetricsCalculator",
    "QualityAssuranceChecker",
    "ReflectionEngine",
]
