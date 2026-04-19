#!/usr/bin/env python3
"""
分散式智能搜索架构 - 适配版Web搜索管理器
Decentralized Intelligent Search Architecture - Adapted Web Search Manager

基于现有UnifiedWebSearchManager重构,符合BaseSearchTool标准

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime
from typing import Any

# 导入原始的Web搜索引擎
from ..external.web_search_engines import SearchResponse as WebSearchResponse
from ..external.web_search_engines import UnifiedWebSearchManager
from ..standards.base_search_tool import (
    BaseSearchTool,
    SearchCapabilities,
    SearchDocument,
    SearchQuery,
    SearchResponse,
    SearchType,
    create_error_response,
    create_success_response,
)

logger = logging.getLogger(__name__)


class AdaptedWebSearchManager(BaseSearchTool):
    """
    适配版Web搜索管理器

    将现有的UnifiedWebSearchManager包装为符合BaseSearchTool标准的工具
    保持原有功能的同时,支持统一管理和智能选择
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化适配版Web搜索管理器

        Args:
            config: 工具配置
        """
        super().__init__("adapted_web_search_manager", config)

        # 初始化原始Web搜索管理器
        self.web_search_config = config.get("web_search", {}) if config else {}
        self.original_manager = None

    async def initialize(self) -> bool:
        """
        初始化Web搜索管理器

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("🚀 初始化适配版Web搜索管理器...")

            # 初始化原始管理器
            self.original_manager = UnifiedWebSearchManager(self.web_search_config)

            # 验证配置和API密钥
            if not await self._validate_configuration():
                logger.error("❌ Web搜索配置验证失败")
                return False

            self.initialized = True
            logger.info("✅ 适配版Web搜索管理器初始化完成")

            return True

        except Exception as e:
            logger.error(f"❌ 适配版Web搜索管理器初始化失败: {e}")
            return False

    async def search(self, query: SearchQuery) -> SearchResponse:
        """
        执行Web搜索

        Args:
            query: 标准化搜索查询

        Returns:
            SearchResponse: 标准化搜索响应
        """
        if not self.initialized:
            return create_error_response(query, "工具未初始化", 0.0, self.name, "not_initialized")

        start_time = time.time()

        try:
            # 验证查询
            if not await self.validate_query(query):
                return create_error_response(query, "查询参数无效", 0.0, self.name, "invalid_query")

            logger.info(f"🔍 执行Web搜索: {query.text}")

            # 检查 original_manager 是否已初始化
            if self.original_manager is None:
                return create_error_response(
                    query, "Web搜索引擎未初始化", 0.0, self.name, "manager_not_initialized"
                )

            # 转换查询格式
            self._convert_query_format(query)

            # 执行原始搜索
            raw_response = await self.original_manager.search(
                query=query.text,
                max_results=query.max_results,
                engines=self._select_engines(query) or [],  # type: ignore
                search_type=self._convert_search_type(query.search_type),
            )

            # 转换响应格式
            response = self._convert_response_format(query, raw_response)

            # 更新性能统计
            search_time = time.time() - start_time
            self.update_stats(response.success, search_time)

            logger.info(
                f"✅ Web搜索完成: 找到 {response.total_found} 个结果,耗时 {search_time:.3f}s"
            )

            return response

        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"❌ Web搜索失败: {e}")

            return create_error_response(query, str(e), search_time, self.name, "search_exception")

    def get_capabilities(self) -> SearchCapabilities:
        """
        获取工具能力描述

        Returns:
            SearchCapabilities: 工具能力详细信息
        """
        return SearchCapabilities(
            name=self.name,
            version="1.0.0",
            description="适配版Web搜索管理器,支持多种搜索引擎的统一接口",
            category="web_search",
            # 支持的搜索类型
            supported_search_types=[SearchType.WEB, SearchType.FULLTEXT, SearchType.HYBRID],
            # 能力特征
            max_results=50,
            supports_filters=True,
            supports_sorting=True,
            supports_faceting=False,
            supports_pagination=True,
            # 性能特征
            avg_response_time=2.0,
            max_concurrent_requests=20,
            rate_limit_per_minute=100,
            # 专业领域能力
            domain_expertise=["general", "news", "research", "technology"],
            language_support=["zh", "en", "ja", "ko", "fr", "de", "es"],
            geographic_coverage=["global", "us", "cn", "eu", "asia"],
            # 高级特性
            ai_powered=False,
            real_time=True,
            streaming_support=False,
            caching_capable=True,
        )

    async def health_check(self) -> dict[str, Any]:
        """
        健康检查

        Returns:
            Dict: 健康状态信息
        """
        try:
            if not self.initialized:
                return {
                    "status": "not_initialized",
                    "tool_name": self.name,
                    "timestamp": datetime.now().isoformat(),
                }

            # 测试搜索
            test_query = SearchQuery(text="health check test", max_results=1)
            start_time = time.time()

            response = await self.search(test_query)

            health_time = time.time() - start_time

            # 获取原始管理器状态
            manager_stats = getattr(self.original_manager, "get_stats", lambda: {})()  # type: ignore

            return {
                "status": "healthy" if response.success else "unhealthy",
                "tool_name": self.name,
                "initialized": self.initialized,
                "response_time": health_time,
                "last_check": datetime.now().isoformat(),
                "uptime": time.time() - self._start_time,
                "test_search_success": response.success,
                "manager_stats": manager_stats,
                "stats": self.get_performance_stats(),
            }

        except Exception as e:
            return {
                "status": "error",
                "tool_name": self.name,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    # === 配置和更新方法 ===

    async def update_config(self, key: str, value: Any):
        """
        更新配置

        Args:
            key: 配置键
            value: 配置值
        """
        if key.startswith("web_search."):
            # 传递给原始管理器
            manager_key = key[12:]  # 移除 'web_search.' 前缀
            if self.original_manager is not None and hasattr(
                self.original_manager, "update_config"
            ):
                await self.original_manager.update_config(manager_key, value)  # type: ignore
            else:
                # 直接更新配置字典
                if self.original_manager is not None and hasattr(self.original_manager, "config"):
                    self.original_manager.config[manager_key] = value  # type: ignore

        self.config[key] = value

    def get_available_engines(self) -> list[str]:
        """
        获取可用的搜索引擎

        Returns:
            list[str]: 搜索引擎列表
        """
        if self.original_manager is not None and hasattr(
            self.original_manager, "get_available_engines"
        ):
            return self.original_manager.get_available_engines()  # type: ignore
        return ["tavily", "google_custom_search", "bocha", "metaso"]

    def get_engine_status(self) -> dict[str, dict[str, Any]]:
        """
        获取搜索引擎状态

        Returns:
            Dict: 搜索引擎状态
        """
        if self.original_manager is not None and hasattr(
            self.original_manager, "get_engine_status"
        ):
            return self.original_manager.get_engine_status()  # type: ignore
        return {}

    # === 内部转换方法 ===

    async def _validate_configuration(self) -> bool:
        """验证配置"""
        try:
            # 检查是否有可用的API密钥
            if self.original_manager is not None and hasattr(
                self.original_manager, "get_available_engines"
            ):
                engines = self.original_manager.get_available_engines()  # type: ignore
                if not engines:
                    logger.warning("⚠️ 没有配置可用的搜索引擎API密钥")
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ 配置验证失败: {e}")
            return False

    def _convert_query_format(self, query: SearchQuery) -> dict[str, Any]:
        """转换查询格式"""
        return {
            "text": query.text,
            "max_results": query.max_results,
            "filters": query.filters,
            "sort_by": query.sort_by,
            "timeout": query.timeout,
        }

    def _select_engines(self, query: SearchQuery) -> list[str | None]:
        """选择搜索引擎"""
        # 基于查询内容选择合适的引擎
        text_lower = query.text.lower()

        engines = []

        # 中文查询优先使用中文友好引擎
        if self._contains_chinese(text_lower):
            engines.extend(["bocha", "metaso"])

        # 英文查询使用主流引擎
        if self._contains_english(text_lower):
            engines.extend(["tavily", "google_custom_search"])

        # 默认使用所有可用引擎
        if not engines:
            engines = self.get_available_engines()

        return engines[:3]  # 最多使用3个引擎

    def _convert_search_type(self, search_type: SearchType) -> str:
        """转换搜索类型"""
        type_mapping = {
            SearchType.WEB: "web",
            SearchType.FULLTEXT: "fulltext",
            SearchType.SEMANTIC: "semantic",
            SearchType.HYBRID: "hybrid",
        }
        return type_mapping.get(search_type, "web")

    def _convert_response_format(
        self, query: SearchQuery, raw_response: WebSearchResponse
    ) -> SearchResponse:
        """转换响应格式"""
        try:
            if not raw_response.success:
                return create_error_response(
                    query,
                    raw_response.error_message or "搜索失败",
                    raw_response.search_time or 0.0,
                    self.name,
                    "search_failed",
                )

            # 转换文档格式
            documents = []
            for result in raw_response.results:
                # SearchResult 是 dataclass,使用属性访问而不是字典访问
                document = SearchDocument(
                    id=f"web_{hash(str(result))}",
                    title=result.title,
                    content=result.snippet,
                    url=result.url,
                    snippet=result.snippet,
                    relevance_score=result.relevance_score,
                    confidence=0.5,  # 默认置信度
                    language="unknown",
                    content_type="html",
                    metadata={
                        "source": result.engine,
                        "engine": result.engine,
                        "published_date": result.timestamp,
                        "position": result.position,
                        "original_result": result,
                    },
                )
                documents.append(document)

            # 计算平均相关性分数
            (
                sum(doc.relevance_score for doc in documents) / len(documents) if documents else 0.0
            )

            return create_success_response(
                query, documents, raw_response.search_time or 0.0, self.name
            )

        except Exception as e:
            logger.error(f"❌ 响应格式转换失败: {e}")
            return create_error_response(
                query, f"响应转换失败: {e!s}", 0.0, self.name, "conversion_error"
            )

    def _contains_chinese(self, text: str) -> bool:
        """检查是否包含中文"""
        return any("\u4e00" <= char <= "\u9fff" for char in text)

    def _contains_english(self, text: str) -> bool:
        """检查是否包含英文"""
        return any("a" <= char.lower() <= "z" for char in text)

    # === 统计和监控方法 ===

    def get_search_stats(self) -> dict[str, Any]:
        """获取搜索统计"""
        stats = self.get_performance_stats()

        # 添加原始管理器统计
        if self.original_manager is not None and hasattr(self.original_manager, "get_stats"):
            manager_stats = self.original_manager.get_stats()  # type: ignore
            stats["manager_stats"] = manager_stats

        # 添加引擎状态
        stats["engine_status"] = self.get_engine_status()

        return stats

    async def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "last_request_time": None,
        }

        # 重置原始管理器统计(如果支持)
        if self.original_manager is not None and hasattr(self.original_manager, "reset_stats"):
            await self.original_manager.reset_stats()  # type: ignore

    # === 高级功能 ===

    async def search_with_fallback(
        self, query: SearchQuery, fallback_engines: list[str]
    ) -> SearchResponse:
        """
        带回退的搜索

        Args:
            query: 搜索查询
            fallback_engines: 回退搜索引擎列表

        Returns:
            SearchResponse: 搜索响应
        """
        try:
            # 首先尝试正常搜索
            response = await self.search(query)

            if response.success or response.total_found > 0:
                return response

            logger.info(f"🔄 主搜索失败,尝试回退引擎: {fallback_engines}")

            # 尝试回退引擎
            for engine in fallback_engines:
                try:
                    if self.original_manager is None:
                        continue

                    fallback_response = await self.original_manager.search(
                        query=query.text,
                        max_results=query.max_results,
                        engines=[engine],  # type: ignore
                    )

                    if fallback_response.success and fallback_response.results:
                        converted_response = self._convert_response_format(query, fallback_response)
                        converted_response.metadata["fallback_engine"] = engine
                        return converted_response

                except Exception as e:
                    logger.warning(f"⚠️ 回退引擎 {engine} 也失败: {e}")
                    continue

            # 所有回退都失败
            return create_error_response(
                query, "主搜索和所有回退引擎都失败", 0.0, self.name, "all_fallbacks_failed"
            )

        except Exception as e:
            return create_error_response(
                query, f"带回退的搜索失败: {e!s}", 0.0, self.name, "fallback_search_error"
            )

    async def batch_search(
        self, queries: list[SearchQuery], max_concurrent: int = 5
    ) -> list[SearchResponse]:
        """
        批量搜索

        Args:
            queries: 搜索查询列表
            max_concurrent: 最大并发数

        Returns:
            list[SearchResponse]: 搜索响应列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def search_single(query: SearchQuery) -> SearchResponse:
            async with semaphore:
                return await self.search(query)

        tasks = [search_single(query) for query in queries]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                processed_responses.append(
                    create_error_response(
                        queries[i],
                        f"批量搜索异常: {response!s}",
                        0.0,
                        self.name,
                        "batch_search_error",
                    )
                )
            else:
                processed_responses.append(response)

        return processed_responses

    def __str__(self) -> str:
        return f"AdaptedWebSearchManager(name='{self.name}', initialized={self.initialized})"

    def __repr__(self) -> str:
        return self.__str__()


# 便捷函数
async def create_adapted_web_search_manager(
    config: dict[str, Any] | None = None,
) -> AdaptedWebSearchManager:
    """
    创建适配版Web搜索管理器

    Args:
        config: 配置字典

    Returns:
        AdaptedWebSearchManager: 适配版Web搜索管理器实例
    """
    manager = AdaptedWebSearchManager(config)
    await manager.initialize()
    return manager


# 注册装饰器
from ..registry.tool_registry import register_to_registry


@register_to_registry(category="web_search", auto_init=False)
def create_web_search_tool(config: dict[str, Any] | None = None) -> AdaptedWebSearchManager:
    """创建Web搜索工具的工厂函数"""
    return AdaptedWebSearchManager(config)


if __name__ == "__main__":
    # 示例用法
    logger.info("🌐 适配版Web搜索管理器")
    logger.info("   兼容BaseSearchTool标准")
    logger.info("   支持智能选择和协调")
    logger.info("   保持原有功能")
    print()
    logger.info("💡 使用方法:")
    logger.info("   manager = AdaptedWebSearchManager()")
    logger.info("   await manager.initialize()")
    logger.info("   query = SearchQuery(text='Python教程', max_results=10)")
    logger.info("   response = await manager.search(query)")
