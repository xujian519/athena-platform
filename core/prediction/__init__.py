#!/usr/bin/env python3
from __future__ import annotations
"""
预测模块
Prediction Module

提供错误预测和预防功能:
- 扩展错误模式库(27种错误模式)
- 增强错误预测器(机器学习)
- 特征工程与模型集成

作者: Athena平台团队
创建时间: 2025-12-27
版本: v2.0.0
"""

# 原有预测器(基础版)
# 增强错误预测器
from .enhanced_error_predictor import (
    EnhancedErrorPredictor,
    FeatureVector,
    PredictionModel,
    PredictionResult,
    get_enhanced_predictor,
)
from .extended_error_patterns import (
    BaseErrorPattern as OriginalErrorPattern,
)

# 扩展错误模式库
from .extended_error_patterns import (
    ErrorPattern,
    ErrorPatternFeatures,
    ExtendedErrorPattern,
    get_error_pattern_features,
    get_error_patterns_by_category,
    get_high_severity_patterns,
    get_prevention_strategies,
    get_recovery_strategies,
)
from .predictive_error_detector import (
    ErrorMetrics,
    ErrorPrediction,
    PredictiveErrorDetector,
    RiskLevel,
    get_predictive_detector,
)
from .predictive_error_detector import (
    ErrorPattern as BaseErrorPattern,
)

__all__ = [
    "BaseErrorPattern",
    # 增强预测器
    "EnhancedErrorPredictor",
    "ErrorMetrics",
    # 扩展错误模式
    "ErrorPattern",
    "ErrorPatternFeatures",
    "ErrorPrediction",
    "ExtendedErrorPattern",
    "FeatureVector",
    "OriginalErrorPattern",
    "PredictionModel",
    "PredictionResult",
    # 原有组件(兼容)
    "PredictiveErrorDetector",
    "RiskLevel",
    "get_enhanced_predictor",
    "get_error_pattern_features",
    "get_error_patterns_by_category",
    "get_high_severity_patterns",
    "get_predictive_detector",
    "get_prevention_strategies",
    "get_recovery_strategies",
]

__version__ = "2.0.0"
