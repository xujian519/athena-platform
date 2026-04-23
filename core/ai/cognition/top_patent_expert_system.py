#!/usr/bin/env python3
"""
顶级专利专家系统 - 向后兼容重定向
Top Patent Expert System - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 top_patent_expert_system/
原文件已备份为 top_patent_expert_system.py.bak

请使用新导入:
    from core.cognition.top_patent_expert_system import TopPatentExpertSystem

此文件仅用于向后兼容,将在未来版本中移除。
"""

import warnings

from .top_patent_expert_system import (
    AnalysisMethods,
    ExpertConsultation,
    ExpertSelectors,
    ExpertTeamAnalysis,
    PatentContext,
    ResponseGenerators,
    TopPatentExpertSystem,
)

# 触发弃用警告
warnings.warn(
    "top_patent_expert_system.py 已重构为模块化目录 top_patent_expert_system/。\n"
    "请使用新导入: from core.cognition.top_patent_expert_system import TopPatentExpertSystem\n"
    "原文件已备份为 top_patent_expert_system.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "TopPatentExpertSystem",
    "ExpertSelectors",
    "ResponseGenerators",
    "AnalysisMethods",
    "ExpertConsultation",
    "PatentContext",
    "ExpertTeamAnalysis",
]
