#!/usr/bin/env python3
"""
快速学习机制 - 向后兼容重定向
Rapid Learning - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 core.learning.rapid_learning/
原文件已备份为 rapid_learning.py.bak

请使用新导入:
    from core.learning.rapid_learning import RapidLearningEngine

此文件仅用于向后兼容,将在未来版本中移除。
"""

from __future__ import annotations
import warnings

from .rapid_learning import (
    SKLEARN_AVAILABLE,
    TORCH_AVAILABLE,
    ActiveLearner,
    AdaptationStrategy,
    CurriculumScheduler,
    LearningExperience,
    LearningMode,
    LearningTask,
    LearningType,
    MetaLearner,
    ModelSnapshot,
    PrioritizedReplayBuffer,
    RapidLearningEngine,
    create_learning_task,
    get_learning_stats,
    learn_from_data,
    rapid_learning_engine,
)

# 触发弃用警告
warnings.warn(
    "rapid_learning.py 已重构为模块化目录 core.learning.rapid_learning/。\n"
    "请使用新导入: from core.learning.rapid_learning import RapidLearningEngine\n"
    "原文件已备份为 rapid_learning.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "ActiveLearner",
    "AdaptationStrategy",
    "CurriculumScheduler",
    "LearningExperience",
    "LearningMode",
    "LearningTask",
    "LearningType",
    "MetaLearner",
    "ModelSnapshot",
    "PrioritizedReplayBuffer",
    "RapidLearner",  # 别名
    "RapidLearningEngine",
    "SKLEARN_AVAILABLE",
    "TORCH_AVAILABLE",
    "create_learning_task",
    "get_learning_stats",
    "learn_from_data",
    "rapid_learning_engine",
]


# 为保持兼容性，提供 RapidLearner 作为 RapidLearningEngine 的别名
RapidLearner = RapidLearningEngine
