#!/usr/bin/env python3
from __future__ import annotations
"""
联网搜索引擎 - 基类
Web Search Engines - Base Classes

定义搜索引擎的抽象基类

作者: 小娜 & 小诺
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

from abc import ABC, abstractmethod
from typing import Any

from core.logging_config import setup_logging
from core.search.external.web_search.types import SearchQuery, SearchResponse

logger = setup_logging()


class BaseSearchEngine(ABC):
    """搜索引擎基类 - 所有搜索引擎的抽象基类"""

    def __init__(self, api_keys: list[str], config: Optional[dict[str, Any]] = None):
        """
        初始化搜索引擎

        Args:
            api_keys: API密钥列表
            config: 配置参数
        """
        self.api_keys = api_keys
        self.config = config or {}
        self.name = self.__class__.__name__
        self.base_url = self.config.get("base_url", "")
        self.timeout = self.config.get("timeout", 30)

    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResponse:
        """执行搜索 - 子类必须实现"""
        pass

    def _build_search_params(self, query: SearchQuery) -> dict[str, Any]:
        """构建搜索参数"""
        params = {
            "q": query.query,
            "num": query.max_results,
            "hl": query.language,
            "gl": query.region,
            "safe": query.safe_search,
        }

        if query.time_range:
            params["date_Range"] = query.time_range

        if query.domains:
            params["site"] = ",".join(query.domains)

        if query.exclude_domains:
            params["exclude_sites"] = ",".join(query.exclude_domains)

        if query.file_type:
            params["file_Type"] = query.file_type

        return params

    def _record_success(self, results_count: int = 0):
        """记录成功搜索"""
        pass

    def _record_failure(self, error_message: str):
        """记录失败搜索"""
        pass
