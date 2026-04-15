from __future__ import annotations
"""
本地搜索引擎适配器
封装 SearXNG+Firecrawl Gateway REST API，提供统一搜索接口
"""

import logging
import time
from typing import Any, Optional

import httpx

from ..base import BaseSearchEngine, SearchQuery, SearchResponse, SearchType
from .config import LocalSearchConfig
from .types import (
    LocalHealthResponse,
    LocalSearchAndScrapeResponse,
    LocalSearchAndScrapeResult,
    LocalSearchResponse,
    LocalSearchResultItem,
    LocalScrapeResult,
)

logger = logging.getLogger(__name__)


class LocalSearchAdapter(BaseSearchEngine):
    """本地搜索引擎适配器 - 封装SearXNG+Firecrawl Gateway"""

    def __init__(self, name: str = "local_search", config: Optional[dict[str, Any]] = None):
        super().__init__(name, config)
        self._lse_config = LocalSearchConfig.from_file(
            config.get("config_path") if config else None
        )
        self._base_url = self._lse_config.get_connection_url()
        self._client: httpx.Optional[AsyncClient] = None
        self._available = False
        self._stats: dict[str, Any] = {
            "total_requests": 0,
            "success_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建HTTP客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(
                    connect=self._lse_config.connect_timeout,
                    read=self._lse_config.timeout,
                    write=10.0,
                    pool=5.0,
                ),
            )
        return self._client

    async def search(self, query: SearchQuery) -> SearchResponse:
        """
        执行搜索

        Args:
            query: 搜索查询对象

        Returns:
            搜索响应
        """
        if not self.validate_query(query):
            raise ValueError("无效的搜索查询")

        # 构建请求参数
        params: dict[str, Any] = {
            "q": query.query,
            "max_results": query.limit or self._lse_config.default_max_results,
        }
        if query.language and query.language != "zh":
            params["language"] = query.language
        else:
            params["language"] = self._lse_config.default_language

        if query.filters:
            if "categories" in query.filters:
                params["categories"] = query.filters["categories"]
            if "time_range" in query.filters:
                params["time_range"] = query.filters["time_range"]
            if "engines" in query.filters:
                params["engines"] = query.filters["engines"]

        start_time = time.time()
        try:
            client = await self._get_client()
            response = await client.get("/v1/search", params=params)
            response.raise_for_status()

            data = response.json()
            local_resp = self._parse_search_response(data, query.query)
            self._update_stats(True, time.time() - start_time)

            return local_resp.to_search_response(query)

        except httpx.TimeoutException as e:
            self._update_stats(False, time.time() - start_time)
            logger.warning(f"搜索超时: {e}")
            raise
        except httpx.HTTPStatusError as e:
            self._update_stats(False, time.time() - start_time)
            logger.warning(f"搜索HTTP错误: {e.response.status_code}")
            raise
        except Exception as e:
            self._update_stats(False, time.time() - start_time)
            logger.warning(f"搜索失败: {e}")
            raise

    async def scrape(self, url: str, format: str = "markdown") -> LocalScrapeResult:
        """
        抓取网页内容

        Args:
            url: 目标URL
            format: 输出格式 (markdown/text)

        Returns:
            抓取结果
        """
        client = await self._get_client()
        try:
            response = await client.post(
                "/v1/scrape",
                json={"url": url, "format": format or self._lse_config.scrape_format},
            )
            response.raise_for_status()

            data = response.json()
            return LocalScrapeResult(
                url=url,
                success=True,
                title=data.get("data", {}).get("metadata", {}).get("title", ""),
                content=data.get("data", {}).get("content", ""),
                metadata=data.get("data", {}).get("metadata", {}),
            )
        except Exception as e:
            logger.warning(f"抓取失败 [{url}]: {e}")
            return LocalScrapeResult(url=url, success=False, error=str(e))

    async def search_and_scrape(
        self, query: str, max_results: int = 3, **kwargs: Any
    ) -> SearchResponse:
        """
        搜索+抓取全文

        Args:
            query: 搜索关键词
            max_results: 最大结果数

        Returns:
            含完整内容的搜索结果
        """
        start_time = time.time()
        try:
            client = await self._get_client()
            response = await client.post(
                "/v1/search-and-scrape",
                json={"query": query, "max_results": max_results},
                timeout=httpx.Timeout(read=60.0),  # 搜索+抓取需要更长时间
            )
            response.raise_for_status()

            data = response.json()
            local_resp = self._parse_search_and_scrape_response(data)
            self._update_stats(True, time.time() - start_time)

            search_query = SearchQuery(query=query, search_type=SearchType.WEB)
            return local_resp.to_search_response(search_query)

        except Exception as e:
            self._update_stats(False, time.time() - start_time)
            logger.warning(f"搜索+抓取失败: {e}")
            raise

    def is_available(self) -> bool:
        """检查搜索引擎是否可用"""
        return self._available

    async def health_check(self) -> LocalHealthResponse:
        """执行健康检查"""
        try:
            client = await self._get_client()
            start = time.time()
            response = await client.get(
                "/health",
                timeout=httpx.Timeout(read=self._lse_config.health_check_timeout),
            )
            elapsed = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                self._available = True
                return LocalHealthResponse(
                    status=data.get("status", "unknown"),
                    timestamp=data.get("timestamp", ""),
                    services=data.get("services", {}),
                    response_time_ms=elapsed,
                )

            self._available = False
            return LocalHealthResponse(status="unhealthy", response_time_ms=elapsed)

        except Exception as e:
            self._available = False
            logger.debug(f"健康检查失败: {e}")
            return LocalHealthResponse(status="unreachable")

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "available": self._available,
            "base_url": self._base_url,
        }

    async def close(self) -> None:
        """关闭HTTP客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _parse_search_response(
        self, data: dict, query: str
    ) -> LocalSearchResponse:
        """解析搜索API响应"""
        results = []
        for item in data.get("results", []):
            results.append(
                LocalSearchResultItem(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", item.get("content", "")),
                    engines=item.get("engines", []),
                    score=item.get("score", 0.0),
                    category=item.get("category", ""),
                )
            )
        return LocalSearchResponse(
            query=query,
            results=results,
            total_results=data.get("total_results", len(results)),
            response_time=data.get("response_time", 0.0),
            failed_engines=data.get("failed_engines", []),
        )

    def _parse_search_and_scrape_response(
        self, data: dict
    ) -> LocalSearchAndScrapeResponse:
        """解析搜索+抓取API响应"""
        results = []
        for item in data.get("results", []):
            results.append(
                LocalSearchAndScrapeResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                    engines=item.get("engines", []),
                )
            )
        return LocalSearchAndScrapeResponse(
            query=data.get("query", ""),
            results=results,
            response_time=data.get("response_time", 0.0),
        )

    def _update_stats(self, success: bool, elapsed: float) -> None:
        """更新请求统计"""
        self._stats["total_requests"] += 1
        if success:
            self._stats["success_requests"] += 1
        else:
            self._stats["failed_requests"] += 1
        self._stats["total_response_time"] += elapsed
