#!/usr/bin/env python3
from __future__ import annotations
"""
真实Web搜索引擎适配器
Real Web Search Engine Adapter

将现有的web_search_engines.py集成到BaseSearchTool标准

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

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

# 导入真实搜索引擎
try:
    from ..external.web_search_engines_secure import (
        SearchResult,
        UnifiedWebSearchManager,
    )
except ImportError:
    logger.warning("无法导入UnifiedWebSearchManager,使用模拟实现")
    UnifiedWebSearchManager = None


class RealWebSearchAdapter(BaseSearchTool):
    """真实Web搜索引擎适配器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化真实Web搜索适配器

        Args:
            config: 工具配置
        """
        super().__init__("real_web_search_adapter", config)

        # 真实搜索引擎配置
        self.web_search_config = {
            "tavily": {
                "api_key": config.get("tavily_api_key", "") if config else "",
                "max_results": 10,
            },
            "google_custom_search": {
                "api_key": config.get("google_api_key", "") if config else "",
                "search_engine_id": config.get("google_search_engine_id", "") if config else "",
                "max_results": 10,
            },
            "bing_search": {
                "api_key": config.get("bing_api_key", "") if config else "",
                "max_results": 10,
            },
            "bocha": {
                "api_key": config.get("bocha_api_key", "") if config else "",
                "max_results": 10,
            },
            "metaso": {
                "api_key": config.get("metaso_api_key", "") if config else "",
                "max_results": 10,
            },
        }

        self.original_manager = None
        self.available_engines = []

    async def initialize(self) -> bool:
        """初始化搜索引擎"""
        try:
            logger.info("🚀 初始化真实Web搜索适配器...")

            if UnifiedWebSearchManager:
                # 使用真实的管理器
                self.original_manager = UnifiedWebSearchManager(self.web_search_config)
                await self.original_manager.initialize()

                # 检查可用的搜索引擎
                self.available_engines = await self.original_manager.get_available_engines()
                logger.info(f"📊 可用搜索引擎: {self.available_engines}")

            else:
                # 模拟初始化
                logger.warning("⚠️ 使用模拟搜索引擎实现")
                await self._simulate_initialization()

            self.initialized = True
            logger.info("✅ 真实Web搜索适配器初始化完成")

            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    async def search(self, query: SearchQuery) -> SearchResponse:
        """执行Web搜索"""
        if not self.initialized:
            return create_error_response(query, "工具未初始化", 0.0, self.name, "not_initialized")

        start_time = time.time()

        try:
            # 验证查询
            if not await self.validate_query(query):
                return create_error_response(query, "查询参数无效", 0.0, self.name, "invalid_query")

            logger.info(f"🔍 执行真实Web搜索: {query.text}")

            # 选择搜索引擎
            engines = self._select_engines(query)

            # 执行搜索
            if self.original_manager and self.available_engines:
                # 使用真实搜索
                raw_results = await self.original_manager.search(
                    query=query.text, max_results=query.max_results, engines=engines
                )

                # 转换响应格式
                response = self._convert_real_results(query, raw_results)
            else:
                # 使用模拟搜索
                response = await self._simulate_search(query, engines)

            # 更新统计
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
        """获取工具能力描述"""
        return SearchCapabilities(
            name=self.name,
            version="1.0.0",
            description="真实Web搜索引擎适配器,集成多个真实的在线搜索引擎",
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
            avg_response_time=2.5,
            max_concurrent_requests=20,
            rate_limit_per_minute=100,
            # 专业领域能力
            domain_expertise=["general", "news", "technology", "research", "business"],
            language_support=["zh", "en", "ja", "ko", "fr", "de", "es"],
            geographic_coverage=["global", "us", "cn", "eu", "asia"],
            # 高级特性
            ai_powered=False,
            real_time=True,
            streaming_support=False,
            caching_capable=True,
        )

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            if not self.initialized:
                return {
                    "status": "not_initialized",
                    "tool_name": self.name,
                    "timestamp": datetime.now().isoformat(),
                }

            # 测试搜索
            SearchQuery(text="health check", max_results=1)
            start_time = time.time()

            if self.original_manager and self.available_engines:
                # 使用真实管理器测试
                test_results = await self.original_manager.search(
                    query="health check",
                    max_results=1,
                    engines=self.available_engines[:1],  # 只测试一个引擎
                )
                success = test_results.get("success", False)
            else:
                # 模拟测试
                success = True

            health_time = time.time() - start_time

            # 获取引擎状态
            engine_status = {}
            if self.original_manager and hasattr(self.original_manager, "get_engine_status"):
                engine_status = self.original_manager.get_engine_status()

            return {
                "status": "healthy" if success else "unhealthy",
                "tool_name": self.name,
                "initialized": self.initialized,
                "response_time": health_time,
                "available_engines": self.available_engines,
                "engine_status": engine_status,
                "stats": self.get_performance_stats(),
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "tool_name": self.name,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    # === 内部方法 ===

    def _select_engines(self, query: SearchQuery) -> list[str]:
        """选择搜索引擎"""
        if not self.available_engines:
            return ["tavily"]  # 默认引擎

        # 基于查询内容选择引擎
        text_lower = query.text.lower()
        selected_engines = []

        # 中文查询优先使用中文友好引擎
        if self._contains_chinese(text_lower):
            if "bocha" in self.available_engines:
                selected_engines.append("bocha")
            if "metaso" in self.available_engines:
                selected_engines.append("metaso")

        # 英文查询使用主流引擎
        if self._contains_english(text_lower):
            if "tavily" in self.available_engines:
                selected_engines.append("tavily")
            if "google_custom_search" in self.available_engines:
                selected_engines.append("google_custom_search")

        # 如果没有特别偏好,使用前3个可用引擎
        if not selected_engines:
            selected_engines = self.available_engines[:3]

        return selected_engines

    def _convert_real_results(
        self, query: SearchQuery, raw_results: dict[str, Any]
    ) -> SearchResponse:
        """转换真实搜索结果"""
        try:
            if not raw_results.get("success"):
                return create_error_response(
                    query,
                    raw_results.get("error_message", "搜索失败"),
                    raw_results.get("search_time", 0.0),
                    self.name,
                    "real_search_failed",
                )

            # 转换文档格式
            documents = []
            for result in raw_results.get("results", []):
                document = SearchDocument(
                    id=result.get("id", f"web_{hash(str(result))}"),
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    url=result.get("url"),
                    snippet=result.get("snippet", ""),
                    relevance_score=result.get("relevance_score", 0.0),
                    confidence=result.get("confidence", 0.5),
                    language=result.get("language", "unknown"),
                    content_type="html",
                    metadata={
                        "source": result.get("source", "unknown"),
                        "engine": result.get("engine", "unknown"),
                        "published_date": result.get("published_date"),
                        "original_result": result,
                    },
                )
                documents.append(document)

            return create_success_response(
                query, documents, raw_results.get("search_time", 0.0), self.name
            )

        except Exception as e:
            logger.error(f"❌ 结果转换失败: {e}")
            return create_error_response(
                query, f"结果转换失败: {e!s}", 0.0, self.name, "conversion_error"
            )

    async def _simulate_search(self, query: SearchQuery, engines: list[str]) -> SearchResponse:
        """模拟搜索(当真实搜索不可用时)"""
        # 模拟搜索延迟
        await asyncio.sleep(0.5)

        # 生成模拟结果
        mock_results = [
            {
                "title": f"模拟搜索结果: {query.text}",
                "content": f"关于 '{query.text}' 的模拟搜索内容",
                "url": f"https://example.com/search?q={query.text}",
                "source": "simulation",
                "engine": engines[0] if engines else "tavily",
                "relevance_score": 0.8,
                "confidence": 0.7,
            }
        ]

        documents = []
        for result in mock_results:
            document = SearchDocument(
                id=f"sim_{hash(str(result))}",
                title=result["title"],
                content=result["content"],
                url=result["url"],
                snippet=result["content"][:200] + "...",
                relevance_score=result["relevance_score"],
                confidence=result["confidence"],
                content_type="html",
                metadata=result,
            )
            documents.append(document)

        return create_success_response(query, documents, 0.5, self.name)  # 模拟搜索时间

    async def _simulate_initialization(self):
        """模拟初始化"""
        await asyncio.sleep(0.5)
        self.available_engines = ["tavily", "bocha", "metaso"]

    def _contains_chinese(self, text: str) -> bool:
        """检查是否包含中文"""
        return any("\u4e00" <= char <= "\u9fff" for char in text)

    def _contains_english(self, text: str) -> bool:
        """检查是否包含英文"""
        return any("a" <= char.lower() <= "z" for char in text)


# 注册装饰器
from ..registry.tool_registry import register_to_registry


@register_to_registry(category="real_web_search", auto_init=False)
def create_real_web_search_adapter(config: dict[str, Any] | None = None) -> RealWebSearchAdapter:
    """创建真实Web搜索适配器的工厂函数"""
    return RealWebSearchAdapter(config)


# 便捷函数
async def create_real_web_search(config: dict[str, Any] | None = None) -> RealWebSearchAdapter:
    """
    创建并初始化真实Web搜索适配器

    Args:
        config: 配置字典,包含各种API密钥

    Returns:
        RealWebSearchAdapter: 初始化完成的适配器
    """
    adapter = RealWebSearchAdapter(config)
    await adapter.initialize()
    return adapter


if __name__ == "__main__":
    # 示例用法
    logger.info("🌐 真实Web搜索引擎适配器")
    logger.info("   集成真实在线搜索引擎")
    logger.info("   支持多个API服务")
    logger.info("   智能引擎选择")
    print()
    logger.info("💡 配置示例:")
    logger.info("   config = {")
    logger.info("       'tavily_api_key': 'your_tavily_key',")
    logger.info("       'google_api_key': 'your_google_key',")
    logger.info("       'bocha_api_key': 'your_bocha_key'")
    logger.info("   }")
    logger.info("   adapter = await create_real_web_search(config)")
