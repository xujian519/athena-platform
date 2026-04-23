#!/usr/bin/env python3
from __future__ import annotations
"""
Athena智能搜索选择器 - 工具评估器
Athena Search Selector - Tool Evaluator

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0

负责评估和推荐搜索工具。
"""

import logging

from ...registry.tool_registry import ToolRegistry, ToolStatus
from ...standards.base_search_tool import QueryComplexity, SearchCapabilities, SearchType
from .types import (
    DomainType,
    QueryAnalysis,
    QueryIntent,
    SelectionStrategy,
    ToolRecommendation,
)

logger = logging.getLogger(__name__)


class ToolEvaluator:
    """工具评估器 - 负责评估和推荐搜索工具"""

    def __init__(self, registry: ToolRegistry):
        """初始化工具评估器

        Args:
            registry: 工具注册中心
        """
        self.registry = registry

    async def get_candidate_tools(
        self, analysis: QueryAnalysis, exclude_tools: list[str]
    ) -> list[str]:
        """获取候选工具"""
        candidate_tools = []

        for tool_name, metadata in self.registry.metadata.items():
            # 排除指定工具
            if tool_name in exclude_tools:
                continue

            # 检查工具状态
            if metadata.status != ToolStatus.ACTIVE:
                continue

            # 检查工具能力
            capabilities = metadata.capabilities
            if not capabilities:
                continue

            # 基本能力匹配
            if self._basic_capability_match(analysis, capabilities):
                candidate_tools.append(tool_name)

        return candidate_tools

    def _basic_capability_match(
        self, analysis: QueryAnalysis, capabilities: SearchCapabilities
    ) -> bool:
        """基本能力匹配检查"""
        # 搜索类型匹配
        search_type_map = {
            DomainType.PATENT: [SearchType.PATENT],
            DomainType.ACADEMIC: [SearchType.ACADEMIC],
            DomainType.GENERAL: [SearchType.WEB, SearchType.FULLTEXT, SearchType.SEMANTIC],
        }

        if analysis.primary_domain in search_type_map:
            required_types = search_type_map[analysis.primary_domain]
            if not any(
                t in capabilities.supported_search_types for t in required_types
            ):
                return False

        # 复杂度匹配
        if analysis.complexity == QueryComplexity.ANALYTICAL and not capabilities.ai_powered:
            return False

        return True

    async def evaluate_tool(
        self, tool_name: str, analysis: QueryAnalysis, strategy: SelectionStrategy
    ) -> ToolRecommendation:
        """评估工具匹配度"""
        metadata = self.registry.get_tool_metadata(tool_name)
        capabilities = metadata.capabilities if metadata else None
        if not capabilities:
            return self._create_empty_recommendation(tool_name)

        # 多维度评分
        scores = {
            "domain_match": self._calculate_domain_match_score(
                analysis, capabilities, strategy
            ),
            "intent_match": self._calculate_intent_match_score(
                analysis, capabilities, strategy
            ),
            "performance": self._calculate_performance_score(tool_name, strategy),
            "capability": self._calculate_capability_score(
                analysis, capabilities, strategy
            ),
            "availability": self._calculate_availability_score(tool_name, strategy),
        }

        # 计算总分
        total_score = sum(
            scores[key] * getattr(strategy, f"{key}_weight") for key in scores.keys()
        )

        # 生成推理说明
        reasoning = self._generate_reasoning(analysis, capabilities, scores)

        # 性能预测
        expected_response_time = self._predict_response_time(tool_name, analysis)
        expected_success_rate = self._predict_success_rate(tool_name, analysis)
        expected_quality_score = self._predict_quality_score(tool_name, analysis)

        # 确定推荐类型
        recommendation_type = self._determine_recommendation_type(total_score, analysis)
        priority = self._calculate_priority(total_score, analysis)

        return ToolRecommendation(
            tool_name=tool_name,
            match_score=total_score,
            confidence=min(total_score + 0.1, 1.0),  # 加上少量置信度缓冲
            reasoning=reasoning,
            expected_response_time=expected_response_time,
            expected_success_rate=expected_success_rate,
            expected_quality_score=expected_quality_score,
            recommendation_type=recommendation_type,
            priority=priority,
        )

    # 评分计算方法
    def _calculate_domain_match_score(
        self, analysis: QueryAnalysis, capabilities: SearchCapabilities, strategy: SelectionStrategy
    ) -> float:
        """计算领域匹配分数"""
        score = 0.0

        # 主要领域匹配
        for domain in capabilities.domain_expertise:
            if domain.lower() in analysis.normalized_text:
                score += 0.5

        # 工具类别匹配
        category_map = {
            DomainType.PATENT: ["patent", "ip"],
            DomainType.ACADEMIC: ["academic", "research"],
            DomainType.BUSINESS: ["business", "commercial"],
            DomainType.TECHNOLOGY: ["technology", "technical"],
            DomainType.LEGAL: ["legal", "law"],
        }

        if analysis.primary_domain in category_map:
            target_categories = category_map[analysis.primary_domain]
            if any(
                cat in capabilities.category.lower() for cat in target_categories
            ):
                score += 0.5

        return min(score, 1.0)

    def _calculate_intent_match_score(
        self, analysis: QueryAnalysis, capabilities: SearchCapabilities, strategy: SelectionStrategy
    ) -> float:
        """计算意图匹配分数"""
        score = 0.0

        # 意图到工具能力映射
        intent_capability_map = {
            QueryIntent.PATENT: {"ai_powered": True, "real_time": False},
            QueryIntent.RESEARCH: {"ai_powered": True, "caching_capable": True},
            QueryIntent.ANALYSIS: {"ai_powered": True, "streaming_support": True},
            QueryIntent.INFORMATIONAL: {"max_results": 10},
            QueryIntent.COMPARISON: {"supports_sorting": True, "supports_faceting": True},
        }

        if analysis.primary_intent in intent_capability_map:
            required_caps = intent_capability_map[analysis.primary_intent]

            for cap, expected in required_caps.items():
                if hasattr(capabilities, cap) and getattr(capabilities, cap) == expected:
                    score += 0.2

        return min(score, 1.0)

    def _calculate_performance_score(self, tool_name: str, strategy: SelectionStrategy) -> float:
        """计算性能分数"""
        metadata = self.registry.get_tool_metadata(tool_name)
        if not metadata:
            return 0.0

        # 基于历史性能
        success_rate = metadata.get_success_rate()
        health_score = metadata.health_score

        # 响应时间评分 (越快越好)
        response_time_score = max(0, 1 - (metadata.avg_response_time / 5.0))

        return success_rate * 0.4 + health_score * 0.3 + response_time_score * 0.3

    def _calculate_capability_score(
        self, analysis: QueryAnalysis, capabilities: SearchCapabilities, strategy: SelectionStrategy
    ) -> float:
        """计算能力分数"""
        score = 0.0

        # 基础能力
        if analysis.complexity == QueryComplexity.ANALYTICAL and capabilities.ai_powered:
            score += 0.3

        if analysis.time_sensitivity and capabilities.real_time:
            score += 0.2

        # 假设有max_results属性
        if hasattr(analysis, "max_results") and hasattr(capabilities, "max_results"):
            if analysis.max_results <= capabilities.max_results:
                score += 0.2

        if analysis.precision_requirement > 0.8 and capabilities.supports_filters:
            score += 0.2

        if (
            analysis.completeness_requirement > 0.8
            and capabilities.supports_faceting
        ):
            score += 0.1

        return min(score, 1.0)

    def _calculate_availability_score(self, tool_name: str, strategy: SelectionStrategy) -> float:
        """计算可用性分数"""
        metadata = self.registry.get_tool_metadata(tool_name)
        if not metadata:
            return 0.0

        # 基于状态和健康评分
        if metadata.status == ToolStatus.ACTIVE:
            return metadata.health_score
        elif metadata.status == ToolStatus.ERROR:
            return 0.0
        else:
            return 0.5

    # 辅助方法
    def _create_empty_recommendation(self, tool_name: str) -> ToolRecommendation:
        """创建空推荐"""
        return ToolRecommendation(
            tool_name=tool_name,
            match_score=0.0,
            confidence=0.0,
            reasoning=["工具信息不可用"],
            expected_response_time=5.0,
            expected_success_rate=0.5,
            expected_quality_score=0.5,
            recommendation_type="complementary",
            priority=1,
        )

    def _generate_reasoning(
        self, analysis: QueryAnalysis, capabilities: SearchCapabilities, scores: dict[str, float]
    ) -> list[str]:
        """生成推荐推理说明"""
        reasoning = []

        if scores["domain_match"] > 0.7:
            reasoning.append(f"在{analysis.primary_domain.value}领域有专业匹配")

        if scores["intent_match"] > 0.7:
            reasoning.append(f"工具能力与{analysis.primary_intent.value}意图高度匹配")

        if scores["performance"] > 0.7:
            reasoning.append("历史性能表现优秀")

        if scores["capability"] > 0.7:
            reasoning.append("技术能力满足查询需求")

        if scores["availability"] > 0.7:
            reasoning.append("当前状态良好,可用性高")

        return reasoning or ["基本匹配查询需求"]

    def _predict_response_time(self, tool_name: str, analysis: QueryAnalysis) -> float:
        """预测响应时间"""
        metadata = self.registry.get_tool_metadata(tool_name)
        if metadata:
            base_time = metadata.avg_response_time

            # 根据查询复杂度调整
            if analysis.complexity == QueryComplexity.ANALYTICAL:
                base_time *= 1.5
            elif analysis.complexity == QueryComplexity.COMPLEX:
                base_time *= 1.2

            return base_time
        return 2.0  # 默认预测时间

    def _predict_success_rate(self, tool_name: str, analysis: QueryAnalysis) -> float:
        """预测成功率"""
        metadata = self.registry.get_tool_metadata(tool_name)
        if metadata:
            base_rate = metadata.get_success_rate()

            # 根据领域匹配调整
            if (
                metadata.capabilities
                and analysis.primary_domain.value in metadata.capabilities.domain_expertise
            ):
                base_rate += 0.1

            return min(base_rate, 1.0)
        return 0.7  # 默认预测成功率

    def _predict_quality_score(self, tool_name: str, analysis: QueryAnalysis) -> float:
        """预测质量分数"""
        metadata = self.registry.get_tool_metadata(tool_name)
        if metadata:
            # 基于健康评分和成功率
            return (metadata.health_score + metadata.get_success_rate()) / 2
        return 0.6  # 默认预测质量

    def _determine_recommendation_type(self, score: float, analysis: QueryAnalysis) -> str:
        """确定推荐类型"""
        if score > 0.8:
            return "primary"
        elif score > 0.6:
            return "fallback"
        else:
            return "complementary"

    def _calculate_priority(self, score: float, analysis: QueryAnalysis) -> int:
        """计算优先级"""
        if score > 0.8:
            return 5
        elif score > 0.6:
            return 4
        elif score > 0.4:
            return 3
        elif score > 0.2:
            return 2
        else:
            return 1
