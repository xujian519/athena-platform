#!/usr/bin/env python3
from __future__ import annotations
"""
小诺个性化学习系统
Xiaonuo Personalized Learning System

专门学习爸爸偏好、习惯和交流风格的智能学习系统

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import json
import os
import pickle
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class LearningInstance:
    """学习实例"""

    timestamp: datetime
    context: str  # 学习场景
    observation: str  # 观察到的行为/偏好
    pattern: str  # 识别的模式
    confidence: float  # 学习置信度
    category: str  # 学习类别
    impact_score: float  # 影响分数


@dataclass
class CommunicationStyle:
    """交流风格"""

    preferred_tone: str = "温暖专业"
    response_length: str = "适中"  # 简短/适中/详细
    technical_depth: str = "专业"  # 入门/适中/专业
    formality_level: str = "半正式"  # 非正式/半正式/正式
    emoji_usage: float = 0.5  # 0-1,表情使用频率
    speed_preference: str = "及时"  # 快速/及时/从容


@dataclass
class DadPreference:
    """爸爸偏好"""

    topic_interests: dict[str, float] = field(default_factory=dict)  # 话题兴趣度
    response_patterns: dict[str, str] = field(default_factory=dict)  # 回应模式
    active_hours: list[int] = field(default_factory=lambda: list(range(9, 22)))  # 活跃时段
    work_style: str = "高效专注"  # 工作风格
    feedback_preference: str = "建设性"  # 反馈偏好
    learning_style: str = "实践导向"  # 学习风格


class XiaonuoPersonalizedLearning:
    """小诺个性化学习系统"""

    def __init__(self):
        self.name = "小诺个性化学习系统"
        self.version = "v1.0.0"

        # 学习数据存储
        self.learning_data_path = "data/learning/xiaonuo_learning.pkl"
        self.profile_path = "data/learning/dad_profile.json"

        # 学习历史
        self.learning_history: deque = deque(maxlen=1000)
        self.patterns: dict[str, Any] = {}

        # 爸爸画像
        self.communication_style = CommunicationStyle()
        self.dad_preference = DadPreference()

        # 学习权重
        self.learning_weights = {
            "direct_feedback": 1.0,  # 直接反馈权重
            "implicit_feedback": 0.7,  # 隐式反馈权重
            "behavior_pattern": 0.8,  # 行为模式权重
            "time_pattern": 0.6,  # 时间模式权重
            "content_preference": 0.9,  # 内容偏好权重
        }

        # 初始化
        self._load_learning_data()

    def _load_learning_data(self) -> Any:
        """加载学习数据"""
        try:
            if os.path.exists(self.learning_data_path):
                with open(self.learning_data_path, "rb") as f:
                    data = pickle.load(f)
                    self.learning_history = data.get("history", deque(maxlen=1000))
                    self.patterns = data.get("patterns", {})
                    print("✅ 成功加载学习数据")
            else:
                print("📝 创建新的学习数据")
        except Exception as e:
            print(f"❌ 加载学习数据失败: {e}")

        try:
            if os.path.exists(self.profile_path):
                with open(self.profile_path, encoding="utf-8") as f:
                    profile = json.load(f)
                    self.communication_style = CommunicationStyle(
                        **profile.get("communication", {})
                    )
                    self.dad_preference = DadPreference(**profile.get("preference", {}))
                    print("✅ 成功加载爸爸画像")
            else:
                print("📝 创建新的爸爸画像")
        except Exception as e:
            print(f"❌ 加载爸爸画像失败: {e}")

    def learn_from_interaction(
        self,
        interaction: dict[str, Any],        dad_response: str | None = None,
        satisfaction_score: float | None = None,
    ):
        """从交互中学习"""
        # 创建学习实例
        instance = LearningInstance(
            timestamp=datetime.now(),
            context=interaction.get("context", "unknown"),
            observation=interaction.get("observation", ""),
            pattern=interaction.get("pattern", ""),
            confidence=interaction.get("confidence", 0.5),
            category=interaction.get("category", "general"),
            impact_score=0.0,
        )

        # 计算影响分数
        if satisfaction_score is not None:
            instance.impact_score = abs(satisfaction_score - 0.5) * 2  # 0-1之间
        elif dad_response:
            # 从爸爸回应中推断满意度
            instance.impact_score = self._infer_satisfaction(dad_response)

        # 更新学习历史
        self.learning_history.append(instance)

        # 更新模式
        self._update_patterns(instance)

        # 更新交流风格
        if instance.category == "communication":
            self._update_communication_style(interaction)

        # 更新偏好
        if instance.category == "preference":
            self._update_preferences(interaction)

        # 保存学习数据
        if len(self.learning_history) % 10 == 0:
            self._save_learning_data()

    def _infer_satisfaction(self, response: str) -> float:
        """从回应推断满意度"""
        positive_keywords = ["好", "棒", "不错", "可以", "满意", "赞", "厉害"]
        negative_keywords = ["不好", "差", "不行", "糟糕", "失望", "烦", "错"]

        positive_count = sum(1 for word in positive_keywords if word in response)
        negative_count = sum(1 for word in negative_keywords if word in response)

        if positive_count > negative_count:
            return 0.7 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            return 0.3 - (negative_count - positive_count) * 0.1
        else:
            return 0.5

    def _update_patterns(self, instance: LearningInstance) -> Any:
        """更新模式"""
        pattern_key = f"{instance.category}:{instance.pattern}"
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = {
                "count": 0,
                "total_confidence": 0,
                "total_impact": 0,
                "examples": [],
            }

        pattern = self.patterns[pattern_key]
        pattern["count"] += 1
        pattern["total_confidence"] += instance.confidence
        pattern["total_impact"] += instance.impact_score

        if len(pattern["examples"]) < 5:
            pattern["examples"].append(
                {
                    "timestamp": instance.timestamp.isoformat(),
                    "observation": instance.observation,
                    "confidence": instance.confidence,
                    "impact": instance.impact_score,
                }
            )

        # 更新平均置信度和影响
        pattern["avg_confidence"] = pattern["total_confidence"] / pattern["count"]
        pattern["avg_impact"] = pattern["total_impact"] / pattern["count"]

    def _update_communication_style(self, interaction: dict[str, Any]) -> Any:
        """更新交流风格"""
        style_updates = interaction.get("style_updates", {})
        for key, value in style_updates.items():
            if hasattr(self.communication_style, key):
                current_value = getattr(self.communication_style, key)
                # 使用加权平均更新
                if isinstance(current_value, (int, float)):
                    setattr(self.communication_style, key, (current_value * 0.8 + value * 0.2))
                else:
                    setattr(self.communication_style, key, value)

    def _update_preferences(self, interaction: dict[str, Any]) -> Any:
        """更新偏好"""
        pref_updates = interaction.get("preference_updates", {})
        for category, value in pref_updates.items():
            if hasattr(self.dad_preference, category):
                current_value = getattr(self.dad_preference, category)
                # 对于字典类型的偏好,需要特殊处理
                if isinstance(current_value, dict) and isinstance(value, dict):
                    for k, v in value.items():
                        current_value[k] = current_value.get(k, 0.5) * 0.8 + v * 0.2
                else:
                    setattr(self.dad_preference, category, value)

    def adapt_response(self, base_response: str, context: dict[str, Any] | None = None) -> str:
        """根据学习结果调整回应"""
        adapted_response = base_response

        # 根据交流风格调整
        if self.communication_style.preferred_tone == "温暖贴心":
            adapted_response = self._add_warmth(adapted_response)
        elif self.communication_style.preferred_tone == "专业高效":
            adapted_response = self._add_professionalism(adapted_response)

        # 调整回应长度
        if self.communication_style.response_length == "简短":
            adapted_response = self._shorten_response(adapted_response)
        elif self.communication_style.response_length == "详细":
            adapted_response = self._elaborate_response(adapted_response)

        # 添加表情
        if self.communication_style.emoji_usage > 0.5:
            adapted_response = self._add_emojis(adapted_response)

        return adapted_response

    def _add_warmth(self, text: str) -> str:
        """添加温暖感"""
        warmth_prefixes = ["爸爸,", "亲爱的爸爸,", "嗯,"]
        warmth_suffixes = ["💕", "～", "哦!"]

        if not any(text.startswith(p) for p in warmth_prefixes):
            text = "爸爸," + text

        if not any(text.endswith(s) for s in warmth_suffixes):
            text = text + "～"

        return text

    def _add_professionalism(self, text: str) -> str:
        """添加专业性"""
        # 移除过多的情感表达
        text = text.replace("～", "")
        text = text.replace("💕", "")
        text = text.replace("哇!", "")

        # 添加专业术语
        if "分析" not in text and "建议" in text:
            text = text.replace("建议", "专业建议")

        return text

    def _shorten_response(self, text: str) -> str:
        """缩短回应"""
        sentences = text.split("。")
        if len(sentences) > 2:
            return "。".join(sentences[:2]) + "。"
        return text

    def _elaborate_response(self, text: str) -> str:
        """详细阐述"""
        # 添加额外说明
        if len(text) < 50:
            text += " 这是我基于专业知识得出的结论。"
        return text

    def _add_emojis(self, text: str) -> str:
        """添加表情"""
        if not any(c in text for c in ["😊", "💕", "🌸", "✨", "🎯"]):
            if "好" in text:
                text += " 😊"
            elif "重要" in text:
                text += " 🎯"
            else:
                text += " 💕"
        return text

    def get_learning_summary(self) -> dict[str, Any]:
        """获取学习总结"""
        total_instances = len(self.learning_history)

        if total_instances == 0:
            return {"message": "暂无学习数据"}

        # 按类别统计
        category_counts = defaultdict(int)
        category_impacts = defaultdict(float)
        recent_learning = []

        for instance in self.learning_history:
            category_counts[instance.category] += 1
            category_impacts[instance.category] += instance.impact_score

            if instance.timestamp > datetime.now() - timedelta(days=7):
                recent_learning.append(instance)

        # 找出最重要的学习
        top_patterns = sorted(
            [(k, v) for k, v in self.patterns.items()],
            key=lambda x: x[1]["avg_impact"],
            reverse=True,
        )[:5]

        return {
            "total_learning_instances": total_instances,
            "learning_by_category": dict(category_counts),
            "avg_impact_by_category": {
                cat: imp / category_counts[cat] for cat, imp in category_impacts.items()
            },
            "recent_learning_7_days": len(recent_learning),
            "top_patterns": top_patterns,
            "communication_style": {
                "preferred_tone": self.communication_style.preferred_tone,
                "response_length": self.communication_style.response_length,
                "formality_level": self.communication_style.formality_level,
            },
            "main_interests": sorted(
                self.dad_preference.topic_interests.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    def predict_response_satisfaction(
        self, response: str, context: dict[str, Any] | None = None
    ) -> float:
        """预测回应满意度"""
        satisfaction_score = 0.5  # 基础分数

        # 根据学习的历史模式调整
        relevant_patterns = [
            pattern for pattern in self.patterns.values() if pattern["avg_confidence"] > 0.7
        ]

        if relevant_patterns:
            # 使用最相关的模式调整预测
            avg_impact = sum(p["avg_impact"] for p in relevant_patterns) / len(relevant_patterns)
            satisfaction_score = 0.5 + (avg_impact - 0.5) * 0.3

        # 根据交流风格调整
        style_match = self._calculate_style_match(response)
        satisfaction_score += style_match * 0.2

        # 根据内容偏好调整
        if context and "topic" in context:
            topic_interest = self.dad_preference.topic_interests.get(context["topic"], 0.5)
            satisfaction_score += (topic_interest - 0.5) * 0.3

        return max(0, min(1, satisfaction_score))

    def _calculate_style_match(self, response: str) -> float:
        """计算风格匹配度"""
        match_score = 0.5

        # 检查长度匹配
        response_length = len(response)
        if (self.communication_style.response_length == "简短" and response_length < 50) or (self.communication_style.response_length == "详细" and response_length > 100) or (self.communication_style.response_length == "适中" and 50 <= response_length <= 100):
            match_score += 0.2

        # 检查表情使用
        emoji_count = sum(1 for c in response if ord(c) > 127 and c not in ",。!?:;")
        if (self.communication_style.emoji_usage > 0.5 and emoji_count > 0) or (self.communication_style.emoji_usage < 0.5 and emoji_count == 0):
            match_score += 0.1

        return match_score

    def _save_learning_data(self) -> Any:
        """保存学习数据"""
        try:
            os.makedirs(os.path.dirname(self.learning_data_path), exist_ok=True)
            data = {
                "history": list(self.learning_history),
                "patterns": self.patterns,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.learning_data_path, "wb") as f:
                pickle.dump(data, f)

            # 同时保存爸爸画像
            profile_data = {
                "communication": self.communication_style.__dict__,
                "preference": self.dad_preference.__dict__,
                "last_updated": datetime.now().isoformat(),
            }
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ 保存学习数据失败: {e}")

    def get_active_hours(self) -> list[int]:
        """获取爸爸活跃时段"""
        return self.dad_preference.active_hours

    def get_topic_interests(self) -> dict[str, float]:
        """获取话题兴趣度"""
        return self.dad_preference.topic_interests

    def update_topic_interest(self, topic: str, delta: float) -> None:
        """更新话题兴趣度"""
        current = self.dad_preference.topic_interests.get(topic, 0.5)
        new_interest = max(0, min(1, current + delta))
        self.dad_preference.topic_interests[topic] = new_interest


# 导出主类
__all__ = [
    "CommunicationStyle",
    "DadPreference",
    "LearningInstance",
    "LearningPath",
    "PersonalizedLearningSystem",
    "UserProfile",
    "XiaonuoPersonalizedLearning",
]


# 为保持兼容性，提供 PersonalizedLearningSystem 作为 XiaonuoPersonalizedLearning 的别名
PersonalizedLearningSystem = XiaonuoPersonalizedLearning


@dataclass
class UserProfile:
    """用户画像"""

    user_id: str
    name: str = ""
    interests: list[str] = field(default_factory=list)
    expertise_level: str = "intermediate"
    learning_style: str = "balanced"
    preferred_response_length: str = "medium"
    preferred_tone: str = "professional"
    interaction_history: list[dict] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LearningPath:
    """学习路径"""

    path_id: str
    user_id: str
    skill_domain: str
    current_level: str
    target_level: str
    milestones: list[dict] = field(default_factory=list)
    estimated_duration: int = 0
    resources: list[str] = field(default_factory=list)
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
