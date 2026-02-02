#!/usr/bin/env python3
"""
多搜索引擎集成模块 - 公共接口
Multiple Search Engines Integration - Public Interface

作者: Athena AI系统
创建时间: 2025-10-15
重构时间: 2026-01-27
版本: 2.0.0

集成多个搜索引擎,提供统一的搜索接口。
"""

from .bocha import BochaSearchEngine
from .google_custom import GoogleCustomSearchEngine
from .metaso import MetasoSearchEngine
from .tavily import TavilySearchEngine

# 导出所有搜索引擎类
__all__ = [
    "TavilySearchEngine",
    "GoogleCustomSearchEngine",
    "BochaSearchEngine",
    "MetasoSearchEngine",
]
