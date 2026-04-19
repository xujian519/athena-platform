#!/usr/bin/env python3
from __future__ import annotations
"""
小诺上下文理解机制
Xiaonuo Context-Aware Understanding System

实现多轮对话上下文理解,支持上下文切换检测和上下文权重学习

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0 "智能上下文理解"
"""

import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import jieba

# 安全修复: 使用joblib替代pickle序列化scikit-learn模型
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from core.logging_config import setup_logging

# 机器学习库

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class ConversationTurn:
    """对话轮次"""

    user_input: str
    intent: str
    entities: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    response: str = ""
    confidence: float = 0.0


@dataclass
class ContextConfig:
    """上下文配置"""

    # 上下文窗口大小
    context_window: int = 5
    # 上下文向量维度
    context_dim: int = 512
    # 时间衰减权重
    time_decay_factor: float = 0.9
    # 上下文相似度阈值
    context_similarity_threshold: float = 0.3
    # 路径配置
    model_dir: str = "models/context_aware"
    cache_dir: str = "cache/context"


class XiaonuoContextAwareSystem:
    """小诺上下文理解系统"""

    def __init__(self, config: ContextConfig = None):
        self.config = config or ContextConfig()

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.cache_dir, exist_ok=True)

        # 上下文存储
        self.conversation_history: deque[ConversationTurn] = deque(
            maxlen=self.config.context_window
        )
        self.context_embeddings: dict[str, Any] = {}
        self.entity_memory: dict[str, Any] = {}

        # 模型组件
        self.tfidf_vectorizer = None
        self.context_classifier = None
        self.intent_transition_model: dict[str, Any] = {}

        # 初始化jieba
        self._init_jieba()

        logger.info("🧠 小诺上下文理解系统初始化完成")
        logger.info(f"📋 上下文窗口大小: {self.config.context_window}")
        logger.info(f"📏 上下文向量维度: {self.config.context_dim}")

    def _init_jieba(self) -> Any:
        """初始化jieba分词"""
        # 添加上下文相关词汇
        context_words = [
            "刚才",
            "之前",
            "继续",
            "然后",
            "接下来",
            "后来",
            "补充",
            "修改",
            "更正",
            "换一个",
            "别的",
            "其他",
            "同样",
            "类似",
            "相反",
            "不同",
            "对比",
            "比较",
            "爸爸",
            "小诺",
            "之前说的",
            "刚才提到的",
            "前面",
        ]

        for word in context_words:
            jieba.add_word(word, freq=1000)

    def add_conversation_turn(
        self,
        user_input: str,
        intent: str,
        entities: list[str] | None = None,
        response: str = "",
        confidence: float = 0.0,
    ) -> None:
        """添加对话轮次到上下文"""
        turn = ConversationTurn(
            user_input=user_input,
            intent=intent,
            entities=entities or [],
            response=response,
            confidence=confidence,
        )

        self.conversation_history.append(turn)

        # 更新实体记忆
        if entities:
            self._update_entity_memory(entities, intent)

        logger.info(f"💾 已添加对话轮次: {intent} - {user_input[:30]}...")

    def _update_entity_memory(self, entities: list[str], intent: str) -> Any:
        """更新实体记忆"""
        current_time = datetime.now()

        for entity in entities:
            if entity not in self.entity_memory:
                self.entity_memory[entity] = {
                    "intents": [],
                    "count": 0,
                    "last_seen": current_time,
                    "contexts": [],
                }

            self.entity_memory[entity]["intents"].append(intent)
            self.entity_memory[entity]["count"] += 1
            self.entity_memory[entity]["last_seen"] = current_time
            self.entity_memory[entity]["contexts"].append(intent)

    def detect_context_switch(
        self, current_intent: str, current_input: str
    ) -> tuple[bool, float, str]:
        """检测上下文切换"""
        if len(self.conversation_history) < 1:
            return False, 1.0, "无历史上下文"

        # 获取最近的意图
        recent_intents = [turn.intent for turn in list(self.conversation_history)[-3:]]

        # 计算意图连续性
        intent_continuity = self._calculate_intent_continuity(current_intent, recent_intents)

        # 计算文本相似度
        text_similarity = self._calculate_text_similarity(current_input)

        # 检测明确的切换词
        switch_keywords = ["换一个", "别的", "其他", "不是", "改为", "重新", "新话题"]
        has_switch_keyword = any(keyword in current_input for keyword in switch_keywords)

        # 综合评分
        continuity_score = (
            0.5 * intent_continuity
            + 0.3 * text_similarity
            + 0.2 * (0.0 if has_switch_keyword else 1.0)
        )

        # 判断是否切换
        is_switch = continuity_score < self.config.context_similarity_threshold
        reason = self._get_switch_reason(
            continuity_score, intent_continuity, text_similarity, has_switch_keyword
        )

        return is_switch, continuity_score, reason

    def _calculate_intent_continuity(self, current_intent: str, recent_intents: list[str]) -> float:
        """计算意图连续性"""
        if not recent_intents:
            return 1.0

        # 意图相关性矩阵
        intent_relations = {
            "TECHNICAL": {"WORK": 0.8, "LEARNING": 0.7, "QUERY": 0.6},
            "EMOTIONAL": {"FAMILY": 0.9, "HEALTH": 0.7},
            "FAMILY": {"EMOTIONAL": 0.9, "WORK": 0.5, "HEALTH": 0.6},
            "LEARNING": {"TECHNICAL": 0.8, "QUERY": 0.9},
            "WORK": {"TECHNICAL": 0.8, "COORDINATION": 0.9, "FAMILY": 0.4},
            "COORDINATION": {"WORK": 0.9, "TECHNICAL": 0.6},
            "ENTERTAINMENT": {"EMOTIONAL": 0.6, "FAMILY": 0.5},
            "HEALTH": {"EMOTIONAL": 0.7, "FAMILY": 0.6},
            "QUERY": {"LEARNING": 0.9, "TECHNICAL": 0.6},
            "COMMAND": {"TECHNICAL": 0.7, "WORK": 0.6},
        }

        # 计算与最近意图的相关性
        max_similarity = 0.0
        for recent_intent in recent_intents:
            if recent_intent == current_intent:
                similarity = 1.0
            elif (
                current_intent in intent_relations
                and recent_intent in intent_relations[current_intent]
            ):
                similarity = intent_relations[current_intent][recent_intent]
            elif (
                recent_intent in intent_relations
                and current_intent in intent_relations[recent_intent]
            ):
                similarity = intent_relations[recent_intent][current_intent]
            else:
                similarity = 0.2  # 默认低相关性

            max_similarity = max(max_similarity, similarity)

        return max_similarity

    def _calculate_text_similarity(self, current_input: str) -> float:
        """计算文本相似度"""
        if not self.conversation_history:
            return 1.0

        # 获取最近的输入文本
        recent_inputs = [turn.user_input for turn in list(self.conversation_history)[-2:]]

        if not recent_inputs:
            return 1.0

        # 简单的词汇重叠计算
        current_words = set(jieba.cut(current_input.lower()))
        max_similarity = 0.0

        for recent_input in recent_inputs:
            recent_words = set(jieba.cut(recent_input.lower()))

            # 计算Jaccard相似度
            intersection = len(current_words & recent_words)
            union = len(current_words | recent_words)
            similarity = intersection / union if union > 0 else 0.0

            max_similarity = max(max_similarity, similarity)

        return max_similarity

    def _get_switch_reason(
        self,
        continuity_score: float,
        intent_continuity: float,
        text_similarity: float,
        has_switch_keyword: bool,
    ) -> str:
        """获取切换原因"""
        reasons = []

        if has_switch_keyword:
            reasons.append("检测到切换关键词")

        if intent_continuity < 0.5:
            reasons.append("意图变化较大")

        if text_similarity < 0.3:
            reasons.append("文本内容差异明显")

        if continuity_score < self.config.context_similarity_threshold:
            reasons.append("上下文连续性不足")

        return "; ".join(reasons) if reasons else "上下文连续"

    def get_context_features(self, current_input: str) -> dict[str, Any]:
        """获取上下文特征"""
        if not self.conversation_history:
            return {
                "has_context": False,
                "recent_intents": [],
                "entity_context": {},
                "time_decay": 1.0,
            }

        # 获取最近的意图
        recent_intents = [turn.intent for turn in list(self.conversation_history)[-3:]]

        # 获取实体上下文
        current_words = set(jieba.cut(current_input))
        entity_context = self._get_relevant_entities(current_words)

        # 计算时间衰减
        time_decay = self._calculate_time_decay()

        # 上下文强度
        context_strength = len(self.conversation_history) / self.config.context_window

        return {
            "has_context": True,
            "recent_intents": recent_intents,
            "entity_context": entity_context,
            "time_decay": time_decay,
            "context_strength": context_strength,
            "conversation_length": len(self.conversation_history),
        }

    def _get_relevant_entities(self, current_words: set) -> dict[str, Any]:
        """获取相关实体"""
        relevant_entities = {}

        for entity, info in self.entity_memory.items():
            entity_words = set(jieba.cut(entity))

            # 检查实体是否在当前输入中相关
            relevance = len(current_words & entity_words) / len(entity_words) if entity_words else 0

            if relevance > 0 or info["count"] > 1:  # 相关或高频实体
                time_diff = (datetime.now() - info["last_seen"]).total_seconds()
                recency = 1.0 / (1.0 + time_diff / 3600)  # 小时级别的衰减

                relevant_entities[entity] = {
                    "count": info["count"],
                    "recent_intents": info["intents"][-3:],
                    "relevance": relevance,
                    "recency": recency,
                }

        return relevant_entities

    def _calculate_time_decay(self) -> float:
        """计算时间衰减权重"""
        if not self.conversation_history:
            return 1.0

        current_time = datetime.now()
        total_weight = 0.0
        total_decayed_weight = 0.0

        for _i, turn in enumerate(self.conversation_history):
            # 计算时间差(秒)
            time_diff = (current_time - turn.timestamp).total_seconds()

            # 计算衰减权重
            decayed_weight = self.config.time_decay_factor ** (time_diff / 60)  # 分钟级别衰减

            total_weight += 1.0
            total_decayed_weight += decayed_weight

        return total_decayed_weight / total_weight if total_weight > 0 else 1.0

    def enhance_intent_prediction(
        self, base_intent: str, base_confidence: float, current_input: str
    ) -> tuple[str, float]:
        """基于上下文增强意图预测"""
        context_features = self.get_context_features(current_input)

        if not context_features["has_context"]:
            return base_intent, base_confidence

        # 检测上下文切换
        is_switch, continuity_score, switch_reason = self.detect_context_switch(
            base_intent, current_input
        )

        # 获取上下文建议
        suggested_intent, suggestion_confidence = self._get_context_suggestion(
            base_intent, context_features
        )

        # 综合决策
        if is_switch:
            # 上下文切换,减少历史影响
            final_confidence = base_confidence * 0.8 + 0.2
            enhanced_intent = base_intent
        else:
            # 上下文连续,结合上下文建议
            if suggestion_confidence > 0.7:
                # 高置信度上下文建议
                final_confidence = (base_confidence + suggestion_confidence) / 2
                enhanced_intent = suggested_intent
            else:
                # 保持原预测,略微调整置信度
                final_confidence = base_confidence * (0.9 + 0.1 * continuity_score)
                enhanced_intent = base_intent

        logger.info(f"🔗 上下文增强: {base_intent} -> {enhanced_intent}")
        logger.info(f"📊 置信度变化: {base_confidence:.3f} -> {final_confidence:.3f}")
        if is_switch:
            logger.info(f"🔄 检测到上下文切换: {switch_reason}")

        return enhanced_intent, final_confidence

    def _get_context_suggestion(
        self, base_intent: str, context_features: dict[str, Any]
    ) -> tuple[str, float]:
        """获取上下文建议"""
        if not context_features["recent_intents"]:
            return base_intent, 0.0

        # 基于最近意图的建议
        recent_intents = context_features["recent_intents"]
        intent_counts = {}

        for intent in recent_intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        # 获取最常见的意图
        most_common_intent = max(intent_counts.items(), key=lambda x: x[1])
        confidence = most_common_intent[1] / len(recent_intents)

        return most_common_intent[0], confidence

    def train_context_models(self, training_data: list[dict[str, Any]]) -> Any:
        """训练上下文模型"""
        logger.info("🚀 开始训练上下文理解模型...")

        # 准备训练数据
        contexts = []
        labels = []

        for data in training_data:
            current_input = data["current_input"]
            context_history = data.get("context_history", [])
            is_switch = data.get("is_context_switch", False)

            # 构建上下文特征
            context_features = self._build_context_features_for_training(
                current_input, context_history
            )

            contexts.append(context_features)
            labels.append(1 if is_switch else 0)

        # 训练上下文切换检测模型
        if len(contexts) > 0:
            self._train_context_switch_detector(contexts, labels)

        logger.info("✅ 上下文理解模型训练完成")

    def _build_context_features_for_training(
        self, current_input: str, context_history: list[str]
    ) -> np.ndarray:
        """为训练构建上下文特征"""
        features = []

        # 基础特征
        features.append(len(context_history))  # 上下文长度
        features.append(len(current_input))  # 当前输入长度

        # 意图连续性特征
        if context_history:
            # 这里简化处理,实际应该有意图信息
            features.append(1.0)  # 假设意图连续性
        else:
            features.append(0.0)

        # 文本相似度特征
        if context_history:
            # 简化的文本相似度计算
            current_words = set(jieba.cut(current_input))
            recent_words = set(jieba.cut(context_history[-1]))
            intersection = len(current_words & recent_words)
            union = len(current_words | recent_words)
            similarity = intersection / union if union > 0 else 0.0
            features.append(similarity)
        else:
            features.append(0.0)

        return np.array(features)

    def _train_context_switch_detector(self, contexts: list[np.ndarray], labels: list[int]):
        """训练上下文切换检测器"""
        # 转换为numpy数组
        X = np.array(contexts)
        y = np.array(labels)

        # 训练随机森林分类器
        self.context_classifier = RandomForestClassifier(
            n_estimators=100, max_depth=5, random_state=42
        )

        self.context_classifier.fit(X, y)

        logger.info(f"🎯 上下文切换检测器训练完成,样本数: {len(X)}")

    def save_context_models(self) -> None:
        """保存上下文模型"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.config.model_dir, f"context_models_{timestamp}.joblib")

        model_data = {
            "conversation_history": list(self.conversation_history),
            "entity_memory": self.entity_memory,
            "context_classifier": self.context_classifier,
            "config": self.config,
        }

        # 安全修复: 使用joblib替代pickle
        joblib.dump(model_data, model_path)

        # 保存最新模型
        latest_path = os.path.join(self.config.model_dir, "latest_context_models.joblib")
        joblib.dump(model_data, latest_path)

        logger.info(f"💾 上下文模型已保存: {model_path}")

    def load_context_models(self, model_path: str | None = None) -> Any | None:
        """加载上下文模型"""
        if model_path is None:
            model_path = os.path.join(self.config.model_dir, "latest_context_models.joblib")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 安全修复: 使用joblib替代pickle
        model_data = joblib.load(model_path)

        self.conversation_history = deque(
            model_data["conversation_history"], maxlen=self.config.context_window
        )
        self.entity_memory = model_data["entity_memory"]
        self.context_classifier = model_data["context_classifier"]
        self.config = model_data["config"]

        logger.info(f"✅ 上下文模型已加载: {model_path}")

    def get_conversation_summary(self) -> dict[str, Any]:
        """获取对话摘要"""
        if not self.conversation_history:
            return {"status": "无对话历史"}

        # 统计意图分布
        intent_counts = {}
        for turn in self.conversation_history:
            intent_counts[turn.intent] = intent_counts.get(turn.intent, 0) + 1

        # 计算对话时长
        if len(self.conversation_history) > 1:
            first_turn = next(iter(self.conversation_history))
            last_turn = list(self.conversation_history)[-1]
            duration = last_turn.timestamp - first_turn.timestamp
        else:
            duration = timedelta(0)

        return {
            "status": "有对话历史",
            "total_turns": len(self.conversation_history),
            "intent_distribution": intent_counts,
            "conversation_duration": str(duration),
            "entity_memory_size": len(self.entity_memory),
            "context_strength": len(self.conversation_history) / self.config.context_window,
        }


def main() -> None:
    """主函数"""
    logger.info("🧠 小诺上下文理解系统测试开始")

    # 创建配置
    config = ContextConfig()

    # 创建上下文理解系统
    context_system = XiaonuoContextAwareSystem(config)

    # 模拟对话场景
    try:
        # 场景1: 连续技术讨论
        logger.info("📝 场景1: 连续技术讨论")
        context_system.add_conversation_turn("帮我分析这段代码", "TECHNICAL", ["代码"])

        enhanced_intent, confidence = context_system.enhance_intent_prediction(
            "TECHNICAL", 0.85, "这个算法复杂度怎么样"
        )
        logger.info(f"增强结果: {enhanced_intent} ({confidence:.3f})")

        context_system.add_conversation_turn("算法复杂度分析", "TECHNICAL", ["算法", "复杂度"])

        # 场景2: 上下文切换
        logger.info("\n📝 场景2: 上下文切换")
        enhanced_intent, confidence = context_system.enhance_intent_prediction(
            "EMOTIONAL", 0.80, "爸爸,我想你了"
        )
        logger.info(f"增强结果: {enhanced_intent} ({confidence:.3f})")

        is_switch, score, reason = context_system.detect_context_switch(
            "EMOTIONAL", "爸爸,我想你了"
        )
        logger.info(f"上下文切换: {is_switch}, 分数: {score:.3f}, 原因: {reason}")

        # 场景3: 实体记忆
        logger.info("\n📝 场景3: 实体记忆")
        context_system.add_conversation_turn("Python编程学习", "LEARNING", ["Python", "编程"])
        context_system.add_conversation_turn("继续学Python", "LEARNING", ["Python"])

        features = context_system.get_context_features("Python的高级特性")
        logger.info(f"上下文特征: {features}")

        # 对话摘要
        logger.info("\n📊 对话摘要:")
        summary = context_system.get_conversation_summary()
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

        # 保存模型
        context_system.save_context_models()

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
