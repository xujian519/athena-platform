#!/usr/bin/env python3
from __future__ import annotations
"""
可解释认知模块 - 向后兼容重定向
Explainable Cognition Module - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.cognition.explainable
作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0-refactored

--- 迁移指南 ---

旧导入:
  from core.cognition.explainable_cognition_module import ExplainableCognitionModule

新导入:
  from core.cognition.explainable import ExplainableCognitionModule
  # 或
  from core.cognition.explainable.core import ExplainableCognitionModule

--- 文件结构 ---

core/cognition/explainable/
├── __init__.py           # 公共接口导出
├── types.py              # 数据模型 (143行)
├── visualizer.py         # 可视化器 (241行)
└── core.py               # 核心模块 (267行)

总计: ~650行 (原文件: 1178行, 减少约45%)

--- 使用示例 ---

# 推荐导入方式
from core.cognition.explainable import (
    ExplainableCognitionModule,
    ReasoningPath,
    ReasoningStep,
    ReasoningStepType,
    FactorImportance,
    DecisionFactor,
    ReasoningPathVisualizer,
)

# 或单独导入
from core.cognition.explainable import ExplainableCognitionModule

"""

import logging
import warnings

logger = logging.getLogger(__name__)

# 向后兼容重定向
from core.cognition.explainable import (  # type: ignore
    DecisionFactor,
    ExplainableCognitionModule,
    FactorImportance,
    ReasoningPath,
    ReasoningPathVisualizer,
    ReasoningStep,
    ReasoningStepType,
)

# 发出迁移警告
warnings.warn(
    "explainable_cognition_module 已重构，请使用新导入路径: "
    "from core.cognition.explainable import ExplainableCognitionModule",
    DeprecationWarning,
    stacklevel=2,
)

logger.info("⚠️  使用已重构的explainable_cognition_module，建议更新导入路径")

# 导出所有公共接口以保持向后兼容
__all__ = [
    "ExplainableCognitionModule",
    "ReasoningPath",
    "ReasoningStep",
    "ReasoningStepType",
    "FactorImportance",
    "DecisionFactor",
    "ReasoningPathVisualizer",
]
