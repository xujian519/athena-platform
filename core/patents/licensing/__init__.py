#!/usr/bin/env python3
"""
许可协议起草系统

提供专利许可协议的完整功能：
1. 专利估值
2. 条款生成
3. 模板管理
4. 条款解释
5. 协议撰写
"""

from .patent_valuator import PatentValuator, ValuationResult
from .clause_generator import ClauseGenerator, LicenseTerms
from .licensing_drafting import LicensingDrafting, LicensingOptions

__all__ = [
    "PatentValuator",
    "ValuationResult",
    "ClauseGenerator",
    "LicenseTerms",
    "LicensingDrafting",
    "LicensingOptions",
]
