#!/usr/bin/env python3
"""
Athena智能搜索选择器 - 向后兼容重定向
Athena Search Selector - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.search.selector.athena_search_selector (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.search.selector.athena_search_selector import (
        AthenaSearchSelector,
        QueryIntent,
        DomainType,
        QueryAnalysis,
        ToolRecommendation,
        SelectionStrategy,
        get_search_selector,
        initialize_search_selector,
    )

新导入方式:
    from core.search.selector.athena_search_selector import (
        AthenaSearchSelector,
        QueryIntent,
        DomainType,
        QueryAnalysis,
        ToolRecommendation,
        SelectionStrategy,
        get_search_selector,
        initialize_search_selector,
    )
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

from __future__ import annotations
import warnings

# 导入重构后的模块
from .athena_search_selector import (
    AthenaSearchSelector,
    DomainType,
    QueryAnalysis,
    QueryIntent,
    SelectionStrategy,
    ToolRecommendation,
    get_search_selector,
    initialize_search_selector,
)

# 发出弃用警告
warnings.warn(
    "athena_search_selector.py 已重构为模块化目录 "
    "core.search.selector.athena_search_selector/。"
    "请更新您的导入语句。详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
__all__ = [
    'QueryIntent',
    'DomainType',
    'QueryAnalysis',
    'ToolRecommendation',
    'SelectionStrategy',
    'AthenaSearchSelector',
    'get_search_selector',
    'initialize_search_selector',
]
