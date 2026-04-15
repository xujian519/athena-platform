#!/usr/bin/env python3
from __future__ import annotations
"""
Google Custom Search搜索引擎
Google Custom Search Engine

作者: Athena AI系统
创建时间: 2025-10-15
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
from datetime import timedelta
from typing import Any

import httpx

from core.search.external.web_search.base import BaseSearchEngine
from core.search.external.web_search.types import (
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)


class GoogleCustomSearchEngine(BaseSearchEngine):
    """Google Custom Search搜索引擎

    特性:
    - 支持自定义搜索引擎ID
    - API密钥轮换策略
    - 高质量搜索结果
    """

    def __init__(
        self,
        api_keys: list[str],
        search_engine_id: str,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        """初始化Google Custom Search引擎

        Args:
            api_keys: Google API密钥列表
            search_engine_id: 自定义搜索引擎ID (CX)
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        super().__init__(
            name="Google Custom Search",
            base_url="https://www.googleapis.com/customsearch/v1",
            timeout=timeout,
            max_retries=max_retries,
        )
        self.api_keys = api_keys
        self.search_engine_id = search_engine_id
        self._last_key_index = 0

    async def search(self, query: SearchQuery) -> SearchResponse:
        """执行搜索

        Args:
            query: 搜索查询对象

        Returns:
            搜索响应对象
        """
        start_time = asyncio.get_event_loop().time()

        # API密钥轮换
        api_key = self.api_keys[self._last_key_index]
        self._last_key_index = (self._last_key_index + 1) % len(self.api_keys)

        try:
            result = await self._search_with_key(api_key, query, start_time)
            self._record_success(result.results_count)
            return result
        except Exception as e:
            self._record_failure(str(e))
            logger.error(f"Google Custom Search搜索失败: {e}")
            raise

    async def _search_with_key(
        self, api_key: str, query: SearchQuery, start_time: float
    ) -> SearchResponse:
        """使用指定API密钥执行搜索

        Args:
            api_key: API密钥
            query: 搜索查询
            start_time: 开始时间

        Returns:
            搜索响应
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {
                "key": api_key,
                "cx": self.search_engine_id,
                "q": query.query,
                "num": min(query.max_results, 10),
            }

            if query.language:
                params["lr"] = f"lang_{query.language}"

            if query.safe_search:
                params["safe"] = "active"

            response = await client.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()
            results = self._parse_google_results(data)

            elapsed = timedelta(
                seconds=asyncio.get_event_loop().time() - start_time
            )

            return SearchResponse(
                query=query.query,
                results=results,
                results_count=len(results),
                engine=self.name,
                elapsed_time=elapsed,
                metadata={
                    "api_key_index": self._last_key_index - 1,
                    "search_info": data.get("searchInformation", {}),
                },
            )

    def _parse_google_results(self, data: dict[str, Any]) -> list[SearchResult]:
        """解析Google搜索结果

        Args:
            data: Google API响应数据

        Returns:
            搜索结果列表
        """
        items = data.get("items", [])
        results = []

        for i, item in enumerate(items):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                position=i + 1,
                engine="google_custom",
                relevance_score=0.8,
                metadata={
                    "cached_url": item.get("cacheId"),
                    "file_format": item.get("fileFormat"),
                    "image_url": item.get("pagemap", {}).get("cse_image", [{}])[
                        0
                    ].get("src"),
                },
            )
            results.append(result)

        return results


__all__ = ["GoogleCustomSearchEngine"]
