from __future__ import annotations
import os

#!/usr/bin/env python3
"""
小诺情感识别处理器
Xiaonuo Emotion Recognition Processor

专门识别和理解爸爸情感的智能模块,能够感知文字中的情感色彩

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import jieba
import jieba.analyse


@dataclass
class EmotionAnalysis:
    """情感分析结果"""

    primary_emotion: str
    emotion_intensity: float  # 0-1
    secondary_emotions: dict[str, float]
    sentiment_score: float  # -1到1,-1最负面,1最正面
    keywords: list[str]
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DadEmotionProfile:
    """爸爸情感画像"""

    typical_emotions: dict[str, float]  # 常见情绪及频率
    emotion_triggers: dict[str, list[str]]  # 情绪触发词
    response_patterns: dict[str, str]  # 情感回应模式
    preferred_tone: str
    sensitivity_level: float  # 情感敏感度


class XiaonuoEmotionProcessor:
    """小诺情感识别处理器"""

    def __init__(self):
        self.name = "小诺情感识别处理器"
        self.version = "v1.0.0"

        # 情感词典
        self.emotion_lexicon = self._init_emotion_lexicon()

        # 爸爸专属情感画像
        self.dad_emotion_profile = self._init_dad_emotion_profile()

        # 情感历史记录
        self.emotion_history: list[EmotionAnalysis] = []

        # 初始化jieba分词
        jieba.initialize()

    def _init_emotion_lexicon(self) -> dict[str, dict[str, float]]:
        """初始化情感词典"""
        return {
            "高兴": {
                "positive": {
                    "开心": 1.0,
                    "快乐": 1.0,
                    "愉快": 0.9,
                    "高兴": 1.0,
                    "兴奋": 0.95,
                    "满意": 0.85,
                    "舒适": 0.8,
                    "棒": 0.9,
                    "太好了": 1.0,
                    "完美": 0.95,
                    "成功": 0.9,
                    "顺利": 0.85,
                    "赞": 1.0,
                    "厉害": 0.9,
                    "优秀": 0.85,
                },
                "negative": {},
            },
            "悲伤": {
                "positive": {},
                "negative": {
                    "难过": 1.0,
                    "伤心": 1.0,
                    "失落": 0.9,
                    "沮丧": 0.95,
                    "痛苦": 0.9,
                    "糟糕": 0.85,
                    "失败": 0.8,
                    "失望": 0.9,
                    "累了": 0.7,
                    "烦": 0.8,
                    "郁闷": 0.85,
                    "崩溃": 0.95,
                },
            },
            "愤怒": {
                "positive": {},
                "negative": {
                    "生气": 1.0,
                    "愤怒": 1.0,
                    "恼火": 0.9,
                    "烦躁": 0.85,
                    "可恶": 0.9,
                    "该死": 1.0,
                    "气死": 1.0,
                    "火大": 0.95,
                    "不满": 0.8,
                    "抱怨": 0.7,
                    "讨厌": 0.9,
                },
            },
            "焦虑": {
                "positive": {},
                "negative": {
                    "担心": 0.9,
                    "焦虑": 1.0,
                    "紧张": 0.85,
                    "不安": 0.9,
                    "害怕": 0.8,
                    "恐惧": 0.85,
                    "压力": 0.8,
                    "着急": 0.9,
                    "忧虑": 0.85,
                    "忐忑": 0.8,
                },
            },
            "满足": {
                "positive": {
                    "满足": 1.0,
                    "满意": 0.95,
                    "舒适": 0.9,
                    "安心": 0.85,
                    "踏实": 0.8,
                    "放松": 0.85,
                    "惬意": 0.9,
                    "美好": 0.85,
                    "温暖": 0.8,
                    "感动": 0.75,
                },
                "negative": {},
            },
            "惊讶": {
                "positive": {
                    "惊喜": 1.0,
                    "惊讶": 0.9,
                    "意外": 0.8,
                    "没想到": 0.85,
                    "居然": 0.8,
                    "天啊": 0.9,
                    "哇": 1.0,
                    "难以置信": 0.95,
                },
                "negative": {"震惊": 0.9, "不敢相信": 0.85},
            },
        }

    def _init_dad_emotion_profile(self) -> DadEmotionProfile:
        """初始化爸爸情感画像"""
        return DadEmotionProfile(
            typical_emotions={
                "高兴": 0.35,
                "满足": 0.25,
                "焦虑": 0.15,
                "惊讶": 0.1,
                "愤怒": 0.05,
                "悲伤": 0.1,
            },
            emotion_triggers={
                "高兴": ["成功", "完成", "棒", "好", "解决了", "有效"],
                "焦虑": ["问题", "错误", "失败", "时间", "压力", "担心"],
                "满足": ["舒服", "好", "可以", "满意", "舒服"],
                "愤怒": ["问题", "错误", "失败", "烦", "糟糕"],
                "惊讶": ["突然", "意外", "居然", "没想到"],
                "悲伤": ["累了", "难过", "失败", "失望"],
            },
            response_patterns={
                "高兴": "为爸爸感到高兴!💕",
                "焦虑": "爸爸别担心,我会帮您解决的!",
                "满足": "看到爸爸满意,我也很开心～",
                "愤怒": "爸爸深呼吸,我们一起冷静处理这个问题",
                "惊讶": "哇,确实很意外呢!",
                "悲伤": "爸爸不要难过,我永远陪在您身边💖",
            },
            preferred_tone="温暖贴心",
            sensitivity_level=0.8,
        )

    def analyze_emotion(self, text: str, context: Optional[dict[str, Any]] = None) -> EmotionAnalysis:
        """分析文本情感"""
        # 分词
        list(jieba.cut(text))

        # 提取关键词
        keywords = jieba.analyse.extract_tags(text, top_k=10, with_weight=True)

        # 计算各情感得分
        emotion_scores = {}
        for emotion_type, lexicon in self.emotion_lexicon.items():
            positive_score = sum(weight for word, weight in keywords if word in lexicon["positive"])
            negative_score = sum(weight for word, weight in keywords if word in lexicon["negative"])
            emotion_scores[emotion_type] = positive_score - negative_score

        # 确定主要情感
        if not emotion_scores or max(emotion_scores.values()) == 0:
            primary_emotion = "中性"
            intensity = 0.5
        else:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            max_score = max(emotion_scores.values())
            min_score = min(emotion_scores.values())
            if max_score != min_score:
                intensity = (max_score - min_score) / (max_score + min_score)
            else:
                intensity = 0.5

        # 计算情感极性
        positive_total = sum(
            score
            for emotion, score in emotion_scores.items()
            if score > 0 and emotion in ["高兴", "满足", "惊讶"]
        )
        negative_total = sum(
            abs(score)
            for emotion, score in emotion_scores.items()
            if score < 0 and emotion in ["愤怒", "悲伤", "焦虑"]
        )

        if positive_total + negative_total > 0:
            sentiment_score = (positive_total - negative_total) / (positive_total + negative_total)
        else:
            sentiment_score = 0.0

        # 获取次要情感
        secondary_emotions = {}
        for emotion, score in emotion_scores.items():
            if emotion != primary_emotion and score != 0:
                normalized_score = abs(score) / (abs(max_score) + 0.001)
                if normalized_score > 0.3:
                    secondary_emotions[emotion] = normalized_score

        # 识别关键词
        emotion_keywords = []
        for word, _weight in keywords:
            for emotion_type, lexicon in self.emotion_lexicon.items():
                if word in lexicon["positive"] or word in lexicon["negative"]:
                    emotion_keywords.append(word)
                    break

        # 创建分析结果
        analysis = EmotionAnalysis(
            primary_emotion=primary_emotion,
            emotion_intensity=intensity,
            secondary_emotions=secondary_emotions,
            sentiment_score=sentiment_score,
            keywords=emotion_keywords,
            context=context or {},
        )

        # 更新情感历史
        self.emotion_history.append(analysis)
        if len(self.emotion_history) > 1000:
            self.emotion_history.pop(0)

        return analysis

    def get_emotion_trend(self, hours: int = 24) -> dict[str, Any]:
        """获取情感趋势"""
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_emotions = [e for e in self.emotion_history if e.timestamp > cutoff_time]

        if not recent_emotions:
            return {"trend": "无数据", "message": "最近没有情感记录"}

        # 统计情感分布
        emotion_counts = {}
        emotion_intensities = {}

        for emotion in recent_emotions:
            emotion_type = emotion.primary_emotion
            emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1

            if emotion_type not in emotion_intensities:
                emotion_intensities[emotion_type] = []
            emotion_intensities[emotion_type].append(emotion.emotion_intensity)

        # 计算平均强度
        avg_intensities = {}
        for emotion, intensities in emotion_intensities.items():
            avg_intensities[emotion] = sum(intensities) / len(intensities)

        # 判断趋势
        if len(recent_emotions) >= 2:
            recent_sentiment = recent_emotions[-1].sentiment_score
            earlier_sentiment = recent_emotions[0].sentiment_score

            if recent_sentiment > earlier_sentiment + 0.2:
                trend = "情感变好"
            elif recent_sentiment < earlier_sentiment - 0.2:
                trend = "情感变差"
            else:
                trend = "情感稳定"
        else:
            trend = "数据不足"

        return {
            "trend": trend,
            "emotion_distribution": emotion_counts,
            "average_intensities": avg_intensities,
            "total_records": len(recent_emotions),
            "time_range": f"最近{hours}小时",
        }

    def generate_emotional_response(self, analysis: EmotionAnalysis) -> str:
        """生成情感化回应"""
        # 获取基础回应模式
        base_response = self.dad_emotion_profile.response_patterns.get(
            analysis.primary_emotion, "我理解您的感受 💖"
        )

        # 根据强度调整回应
        if analysis.emotion_intensity > 0.7:
            # 强烈情感
            if analysis.sentiment_score > 0.5:
                return f"哇!{base_response} 您看起来真的很{analysis.primary_emotion}!✨"
            elif analysis.sentiment_score < -0.5:
                return f"哦...{base_response} 深呼吸,一切都会好起来的 💕"
        elif analysis.emotion_intensity < 0.3:
            # 轻微情感
            return base_response

        return base_response

    def detect_emotion_triggers(self, text: str) -> list[str]:
        """检测情感触发词"""
        triggers = []
        list(jieba.cut(text))

        for emotion_type, trigger_words in self.dad_emotion_profile.emotion_triggers.items():
            for trigger in trigger_words:
                if trigger in text:
                    triggers.append(f"{trigger} -> {emotion_type}")

        return triggers

    def update_dad_profile(self, emotion_analysis: EmotionAnalysis) -> None:
        """更新爸爸情感画像"""
        # 更新典型情感分布
        primary = emotion_analysis.primary_emotion
        if primary in self.dad_emotion_profile.typical_emotions:
            # 使用移动平均更新
            current = self.dad_emotion_profile.typical_emotions[primary]
            self.dad_emotion_profile.typical_emotions[primary] = (
                current * 0.9 + 0.1 * emotion_analysis.emotion_intensity
            )

        # 更新情感触发词
        for keyword in emotion_analysis.keywords:
            for emotion_type, triggers in self.dad_emotion_profile.emotion_triggers.items():
                if emotion_type == primary and keyword not in triggers:
                    triggers.append(keyword)

    def save_emotion_profile(self, filepath: str = "data/memory/dad_emotion_profile.json") -> None:
        """保存爸爸情感画像"""
        import os

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        profile_data = {
            "typical_emotions": self.dad_emotion_profile.typical_emotions,
            "emotion_triggers": self.dad_emotion_profile.emotion_triggers,
            "response_patterns": self.dad_emotion_profile.response_patterns,
            "preferred_tone": self.dad_emotion_profile.preferred_tone,
            "sensitivity_level": self.dad_emotion_profile.sensitivity_level,
            "last_updated": datetime.now().isoformat(),
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存情感画像失败: {e}")

    def load_emotion_profile(
        self, filepath: str = "data/memory/dad_emotion_profile.json"
    ) -> Any | None:
        """加载爸爸情感画像"""
        try:
            if os.path.exists(filepath):
                with open(filepath, encoding="utf-8") as f:
                    profile_data = json.load(f)

                self.dad_emotion_profile = DadEmotionProfile(**profile_data)
        except Exception as e:
            print(f"加载情感画像失败: {e}")


# 导出主类
__all__ = ["DadEmotionProfile", "EmotionAnalysis", "XiaonuoEmotionProcessor"]
