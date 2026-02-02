#!/usr/bin/env python3
"""
快速学习机制 - 类型定义
Rapid Learning - Type Definitions

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LearningType(Enum):
    """学习类型"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    META_LEARNING = "meta_learning"
    FEW_SHOT = "few_shot"
    SELF_SUPERVISED = "self_supervised"


class LearningMode(Enum):
    """学习模式"""
    ONLINE = "online"
    INCREMENTAL = "incremental"
    BATCH = "batch"
    ACTIVE = "active"
    CURRICULUM = "curriculum"


class AdaptationStrategy(Enum):
    """适应策略"""
    GRADIENT_DESCENT = "gradient_descent"
    EVOLUTIONARY = "evolutionary"
    NEURAL_ARCHITECTURE = "neural_architecture"
    TRANSFER = "transfer"
    META_OPTIMIZATION = "meta_optimization"


@dataclass
class LearningExperience:
    """学习经验"""
    experience_id: str
    task_type: str
    input_data: Any
    output_data: Any
    context: dict[str, Any]
    reward: float
    timestamp: datetime
    importance: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningTask:
    """学习任务"""
    task_id: str
    task_type: LearningType
    learning_mode: LearningMode
    data_source: str
    model_type: str
    hyperparameters: dict[str, Any]
    performance_metric: str
    target_performance: float
    max_episodes: int = 1000
    patience: int = 100
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ModelSnapshot:
    """模型快照"""
    snapshot_id: str
    model_type: str
    model_data: bytes
    performance: float
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "LearningType",
    "LearningMode",
    "AdaptationStrategy",
    "LearningExperience",
    "LearningTask",
    "ModelSnapshot",
]
