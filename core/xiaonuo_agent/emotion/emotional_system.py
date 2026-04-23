#!/usr/bin/env python3
from __future__ import annotations
"""
情感系统 (Emotional System)
基于PAD三维情感模型的情感状态管理系统

核心思想:
1. PAD模型:愉悦度(Pleasure)、激活度(Arousal)、优势度(Dominance)
2. 情感动态:根据外部刺激更新情感状态
3. 情感衰减:情感随时间自然衰减
4. 情感表达:将情感状态转化为可理解的描述

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EmotionCategory(Enum):
    """情感类别"""

    # 积极情感
    HAPPY = "happy"  # 快乐
    EXCITED = "excited"  # 兴奋
    CONFIDENT = "confident"  # 自信
    SATISFIED = "satisfied"  # 满意
    GRATEFUL = "grateful"  # 感激

    # 消极情感
    SAD = "sad"  # 悲伤
    ANGRY = "angry"  # 愤怒
    ANXIOUS = "anxious"  # 焦虑
    FRUSTRATED = "frustrated"  # 沮丧
    DISAPPOINTED = "disappointed"  # 失望

    # 中性情感
    CALM = "calm"  # 平静
    NEUTRAL = "neutral"  # 中性
    SURPRISED = "surprised"  # 惊讶
    CURIOUS = "curious"  # 好奇


class StimulusType(Enum):
    """刺激类型"""

    SUCCESS = "success"  # 成功刺激
    FAILURE = "failure"  # 失败刺激
    PRAISE = "praise"  # 赞美刺激
    CRITICISM = "criticism"  # 批评刺激
    CHALLENGE = "challenge"  # 挑战刺激
    HELP = "help"  # 帮助刺激
    NEW_INFO = "new_info"  # 新信息刺激
    REPEAT = "repeat"  # 重复刺激(疲劳)


@dataclass
class EmotionalState:
    """情感状态(PAD三维)"""

    pleasure: float = 0.0  # 愉悦度: -1.0 (痛苦) ~ 1.0 (快乐)
    arousal: float = 0.0  # 激活度: -1.0 (平静) ~ 1.0 (兴奋)
    dominance: float = 0.0  # 优势度: -1.0 (弱势) ~ 1.0 (强势)

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    decay_rate: float = 0.95  # 情感衰减率(每小时)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "pleasure": round(self.pleasure, 3),
            "arousal": round(self.arousal, 3),
            "dominance": round(self.dominance, 3),
            "timestamp": self.timestamp,
            "category": self.categorize().value,
        }

    def categorize(self) -> EmotionCategory:
        """
        将PAD值映射为情感类别

        映射规则(基于PAD情感模型研究):
        - 高P+高A+高D: 快乐/兴奋
        - 高P+低A+高D: 自信/满意
        - 低P+高A+高D: 愤怒
        - 低P+低A+低D: 悲伤
        - 中P+高A+中D: 惊讶/好奇
        - 中P+低A+中D: 平静
        """
        p, a, d = self.pleasure, self.arousal, self.dominance

        # 高愉悦度
        if p > 0.3:
            if a > 0.3:
                return EmotionCategory.EXCITED if d > 0 else EmotionCategory.HAPPY
            else:
                return EmotionCategory.CONFIDENT if d > 0 else EmotionCategory.SATISFIED

        # 低愉悦度
        elif p < -0.3:
            if a > 0.3:
                return EmotionCategory.ANGRY if d > 0 else EmotionCategory.ANXIOUS
            else:
                return EmotionCategory.FRUSTRATED if d > 0 else EmotionCategory.SAD

        # 中性区域
        else:
            if abs(a) > 0.5:
                return EmotionCategory.SURPRISED if a > 0 else EmotionCategory.CALM
            elif abs(a) > 0.3:
                return EmotionCategory.CURIOUS
            else:
                return EmotionCategory.NEUTRAL

    def decay(self, hours: float = 1.0):
        """情感衰减"""
        decay_factor = self.decay_rate**hours
        self.pleasure *= decay_factor
        self.arousal *= decay_factor
        self.dominance *= decay_factor
        self.timestamp = datetime.now().isoformat()

    def distance_to(self, other: EmotionalState) -> float:
        """计算与另一个情感状态的距离(欧氏距离)"""
        return math.sqrt(
            (self.pleasure - other.pleasure) ** 2
            + (self.arousal - other.arousal) ** 2
            + (self.dominance - other.dominance) ** 2
        )


@dataclass
class EmotionalTrigger:
    """情感触发器"""

    stimulus_type: StimulusType
    intensity: float  # 刺激强度: 0.0 ~ 1.0
    pleasure_delta: float  # 愉悦度变化
    arousal_delta: float  # 激活度变化
    dominance_delta: float  # 优势度变化

    context: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EmotionalSystem:
    """
    情感系统 - PAD三维情感模型

    核心功能:
    1. 情感状态跟踪(PAD三维)
    2. 情感动态更新(基于外部刺激)
    3. 情感衰减(随时间自然衰减)
    4. 情感表达(转换为可理解描述)
    5. 情感调节(自我调节机制)

    PAD模型说明:
    - Pleasure (愉悦度): 情感的正负性,-1(痛苦) ~ 1(快乐)
    - Arousal (激活度): 情感的强烈程度,-1(平静) ~ 1(兴奋)
    - Dominance (优势度): 控制感/主动性,-1(弱势) ~ 1(强势)
    """

    # 预定义的情感触发器(基于心理学研究)
    PREDEFINED_TRIGGERS = {
        StimulusType.SUCCESS: EmotionalTrigger(
            stimulus_type=StimulusType.SUCCESS,
            intensity=0.8,
            pleasure_delta=0.5,
            arousal_delta=0.3,
            dominance_delta=0.4,
        ),
        StimulusType.FAILURE: EmotionalTrigger(
            stimulus_type=StimulusType.FAILURE,
            intensity=0.8,
            pleasure_delta=-0.5,
            arousal_delta=0.2,
            dominance_delta=-0.3,
        ),
        StimulusType.PRAISE: EmotionalTrigger(
            stimulus_type=StimulusType.PRAISE,
            intensity=0.6,
            pleasure_delta=0.4,
            arousal_delta=0.1,
            dominance_delta=0.2,
        ),
        StimulusType.CRITICISM: EmotionalTrigger(
            stimulus_type=StimulusType.CRITICISM,
            intensity=0.6,
            pleasure_delta=-0.3,
            arousal_delta=0.3,
            dominance_delta=-0.2,
        ),
        StimulusType.CHALLENGE: EmotionalTrigger(
            stimulus_type=StimulusType.CHALLENGE,
            intensity=0.5,
            pleasure_delta=0.0,
            arousal_delta=0.4,
            dominance_delta=0.1,
        ),
        StimulusType.HELP: EmotionalTrigger(
            stimulus_type=StimulusType.HELP,
            intensity=0.7,
            pleasure_delta=0.3,
            arousal_delta=-0.1,
            dominance_delta=0.3,
        ),
        StimulusType.NEW_INFO: EmotionalTrigger(
            stimulus_type=StimulusType.NEW_INFO,
            intensity=0.4,
            pleasure_delta=0.1,
            arousal_delta=0.2,
            dominance_delta=0.0,
        ),
        StimulusType.REPEAT: EmotionalTrigger(
            stimulus_type=StimulusType.REPEAT,
            intensity=0.3,
            pleasure_delta=-0.1,
            arousal_delta=-0.2,
            dominance_delta=0.0,
        ),
    }

    def __init__(self, initial_state: EmotionalState | None = None, decay_rate: float = 0.95):
        """
        初始化情感系统

        Args:
            initial_state: 初始情感状态
            decay_rate: 情感衰减率(每小时)
        """
        self.current_state = initial_state or EmotionalState()
        self.current_state.decay_rate = decay_rate

        # 情感历史
        self.emotional_history: list[EmotionalState] = [self.current_state]

        # 触发历史
        self.trigger_history: list[EmotionalTrigger] = []

        # 统计信息
        self.stats = {
            "total_triggers": 0,
            "emotion_changes": 0,
            "average_intensity": 0.0,
            "dominant_emotion": EmotionCategory.NEUTRAL,
        }

    async def stimulate(
        self,
        stimulus_type: StimulusType,
        intensity: float = 0.5,
        context: Optional[dict[str, Any]] = None,
    ) -> EmotionalState:
        """
        接受刺激并更新情感状态

        Args:
            stimulus_type: 刺激类型
            intensity: 刺激强度 (0.0 ~ 1.0)
            context: 上下文信息

        Returns:
            更新后的情感状态
        """
        try:
            # 获取预定义触发器或创建新触发器
            if stimulus_type in self.PREDEFINED_TRIGGERS:
                trigger = self.PREDEFINED_TRIGGERS[stimulus_type]
            else:
                # 创建默认触发器
                trigger = EmotionalTrigger(
                    stimulus_type=stimulus_type,
                    intensity=intensity,
                    pleasure_delta=0.0,
                    arousal_delta=0.0,
                    dominance_delta=0.0,
                )
    
            # 应用强度调整
            factor = intensity / trigger.intensity if trigger.intensity > 0 else intensity
            self.current_state.pleasure += trigger.pleasure_delta * factor
            self.current_state.arousal += trigger.arousal_delta * factor
            self.current_state.dominance += trigger.dominance_delta * factor
    
            # 限制范围在[-1, 1]
            self.current_state.pleasure = max(-1.0, min(1.0, self.current_state.pleasure))
            self.current_state.arousal = max(-1.0, min(1.0, self.current_state.arousal))
            self.current_state.dominance = max(-1.0, min(1.0, self.current_state.dominance))
    
            self.current_state.timestamp = datetime.now().isoformat()
    
            # 记录触发历史
            trigger.intensity = intensity
            trigger.context = context or {}
            trigger.timestamp = self.current_state.timestamp
            self.trigger_history.append(trigger)
    
            # 更新历史
            self.emotional_history.append(self.current_state)
    
            # 更新统计
            self.stats["total_triggers"] += 1
            self.stats["emotion_changes"] += len(self.emotional_history) - 1
            self.stats["average_intensity"] = (
                self.stats["average_intensity"] * (self.stats["total_triggers"] - 1) + intensity
            ) / self.stats["total_triggers"]
            self.stats["dominant_emotion"] = self.current_state.categorize()
    
            logger.info(
                f"😊 情感刺激: {stimulus_type.value} (强度={intensity:.2f}) "
                f"-> {self.current_state.categorize().value}"
            )
    
            return self.current_state
        except Exception as e:
            logger.error(f"处理情感刺激异常: {e}", exc_info=True)
            return self.current_state

    async def decay_emotion(self, hours: float = 1.0):
        """
        情感衰减

        Args:
            hours: 衰减时长(小时)
        """
        try:
            old_state = EmotionalState(
                pleasure=self.current_state.pleasure,
                arousal=self.current_state.arousal,
                dominance=self.current_state.dominance,
            )
    
            self.current_state.decay(hours)
            self.emotional_history.append(self.current_state)
    
            distance = old_state.distance_to(self.current_state)
            logger.debug(f"📉 情感衰减: {hours:.1f}小时, 变化={distance:.3f}")
        except Exception as e:
            logger.error(f"情感衰减异常: {e}", exc_info=True)

    def get_current_emotion(self) -> EmotionalState:
        """获取当前情感状态"""
        return self.current_state

    def get_emotion_description(self) -> str:
        """
        获取情感描述

        Returns:
            情感状态的自然语言描述
        """
        category = self.current_state.categorize()

        # PAD值描述
        pleasure_desc = self._describe_pleasure()
        arousal_desc = self._describe_arousal()
        dominance_desc = self._describe_dominance()

        # 组合描述
        descriptions = []
        if pleasure_desc:
            descriptions.append(pleasure_desc)
        if arousal_desc:
            descriptions.append(arousal_desc)
        if dominance_desc:
            descriptions.append(dominance_desc)

        if descriptions:
            base_desc = "、".join(descriptions)
            return f"我感到{base_desc}({self._get_emotion_emoji(category)})"
        else:
            return f"我感到平静({self._get_emotion_emoji(category)})"

    def _describe_pleasure(self) -> str:
        """描述愉悦度"""
        p = self.current_state.pleasure
        if p > 0.6:
            return "非常快乐"
        elif p > 0.3:
            return "愉快"
        elif p > -0.3:
            return None
        elif p > -0.6:
            return "有些不快"
        else:
            return "很不开心"

    def _describe_arousal(self) -> str:
        """描述激活度"""
        a = self.current_state.arousal
        if a > 0.6:
            return "非常兴奋"
        elif a > 0.3:
            return "有些激动"
        elif a > -0.3:
            return None
        elif a > -0.6:
            return "有些疲惫"
        else:
            return "很平静"

    def _describe_dominance(self) -> str:
        """描述优势度"""
        d = self.current_state.dominance
        if d > 0.6:
            return "充满自信"
        elif d > 0.3:
            return "比较有把握"
        elif d > -0.3:
            return None
        elif d > -0.6:
            return "有些不安"
        else:
            return "感到无助"

    def _get_emotion_emoji(self, category: EmotionCategory) -> str:
        """获取情感表情符号"""
        emoji_map = {
            EmotionCategory.HAPPY: "😊",
            EmotionCategory.EXCITED: "🤩",
            EmotionCategory.CONFIDENT: "😎",
            EmotionCategory.SATISFIED: "😌",
            EmotionCategory.GRATEFUL: "🙏",
            EmotionCategory.SAD: "😢",
            EmotionCategory.ANGRY: "😠",
            EmotionCategory.ANXIOUS: "😰",
            EmotionCategory.FRUSTRATED: "😤",
            EmotionCategory.DISAPPOINTED: "😞",
            EmotionCategory.CALM: "😐",
            EmotionCategory.NEUTRAL: "😶",
            EmotionCategory.SURPRISED: "😲",
            EmotionCategory.CURIOUS: "🤔",
        }
        return emoji_map.get(category, "😶")

    def get_emotional_trend(self, window: int = 10) -> dict[str, float]:
        """
        获取情感趋势(最近N个状态)

        Args:
            window: 窗口大小

        Returns:
            趋势数据
        """
        recent_states = self.emotional_history[-window:]

        if len(recent_states) < 2:
            return {"pleasure_trend": 0.0, "arousal_trend": 0.0, "dominance_trend": 0.0}

        # 计算平均变化率
        pleasure_changes = []
        arousal_changes = []
        dominance_changes = []

        for i in range(1, len(recent_states)):
            pleasure_changes.append(recent_states[i].pleasure - recent_states[i - 1].pleasure)
            arousal_changes.append(recent_states[i].arousal - recent_states[i - 1].arousal)
            dominance_changes.append(recent_states[i].dominance - recent_states[i - 1].dominance)

        return {
            "pleasure_trend": sum(pleasure_changes) / len(pleasure_changes),
            "arousal_trend": sum(arousal_changes) / len(arousal_changes),
            "dominance_trend": sum(dominance_changes) / len(dominance_changes),
        }

    def is_emotion_stable(self, threshold: float = 0.1) -> bool:
        """
        判断情感是否稳定

        Args:
            threshold: 稳定性阈值

        Returns:
            是否稳定
        """
        if len(self.emotional_history) < 3:
            return True

        recent = self.emotional_history[-3:]
        max_change = max(
            abs(recent[0].pleasure - recent[-1].pleasure),
            abs(recent[0].arousal - recent[-1].arousal),
            abs(recent[0].dominance - recent[-1].dominance),
        )

        return max_change < threshold

    async def regulate_emotion(self, target: EmotionalState | None = None):
        """
        情感自我调节

        Args:
            target: 目标情感状态(默认为平静状态)
        """
        try:
            if target is None:
                # 默认调节到平静状态
                target = EmotionalState(pleasure=0.0, arousal=0.0, dominance=0.0)
    
            # 逐渐向目标状态靠近
            adjustment_rate = 0.1
            self.current_state.pleasure += (
                target.pleasure - self.current_state.pleasure
            ) * adjustment_rate
            self.current_state.arousal += (
                target.arousal - self.current_state.arousal
            ) * adjustment_rate
            self.current_state.dominance += (
                target.dominance - self.current_state.dominance
            ) * adjustment_rate
    
            self.current_state.timestamp = datetime.now().isoformat()
            self.emotional_history.append(self.current_state)
    
            logger.debug(f"🎯 情感调节: 向 {target.categorize().value} 靠近")
        except Exception as e:
            logger.error(f"情感调节异常: {e}", exc_info=True)

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "current_emotion": self.current_state.categorize().value,
            "current_state": self.current_state.to_dict(),
            "history_length": len(self.emotional_history),
            "is_stable": self.is_emotion_stable(),
            "trend": self.get_emotional_trend(),
        }

    def export_history(self, filepath: str):
        """
        导出情感历史

        Args:
            filepath: 导出文件路径
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "history": [state.to_dict() for state in self.emotional_history],
                    "triggers": [
                        {
                            "type": t.stimulus_type.value,
                            "intensity": t.intensity,
                            "timestamp": t.timestamp,
                            "context": t.context,
                        }
                        for t in self.trigger_history
                    ],
                    "stats": self.stats,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(f"📁 情感历史已导出: {filepath}")


# 便捷函数
async def create_emotional_system(**kwargs) -> EmotionalSystem:
    """创建情感系统"""
    return EmotionalSystem(**kwargs)
