#!/usr/bin/env python3
"""
上下文分析器
Context Analyzer

分析对话上下文，理解深层意图

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import logging
from datetime import datetime
from typing import Any

from core.async_main import async_main

logger = logging.getLogger(__name__)

class ContextAnalyzer:
    """上下文分析器"""

    def __init__(self):
        """初始化上下文分析器"""
        self.session_context = {}
        self.user_profiles = {}

    async def analyze(self, text: str, context: dict | None = None) -> dict[str, Any]:
        """
        分析文本上下文

        Args:
            text: 输入文本
            context: 上下文信息

        Returns:
            分析结果
        """
        try:
            # 分析对话历史
            conversation_context = await self._analyze_conversation_history(context)

            # 分析用户状态
            user_state = await self._analyze_user_state(context)

            # 分析业务上下文
            business_context = await self._analyze_business_context(text, context)

            # 分析时间上下文
            temporal_context = await self._analyze_temporal_context(context)

            # 分析情感上下文
            emotional_context = await self._analyze_emotional_context(text, context)

            return {
                "conversation": conversation_context,
                "user_state": user_state,
                "business": business_context,
                "temporal": temporal_context,
                "emotional": emotional_context,
                "summary": self._generate_context_summary(
                    conversation_context, user_state, business_context
                )
            }

        except Exception as e:
            logger.error(f"上下文分析失败: {str(e)}")
            return {"error": str(e)}

    async def _analyze_conversation_history(self, context: dict | None) -> dict[str, Any]:
        """分析对话历史"""
        if not context:
            return {"type": "new_conversation", "depth": 0}

        history = context.get("conversation_history", [])
        if not history:
            return {"type": "new_conversation", "depth": 0}

        # 分析对话深度
        depth = len(history)
        last_topic = history[-1].get("topic", "") if history else ""
        topic_continuity = self._check_topic_continuity(history)

        return {
            "type": "ongoing_conversation",
            "depth": depth,
            "last_topic": last_topic,
            "topic_continuity": topic_continuity,
            "turn_count": depth
        }

    async def _analyze_user_state(self, context: dict | None) -> dict[str, Any]:
        """分析用户状态"""
        if not context:
            return {"status": "unknown"}

        user_id = context.get("user_id", "anonymous")

        # 获取用户历史
        user_history = self.user_profiles.get(user_id, {})

        # 分析用户熟悉度
        familiarity = self._assess_user_familiarity(user_history)

        # 分析用户偏好
        preferences = user_history.get("preferences", {})

        # 分析用户活跃度
        activity = user_history.get("activity", {})

        return {
            "user_id": user_id,
            "familiarity": familiarity,
            "preferences": preferences,
            "activity": activity,
            "status": "identified" if user_id != "anonymous" else "anonymous"
        }

    async def _analyze_business_context(self, text: str, context: dict | None) -> dict[str, Any]:
        """分析业务上下文"""
        business_context = {
            "domain": "general",
            "stage": "initial",
            "related_cases": [],
            "legal_framework": []
        }

        # 从上下文中提取业务信息
        if context:
            # 检查是否有相关的业务记录
            if "ongoing_cases" in context:
                business_context["related_cases"] = context["ongoing_cases"]

            # 检查是否有相关的法律框架
            if "legal_framework" in context:
                business_context["legal_framework"] = context["legal_framework"]

            # 确定业务阶段
            if "previous_actions" in context:
                actions = context["previous_actions"]
                if "drafting" in actions:
                    business_context["stage"] = "drafting"
                elif "reviewing" in actions:
                    business_context["stage"] = "reviewing"
                elif "filing" in actions:
                    business_context["stage"] = "filing"

        return business_context

    async def _analyze_temporal_context(self, context: dict | None) -> dict[str, Any]:
        """分析时间上下文"""
        temporal_context = {
            "current_time": datetime.now().isoformat(),
            "urgency": "normal",
            "deadlines": [],
            "time_sensitivity": "low"
        }

        if context:
            # 检查截止日期
            if "deadlines" in context:
                temporal_context["deadlines"] = context["deadlines"]

                # 计算紧急程度
                for deadline in context["deadlines"]:
                    deadline_date = datetime.fromisoformat(deadline)
                    time_remaining = deadline_date - datetime.now()

                    if time_remaining.days < 1:
                        temporal_context["urgency"] = "critical"
                        temporal_context["time_sensitivity"] = "high"
                    elif time_remaining.days < 7:
                        temporal_context["urgency"] = "high"
                        temporal_context["time_sensitivity"] = "medium"

            # 检查工作时间
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 18:
                temporal_context["business_hours"] = True
            else:
                temporal_context["business_hours"] = False

        return temporal_context

    async def _analyze_emotional_context(self, text: str, context: dict | None) -> dict[str, Any]:
        """分析情感上下文"""
        emotional_context = {
            "sentiment": "neutral",
            "stress_level": "low",
            "confidence": "neutral",
            "emotional_indicators": []
        }

        # 分析文本情感
        stress_keywords = ["担心", "焦虑", "着急", "紧急", "怕", "愁"]
        positive_keywords = ["满意", "开心", "感谢", "好", "顺利"]
        negative_keywords = ["糟糕", "失败", "拒绝", "不行", "问题"]

        text_lower = text.lower()

        # 计算情感指标
        stress_count = sum(1 for word in stress_keywords if word in text_lower)
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)

        if stress_count > 2:
            emotional_context["stress_level"] = "high"
            emotional_context["emotional_indicators"].append("stressed")
        elif stress_count > 0:
            emotional_context["stress_level"] = "medium"
            emotional_context["emotional_indicators"].append("concerned")

        if positive_count > negative_count:
            emotional_context["sentiment"] = "positive"
        elif negative_count > positive_count:
            emotional_context["sentiment"] = "negative"
            emotional_context["emotional_indicators"].append("negative")

        return emotional_context

    def _check_topic_continuity(self, history: list[dict]) -> bool:
        """检查话题连续性"""
        if len(history) < 2:
            return True

        # 简化实现：检查最后两次对话的主题
        last_topic = history[-1].get("topic", "")
        prev_topic = history[-2].get("topic", "")

        return last_topic == prev_topic

    def _assess_user_familiarity(self, user_history: dict) -> str:
        """评估用户熟悉度"""
        interaction_count = user_history.get("interaction_count", 0)
        user_history.get("last_interaction")

        if interaction_count > 10:
            return "expert"
        elif interaction_count > 3:
            return "familiar"
        elif interaction_count > 0:
            return "novice"
        else:
            return "new"

    def _generate_context_summary(self, conversation: dict, user_state: dict, business: dict) -> str:
        """生成上下文摘要"""
        summary_parts = []

        if conversation["type"] == "ongoing_conversation":
            summary_parts.append(f"对话深度: {conversation['depth']}")

        if user_state.get("status") == "identified":
            summary_parts.append(f"用户熟悉度: {user_state.get('familiarity', 'unknown')}")

        if business.get("stage") != "initial":
            summary_parts.append(f"业务阶段: {business['stage']}")

        return ", ".join(summary_parts) if summary_parts else "新对话"

    def update_context(self, user_id: str, interaction: dict) -> None:
        """更新上下文"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "interaction_count": 0,
                "preferences": {},
                "activity": {},
                "last_interaction": None
            }

        profile = self.user_profiles[user_id]
        profile["interaction_count"] += 1
        profile["last_interaction"] = datetime.now().isoformat()

        # 更新活动记录
        activity = profile["activity"]
        today = datetime.now().date().isoformat()
        if today not in activity:
            activity[today] = 0
        activity[today] += 1

# 使用示例
@async_main
async def main():
    """测试上下文分析器"""
    analyzer = ContextAnalyzer()

    # 模拟上下文
    context = {
        "user_id": "user123",
        "conversation_history": [
            {"topic": "patent", "content": "我想申请专利"},
            {"topic": "patent", "content": "技术方案是AI相关的"}
        ],
        "ongoing_cases": ["patent_001"],
        "deadlines": ["2024-12-20T00:00:00"]
    }

    text = "我担心专利申请来不及了"
    result = await analyzer.analyze(text, context)

    print("上下文分析结果:")
    print(f"情感状态: {result['emotional']['sentiment']}")
    print(f"压力水平: {result['emotional']['stress_level']}")
    print(f"紧急程度: {result['temporal']['urgency']}")
    print(f"摘要: {result['summary']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
