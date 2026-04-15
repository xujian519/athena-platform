#!/usr/bin/env python3
from __future__ import annotations
"""
顶级专利专家系统 - 公共接口
Top Patent Expert System - Public Interface

作者: Athena AI系统
创建时间: 2025-12-16
重构时间: 2026-01-27
版本: 2.0.0

集成中国顶级专利代理人、专利律师、专利审查员和技术专家的专家系统
"""

from .analysis import AnalysisMethods
from .expert_selectors import ExpertSelectors
from .response_generators import ResponseGenerators
from .system import TopPatentExpertSystem
from .types import ExpertConsultation, ExpertTeamAnalysis, PatentContext

# 导出公共接口
__all__ = [
    # 核心类
    "TopPatentExpertSystem",
    "ExpertSelectors",
    "ResponseGenerators",
    "AnalysisMethods",
    # 数据类型
    "ExpertConsultation",
    "PatentContext",
    "ExpertTeamAnalysis",
]
