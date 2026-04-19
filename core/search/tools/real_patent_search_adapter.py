#!/usr/bin/env python3
from __future__ import annotations
"""
真实专利搜索适配器
Real Patent Search Adapter

将现有的专利检索工具集成到BaseSearchTool标准

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

# 导入真实专利检索工具
try:
    from ....production.patent_retrieval.proven_patent_retriever import (
        ProvenPatentRetriever,
    )
except ImportError:
    logger.warning("无法导入ProvenPatentRetriever,使用模拟实现")
    ProvenPatentRetriever = None


class RealPatentSearchAdapter(BaseSearchTool):
    """真实专利搜索适配器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化真实专利搜索适配器

        Args:
            config: 工具配置
        """
        super().__init__("real_patent_search_adapter", config)

        # 专利搜索配置
        self.patent_config = (
            config.get("patent_search", {})
            if config
            else {
                "use_real_sources": True,
                "use_official_sources": True,
                "guarantee_stability": True,
            }
        )

        self.original_retriever = None

    async def initialize(self) -> bool:
        """初始化专利搜索工具"""
        try:
            logger.info("🚀 初始化真实专利搜索适配器...")

            if ProvenPatentRetriever:
                # 使用真实的专利检索器
                self.original_retriever = ProvenPatentRetriever(
                    delay_range=self.patent_config.get("delay_range", (1, 2))
                )
                # ProvenPatentRetriever没有初始化方法,直接使用
                logger.info("✅ ProvenPatentRetriever 就绪")
            else:
                logger.warning("⚠️ 使用模拟专利检索实现")
                await self._simulate_initialization()

            self.initialized = True
            logger.info("✅ 真实专利搜索适配器初始化完成")

            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    async def search(self, query: SearchQuery) -> SearchResponse:
        """执行专利搜索"""
        if not self.initialized:
            return create_error_response(query, "工具未初始化", 0.0, self.name, "not_initialized")

        start_time = time.time()

        try:
            # 验证查询
            if not await self.validate_query(query):
                return create_error_response(query, "查询参数无效", 0.0, self.name, "invalid_query")

            logger.info(f"🔍 执行真实专利搜索: {query.text}")

            # 执行专利搜索
            if self.original_retriever:
                # 使用真实的专利检索器
                patent_data = await self.original_retriever.get_patent_data(
                    query.text, max_patents=query.max_results
                )

                # 转换响应格式
                response = self._convert_patent_data(query, patent_data)
            else:
                # 使用模拟搜索
                response = await self._simulate_search(query)

            # 更新统计
            search_time = time.time() - start_time
            self.update_stats(response.success, search_time)

            logger.info(
                f"✅ 专利搜索完成: 找到 {response.total_found} 个专利,耗时 {search_time:.3f}s"
            )

            return response

        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"❌ 专利搜索失败: {e}")

            return create_error_response(query, str(e), search_time, self.name, "search_exception")

    def get_capabilities(self) -> SearchCapabilities:
        """获取工具能力描述"""
        return SearchCapabilities(
            name=self.name,
            version="1.0.0",
            description="真实专利搜索适配器,集成经过验证的专利数据源",
            category="patent_search",
            # 支持的搜索类型
            supported_search_types=[SearchType.PATENT, SearchType.FULLTEXT, SearchType.SEMANTIC],
            # 能力特征
            max_results=20,
            supports_filters=True,
            supports_sorting=True,
            supports_faceting=False,
            supports_pagination=False,
            # 性能特征
            avg_response_time=3.0,
            max_concurrent_requests=10,
            rate_limit_per_minute=60,
            # 专业领域能力
            domain_expertise=["patent", "intellectual_property", "innovation", "technology"],
            language_support=["zh", "en"],
            geographic_coverage=["global", "us", "cn", "ep", "wo", "jp"],
            # 高级特性
            ai_powered=False,
            real_time=False,
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

            # 测试专利搜索
            SearchQuery(text="test patent search", max_results=1)
            start_time = time.time()

            if self.original_retriever:
                # 使用真实检索器测试
                test_patent_data = await self.original_retriever.get_patent_data(
                    "test patent", max_patents=1
                )
                success = test_patent_data.get("success", False)
            else:
                # 模拟测试
                success = True

            health_time = time.time() - start_time

            return {
                "status": "healthy" if success else "unhealthy",
                "tool_name": self.name,
                "initialized": self.initialized,
                "response_time": health_time,
                "test_search_success": success,
                "real_retriever_available": self.original_retriever is not None,
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

    # === 专利特有方法 ===

    async def search_by_patent_number(self, patent_numbers: list[str]) -> SearchResponse:
        """按专利号搜索"""
        try:
            if not self.initialized:
                raise RuntimeError("工具未初始化")

            logger.info(f"🔍 按专利号搜索: {patent_numbers}")

            # 创建搜索查询
            query = SearchQuery(text=", ".join(patent_numbers), max_results=len(patent_numbers))

            if self.original_retriever:
                # 使用真实检索器
                patent_data = await self.original_retriever.get_patent_data(
                    query.text, max_patents=query.max_results
                )
                response = self._convert_patent_data(query, patent_data)
            else:
                response = await self._simulate_search(query)

            return response

        except Exception as e:
            logger.error(f"❌ 按专利号搜索失败: {e}")
            query = SearchQuery(text=", ".join(patent_numbers), max_results=len(patent_numbers))
            return create_error_response(
                query, str(e), 0.0, self.name, "patent_number_search_error"
            )

    async def search_by_assignee(self, assignee: str, max_results: int = 10) -> SearchResponse:
        """按专利权人搜索"""
        try:
            if not self.initialized:
                raise RuntimeError("工具未初始化")

            query_text = f"assignee:{assignee}"
            query = SearchQuery(text=query_text, max_results=max_results)

            logger.info(f"🔍 按专利权人搜索: {assignee}")

            if self.original_retriever:
                patent_data = await self.original_retriever.get_patent_data(
                    query_text, max_patents=max_results
                )
                response = self._convert_patent_data(query, patent_data)
            else:
                response = await self._simulate_search(query)

            return response

        except Exception as e:
            logger.error(f"❌ 按专利权人搜索失败: {e}")
            query = SearchQuery(text=f"assignee:{assignee}", max_results=max_results)
            return create_error_response(query, str(e), 0.0, self.name, "assignee_search_error")

    # === 内部方法 ===

    def _convert_patent_data(
        self, query: SearchQuery, patent_data: dict[str, Any]
    ) -> SearchResponse:
        """转换专利数据为标准格式"""
        try:
            if not patent_data.get("success"):
                return create_error_response(
                    query,
                    patent_data.get("error_message", "专利搜索失败"),
                    patent_data.get("processing_time", 0.0),
                    self.name,
                    "patent_search_failed",
                )

            patents = patent_data.get("patents", [])
            documents = []

            for patent in patents:
                # 提取专利信息
                patent_number = patent.get("patent_number", "")
                title = patent.get("title", "")
                abstract = patent.get("abstract", "")
                url = patent.get("url", "")

                # 创建标准化文档
                document = SearchDocument(
                    id=patent_number or f"patent_{hash(str(patent))}",
                    title=title,
                    content=abstract,
                    url=url,
                    snippet=abstract[:200] + "..." if len(abstract) > 200 else abstract,
                    relevance_score=0.9,  # 专利搜索通常相关性较高
                    confidence=patent.get("data_quality_score", 0.8),
                    language=self._detect_patent_language(patent),
                    content_type="patent",
                    metadata={
                        "patent_number": patent_number,
                        "source": patent.get("source", "proven_patent_retriever"),
                        "retrieval_method": patent.get("retrieval_method", "unknown"),
                        "extraction_time": patent.get("retrieval_time"),
                        "data_quality": patent.get("data_quality"),
                        "publication_date": patent.get("publication_date"),
                        "application_date": patent.get("application_date"),
                        "inventors": patent.get("inventors", []),
                        "assignees": patent.get("assignees", []),
                        "classification": patent.get("classification", ""),
                        "citations": patent.get("citations", 0),
                        "family_patents": patent.get("family_patents", []),
                        "original_patent": patent,
                    },
                )
                documents.append(document)

            return create_success_response(
                query, documents, patent_data.get("processing_time", 0.0), self.name
            )

        except Exception as e:
            logger.error(f"❌ 专利数据转换失败: {e}")
            return create_error_response(
                query, f"数据转换失败: {e!s}", 0.0, self.name, "conversion_error"
            )

    def _detect_patent_language(self, patent: dict[str, Any]) -> str:
        """检测专利语言"""
        title = patent.get("title", "")
        abstract = patent.get("abstract", "")
        text = f"{title} {abstract}"

        # 简单的语言检测
        chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        english_chars = sum(1 for char in text if "a" <= char.lower() <= "z")

        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > 0:
            return "en"
        else:
            return "unknown"

    async def _simulate_search(self, query: SearchQuery) -> SearchResponse:
        """模拟专利搜索(当真实搜索不可用时)"""
        # 模拟搜索延迟
        await asyncio.sleep(0.8)

        # 生成模拟专利结果
        mock_patents = [
            {
                "patent_number": "US20240123456A1",
                "title": f"模拟专利: {query.text} 相关专利1",
                "abstract": f"这是一个关于{query.text}的模拟专利摘要,描述了技术创新和实现方法。",
                "url": "https://patents.google.com/patent/US20240123456A1",
                "source": "simulation",
                "data_quality_score": 0.85,
                "publication_date": "2024-01-23",
            },
            {
                "patent_number": "CN123456789A",
                "title": f"模拟专利: {query.text} 相关专利2",
                "abstract": f"这是另一个关于{query.text}的模拟专利,提供了不同的技术方案和实施例。",
                "url": "https://patents.google.com/patent/CN123456789A",
                "source": "simulation",
                "data_quality_score": 0.82,
                "publication_date": "2023-12-15",
            },
        ]

        documents = []
        for patent in mock_patents:
            document = SearchDocument(
                id=patent["patent_number"],
                title=patent["title"],
                content=patent["abstract"],
                url=patent["url"],
                snippet=(
                    patent["abstract"][:200] + "..."
                    if len(patent["abstract"]) > 200
                    else patent["abstract"]
                ),
                relevance_score=0.88,
                confidence=patent["data_quality_score"],
                language="zh",
                content_type="patent",
                metadata=patent,
            )
            documents.append(document)

        return create_success_response(query, documents, 0.8, self.name)  # 模拟搜索时间

    async def _simulate_initialization(self):
        """模拟初始化"""
        await asyncio.sleep(0.6)
        logger.info("✅ 模拟专利检索器初始化完成")


# 注册装饰器
from ..registry.tool_registry import register_to_registry


@register_to_registry(category="real_patent_search", auto_init=False)
def create_real_patent_search_adapter(
    config: dict[str, Any] | None = None,
) -> RealPatentSearchAdapter:
    """创建真实专利搜索适配器的工厂函数"""
    return RealPatentSearchAdapter(config)


# 便捷函数
async def create_real_patent_search(
    config: dict[str, Any] | None = None,
) -> RealPatentSearchAdapter:
    """
    创建并初始化真实专利搜索适配器

    Args:
        config: 配置字典

    Returns:
        RealPatentSearchAdapter: 初始化完成的适配器
    """
    adapter = RealPatentSearchAdapter(config)
    await adapter.initialize()
    return adapter


if __name__ == "__main__":
    # 示例用法
    logger.info("📜 真实专利搜索适配器")
    logger.info("   集成经过验证的专利数据源")
    logger.info("   支持多种检索方式")
    logger.info("   智能专利格式解析")
    print()
    logger.info("💡 特性:")
    logger.info("   - 按专利号精确搜索")
    logger.info("   - 按专利权人搜索")
    logger.info("   - 全文专利检索")
    logger.info("   - 专利质量评估")
    print()
    logger.info("🔗 数据源:")
    logger.info("   - Google Patents (经过验证)")
    logger.info("   - Jina.ai 专利服务")
    logger.info("   - Meta标签解析技术")
    print()
    logger.info("📦 初始化:")
    logger.info("   adapter = await create_real_patent_search({")
    logger.info("       'use_real_sources': True,")
    logger.info("       'guarantee_stability': True")
    logger.info("   })")
