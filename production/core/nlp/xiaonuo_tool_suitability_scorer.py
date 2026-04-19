#!/usr/bin/env python3
"""
小诺工具适用性评分系统
Xiaonuo Tool Suitability Scoring System

构建多维度的工具适用性评分系统,支持评分预测和历史跟踪

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0 "智能评分系统"
"""

from __future__ import annotations
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import jieba

# 安全修复: 使用joblib替代pickle序列化scikit-learn模型
import joblib
import numpy as np
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestClassifier,
)

# 机器学习库
from sklearn.metrics import mean_squared_error, r2_score

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class IntentCategory(Enum):
    """意图类别"""

    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    FAMILY = "family"
    LEARNING = "learning"
    COORDINATION = "coordination"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    WORK = "work"
    QUERY = "query"
    COMMAND = "command"


class SuitabilityDimension(Enum):
    """适用性维度"""

    FUNCTIONAL_MATCH = "functional_match"  # 功能匹配度
    PERFORMANCE_ADEQUACY = "performance_adequacy"  # 性能充分性
    COMPLEXITY_APPROPRIATENESS = "complexity_appropriateness"  # 复杂度适当性
    USER_EXPERIENCE = "user_experience"  # 用户体验
    RELIABILITY = "reliability"  # 可靠性
    SCALABILITY = "scalability"  # 可扩展性
    COST_EFFECTIVENESS = "cost_effectiveness"  # 成本效益
    CONTEXT_FIT = "context_fit"  # 上下文适配度


@dataclass
class ToolCapability:
    """工具能力定义"""

    name: str
    category: str
    functional_features: list[str]
    performance_metrics: dict[str, float]
    complexity_score: float  # 0-1
    reliability_score: float  # 0-1
    scalability_score: float  # 0-1
    cost_score: float  # 0-1 (越高越便宜)
    description: str


@dataclass
class SuitabilityScore:
    """适用性评分结果"""

    tool_name: str
    overall_score: float
    dimension_scores: dict[SuitabilityDimension, float]
    confidence: float
    explanation: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SuitabilityConfig:
    """适用性评分配置"""

    # 评分权重
    dimension_weights: dict[SuitabilityDimension, float] = field(default_factory=dict)
    # 模型参数
    max_features: int = 5000
    n_estimators: int = 100
    min_samples_split: int = 5
    # 路径配置
    model_dir: str = "models/tool_suitability"
    data_dir: str = "data/tool_suitability"


