#!/usr/bin/env python3
from __future__ import annotations
"""
统一搜索服务入口
Unified Search Service Entry Point

Athena平台的统一搜索接口,集成智能路由、Reranker和LLM增强
这是所有搜索请求的推荐入口点

作者: Athena AI Team
创建时间: 2026-01-09
版本: v1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from core.cache.optimized_cache_manager import CacheLevel, get_cache_manager
from core.monitoring.search_performance_monitor import (
    SearchRecord,
    get_performance_monitor,
)
from core.vector_db.enhanced_vector_search_with_reranker import (
    EnhancedSearchResult,
)
from core.vector_db.intelligent_search_router import (
    RouteDecision,
    RoutingAnalysis,
    get_intelligent_router,
)
from core.vector_db.llm_enhanced_vector_search import (
    LLMEnhancedSearchResult,
)

logger = logging.getLogger(__name__)


@dataclass
class SearchRequest:
    """搜索请求"""

    query: str  # 查询文本
    top_k: int = 10  # 返回结果数量
    scenario: str | None = None  # 场景提示
    conversation_mode: bool = False  # 对话模式
    requires_answer: bool = False  # 需要答案
    batch_mode: bool = False  # 批量模式
    force_decision: RouteDecision | None = None  # 强制路由决策

    # 性能选项
    enable_cache: bool = True  # 启用缓存
    max_latency: float | None = None  # 最大延迟限制

    # 调试选项
    debug_mode: bool = False  # 调试模式
    return_analysis: bool = False  # 返回路由分析

    def to_context(self) -> dict[str, Any]:
        """转换为上下文字典"""
        return {
            "top_k": self.top_k,
            "scenario": self.scenario,
            "conversation_mode": self.conversation_mode,
            "requires_answer": self.requires_answer,
            "batch_mode": self.batch_mode,
            "enable_cache": self.enable_cache,
            "max_latency": self.max_latency,
        }


@dataclass
class SearchResponse:
    """搜索响应"""

    success: bool  # 是否成功
    query: str  # 原始查询
    results: list[Any]  # 搜索结果
    total_found: int  # 总结果数
    search_time: float  # 搜索耗时

    # LLM增强信息
    rewritten_query: str | None = None  # 重写后的查询
    generated_answer: str | None = None  # 生成的答案
    query_understanding: dict | None = None  # 查询理解

    # 路由分析
    routing_analysis: RoutingAnalysis | None = None  # 路由分析结果

    # 性能指标
    vector_search_time: float = 0.0
    rerank_time: float = 0.0
    llm_time: float = 0.0

    # 元数据
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class UnifiedSearchService:
    """
    统一搜索服务

    这是Athena平台推荐的搜索入口,提供:
    - 智能路由自动选择最优策略
    - Reranker增强检索精度
    - LLM增强查询理解和答案生成
    - 性能监控和优化
    - 缓存和降级机制
    """

    def __init__(self, enable_monitoring: bool = True, enable_cache: bool = True):
        """
        初始化统一搜索服务

        Args:
            enable_monitoring: 是否启用性能监控
            enable_cache: 是否启用缓存优化
        """
        self.name = "Athena统一搜索服务"
        self.version = "1.0.0"
        self.router = None
        self.enable_monitoring = enable_monitoring
        self.enable_cache = enable_cache
        self.monitor = None
        self.cache_mgr = None

        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "total_response_time": 0.0,
        }

        # 初始化监控器
        if enable_monitoring:
            self.monitor = get_performance_monitor()
            logger.info("✅ 性能监控已启用")

        # 初始化缓存管理器
        if enable_cache:
            self.cache_mgr = get_cache_manager()
            logger.info("✅ 缓存优化已启用")

        logger.info(f"🔍 {self.name}初始化完成")

    async def _ensure_router(self):
        """确保路由器已加载"""
        if self.router is None:
            self.router = get_intelligent_router()
            logger.info("✅ 智能路由器已加载")

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        执行统一搜索

        Args:
            request: 搜索请求

        Returns:
            搜索响应
        """
        start_time = asyncio.get_event_loop().time()

        await self._ensure_router()

        self.stats["total_requests"] += 1

        logger.info(f"🔍 统一搜索请求: {request.query[:50]}...")
        logger.info(f"   Top-K: {request.top_k}")
        logger.info(f"   场景: {request.scenario or '自动'}")

        try:
            # 准备上下文
            context = request.to_context()

            # 如果启用了缓存且有强制决策,尝试从缓存获取
            if (
                request.enable_cache
                and self.enable_cache
                and self.cache_mgr
                and request.force_decision is not None
            ):
                cached_result = await self.cache_mgr.get(
                    query=request.query,
                    mode=request.force_decision.value,
                    top_k=request.top_k,
                    scenario=request.scenario,
                    conversation_mode=request.conversation_mode,
                )

                if cached_result is not None:
                    logger.info("✅ 缓存命中")

                    # 从缓存构建响应
                    elapsed = asyncio.get_event_loop().time() - start_time

                    self.stats["successful_requests"] += 1
                    self.stats["total_response_time"] += elapsed
                    self.stats["avg_response_time"] = (
                        self.stats["total_response_time"] / self.stats["total_requests"]
                    )

                    # 记录缓存命中到监控器
                    if self.enable_monitoring and self.monitor:
                        search_record = SearchRecord(
                            query=request.query,
                            query_length=len(request.query),
                            complexity=cached_result.get("complexity", "unknown"),
                            scenario=cached_result.get("scenario", "unknown"),
                            decision=cached_result.get("decision", "unknown"),
                            confidence=cached_result.get("confidence", 0.0),
                            total_time=elapsed,
                            vector_time=cached_result.get("vector_time", 0.0),
                            rerank_time=cached_result.get("rerank_time", 0.0),
                            llm_time=cached_result.get("llm_time", 0.0),
                            results_count=len(cached_result.get("results", [])),
                            avg_score=cached_result.get("avg_score", 0.0),
                            success=True,
                            cached=True,
                        )
                        self.monitor.record_search(search_record)

                    return SearchResponse(
                        success=True,
                        query=request.query,
                        results=cached_result.get("results", []),
                        total_found=len(cached_result.get("results", [])),
                        search_time=elapsed,
                        rewritten_query=cached_result.get("rewritten_query"),
                        generated_answer=cached_result.get("generated_answer"),
                        query_understanding=cached_result.get("query_understanding"),
                        metadata=cached_result.get("metadata", {}),
                    )

            # 执行智能路由搜索
            routing_analysis, search_result = await self.router.route_search(
                query=request.query, context=context, force_decision=request.force_decision
            )

            # 构建响应
            elapsed = asyncio.get_event_loop().time() - start_time

            # 提取结果
            if isinstance(search_result, LLMEnhancedSearchResult):
                results = (
                    search_result.search_results.results if search_result.search_results else []
                )
                rewritten_query = search_result.rewritten_query
                generated_answer = search_result.generated_answer
                query_understanding = search_result.query_understanding
                llm_time = search_result.llm_operation_time

                vector_time = (
                    search_result.search_results.vector_search_time
                    if search_result.search_results
                    else 0.0
                )
                rerank_time = (
                    search_result.search_results.rerank_time
                    if search_result.search_results
                    else 0.0
                )

            elif isinstance(search_result, EnhancedSearchResult):
                results = search_result.results
                rewritten_query = None
                generated_answer = None
                query_understanding = None
                llm_time = 0.0
                vector_time = search_result.vector_search_time
                rerank_time = search_result.rerank_time
            else:
                results = []
                rewritten_query = None
                generated_answer = None
                query_understanding = None
                llm_time = 0.0
                vector_time = 0.0
                rerank_time = 0.0

            # 构建响应
            response = SearchResponse(
                success=True,
                query=request.query,
                results=results,
                total_found=len(results),
                search_time=elapsed,
                rewritten_query=rewritten_query,
                generated_answer=generated_answer,
                query_understanding=query_understanding,
                routing_analysis=routing_analysis if request.return_analysis else None,
                vector_search_time=vector_time,
                rerank_time=rerank_time,
                llm_time=llm_time,
                metadata={
                    "search_mode": routing_analysis.suggested_decision.value,
                    "complexity": routing_analysis.complexity.value,
                    "scenario": routing_analysis.scenario.value,
                    "confidence": routing_analysis.confidence,
                },
            )

            # 更新统计
            self.stats["successful_requests"] += 1
            self.stats["total_response_time"] += elapsed
            self.stats["avg_response_time"] = (
                self.stats["total_response_time"] / self.stats["total_requests"]
            )

            # 记录到监控器
            if self.enable_monitoring and self.monitor:
                search_record = SearchRecord(
                    query=request.query,
                    query_length=len(request.query),
                    complexity=routing_analysis.complexity.value,
                    scenario=routing_analysis.scenario.value,
                    decision=routing_analysis.suggested_decision.value,
                    confidence=routing_analysis.confidence,
                    total_time=elapsed,
                    vector_time=vector_time,
                    rerank_time=rerank_time,
                    llm_time=llm_time,
                    results_count=len(results),
                    avg_score=response.metadata.get("avg_score", 0.0) if response.metadata else 0.0,
                    success=True,
                    cached=False,
                )
                self.monitor.record_search(search_record)

            # 保存到缓存 (如果启用)
            if request.enable_cache and self.enable_cache and self.cache_mgr:
                cache_data = {
                    "results": results,
                    "rewritten_query": rewritten_query,
                    "generated_answer": generated_answer,
                    "query_understanding": query_understanding,
                    "metadata": response.metadata,
                    "complexity": routing_analysis.complexity.value,
                    "scenario": routing_analysis.scenario.value,
                    "decision": routing_analysis.suggested_decision.value,
                    "confidence": routing_analysis.confidence,
                    "vector_time": vector_time,
                    "rerank_time": rerank_time,
                    "llm_time": llm_time,
                    "avg_score": (
                        response.metadata.get("avg_score", 0.0) if response.metadata else 0.0
                    ),
                }

                await self.cache_mgr.set(
                    query=request.query,
                    value=cache_data,
                    mode=routing_analysis.suggested_decision.value,
                    top_k=request.top_k,
                    level=CacheLevel.L1_MEMORY,
                    **{
                        "scenario": request.scenario,
                        "conversation_mode": request.conversation_mode,
                    },
                )
                logger.debug("💾 结果已缓存")

            logger.info(f"✅ 搜索完成: {len(results)} 个结果,耗时 {elapsed:.2f}秒")

            return response

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")

            # 更新统计
            self.stats["failed_requests"] += 1

            # 返回错误响应
            return SearchResponse(
                success=False,
                query=request.query,
                results=[],
                total_found=0,
                search_time=asyncio.get_event_loop().time() - start_time,
                metadata={"error": str(e)},
            )

    async def batch_search(
        self, queries: list[str], top_k: int = 10, scenario: str | None = None
    ) -> list[SearchResponse]:
        """
        批量搜索

        Args:
            queries: 查询列表
            top_k: 返回结果数量
            scenario: 场景提示

        Returns:
            搜索响应列表
        """
        logger.info(f"📦 批量搜索: {len(queries)} 个查询")

        # 创建请求
        requests = [
            SearchRequest(query=q, top_k=top_k, scenario=scenario, batch_mode=True) for q in queries
        ]

        # 并发执行搜索
        responses = await asyncio.gather(*[self.search(req) for req in requests])

        logger.info("✅ 批量搜索完成")

        return responses

    def get_service_stats(self) -> dict[str, Any]:
        """获取服务统计"""
        router_stats = self.router.get_routing_stats() if self.router else {}
        monitor_stats = self.monitor.get_summary() if self.monitor else {}

        return {
            "service_stats": {
                "total_requests": self.stats["total_requests"],
                "successful_requests": self.stats["successful_requests"],
                "failed_requests": self.stats["failed_requests"],
                "success_rate": (
                    self.stats["successful_requests"] / self.stats["total_requests"]
                    if self.stats["total_requests"] > 0
                    else 0
                ),
                "avg_response_time": self.stats["avg_response_time"],
            },
            "router_stats": router_stats,
            "monitor_stats": monitor_stats,
        }

    def print_performance_dashboard(self) -> Any:
        """打印性能监控仪表盘"""
        if self.monitor:
            self.monitor.print_dashboard()
        else:
            logger.info("⚠️ 性能监控未启用")

    def get_optimization_suggestions(self) -> list[dict[str, Any]]:
        """获取优化建议"""
        if self.monitor:
            return self.monitor.get_optimization_suggestions()
        return []

    def export_metrics(self, filepath: str | None = None) -> str | None:
        """导出性能指标"""
        if self.monitor:
            return self.monitor.export_metrics(filepath)
        return None


