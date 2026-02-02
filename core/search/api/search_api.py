#!/usr/bin/env python3
"""
搜索API
Search API

提供统一的搜索API接口,支持多种搜索模式和参数

作者: Athena AI系统
创建时间: 2025-12-04
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .. import AthenaSearchEngine
from ..types import SearchResult, SearchType

logger = logging.getLogger(__name__)


@dataclass
class SearchRequest:
    """搜索请求"""

    query: str
    sources: list[str] | None = None
    search_type: SearchType = SearchType.HYBRID
    limit: int = 10
    filters: dict[str, Any] | None = None
    sort_by: str | None = None
    include_metadata: bool = True


@dataclass
class SearchResponse:
    """搜索响应"""

    query: str
    results: list[SearchResult]
    total_found: int
    search_time: float
    sources_used: list[str]
    metadata: dict[str, Any]
class SearchAPI:
    """搜索API类"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化搜索API

        Args:
            config: 搜索配置
        """
        self.config = config or {}
        self.search_engine: AthenaSearchEngine | None = None
        self.initialized = False

        # 搜索统计 - 使用显式类型注解
        self.search_stats: dict[str, Any] = {
            "total_searches": 0,
            "total_results": 0,
            "average_search_time": 0.0,
            "most_common_queries": {},
            "last_search_time": None,
        }

    async def initialize(self):
        """初始化搜索API"""
        if self.initialized:
            return

        logger.info("🚀 初始化搜索API...")

        try:
            # 初始化搜索引擎
            self.search_engine = AthenaSearchEngine(self.config)
            await self.search_engine.initialize()

            self.initialized = True
            logger.info("✅ 搜索API初始化完成")

        except Exception as e:
            logger.error(f"❌ 搜索API初始化失败: {e}")
            raise

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        执行搜索

        Args:
            request: 搜索请求

        Returns:
            搜索响应
        """
        if not self.initialized:
            await self.initialize()

        start_time = datetime.now()

        logger.info(f"🔍 搜索API请求: {request.query}")
        logger.info(f"   来源: {request.sources}")
        logger.info(f"   类型: {request.search_type.value}")
        logger.info(f"   限制: {request.limit}")

        try:
            # 执行搜索
            if self.search_engine is None:
                raise RuntimeError("搜索引擎未初始化")

            search_results = await self.search_engine.search(
                query=request.query,
                sources=request.sources,
                search_type=request.search_type,
                limit=request.limit,
            )

            # 处理过滤器
            filtered_results = self._apply_filters(search_results, request.filters)

            # 处理排序
            sorted_results = self._apply_sorting(filtered_results, request.sort_by)

            # 构建响应
            response = self._build_response(request, sorted_results, start_time)

            # 更新统计
            self._update_statistics(request, response)

            return response

        except Exception as e:
            logger.error(f"❌ 搜索API失败: {e}")
            raise

    async def quick_search(
        self, query: str, sources: list[str] | None = None, limit: int = 10
    ) -> SearchResponse:
        """
        快速搜索(简化接口)

        Args:
            query: 搜索查询
            sources: 搜索来源
            limit: 结果数量

        Returns:
            搜索响应
        """
        request = SearchRequest(
            query=query, sources=sources, limit=limit, search_type=SearchType.HYBRID
        )
        return await self.search(request)

    async def internal_search(
        self, query: str, search_type: SearchType = SearchType.SEMANTIC, limit: int = 10
    ) -> SearchResponse:
        """
        内部搜索

        Args:
            query: 搜索查询
            search_type: 搜索类型
            limit: 结果数量

        Returns:
            搜索响应
        """
        request = SearchRequest(
            query=query, sources=["internal"], search_type=search_type, limit=limit
        )
        return await self.search(request)

    async def external_search(
        self, query: str, engines: list[str] | None = None, limit: int = 10
    ) -> SearchResponse:
        """
        外部搜索

        Args:
            query: 搜索查询
            engines: 搜索引擎列表
            limit: 结果数量

        Returns:
            搜索响应
        """
        request = SearchRequest(query=query, sources=["external"], limit=limit)
        return await self.search(request)

    def _apply_filters(
        self, results: list[SearchResult], filters: dict[str, Any]
    ) -> list[SearchResult]:
        """应用过滤器"""
        if not filters:
            return results

        filtered_results = []

        for result in results:
            if self._result_matches_filters(result, filters):
                filtered_results.append(result)

        return filtered_results

    def _result_matches_filters(self, result: SearchResult, filters: dict[str, Any]) -> bool:
        """检查结果是否匹配过滤器"""
        # 实现具体的过滤逻辑
        # 这里可以基于文档类型、来源、时间等进行过滤
        return True

    def _apply_sorting(
        self, results: list[SearchResult], sort_by: str,
    ) -> list[SearchResult]:
        """应用排序"""
        if not sort_by:
            return results

        # 实现具体的排序逻辑
        # 这里可以按相关性、时间、来源等进行排序
        return results

    def _build_response(
        self, request: SearchRequest, results: list[SearchResult], start_time: datetime
    ) -> SearchResponse:
        """构建搜索响应"""
        search_time = (datetime.now() - start_time).total_seconds()
        total_found = sum(len(result.documents) for result in results)
        sources_used = request.sources or ["internal", "external"]

        # 合并所有文档
        all_documents = []
        for result in results:
            all_documents.extend(result.documents)

        return SearchResponse(
            query=request.query,
            results=results,
            total_found=total_found,
            search_time=search_time,
            sources_used=sources_used,
            metadata={
                "limit": request.limit,
                "search_type": request.search_type.value,
                "filters": request.filters,
                "sort_by": request.sort_by,
            },
        )

    def _update_statistics(self, request: SearchRequest, response: SearchResponse) -> None:
        """更新搜索统计"""
        # 使用类型忽略来处理多类型字典的更新操作
        total_searches = int(self.search_stats.get("total_searches", 0))
        self.search_stats["total_searches"] = total_searches + 1

        total_results = int(self.search_stats.get("total_results", 0))
        self.search_stats["total_results"] = total_results + response.total_found

        avg_time = float(self.search_stats.get("average_search_time", 0.0))
        self.search_stats["average_search_time"] = (
            avg_time * (total_searches - 1) + response.search_time
        ) / (total_searches if total_searches > 0 else 1)
        self.search_stats["last_search_time"] = datetime.now().isoformat()

        # 更新常用查询
        query = request.query.lower()
        most_common: dict[str, int] = self.search_stats.get("most_common_queries", {})
        if query in most_common:
            most_common[query] += 1
        else:
            most_common[query] = 1
        self.search_stats["most_common_queries"] = most_common

    async def get_suggestions(self, query: str, limit: int = 5) -> list[str]:
        """
        获取搜索建议

        Args:
            query: 部分查询
            limit: 建议数量

        Returns:
            建议列表
        """
        # 这里可以实现基于历史查询的搜索建议
        # 现在返回简单的建议
        common_queries = list(self.search_stats["most_common_queries"].keys())

        suggestions = []
        for common_query in common_queries:
            if query in common_query:
                suggestions.append(common_query)
                if len(suggestions) >= limit:
                    break

        return suggestions

    async def get_statistics(self) -> dict[str, Any]:
        """获取搜索统计信息"""
        engine_status = None
        if self.search_engine is not None:
            engine_status = await self.search_engine.get_status()

        return {
            "search_stats": self.search_stats,
            "engine_status": engine_status,
            "api_status": "initialized" if self.initialized else "not_initialized",
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            if not self.initialized:
                return {"status": "not_initialized", "timestamp": datetime.now().isoformat()}

            # 检查搜索引擎状态
            if self.search_engine is None:
                return {
                    "status": "error",
                    "error": "搜索引擎未初始化",
                    "timestamp": datetime.now().isoformat(),
                }

            engine_status = await self.search_engine.get_status()

            return {
                "status": "healthy",
                "api_initialized": self.initialized,
                "engine_status": engine_status,
                "search_stats": self.search_stats,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    async def shutdown(self):
        """关闭搜索API"""
        logger.info("🔄 关闭搜索API...")

        if self.search_engine:
            await self.search_engine.shutdown()

        self.initialized = False
        logger.info("✅ 搜索API已关闭")


# 导出便捷函数
__all__ = ["SearchAPI", "SearchRequest", "SearchResponse"]
