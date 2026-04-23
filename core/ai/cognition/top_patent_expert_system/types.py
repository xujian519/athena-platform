#!/usr/bin/env python3

"""
顶级专利专家系统 - 数据类型定义
Top Patent Expert System - Data Types

作者: Athena AI系统
创建时间: 2025-12-16
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ExpertConsultation:
    """专家咨询记录"""

    expert_id: str
    expert_type: str  # agent, lawyer, examiner, technical
    consultation_type: str  # writing, legal, examination, technical
    query: str
    response: str
    confidence: float
    reasoning_process: str
    references: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PatentContext:
    """专利分析上下文"""

    technology_field: str
    patent_type: str
    analysis_stage: str
    user_intent: str
    technical_complexity: str
    deadline_requirement: str
    target_jurisdiction: str


@dataclass
class ExpertTeamAnalysis:
    """专家团队分析结果"""

    analysis_id: str
    team_composition: list[dict[str, Any]
    individual_opinions: list[ExpertConsultation]
    consensus_opinion: str
    risk_assessment: dict[str, Any]
    recommendations: list[str]
    next_steps: list[str]
    confidence_score: float
    analysis_time: float
    conclusions: list[str] = field(default_factory=list)


__all__ = ["ExpertConsultation", "PatentContext", "ExpertTeamAnalysis"]

