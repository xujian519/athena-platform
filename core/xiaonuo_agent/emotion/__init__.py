#!/usr/bin/env python3
from __future__ import annotations
"""
情感模块 (Emotion Module)
基于PAD模型的情感管理系统

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

from core.xiaonuo_agent.emotion.emotional_system import (
    EmotionalState,
    EmotionalSystem,
    EmotionalTrigger,
    EmotionCategory,
    StimulusType,
    create_emotional_system,
)

__all__ = [
    "EmotionCategory",
    "EmotionalState",
    "EmotionalSystem",
    "EmotionalTrigger",
    "StimulusType",
    "create_emotional_system",
]
