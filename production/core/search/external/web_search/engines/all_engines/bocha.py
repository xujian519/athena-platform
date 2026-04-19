#!/usr/bin/env python3
from __future__ import annotations
"""
博查搜索引擎 - AI优化的中文搜索引擎
Bocha Search Engine - AI-Optimized Chinese Search Engine

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


class BochaSearchEngine(BaseSearchEngine):
    """博查搜索引擎

    特性:
    - AI优化的中文搜索
    - 智能结果排序
    - 支持深度搜索
    - API密钥轮换
    """

    def __init__(
        self,
        api_keys: list[str],
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        """初始化博查搜索引擎

        Args:
            api_keys: 博查API密钥列表
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        super().__init__(
            api_keys,
            config={
                "base_url": "https://api.bocha.cn/api/web/search",
                "timeout": timeout,
                "max_retries": max_retries,
            }
        )
        self.api_keys = api_keys
        self._last_key_index = 0

        if not api_keys:
            raise ValueError("至少需要一个API密钥")

        logger.info(f"博查搜索引擎初始化完成,共{len(api_keys)}个API密钥")

    async def search(self, query: SearchQuery) -> SearchResponse:
        """执行搜索

        Args:
            query: 搜索查询对象

        Returns:
            搜索响应对象
        """
        start_time = asyncio.get_event_loop().time()

        api_key = self.api_keys[self._last_key_index]
        self._last_key_index = (self._last_key_index + 1) % len(self.api_keys)

        try:
            result = await self._search_with_key(api_key, query, start_time)
            self._record_success(result.results_count)
            return result
        except Exception as e:
            self._record_failure(str(e))
            logger.error(f"博查搜索失败: {e}")
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
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "query": query.query,
            "num_results": min(query.max_results, 20),
            "search_depth": "advanced" if query.advanced else "basic",
        }

        if query.language:
            payload["language"] = query.language

        if query.time_range:
            payload["time_range"] = query.time_range

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.base_url, json=payload, headers=headers
            )
            response.raise_for_status()

            data = response.json()
            results = self._parse_bocha_results(data)

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
                    "ai_score": data.get("ai_score", 0.0),
                },
            )

    def _parse_bocha_results(self, data: dict[str, Any]) -> list[SearchResult]:
        """解析博查搜索结果

        Args:
            data: 博查API响应数据

        Returns:
            搜索结果列表
        """
        search_results = (
            data.get("data", {}).get("web_Pages", {}).get("value", [])
        )
        results = []

        for i, item in enumerate(search_results):
            result = SearchResult(
                title=item.get("name", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                position=i + 1,
                engine="bocha",
                relevance_score=item.get("relevance_score", 0.8),
                metadata={
                    "display_url": item.get("displayUrl"),
                    "date_last_crawled": item.get("dateLastCrawled"),
                    "is_family_friendly": item.get("isFamilyFriendly", True),
                },
            )
            results.append(result)

        return results


__all__ = ["BochaSearchEngine"]
