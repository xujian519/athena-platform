#!/usr/bin/env python3
"""
增强学习引擎 - 数据类型
Enhanced Learning Engine - Data Types

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LearningStrategy(Enum):
    """学习策略"""

    SUPERVISED = "supervised"  # 监督学习
    REINFORCEMENT = "reinforcement"  # 强化学习
    UNSUPERVISED = "unsupervised"  # 无监督学习
    TRANSFER = "transfer"  # 迁移学习
    HYBRID = "hybrid"  # 混合学习


class AdaptationMode(Enum):
    """适应模式"""

    PROACTIVE = "proactive"  # 主动适应
    REACTIVE = "reactive"  # 被动适应
    SCHEDULED = "scheduled"  # 定时适应
    ON_DEMAND = "on_demand"  # 按需适应


@dataclass
class Experience:
    """经验数据"""

    id: str
    task: str
    action: str
    result: Any
    reward: float
    context: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningResult:
    """学习结果"""

    success: bool
    strategy_used: LearningStrategy
    performance_score: float
    adaptation_applied: bool
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class LearningMetrics:
    """学习指标"""

    total_experiences: int = 0
    successful_experiences: int = 0
    average_reward: float = 0.0
    learning_rate: float = 0.01
    adaptation_count: int = 0
    pattern_discovered: int = 0
    last_update: datetime = field(default_factory=datetime.now)


__all__ = [
    "LearningStrategy",
    "AdaptationMode",
    "Experience",
    "LearningResult",
    "LearningMetrics",
]
