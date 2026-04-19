#!/usr/bin/env python3
from __future__ import annotations
"""
联网搜索引擎 - 数据模型
Web Search Engines - Data Models

定义搜索相关的数据结构

作者: 小娜 & 小诺
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class SearchEngineType(Enum):
    """搜索引擎类型"""

    TAVILY = "tavily"
    GOOGLE_CUSTOM_SEARCH = "google_custom_search"
    BING_SEARCH = "bing_search"
    DUCKDUCKGO = "duckduckgo"
    BRAVE = "brave"
    PERPLEXITY = "perplexity"
    BOCHA = "bocha"
    METASO = "metaso"
    DEEPSEARCH = "deepsearch"


@dataclass
class SearchQuery:
    """搜索查询"""

    query: str
    engine_type: SearchEngineType = SearchEngineType.TAVILY
    max_results: int = 10
    language: str = "zh-CN"
    region: str = "CN"
    safe_search: str = "moderate"
    time_range: str = ""  # y=year, m=month, w=week, d=day
    domains: list[str] | None = None
    exclude_domains: list[str] | None = None
    include_domains: list[str] | None = None
    file_type: str = ""  # pdf, doc, docx, etc.
    advanced: bool = False  # 高级搜索模式


@dataclass
class SearchResult:
    """搜索结果"""

    title: str
    url: str
    snippet: str
    position: int
    engine: str
    relevance_score: float = 0.0
    timestamp: str = ""
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResponse:
    """搜索响应"""

    success: bool
    query: str
    engine: str
    results: list[SearchResult]
    total_results: int = 0
    search_time: float = 0.0
    api_key_used: str = ""
    error_message: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
