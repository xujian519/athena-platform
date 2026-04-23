#!/usr/bin/env python3
"""
专利组合管理系统

提供完整的专利组合管理功能：
1. 专利清单管理
2. 分类分级
3. 价值评估
4. 维持决策
5. 组合管理
"""

from .maintenance_decider import DecisionType, MaintenanceDecision, MaintenanceDecisionMaker
from .patent_classifier import (
    ClassificationResult,
    GradingResult,
    MaintenanceStrategy,
    PatentClassifier,
    PatentGrade,
    TechnologyField,
)
from .patent_list_manager import PatentListManager, PatentRecord, PatentStatus, PatentType
from .portfolio_manager import PortfolioManager
from .value_assessor import ValueAssessment, ValueAssessor

__all__ = [
    # 清单管理
    "PatentListManager",
    "PatentRecord",
    "PatentStatus",
    "PatentType",

    # 分类分级
    "PatentClassifier",
    "TechnologyField",
    "PatentGrade",
    "MaintenanceStrategy",
    "ClassificationResult",
    "GradingResult",

    # 价值评估
    "ValueAssessor",
    "ValueAssessment",

    # 维持决策
    "MaintenanceDecisionMaker",
    "DecisionType",
    "MaintenanceDecision",

    # 主控制器
    "PortfolioManager",
]
