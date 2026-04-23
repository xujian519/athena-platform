from __future__ import annotations
"""
本地搜索引擎数据类型
映射 SearXNG+Firecrawl Gateway REST API 的请求/响应格式
"""

from dataclasses import dataclass, field
from typing import Optional, Any

from ..base import SearchResult, SearchResponse, SearchQuery, SearchType


@dataclass
class LocalSearchRequest:
    """搜索请求"""

    query: str
    max_results: int = 5
    categories: Optional[str] = None  # general, news, science, it, files
    time_range: Optional[str] = None  # day, week, month, year
    language: Optional[str] = None  # zh-CN, en, etc.
    engines: Optional[str] = None  # google, bing, duckduckgo, etc.


@dataclass
class LocalSearchResultItem:
    """单条搜索结果"""

    title: str
    url: str
    snippet: str = ""
    engines: list[str] = field(default_factory=list)
    score: float = 0.0
    category: str = ""

    def to_search_result(self) -> SearchResult:
        """转换为Athena标准SearchResult"""
        return SearchResult(
            title=self.title,
            content=self.snippet,
            url=self.url,
            relevance_score=self.score,
            metadata={"engines": self.engines, "category": self.category},
        )


@dataclass
class LocalSearchResponse:
    """搜索响应"""

    query: str = ""
    results: list[LocalSearchResultItem] = field(default_factory=list)
    total_results: int = 0
    response_time: float = 0.0
    failed_engines: list[str] = field(default_factory=list)

    def to_search_response(self, search_query: SearchQuery) -> SearchResponse:
        """转换为Athena标准SearchResponse"""
        return SearchResponse(
            results=[r.to_search_result() for r in self.results],
            total=self.total_results,
            query=search_query,
            search_time=self.response_time,
            engine="local_search",
        )


@dataclass
class LocalScrapeRequest:
    """网页抓取请求"""

    url: str
    format: str = "markdown"  # markdown 或 text


@dataclass
class LocalScrapeResult:
    """单页抓取结果"""

    url: str
    success: bool = False
    title: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass
class LocalSearchAndScrapeResult:
    """搜索+抓取联合结果"""

    title: str
    url: str
    snippet: str = ""
    content: str = ""  # 抓取的完整页面内容
    score: float = 0.0
    engines: list[str] = field(default_factory=list)

    def to_search_result(self) -> SearchResult:
        """转换为Athena标准SearchResult（含完整内容）"""
        return SearchResult(
            title=self.title,
            content=self.content or self.snippet,
            url=self.url,
            relevance_score=self.score,
            metadata={"engines": self.engines, "has_full_content": bool(self.content)},
        )


@dataclass
class LocalSearchAndScrapeResponse:
    """搜索+抓取联合响应"""

    query: str = ""
    results: list[LocalSearchAndScrapeResult] = field(default_factory=list)
    response_time: float = 0.0

    def to_search_response(self, search_query: SearchQuery) -> SearchResponse:
        """转换为Athena标准SearchResponse"""
        return SearchResponse(
            results=[r.to_search_result() for r in self.results],
            total=len(self.results),
            query=search_query,
            search_time=self.response_time,
            engine="local_search",
        )


@dataclass
class LocalHealthResponse:
    """健康检查响应"""

    status: str = "unknown"
    timestamp: str = ""
    services: dict[str, str] = field(default_factory=dict)
    response_time_ms: float = 0.0
