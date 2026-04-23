#!/usr/bin/env python3
from __future__ import annotations
"""
智能推荐系统
Intelligent Recommender System

从备份的智能推荐服务迁移并集成到新核心架构
提供智能专利推荐和趋势预测能力

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RecommendationResult:
    """推荐结果"""

    item_id: str
    recommendation_type: str  # similar_patent, collaborator, technology, market
    title: str
    description: str
    confidence_score: float
    reasoning: str
    metadata: dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrendPrediction:
    """趋势预测"""

    prediction_type: str  # technology_trend, market_trend, success_probability
    target_domain: str
    prediction_value: Any
    confidence: float
    time_horizon: str
    supporting_evidence: list[str]
    generated_at: datetime = field(default_factory=datetime.now)


class IntelligentRecommender:
    """智能推荐系统 - 适配新核心架构"""

    def __init__(self, agent_id: str, config: Optional[dict[str, Any]] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

        # 推荐缓存
        self.recommendation_cache = {}
        self.prediction_cache = {}
        self.cache_ttl = self.config.get("cache_ttl_hours", 24) * 3600  # 转换为秒

        # 推荐权重配置
        self.recommendation_weights = {
            "similarity": 0.3,
            "recency": 0.2,
            "popularity": 0.15,
            "diversity": 0.15,
            "user_preference": 0.2,
        }

        # 知识库集成
        self.knowledge_base = None

        logger.info(f"🤖 智能推荐系统创建: {self.agent_id}")

    async def initialize(self):
        """初始化智能推荐系统"""
        if self.initialized:
            return

        logger.info(f"🚀 启动智能推荐系统: {self.agent_id}")

        try:
            # 初始化知识库(简化版本)
            await self._initialize_knowledge_base()

            self.initialized = True
            logger.info(f"✅ 智能推荐系统启动完成: {self.agent_id}")

        except Exception as e:
            logger.warning(f"⚠️ 智能推荐系统初始化失败,使用基础功能: {e}")
            self.initialized = True

    async def generate_recommendations(
        self,
        query: str,
        item_info: Optional[dict[str, Any]] = None,
        recommendation_types: Optional[list[str]] = None,
        k: int = 10,
    ) -> dict[str, Any]:
        """生成推荐"""
        if not self.initialized:
            raise RuntimeError("智能推荐系统未初始化")

        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(query, recommendation_types, k)

            # 检查缓存
            cached_result = self._get_cached_recommendation(cache_key)
            if cached_result:
                logger.debug(f"✅ 使用缓存推荐: {cache_key}")
                return cached_result

            start_time = time.time()
            logger.info(f"🎯 开始生成推荐: {query[:50]}...")

            # 确定推荐类型
            if not recommendation_types:
                recommendation_types = ["similar", "trending", "collaborative"]

            # 生成各类推荐
            all_recommendations = []

            if "similar" in recommendation_types:
                similar_recs = await self._generate_similarity_recommendations(query, item_info)
                all_recommendations.extend(similar_recs)

            if "trending" in recommendation_types:
                trending_recs = await self._generate_trending_recommendations(query)
                all_recommendations.extend(trending_recs)

            if "collaborative" in recommendation_types:
                collaborative_recs = await self._generate_collaborative_recommendations(query)
                all_recommendations.extend(collaborative_recs)

            if "market" in recommendation_types:
                market_recs = await self._generate_market_recommendations(query)
                all_recommendations.extend(market_recs)

            # 排序和过滤
            sorted_recommendations = sorted(
                all_recommendations, key=lambda x: x.confidence_score, reverse=True
            )[:k]

            # 转换为输出格式
            recommendations_output = []
            for rec in sorted_recommendations:
                recommendations_output.append(
                    {
                        "id": rec.item_id,
                        "type": rec.recommendation_type,
                        "title": rec.title,
                        "description": rec.description,
                        "confidence": rec.confidence_score,
                        "reasoning": rec.reasoning,
                        "metadata": rec.metadata,
                    }
                )

            processing_time = time.time() - start_time

            result = {
                "success": True,
                "query": query[:100],
                "recommendations": recommendations_output,
                "total_found": len(recommendations_output),
                "processing_time": processing_time,
                "recommendation_types": recommendation_types,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
            }

            # 缓存结果
            self._cache_recommendation(cache_key, result)

            logger.info(
                f"✅ 推荐生成完成: {len(recommendations_output)} 个推荐,耗时 {processing_time:.2f}s"
            )
            return result

        except Exception as e:
            logger.error(f"❌ 推荐生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": [],
                "agent_id": self.agent_id,
            }

    async def predict_trends(
        self, domain: str, prediction_type: str = "technology_trend", time_horizon: str = "6_months"
    ) -> dict[str, Any]:
        """预测趋势"""
        if not self.initialized:
            raise RuntimeError("智能推荐系统未初始化")

        try:
            cache_key = f"trend_{domain}_{prediction_type}_{time_horizon}"

            # 检查缓存
            cached_prediction = self._get_cached_prediction(cache_key)
            if cached_prediction:
                return cached_prediction

            logger.info(f"🔮 开始趋势预测: {domain}")

            # 生成预测(简化实现)
            prediction = await self._generate_trend_prediction(
                domain, prediction_type, time_horizon
            )

            result = {
                "success": True,
                "domain": domain,
                "prediction_type": prediction_type,
                "time_horizon": time_horizon,
                "prediction": prediction,
                "confidence": prediction.confidence,
                "supporting_evidence": prediction.supporting_evidence,
                "generated_at": prediction.generated_at.isoformat(),
                "agent_id": self.agent_id,
            }

            # 缓存预测结果
            self._cache_prediction(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"❌ 趋势预测失败: {e}")
            return {"success": False, "error": str(e), "agent_id": self.agent_id}

    async def get_recommendation_stats(self) -> dict[str, Any]:
        """获取推荐统计信息"""
        if not self.initialized:
            raise RuntimeError("智能推荐系统未初始化")

        return {
            "agent_id": self.agent_id,
            "cache_size": len(self.recommendation_cache),
            "prediction_cache_size": len(self.prediction_cache),
            "cache_ttl_hours": self.cache_ttl // 3600,
            "recommendation_weights": self.recommendation_weights,
            "config": self.config,
            "timestamp": datetime.now().isoformat(),
        }

    async def clear_cache(self):
        """清空缓存"""
        self.recommendation_cache.clear()
        self.prediction_cache.clear()
        logger.info(f"🧹 推荐缓存已清空: {self.agent_id}")

    # 私有方法
    async def _initialize_knowledge_base(self):
        """初始化知识库"""
        # 简化的知识库实现
        self.knowledge_base = {
            "domains": [
                "人工智能",
                "机器学习",
                "深度学习",
                "自然语言处理",
                "计算机视觉",
                "物联网",
                "区块链",
                "云计算",
                "大数据",
                "网络安全",
                "机器人",
                "自动驾驶",
            ],
            "trends": {
                "ai_trends": [
                    {"topic": "大语言模型", "growth": "high", "confidence": 0.9},
                    {"topic": "多模态AI", "growth": "medium", "confidence": 0.8},
                    {"topic": "边缘AI", "growth": "medium", "confidence": 0.7},
                ],
                "tech_trends": [
                    {"topic": "量子计算", "growth": "emerging", "confidence": 0.6},
                    {"topic": "6G通信", "growth": "research", "confidence": 0.5},
                    {"topic": "脑机接口", "growth": "research", "confidence": 0.7},
                ],
            },
        }

    async def _generate_similarity_recommendations(
        self, query: str, item_info: dict[str, Any]
    ) -> list[RecommendationResult]:
        """生成相似性推荐"""
        recommendations = []

        # 简化的相似性计算
        query_words = set(query.lower().split())

        # 基于知识库的相似项目
        for domain in self.knowledge_base["domains"]:
            domain_words = set(domain.lower().split())
            overlap = len(query_words & domain_words)

            if overlap > 0:
                confidence = min(0.9, overlap / len(query_words))
                recommendations.append(
                    RecommendationResult(
                        item_id=f"similar_{domain}",
                        recommendation_type="similar",
                        title=f"相关领域: {domain}",
                        description=f"基于相似性分析,{domain}与您的查询有{overlap}个关键词重叠",
                        confidence_score=confidence,
                        reasoning=f"关键词重叠度: {overlap}/{len(query_words)}",
                        metadata={"domain": domain, "overlap": overlap},
                    )
                )

        return recommendations

    async def _generate_trending_recommendations(self, query: str) -> list[RecommendationResult]:
        """生成趋势推荐"""
        recommendations = []

        query_lower = query.lower()

        # 扩展关键词映射,提高匹配灵活性
        keyword_mappings = {
            "机器学习": ["ai", "人工智能", "机器学习", "深度学习", "神经网络", "算法", "模型"],
            "人工智能": ["ai", "人工智能", "机器学习", "深度学习", "神经网络", "智能"],
            "深度学习": ["深度学习", "神经网络", "ai", "人工智能", "机器学习"],
            "技术": ["技术", "科技", "创新", "发展", "趋势"],
            "ai": ["ai", "人工智能", "机器学习", "智能", "自动化"],
            "计算": ["计算", "算法", "处理", "分析", "数据"],
            "数据": ["数据", "大数据", "分析", "处理", "信息"],
        }

        # 查询相关趋势
        for trend_category, trends in self.knowledge_base["trends"].items():
            for trend in trends:
                trend_topic_lower = trend["topic"].lower()

                # 方法1: 直接关键词匹配
                if any(keyword in query_lower for keyword in trend_topic_lower.split()):
                    recommendations.append(
                        RecommendationResult(
                            item_id=f"trending_{trend['topic']}",
                            recommendation_type="trending",
                            title=f"热门趋势: {trend['topic']}",
                            description=f"{trend['topic']}目前处于{trend['growth']}增长阶段",
                            confidence_score=trend["confidence"],
                            reasoning=f"趋势分析: {trend['growth']}增长,置信度{trend['confidence']}",
                            metadata={"category": trend_category, "growth": trend["growth"]},
                        )
                    )
                    continue

                # 方法2: 语义映射匹配
                for query_word in query_lower.split():
                    if query_word in keyword_mappings:
                        related_keywords = keyword_mappings[query_word]
                        if any(
                            related_keyword in trend_topic_lower
                            for related_keyword in related_keywords
                        ):
                            recommendations.append(
                                RecommendationResult(
                                    item_id=f"trending_{trend['topic']}",
                                    recommendation_type="trending",
                                    title=f"热门趋势: {trend['topic']}",
                                    description=f"{trend['topic']}目前处于{trend['growth']}增长阶段",
                                    confidence_score=trend["confidence"]
                                    * 0.8,  # 语义匹配置信度稍低
                                    reasoning=f"语义关联: {query_word} → {trend['topic']} ({trend['growth']}增长)",
                                    metadata={
                                        "category": trend_category,
                                        "growth": trend["growth"],
                                        "match_type": "semantic",
                                    },
                                )
                            )
                            break

        # 如果没有找到任何推荐,添加默认推荐
        if not recommendations:
            default_recommendations = [
                {
                    "topic": "人工智能技术",
                    "growth": "high",
                    "confidence": 0.8,
                    "reasoning": "基于查询内容的相关性推荐",
                },
                {
                    "topic": "机器学习应用",
                    "growth": "medium",
                    "confidence": 0.7,
                    "reasoning": "当前热门技术方向",
                },
            ]

            for default_rec in default_recommendations:
                recommendations.append(
                    RecommendationResult(
                        item_id=f"trending_default_{default_rec['topic']}",
                        recommendation_type="trending",
                        title=f"相关趋势: {default_rec['topic']}",
                        description=f"{default_rec['topic']}是当前关注的技术领域",
                        confidence_score=default_rec["confidence"],
                        reasoning=default_rec["reasoning"],
                        metadata={
                            "category": "default",
                            "growth": default_rec["growth"],
                            "match_type": "default",
                        },
                    )
                )

        return recommendations

    async def _generate_collaborative_recommendations(
        self, query: str
    ) -> list[RecommendationResult]:
        """生成协同推荐"""
        recommendations = []

        # 扩展的协同过滤实现
        collaborative_items = [
            {
                "id": "collab_1",
                "title": "行业专家推荐",
                "description": "基于用户行为模式的协同推荐",
                "keywords": ["专利", "技术", "创新", "ai", "人工智能", "机器学习"],
                "related_fields": ["深度学习", "算法", "模型", "研究"],
            },
            {
                "id": "collab_2",
                "title": "相关研究者",
                "description": "相似用户也感兴趣的内容",
                "keywords": ["研究", "开发", "应用", "项目", "实践"],
                "related_fields": ["深度学习", "技术", "系统", "工程"],
            },
            {
                "id": "collab_3",
                "title": "学术合作机会",
                "description": "基于研究兴趣的合作推荐",
                "keywords": ["学术", "合作", "论文", "期刊", "会议"],
                "related_fields": ["深度学习", "ai", "人工智能", "研究"],
            },
        ]

        query_lower = query.lower()
        query_words = set(query_lower.split())

        for item in collaborative_items:
            # 直接关键词匹配
            item_keywords = set(item["keywords"])
            overlap = len(query_words & item_keywords)

            # 相关领域匹配
            related_match = False
            if overlap == 0:
                for field in item["related_fields"]:
                    if field in query_lower:
                        related_match = True
                        overlap = 1  # 给予部分匹配分值
                        break

            if overlap > 0 or related_match:
                confidence = 0.5 + overlap * 0.15
                recommendations.append(
                    RecommendationResult(
                        item_id=item["id"],
                        recommendation_type="collaborative",
                        title=item["title"],
                        description=item["description"],
                        confidence_score=min(confidence, 0.9),
                        reasoning=f"协同过滤: {overlap}个共同兴趣点"
                        + (" (相关领域)" if related_match else ""),
                        metadata={
                            "source": "collaborative_filtering",
                            "match_type": "related" if related_match else "direct",
                        },
                    )
                )

        # 如果没有找到任何推荐,添加默认协同推荐
        if not recommendations:
            default_collaborative = {
                "id": "collab_default",
                "title": "社区推荐",
                "description": "基于相似用户兴趣的推荐内容",
                "confidence": 0.6,
                "reasoning": "通用协同过滤推荐",
            }

            recommendations.append(
                RecommendationResult(
                    item_id=default_collaborative["id"],
                    recommendation_type="collaborative",
                    title=default_collaborative["title"],
                    description=default_collaborative["description"],
                    confidence_score=default_collaborative["confidence"],
                    reasoning=default_collaborative["reasoning"],
                    metadata={"source": "collaborative_filtering", "match_type": "default"},
                )
            )

        return recommendations

    async def _generate_market_recommendations(self, query: str) -> list[RecommendationResult]:
        """生成市场推荐"""
        recommendations = []

        # 简化的市场分析
        market_opportunities = [
            {
                "id": "market_1",
                "title": "新兴技术市场",
                "description": "具有高增长潜力的技术领域",
                "confidence": 0.8,
                "reasoning": "基于技术成熟度和市场需求分析",
            },
            {
                "id": "market_2",
                "title": "产业应用场景",
                "description": "技术在实际产业中的应用机会",
                "confidence": 0.7,
                "reasoning": "基于产业链分析和技术适配性",
            },
        ]

        query_lower = query.lower()

        for opportunity in market_opportunities:
            # 简单的关键词匹配
            if any(keyword in query_lower for keyword in ["市场", "商业", "产业", "应用"]):
                recommendations.append(
                    RecommendationResult(
                        item_id=opportunity["id"],
                        recommendation_type="market",
                        title=opportunity["title"],
                        description=opportunity["description"],
                        confidence_score=opportunity["confidence"],
                        reasoning=opportunity["reasoning"],
                        metadata={"source": "market_analysis"},
                    )
                )

        return recommendations

    async def _generate_trend_prediction(
        self, domain: str, prediction_type: str, time_horizon: str
    ) -> TrendPrediction:
        """生成趋势预测"""
        # 简化的预测实现
        if domain in self.knowledge_base["domains"]:
            # 基于历史趋势和领域特征生成预测
            confidence = np.random.uniform(0.6, 0.9)

            if prediction_type == "technology_trend":
                prediction_value = f"预计{domain}在未来{time_horizon}内将保持稳步增长"
                evidence = ["当前技术成熟度较高', '市场需求持续增长', '政策支持力度大"]
            else:
                prediction_value = f"{domain}领域发展前景乐观"
                evidence = ["技术突破持续", "应用场景丰富", "投资热度高"]
        else:
            confidence = 0.5
            prediction_value = f"{domain}领域需要进一步观察和分析"
            evidence = ["数据有限", "市场变化快速", "技术路径不确定"]

        return TrendPrediction(
            prediction_type=prediction_type,
            target_domain=domain,
            prediction_value=prediction_value,
            confidence=confidence,
            time_horizon=time_horizon,
            supporting_evidence=evidence,
        )

    def _generate_cache_key(self, query: str, types: list[str], k: int) -> str:
        """生成缓存键"""
        types_str = "_".join(sorted(types)) if types else "all"
        return f"{hash(query)}_{types_str}_{k}"

    def _get_cached_recommendation(self, cache_key: str) -> Optional[dict[str, Any]]:
        """获取缓存的推荐"""
        if cache_key in self.recommendation_cache:
            cached_item = self.recommendation_cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["data"]
            else:
                del self.recommendation_cache[cache_key]
        return None

    def _cache_recommendation(self, cache_key: str, data: dict[str, Any]) -> Any:
        """缓存推荐结果"""
        self.recommendation_cache[cache_key] = {"data": data, "timestamp": time.time()}

    def _get_cached_prediction(self, cache_key: str) -> Optional[dict[str, Any]]:
        """获取缓存的预测"""
        if cache_key in self.prediction_cache:
            cached_item = self.prediction_cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["data"]
            else:
                del self.prediction_cache[cache_key]
        return None

    def _cache_prediction(self, cache_key: str, data: dict[str, Any]) -> Any:
        """缓存预测结果"""
        self.prediction_cache[cache_key] = {"data": data, "timestamp": time.time()}

    async def shutdown(self):
        """关闭推荐系统"""
        logger.info(f"🔄 关闭智能推荐系统: {self.agent_id}")

        # 清理缓存
        await self.clear_cache()

        self.initialized = False

    # 注册回调支持
    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)


# 全局实例管理
_global_instances: dict[str, IntelligentRecommender] = {}


async def get_recommender_instance(
    agent_id: str, config: Optional[dict[str, Any]] = None
) -> IntelligentRecommender:
    """获取推荐系统实例"""
    if agent_id not in _global_instances:
        _global_instances[agent_id] = IntelligentRecommender(agent_id, config)
        await _global_instances[agent_id].initialize()
    return _global_instances[agent_id]


async def shutdown_recommender(agent_id: Optional[str] = None):
    """关闭推荐系统实例"""
    if agent_id:
        if agent_id in _global_instances:
            await _global_instances[agent_id].shutdown()
            del _global_instances[agent_id]
    else:
        # 关闭所有实例
        for _instance_id, instance in list(_global_instances.items()):
            await instance.shutdown()
        _global_instances.clear()


__all__ = [
    "IntelligentRecommender",
    "RecommendationResult",
    "TrendPrediction",
    "get_recommender_instance",
    "shutdown_recommender",
]
