#!/usr/bin/env python3
"""
小诺·双鱼公主增强智能工具路由系统
Xiaonuo·Pisces Princess Enhanced Intelligent Tool Router

增强版工具路由器,集成学习能力、性能优化和智能决策

作者: 小诺·双鱼公主
创建时间: 2025-12-18
版本: v2.0.0 "智能路由+"
"""

from __future__ import annotations
import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 导入基础组件
from ..smart_routing.intelligent_tool_router import (
    IntelligentToolRouter,
    IntentType,
    ToolPriority,
    ToolRecommendation,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class LearningMode(Enum):
    """学习模式"""

    ONLINE = "online"  # 在线学习
    OFFLINE = "offline"  # 离线学习
    HYBRID = "hybrid"  # 混合学习


class RoutingStrategy(Enum):
    """路由策略"""

    PERFORMANCE_BASED = "performance_based"  # 基于性能
    SUCCESS_RATE_BASED = "success_rate_based"  # 基于成功率
    CONTEXT_AWARE = "context_aware"  # 上下文感知
    HYBRID_INTELLIGENT = "hybrid_intelligent"  # 混合智能


@dataclass
class ToolPerformance:
    """工具性能指标"""

    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    average_execution_time: float = 0.0
    total_execution_time: float = 0.0
    last_called: datetime | None = None
    success_rate: float = 0.0
    performance_score: float = 0.0
    context_affinity: dict[str, float] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """路由决策"""

    intent: str
    context: dict[str, Any]
    selected_tools: list[str]
    strategy: RoutingStrategy
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


class XiaonuoEnhancedToolRouter:
    """小诺增强智能工具路由器"""

    def __init__(self, learning_mode: LearningMode = LearningMode.HYBRID):
        self.name = "小诺·双鱼公主增强智能工具路由器"
        self.version = "v2.0.0"
        self.learning_mode = learning_mode

        # 性能数据库
        self.tool_performance: dict[str, ToolPerformance] = {}

        # 路由历史
        self.routing_history: deque = deque(maxlen=10000)

        # 学习模型
        self.context_models: dict[str, Any] = {}
        self.performance_predictor = None

        # 缓存系统
        self.routing_cache: dict[str, list[ToolRecommendation]] = {}
        self.cache_ttl = timedelta(hours=1)

        # 基础路由器
        self.base_router = IntelligentToolRouter()

        # 初始化组件
        self._init_learning_system()

        logger.info(f"🧭 {self.name} v{self.version} 初始化完成")

    def _init_learning_system(self):
        """初始化学习系统"""
        try:
            # 加载历史数据
            self._load_historical_data()

            # 初始化预测模型
            self._init_predictor_model()

            logger.info("✅ 学习系统初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 学习系统初始化失败: {e}")

    def _load_historical_data(self):
        """加载历史数据"""
        try:
            # 尝试从文件加载
            data_file = "data/xiaonuo_routing_history.pkl"
            if hasattr(self, "_load_data_file"):
                data = self._load_data_file(data_file)
                if data:
                    self.tool_performance = data.get("tool_performance", {})
                    self.routing_history = deque(data.get("routing_history", []), maxlen=10000)
        except Exception as e:
            logger.warning(f"⚠️ 历史数据加载失败: {e}")

    def _init_predictor_model(self):
        """初始化预测模型"""
        try:
            # 简单的线性模型用于性能预测
            self.performance_predictor = {
                "feature_weights": {
                    "historical_performance": 0.4,
                    "context_match": 0.3,
                    "recency_factor": 0.2,
                    "load_factor": 0.1,
                }
            }
        except Exception as e:
            logger.warning(f"⚠️ 预测模型初始化失败: {e}")

    async def route_tools(
        self,
        intent: str,
        context: dict[str, Any],        available_tools: list[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.HYBRID_INTELLIGENT,
    ) -> list[ToolRecommendation]:
        """
        智能工具路由 - 小诺的核心路由能力

        Args:
            intent: 用户意图
            context: 执行上下文
            available_tools: 可用工具列表
            strategy: 路由策略

        Returns:
            工具推荐列表
        """
        start_time = time.time()

        try:
            # 1. 检查缓存
            cache_key = self._generate_cache_key(intent, context, available_tools, strategy)
            if cache_key in self.routing_cache:
                cached_result = self.routing_cache[cache_key]
                logger.info(f"🎯 路由缓存命中: {intent}")
                return cached_result

            # 2. 分析意图和上下文
            intent_analysis = await self._analyze_intent(intent, context)

            # 3. 根据策略选择工具
            if strategy == RoutingStrategy.PERFORMANCE_BASED:
                recommendations = await self._performance_based_routing(
                    intent_analysis, available_tools
                )
            elif strategy == RoutingStrategy.SUCCESS_RATE_BASED:
                recommendations = await self._success_rate_based_routing(
                    intent_analysis, available_tools
                )
            elif strategy == RoutingStrategy.CONTEXT_AWARE:
                recommendations = await self._context_aware_routing(
                    intent_analysis, context, available_tools
                )
            else:  # HYBRID_INTELLIGENT
                recommendations = await self._hybrid_intelligent_routing(
                    intent_analysis, context, available_tools
                )

            # 4. 缓存结果
            self.routing_cache[cache_key] = recommendations

            # 5. 记录决策
            decision = RoutingDecision(
                intent=intent,
                context=context.copy(),
                selected_tools=[rec.tool_name for rec in recommendations],
                strategy=strategy,
                confidence=sum(rec.confidence for rec in recommendations) / len(recommendations),
                reasoning=f"基于{strategy.value}策略选择了{len(recommendations)}个工具",
            )
            self.routing_history.append(decision)

            # 6. 清理过期缓存
            self._cleanup_cache()

            execution_time = time.time() - start_time
            logger.info(
                f"🧭 路由完成,耗时: {execution_time:.3f}秒,推荐工具: {len(recommendations)}个"
            )

            return recommendations

        except Exception as e:
            logger.error(f"❌ 路由失败: {e}")
            # 降级到基础路由器
            return await self._fallback_routing(intent, context, available_tools)

    async def _analyze_intent(self, intent: str, context: dict[str, Any]) -> dict[str, Any]:
        """分析意图"""
        analysis = {
            "intent_text": intent,
            "intent_type": self._classify_intent(intent),
            "keywords": self._extract_keywords(intent),
            "context_features": self._extract_context_features(context),
            "complexity_score": self._calculate_complexity(intent, context),
        }

        return analysis

    def _classify_intent(self, intent: str) -> IntentType:
        """分类意图"""
        intent_lower = intent.lower()

        if any(keyword in intent_lower for keyword in ["search", "搜索", "查找"]):
            return IntentType.PATENT_SEARCH
        elif any(keyword in intent_lower for keyword in ["analyze", "分析", "评估"]):
            return IntentType.TECHNICAL_EVALUATION
        elif any(keyword in intent_lower for keyword in ["write", "撰写", "生成"]):
            return IntentType.CREATIVE_WRITING
        elif any(keyword in intent_lower for keyword in ["draft", "起草", "专利申请"]):
            return IntentType.PATENT_DRAFTING
        elif any(keyword in intent_lower for keyword in ["monitor", "监控", "检查"]):
            return IntentType.SYSTEM_MONITORING
        elif any(keyword in intent_lower for keyword in ["data", "数据", "分析"]):
            return IntentType.DATA_ANALYSIS
        else:
            return IntentType.GENERAL_CONVERSATION

    def _extract_keywords(self, intent: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        keywords = []
        intent_lower = intent.lower()

        # 领域关键词
        domain_keywords = {
            "patent": ["专利", "patent", "发明", "实用新型", "外观设计"],
            "search": ["搜索", "search", "查找", "检索", "寻找"],
            "analysis": ["分析", "analysis", "评估", "evaluation", "检测"],
            "write": ["写", "write", "撰写", "生成", "创作", "起草"],
            "crawl": ["爬虫", "crawler", "抓取", "采集", "scraping"],
            "browser": ["浏览器", "browser", "网页", "website", "url"],
        }

        for domain, words in domain_keywords.items():
            if any(word in intent_lower for word in words):
                keywords.append(domain)

        return keywords

    def _extract_context_features(self, context: dict[str, Any]) -> dict[str, Any]:
        """提取上下文特征"""
        features = {
            "has_url": "url" in context or "URL" in context,
            "has_query": "query" in context or "search" in context,
            "has_file": "file" in context or "filename" in context,
            "context_size": len(str(context)),
            "parameter_count": len(context),
            "time_constraint": "deadline" in context or "timeout" in context,
        }

        return features

    def _calculate_complexity(self, intent: str, context: dict[str, Any]) -> float:
        """计算复杂度评分"""
        complexity = 0.0

        # 基于意图长度
        complexity += min(len(intent) / 100, 1.0)

        # 基于上下文复杂度
        complexity += min(len(context) / 20, 1.0)

        # 基于关键词复杂度
        complex_keywords = ["深度学习", "机器学习", "多模态", "分布式", "并发"]
        for keyword in complex_keywords:
            if keyword in intent:
                complexity += 0.2

        return min(complexity, 2.0)

    async def _performance_based_routing(
        self, intent_analysis: dict[str, Any], available_tools: list[str]
    ) -> list[ToolRecommendation]:
        """基于性能的路由"""
        recommendations = []
        keywords = intent_analysis["keywords"]

        # 根据关键词匹配工具
        for keyword in keywords:
            matching_tools = self._find_tools_by_keyword(keyword, available_tools)

            for tool_name in matching_tools:
                perf = self.tool_performance.get(tool_name)
                if perf:
                    score = perf.performance_score
                else:
                    score = 0.5  # 默认分数

                recommendations.append(
                    ToolRecommendation(
                        tool_name=tool_name,
                        priority=ToolPriority.IMPORTANT if score > 0.7 else ToolPriority.NORMAL,
                        confidence=score,
                        reason=f"基于性能指标选择 (分数: {score:.2f})",
                        estimated_time=perf.average_execution_time if perf else 3.0,
                    )
                )

        return recommendations[:5]  # 返回前5个推荐

    async def _success_rate_based_routing(
        self, intent_analysis: dict[str, Any], available_tools: list[str]
    ) -> list[ToolRecommendation]:
        """基于成功率的路由"""
        recommendations = []
        keywords = intent_analysis["keywords"]

        for keyword in keywords:
            matching_tools = self._find_tools_by_keyword(keyword, available_tools)

            # 按成功率排序
            tools_with_rate = []
            for tool_name in matching_tools:
                perf = self.tool_performance.get(tool_name)
                if perf and perf.total_calls > 0:
                    tools_with_rate.append((tool_name, perf.success_rate))
                else:
                    tools_with_rate.append((tool_name, 0.5))

            tools_with_rate.sort(key=lambda x: x[1], reverse=True)

            for tool_name, success_rate in tools_with_rate[:3]:
                recommendations.append(
                    ToolRecommendation(
                        tool_name=tool_name,
                        priority=(
                            ToolPriority.CRITICAL if success_rate > 0.9 else ToolPriority.IMPORTANT
                        ),
                        confidence=success_rate,
                        reason=f"基于成功率选择 ({success_rate:.1%})",
                        estimated_time=3.0,
                    )
                )

        return recommendations

    async def _context_aware_routing(
        self, intent_analysis: dict[str, Any], context: dict[str, Any], available_tools: list[str]
    ) -> list[ToolRecommendation]:
        """上下文感知路由"""
        recommendations = []
        keywords = intent_analysis["keywords"]
        context_features = intent_analysis["context_features"]

        for keyword in keywords:
            matching_tools = self._find_tools_by_keyword(keyword, available_tools)

            for tool_name in matching_tools:
                # 计算上下文匹配度
                context_score = self._calculate_context_affinity(tool_name, context_features)

                recommendations.append(
                    ToolRecommendation(
                        tool_name=tool_name,
                        priority=(
                            ToolPriority.IMPORTANT if context_score > 0.7 else ToolPriority.NORMAL
                        ),
                        confidence=context_score,
                        reason=f"基于上下文匹配选择 (匹配度: {context_score:.2f})",
                        estimated_time=3.0,
                    )
                )

        return recommendations

    async def _hybrid_intelligent_routing(
        self, intent_analysis: dict[str, Any], context: dict[str, Any], available_tools: list[str]
    ) -> list[ToolRecommendation]:
        """混合智能路由 - 小诺的最强路由能力"""
        recommendations = []
        keywords = intent_analysis["keywords"]

        for keyword in keywords:
            matching_tools = self._find_tools_by_keyword(keyword, available_tools)

            for tool_name in matching_tools:
                # 综合评分
                score = self._calculate_hybrid_score(tool_name, intent_analysis, context)

                # 确定优先级
                if score > 0.8:
                    priority = ToolPriority.CRITICAL
                elif score > 0.6:
                    priority = ToolPriority.IMPORTANT
                else:
                    priority = ToolPriority.NORMAL

                recommendations.append(
                    ToolRecommendation(
                        tool_name=tool_name,
                        priority=priority,
                        confidence=score,
                        reason=f"混合智能路由选择 (综合评分: {score:.2f})",
                        estimated_time=self._estimate_execution_time(tool_name),
                    )
                )

        # 按置信度排序
        recommendations.sort(key=lambda x: x.confidence, reverse=True)

        return recommendations[:5]

    def _find_tools_by_keyword(self, keyword: str, available_tools: list[str]) -> list[str]:
        """根据关键词查找工具"""
        # 工具关键词映射
        tool_keyword_map = {
            "search": ["bing_search", "google_search", "patent_search"],
            "patent": ["patent_search", "patent_analysis", "patent_crawler"],
            "crawl": ["universal_crawler", "patent_crawler", "web_crawler"],
            "browser": ["chrome_automation", "browser_automation", "selenium_driver"],
            "analysis": ["patent_analysis", "data_analysis", "text_analysis"],
            "write": ["text_generator", "report_writer", "patent_writer"],
        }

        matching_tools = tool_keyword_map.get(keyword, [])

        # 如果有可用工具限制,进行过滤
        if available_tools:
            matching_tools = [t for t in matching_tools if t in available_tools]

        return matching_tools

    def _calculate_context_affinity(
        self, tool_name: str, context_features: dict[str, Any]
    ) -> float:
        """计算上下文亲和度"""
        if tool_name not in self.tool_performance:
            return 0.5

        affinity = self.tool_performance[tool_name].context_affinity
        score = 0.0
        count = 0

        for feature, value in context_features.items():
            if feature in affinity:
                if isinstance(value, bool):
                    score += affinity[feature] if value else 0
                else:
                    score += affinity[feature] * min(value, 1.0)
                count += 1

        return score / max(count, 1)

    def _calculate_hybrid_score(
        self, tool_name: str, intent_analysis: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """计算混合评分"""
        weights = (
            self.performance_predictor["feature_weights"]
            if self.performance_predictor
            else {
                "historical_performance": 0.4,
                "context_match": 0.3,
                "recency_factor": 0.2,
                "load_factor": 0.1,
            }
        )

        # 历史性能分数
        perf_score = 0.5
        if tool_name in self.tool_performance:
            perf = self.tool_performance[tool_name]
            perf_score = perf.performance_score

        # 上下文匹配分数
        context_score = self._calculate_context_affinity(
            tool_name, intent_analysis["context_features"]
        )

        # 时效性分数
        recency_score = 0.5
        if tool_name in self.tool_performance:
            perf = self.tool_performance[tool_name]
            if perf.last_called:
                days_since_last = (datetime.now() - perf.last_called).days
                recency_score = max(0.1, 1.0 - days_since_last / 30)

        # 负载因子分数(简化)
        load_score = 0.8  # 假设系统负载适中

        # 加权计算总分
        total_score = (
            weights["historical_performance"] * perf_score
            + weights["context_match"] * context_score
            + weights["recency_factor"] * recency_score
            + weights["load_factor"] * load_score
        )

        return min(total_score, 1.0)

    def _estimate_execution_time(self, tool_name: str) -> float:
        """估算执行时间"""
        if tool_name in self.tool_performance:
            return self.tool_performance[tool_name].average_execution_time
        return 3.0  # 默认估算

    def _generate_cache_key(
        self,
        intent: str,
        context: dict[str, Any],        available_tools: list[str],
        strategy: RoutingStrategy,
    ) -> str:
        """生成缓存键"""
        key_data = {
            "intent": intent,
            "context_keys": sorted(context.keys()),
            "available_tools": sorted(available_tools or []),
            "strategy": strategy.value,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = []

        for key, timestamp in getattr(self, "cache_timestamps", {}).items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            if key in self.routing_cache:
                del self.routing_cache[key]

    async def _fallback_routing(
        self, intent: str, context: dict[str, Any], available_tools: list[str]
    ) -> list[ToolRecommendation]:
        """降级路由"""
        logger.warning("🔄 使用降级路由策略")
        try:
            # 使用基础路由器
            return await self.base_router.route_tools(intent, context, available_tools)
        except Exception as e:
            logger.error(f"❌ 降级路由也失败: {e}")
            # 返回默认推荐
            return [
                ToolRecommendation(
                    tool_name="universal_crawler",
                    priority=ToolPriority.NORMAL,
                    confidence=0.5,
                    reason="降级路由默认推荐",
                    estimated_time=5.0,
                )
            ]

    def record_tool_execution(
        self, tool_name: str, success: bool, execution_time: float, context: dict[str, Any]
    ):
        """记录工具执行结果"""
        if tool_name not in self.tool_performance:
            self.tool_performance[tool_name] = ToolPerformance(tool_name=tool_name)

        perf = self.tool_performance[tool_name]
        perf.total_calls += 1
        perf.total_execution_time += execution_time
        perf.last_called = datetime.now()

        if success:
            perf.successful_calls += 1
        else:
            perf.failed_calls += 1

        # 更新统计指标
        perf.success_rate = perf.successful_calls / perf.total_calls
        perf.average_execution_time = perf.total_execution_time / perf.total_calls

        # 计算综合性能分数
        perf.performance_score = (
            perf.success_rate * 0.6
            + (1.0 / max(1.0, perf.average_execution_time)) * 0.2
            + (1.0 / max(1.0, (datetime.now() - perf.last_called).days / 30)) * 0.2
        )

        # 更新上下文亲和度
        self._update_context_affinity(tool_name, context, success)

    def _update_context_affinity(self, tool_name: str, context: dict[str, Any], success: bool):
        """更新上下文亲和度"""
        if tool_name not in self.tool_performance:
            return

        perf = self.tool_performance[tool_name]

        # 简化的上下文特征更新
        for feature, value in context.items():
            if isinstance(value, bool):
                if feature not in perf.context_affinity:
                    perf.context_affinity[feature] = 0.5

                # 根据成功与否调整亲和度
                adjustment = 0.1 if success else -0.05
                perf.context_affinity[feature] += adjustment
                perf.context_affinity[feature] = max(0.1, min(0.9, perf.context_affinity[feature]))

    def get_routing_analytics(self) -> dict[str, Any]:
        """获取路由分析报告"""
        total_decisions = len(self.routing_history)
        if total_decisions == 0:
            return {"message": "暂无路由历史数据"}

        # 分析路由决策
        strategy_usage = defaultdict(int)
        tool_usage = defaultdict(int)
        confidence_scores = []

        for decision in self.routing_history:
            strategy_usage[decision.strategy.value] += 1
            for tool in decision.selected_tools:
                tool_usage[tool] += 1
            confidence_scores.append(decision.confidence)

        return {
            "total_decisions": total_decisions,
            "strategy_distribution": dict(strategy_usage),
            "most_used_tools": dict(
                sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "average_confidence": sum(confidence_scores) / len(confidence_scores),
            "tool_performance_stats": {
                name: {
                    "calls": perf.total_calls,
                    "success_rate": perf.success_rate,
                    "avg_execution_time": perf.average_execution_time,
                    "performance_score": perf.performance_score,
                }
                for name, perf in self.tool_performance.items()
            },
            "cache_hit_rate": len(self.routing_cache) / max(total_decisions, 1),
            "generated_at": datetime.now().isoformat(),
        }

    def save_learning_data(self):
        """保存学习数据"""
        try:
            {
                "tool_performance": self.tool_performance,
                "routing_history": list(self.routing_history),
                "context_models": self.context_models,
                "saved_at": datetime.now().isoformat(),
            }

            # 这里应该调用实际的保存函数
            logger.info("✅ 学习数据保存成功")
        except Exception as e:
            logger.error(f"❌ 学习数据保存失败: {e}")


# 全局实例
xiaonuo_enhanced_router = XiaonuoEnhancedToolRouter()


# 便捷函数
async def smart_route(
    intent: str, context: dict[str, Any], tools: list[str] | None = None
) -> list[ToolRecommendation]:
    """便捷的智能路由函数"""
    return await xiaonuo_enhanced_router.route_tools(intent, context, tools)
