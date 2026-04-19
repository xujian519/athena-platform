#!/usr/bin/env python3
"""
学习引擎 - 向后兼容重定向
Learning Engine - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 learning_engine/
原文件已备份为 learning_engine.py.bak

请使用新导入:
    from core.learning.learning_engine import LearningEngine

此文件仅用于向后兼容,将在未来版本中移除。
"""

import warnings

from .learning_engine import (
    AdaptiveOptimizer,
    ExperienceStore,
    KnowledgeGraphUpdater,
    LearningEngine,
    PatternRecognizer,
)

# 触发弃用警告
warnings.warn(
    "learning_engine.py 已重构为模块化目录 learning_engine/。\n"
    "请使用新导入: from core.learning.learning_engine import LearningEngine\n"
    "原文件已备份为 learning_engine.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "AdaptiveOptimizer",
    "ExperienceStore",
    "KnowledgeGraphUpdater",
    "LearningEngine",
    "PatternRecognizer",
]
