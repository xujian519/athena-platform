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

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from .engine import EnhancedLearningEngine
from .types import (
    AdaptationMode,
    Experience,
    LearningMetrics,
    LearningResult,
    LearningStrategy,
)

# =============================================================================
# === 学习配置类 ===
# =============================================================================

@dataclass
class LearningConfig:
    """学习配置"""
    learning_rate: float = 0.01
    batch_size: int = 32
    max_episodes: int = 1000
    gamma: float = 0.99
    epsilon: float = 0.1
    epsilon_decay: float = 0.995
    memory_size: int = 10000
    target_update_freq: int = 100


# =============================================================================
# === 别名和兼容性 ===
# =============================================================================

# 为保持兼容性，提供 LearningEngineV4 作为别名
LearningEngineV4 = EnhancedLearningEngine

# 为保持兼容性，提供 LearningTask 作为 Experience 的别名
LearningTask = Experience


# 全局实例
_learning_engine_v4_instance: EnhancedLearningEngine | None = None


def get_learning_engine_v4(agent_id: str = "default") -> EnhancedLearningEngine:
    """获取学习引擎v4单例"""
    global _learning_engine_v4_instance
    if _learning_engine_v4_instance is None:
        _learning_engine_v4_instance = EnhancedLearningEngine(agent_id=agent_id)
    return _learning_engine_v4_instance


# 导出公共接口
__all__ = [
    "EnhancedLearningEngine",
    "LearningEngineV4",  # 别名
    "LearningStrategy",
    "AdaptationMode",
    "Experience",
    "LearningTask",  # 别名
    "LearningResult",
    "LearningMetrics",
    "LearningConfig",
    "get_learning_engine_v4",
]
