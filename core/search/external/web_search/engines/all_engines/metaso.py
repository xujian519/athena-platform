#!/usr/bin/env python3
from __future__ import annotations
"""
秘塔搜索引擎 - 中国版Perplexity,智能AI搜索
Metaso Search Engine - Chinese Perplexity-like AI Search

作者: Athena AI系统
创建时间: 2025-10-15
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
import re
from datetime import timedelta

import httpx

from core.search.external.web_search.base import BaseSearchEngine
from core.search.external.web_search.types import (
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)


class MetasoSearchEngine(BaseSearchEngine):
    """秘塔搜索引擎

    特性:
    - AI增强的搜索体验
    - 多端点故障转移
    - 智能内容提取
    - 支持对话式搜索
    """

    def __init__(
        self,
        api_keys: list[str],
        timeout: float = 15.0,
        max_retries: int = 3,
    ):
        """初始化秘塔搜索引擎

        Args:
            api_keys: 秘塔API密钥列表
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        super().__init__(
            api_keys,
            config={
                "base_url": "https://api.metaso.cn/v1/chat/completions",
                "timeout": timeout,
                "max_retries": max_retries,
            }
        )
        self.api_keys = api_keys
        self._last_key_index = 0

        # 多个可能的API端点
        self.possible_endpoints = [
            ("https://api.metaso.cn", "/v1/chat/completions"),
            ("https://open.metaso.cn", "/v1/chat/completions"),
            ("https://metaso.cn/api", "/v1/chat/completions"),
            ("https://api.metaso.ai", "/v1/chat/completions"),
        ]

        if not api_keys:
            raise ValueError("至少需要一个API密钥")

        logger.info(f"秘塔搜索引擎初始化完成,共{len(api_keys)}个API密钥")

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
            logger.error(f"秘塔搜索失败: {e}")
            raise

    async def _search_with_key(
        self, api_key: str, query: SearchQuery, start_time: float
    ) -> SearchResponse:
        """使用指定API密钥执行搜索,支持多端点故障转移

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
            "model": "metaso-ai",
            "messages": [
                {
                    "role": "user",
                    "content": f"请搜索并总结关于'{query.query}'的信息,包括相关链接和来源。",
                }
            ],
            "stream": False,
            "search_mode": True,
        }

        last_error = None

        # 尝试多个端点
        for base_url, endpoint in self.possible_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                logger.debug(f"尝试端点: {url}")

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url, json=payload, headers=headers
                    )
                    response.raise_for_status()

                    data = response.json()
                    results = self._extract_search_results_from_content(
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", ""),
                        query,
                    )

                    elapsed = timedelta(
                        seconds=asyncio.get_event_loop().time() - start_time
                    )

                    return SearchResponse(
                        query=query.query,
                        results=results,
                        results_count=len(results),
                        engine=self.name,
                        elapsed_time=elapsed,
                        metadata={"endpoint": url, "api_key_index": self._last_key_index - 1},
                    )

            except Exception as e:
                last_error = e
                logger.warning(f"端点 {base_url} 失败: {e}")
                continue

        # 所有端点都失败
        raise Exception(f"所有端点均失败,最后错误: {last_error}")

    def _extract_search_results_from_content(
        self, content: str, query: SearchQuery
    ) -> list[SearchResult]:
        """从AI生成的内容中提取搜索结果

        Args:
            content: AI生成的回复内容
            query: 原始搜索查询

        Returns:
            搜索结果列表
        """
        results = []

        # 提取链接的模式
        url_patterns = [
            r"https?://[^\s\)]+",
            r"www\.[^\s\)]+",
        ]

        # 提取引用标记的模式
        link_patterns = [
            r"\[(\d+)\]",
            r"\[\[(\d+)\]\]",
        ]

        # 查找所有URL
        urls = []
        for pattern in url_patterns:
            urls.extend(re.findall(pattern, content))

        # 查找所有引用标记
        references = []
        for pattern in link_patterns:
            references.extend(re.findall(pattern, content))

        # 如果直接找到URL,创建结果
        if urls:
            for i, url in enumerate(urls[: query.max_results]):
                # 清理URL
                url = url.rstrip(".,;:)")
                if not url.startswith("http"):
                    url = f"https://{url}"

                # 提取URL周围的文本作为摘要
                snippet = self._extract_snippet_around_url(content, url)

                result = SearchResult(
                    title=f"搜索结果 {i + 1}",
                    url=url,
                    snippet=snippet,
                    position=i + 1,
                    engine="metaso",
                    relevance_score=0.7,
                    metadata={"extracted_from_ai_content": True},
                )
                results.append(result)

        # 如果没有找到URL但有引用,尝试从内容中提取结构化信息
        if not results and len(content) > 100:
            result = SearchResult(
                title=f"关于 {query.query} 的AI搜索结果",
                url="",
                snippet=content[:500] + "..."
                if len(content) > 500
                else content,
                position=1,
                engine="metaso",
                relevance_score=0.6,
                metadata={"ai_generated_summary": True},
            )
            results.append(result)

        return results

    def _extract_snippet_around_url(self, content: str, url: str) -> str:
        """提取URL周围的文本作为摘要

        Args:
            content: 完整内容
            url: 要查找的URL

        Returns:
            URL周围的文本摘要
        """
        # 查找URL在内容中的位置
        url_index = content.find(url)
        if url_index == -1:
            return ""

        # 提取周围150个字符
        start = max(0, url_index - 75)
        end = min(len(content), url_index + len(url) + 75)

        snippet = content[start:end]

        # 清理snippet
        snippet = re.sub(r"\s+", " ", snippet)
        snippet = snippet.strip()

        if len(snippet) > 200:
            snippet = snippet[:200] + "..."

        return snippet


__all__ = ["MetasoSearchEngine"]
