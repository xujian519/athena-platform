#!/usr/bin/env python3
"""
专利诉讼支持系统

提供完整的专利诉讼支持功能：
1. 诉讼策略分析
2. 证据整理
3. 代理词生成
4. 庭审辅助
5. 综合支持
"""

from .evidence_organizer import (
    Evidence,
    EvidenceCategory,
    EvidenceChain,
    EvidenceOrganizationResult,
    EvidenceOrganizer,
    EvidenceReliability,
    EvidenceType,
)
from .litigation_strategy_analyzer import (
    CaseAnalysis,
    LitigationRole,
    LitigationStrategyAnalyzer,
    LitigationType,
    RiskLevel,
)
from .litigation_supporter import (
    LitigationSupporter,
    LitigationSupportOptions,
    LitigationSupportResult,
)
from .pleading_generator import (
    LegalArgument,
    PleadingGenerator,
    PleadingResult,
    PleadingStructure,
    PleadingType,
)
from .trial_assistant import (
    ExaminationOutline,
    TrialAssistant,
    TrialPhase,
    TrialPoint,
    TrialPreparationGuide,
    TrialStrategy,
)

__all__ = [
    # 策略分析
    "LitigationStrategyAnalyzer",
    "LitigationType",
    "LitigationRole",
    "RiskLevel",
    "CaseAnalysis",

    # 证据整理
    "EvidenceOrganizer",
    "EvidenceType",
    "EvidenceCategory",
    "EvidenceReliability",
    "Evidence",
    "EvidenceChain",
    "EvidenceOrganizationResult",

    # 代理词生成
    "PleadingGenerator",
    "PleadingType",
    "LegalArgument",
    "PleadingStructure",
    "PleadingResult",

    # 庭审辅助
    "TrialAssistant",
    "TrialPhase",
    "TrialPoint",
    "ExaminationOutline",
    "TrialStrategy",
    "TrialPreparationGuide",

    # 主控制器
    "LitigationSupporter",
    "LitigationSupportOptions",
    "LitigationSupportResult",
]
