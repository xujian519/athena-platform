#!/usr/bin/env python3
"""
联网搜索引擎 - 统一管理器
Web Search Engines - Unified Manager

统一管理多个搜索引擎，实现回退和负载均衡

作者: 小娜 & 小诺
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

from typing import Any, Optional

from core.logging_config import setup_logging
from core.search.external.web_search.api_key_manager import APIKeyManager
from core.search.external.web_search.engines.all import (
    BochaSearchEngine,
    GoogleCustomSearchEngine,
    MetasoSearchEngine,
    TavilySearchEngine,
)
from core.search.external.web_search.types import (
    SearchEngineType,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = setup_logging()


class UnifiedWebSearchManager:
    """统一联网搜索管理器 - 整合多个搜索引擎"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化统一搜索管理器

        Args:
            config: 搜索配置
        """
        self.config = config or self._get_default_config()

        # API密钥管理
        api_keys = self.config.get("api_keys", {})
        self.api_key_manager = APIKeyManager(api_keys)

        # 初始化搜索引擎
        self.engines: dict[SearchEngineType, Any] = {}
        self._initialize_engines()

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "api_keys": {
                "tavily": [
                    "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",
                    "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",
                ],
                "bocha": ["api-key-2025103121204559208"],
                "metaso": [
                    "mk-CA690CA8375C1E2E0856389E3B0BA587",
                    "mk-C1C2001C283A4EDB2DABBD62E07C5B13",
                ],
                "google_custom_search": ["YOUR_GOOGLE_API_KEY"],
            },
            "engine_priorities": [
                SearchEngineType.TAVILY,
                SearchEngineType.METASO,
                SearchEngineType.BOCHA,
                SearchEngineType.GOOGLE_CUSTOM_SEARCH,
                SearchEngineType.BING_SEARCH,
            ],
            "max_results_per_engine": 10,
            "timeout": 30,
            "retry_count": 2,
            "enable_fallback": True,
        }

    def _initialize_engines(self) -> Any:
        """初始化搜索引擎"""
        # 直接从配置中获取API密钥
        api_keys_config = self.config.get("api_keys", {})

        # 初始化Tavily
        tavily_keys = api_keys_config.get("tavily", [])
        if tavily_keys:
            self.engines[SearchEngineType.TAVILY] = TavilySearchEngine(
                tavily_keys, self.config.get("engine_configs", {}).get("tavily", {})
            )
            logger.info(f"✅ Tavily引擎已初始化,配置了 {len(tavily_keys)} 个API密钥")

        # 初始化博查
        bocha_keys = api_keys_config.get("bocha", [])
        if bocha_keys:
            self.engines[SearchEngineType.BOCHA] = BochaSearchEngine(
                bocha_keys, self.config.get("engine_configs", {}).get("bocha", {})
            )
            logger.info(f"✅ 博查引擎已初始化,配置了 {len(bocha_keys)} 个API密钥")

        # 初始化秘塔
        metaso_keys = api_keys_config.get("metaso", [])
        if metaso_keys:
            self.engines[SearchEngineType.METASO] = MetasoSearchEngine(
                metaso_keys, self.config.get("engine_configs", {}).get("metaso", {})
            )
            logger.info(f"✅ 秘塔引擎已初始化,配置了 {len(metaso_keys)} 个API密钥")

        # 初始化Google Custom Search
        google_keys = api_keys_config.get("google_custom_search", [])
        if google_keys:
            self.engines[SearchEngineType.GOOGLE_CUSTOM_SEARCH] = (
                GoogleCustomSearchEngine(
                    google_keys,
                    self.config.get("engine_configs", {}).get(
                        "google_custom_search", {}
                    ),
                )
            )
            logger.info(
                f"✅ Google Custom Search引擎已初始化,配置了 {len(google_keys)} 个API密钥"
            )

        # 初始化DeepSearch深度搜索
        try:
            from core.search.deepsearch.deepsearch_integration import DeepSearchEngine

            self.engines[SearchEngineType.DEEPSEARCH] = DeepSearchEngine(
                ["integrated"],
                self.config.get("engine_configs", {}).get("deepsearch", {}),
            )
            logger.info("✅ DeepSearch深度搜索引擎已初始化")
        except ImportError as e:
            logger.warning(f"DeepSearch引擎初始化失败: {e}")
        except Exception as e:
            logger.error(f"DeepSearch引擎初始化异常: {e}")

    async def search(
        self,
        query: str,
        engines: Optional[list[SearchEngineType]] | None = None,
        **kwargs: Any,
    ) -> SearchResponse:
        """
        执行搜索

        Args:
            query: 搜索查询
            engines: 搜索引擎列表
            **kwargs: 其他搜索参数

        Returns:
            搜索响应
        """
        search_query = SearchQuery(query=query, **kwargs)  # type: ignore[arg-type]

        # 如果没有指定引擎,使用优先级顺序
        if not engines:
            engines = self.config.get("engine_priorities", [SearchEngineType.TAVILY])

        results: list[SearchResult] = []
        total_time = 0

        # 按优先级搜索
        for engine_type in engines:
            if engine_type not in self.engines:
                logger.warning(f"⚠️ 搜索引擎 {engine_type.value} 未初始化,跳过")
                continue

            try:
                search_result = await self.engines[engine_type].search(search_query)

                if search_result.success and search_result.results:
                    results.extend(search_result.results)
                    total_time += search_result.search_time

                    # 如果是第一个引擎且成功,可以提前返回
                    if len(engines) == 1:
                        return search_result

                    # 如果有足够结果,可以提前返回
                    if len(results) >= search_query.max_results:
                        break
                else:
                    logger.warning(
                        f"❌ {engine_type.value} 搜索失败: {search_result.error_message}"
                    )

                    # 如果启用回退机制,继续尝试下一个引擎
                    if not self.config.get("enable_fallback", True):
                        continue

            except Exception as e:
                logger.error(f"❌ {engine_type.value} 搜索异常: {e}")
                continue

        # 如果没有成功的结果,返回失败响应
        if not results:
            return SearchResponse(
                success=False,
                query=query,
                engine="multiple_engines",
                results=[],
                error_message="All search engines failed",
                search_time=total_time,
            )

        # 创建合并响应
        # 重新排序和去重
        unique_results = self._deduplicate_results(results)
        sorted_results = sorted(
            unique_results, key=lambda x: x.relevance_score, reverse=True
        )

        return SearchResponse(
            success=True,
            query=query,
            engine="unified",
            results=sorted_results[: search_query.max_results],
            total_results=len(sorted_results),
            search_time=total_time,
        )

    def _deduplicate_results(self, results: list[SearchResult]) -> list[SearchResult]:
        """去重搜索结果"""
        seen_urls = set()
        unique_results = []

        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return unique_results

    async def search_with_fallback(
        self, query: str, primary_engine: SearchEngineType, **kwargs: Any
    ) -> SearchResponse:
        """
        带回退的搜索

        Args:
            query: 搜索查询
            primary_engine: 主要搜索引擎
            **kwargs: 其他参数

        Returns:
            搜索响应
        """
        # 先尝试主要搜索引擎
        primary_result = await self.search(query, [primary_engine])

        if primary_result.success and primary_result.results:
            return primary_result

        # 主要引擎失败,尝试其他引擎
        logger.info(f"🔄 主要引擎 {primary_engine.value} 失败,尝试回退搜索")

        fallback_engines = [
            engine
            for engine in self.config.get("engine_priorities", [])
            if engine != primary_engine and engine in self.engines
        ]

        if fallback_engines:
            return await self.search(query, fallback_engines)

        # 所有引擎都失败
        return primary_result

    def get_engine_stats(self) -> dict[str, Any]:
        """获取搜索引擎统计信息"""
        stats: dict[str, Any] = {
            "available_engines": list(self.engines.keys()),
            "api_key_stats": self.api_key_manager.get_stats(),
        }

        # 添加各引擎的配置信息
        for engine_type, engine in self.engines.items():
            stats[engine_type.value] = {
                "name": engine.name,
                "base_url": engine.base_url,
                "configured_keys": len(engine.api_keys),
                "timeout": engine.timeout,
            }

        return stats
