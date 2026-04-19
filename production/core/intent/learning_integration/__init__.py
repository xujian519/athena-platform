#!/usr/bin/env python3
"""
意图识别学习引擎集成模块
Intent Recognition Learning Engines Integration Module

提供P0-P3所有学习引擎的统一集成:
- P0: 自主学习 - 性能监控和优化
- P1: 在线学习 - 模型持续优化
- P2: 强化学习 - 对话策略优化
- P3: 元学习 - 快速适应新领域

使用示例:
    from production.core.intent.learning_integration import get_intent_learning_orchestrator

    # 获取编排器
    orchestrator = get_intent_learning_orchestrator()

    # 记录意图识别经验
    await orchestrator.record_experience(
        query="搜索专利",
        predicted_intent="PATENT_SEARCH",
        confidence=0.95,
        response_time_ms=50.0,
        true_intent="PATENT_SEARCH",
    )

    # 触发系统优化
    await orchestrator.optimize_system()

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

from __future__ import annotations
from .intent_learning_orchestrator import (
    IntentLearningOrchestrator,
    IntentRecognitionExperience,
    LearningMetrics,
    LearningPriority,
    get_intent_learning_orchestrator,
)
from .performance_monitor import (
    AlertType,
    PerformanceAlert,
    PerformanceLevel,
    PerformanceMonitor,
    PerformanceSnapshot,
)

__all__ = [
    # 编排器
    "IntentLearningOrchestrator",
    "get_intent_learning_orchestrator",
    # 数据类
    "IntentRecognitionExperience",
    "LearningMetrics",
    "LearningPriority",
    # 性能监控
    "PerformanceMonitor",
    "PerformanceSnapshot",
    "PerformanceAlert",
    "PerformanceLevel",
    "AlertType",
]

__version__ = "1.0.0"
__author__ = "Athena AI Team"
