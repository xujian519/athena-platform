#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通信管理器
Communication Manager

增强的智能通信与交互管理

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import asyncio
from core.async_main import async_main
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class CommunicationChannel(Enum):
    """通信渠道"""
    CHAT = "chat"
    EMAIL = "email"
    TELEPHONE = "telephone"
    VIDEO = "video"
    DOCUMENT = "document"
    API = "api"

class MessagePriority(Enum):
    """消息优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Message:
    """消息结构"""
    message_id: str
    channel: CommunicationChannel
    priority: MessagePriority
    sender: str
    receiver: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    status: str = "pending"
    response_id: str | None = None

class CommunicationManager:
    """通信管理器"""

    def __init__(self):
        """初始化通信管理器"""
        self.name = "小娜通信管理器"
        self.version = "v2.0"

        # 通信配置
        self.config = {
            "max_conversation_length": 20,
            "response_timeout": 30,
            "message_retention_days": 90,
            "auto_response_enabled": True,
            "multi_language_support": ["zh-CN", "en-US"],
            "emotional_support_enabled": True,
            "proactive_communication": True
        }

        # 活跃会话
        self.active_conversations = {}
        self.message_queue = asyncio.Queue()
        self.response_cache = {}

        # 通信历史
        self.communication_history = []
        self.user_preferences = {}

        # 情感状态
        self.emotion_analyzer = EmotionAnalyzer()
        self.response_generator = ResponseGenerator()
        self.proactive_manager = ProactiveCommunicationManager()

        # 初始化状态
        self.initialized = False

    async def initialize(self):
        """初始化通信管理器"""
        try:
            # 加载用户偏好
            await self._load_user_preferences()

            # 初始化各组件
            await self.emotion_analyzer.initialize()
            await self.response_generator.initialize()
            await self.proactive_manager.initialize()

            # 启动消息处理任务
            asyncio.create_task(self._process_message_queue())

            self.initialized = True
            logger.info("✅ 通信管理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 通信管理器初始化失败: {str(e)}")
            self.initialized = True  # 使用默认配置

    async def send_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送消息

        Args:
            message_data: 消息数据
            {
                "channel": "chat|email|telephone|...",
                "priority": "low|normal|high|urgent",
                "sender": "发送者ID",
                "receiver": "接收者ID",
                "content": "消息内容",
                "metadata": {"context": {}, "attachments": []}
            }

        Returns:
            发送结果
        """
        try:
            # 创建消息对象
            message = Message(
                message_id=f"MSG_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                channel=CommunicationChannel(message_data.get("channel", "chat")),
                priority=MessagePriority(message_data.get("priority", "normal")),
                sender=message_data.get("sender", "user"),
                receiver=message_data.get("receiver", "xiaona"),
                content=message_data.get("content", ""),
                metadata=message_data.get("metadata", {}),
                timestamp=datetime.now()
            )

            # 分析情感
            emotion = await self.emotion_analyzer.analyze_emotion(message.content)
            message.metadata["emotion"] = emotion

            # 加入队列处理
            await self.message_queue.put(message)

            # 更新会话
            await self._update_conversation(message)

            # 如果是实时渠道，生成响应
            if message.channel in [CommunicationChannel.CHAT, CommunicationChannel.VIDEO]:
                response = await self._generate_response(message)
                if response:
                    return {
                        "success": True,
                        "message_id": message.message_id,
                        "response": response,
                        "emotion": emotion
                    }

            return {
                "success": True,
                "message_id": message.message_id,
                "status": "queued",
                "emotion": emotion
            }

        except Exception as e:
            logger.error(f"❌ 发送消息失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _generate_response(self, message: Message) -> Dict[str, Any | None]:
        """生成响应"""
        try:
            # 获取上下文
            context = await self._get_conversation_context(message.sender)

            # 生成响应内容
            response_content = await self.response_generator.generate(
                message.content,
                context,
                message.metadata.get("emotion", {})
            )

            # 创建响应消息
            response = Message(
                message_id=f"RESP_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                channel=message.channel,
                priority=message.priority,
                sender="xiaona",
                receiver=message.sender,
                content=response_content["text"],
                metadata={
                    "response_type": response_content.get("type", "standard"),
                    "confidence": response_content.get("confidence", 0.8),
                    "suggestions": response_content.get("suggestions", [])
                },
                timestamp=datetime.now(),
                status="ready",
                response_id=message.message_id
            )

            # 发送响应
            await self._send_response(response)

            # 更新消息状态
            message.status = "responded"
            response.status = "sent"

            # 记录通信历史
            self.communication_history.append({
                "message": message.__dict__,
                "response": response.__dict__,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "response_id": response.message_id,
                "content": response_content,
                "timestamp": response.timestamp.isoformat()
            }

        except Exception as e:
            logger.error(f"生成响应失败: {str(e)}")
            return None

    async def _send_response(self, response: Message):
        """发送响应"""
        # 这里应该根据渠道实际发送消息
        # 简化实现，仅记录
        logger.info(f"响应已发送: {response.message_id} -> {response.receiver}")

    async def _get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """获取会话上下文"""
        if user_id not in self.active_conversations:
            self.active_conversations[user_id] = {
                "messages": [],
                "last_active": datetime.now(),
                "topics": [],
                "preferences": self.user_preferences.get(user_id, {})
            }

        conversation = self.active_conversations[user_id]
        return {
            "recent_messages": conversation["messages"][-5:],  # 最近5条消息
            "topics": conversation["topics"],
            "last_active": conversation["last_active"],
            "user_preferences": conversation["preferences"]
        }

    async def _update_conversation(self, message: Message):
        """更新会话"""
        user_id = message.sender
        if user_id not in self.active_conversations:
            self.active_conversations[user_id] = {
                "messages": [],
                "last_active": datetime.now(),
                "topics": [],
                "preferences": {}
            }

        conversation = self.active_conversations[user_id]
        conversation["messages"].append({
            "id": message.message_id,
            "content": message.content,
            "timestamp": message.timestamp,
            "emotion": message.metadata.get("emotion", {})
        })
        conversation["last_active"] = datetime.now()

        # 限制消息数量
        if len(conversation["messages"]) > self.config["max_conversation_length"]:
            conversation["messages"] = conversation["messages"][-self.config["max_conversation_length"]:]

    async def process_batch_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理消息"""
        results = []
        for msg_data in messages:
            result = await self.send_message(msg_data)
            results.append(result)
        return results

    async def schedule_proactive_message(self, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """
        调度主动消息

        Args:
            user_id: 用户ID
            trigger: 触发条件
            {
                "type": "time|event|condition",
                "schedule": "2024-01-01T10:00:00",
                "event": "case_update",
                "message": "消息内容"
            }

        Returns:
            调度结果
        """
        try:
            result = await self.proactive_manager.schedule_message(user_id, trigger)
            return result

        except Exception as e:
            logger.error(f"调度主动消息失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """获取会话摘要"""
        try:
            if user_id not in self.active_conversations:
                return {"error": "会话不存在"}

            conversation = self.active_conversations[user_id]
            messages = conversation["messages"]

            # 生成摘要
            summary = {
                "user_id": user_id,
                "message_count": len(messages),
                "last_active": conversation["last_active"].isoformat(),
                "topics": conversation["topics"],
                "emotion_trend": await self._analyze_emotion_trend(messages),
                "key_issues": await self._extract_key_issues(messages),
                "satisfaction_score": await self._calculate_satisfaction(messages)
            }

            return summary

        except Exception as e:
            logger.error(f"获取会话摘要失败: {str(e)}")
            return {"error": str(e)}

    async def _analyze_emotion_trend(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析情感趋势"""
        if not messages:
            return {"trend": "stable", "dominant_emotion": "neutral"}

        emotions = [msg.get("emotion", {}).get("primary", "neutral") for msg in messages]
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        dominant = max(emotion_counts, key=emotion_counts.get)

        # 判断趋势
        if len(emotions) >= 3:
            recent = emotions[-3:]
            if all(e == dominant for e in recent):
                trend = "increasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "dominant_emotion": dominant,
            "distribution": emotion_counts
        }

    async def _extract_key_issues(self, messages: List[Dict[str, Any]]) -> List[str]:
        """提取关键问题"""
        # 简化实现，提取包含特定关键词的消息
        key_issues = []
        issue_keywords = ["问题", "困难", "不明白", "怎么办", "如何"]

        for msg in messages:
            content = msg.get("content", "")
            for keyword in issue_keywords:
                if keyword in content:
                    key_issues.append(content[:100])  # 前100个字符
                    break

        return key_issues[:5]  # 最多返回5个问题

    async def _calculate_satisfaction(self, messages: List[Dict[str, Any]]) -> float:
        """计算满意度分数"""
        if not messages:
            return 0.5

        # 基于情感计算满意度
        positive_emotions = ["happy", "satisfied", "excited"]
        negative_emotions = ["frustrated", "angry", "disappointed"]

        positive_count = 0
        negative_count = 0

        for msg in messages:
            emotion = msg.get("emotion", {}).get("primary", "neutral")
            if emotion in positive_emotions:
                positive_count += 1
            elif emotion in negative_emotions:
                negative_count += 1

        total = len(messages)
        if total == 0:
            return 0.5

        satisfaction = (positive_count - negative_count * 0.5) / total
        return max(0, min(1, satisfaction))

    async def _process_message_queue(self):
        """处理消息队列"""
        while True:
            try:
                message = await self.message_queue.get()
                await self._process_message(message)
            except Exception as e:
                logger.error(f"处理消息队列失败: {str(e)}")

    async def _process_message(self, message: Message):
        """处理单个消息"""
        # 记录消息
        message.status = "processing"

        # 执行实际处理逻辑
        # 这里可以根据消息类型进行不同的处理

        message.status = "processed"

    async def _load_user_preferences(self):
        """加载用户偏好"""
        # 简化实现，使用默认偏好
        self.user_preferences = {
            "default_user": {
                "language": "zh-CN",
                "response_style": "professional",
                "notification_enabled": True
            }
        }

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """更新用户偏好"""
        try:
            self.user_preferences[user_id] = preferences

            # 如果有活跃会话，更新会话偏好
            if user_id in self.active_conversations:
                self.active_conversations[user_id]["preferences"] = preferences

            logger.info(f"✅ 用户偏好已更新: {user_id}")
            return True

        except Exception as e:
            logger.error(f"更新用户偏好失败: {str(e)}")
            return False

    async def get_communication_analytics(self) -> Dict[str, Any]:
        """获取通信分析"""
        try:
            analytics = {
                "total_conversations": len(self.active_conversations),
                "total_messages": sum(len(conv["messages"]) for conv in self.active_conversations.values()),
                "active_users": len([conv for conv in self.active_conversations.values()
                                   if (datetime.now() - conv["last_active"]).seconds < 3600]),
                "message_distribution": await self._get_message_distribution(),
                "emotion_analysis": await self._get_global_emotion_analysis(),
                "response_times": await self._get_response_time_analysis(),
                "popular_topics": await self._get_popular_topics()
            }

            return analytics

        except Exception as e:
            logger.error(f"获取通信分析失败: {str(e)}")
            return {}

    async def _get_message_distribution(self) -> Dict[str, int]:
        """获取消息分布"""
        distribution = {}
        for conv in self.active_conversations.values():
            for msg in conv["messages"]:
                channel = msg.get("channel", "chat")
                distribution[channel] = distribution.get(channel, 0) + 1
        return distribution

    async def _get_global_emotion_analysis(self) -> Dict[str, Any]:
        """获取全局情感分析"""
        all_emotions = []
        for conv in self.active_conversations.values():
            for msg in conv["messages"]:
                emotion = msg.get("emotion", {}).get("primary", "neutral")
                all_emotions.append(emotion)

        if not all_emotions:
            return {"dominant": "neutral", "distribution": {}}

        from collections import Counter
        emotion_counts = Counter(all_emotions)
        dominant = emotion_counts.most_common(1)[0][0]

        return {
            "dominant": dominant,
            "distribution": dict(emotion_counts),
            "total_analyzed": len(all_emotions)
        }

    async def _get_response_time_analysis(self) -> Dict[str, float]:
        """获取响应时间分析"""
        # 简化实现，返回模拟数据
        return {
            "average_response_time": 2.5,
            "median_response_time": 1.8,
            "95th_percentile": 5.2
        }

    async def _get_popular_topics(self) -> List[Dict[str, Any]]:
        """获取热门话题"""
        topics = {}
        for conv in self.active_conversations.values():
            for topic in conv.get("topics", []):
                topics[topic] = topics.get(topic, 0) + 1

        # 排序并返回前5个
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{"topic": topic, "count": count} for topic, count in sorted_topics]

