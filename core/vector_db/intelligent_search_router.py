#!/usr/bin/env python3
from __future__ import annotations
"""
智能搜索路由器
Intelligent Search Router

根据查询特征、场景需求和系统状态,智能选择最优的搜索策略
作者: Athena AI Team
创建时间: 2026-01-09
版本: v1.0.0
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.vector_db.enhanced_vector_search_with_reranker import (
    EnhancedSearchResult,
    SearchMode,
    get_enhanced_searcher,
)
from core.vector_db.llm_enhanced_vector_search import (
    LLMEnhancedSearchConfig,
    LLMEnhancedSearchResult,
    LLMOperation,
    get_llm_enhanced_searcher,
)

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """查询复杂度"""

    SIMPLE = "simple"  # 简单查询 (关键词)
    MEDIUM = "medium"  # 中等查询 (短语)
    COMPLEX = "complex"  # 复杂查询 (长句/问题)
    VERY_COMPLEX = "very_complex"  # 非常复杂 (多问/推理)


class SearchScenario(Enum):
    """搜索场景"""

    QUICK_PREVIEW = "quick_preview"  # 快速预览
    PRECISE_RETRIEVAL = "precise_retrieval"  # 精确检索
    ANSWER_GENERATION = "answer_generation"  # 答案生成
    CONVERSATION = "conversation"  # 对话交互
    BATCH_PROCESSING = "batch_processing"  # 批量处理


class RouteDecision(Enum):
    """路由决策"""

    VECTOR_ONLY = "vector_only"  # 仅向量搜索
    RERANK_TOP_K = "rerank_top_k"  # Rerank Top-K
    LLM_REWRITE = "llm_rewrite"  # LLM查询重写
    LLM_FULL = "llm_full"  # LLM完整流程


@dataclass
class RoutingConfig:
    """路由配置"""

    # 复杂度阈值
    simple_query_max_length: int = 30
    medium_query_max_length: int = 80

    # 性能阈值
    max_llm_latency: float = 3.0  # 最大LLM延迟 (秒)
    max_total_latency: float = 5.0  # 最大总延迟 (秒)

    # 场景权重
    precision_weight: float = 0.6  # 精度权重
    speed_weight: float = 0.4  # 速度权重

    # LLM使用条件
    llm_required_keywords: list[str] = field(
        default_factory=lambda: [
            "解释",
            "分析",
            "对比",
            "原因",
            "如何",
            "怎么",
            "为什么",
            "explain",
            "analyze",
            "compare",
            "why",
            "how",
        ]
    )

    llm_required_patterns: list[str] = field(
        default_factory=lambda: [
            r"[??]",  # 问题
            r"怎么.*办",  # 怎么办
            r"如何.*做",  # 如何做
            r"为什么",  # 为什么
            r"请.*解释",  # 请解释
        ]
    )


@dataclass
class RoutingAnalysis:
    """路由分析结果"""

    query: str
    complexity: QueryComplexity
    scenario: SearchScenario
    suggested_decision: RouteDecision
    confidence: float
    reasoning: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


class IntelligentSearchRouter:
    """智能搜索路由器"""

    def __init__(self, config: RoutingConfig = None):
        """
        初始化智能路由器

        Args:
            config: 路由配置
        """
        self.config = config or RoutingConfig()
        self.name = "智能搜索路由器"
        self.version = "1.0.0"

        logger.info(f"🧭 初始化{self.name}...")

        # 搜索器实例 (延迟加载)
        self.enhanced_searcher = None
        self.llm_searcher = None

        # 路由统计
        self.routing_stats = {
            "total_routes": 0,
            "decision_usage": {decision.value: 0 for decision in RouteDecision},
            "complexity_distribution": {complexity.value: 0 for complexity in QueryComplexity},
            "scenario_distribution": {scenario.value: 0 for scenario in SearchScenario},
        }

        # 性能监控
        self.performance_history = []

        logger.info(f"✅ {self.name}初始化完成")

    async def _ensure_searchers(self):
        """确保搜索器已加载"""
        if self.enhanced_searcher is None:
            self.enhanced_searcher = await get_enhanced_searcher()

        if self.llm_searcher is None:
            # 使用默认配置
            llm_config = LLMEnhancedSearchConfig(
                enable_query_rewrite=True, enable_answer_generation=True, use_reranker=True
            )
            self.llm_searcher = await get_llm_enhanced_searcher(llm_config)

    def analyze_query(self, query: str, context: Optional[dict[str, Any]] = None) -> RoutingAnalysis:
        """
        分析查询特征

        Args:
            query: 查询文本
            context: 上下文信息

        Returns:
            路由分析结果
        """
        context = context or {}
        reasoning = []

        # 1. 分析查询复杂度
        complexity = self._analyze_complexity(query)
        reasoning.append(f"查询复杂度: {complexity.value}")

        # 2. 识别搜索场景
        scenario = self._identify_scenario(query, context)
        reasoning.append(f"搜索场景: {scenario.value}")

        # 3. 做出路由决策
        decision = self._make_decision(complexity, scenario, query, context)
        reasoning.append(f"路由决策: {decision.value}")

        # 4. 计算置信度
        confidence = self._calculate_confidence(complexity, scenario, decision)

        return RoutingAnalysis(
            query=query,
            complexity=complexity,
            scenario=scenario,
            suggested_decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "query_length": len(query),
                "has_question_mark": "?" in query or "?" in query,
                "context": context,
            },
        )

    def _analyze_complexity(self, query: str) -> QueryComplexity:
        """分析查询复杂度"""
        query_length = len(query)
        word_count = len(query.split())

        # 检查特殊模式
        has_multiple_questions = query.count("?") + query.count("?") > 1
        has_conjunctions = any(kw in query for kw in ["和", "与", "或", "以及", "并且", "同时"])
        has_comparison = any(kw in query for kw in ["对比", "比较", "区别", "差异"])

        # 判断复杂度
        if word_count <= 3 or query_length <= self.config.simple_query_max_length:
            return QueryComplexity.SIMPLE
        elif (
            query_length <= self.config.medium_query_max_length
            and not has_multiple_questions
            and not has_comparison
        ):
            return QueryComplexity.MEDIUM
        elif (
            query_length > self.config.medium_query_max_length
            or has_multiple_questions
            or has_conjunctions
        ):
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.VERY_COMPLEX

    def _identify_scenario(self, query: str, context: dict[str, Any]) -> SearchScenario:
        """识别搜索场景"""
        # 从上下文获取场景提示
        scenario_hint = context.get("scenario")

        if scenario_hint:
            try:
                return SearchScenario(scenario_hint)
            except ValueError:
                pass

        # 根据查询特征判断
        if context.get("conversation_mode") or context.get("requires_answer"):
            return SearchScenario.ANSWER_GENERATION

        if context.get("batch_mode"):
            return SearchScenario.BATCH_PROCESSING

        if any(kw in query for kw in self.config.llm_required_keywords):
            return SearchScenario.ANSWER_GENERATION

        if any(re.search(pattern, query) for pattern in self.config.llm_required_patterns):
            return SearchScenario.ANSWER_GENERATION

        # 默认场景
        complexity = self._analyze_complexity(query)
        if complexity == QueryComplexity.SIMPLE:
            return SearchScenario.QUICK_PREVIEW
        else:
            return SearchScenario.PRECISE_RETRIEVAL

    def _make_decision(
        self,
        complexity: QueryComplexity,
        scenario: SearchScenario,
        query: str,
        context: dict[str, Any],    ) -> RouteDecision:
        """做出路由决策"""
        # 场景优先级
        if scenario == SearchScenario.QUICK_PREVIEW:
            return RouteDecision.VECTOR_ONLY

        if scenario == SearchScenario.BATCH_PROCESSING:
            # 批量处理使用Rerank,避免LLM开销
            return RouteDecision.RERANK_TOP_K

        if scenario == SearchScenario.ANSWER_GENERATION:
            # 答案生成场景
            if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
                return RouteDecision.LLM_FULL
            else:
                return RouteDecision.LLM_REWRITE

        if scenario == SearchScenario.PRECISE_RETRIEVAL:
            # 精确检索场景
            if complexity == QueryComplexity.SIMPLE:
                return RouteDecision.VECTOR_ONLY
            else:
                return RouteDecision.RERANK_TOP_K

        if scenario == SearchScenario.CONVERSATION:
            # 对话场景使用LLM
            return RouteDecision.LLM_FULL

        # 默认决策
        if complexity in [QueryComplexity.SIMPLE, QueryComplexity.MEDIUM]:
            return RouteDecision.RERANK_TOP_K
        else:
            return RouteDecision.LLM_REWRITE

    def _calculate_confidence(
        self, complexity: QueryComplexity, scenario: SearchScenario, decision: RouteDecision
    ) -> float:
        """计算决策置信度"""
        # 简单场景的决策更确定
        if complexity == QueryComplexity.SIMPLE:
            base_confidence = 0.95
        elif complexity == QueryComplexity.MEDIUM:
            base_confidence = 0.85
        else:
            base_confidence = 0.75

        # 场景和决策的匹配度
        if scenario == SearchScenario.QUICK_PREVIEW and decision == RouteDecision.VECTOR_ONLY:
            return min(base_confidence + 0.1, 1.0)

        if scenario == SearchScenario.ANSWER_GENERATION and decision in [
            RouteDecision.LLM_REWRITE,
            RouteDecision.LLM_FULL,
        ]:
            return min(base_confidence + 0.1, 1.0)

        return base_confidence

    async def route_search(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
        force_decision: RouteDecision | None = None,
    ) -> tuple[RoutingAnalysis, Any]:
        """
        执行智能路由搜索

        Args:
            query: 查询文本
            context: 上下文信息
            force_decision: 强制使用指定的路由决策

        Returns:
            (路由分析, 搜索结果)
        """
        await self._ensure_searchers()

        # 分析查询
        analysis = self.analyze_query(query, context)

        # 使用强制决策或建议决策
        decision = force_decision or analysis.suggested_decision

        logger.info(f"🧭 路由决策: {decision.value}")
        logger.info(f"   查询: {query[:50]}...")
        logger.info(f"   复杂度: {analysis.complexity.value}")
        logger.info(f"   场景: {analysis.scenario.value}")
        logger.info(f"   置信度: {analysis.confidence:.2f}")

        # 更新统计
        self.routing_stats["total_routes"] += 1
        self.routing_stats["decision_usage"][decision.value] += 1
        self.routing_stats["complexity_distribution"][analysis.complexity.value] += 1
        self.routing_stats["scenario_distribution"][analysis.scenario.value] += 1

        # 执行搜索
        start_time = time.time()

        try:
            if decision == RouteDecision.VECTOR_ONLY:
                result = await self._execute_vector_only(query, context)
            elif decision == RouteDecision.RERANK_TOP_K:
                result = await self._execute_rerank(query, context)
            elif decision == RouteDecision.LLM_REWRITE:
                result = await self._execute_llm_rewrite(query, context)
            else:  # LLM_FULL
                result = await self._execute_llm_full(query, context)

            # 记录性能
            total_time = time.time() - start_time
            self.performance_history.append(
                {
                    "decision": decision.value,
                    "complexity": analysis.complexity.value,
                    "time": total_time,
                    "timestamp": time.time(),
                }
            )

            # 限制历史记录大小
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]

            return analysis, result

        except Exception as e:
            logger.error(f"❌ 搜索执行失败: {e}")
            # 降级到向量搜索
            fallback_result = await self._execute_vector_only(query, context)
            return analysis, fallback_result

    async def _execute_vector_only(
        self, query: str, context: dict[str, Any]
    ) -> EnhancedSearchResult:
        """执行仅向量搜索"""
        top_k = context.get("top_k", 10)
        return await self.enhanced_searcher.search(
            query=query, mode=SearchMode.VECTOR_ONLY, top_k=top_k
        )

    async def _execute_rerank(self, query: str, context: dict[str, Any]) -> EnhancedSearchResult:
        """执行Rerank搜索"""
        top_k = context.get("top_k", 10)
        return await self.enhanced_searcher.search(
            query=query, mode=SearchMode.RERANK_TOP_K, top_k=top_k
        )

    async def _execute_llm_rewrite(
        self, query: str, context: dict[str, Any]
    ) -> LLMEnhancedSearchResult:
        """执行LLM查询重写"""
        operations = [LLMOperation.QUERY_REWRITE]
        top_k = context.get("top_k", 10)

        return await self.llm_searcher.search(query=query, operations=operations, top_k=top_k)

    async def _execute_llm_full(
        self, query: str, context: dict[str, Any]
    ) -> LLMEnhancedSearchResult:
        """执行完整LLM流程"""
        operations = [LLMOperation.QUERY_REWRITE, LLMOperation.ANSWER_GENERATION]
        top_k = context.get("top_k", 10)

        return await self.llm_searcher.search(query=query, operations=operations, top_k=top_k)

    def get_routing_stats(self) -> dict[str, Any]:
        """获取路由统计"""
        # 计算平均性能
        avg_times_by_decision = {}
        if self.performance_history:
            decision_times = {}
            decision_counts = {}

            for record in self.performance_history:
                decision = record["decision"]
                time = record["time"]

                if decision not in decision_times:
                    decision_times[decision] = 0.0
                    decision_counts[decision] = 0

                decision_times[decision] += time
                decision_counts[decision] += 1

            for decision in decision_times:
                avg_times_by_decision[decision] = (
                    decision_times[decision] / decision_counts[decision]
                )

        return {
            "routing_stats": {
                "total_routes": self.routing_stats["total_routes"],
                "decision_usage": self.routing_stats["decision_usage"],
                "complexity_distribution": self.routing_stats["complexity_distribution"],
                "scenario_distribution": self.routing_stats["scenario_distribution"],
            },
            "performance_stats": {
                "avg_times_by_decision": avg_times_by_decision,
                "total_performance_records": len(self.performance_history),
            },
            "config": {
                "simple_query_max_length": self.config.simple_query_max_length,
                "medium_query_max_length": self.config.medium_query_max_length,
                "precision_weight": self.config.precision_weight,
                "speed_weight": self.config.speed_weight,
            },
        }

    def get_routing_report(self) -> str:
        """获取路由报告"""
        stats = self.get_routing_stats()

        report = []
        report.append("=" * 60)
        report.append("🧭 智能路由统计报告")
        report.append("=" * 60)
        report.append("")

        report.append("📊 路由决策分布:")
        for decision, count in stats["routing_stats"]["decision_usage"].items():
            percentage = (
                count / stats["routing_stats"]["total_routes"] * 100
                if stats["routing_stats"]["total_routes"] > 0
                else 0
            )
            report.append(f"   {decision}: {count} ({percentage:.1f}%)")

        report.append("")
        report.append("📈 查询复杂度分布:")
        for complexity, count in stats["routing_stats"]["complexity_distribution"].items():
            percentage = (
                count / stats["routing_stats"]["total_routes"] * 100
                if stats["routing_stats"]["total_routes"] > 0
                else 0
            )
            report.append(f"   {complexity}: {count} ({percentage:.1f}%)")

        report.append("")
        report.append("⏱️ 平均响应时间:")
        for decision, avg_time in stats["performance_stats"]["avg_times_by_decision"].items():
            report.append(f"   {decision}: {avg_time:.2f}秒")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


# 全局单例
_intelligent_router: IntelligentSearchRouter | None = None


def get_intelligent_router(config: RoutingConfig = None) -> IntelligentSearchRouter:
    """获取智能路由器单例"""
    global _intelligent_router

    if _intelligent_router is None:
        _intelligent_router = IntelligentSearchRouter(config)

    return _intelligent_router


# 便捷函数
async def intelligent_search(
    query: str, context: Optional[dict[str, Any]] = None
) -> tuple[RoutingAnalysis, Any]:
    """便捷函数:智能搜索"""
    router = get_intelligent_router()
    return await router.route_search(query, context)
