#!/usr/bin/env python3
from __future__ import annotations
"""
Athena超级推理模块
Super Reasoning Module for Athena

提供多阶段、多层次的超级推理能力

作者: Athena AI团队
版本: v1.0.0
"""

from .athena_super_reasoning import (
    AthenaSuperReasoningEngine,
    ConfidenceLevel,
    Hypothesis,
    HypothesisManager,
    NaturalThinkingFlow,
    ReasoningState,
    ThinkingPhase,
    ThoughtNode,
)

__all__ = [
    "AthenaSuperReasoningEngine",
    "ConfidenceLevel",
    "Hypothesis",
    "HypothesisManager",
    "NaturalThinkingFlow",
    "ReasoningState",
    "ThinkingPhase",
    "ThoughtNode",
]
