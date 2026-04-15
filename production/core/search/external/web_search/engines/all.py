#!/usr/bin/env python3
"""
多搜索引擎集成 - 向后兼容重定向
Multiple Search Engines Integration - Backward Compatibility Redirect

⚠️ DEPRECATED: 此文件已重构为模块化目录 all_engines/
原文件已备份为 all.py.bak

请使用新导入:
    from core.search.external.web_search.engines.all_engines import (
        TavilySearchEngine,
        GoogleCustomSearchEngine,
        BochaSearchEngine,
        MetasoSearchEngine,
    )

此文件仅用于向后兼容,将在未来版本中移除。
"""

from __future__ import annotations
import warnings

from .all_engines import (
    BochaSearchEngine,
    GoogleCustomSearchEngine,
    MetasoSearchEngine,
    TavilySearchEngine,
)

# 触发弃用警告
warnings.warn(
    "all.py 已重构为模块化目录 all_engines/。\n"
    "请使用新导入: from core.search.external.web_search.engines.all_engines import TavilySearchEngine\n"
    "原文件已备份为 all.py.bak",
    DeprecationWarning,
    stacklevel=2,
)

# 导出所有公共接口以保持向后兼容
__all__ = [
    "TavilySearchEngine",
    "GoogleCustomSearchEngine",
    "BochaSearchEngine",
    "MetasoSearchEngine",
]
