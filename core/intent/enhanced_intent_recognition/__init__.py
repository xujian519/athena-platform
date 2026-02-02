#!/usr/bin/env python3
"""
增强意图识别引擎 - 公共接口
Enhanced Intent Recognition Engine - Public Interface

作者: Athena AI系统
创建时间: 2025-12-23
重构时间: 2026-01-27
版本: 2.0.0

增强的意图识别引擎,支持关键词+模式+语义的混合匹配
"""

from typing import Any

from .engine import (
    EnhancedIntentRecognitionEngine,
    create_enhanced_intent_engine,
    get_enhanced_intent_engine,
    recognize_intent as _recognize_intent,
)


# 便捷函数
def recognize_intent(
    text: str, context: dict[str, Any]  | None = None, user_id: str | None = None
) -> Any:
    """便捷函数:识别意图(同步)"""
    engine = get_enhanced_intent_engine()
    return engine.recognize_intent(text, context)


async def recognize_intent_async(
    text: str, context: dict[str, Any]  | None = None, user_id: str | None = None
) -> Any:
    """便捷函数:异步识别意图"""
    engine = get_enhanced_intent_engine()
    return await engine.recognize_intent_async(text, context, user_id)


# 导出公共接口
__all__ = [
    "EnhancedIntentRecognitionEngine",
    "create_enhanced_intent_engine",
    "get_enhanced_intent_engine",
    "recognize_intent",
    "recognize_intent_async",
]
