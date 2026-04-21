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

from .litigation_strategy_analyzer import (
    LitigationStrategyAnalyzer,
    LitigationType,
    LitigationRole,
    RiskLevel,
    CaseAnalysis
)

from .evidence_organizer import (
    EvidenceOrganizer,
    EvidenceType,
    EvidenceCategory,
    EvidenceReliability,
    Evidence,
    EvidenceChain,
    EvidenceOrganizationResult
)

from .pleading_generator import (
    PleadingGenerator,
    PleadingType,
    LegalArgument,
    PleadingStructure,
    PleadingResult
)

from .trial_assistant import (
    TrialAssistant,
    TrialPhase,
    TrialPoint,
    ExaminationOutline,
    TrialStrategy,
    TrialPreparationGuide
)

from .litigation_supporter import (
    LitigationSupporter,
    LitigationSupportOptions,
    LitigationSupportResult
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
