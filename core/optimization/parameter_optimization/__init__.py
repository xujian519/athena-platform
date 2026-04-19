#!/usr/bin/env python3
from __future__ import annotations
"""
参数优化模块
Parameter Optimization Module

借鉴Heretic项目的Optuna TPE优化算法,
为Athena平台提供自动化参数调优能力。

核心功能:
1. 提示词参数优化
2. 记忆检索参数优化
3. 多模态融合权重优化
4. 跨Agent协作参数优化

作者: Athena平台团队
创建时间: 2025-01-04
版本: v1.0.0 "Heretic技术借鉴"
"""


__all__ = [
    "BaseParameterOptimizer",
    "EvaluationMetrics",
    "MemoryRetrievalOptimizer",
    "MultimodalFusionOptimizer",
    "PromptParameterOptimizer",
    "StudyManager",
]

__version__ = "1.0.0"
__author__ = "Athena Platform Team"

# 模块信息
MODULE_INFO = {
    "name": "parameter_optimization",
    "version": "1.0.0",
    "description": "借鉴Heretic的Optuna TPE优化算法的参数优化系统",
    "technologies": ["Optuna", "TPE", "参数优化", "超参数调优"],
    "inspired_by": "Heretic (p-e-w/heretic)",
    "license": "AGPL-3.0+",
}
