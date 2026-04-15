from __future__ import annotations
"""
本地搜索引擎模块
提供 SearXNG+Firecrawl 的统一适配器接口
"""

from .adapter import LocalSearchAdapter
from typing import Optional
from .config import LocalSearchConfig
from .types import (
    LocalHealthResponse,
    LocalSearchAndScrapeResponse,
    LocalSearchResponse,
    LocalScrapeResult,
)

__all__ = [
    "LocalSearchAdapter",
    "LocalSearchConfig",
    "LocalSearchResponse",
    "LocalSearchAndScrapeResponse",
    "LocalScrapeResult",
    "LocalHealthResponse",
    "get_local_search_adapter",
]

# 懒加载单例
_adapter_instance: Optional[LocalSearchAdapter] = None


def get_local_search_adapter() -> LocalSearchAdapter:
    """获取本地搜索引擎适配器单例"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = LocalSearchAdapter()
    return _adapter_instance
