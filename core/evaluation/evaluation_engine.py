#!/usr/bin/env python3
from __future__ import annotations
"""
评估引擎 - 向后兼容重定向
Evaluation Engine - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.evaluation.evaluation_engine (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.evaluation.evaluation_engine import (
        EvaluationEngine,
        EvaluationResult,
        MetricsCalculator,
    )

新导入方式:
    from core.evaluation.evaluation_engine import (
        EvaluationEngine,
        EvaluationResult,
        EvaluationCriteria,
        EvaluationLevel,
        EvaluationType,
        MetricsCalculator,
        QualityAssuranceChecker,
        ReflectionEngine,
        ReflectionRecord,
        ReflectionType,
    )
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

import warnings

# 导入重构后的模块
from .evaluation_engine import (
    EvaluationCriteria,
    EvaluationEngine,
    EvaluationLevel,
    EvaluationResult,
    EvaluationType,
    MetricsCalculator,
    QualityAssuranceChecker,
    ReflectionEngine,
    ReflectionRecord,
    ReflectionType,
)

# 发出弃用警告
warnings.warn(
    "evaluation_engine.py 已重构为模块化目录 "
    "core.evaluation.evaluation_engine/。"
    "请更新您的导入语句。详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
__all__ = [
    "EvaluationCriteria",
    "EvaluationEngine",
    "EvaluationLevel",
    "EvaluationResult",
    "EvaluationType",
    "MetricsCalculator",
    "QualityAssuranceChecker",
    "ReflectionEngine",
    "ReflectionRecord",
    "ReflectionType",
]
