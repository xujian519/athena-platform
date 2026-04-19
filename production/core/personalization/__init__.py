from __future__ import annotations
"""
个性化响应模块 - Personalization Module

提供用户偏好管理和响应个性化功能
"""

from core.personalization.response_adaptor import (
    LanguageStyle,
    OutputFormat,
    # 核心类
    ResponseAdapter,
    # 枚举
    ResponseDetail,
    TechnicalDepth,
    # 数据类
    UserPreference,
    adapt_response,
    # 便捷函数
    get_response_adapter,
    get_user_preference,
    learn_from_feedback,
    save_user_preference,
)

__all__ = [
    "LanguageStyle",
    "OutputFormat",
    # 核心类
    "ResponseAdapter",
    # 枚举
    "ResponseDetail",
    "TechnicalDepth",
    # 数据类
    "UserPreference",
    "adapt_response",
    # 便捷函数
    "get_response_adapter",
    "get_user_preference",
    "learn_from_feedback",
    "save_user_preference",
]
