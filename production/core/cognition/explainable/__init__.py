#!/usr/bin/env python3
from __future__ import annotations
"""
可解释认知模块 - 重构版本
Explainable Cognition Module - Refactored Version

本模块实现推理路径可视化和决策因子权重展示

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0-refactored
"""

# 数据模型
# 核心模块
from .core import ExplainableCognitionModule
from .types import (
    DecisionFactor,
    FactorImportance,
    ReasoningPath,
    ReasoningStep,
    ReasoningStepType,
)

# 可视化
from .visualizer import ReasoningPathVisualizer

__all__ = [
    # 数据模型
    "ReasoningStepType",
    "FactorImportance",
    "ReasoningStep",
    "DecisionFactor",
    "ReasoningPath",
    # 可视化
    "ReasoningPathVisualizer",
    # 核心模块
    "ExplainableCognitionModule",
]

__version__ = "2.1.0"