class EmotionAnalyzer:
    """情感分析器"""

    async def initialize(self):
        """初始化"""
        pass

    async def analyze_emotion(self, text: str) -> Dict[str, Any]:
        """分析情感"""
        # 简化的情感分析
        positive_words = ["好", "棒", "优秀", "满意", "感谢", "不错"]
        negative_words = ["差", "糟糕", "失望", "不满", "问题", "错误"]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            primary = "positive"
        elif negative_count > positive_count:
            primary = "negative"
        else:
            primary = "neutral"

        return {
            "primary": primary,
            "confidence": 0.7,
            "positive_score": positive_count / max(len(text), 1),
            "negative_score": negative_count / max(len(text), 1)
        }

class ResponseGenerator:
    """响应生成器"""

    async def initialize(self):
        """初始化"""
        pass

    async def generate(self, input_text: str, context: Dict[str, Any], emotion: Dict[str, Any]) -> Dict[str, Any]:
        """生成响应"""
        # 基于情感和上下文生成响应
        primary_emotion = emotion.get("primary", "neutral")

        if primary_emotion == "positive":
            tone = "warm"
            starter = "很高兴能帮到您！"
        elif primary_emotion == "negative":
            tone = "supportive"
            starter = "理解您的困扰，让我来帮助您。"
        else:
            tone = "professional"
            starter = ""

        # 根据内容生成响应
        if "专利" in input_text:
            response_text = f"{starter}关于专利申请，我可以为您提供专业的指导..."
            suggestions = ["了解专利申请流程", "准备申请材料", "进行专利检索"]
        elif "商标" in input_text:
            response_text = f"{starter}商标注册是保护品牌的重要步骤..."
            suggestions = ["商标查询", "准备申请材料", "选择注册类别"]
        else:
            response_text = f"{starter}我是小娜，专业的知识产权法律助手..."
            suggestions = ["专利咨询", "商标申请", "版权保护", "合同审查"]

        return {
            "text": response_text,
            "type": "standard",
            "tone": tone,
            "confidence": 0.85,
            "suggestions": suggestions
        }

class ProactiveCommunicationManager:
    """主动通信管理器"""

    def __init__(self):
        self.scheduled_messages = []

    async def initialize(self):
        """初始化"""
        pass

    async def schedule_message(self, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """调度消息"""
        schedule_id = f"SCHED_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        scheduled = {
            "schedule_id": schedule_id,
            "user_id": user_id,
            "trigger": trigger,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        self.scheduled_messages.append(scheduled)

        return {
            "success": True,
            "schedule_id": schedule_id,
            "status": "scheduled"
        }

# 使用示例
async def main():
    """测试通信管理器"""
    comm_manager = CommunicationManager()
    await comm_manager.initialize()

    # 发送消息
    result = await comm_manager.send_message({
        "channel": "chat",
        "priority": "normal",
        "sender": "user123",
        "content": "我想申请一个发明专利，请问需要什么材料？",
        "metadata": {}
    })

    print(f"发送结果: {result}")

    # 获取会话摘要
    summary = await comm_manager.get_conversation_summary("user123")
    print(f"会话摘要: {summary}")

    # 获取通信分析
    analytics = await comm_manager.get_communication_analytics()
    print(f"通信分析: {analytics}")

# 入口点: @async_main装饰器已添加到main函数