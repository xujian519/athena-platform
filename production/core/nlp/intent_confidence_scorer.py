#!/usr/bin/env python3
"""
意图置信度评分器
Intent Confidence Scorer

为所有智能体提供意图识别的置信度评分:
1. 基于关键词的初步评分
2. 基于语义的二次评分
3. 置信度阈值判断
4. 低置信度语义澄清
5. 置信度历史追踪

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "置信度增强"
"""

from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """置信度等级"""

    VERY_HIGH = "very_high"  # >0.95
    HIGH = "high"  # 0.85-0.95
    MEDIUM = "medium"  # 0.70-0.85
    LOW = "low"  # 0.50-0.70
    VERY_LOW = "very_low"  # <0.50


@dataclass
class IntentClassification:
    """意图分类结果"""

    intent: str
    confidence: float
    confidence_level: ConfidenceLevel
    reasoning: str
    needs_clarification: bool
    alternative_intents: list[tuple[str, float]] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConfidenceHistory:
    """置信度历史"""

    intent: str
    confidences: deque[float] = field(default_factory=lambda: deque(maxlen=100))
    avg_confidence: float = 0.0
    success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class IntentConfidenceScorer:
    """
    意图置信度评分器

    核心功能:
    1. 多维度置信度计算
    2. 语义澄清机制
    3. 历史统计分析
    4. 动态阈值调整
    5. 置信度校准
    """

    def __init__(self):
        # 置信度阈值
        self.confidence_threshold = 0.70
        self.clarification_threshold = 0.50

        # 意图关键词库
        self.intent_keywords = self._initialize_intent_keywords()

        # 置信度历史
        self.confidence_history: dict[str, ConfidenceHistory] = {}

        # 统计信息
        self.metrics = {
            "total_classifications": 0,
            "low_confidence_count": 0,
            "clarification_count": 0,
            "avg_confidence": 0.0,
        }

        logger.info("🎯 意图置信度评分器初始化完成")

    def _initialize_intent_keywords(self) -> dict[str, list[str]]:
        """初始化意图关键词库"""
        return {
            # 技术类意图
            "技术问题": ["代码", "编程", "bug", "调试", "开发", "算法", "架构", "API"],
            "数据分析": ["数据", "分析", "统计", "可视化", "报表", "指标"],
            # 情感类意图
            "情感表达": ["爱", "喜欢", "开心", "快乐", "幸福", "感谢"],
            "情感诉求": ["想", "思念", "陪伴", "安慰", "关心"],
            # 业务类意图
            "业务咨询": ["咨询", "询问", "了解", "介绍"],
            "任务执行": ["帮我", "执行", "完成", "处理", "操作"],
            # 专利类意图
            "专利检索": ["检索", "搜索", "查找", "专利"],
            "专利分析": ["分析", "评估", "判断", "可专利性"],
            "专利申请": ["申请", "撰写", "提交", "专利"],
            # 协作类意图
            "团队协作": ["协作", "合作", "团队", "一起"],
            "任务委派": ["委派", "分配", "负责", "处理"],
            # 综合类意图
            "知识查询": ["是什么", "怎么样", "如何", "怎么"],
            "系统操作": ["启动", "停止", "配置", "设置"],
        }

    async def classify_with_confidence(
        self,
        message: str,
        base_intent: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> IntentClassification:
        """
        带置信度的意图分类

        Args:
            message: 用户消息
            base_intent: 基础意图(可选)
            context: 上下文信息

        Returns:
            IntentClassification: 意图分类结果
        """
        # 1. 基础意图识别
        if base_intent:
            intent = base_intent
            keyword_score = await self._calculate_keyword_score(message, intent)
        else:
            intent, keyword_score = await self._classify_by_keywords(message)

        # 2. 计算多维度置信度
        scores = {
            "keyword": keyword_score,
            "semantic": await self._calculate_semantic_score(message, intent),
            "context": await self._calculate_context_score(message, intent, context),
            "length": await self._calculate_length_score(message),
            "clarity": await self._calculate_clarity_score(message),
        }

        # 3. 加权综合置信度
        weights = {
            "keyword": 0.35,
            "semantic": 0.30,
            "context": 0.20,
            "length": 0.10,
            "clarity": 0.05,
        }

        confidence = sum(scores[key] * weights[key] for key in scores)

        # 4. 获取置信度等级
        confidence_level = self._get_confidence_level(confidence)

        # 5. 生成推理说明
        reasoning = self._generate_reasoning(intent, scores, confidence_level)

        # 6. 判断是否需要澄清
        needs_clarification = confidence < self.clarification_threshold

        # 7. 获取备选意图
        alternative_intents = []
        if confidence < 0.80:
            alternative_intents = await self._get_alternative_intents(message, intent)

        # 8. 创建分类结果
        classification = IntentClassification(
            intent=intent,
            confidence=confidence,
            confidence_level=confidence_level,
            reasoning=reasoning,
            needs_clarification=needs_clarification,
            alternative_intents=alternative_intents,
        )

        # 9. 更新历史
        await self._update_confidence_history(intent, confidence)

        # 10. 更新统计
        self.metrics["total_classifications"] += 1
        if confidence < self.confidence_threshold:
            self.metrics["low_confidence_count"] += 1
        if needs_clarification:
            self.metrics["clarification_count"] += 1

        self.metrics["avg_confidence"] = self.metrics["avg_confidence"] * 0.9 + confidence * 0.1

        logger.info(
            f"🎯 意图分类: {intent} (置信度: {confidence:.2%}, " f"等级: {confidence_level.value})"
        )

        return classification

    async def _classify_by_keywords(self, message: str) -> tuple[str, float]:
        """基于关键词的意图分类"""
        message_lower = message.lower()

        best_intent = "未知"
        best_score = 0.0

        for intent, keywords in self.intent_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1.0

            # 归一化
            if keywords:
                score = min(score / len(keywords), 1.0)

            if score > best_score:
                best_score = score
                best_intent = intent

        return best_intent, best_score

    async def _calculate_keyword_score(self, message: str, intent: str) -> float:
        """计算关键词匹配分数"""
        keywords = self.intent_keywords.get(intent, [])
        if not keywords:
            return 0.5  # 默认分数

        message_lower = message.lower()
        match_count = sum(1 for kw in keywords if kw in message_lower)

        return min(match_count / len(keywords), 1.0)

    async def _calculate_semantic_score(self, message: str, intent: str) -> float:
        """计算语义相似度分数"""
        # 简化实现:基于文本长度和复杂度
        # 实际应该使用BERT等语义模型

        # 消息长度合理性 (10-200字)
        length = len(message)
        if 10 <= length <= 200:
            length_score = 1.0
        elif length < 10:
            length_score = 0.6
        else:
            length_score = 0.8

        # 包含问号或疑问词
        question_words = ["什么", "怎么", "如何", "为什么", "哪", "吗"]
        has_question = any(qw in message for qw in question_words)
        question_score = 0.9 if has_question else 0.7

        return (length_score + question_score) / 2

    async def _calculate_context_score(
        self, message: str, intent: str, context: dict[str, Any]
    ) -> float:
        """计算上下文一致性分数"""
        if not context:
            return 0.5  # 无上下文时的默认分数

        score = 0.5

        # 检查历史意图一致性
        if "previous_intents" in context:
            previous = context["previous_intents"]
            if previous and intent in previous[-3:]:
                score += 0.3  # 最近3次有相同意图

        # 检查用户偏好
        if "user_preferences" in context:
            prefs = context["user_preferences"]
            if prefs.get("preferred_intent") == intent:
                score += 0.2

        return min(score, 1.0)

    async def _calculate_length_score(self, message: str) -> float:
        """计算长度合理性分数"""
        length = len(message)

        # 理想长度: 20-150字
        if 20 <= length <= 150:
            return 1.0
        elif 10 <= length < 20 or 150 < length <= 300:
            return 0.8
        elif length < 10:
            return 0.5  # 太短
        else:
            return 0.6  # 太长

    async def _calculate_clarity_score(self, message: str) -> float:
        """计算表达清晰度分数"""
        score = 0.5

        # 包含标点符号
        if any(punct in message for punct in "。!?,.?!"):
            score += 0.2

        # 不包含过多重复字符
        if len(set(message)) / len(message) > 0.3:
            score += 0.2

        # 包含完整句子结构
        if "。 " in message or "! " in message or "? " in message:
            score += 0.1

        return min(score, 1.0)

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """获取置信度等级"""
        if confidence >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _generate_reasoning(
        self, intent: str, scores: dict[str, float], level: ConfidenceLevel
    ) -> str:
        """生成推理说明"""
        reasons = []

        # 关键词匹配
        if scores["keyword"] > 0.7:
            reasons.append(f"关键词匹配度高({scores['keyword']:.1%})")

        # 语义合理
        if scores["semantic"] > 0.7:
            reasons.append("语义表达清晰")

        # 上下文一致
        if scores["context"] > 0.7:
            reasons.append("上下文一致")

        # 置信度等级
        if level in [ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH]:
            reasons.append("高置信度识别")
        elif level == ConfidenceLevel.MEDIUM:
            reasons.append("中等置信度")
        else:
            reasons.append("低置信度,建议确认")

        return "; ".join(reasons)

    async def _get_alternative_intents(
        self, message: str, primary_intent: str
    ) -> list[tuple[str, float]]:
        """获取备选意图"""
        alternatives = []

        for intent in self.intent_keywords:
            if intent == primary_intent:
                continue

            score = await self._calculate_keyword_score(message, intent)
            if score > 0.3:  # 至少有一定相关性
                alternatives.append((intent, score))

        # 按分数排序,返回前3个
        alternatives.sort(key=lambda x: x[1], reverse=True)
        return alternatives[:3]

    async def _update_confidence_history(self, intent: str, confidence: float):
        """更新置信度历史"""
        if intent not in self.confidence_history:
            self.confidence_history[intent] = ConfidenceHistory(intent=intent)

        history = self.confidence_history[intent]
        history.confidences.append(confidence)

        # 更新平均置信度
        history.avg_confidence = sum(history.confidences) / len(history.confidences)
        history.last_updated = datetime.now()

    async def semantic_clarify(
        self, message: str, classification: IntentClassification
    ) -> IntentClassification:
        """
        语义澄清

        当置信度过低时,通过澄清对话提高准确性
        """
        logger.info(f"🔍 开始语义澄清: {classification.intent}")

        # 在实际应用中,这里会:
        # 1. 向用户提出澄清问题
        # 2. 根据用户回答重新分类
        # 3. 更新置信度

        # 简化实现:基于备选意图重新评估
        if classification.alternative_intents:
            # 选择分数最高的备选意图
            best_alt, alt_score = classification.alternative_intents[0]

            # 如果备选意图分数明显更高,则切换
            if alt_score > classification.confidence * 1.2:
                classification.intent = best_alt
                classification.confidence = min(alt_score * 1.1, 0.95)
                classification.confidence_level = self._get_confidence_level(
                    classification.confidence
                )
                classification.reasoning = "经过语义澄清后重新识别"

        classification.needs_clarification = False

        logger.info(f"✅ 语义澄清完成: {classification.intent}")

        return classification

    async def get_confidence_metrics(self) -> dict[str, Any]:
        """获取置信度统计指标"""
        return {
            "overall": {
                "total": self.metrics["total_classifications"],
                "low_confidence_rate": (
                    self.metrics["low_confidence_count"]
                    / max(self.metrics["total_classifications"], 1)
                ),
                "clarification_rate": (
                    self.metrics["clarification_count"]
                    / max(self.metrics["total_classifications"], 1)
                ),
                "avg_confidence": self.metrics["avg_confidence"],
            },
            "by_intent": {
                intent: {
                    "avg_confidence": history.avg_confidence,
                    "sample_count": len(history.confidences),
                }
                for intent, history in self.confidence_history.items()
            },
        }

    def set_confidence_threshold(self, threshold: float) -> None:
        """设置置信度阈值"""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"📊 置信度阈值已更新: {threshold:.2%}")
        else:
            raise ValueError("阈值必须在0-1之间")


# 导出便捷函数
_confidence_scorer: IntentConfidenceScorer | None = None


def get_intent_confidence_scorer() -> IntentConfidenceScorer:
    """获取意图置信度评分器单例"""
    global _confidence_scorer
    if _confidence_scorer is None:
        _confidence_scorer = IntentConfidenceScorer()
    return _confidence_scorer
