#!/usr/bin/env python3
"""
联网搜索引擎 - 公共接口
Web Search Engines - Public Interface

统一联网搜索引擎集成系统

作者: 小娜 & 小诺
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

# 数据模型
from core.search.external.web_search.types import (
    SearchEngineType,
    SearchQuery,
    SearchResult,
    SearchResponse,
)

# API密钥管理器
from core.search.external.web_search.api_key_manager import APIKeyManager

# 基类
from core.search.external.web_search.base import BaseSearchEngine

# 搜索引擎实现
from core.search.external.web_search.engines import (
    BochaSearchEngine,
    GoogleCustomSearchEngine,
    MetasoSearchEngine,
    TavilySearchEngine,
)

# 统一管理器
from core.search.external.web_search.manager import UnifiedWebSearchManager

# 便捷工具
from core.search.external.web_search.utils import (
    get_web_search_manager,
    quick_search,
    test_web_search,
)

__all__ = [
    # 数据模型
    "SearchEngineType",
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    # API密钥管理器
    "APIKeyManager",
    # 基类
    "BaseSearchEngine",
    # 搜索引擎实现
    "TavilySearchEngine",
    "GoogleCustomSearchEngine",
    "BochaSearchEngine",
    "MetasoSearchEngine",
    # 统一管理器
    "UnifiedWebSearchManager",
    # 便捷工具
    "get_web_search_manager",
    "quick_search",
    "test_web_search",
]

__version__ = "2.1.0"
__author__ = "小娜 & 小诺"
