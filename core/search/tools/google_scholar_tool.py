#!/usr/bin/env python3
from __future__ import annotations
"""
Google Scholar 搜索工具
Google Scholar Search Tool

基于 Serper API 的 Google Scholar 搜索工具

作者: 小诺·双鱼公主 (Xiaonuo Pisces Princess)
版本: v1.0.0
创建: 2025-12-31
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from ..external.serper_api_manager import (
    SerperAPIManager,
    SerperConfig,
    SerperSearchRequest,
    SerperSearchType,
)
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


class GoogleScholarSearchTool(BaseSearchTool):
    """
    Google Scholar 搜索工具

    功能:
    • 学术论文检索
    • 作者信息查询
    • 引用关系分析
    • 相关文献发现

    集成: Serper.dev API
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化 Google Scholar 搜索工具

        Args:
            config: 工具配置,包含:
                - serper_api_key: Serper API 密钥 (必需)
                - enable_cache: 是否启用缓存 (默认 True)
        """
        super().__init__("google_scholar_search", config)

        # Serper 配置
        self.serper_config = SerperConfig(
            api_key=config.get("serper_api_key", "") if config else "",
            enable_cache=config.get("enable_cache", True) if config else True,
        )

        self.serper_manager: SerperAPIManager | None = None

    async def initialize(self) -> bool:
        """初始化工具"""
        try:
            logger.info("🎓 初始化 Google Scholar 搜索工具...")

            if not self.serper_config.api_key:
                logger.warning("⚠️  未配置 Serper API 密钥,尝试从环境变量读取")
                import os

                self.serper_config.api_key = os.getenv("SERPER_API_KEY", "")

            if not self.serper_config.api_key:
                logger.error("❌ 缺少 Serper API 密钥")
                return False

            # 创建 Serper 管理器
            self.serper_manager = SerperAPIManager(self.serper_config)
            await self.serper_manager.initialize()

            self.initialized = True
            logger.info("✅ Google Scholar 搜索工具初始化完成")

            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    async def search(self, query: SearchQuery) -> SearchResponse:
        """
        执行 Google Scholar 搜索

        Args:
            query: 搜索查询对象

        Returns:
            SearchResponse: 搜索响应
        """
        if not self.initialized or not self.serper_manager:
            return create_error_response(query, "工具未初始化", 0.0, self.name, "not_initialized")

        start_time = time.time()

        try:
            # 验证查询
            if not await self.validate_query(query):
                return create_error_response(query, "查询参数无效", 0.0, self.name, "invalid_query")

            logger.info(f"📚 执行 Google Scholar 搜索: {query.text}")

            # 构建 Serper 请求
            serper_request = SerperSearchRequest(
                query=query.text,
                search_type=SerperSearchType.SCHOLAR,
                num_results=query.max_results or 10,
                gl=query.filters.get("country") if query.filters else None,
                hl=query.filters.get("language") if query.filters else None,
            )

            # 执行搜索
            serper_result = await self.serper_manager.search(serper_request)

            # 转换响应格式
            if serper_result.success:
                documents = self._convert_to_documents(serper_result.results, query)

                search_time = time.time() - start_time
                response = create_success_response(
                    query,
                    documents,
                    search_time,
                    self.name,
                    metadata={
                        "total_results": serper_result.total_results,
                        "api_credits_used": serper_result.api_credits_used,
                        "search_type": "scholar",
                    },
                )

                # 更新统计
                self.update_stats(True, search_time)

                logger.info(
                    f"✅ Scholar 搜索完成: 找到 {len(documents)} 个结果, "
                    f"耗时 {search_time:.3f}s"
                )

                return response
            else:
                search_time = time.time() - start_time
                self.update_stats(False, search_time)

                return create_error_response(
                    query,
                    serper_result.error_message or "搜索失败",
                    search_time,
                    self.name,
                    "search_failed",
                )

        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"❌ Scholar 搜索失败: {e}")
            self.update_stats(False, search_time)

            return create_error_response(query, str(e), search_time, self.name, "search_exception")

    async def validate_query(self, query: SearchQuery) -> bool:
        """验证查询参数"""
        if not query.text or len(query.text.strip()) == 0:
            return False

        if len(query.text) > 500:
            logger.warning("查询文本过长,截断到500字符")
            query.text = query.text[:500]

        return True

    def get_capabilities(self) -> SearchCapabilities:
        """获取工具能力描述"""
        return SearchCapabilities(
            name=self.name,
            version="1.0.0",
            description="Google Scholar 学术论文搜索工具,基于 Serper API",
            category="academic_search",
            # 支持的搜索类型
            supported_search_types=[SearchType.ACADEMIC, SearchType.FULLTEXT],
            # 能力特征
            max_results=20,
            supports_filters=True,
            supports_sorting=False,
            supports_faceting=False,
            supports_pagination=True,
            # 性能特征
            avg_response_time=2.0,
            max_concurrent_requests=10,
            rate_limit_per_minute=100,
            # 专业领域能力
            domain_expertise=[
                "academic_research",
                "computer_science",
                "medicine",
                "physics",
                "chemistry",
                "engineering",
                "law",
                "business",
            ],
            language_support=["en", "zh", "fr", "de", "es", "ja"],
            geographic_coverage=["global"],
            # 高级特性
            ai_powered=False,
            real_time=True,
            streaming_support=False,
            caching_capable=True,
        )

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            if not self.initialized or not self.serper_manager:
                return {
                    "status": "not_initialized",
                    "tool_name": self.name,
                    "timestamp": datetime.now().isoformat(),
                }

            # 获取 Serper 统计
            serper_stats = self.serper_manager.get_statistics()

            return {
                "status": "healthy",
                "tool_name": self.name,
                "initialized": self.initialized,
                "serper_statistics": serper_stats,
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

    def _convert_to_documents(
        self, results: list[dict[str, Any]], query: SearchQuery
    ) -> list[SearchDocument]:
        """转换搜索结果为文档格式"""
        documents = []

        for i, result in enumerate(results):
            # 构建元数据
            metadata = {
                "source": "google_scholar",
                "type": result.get("type", "scholar"),
                "authors": result.get("authors", []),
                "year": result.get("year"),
                "publication": result.get("publication"),
                "citation": result.get("citation"),
                "rank": i + 1,
            }

            # 构建文档
            document = SearchDocument(
                id=f"scholar_{hash(result.get('link', ''))}_{i}",
                title=result.get("title", ""),
                content=result.get("snippet", ""),
                url=result.get("link"),
                snippet=result.get("snippet", ""),
                relevance_score=1.0 - (i * 0.05),
                confidence=0.85,
                language=self._detect_language(result),
                content_type="text/html",
                metadata=metadata,
            )

            documents.append(document)

        return documents

    def _detect_language(self, result: dict[str, Any]) -> str:
        """检测文档语言"""
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        text = title + " " + snippet

        if any("\u4e00" <= char <= "\u9fff" for char in text):
            return "zh"
        else:
            return "en"


# 注册到工具注册表
from ..registry.tool_registry import register_to_registry


@register_to_registry(category="academic_search", auto_init=False)
def create_google_scholar_tool(config: Optional[dict[str, Any]] = None) -> GoogleScholarSearchTool:
    """创建 Google Scholar 搜索工具的工厂函数"""
    return GoogleScholarSearchTool(config)


# 便捷函数
async def create_scholar_search(
    serper_api_key: Optional[str] = None, enable_cache: bool = True
) -> GoogleScholarSearchTool:
    """
    创建并初始化 Google Scholar 搜索工具

    Args:
        serper_api_key: Serper API 密钥 (如果为None,从环境变量读取)
        enable_cache: 是否启用缓存

    Returns:
        GoogleScholarSearchTool: 初始化完成的工具
    """
    import os

    if serper_api_key is None:
        serper_api_key = os.getenv("SERPER_API_KEY", "")

    config = {"serper_api_key": serper_api_key, "enable_cache": enable_cache}

    tool = GoogleScholarSearchTool(config)
    await tool.initialize()

    return tool


if __name__ == "__main__":
    # 测试代码
    async def test_scholar_tool():
        """测试 Scholar 搜索工具"""
        print("🧪 测试 Google Scholar 搜索工具")
        print()

        tool = await create_scholar_search()

        # 测试搜索
        query = SearchQuery(text="deep learning", max_results=5)

        response = await tool.search(query)

        print(f"查询: {response.query.text}")
        print(f"成功: {response.success}")
        print(f"找到结果: {response.total_found}")
        print(f"搜索时间: {response.search_time:.2f}s")

        if response.documents:
            print(f"\n前 {len(response.documents)} 个结果:")
            for i, doc in enumerate(response.documents[:3], 1):
                print(f"\n{i}. {doc.title}")
                print(f"   作者: {doc.metadata.get('authors', [])}")
                print(f"   年份: {doc.metadata.get('year', 'N/A')}")
                print(f"   链接: {doc.url}")

        # 健康检查
        print("\n" + "=" * 60)
        print("健康检查")
        print("=" * 60)
        health = await tool.health_check()
        for key, value in health.items():
            print(f"{key}: {value}")

    asyncio.run(test_scholar_tool())
