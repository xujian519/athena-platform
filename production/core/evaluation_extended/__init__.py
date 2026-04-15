#!/usr/bin/env python3
"""
Athena扩展评估引擎模块 - 生产环境
Extended Evaluation Engine Module - Production

提供多种类型的扩展评估能力

使用示例:
    from production.core.evaluation_extended import (
        ExtendedEvaluationEngine,
        ExtendedEvaluationType,
        get_extended_evaluation_engine,
    )

    engine = get_extended_evaluation_engine()
    result = await engine.evaluate(
        evaluation_type=ExtendedEvaluationType.SECURITY,
        target_type="api",
        target_id="api_001",
        data={"encryption_enabled": True},
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

# 导入基础类型
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ================================
# 枚举定义
# ================================


class ExtendedEvaluationType(Enum):
    """扩展评估类型"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SECURITY = "security"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    USER_EXPERIENCE = "user_experience"
    SCALABILITY = "scalability"
    EFFICIENCY = "efficiency"
    COMPLIANCE = "compliance"
    INNOVATION = "innovation"


class RiskLevel(Enum):
    """风险等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class TrendDirection(Enum):
    """趋势方向"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


# ================================
# 导出完整模块
# ================================

# 如果需要完整功能，使用完整模块
try:
    from core.evaluation.extended_evaluation_engine import (
        BenchmarkResult,
        ExtendedEvaluationResult,
        ExtendedEvaluator,
        ReliabilityEvaluator,
        RiskAssessment,
        SecurityEvaluator,
        TrendAnalysis,
        UserExperienceEvaluator,
    )
    from core.evaluation.extended_evaluation_engine import (
        ExtendedEvaluationEngine as _ExtendedEvaluationEngine,
    )
    from core.evaluation.extended_evaluation_engine import (
        get_extended_evaluation_engine as _get_extended_evaluation_engine,
    )

    # 重新导出
    ExtendedEvaluationEngine = _ExtendedEvaluationEngine
    get_extended_evaluation_engine = _get_extended_evaluation_engine

    __all__ = [
        "__version__",
        # 枚举
        "ExtendedEvaluationType",
        "RiskLevel",
        "TrendDirection",
        # 数据模型
        "RiskAssessment",
        "TrendAnalysis",
        "BenchmarkResult",
        "ExtendedEvaluationResult",
        # 评估器
        "ExtendedEvaluator",
        "SecurityEvaluator",
        "ReliabilityEvaluator",
        "UserExperienceEvaluator",
        # 扩展引擎
        "ExtendedEvaluationEngine",
        "get_extended_evaluation_engine",
    ]

except ImportError:
    # 如果无法导入完整模块，提供基础接口
    logger.warning("完整评估模块不可用，使用简化接口")

    def get_extended_evaluation_engine(config=None):
        """获取扩展评估引擎（简化版本）"""
        logger.info("使用简化版评估引擎")
        return None

    ExtendedEvaluationEngine = None

    __all__ = [
        "__version__",
        # 枚举
        "ExtendedEvaluationType",
        "RiskLevel",
        "TrendDirection",
        # 扩展引擎
        "ExtendedEvaluationEngine",
        "get_extended_evaluation_engine",
    ]
