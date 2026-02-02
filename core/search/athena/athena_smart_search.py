#!/usr/bin/env python3
"""
分散式智能搜索架构 - Athena智能搜索系统
Decentralized Intelligent Search Architecture - Athena Smart Search System

统一整合所有组件,提供完整的智能搜索能力

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


from ..coordinator.lightweight_coordinator import (
    LightweightCoordinator,
    MetricType,
    get_lightweight_coordinator,
)
from ..registry.tool_registry import ToolRegistry, ToolStatus, get_tool_registry
from ..selector.athena_search_selector import (
    AthenaSearchSelector,
    QueryAnalysis,
    ToolRecommendation,
    get_search_selector,  # type: ignore
)
from ..standards.base_search_tool import (
    BaseSearchTool,
    SearchDocument,
    SearchQuery,
    SearchResponse,
    SearchType,
)

logger = logging.getLogger(__name__)


@dataclass
class SearchRequest:
    """智能搜索请求"""

    query_text: str
    search_type: SearchType = SearchType.HYBRID
    max_results: int = 10
    max_tools: int = 3
    timeout: float = 30.0

    # 高级选项
    prefer_tools: list[str] | None = None
    exclude_tools: list[str] | None = None
    require_fallback: bool = True
    enable_result_fusion: bool = True
    strategy: str | None = None

    # 上下文信息
    user_id: str | None = None
    session_id: str | None = None
    conversation_context: dict[str, Any] | None = None


@dataclass
class SearchResult:
    """智能搜索结果"""

    success: bool
    query: str
    tool_recommendations: list[ToolRecommendation]
    responses: list[SearchResponse]
    fused_documents: list[SearchDocument]

    # 性能指标
    total_time: float
    analysis_time: float
    selection_time: float
    search_time: float
    fusion_time: float

    # 统计信息
    tools_used: list[str]
    total_documents: int
    unique_documents: int

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SearchSession:
    """搜索会话"""

    session_id: str
    user_id: str
    start_time: datetime = field(default_factory=datetime.now)
    search_history: list[SearchResult] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def add_search(self, result: SearchResult):
        """添加搜索结果到会话"""
        self.search_history.append(result)


class AthenaSmartSearch:
    """
    Athena智能搜索系统

    核心功能:
    1. 智能工具选择 - 基于查询自动选择最佳工具
    2. 并行搜索执行 - 同时使用多个工具搜索
    3. 结果智能融合 - 合并和排序多工具结果
    4. 学习优化 - 基于反馈持续优化
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        selector: AthenaSearchSelector | None = None,
        coordinator: LightweightCoordinator | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        初始化Athena智能搜索系统

        Args:
            registry: 工具注册中心
            selector: 智能选择器
            coordinator: 轻量协调器
            config: 系统配置
        """
        self.registry = registry or get_tool_registry()
        self.selector: AthenaSearchSelector = selector or get_search_selector()
        self.coordinator = coordinator or get_lightweight_coordinator()
        self.config = config or {}

        # 会话管理
        self.sessions: dict[str, SearchSession] = {}

        # 统计信息
        self.stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "popular_queries": {},
            "most_used_tools": {},
            "session_count": 0,
        }

        # 初始化时间
        self._start_time = datetime.now()
        self.initialized = False

    async def initialize(self) -> bool:
        """
        初始化智能搜索系统

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("🚀 初始化Athena智能搜索系统...")

            # 初始化各个组件
            if not self.registry.initialized:
                await self.registry.initialize()

            # 初始化协调器
            await self.coordinator.initialize()

            # 设置事件监听
            self._setup_event_handlers()

            self.initialized = True
            logger.info("✅ Athena智能搜索系统初始化完成")

            return True

        except Exception as e:
            logger.error(f"❌ Athena智能搜索系统初始化失败: {e}")
            return False

    async def search(self, request: SearchRequest) -> SearchResult:
        """
        执行智能搜索

        Args:
            request: 搜索请求

        Returns:
            SearchResult: 搜索结果
        """
        start_time = time.time()

        try:
            if not self.initialized:
                raise RuntimeError("系统未初始化")

            logger.info(f"🔍 开始智能搜索: {request.query_text}")

            # 第一步:查询分析
            analysis_start = time.time()
            analysis: QueryAnalysis = await self.selector.analyze_query(request.query_text)
            analysis_time = time.time() - analysis_start

            # 第二步:工具选择
            selection_start = time.time()

            # 设置选择策略
            if request.strategy:
                self.selector.set_strategy(request.strategy)

            # 获取工具推荐
            recommendations = await self.selector.select_tools(
                analysis, max_tools=request.max_tools, exclude_tools=request.exclude_tools
            )

            # 应用用户偏好
            if request.prefer_tools:
                recommendations = self._apply_tool_preferences(
                    recommendations, request.prefer_tools
                )

            selection_time = time.time() - selection_start

            # 第三步:并行搜索
            search_start = time.time()
            responses = await self._execute_parallel_search(analysis, recommendations, request)
            search_time = time.time() - search_start

            # 第四步:结果融合(如果启用)
            fusion_start = time.time()
            fused_documents = []
            if request.enable_result_fusion and len(responses) > 1:
                fused_documents = await self._fuse_search_results(responses, analysis, request)
            else:
                # 直接合并所有文档
                fused_documents = self._merge_all_documents(responses)
            fusion_time = time.time() - fusion_start

            # 创建搜索结果
            total_time = time.time() - start_time
            result = SearchResult(
                success=len(fused_documents) > 0 or any(r.success for r in responses),
                query=request.query_text,
                tool_recommendations=recommendations,
                responses=responses,
                fused_documents=fused_documents,
                total_time=total_time,
                analysis_time=analysis_time,
                selection_time=selection_time,
                search_time=search_time,
                fusion_time=fusion_time,
                tools_used=[r.tool_name for r in responses if r.success],
                total_documents=sum(len(r.documents) for r in responses),
                unique_documents=len(fused_documents),
                metadata={
                    "analysis": analysis,
                    "request_id": f"search_{int(time.time() * 1000)}",
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # 更新统计
            self._update_stats(request, result)

            # 记录到会话
            if request.session_id:
                self._add_to_session(request.session_id, result, request.user_id)

            # 记录指标
            await self.coordinator.add_metric(
                tool_name="athena_smart_search",
                metric_type=MetricType.PERFORMANCE,
                metric_name="search_duration",
                value=total_time,
                unit="seconds",
                tags={"success": str(result.success), "tools_count": str(len(recommendations))},
            )

            logger.info(
                f"✅ 智能搜索完成: 找到 {len(fused_documents)} 个文档,耗时 {total_time:.3f}s"
            )

            return result

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ 智能搜索失败: {e}")

            # 创建错误结果
            error_result = SearchResult(
                success=False,
                query=request.query_text,
                tool_recommendations=[],
                responses=[],
                fused_documents=[],
                total_time=total_time,
                analysis_time=0.0,
                selection_time=0.0,
                search_time=0.0,
                fusion_time=0.0,
                tools_used=[],
                total_documents=0,
                unique_documents=0,
                metadata={"error": str(e)},
            )

            self._update_stats(request, error_result)
            return error_result

    async def search_simple(
        self, query_text: str, max_results: int = 10, search_type: SearchType = SearchType.HYBRID
    ) -> SearchResult:
        """
        简化搜索接口

        Args:
            query_text: 查询文本
            max_results: 最大结果数
            search_type: 搜索类型

        Returns:
            SearchResult: 搜索结果
        """
        request = SearchRequest(
            query_text=query_text, max_results=max_results, search_type=search_type
        )
        return await self.search(request)

    async def _execute_parallel_search(
        self,
        analysis: QueryAnalysis,
        recommendations: list[ToolRecommendation],
        request: SearchRequest,
    ) -> list[SearchResponse]:
        """执行并行搜索"""
        if not recommendations:
            return []

        # 构建搜索查询
        search_query = SearchQuery(
            text=request.query_text,
            search_type=request.search_type,
            max_results=request.max_results,
            timeout=request.timeout,
            user_id=request.user_id,
            session_id=request.session_id,
        )

        # 创建搜索任务
        search_tasks = []
        for recommendation in recommendations[: request.max_tools]:
            tool = self.registry.get_tool(recommendation.tool_name)
            if tool and tool.initialized:
                task = self._search_single_tool(tool, search_query, recommendation)
                search_tasks.append(task)

        # 并行执行搜索
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*search_tasks, return_exceptions=True), timeout=request.timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ 搜索超时: {request.timeout}秒")
            responses = []
            for task in search_tasks:
                if not task.done():
                    task.cancel()
                    responses.append("搜索超时")

        # 处理结果
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"❌ 工具 {recommendations[i].tool_name} 搜索异常: {response}")
                # 创建错误响应
                error_response = SearchResponse(
                    success=False,
                    query=search_query,
                    tool_name=recommendations[i].tool_name,
                    error_message=str(response),
                    error_type="search_exception",
                )
                processed_responses.append(error_response)
            else:
                processed_responses.append(response)

        return processed_responses

    async def _search_single_tool(
        self, tool: BaseSearchTool, query: SearchQuery, recommendation: ToolRecommendation
    ) -> SearchResponse:
        """单个工具搜索"""
        try:
            # 记录工具调用
            tool_start = time.time()

            # 执行搜索
            response = await tool.search(query)

            # 记录性能指标
            tool_time = time.time() - tool_start
            await self.coordinator.add_metric(
                tool_name=tool.name,
                metric_type=MetricType.PERFORMANCE,
                metric_name="search_duration",
                value=tool_time,
                unit="seconds",
                tags={"success": str(response.success), "documents": str(len(response.documents))},
            )

            # 添加推荐信息到响应
            response.metadata["recommendation"] = recommendation

            return response

        except Exception as e:
            logger.error(f"❌ 工具 {tool.name} 搜索失败: {e}")
            return SearchResponse(
                success=False,
                query=query,
                tool_name=tool.name,
                error_message=str(e),
                error_type="search_exception",
            )

    async def _fuse_search_results(
        self, responses: list[SearchResponse], analysis: QueryAnalysis, request: SearchRequest
    ) -> list[SearchDocument]:
        """融合搜索结果"""
        if not responses:
            return []

        try:
            # 收集所有文档
            all_documents = []
            for response in responses:
                if response.success:
                    # 添加工具权重信息
                    for doc in response.documents:
                        doc.metadata["source_tool"] = response.tool_name
                        doc.metadata["tool_confidence"] = response.metadata.get(
                            "recommendation", {}
                        ).get("confidence", 0.5)
                    all_documents.extend(response.documents)

            if not all_documents:
                return []

            # 去重(基于URL或ID)
            unique_documents = self._deduplicate_documents(all_documents)

            # 重新评分
            scored_documents = await self._rescore_documents(unique_documents, analysis, responses)

            # 排序和限制数量
            scored_documents.sort(key=lambda x: x.relevance_score, reverse=True)
            final_documents = scored_documents[: request.max_results]

            return final_documents

        except Exception as e:
            logger.error(f"❌ 结果融合失败: {e}")
            # 降级到简单合并
            return self._merge_all_documents(responses)[: request.max_results]

    def _merge_all_documents(self, responses: list[SearchResponse]) -> list[SearchDocument]:
        """简单合并所有文档"""
        all_documents = []
        for response in responses:
            if response.success:
                all_documents.extend(response.documents)
        return all_documents

    def _deduplicate_documents(self, documents: list[SearchDocument]) -> list[SearchDocument]:
        """去重文档"""
        seen_ids = set()
        seen_urls = set()
        unique_documents = []

        for doc in documents:
            # 使用ID或URL去重
            doc_key = doc.id or doc.url

            if doc_key:
                if doc.id and doc.id not in seen_ids:
                    seen_ids.add(doc.id)
                    unique_documents.append(doc)
                elif doc.url and doc.url not in seen_urls:
                    seen_urls.add(doc.url)
                    unique_documents.append(doc)
            else:
                # 没有ID或URL的文档,基于内容哈希去重
                content_hash = hash(doc.content[:200])  # 使用前200字符
                if content_hash not in seen_ids:
                    seen_ids.add(content_hash)
                    unique_documents.append(doc)

        return unique_documents

    async def _rescore_documents(
        self,
        documents: list[SearchDocument],
        analysis: QueryAnalysis,
        responses: list[SearchResponse],
    ) -> list[SearchDocument]:
        """重新评分文档"""
        try:
            for doc in documents:
                # 基础分数
                base_score = doc.relevance_score

                # 工具置信度加成
                tool_confidence = doc.metadata.get("tool_confidence", 0.5)
                tool_bonus = tool_confidence * 0.2

                # 新鲜度加成(如果有时间信息)
                freshness_bonus = 0.0
                if doc.publication_date:
                    days_old = (datetime.now() - doc.publication_date).days
                    if days_old <= 30:
                        freshness_bonus = 0.1
                    elif days_old <= 365:
                        freshness_bonus = 0.05

                # 质量加成
                quality_bonus = doc.source_quality * 0.1

                # 计算新分数
                new_score = base_score + tool_bonus + freshness_bonus + quality_bonus
                doc.relevance_score = min(new_score, 1.0)

            return documents

        except Exception as e:
            logger.error(f"❌ 重新评分失败: {e}")
            return documents

    def _apply_tool_preferences(
        self, recommendations: list[ToolRecommendation], preferred_tools: list[str]
    ) -> list[ToolRecommendation]:
        """应用工具偏好"""
        if not preferred_tools:
            return recommendations

        # 分离偏好工具和其他工具
        preferred = [r for r in recommendations if r.tool_name in preferred_tools]
        others = [r for r in recommendations if r.tool_name not in preferred_tools]

        # 偏好工具优先
        return preferred + others

    def _setup_event_handlers(self):
        """设置事件处理器"""
        # 监听工具注册事件
        self.registry.on_tool_registered(self._on_tool_registered)
        self.registry.on_tool_unregistered(self._on_tool_unregistered)

        # 监听告警事件
        self.coordinator.register_event_handler("tool_health_warning", self._on_tool_health_warning)

    async def _on_tool_registered(self, tool_name: str, metadata: Any):
        """工具注册事件处理"""
        logger.info(f"📝 工具已注册: {tool_name}")
        await self.coordinator.emit_event(
            "tool_registered", {"tool_name": tool_name, "metadata": metadata}
        )

    async def _on_tool_unregistered(self, tool_name: str):
        """工具注销事件处理"""
        logger.info(f"📝 工具已注销: {tool_name}")
        await self.coordinator.emit_event("tool_unregistered", {"tool_name": tool_name})

    async def _on_tool_health_warning(self, data: dict[str, Any]):
        """工具健康警告事件处理"""
        logger.warning(f"⚠️ 工具健康警告: {data}")

    # === 会话管理 ===

    def create_session(self, session_id: str, user_id: str | None = None) -> SearchSession:
        """创建搜索会话"""
        session = SearchSession(session_id=session_id, user_id=user_id)
        self.sessions[session_id] = session
        self.stats["session_count"] += 1
        return session

    def get_session(self, session_id: str) -> SearchSession | None:
        """获取搜索会话"""
        return self.sessions.get(session_id)

    def _add_to_session(self, session_id: str, result: SearchResult, user_id: str | None = None):
        """添加搜索结果到会话"""
        if session_id not in self.sessions:
            self.create_session(session_id, user_id)

        self.sessions[session_id].add_search(result)

    # === 统计和监控 ===

    def _update_stats(self, request: SearchRequest, result: SearchResult):
        """更新统计信息"""
        self.stats["total_searches"] += 1

        if result.success:
            self.stats["successful_searches"] += 1

        # 更新平均时间
        total = self.stats["total_searches"]
        current_avg = self.stats["avg_time"]
        self.stats["avg_time"] = (current_avg * (total - 1) + result.total_time) / total

        # 更新流行查询
        query = request.query_text.lower()
        self.stats["popular_queries"][query] = self.stats["popular_queries"].get(query, 0) + 1

        # 更新工具使用统计
        for tool_name in result.tools_used:
            self.stats["most_used_tools"][tool_name] = (
                self.stats["most_used_tools"].get(tool_name, 0) + 1
            )

    def get_stats(self) -> dict[str, Any]:
        """获取系统统计信息"""
        # 更新会话统计
        active_sessions = len(self.sessions)
        total_searches_in_sessions = sum(len(s.search_history) for s in self.sessions.values())

        return {
            **self.stats,
            "active_sessions": active_sessions,
            "total_searches_in_sessions": total_searches_in_sessions,
            "registered_tools": len(self.registry.tools),
            "available_tools": len(self.registry.list_tools(status_filter=ToolStatus.ACTIVE)),
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
            "timestamp": datetime.now().isoformat(),
        }

    async def add_search_feedback(
        self,
        query_text: str,
        selected_tools: list[str],
        success: bool,
        satisfaction: float,
        session_id: str | None = None,
    ):
        """添加搜索反馈"""
        # 向选择器添加反馈
        self.selector.add_feedback(query_text, selected_tools, success, satisfaction)

        # 记录到协调器
        await self.coordinator.add_metric(
            tool_name="athena_smart_search",
            metric_type=MetricType.USAGE,
            metric_name="user_satisfaction",
            value=satisfaction,
            unit="score",
            tags={"success": str(success), "session_id": session_id or "none"},
        )

        logger.info(f"📊 已记录搜索反馈: 成功={success}, 满意度={satisfaction}")

    # === 系统管理 ===

    async def health_check(self) -> dict[str, Any]:
        """系统健康检查"""
        try:
            # 检查各组件状态
            registry_health = await self.registry.health_check_all()

            # 测试搜索功能
            test_result = await self.search_simple("health check", max_results=1)

            # 检查协调器状态
            coordinator_health = self.coordinator.get_stats()

            return {
                "status": "healthy" if test_result.success else "degraded",
                "athena_smart_search": {
                    "initialized": self.initialized,
                    "uptime": (datetime.now() - self._start_time).total_seconds(),
                    "test_search_success": test_result.success,
                },
                "registry_health": registry_health,
                "coordinator_health": coordinator_health,
                "stats": self.get_stats(),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    async def shutdown(self):
        """关闭智能搜索系统"""
        try:
            logger.info("🔄 关闭Athena智能搜索系统...")

            # 关闭协调器
            await self.coordinator.shutdown()

            # 关闭注册中心
            await self.registry.shutdown()

            self.initialized = False
            logger.info("✅ Athena智能搜索系统已关闭")

        except Exception as e:
            logger.error(f"❌ Athena智能搜索系统关闭失败: {e}")


# 全局智能搜索实例
_athena_smart_search: AthenaSmartSearch | None = None


def get_athena_smart_search() -> AthenaSmartSearch:
    """获取全局Athena智能搜索实例"""
    global _athena_smart_search
    if _athena_smart_search is None:
        _athena_smart_search = AthenaSmartSearch()
    return _athena_smart_search


async def initialize_athena_smart_search(
    config: dict[str, Any] | None = None,
) -> AthenaSmartSearch:
    """初始化全局Athena智能搜索系统"""
    smart_search = get_athena_smart_search()
    await smart_search.initialize()
    return smart_search


if __name__ == "__main__":
    # 示例用法
    logger.info("🧠 Athena智能搜索系统")
    logger.info("   智能工具选择")
    logger.info("   并行搜索执行")
    logger.info("   结果智能融合")
    logger.info("   学习优化机制")
    print()
    logger.info("💡 使用方法:")
    logger.info("   athena = AthenaSmartSearch()")
    logger.info("   await athena.initialize()")
    logger.info("   result = await athena.search_simple('人工智能专利', max_results=10)")
    logger.info("   logger.info(f'找到 {len(result.fused_documents)} 个相关文档')")
