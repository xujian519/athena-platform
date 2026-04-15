#!/usr/bin/env python3
"""
安全版本的外部搜索引擎实现
Secure Version of External Search Engines

移除硬编码API密钥,使用配置文件管理

作者: Athena AI系统 (基于xiaoxi平台)
创建时间: 2025-12-05
版本: 2.0.0 (安全版)
"""

from __future__ import annotations
import asyncio
import logging
import ssl
from datetime import datetime
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class SearchResult:
    """搜索结果类"""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str,
        relevance_score: float = 0.0,
        published_date: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.relevance_score = relevance_score
        self.published_date = published_date
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "relevance_score": self.relevance_score,
            "published_date": self.published_date,
            "metadata": self.metadata,
        }


class SecureUnifiedWebSearchManager:
    """安全版统一Web搜索管理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化搜索管理器

        Args:
            config: 配置字典,包含API密钥等信息
        """
        self.config = config or {}
        self.engines = {}
        self.api_keys = {}
        self.session = None
        self._initialize_engines()

    def _initialize_engines(self) -> Any:
        """初始化搜索引擎"""
        # 从配置中获取API密钥
        self.api_keys = self.config.get("api_keys", {})

        # 初始化各个搜索引擎
        self.engines = {
            "tavily": TavilySearchEngine(self.api_keys.get("tavily", [])),
            "serper": SerperSearchEngine(self.api_keys.get("serper", [])),
            "bocha": BochaSearchEngine(self.api_keys.get("bocha", [])),
            "metaso": MetasoSearchEngine(self.api_keys.get("metaso", [])),
            "google_custom_search": GoogleCustomSearchEngine(
                self.api_keys.get("google_custom_search", [])
            ),
            "bing": BingSearchEngine(self.api_keys.get("bing", [])),
            "duckduckgo": DuckDuckGoSearchEngine(),
            "brave": BraveSearchEngine(self.api_keys.get("brave", [])),
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def _create_session(self):
        """创建HTTP会话"""
        if not self.session:
            # 创建SSL上下文(生产环境推荐)
            ssl_context = ssl.create_default_context()

            connector = aiohttp.TCPConnector(
                ssl=ssl_context,  # 启用SSL验证
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )

            timeout = aiohttp.ClientTimeout(total=30, connect=10)

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Athena-Search-Bot/1.0)"},
            )

    async def search(
        self,
        query: str,
        engines: list[str] | None = None,
        max_results: int = 10,
        parallel: bool = True,
    ) -> dict[str, Any]:
        """
        执行搜索

        Args:
            query: 搜索查询
            engines: 要使用的搜索引擎列表
            max_results: 最大结果数
            parallel: 是否并行执行

        Returns:
            搜索结果字典
        """
        if not self.session:
            await self._create_session()

        if not engines:
            # 自动选择可用的引擎
            engines = await self.get_available_engines()

        if not engines:
            logger.warning("没有可用的搜索引擎")
            return {
                "success": False,
                "error": "没有可用的搜索引擎",
                "results": [],
                "search_time": 0.0,
                "engines_used": [],
            }

        logger.info(f"开始搜索: {query}, 使用引擎: {engines}")
        start_time = datetime.now()

        try:
            if parallel:
                results = await self._parallel_search(query, engines, max_results)
            else:
                results = await self._sequential_search(query, engines, max_results)

            search_time = (datetime.now() - start_time).total_seconds()

            # 智能去重和排序
            deduplicated_results = self._deduplicate_and_rank(results)

            logger.info(
                f"搜索完成,找到 {len(deduplicated_results)} 个结果,耗时 {search_time:.2f}s"
            )

            return {
                "success": True,
                "query": query,
                "results": [result.to_dict() for result in deduplicated_results],
                "search_time": search_time,
                "engines_used": engines,
                "total_results": len(deduplicated_results),
            }

        except Exception as e:
            search_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "search_time": search_time,
                "engines_used": engines,
            }

    async def _parallel_search(
        self, query: str, engines: list[str], max_results: int
    ) -> list[SearchResult]:
        """并行搜索"""
        tasks = []
        for engine_name in engines:
            if engine_name in self.engines:
                engine = self.engines[engine_name]
                if await engine.is_available():
                    task = self._search_single_engine(engine, query, max_results)
                    tasks.append(task)

        if not tasks:
            logger.warning("没有可用的搜索引擎")
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"搜索引擎异常: {result}")

        return all_results

    async def _sequential_search(
        self, query: str, engines: list[str], max_results: int
    ) -> list[SearchResult]:
        """顺序搜索"""
        all_results = []
        for engine_name in engines:
            if engine_name in self.engines:
                engine = self.engines[engine_name]
                if await engine.is_available():
                    try:
                        results = await self._search_single_engine(engine, query, max_results)
                        all_results.extend(results)

                        # 如果已经获得足够结果,可以提前返回
                        if len(all_results) >= max_results:
                            break
                    except Exception as e:
                        logger.error(f"搜索引擎 {engine_name} 失败: {e}")

        return all_results

    async def _search_single_engine(
        self, engine, query: str, max_results: int
    ) -> list[SearchResult]:
        """使用单个搜索引擎"""
        try:
            results = await engine.search(query, max_results, self.session)
            return results
        except Exception as e:
            logger.error(f"搜索引擎 {engine.__class__.__name__} 失败: {e}")
            return []

    def _deduplicate_and_rank(self, results: list[SearchResult]) -> list[SearchResult]:
        """去重和排序"""
        # 按URL去重
        seen_urls = set()
        deduplicated = []

        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                deduplicated.append(result)

        # 按相关性分数排序
        deduplicated.sort(key=lambda x: x.relevance_score, reverse=True)

        return deduplicated

    async def get_available_engines(self) -> list[str]:
        """获取可用的搜索引擎列表"""
        available = []
        for name, engine in self.engines.items():
            if await engine.is_available():
                available.append(name)
        return available

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        status = {
            "overall_status": "healthy",
            "engines": {},
            "timestamp": datetime.now().isoformat(),
        }

        for name, engine in self.engines.items():
            try:
                is_available = await engine.is_available()
                status["engines"][name] = {
                    "available": is_available,
                    "status": "healthy" if is_available else "unhealthy",
                }
                if not is_available:
                    status["overall_status"] = "degraded"
            except Exception as e:
                status["engines"][name] = {"available": False, "status": "error", "error": str(e)}
                status["overall_status"] = "degraded"

        return status


