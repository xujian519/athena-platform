#!/usr/bin/env python3
"""
增强学习引擎 - 公共接口
Enhanced Learning Engine - Public Interface

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

基于BaseModule的标准化学习引擎,支持统一接口和学习模型
"""

from .engine import EnhancedLearningEngine
from .types import (
    AdaptationMode,
    Experience,
    LearningMetrics,
    LearningResult,
    LearningStrategy,
)

# 导出公共接口
__all__ = [
    "EnhancedLearningEngine",
    "LearningStrategy",
    "AdaptationMode",
    "Experience",
    "LearningResult",
    "LearningMetrics",
]
