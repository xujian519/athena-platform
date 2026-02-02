#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联网搜索引擎集成系统 - 向后兼容重定向
Web Search Engines Integration System - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.search.external.web_search

作者: 小娜 & 小诺
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0-refactored

--- 迁移指南 ---

旧导入:
  from core.search.external.web_search_engines import UnifiedWebSearchManager

新导入:
  from core.search.external.web_search import UnifiedWebSearchManager
  # 或
  from core.search.external.web_search.manager import UnifiedWebSearchManager

--- 文件结构 ---

core/search/external/web_search/
├── __init__.py              # 公共接口导出
├── types.py                 # 数据模型 (79行)
├── api_key_manager.py       # API密钥管理器 (108行)
├── base.py                  # 基类 (47行)
├── engines/
│   ├── __init__.py          # 搜索引擎导出
│   └── all.py               # 所有搜索引擎实现 (897行)
├── manager.py               # 统一管理器 (239行)
└── utils.py                 # 便捷工具 (74行)

总计: ~1444行 (原文件: 1414行, 由于添加了文档略有增加)

--- 使用示例 ---

# 推荐导入方式
from core.search.external.web_search import (
    UnifiedWebSearchManager,
    SearchEngineType,
    SearchQuery,
    quick_search,
)

# 或单独导入
from core.search.external.web_search import UnifiedWebSearchManager

"""

import logging
import warnings

logger = logging.getLogger(__name__)

# 向后兼容重定向
from core.search.external.web_search import (  # type: ignore
    APIKeyManager,
    BaseSearchEngine,
    BochaSearchEngine,
    GoogleCustomSearchEngine,
    MetasoSearchEngine,
    SearchEngineType,
    SearchQuery,
    SearchResult,
    SearchResponse,
    TavilySearchEngine,
    UnifiedWebSearchManager,
    get_web_search_manager,
    quick_search,
    test_web_search,
)

# 发出迁移警告
warnings.warn(
    "web_search_engines 已重构，请使用新导入路径: "
    "from core.search.external.web_search import UnifiedWebSearchManager",
    DeprecationWarning,
    stacklevel=2,
)

logger.info("⚠️  使用已重构的web_search_engines，建议更新导入路径")

# 导出所有公共接口以保持向后兼容
__all__ = [
    "SearchEngineType",
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    "APIKeyManager",
    "BaseSearchEngine",
    "TavilySearchEngine",
    "GoogleCustomSearchEngine",
    "BochaSearchEngine",
    "MetasoSearchEngine",
    "UnifiedWebSearchManager",
    "quick_search",
    "get_web_search_manager",
    "test_web_search",
]
