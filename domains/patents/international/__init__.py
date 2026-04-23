#!/usr/bin/env python3
"""
国际专利申请系统

提供完整的国际专利申请支持：
1. PCT申请辅助
2. 各国法律适配
3. 翻译辅助
4. 国际申请管理
"""

from .international_filing_manager import InternationalFilingManager
from .legal_adapter import CountryLawInfo, LegalAdapter
from .pct_assistant import PCTApplication, PCTAssistant
from .translation_assistant import TranslationAssistant

__all__ = [
    "PCTAssistant",
    "PCTApplication",
    "LegalAdapter",
    "CountryLawInfo",
    "TranslationAssistant",
    "InternationalFilingManager",
]
