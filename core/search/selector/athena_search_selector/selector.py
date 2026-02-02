#!/usr/bin/env python3
"""
Athena智能搜索选择器 - 主选择器
Athena Search Selector - Main Selector

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0

智能搜索选择器的主类，协调各个组件完成工具选择任务。
"""

import logging
from datetime import datetime
from typing import Any, Optional

from ...registry.tool_registry import ToolRegistry, get_tool_registry
from ...standards.base_search_tool import QueryComplexity
from .types import (
    QueryAnalysis,
    ToolRecommendation,
    SelectionStrategy,
    QueryIntent,
    DomainType,
)
from .query_analyzer import QueryAnalyzer
from .tool_evaluator import ToolEvaluator

logger = logging.getLogger(__name__)


class AthenaSearchSelector:
    """
    Athena智能搜索选择器

    核心能力:
    1. 深度查询分析 - 理解用户意图和需求
    2. 智能工具匹配 - 选择最佳工具组合
    3. 性能学习优化 - 基于历史数据持续优化
    4. 策略动态调整 - 根据效果调整选择策略
    """

    def __init__(
        self, registry: ToolRegistry | None = None, config: Optional[dict[str, Any] | None = None
    ):
        """
        初始化智能选择器

        Args:
            registry: 工具注册中心
            config: 选择器配置
        """
        self.registry = registry or get_tool_registry()
        self.config = config or {}

        # 选择策略
        self.strategies = self._initialize_strategies()
        self.current_strategy = self.strategies.get("balanced", self.strategies["default"])

        # 初始化组件
        self.query_analyzer = QueryAnalyzer()
        self.tool_evaluator = ToolEvaluator(self.registry)

        # 学习数据
        self.query_history: list[dict[str, Any]] = []
        self.tool_performance: dict[str, dict[str, Any]] = {}
        self.selection_feedback: list[dict[str, Any]] = []

        # 统计信息
        self.stats = {
            "total_selections": 0,
            "successful_selections": 0,
            "avg_selection_time": 0.0,
            "most_selected_tools": {},
            "strategy_performance": {},
        }

        # 初始化时间
        self._start_time = datetime.now()

        logger.info("✅ 初始化Athena智能搜索选择器")

    def _initialize_strategies(self) -> dict[str, SelectionStrategy]:
        """初始化选择策略"""
        from .types import SelectionStrategy

        return {
            "default": SelectionStrategy(name="default", description="默认平衡策略"),
            "speed_optimized": SelectionStrategy(
                name="speed_optimized",
                description="速度优先策略",
                performance_weight=0.4,
                domain_match_weight=0.2,
                max_tools_per_query=1,
            ),
            "quality_optimized": SelectionStrategy(
                name="quality_optimized",
                description="质量优先策略",
                domain_match_weight=0.4,
                intent_match_weight=0.3,
                max_tools_per_query=5,
                require_fallback=True,
            ),
            "cost_optimized": SelectionStrategy(
                name="cost_optimized",
                description="成本优先策略",
                max_tools_per_query=1,
                min_confidence_threshold=0.5,
            ),
            "comprehensive": SelectionStrategy(
                name="comprehensive",
                description="全面覆盖策略",
                max_tools_per_query=4,
                require_fallback=True,
                min_confidence_threshold=0.4,
            ),
        }

    async def analyze_query(self, query_text: str) -> QueryAnalysis:
        """
        分析查询

        Args:
            query_text: 查询文本

        Returns:
            QueryAnalysis: 查询分析结果
        """
        return await self.query_analyzer.analyze(query_text)

    async def select_tools(
        self,
        analysis: QueryAnalysis,
        strategy: SelectionStrategy | None = None,
        max_tools: int | None = None,
        exclude_tools: Optional[list["key"] = None,
    ) -> list[ToolRecommendation]:
        """
        选择最佳搜索工具

        Args:
            analysis: 查询分析结果
            strategy: 选择策略
            max_tools: 最大工具数量
            exclude_tools: 排除的工具

        Returns:
            list[ToolRecommendation]: 工具推荐列表
        """
        try:
            start_time = datetime.now()

            # 使用指定策略或默认策略
            strategy = strategy or self.current_strategy
            max_tools = max_tools or strategy.max_tools_per_query
            exclude_tools = exclude_tools or []

            # 获取候选工具
            candidate_tools = await self.tool_evaluator.get_candidate_tools(
                analysis, exclude_tools
            )

            if not candidate_tools:
                logger.warning("⚠️ 没有找到合适的候选工具")
                return []

            # 评估每个候选工具
            recommendations = []
            for tool_name in candidate_tools:
                recommendation = await self.tool_evaluator.evaluate_tool(
                    tool_name, analysis, strategy
                )
                if recommendation.confidence >= strategy.min_confidence_threshold:
                    recommendations.append(recommendation)

            # 按分数排序
            recommendations.sort(key=lambda x: x.match_score, reverse=True)

            # 应用策略限制
            final_recommendations = self._apply_strategy_limits(
                recommendations, strategy, max_tools
            )

            # 添加fallback工具(如果需要)
            if strategy.require_fallback and len(final_recommendations) < max_tools:
                fallback_tools = await self._get_fallback_tools(
                    analysis, exclude_tools, final_recommendations
                )
                final_recommendations.extend(fallback_tools)

            # 记录选择历史
            self._record_selection(analysis, final_recommendations, strategy)

            # 更新统计
            selection_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(len(final_recommendations), selection_time)

            logger.info(
                f"✅ 选择了 {len(final_recommendations)} 个工具,耗时 {selection_time:.3f}s"
            )

            return final_recommendations

        except Exception as e:
            logger.error(f"❌ 工具选择失败: {e}")
            return []

    def _apply_strategy_limits(
        self,
        recommendations: list[ToolRecommendation],
        strategy: SelectionStrategy,
        max_tools: int,
    ) -> list[ToolRecommendation]:
        """应用策略限制"""
        # 限制数量
        limited_recommendations = recommendations[:max_tools]

        # 确保包含主要推荐
        primary_recommendations = []
            r for r in limited_recommendations if r.recommendation_type == "primary"
        ]
        if not primary_recommendations and limited_recommendations:
            limited_recommendations[0].recommendation_type = "primary"

        return limited_recommendations

    async def _get_fallback_tools(
        self,
        analysis: QueryAnalysis,
        exclude_tools: list[str],
        primary_recommendations: list[ToolRecommendation],
    ) -> list[ToolRecommendation]:
        """获取fallback工具"""
        # 这里可以实现更复杂的fallback逻辑
        return []

    def _record_selection(
        self,
        analysis: QueryAnalysis,
        recommendations: list[ToolRecommendation],
        strategy: SelectionStrategy,
    ):
        """记录选择历史"""
        self.query_history.append(
            {
                "timestamp": datetime.now(),
                "analysis": analysis,
                "recommendations": recommendations,
                "strategy": strategy.name,
            }
        )

        # 限制历史记录数量
        if len(self.query_history) > 1000:
            self.query_history = self.query_history[-500:]

    def _update_stats(self, num_recommendations: int, selection_time: float):
        """更新统计信息"""
        self.stats["total_selections"] += 1
        if num_recommendations > 0:
            self.stats["successful_selections"] += 1

        # 更新平均选择时间
        total = self.stats["total_selections"]
        current_avg = self.stats["avg_selection_time"]
        self.stats["avg_selection_time"] = (
            current_avg * (total - 1) + selection_time
        ) / total

        # 更新最常用工具统计
        for recommendation in recommendations[:3]:  # 只统计前3个
            tool_name = recommendation.tool_name
            self.stats["most_selected_tools"][tool_name] = (
                self.stats["most_selected_tools"].get(tool_name, 0) + 1
            )

    # 公共接口
    async def search_and_select(
        self, query_text: str, **kwargs
    ) -> tuple[QueryAnalysis, list[ToolRecommendation]]:
        """分析查询并选择工具 - 便捷接口"""
        analysis = await self.analyze_query(query_text)
        recommendations = await self.select_tools(analysis, **kwargs)
        return analysis, recommendations

    def get_stats(self) -> dict[str, Any]:
        """获取选择器统计信息"""
        return {
            **self.stats,
            "query_history_count": len(self.query_history),
            "available_strategies": list(self.strategies.keys()),
            "current_strategy": self.current_strategy.name,
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
        }

    def set_strategy(self, strategy_name: str) -> bool:
        """设置选择策略"""
        if strategy_name in self.strategies:
            self.current_strategy = self.strategies[strategy_name]
            logger.info(f"✅ 已切换到策略: {strategy_name}")
            return True
        else:
            logger.warning(f"⚠️ 未找到策略: {strategy_name}")
            return False

    def add_feedback(
        self, query_text: str, selected_tools: list[str], success: bool, satisfaction: float
    ):
        """添加选择反馈"""
        feedback = {
            "timestamp": datetime.now(),
            "query_text": query_text,
            "selected_tools": selected_tools,
            "success": success,
            "satisfaction": satisfaction,
        }

        self.selection_feedback.append(feedback)

        # 限制反馈记录数量
        if len(self.selection_feedback) > 1000:
            self.selection_feedback = self.selection_feedback[-500:]

        logger.info(f"📊 已记录选择反馈: 成功={success}, 满意度={satisfaction}")
