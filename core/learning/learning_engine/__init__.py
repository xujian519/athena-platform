#!/usr/bin/env python3
"""
学习引擎 - 公共接口
Learning Engine - Public Interface

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

支持机器学习、经验积累、模式识别和自适应调整
"""

# 导入异常
from ..exceptions import (
    AdaptationError,
    ConfigurationError,
    ExperienceStoreError,
    LearningEngineError,
    LearningModuleError,
    ModelSerializationError,
    ModelValidationError,
    OptimizationError,
    PatternRecognitionError,
)
from .adaptive_optimizer import AdaptiveOptimizer
from .engine import LearningEngine
from .experience_store import ExperienceStore
from .knowledge_updater import KnowledgeGraphUpdater
from .pattern_recognizer import PatternRecognizer

# 导出公共接口
__all__ = [
    "LearningEngine",
    "ExperienceStore",
    "PatternRecognizer",
    "AdaptiveOptimizer",
    "KnowledgeGraphUpdater",
    # 异常类
    "LearningModuleError",
    "LearningEngineError",
    "ExperienceStoreError",
    "PatternRecognitionError",
    "OptimizationError",
    "ModelValidationError",
    "ModelSerializationError",
    "AdaptationError",
    "ConfigurationError",
]