# 全局单例
_unified_search_service: UnifiedSearchService | None = None


async def get_unified_search_service() -> UnifiedSearchService:
    """获取统一搜索服务单例"""
    global _unified_search_service

    if _unified_search_service is None:
        _unified_search_service = UnifiedSearchService()
        await _unified_search_service._ensure_router()

    return _unified_search_service


# 便捷函数
async def unified_search(
    query: str,
    top_k: int = 10,
    scenario: str | None = None,
    requires_answer: bool = False,
    conversation_mode: bool = False,
) -> SearchResponse:
    """
    便捷函数:统一搜索

    这是Athena平台推荐的搜索入口

    Args:
        query: 查询文本
        top_k: 返回结果数量
        scenario: 场景提示 ('quick_preview', 'precise_retrieval', 'answer_generation')
        requires_answer: 是否需要LLM生成答案
        conversation_mode: 是否是对话模式

    Returns:
        搜索响应

    Examples:
        >>> # 简单搜索
        >>> response = await unified_search("专利侵权")
        >>>
        >>> # 需要答案生成
        >>> response = await unified_search(
        ...     "请解释专利权的无效宣告程序",
        ...     requires_answer=True
        ... )
        >>> print(response.generated_answer)
        >>>
        >>> # 对话模式
        >>> response = await unified_search(
        ...     "发明专利的保护期是多久?",
        ...     conversation_mode=True
        ... )
    """
    service = await get_unified_search_service()

    request = SearchRequest(
        query=query,
        top_k=top_k,
        scenario=scenario,
        requires_answer=requires_answer,
        conversation_mode=conversation_mode,
    )

    return await service.search(request)


