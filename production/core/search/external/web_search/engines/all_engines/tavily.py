#!/usr/bin/env python3
from __future__ import annotations
"""
Tavily搜索引擎 - API密钥轮换策略
Tavily Search Engine - API Key Rotation Strategy

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


class TavilySearchEngine(BaseSearchEngine):
    """Tavily搜索引擎

    特性:
    - API密钥轮换策略,提高可用性
    - 智能搜索结果解析
    - 支持深度搜索和话题搜索
    """

    def __init__(
        self,
        api_keys: list[str],
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        """初始化Tavily搜索引擎

        Args:
            api_keys: Tavily API密钥列表(支持轮换)
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        super().__init__(
            api_keys,
            config={
                "base_url": "https://api.tavily.com/search",
                "timeout": timeout,
                "max_retries": max_retries,
            }
        )
        self.api_keys = api_keys
        self._last_key_index = 0 if api_keys else -1

        if not api_keys:
            raise ValueError("至少需要一个API密钥")

        logger.info(f"Tavily搜索引擎初始化完成,共{len(api_keys)}个API密钥")

    async def search(self, query: SearchQuery) -> SearchResponse:
        """执行搜索

        Args:
            query: 搜索查询对象

        Returns:
            搜索响应对象
        """
        start_time = asyncio.get_event_loop().time()

        # API密钥轮换
        self._last_key_index = (self._last_key_index + 1) % len(self.api_keys)
        api_key = self.api_keys[self._last_key_index]

        try:
            result = await self._search_with_key(api_key, query, start_time)
            self._record_success(result.total_results)
            return result
        except Exception as e:
            self._record_failure(str(e))
            logger.error(f"Tavily搜索失败: {e}")
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
            search_params = {
                "api_key": api_key,
                "query": query.query,
                "max_results": min(query.max_results, 10),
                "search_depth": "advanced" if query.advanced else "basic",
                "include_answer": True,
                "include_raw_content": False,
                "include_images": False,
            }

            if query.time_range:
                days_map = {
                    "1d": 1,
                    "1w": 7,
                    "1m": 30,
                    "1y": 365,
                }
                if query.time_range in days_map:
                    search_params["days"] = days_map[query.time_range]

            response = await client.post(
                self.base_url,
                json=search_params,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            data = response.json()
            results = self._parse_tavily_results(data)

            elapsed = timedelta(
                seconds=asyncio.get_event_loop().time() - start_time
            )

            return SearchResponse(
                success=True,
                query=query.query,
                results=results,
                total_results=len(results),
                engine=self.name,
                search_time=elapsed.total_seconds(),
                metadata={"api_key_index": self._last_key_index},
            )

    def _parse_tavily_results(self, data: dict[str, Any]) -> list[SearchResult]:
        """解析Tavily搜索结果

        Args:
            data: Tavily API响应数据

        Returns:
            搜索结果列表
        """
        search_results = data.get("results", [])
        results = []

        for i, item in enumerate(search_results):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                position=i + 1,
                engine="tavily",
                relevance_score=self._calculate_relevance_score(item),
                metadata={
                    "score": item.get("score", 0.0),
                    "published_date": item.get("published_date"),
                },
            )
            results.append(result)

        return results

    def _calculate_relevance_score(self, item: dict[str, Any]) -> float:
        """计算相关性得分

        Args:
            item: 搜索结果项

        Returns:
            相关性得分 (0.0-1.0)
        """
        base_score = item.get("score", 0.0)
        return min(base_score / 10.0, 1.0)


__all__ = ["TavilySearchEngine"]