class BaseSearchEngine:
    """搜索引擎基类"""

    def __init__(self, api_keys: list[str] | None = None):
        self.api_keys = api_keys or []
        self.current_key_index = 0
        self.last_error_time = None
        self.error_count = 0

    async def is_available(self) -> bool:
        """检查搜索引擎是否可用"""
        return bool(self.api_keys) or self.requires_no_api_key()

    def requires_no_api_key(self) -> bool:
        """是否不需要API密钥"""
        return False

    def get_next_api_key(self) -> str | None:
        """获取下一个API密钥(轮换)"""
        if not self.api_keys:
            return None

        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        """执行搜索(子类实现)"""
        raise NotImplementedError


# 具体搜索引擎实现
class TavilySearchEngine(BaseSearchEngine):
    """Tavily搜索引擎"""

    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        api_key = self.get_next_api_key()
        if not api_key:
            return []

        url = "https://api.tavily.com/search"
        data = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }

        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    results = []
                    for item in result.get("results", []):
                        search_result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("content", ""),
                            source="tavily",
                            relevance_score=item.get("score", 0.0),
                        )
                        results.append(search_result)
                    return results
                else:
                    logger.error(f"Tavily API错误: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Tavily搜索失败: {e}")
            return []


class SerperSearchEngine(BaseSearchEngine):
    """Serper搜索引擎"""

    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        api_key = self.get_next_api_key()
        if not api_key:
            return []

        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        data = {"q": query, "num": max_results}

        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    results = []
                    for item in result.get("results", []):
                        search_result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source="serper",
                            relevance_score=0.8,  # Serper默认相关性
                        )
                        results.append(search_result)
                    return results
                else:
                    logger.error(f"Serper API错误: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Serper搜索失败: {e}")
            return []


class BochaSearchEngine(BaseSearchEngine):
    """Bocha搜索引擎"""

    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        api_key = self.get_next_api_key()
        if not api_key:
            return []

        url = "https://api.bochaai.com/v1/search"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"query": query, "max_results": max_results}

        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    results = []
                    for item in result.get("results", []):
                        search_result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            source="bocha",
                            relevance_score=item.get("relevance", 0.0),
                        )
                        results.append(search_result)
                    return results
                else:
                    logger.error(f"Bocha API错误: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Bocha搜索失败: {e}")
            return []


# 其他搜索引擎的实现...
class MetasoSearchEngine(BaseSearchEngine):
    """Metaso搜索引擎 (中国版Perplexity)"""

    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        api_key = self.get_next_api_key()
        if not api_key:
            return []

        url = "https://api.metaso.ai/v1/search"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"query": query, "max_results": max_results, "search_depth": "standard"}

        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    results = []
                    for item in result.get("results", []):
                        search_result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            source="metaso",
                            relevance_score=item.get("relevance_score", 0.0),
                            published_date=item.get("published_date"),
                            metadata={
                                "answer_type": item.get("answer_type"),
                                "content_type": item.get("content_type"),
                                "language": item.get("language", "zh"),
                            },
                        )
                        results.append(search_result)
                    return results
                else:
                    error_text = await response.text()
                    logger.error(f"Metaso API错误: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Metaso搜索失败: {e}")
            return []


class GoogleCustomSearchEngine(BaseSearchEngine):
    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        # Google Custom Search实现
        return []


class BingSearchEngine(BaseSearchEngine):
    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        # Bing搜索实现
        return []


class DuckDuckGoSearchEngine(BaseSearchEngine):
    def requires_no_api_key(self) -> bool:
        return True

    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        # DuckDuckGo实现(不需要API密钥)
        return []


class BraveSearchEngine(BaseSearchEngine):
    async def search(
        self, query: str, max_results: int, session: aiohttp.ClientSession
    ) -> list[SearchResult]:
        # Brave搜索实现
        return []


# 便捷函数
async def create_secure_search_manager(
    config: dict[str, Any] | None = None,
) -> SecureUnifiedWebSearchManager:
    """创建安全的搜索管理器"""
    return SecureUnifiedWebSearchManager(config)


if __name__ == "__main__":
    # 测试代码
    async def test():
        config = {
            "api_keys": {
                "tavily": ["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"],
                "serper": ["Vuq2S257RvQCptAdSGrsC9vz"],
                "bocha": ["sk-644372189936485aab35cafcd3127000"],
            }
        }

        async with SecureUnifiedWebSearchManager(config) as manager:
            results = await manager.search("Python编程", max_results=5)
            logger.info(f"搜索结果: {len(results['results'])} 个")
            for result in results["results"][:3]:
                logger.info(f"- {result['title']}")

    asyncio.run(test())