async def quick_search(query: str, top_k: int = 5) -> list[Any]:
    """
    快速搜索(仅返回结果)

    Args:
        query: 查询文本
        top_k: 返回结果数量

    Returns:
        搜索结果列表
    """
    response = await unified_search(query=query, top_k=top_k, scenario="quick_preview")

    return response.results


async def search_with_answer(query: str, top_k: int = 5) -> dict[str, Any]:
    """
    搜索并生成答案

    Args:
        query: 查询文本
        top_k: 检索结果数量

    Returns:
        包含结果和答案的字典
    """
    response = await unified_search(
        query=query, top_k=top_k, scenario="answer_generation", requires_answer=True
    )

    return {
        "query": response.query,
        "results": response.results,
        "answer": response.generated_answer,
        "rewritten_query": response.rewritten_query,
        "search_time": response.search_time,
    }


# 示例和测试
async def main():
    """主函数示例"""
    print("=" * 80)
    print("🔍 Athena统一搜索服务演示")
    print("=" * 80)
    print()

    service = await get_unified_search_service()

    # 示例1: 简单搜索
    print("1️⃣ 简单搜索")
    request = SearchRequest(query="专利侵权", top_k=5)
    response = await service.search(request)
    print(f"   找到 {len(response.results)} 个结果")
    print(f"   耗时: {response.search_time:.2f}秒")
    if response.results:
        print(f"   Top-1: {response.results[0].content[:60]}...")
    print()

    # 示例2: 需要答案生成
    print("2️⃣ 答案生成搜索")
    request = SearchRequest(query="发明专利的保护期是多久?", top_k=5, requires_answer=True)
    response = await service.search(request)
    print(f"   耗时: {response.search_time:.2f}秒")
    if response.rewritten_query:
        print(f"   重写查询: {response.rewritten_query}")
    if response.generated_answer:
        print(f"   生成答案: {response.generated_answer[:100]}...")
    print()

    # 示例3: 批量搜索
    print("3️⃣ 批量搜索")
    responses = await service.batch_search(queries=["专利权", "商标权", "著作权"], top_k=3)
    for i, resp in enumerate(responses, 1):
        print(f"   查询{i}: {resp.query} -> {len(resp.results)} 个结果")
    print()

    # 显示统计
    print("📊 服务统计:")
    stats = service.get_service_stats()
    print(f"   总请求数: {stats['service_stats']['total_requests']}")
    print(f"   成功率: {stats['service_stats']['success_rate']:.1%}")
    print(f"   平均响应时间: {stats['service_stats']['avg_response_time']:.2f}秒")
    print()

    print("✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
