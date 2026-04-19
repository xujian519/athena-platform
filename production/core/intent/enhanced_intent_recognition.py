#!/usr/bin/env python3
"""
增强意图识别引擎 - 向后兼容重定向
Enhanced Intent Recognition Engine - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 enhanced_intent_recognition/
原文件已备份为 enhanced_intent_recognition.py.bak

请使用新导入:
    from core.intent.enhanced_intent_recognition import EnhancedIntentRecognitionEngine

此文件仅用于向后兼容,将在未来版本中移除。
"""

from __future__ import annotations
import warnings

from .enhanced_intent_recognition import (
    EnhancedIntentRecognitionEngine,
    create_enhanced_intent_engine,
    get_enhanced_intent_engine,
    recognize_intent,
    recognize_intent_async,
)

# 触发弃用警告
warnings.warn(
    "enhanced_intent_recognition.py 已重构为模块化目录 enhanced_intent_recognition/。\n"
    "请使用新导入: from core.intent.enhanced_intent_recognition import EnhancedIntentRecognitionEngine\n"
    "原文件已备份为 enhanced_intent_recognition.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "EnhancedIntentRecognitionEngine",
    "create_enhanced_intent_engine",
    "get_enhanced_intent_engine",
    "recognize_intent",
    "recognize_intent_async",
]
