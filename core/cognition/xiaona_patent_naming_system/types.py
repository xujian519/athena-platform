#!/usr/bin/env python3
"""
小娜专利命名系统 - 类型定义
Xiaona Patent Naming System - Type Definitions

作者: 小娜·天秤女神
创建时间: 2025-12-17
重构时间: 2026-01-27
版本: v2.0.0
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PatentType(Enum):
    """专利类型"""

    INVENTION = "invention"  # 发明专利
    UTILITY_MODEL = "utility_model"  # 实用新型专利
    DESIGN = "design"  # 外观设计专利


class NamingStyle(Enum):
    """命名风格"""

    TECHNICAL = "technical"  # 技术导向型
    FUNCTIONAL = "functional"  # 功能导向型
    INNOVATION = "innovation"  # 创新导向型
    APPLICATION = "application"  # 应用导向型


@dataclass
class PatentNamingRequest:
    """专利命名请求"""

    patent_type: PatentType
    technical_field: str
    invention_description: str
    key_features: list[str]
    application_scenarios: list[str]
    innovation_points: list[str]
    naming_preferences: list[str] = field(default_factory=list)
    naming_style: NamingStyle = NamingStyle.TECHNICAL
    special_requirements: list[str] = field(default_factory=list)
    client_info: dict[str, Any] | None = None


@dataclass
class PatentNamingResult:
    """专利命名结果"""

    patent_name: str
    alternative_names: list[str]
    naming_rationale: str
    technical_highlights: list[str]
    innovation_highlights: list[str]
    compliance_check: dict[str, Any]
    naming_confidence: float
    professional_insights: list[str]
    recommendations: list[str]
