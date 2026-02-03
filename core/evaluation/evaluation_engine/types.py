#!/usr/bin/env python3
"""
评估引擎 - 类型定义
Evaluation Engine - Type Definitions

作者: Athena平台团队
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.0.0

定义评估引擎使用的枚举类型和数据类。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EvaluationType(Enum):
    """评估类型"""

    PERFORMANCE = "performance"  # 性能评估
    QUALITY = "quality"  # 质量评估
    ACCURACY = "accuracy"  # 准确性评估
    EFFICIENCY = "efficiency"  # 效率评估
    SAFETY = "safety"  # 安全性评估
    RELIABILITY = "reliability"  # 可靠性评估
    USER_SATISFACTION = "user_satisfaction"  # 用户满意度
    COMPLIANCE = "compliance"  # 合规性评估


class EvaluationLevel(Enum):
    """评估等级"""

    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class ReflectionType(Enum):
    """反思类型"""

    SELF_REFLECTION = "self_reflection"  # 自我反思
    PEER_REVIEW = "peer_review"  # 同行评议
    PERFORMANCE_REVIEW = "performance_review"  # 性能回顾
    INCIDENT_REVIEW = "incident_review"  # 事件回顾
    STRATEGIC_REVIEW = "strategic_review"  # 战略回顾


@dataclass
class EvaluationCriteria:
    """评估标准"""

    id: str
    name: str
    description: str
    weight: float = 1.0
    min_value: float = 0.0
    max_value: float = 100.0
    target_value: float = 80.0
    current_value: float = 0.0
    score: float = 0.0
    status: str = "pending"
    evidence: list[dict[str, Any]] = field(default_factory=list)
    comments: str = ""


@dataclass
class EvaluationResult:
    """评估结果"""

    id: str
    evaluator_id: str
    target_type: str  # 评估目标类型
    target_id: str  # 评估目标ID
    evaluation_type: EvaluationType
    criteria_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    overall_score: float = 0.0
    level: EvaluationLevel = EvaluationLevel.NEEDS_IMPROVEMENT
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflectionRecord:
    """反思记录"""

    id: str
    evaluator_id: str
    target_evaluation_id: str
    reflection_type: ReflectionType
    context: dict[str, Any] = field(default_factory=dict)
    observations: str = ""
    analysis: str = ""
    insights: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    lessons_learned: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# === 别名和兼容性 ===
# =============================================================================

# 为保持兼容性，提供 AssessmentType 作为别名
AssessmentType = EvaluationType


class EvaluationScope(Enum):
    """评估范围"""

    # 系统级别
    SYSTEM = "system"  # 系统整体评估
    MODULE = "module"  # 模块级别评估
    COMPONENT = "component"  # 组件级别评估
    FUNCTION = "function"  # 函数级别评估

    # 业务级别
    WORKFLOW = "workflow"  # 工作流评估
    TASK = "task"  # 任务评估
    OPERATION = "operation"  # 操作评估

    # 数据级别
    DATA_QUALITY = "data_quality"  # 数据质量评估
    DATA_INTEGRITY = "data_integrity"  # 数据完整性评估
    DATA_SECURITY = "data_security"  # 数据安全评估


__all__ = [
    "EvaluationType",
    "AssessmentType",  # 别名
    "EvaluationLevel",
    "EvaluationScope",
    "ReflectionType",
    "EvaluationCriteria",
    "EvaluationResult",
    "ReflectionRecord",
]
