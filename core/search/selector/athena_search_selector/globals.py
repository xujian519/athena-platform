#!/usr/bin/env python3
from __future__ import annotations
"""
Athena智能搜索选择器 - 全局函数
Athena Search Selector - Global Functions

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0

提供全局实例管理和初始化函数。
"""

from typing import Any

from ...registry.tool_registry import ToolRegistry
from .selector import AthenaSearchSelector

# 全局选择器实例
_search_selector: AthenaSearchSelector | None = None


def get_search_selector() -> AthenaSearchSelector:
    """获取全局搜索选择器实例"""
    global _search_selector
    if _search_selector is None:
        _search_selector = AthenaSearchSelector()
    return _search_selector


async def initialize_search_selector(
    registry: ToolRegistry | None = None, config: dict[str, Any] | None = None
) -> AthenaSearchSelector:
    """初始化全局搜索选择器"""
    selector = get_search_selector()
    return selector
