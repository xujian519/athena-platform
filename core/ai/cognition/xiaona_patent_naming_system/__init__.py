#!/usr/bin/env python3

"""
小娜专利命名系统 - 公共接口
Xiaona Patent Naming System - Public Interface

作者: 小娜·天秤女神
创建时间: 2025-12-17
重构时间: 2026-01-27
版本: v2.0.0

此模块提供专利命名系统的公共接口导出。
"""

# 导入类型定义
# 导入主系统
from .types import (
    NamingStyle,
    PatentNamingRequest,
    PatentNamingResult,
    PatentType,
)

# 导出公共接口
__all__ = [
    # 类型
    "PatentType",
    "NamingStyle",
    "PatentNamingRequest",
    "PatentNamingResult",
    # 主系统
    "XiaonaPatentNamingSystem",
]

