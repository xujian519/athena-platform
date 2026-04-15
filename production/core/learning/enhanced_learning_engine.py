#!/usr/bin/env python3
"""
增强学习引擎 - 向后兼容重定向
Enhanced Learning Engine - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 enhanced_learning_engine/
原文件已备份为 enhanced_learning_engine.py.bak

请使用新导入:
    from core.learning.enhanced_learning_engine import EnhancedLearningEngine

此文件仅用于向后兼容,将在未来版本中移除。
"""

from __future__ import annotations
import warnings

from .enhanced_learning_engine import (
    AdaptationMode,
    EnhancedLearningEngine,
    Experience,
    LearningMetrics,
    LearningResult,
    LearningStrategy,
)

# 触发弃用警告
warnings.warn(
    "enhanced_learning_engine.py 已重构为模块化目录 enhanced_learning_engine/。\n"
    "请使用新导入: from core.learning.enhanced_learning_engine import EnhancedLearningEngine\n"
    "原文件已备份为 enhanced_learning_engine.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "EnhancedLearningEngine",
    "LearningStrategy",
    "AdaptationMode",
    "Experience",
    "LearningResult",
    "LearningMetrics",
]