class XiaonuoToolSuitabilityScorer:
    """小诺工具适用性评分器"""

    def __init__(self, config: SuitabilityConfig = None):
        self.config = config or SuitabilityConfig()

        # 设置默认维度权重
        self._init_dimension_weights()

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)

        # 工具能力和评分历史
        self.tool_capabilities: dict[str, ToolCapability] = {}
        self.suitability_history: dict[str, list[SuitabilityScore]] = defaultdict(list)
        self.scoring_models: dict[SuitabilityDimension, Any] = {}

        # 特征提取器
        self.text_vectorizer = None
        self.feature_scaler = None

        # 初始化
        self._init_tool_capabilities()
        self._init_jieba()

        logger.info("📊 小诺工具适用性评分器初始化完成")
        logger.info(f"🔧 工具能力数量: {len(self.tool_capabilities)}")
        logger.info(f"📏 评分维度数量: {len(SuitabilityDimension)}")

    def _init_dimension_weights(self) -> Any:
        """初始化维度权重"""
        self.config.dimension_weights = {
            SuitabilityDimension.FUNCTIONAL_MATCH: 0.25,
            SuitabilityDimension.PERFORMANCE_ADEQUACY: 0.20,
            SuitabilityDimension.COMPLEXITY_APPROPRIATENESS: 0.15,
            SuitabilityDimension.USER_EXPERIENCE: 0.15,
            SuitabilityDimension.RELIABILITY: 0.10,
            SuitabilityDimension.SCALABILITY: 0.05,
            SuitabilityDimension.COST_EFFECTIVENESS: 0.05,
            SuitabilityDimension.CONTEXT_FIT: 0.05,
        }

    def _init_tool_capabilities(self) -> Any:
        """初始化工具能力"""
        self.tool_capabilities = {
            # 代码分析工具
            "code_analyzer": ToolCapability(
                name="code_analyzer",
                category="code_analysis",
                functional_features=[
                    "静态代码分析",
                    "代码质量检查",
                    "安全漏洞检测",
                    "复杂度分析",
                    "代码规范检查",
                    "性能分析",
                ],
                performance_metrics={
                    "analysis_speed": 0.85,  # 分析速度
                    "accuracy": 0.90,  # 准确性
                    "coverage": 0.80,  # 覆盖率
                },
                complexity_score=0.6,
                reliability_score=0.85,
                scalability_score=0.70,
                cost_score=0.80,
                description="代码分析和质量检查工具",
            ),
            "api_tester": ToolCapability(
                name="api_tester",
                category="code_analysis",
                functional_features=[
                    "API接口测试",
                    "性能测试",
                    "压力测试",
                    "自动化测试",
                    "接口文档生成",
                    "响应时间分析",
                ],
                performance_metrics={"test_speed": 0.90, "accuracy": 0.85, "reliability": 0.80},
                complexity_score=0.4,
                reliability_score=0.80,
                scalability_score=0.85,
                cost_score=0.85,
                description="API接口测试工具",
            ),
            # 知识图谱工具
            "knowledge_graph": ToolCapability(
                name="knowledge_graph",
                category="knowledge_management",
                functional_features=[
                    "知识查询",
                    "关系分析",
                    "图谱可视化",
                    "实体识别",
                    "知识推理",
                    "语义搜索",
                ],
                performance_metrics={"query_speed": 0.75, "accuracy": 0.85, "scalability": 0.70},
                complexity_score=0.7,
                reliability_score=0.80,
                scalability_score=0.65,
                cost_score=0.70,
                description="知识图谱查询和分析工具",
            ),
            # 决策引擎工具
            "decision_engine": ToolCapability(
                name="decision_engine",
                category="decision_support",
                functional_features=[
                    "多属性决策",
                    "风险评估",
                    "方案排序",
                    "权重计算",
                    "敏感性分析",
                    "决策可视化",
                ],
                performance_metrics={
                    "processing_speed": 0.80,
                    "accuracy": 0.85,
                    "flexibility": 0.90,
                },
                complexity_score=0.8,
                reliability_score=0.85,
                scalability_score=0.75,
                cost_score=0.65,
                description="智能决策支持引擎",
            ),
            # 聊天完成工具
            "chat_companion": ToolCapability(
                name="chat_companion",
                category="conversation",
                functional_features=[
                    "对话生成",
                    "情感回应",
                    "知识问答",
                    "上下文理解",
                    "多轮对话",
                    "个性化交互",
                ],
                performance_metrics={"response_speed": 0.95, "accuracy": 0.80, "naturalness": 0.85},
                complexity_score=0.3,
                reliability_score=0.90,
                scalability_score=0.80,
                cost_score=0.90,
                description="智能聊天伴侣",
            ),
            # 网络搜索工具
            "web_search": ToolCapability(
                name="web_search",
                category="information_retrieval",
                functional_features=[
                    "网络搜索",
                    "信息聚合",
                    "结果排序",
                    "多源搜索",
                    "实时搜索",
                    "搜索优化",
                ],
                performance_metrics={"search_speed": 0.90, "relevance": 0.85, "coverage": 0.95},
                complexity_score=0.2,
                reliability_score=0.75,
                scalability_score=0.90,
                cost_score=0.85,
                description="网络搜索和信息获取工具",
            ),
            # 系统监控工具
            "system_monitor": ToolCapability(
                name="system_monitor",
                category="infrastructure/infrastructure/monitoring",
                functional_features=[
                    "性能监控",
                    "异常检测",
                    "告警通知",
                    "日志分析",
                    "资源监控",
                    "健康检查",
                ],
                performance_metrics={
                    "monitoring_speed": 0.90,
                    "detection_accuracy": 0.85,
                    "response_time": 0.80,
                },
                complexity_score=0.5,
                reliability_score=0.90,
                scalability_score=0.85,
                cost_score=0.80,
                description="系统监控和告警工具",
            ),
        }

    def _init_jieba(self) -> Any:
        """初始化jieba分词"""
        # 添加评分相关词汇
        scoring_words = [
            "性能",
            "准确性",
            "可靠性",
            "可用性",
            "易用性",
            "复杂度",
            "成本",
            "效率",
            "效果",
            "质量",
            "适配",
            "匹配",
            "适合",
            "推荐",
            "优先级",
        ]

        for word in scoring_words:
            jieba.add_word(word, freq=1000)

    def calculate_suitability_score(
        self, tool_name: str, user_request: str, intent: str, context: dict[str, Any] | None = None
    ) -> SuitabilityScore:
        """计算工具适用性评分"""
        if tool_name not in self.tool_capabilities:
            return SuitabilityScore(
                tool_name=tool_name,
                overall_score=0.0,
                dimension_scores={},
                confidence=0.0,
                explanation="工具不存在",
            )

        tool = self.tool_capabilities[tool_name]
        dimension_scores = {}

        # 计算各维度评分
        dimension_scores[SuitabilityDimension.FUNCTIONAL_MATCH] = self._calculate_functional_match(
            tool, user_request, intent
        )
        dimension_scores[SuitabilityDimension.PERFORMANCE_ADEQUACY] = (
            self._calculate_performance_adequacy(tool, user_request, context)
        )
        dimension_scores[SuitabilityDimension.COMPLEXITY_APPROPRIATENESS] = (
            self._calculate_complexity_appropriateness(tool, user_request, context)
        )
        dimension_scores[SuitabilityDimension.USER_EXPERIENCE] = self._calculate_user_experience(
            tool, context
        )
        dimension_scores[SuitabilityDimension.RELIABILITY] = tool.reliability_score
        dimension_scores[SuitabilityDimension.SCALABILITY] = (
            self._calculate_scalability_requirement(tool, user_request, context)
        )
        dimension_scores[SuitabilityDimension.COST_EFFECTIVENESS] = tool.cost_score
        dimension_scores[SuitabilityDimension.CONTEXT_FIT] = self._calculate_context_fit(
            tool, user_request, intent, context
        )

        # 计算综合评分
        overall_score = sum(
            dimension_scores[dim] * self.config.dimension_weights[dim]
            for dim in SuitabilityDimension
        )

        # 生成解释
        explanation = self._generate_explanation(tool, dimension_scores, user_request, intent)

        # 计算置信度
        confidence = self._calculate_confidence(dimension_scores, tool)

        score = SuitabilityScore(
            tool_name=tool_name,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            confidence=confidence,
            explanation=explanation,
        )

        # 保存评分历史
        self.suitability_history[tool_name].append(score)

        return score

    def _calculate_functional_match(
        self, tool: ToolCapability, user_request: str, intent: str
    ) -> float:
        """计算功能匹配度"""
        request_lower = user_request.lower()
        match_score = 0.0

        # 关键词匹配
        for feature in tool.functional_features:
            feature_lower = feature.lower()
            # 精确匹配
            if feature_lower in request_lower:
                match_score += 1.0
            # 部分匹配
            elif any(word in request_lower for word in feature_lower.split()):
                match_score += 0.5

        # 归一化
        match_score = min(match_score / len(tool.functional_features), 1.0)

        # 意图匹配调整
        intent_tool_match = {
            "technical": [
                "code_analysis",
                "infrastructure/infrastructure/monitoring",
                "decision_support",
            ],
            "emotional": ["conversation", "decision_support"],
            "family": [
                "conversation",
                "decision_support",
                "infrastructure/infrastructure/monitoring",
            ],
            "learning": ["knowledge_management", "information_retrieval", "conversation"],
            "coordination": [
                "decision_support",
                "infrastructure/infrastructure/monitoring",
                "project_management",
            ],
            "entertainment": ["conversation", "information_retrieval"],
            "health": [
                "conversation",
                "infrastructure/infrastructure/monitoring",
                "decision_support",
            ],
            "work": [
                "decision_support",
                "infrastructure/infrastructure/monitoring",
                "project_management",
            ],
            "query": ["information_retrieval", "knowledge_management"],
            "command": [
                "infrastructure/infrastructure/monitoring",
                "code_analysis",
                "project_management",
            ],
        }

        if intent in intent_tool_match and tool.category in intent_tool_match[intent]:
            match_score = min(match_score + 0.2, 1.0)

        return match_score

    def _calculate_performance_adequacy(
        self, tool: ToolCapability, user_request: str, context: dict[str, Any]
    ) -> float:
        """计算性能充分性"""
        # 基础性能分数
        base_performance = np.mean(list(tool.performance_metrics.values()))

        # 根据用户请求调整
        performance_adjustment = 0.0

        # 紧急程度调整
        if context and context.get("urgency", 0) > 0.7:
            if tool.performance_metrics.get("speed", 0.5) > 0.8:
                performance_adjustment += 0.2
            else:
                performance_adjustment -= 0.2

        # 复杂度调整
        request_complexity = len(user_request.split()) / 20.0  # 归一化复杂度
        if tool.complexity_score > request_complexity:
            performance_adjustment += 0.1
        else:
            performance_adjustment -= 0.1

        return max(0.0, min(1.0, base_performance + performance_adjustment))

    def _calculate_complexity_appropriateness(
        self, tool: ToolCapability, user_request: str, context: dict[str, Any]
    ) -> float:
        """计算复杂度适当性"""
        request_complexity = len(user_request.split()) / 20.0  # 归一化
        request_complexity = max(0.0, min(1.0, request_complexity))

        # 用户技能水平(如果提供)
        user_skill = context.get("user_skill_level", 0.5) if context else 0.5

        # 理想复杂度 = 用户技能水平 * 0.7 + 请求复杂度 * 0.3
        ideal_complexity = user_skill * 0.7 + request_complexity * 0.3

        # 计算复杂度匹配度
        complexity_match = 1.0 - abs(tool.complexity_score - ideal_complexity)

        return complexity_match

    def _calculate_user_experience(self, tool: ToolCapability, context: dict[str, Any]) -> float:
        """计算用户体验分数"""
        base_ux = 0.5  # 基础分数

        # 复杂度越低,用户体验越好
        complexity_bonus = (1.0 - tool.complexity_score) * 0.3

        # 可靠性越高,用户体验越好
        reliability_bonus = tool.reliability_score * 0.3

        # 响应时间(如果有)
        response_bonus = 0.0
        if tool.performance_metrics.get("response_speed"):
            response_bonus = tool.performance_metrics["response_speed"] * 0.2

        total_ux = base_ux + complexity_bonus + reliability_bonus + response_bonus

        return max(0.0, min(1.0, total_ux))

    def _calculate_scalability_requirement(
        self, tool: ToolCapability, user_request: str, context: dict[str, Any]
    ) -> float:
        """计算可扩展性需求分数"""
        base_scalability = tool.scalability_score

        # 检查请求中的扩展性关键词
        scalability_keywords = ["大量", "批量", "规模", "扩展", "分布式", "并发"]
        has_scalability_need = any(
            keyword in user_request.lower() for keyword in scalability_keywords
        )

        if has_scalability_need:
            # 如果需要扩展性,高扩展性工具得分更高
            if tool.scalability_score > 0.7:
                base_scalability = min(base_scalability + 0.2, 1.0)
            else:
                base_scalability = max(base_scalability - 0.2, 0.0)

        return base_scalability

    def _calculate_context_fit(
        self, tool: ToolCapability, user_request: str, intent: str, context: dict[str, Any]
    ) -> float:
        """计算上下文适配度"""
        if not context:
            return 0.5

        context_score = 0.0
        factors = 0

        # 时间上下文
        if "time_sensitive" in context:
            if context["time_sensitive"] and tool.performance_metrics.get("speed", 0.5) > 0.7:
                context_score += 0.3
            factors += 1

        # 资源限制上下文
        if "resource_limited" in context:
            if context["resource_limited"] and tool.cost_score > 0.7:
                context_score += 0.3
            factors += 1

        # 安全要求上下文
        if "security_required" in context:
            if context["security_required"] and tool.reliability_score > 0.8:
                context_score += 0.3
            factors += 1

        return context_score / factors if factors > 0 else 0.5

    def _generate_explanation(
        self,
        tool: ToolCapability,
        dimension_scores: dict[SuitabilityDimension, float],
        user_request: str,
        intent: str,
    ) -> str:
        """生成评分解释"""
        explanations = []

        # 功能匹配解释
        func_score = dimension_scores[SuitabilityDimension.FUNCTIONAL_MATCH]
        if func_score > 0.8:
            explanations.append(f"功能匹配度高({func_score:.2f}),工具功能完全满足需求")
        elif func_score > 0.5:
            explanations.append(f"功能匹配度中等({func_score:.2f}),工具功能部分满足需求")
        else:
            explanations.append(f"功能匹配度低({func_score:.2f}),工具功能与需求不匹配")

        # 性能解释
        perf_score = dimension_scores[SuitabilityDimension.PERFORMANCE_ADEQUACY]
        if perf_score > 0.8:
            explanations.append(f"性能表现优秀({perf_score:.2f})")
        elif perf_score > 0.5:
            explanations.append(f"性能表现一般({perf_score:.2f})")

        # 复杂度解释
        complex_score = dimension_scores[SuitabilityDimension.COMPLEXITY_APPROPRIATENESS]
        if complex_score > 0.8:
            explanations.append(f"复杂度非常适合({complex_score:.2f})")
        elif complex_score < 0.3:
            explanations.append(f"复杂度可能过高({complex_score:.2f})")

        # 可靠性解释
        reliability_score = dimension_scores[SuitabilityDimension.RELIABILITY]
        if reliability_score > 0.9:
            explanations.append(f"工具可靠性极高({reliability_score:.2f})")
        elif reliability_score < 0.5:
            explanations.append(f"工具可靠性需要关注({reliability_score:.2f})")

        return "; ".join(explanations)

    def _calculate_confidence(
        self, dimension_scores: dict[SuitabilityDimension, float], tool: ToolCapability
    ) -> float:
        """计算置信度"""
        # 维度评分的一致性
        scores = list(dimension_scores.values())
        score_std = np.std(scores)
        consistency = 1.0 - min(score_std, 1.0)

        # 工具信息完整性
        info_completeness = 1.0  # 假设所有工具都有完整信息

        # 历史数据可用性
        history_confidence = min(len(self.suitability_history[tool.name]) / 10.0, 1.0)

        # 综合置信度
        confidence = consistency * 0.4 + info_completeness * 0.3 + history_confidence * 0.3

        return max(0.0, min(1.0, confidence))

    def batch_score_tools(
        self,
        user_request: str,
        intent: str,
        tool_names: list[str],
        context: dict[str, Any] | None = None,
    ) -> list[SuitabilityScore]:
        """批量评分工具"""
        scores = []
        for tool_name in tool_names:
            score = self.calculate_suitability_score(tool_name, user_request, intent, context)
            scores.append(score)

        # 按综合评分排序
        scores.sort(key=lambda x: x.overall_score, reverse=True)

        return scores

    def train_suitability_models(self, training_data: list[dict[str, Any]]) -> Any:
        """训练适用性评分模型"""
        logger.info("🚀 开始训练适用性评分模型...")

        if not training_data:
            logger.warning("⚠️ 没有训练数据")
            return

        # 准备特征和标签
        features = []
        labels = {dim.value: [] for dim in SuitabilityDimension}

        for data in training_data:
            feature_vector = self._extract_features(data)
            features.append(feature_vector)

            for dim in SuitabilityDimension:
                score = data.get("dimension_scores", {}).get(dim.value, 0.5)
                labels[dim.value].append(score)

        X = np.array(features)

        # 训练每个维度的模型
        for dim in SuitabilityDimension:
            y = np.array(labels[dim.value])

            # 选择模型
            if dim == SuitabilityDimension.FUNCTIONAL_MATCH:
                # 分类问题,使用随机森林
                model = RandomForestClassifier(
                    n_estimators=self.config.n_estimators, random_state=42
                )
            else:
                # 回归问题,使用梯度提升
                model = GradientBoostingRegressor(
                    n_estimators=self.config.n_estimators,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42,
                )

            # 训练模型
            model.fit(X, y)
            self.scoring_models[dim] = model

            # 评估模型
            if hasattr(model, "predict"):
                y_pred = model.predict(X)
                if dim == SuitabilityDimension.FUNCTIONAL_MATCH:
                    accuracy = np.mean(y_pred == y)
                    logger.info(f"📊 {dim.value} 模型准确率: {accuracy:.4f}")
                else:
                    mse = mean_squared_error(y, y_pred)
                    r2 = r2_score(y, y_pred)
                    logger.info(f"📊 {dim.value} 模型 MSE: {mse:.4f}, R2: {r2:.4f}")

        logger.info("✅ 适用性评分模型训练完成")

    def _extract_features(self, data: dict[str, Any]) -> list[float]:
        """提取特征"""
        features = []

        # 文本特征
        text = data.get("user_request", "")
        words = jieba.cut(text)
        features.append(len(text))  # 文本长度
        features.append(len(list(words)))  # 词数
        features.append(text.count("?") + text.count("?"))  # 问题数量
        features.append(len([w for w in words if len(w) > 1]))  # 实词数量

        # 意图特征
        intent = data.get("intent", "")
        intent_features = [1 if intent == i.value else 0 for i in IntentCategory]
        features.extend(intent_features)

        # 上下文特征
        context = data.get("context", {})
        features.append(context.get("urgency", 0))
        features.append(context.get("resource_limited", 0))
        features.append(context.get("security_required", 0))
        features.append(context.get("time_sensitive", 0))

        return features

    def get_suitability_trends(self, tool_name: str, days: int = 30) -> dict[str, Any]:
        """获取适用性趋势分析"""
        if tool_name not in self.suitability_history:
            return {"error": "没有评分历史"}

        # 获取最近N天的评分
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_scores = [
            score for score in self.suitability_history[tool_name] if score.timestamp >= cutoff_date
        ]

        if not recent_scores:
            return {"error": "指定时间范围内没有评分记录"}

        # 计算趋势
        overall_scores = [s.overall_score for s in recent_scores]
        avg_score = np.mean(overall_scores)
        trend_slope = self._calculate_trend(overall_scores)

        # 维度分析
        dimension_trends = {}
        for dim in SuitabilityDimension:
            dim_scores = [s.dimension_scores.get(dim, 0.5) for s in recent_scores]
            if dim_scores:
                dimension_trends[dim.value] = {
                    "average": np.mean(dim_scores),
                    "trend": self._calculate_trend(dim_scores),
                    "volatility": np.std(dim_scores),
                }

        return {
            "tool_name": tool_name,
            "period_days": days,
            "score_count": len(recent_scores),
            "average_score": avg_score,
            "trend": trend_slope,
            "dimension_trends": dimension_trends,
            "recommendation": self._get_trend_recommendation(trend_slope, avg_score),
        }

    def _calculate_trend(self, scores: list[float]) -> float:
        """计算趋势斜率"""
        if len(scores) < 2:
            return 0.0

        x = np.arange(len(scores))
        y = np.array(scores)

        # 线性回归计算斜率
        slope = np.polyfit(x, y, 1)[0]
        return slope

    def _get_trend_recommendation(self, trend: float, avg_score: float) -> str:
        """获取趋势建议"""
        if trend > 0.01:
            return "工具适用性呈上升趋势,表现良好"
        elif trend < -0.01:
            return "工具适用性呈下降趋势,需要关注和优化"
        else:
            if avg_score > 0.8:
                return "工具适用性稳定在高水平"
            elif avg_score > 0.6:
                return "工具适用性稳定在中等水平,有提升空间"
            else:
                return "工具适用性稳定在较低水平,需要改进"

    def save_models(self) -> None:
        """保存模型"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.config.model_dir, f"suitability_models_{timestamp}.joblib")

        model_data = {
            "tool_capabilities": self.tool_capabilities,
            "suitability_history": dict(self.suitability_history),
            "scoring_models": self.scoring_models,
            "config": self.config,
        }

        # 安全修复: 使用joblib替代pickle
        joblib.dump(model_data, model_path)

        # 保存最新模型
        latest_path = os.path.join(self.config.model_dir, "latest_suitability_models.joblib")
        joblib.dump(model_data, latest_path)

        logger.info(f"💾 适用性评分模型已保存: {model_path}")

    def load_models(self, model_path: str | None = None) -> Any | None:
        """加载模型"""
        if model_path is None:
            model_path = os.path.join(self.config.model_dir, "latest_suitability_models.joblib")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 安全修复: 使用joblib替代pickle
        model_data = joblib.load(model_path)

        self.tool_capabilities = model_data["tool_capabilities"]
        self.suitability_history = defaultdict(list, model_data["suitability_history"])
        self.scoring_models = model_data.get("scoring_models", {})
        self.config = model_data["config"]

        logger.info(f"✅ 适用性评分模型已加载: {model_path}")


def main() -> None:
    """主函数"""
    logger.info("📊 小诺工具适用性评分系统测试开始")

    # 创建配置
    config = SuitabilityConfig()

    # 创建评分器
    scorer = XiaonuoToolSuitabilityScorer(config)

    # 测试工具适用性评分
    try:
        # 测试场景1:代码分析请求
        request1 = "帮我分析这段Python代码的性能问题"
        intent1 = "technical"
        context1 = {"urgency": 0.8, "user_skill_level": 0.7}

        score1 = scorer.calculate_suitability_score("code_analyzer", request1, intent1, context1)
        logger.info("\n📊 评分结果 1:")
        logger.info(f"工具: {score1.tool_name}")
        logger.info(f"综合评分: {score1.overall_score:.3f}")
        logger.info(f"置信度: {score1.confidence:.3f}")
        logger.info(f"解释: {score1.explanation}")

        # 批量评分测试
        tools = ["code_analyzer", "chat_companion", "web_search", "system_monitor"]
        batch_scores = scorer.batch_score_tools(request1, intent1, tools, context1)

        logger.info("\n📈 批量评分结果:")
        for score in batch_scores:
            logger.info(f"  {score.tool_name}: {score.overall_score:.3f}")

        # 测试场景2:情感交流请求
        request2 = "爸爸,今天工作很累,想聊聊"
        intent2 = "emotional"
        context2 = {"time_sensitive": 0.3, "resource_limited": 0.1}

        score2 = scorer.calculate_suitability_score("chat_companion", request2, intent2, context2)
        logger.info("\n📊 评分结果 2:")
        logger.info(f"工具: {score2.tool_name}")
        logger.info(f"综合评分: {score2.overall_score:.3f}")
        logger.info(f"置信度: {score2.confidence:.3f}")
        logger.info(f"解释: {score2.explanation}")

        # 趋势分析测试
        # 模拟历史评分
        for i in range(10):
            dummy_score = SuitabilityScore(
                tool_name="code_analyzer",
                overall_score=0.7 + i * 0.02,
                dimension_scores={},
                confidence=0.8,
                explanation="测试评分",
            )
            dummy_score.timestamp = datetime.now() - timedelta(days=i)
            scorer.suitability_history["code_analyzer"].append(dummy_score)

        trends = scorer.get_suitability_trends("code_analyzer", days=30)
        logger.info("\n📈 趋势分析结果:")
        for key, value in trends.items():
            if key != "tool_name":
                logger.info(f"  {key}: {value}")

        # 保存模型
        scorer.save_models()

        logger.info("🎉 工具适用性评分系统测试完成!")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
