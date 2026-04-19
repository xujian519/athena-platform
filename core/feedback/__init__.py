from __future__ import annotations
"""
反馈闭环模块
System Feedback Loop Module

实现"实践-认识-再实践"的持续优化循环
"""

from .system_feedback_loop import (
    EffectivenessAssessment,
    EffectivenessLevel,
    ExecutionResult,
    ImprovementAction,
    ImprovementType,
    LearningRecord,
    ProblemDiagnosis,
    SystemFeedbackLoop,
    get_feedback_loop,
    record_and_learn,
)

__all__ = [
    "EffectivenessAssessment",
    "EffectivenessLevel",
    "ExecutionResult",
    "ImprovementAction",
    "ImprovementType",
    "LearningRecord",
    "ProblemDiagnosis",
    "SystemFeedbackLoop",
    "get_feedback_loop",
    "record_and_learn",
]
