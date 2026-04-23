from __future__ import annotations
"""
搜索模块基础定义
定义搜索接口和基础数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SearchType(Enum):
    """搜索类型枚举"""

    WEB = "web"
    PATENT = "patent"
    ACADEMIC = "academic"
    DEEPSEARCH = "deepsearch"


@dataclass
class SearchQuery:
    """搜索查询数据结构"""

    query: str
    search_type: SearchType
    limit: int = 10
    offset: int = 0
    filters: Optional[dict[str, Any]] = None
    language: str = "zh"


@dataclass
class SearchResult:
    """搜索结果数据结构"""

    title: str
    content: str
    url: Optional[str] = None
    relevance_score: float = 0.0
    metadata: Optional[dict[str, Any]] = None


@dataclass
class SearchResponse:
    """搜索响应数据结构"""

    results: list[SearchResult]
    total: int
    query: SearchQuery
    search_time: float
    engine: str


class BaseSearchEngine(ABC):
    """搜索引擎基类"""

    def __init__(self, name: str, config: Optional[dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResponse:
        """
        执行搜索

        Args:
            query: 搜索查询对象

        Returns:
            搜索响应对象
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查搜索引擎是否可用"""
        pass

    def validate_query(self, query: SearchQuery) -> bool:
        """验证查询参数"""
        if not query.query:
            return False
        return not query.limit <= 0
