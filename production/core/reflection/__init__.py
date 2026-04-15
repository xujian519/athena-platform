#!/usr/bin/env python3
"""
Athena统一反思引擎模块 - 生产环境
Unified Reflection Engine Module - Production

整合三个分散的反思引擎实现，提供统一的反思接口

使用示例:
    from production.core.reflection import (
        UnifiedReflectionEngine,
        ReflectionType,
        ReflectionLevel,
        DomainType,
        get_unified_reflection_engine,
    )

    engine = get_unified_reflection_engine()
    result = await engine.reflect(
        original_prompt="分析专利CN123456789A的新颖性",
        output="该专利具有新颖性...",
        domain=DomainType.PATENT,
        reflection_type=ReflectionType.OUTPUT,
    )
"""

from __future__ import annotations
__version__ = "1.0.0"

# 直接从源文件导入，避免循环导入
import sys
from pathlib import Path

# 添加核心模块路径
core_path = Path(__file__).parent.parent.parent.parent
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

# 导入核心组件（直接从模块文件）
import asyncio
import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ================================
# 枚举定义
# ================================


class ReflectionLevel(Enum):
    """反思级别"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class ReflectionType(Enum):
    """反思类型"""
    OUTPUT = "output"
    EXECUTION = "execution"
    SELECTION = "selection"
    PERFORMANCE = "performance"
    STRATEGY = "strategy"


class ReflectionOutcome(Enum):
    """反思结果等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    TERRIBLE = "terrible"


class DomainType(Enum):
    """专业领域类型"""
    GENERAL = "general"
    LEGAL = "legal"
    PATENT = "patent"
    TECHNICAL = "technical"


class QualityMetric(Enum):
    """通用质量评估指标"""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    RELEVANCE = "relevance"
    USEFULNESS = "usefulness"
    CONSISTENCY = "consistency"


class LegalQualityMetric(Enum):
    """法律质量评估指标"""
    FACTUAL_ACCURACY = "factual_accuracy"
    LEGAL_BASIS = "legal_basis"
    REASONING_LOGIC = "reasoning_logic"
    COMPLETENESS = "completeness"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE = "compliance"


class PatentQualityMetric(Enum):
    """专利质量评估指标"""
    TECHNICAL_DISCLOSURE = "technical_disclosure"
    NOVELTY_ASSESSMENT = "novelty_assessment"
    INVENTIVE_STEP = "inventive_step"
    CLAIM_DRAFTING = "claim_drafting"
    PRIOR_ART_ANALYSIS = "prior_art_analysis"


# ================================
# 导出简化版本（用于生产环境快速使用）
# ================================

# 如果需要完整功能，使用完整模块
try:
    from core.reflection.unified_reflection_engine import (
        GeneralReflectionEvaluator,
        LegalReflectionEvaluator,
        PatentReflectionEvaluator,
        ReflectionCriterion,
        ReflectionEvaluator,
        ReflectionHistory,
        ReflectionScore,
        UnifiedReflectionResult,
    )
    from core.reflection.unified_reflection_engine import (
        UnifiedReflectionEngine as _UnifiedReflectionEngine,
    )
    from core.reflection.unified_reflection_engine import (
        get_unified_reflection_engine as _get_unified_reflection_engine,
    )

    # 重新导出
    UnifiedReflectionEngine = _UnifiedReflectionEngine
    get_unified_reflection_engine = _get_unified_reflection_engine

    __all__ = [
        "__version__",
        # 枚举
        "ReflectionLevel",
        "ReflectionType",
        "ReflectionOutcome",
        "DomainType",
        "QualityMetric",
        "LegalQualityMetric",
        "PatentQualityMetric",
        # 数据模型
        "ReflectionCriterion",
        "ReflectionScore",
        "UnifiedReflectionResult",
        "ReflectionHistory",
        # 评估器
        "ReflectionEvaluator",
        "GeneralReflectionEvaluator",
        "LegalReflectionEvaluator",
        "PatentReflectionEvaluator",
        # 统一引擎
        "UnifiedReflectionEngine",
        "get_unified_reflection_engine",
    ]

except ImportError:
    # 如果无法导入完整模块，提供基础接口
    logger.warning("完整反思模块不可用，使用简化接口")

    def get_unified_reflection_engine(config=None):
        """获取统一反思引擎（简化版本）"""
        logger.info("使用简化版反思引擎")
        return None

    UnifiedReflectionEngine = None

    __all__ = [
        "__version__",
        # 枚举
        "ReflectionLevel",
        "ReflectionType",
        "ReflectionOutcome",
        "DomainType",
        "QualityMetric",
        "LegalQualityMetric",
        "PatentQualityMetric",
        # 统一引擎
        "UnifiedReflectionEngine",
        "get_unified_reflection_engine",
    ]
