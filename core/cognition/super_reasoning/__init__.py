#!/usr/bin/env python3
from __future__ import annotations
"""
Athena超级推理引擎 - 公共接口
Athena Super Reasoning Engine - Public Interface

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0

基于超级思维链协议的高级推理系统,为Athena提供深度思维和多维度分析能力。
"""

from .engine import AthenaSuperReasoningEngine
from .types import ReasoningConfig, ReasoningMode, ThinkingPhase, ThinkingState

# 为了兼容性,提供简化的别名
AthenaSuperReasoning = AthenaSuperReasoningEngine
SuperReasoningEngine = AthenaSuperReasoningEngine

__all__ = [
    # 核心引擎
    "AthenaSuperReasoningEngine",
    "AthenaSuperReasoning",
    "SuperReasoningEngine",
    # 类型定义
    "ThinkingPhase",
    "ReasoningMode",
    "ThinkingState",
    "ReasoningConfig",
]
