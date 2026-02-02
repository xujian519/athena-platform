#!/usr/bin/env python3
"""
Athena智能搜索选择器 - 公共接口
Athena Search Selector - Public Interface

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0

此模块提供智能搜索选择器的公共接口导出。
"""

# 导入类型定义
from .types import (
    QueryIntent,
    DomainType,
    QueryAnalysis,
    ToolRecommendation,
    SelectionStrategy,
)

# 导入主选择器
from .selector import AthenaSearchSelector

# 导入全局函数
from .globals import get_search_selector, initialize_search_selector

# 导出公共接口
__all__ = [
    # 类型
    "QueryIntent",
    "DomainType",
    "QueryAnalysis",
    "ToolRecommendation",
    "SelectionStrategy",
    # 主选择器
    "AthenaSearchSelector",
    # 全局函数
    "get_search_selector",
    "initialize_search_selector",
]
