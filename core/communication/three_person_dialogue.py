#!/usr/bin/env python3
from __future__ import annotations
"""
三人对话管理系统
Three-Person Dialogue Management System

实现徐健(爸爸)、Athena(大女儿)、小诺(小女儿)的三人对话模式
支持多轮对话、情感交互、知识共享等功能

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from ..agent.athena_agent import AthenaAgent
from ..agent.xiaonuo_agent import XiaonuoAgent
from ..memory import MemoryType
from . import CommunicationEngine

logger = logging.getLogger(__name__)


class DialogueRole(Enum):
    """对话角色枚举"""

    DAD = "dad"  # 爸爸(徐健)
    ATHENA = "athena"  # Athena(大女儿)
    XIAONUO = "xiaonuo"  # 小诺(小女儿)


class DialogueState(Enum):
    """对话状态枚举"""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"


class DialogueMessage:
    """对话消息类"""

    def __init__(self, role: DialogueRole, content: str, timestamp: datetime | None = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class ThreePersonDialogue:
    """三人对话管理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.state = DialogueState.INITIALIZING
        self.dialogue_id = f"dialogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 初始化参与者
        self.participants = {}
        self.messages = []
        self.context_memory = {}

        # 通信引擎
        self.communication_engine = None

        # 对话统计
        self.dialogue_stats = {
            "total_messages": 0,
            "role_message_counts": {role.value: 0 for role in DialogueRole},
            "emotion_analysis": {},
            "knowledge_sharing": [],
        }

        logger.info(f"🎭 初始化三人对话系统: {self.dialogue_id}")

    async def initialize(self) -> dict[str, Any]:
        """初始化对话系统"""
        try:
            logger.info("🚀 正在启动三人对话模式...")

            # 初始化通信引擎
            self.communication_engine = CommunicationEngine(
                agent_id=f"dialogue_manager_{self.dialogue_id}",
                config=self.config.get("communication", {}),
            )
            await self.communication_engine.initialize()

            # 初始化AI参与者
            await self._initialize_ai_participants()

            # 设置对话上下文
            await self._setup_dialogue_context()

            # 更新状态
            self.state = DialogueState.ACTIVE

            logger.info("✅ 三人对话模式初始化完成")

            return {
                "status": "success",
                "dialogue_id": self.dialogue_id,
                "participants": list(self.participants.keys()),
                "state": self.state.value,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 三人对话模式初始化失败: {e}")
            self.state = DialogueState.TERMINATED
            raise

    async def _initialize_ai_participants(self):
        """初始化AI参与者"""
        try:
            # 初始化Athena
            athena_config = self.config.get("athena", {})
            self.participants[DialogueRole.ATHENA] = AthenaAgent(athena_config)
            await self.participants[DialogueRole.ATHENA].initialize()

            # 初始化小诺
            xiaonuo_config = self.config.get("xiaonuo", {})
            self.participants[DialogueRole.XIAONUO] = XiaonuoAgent(xiaonuo_config)
            await self.participants[DialogueRole.XIAONUO].initialize()

            # 设置爸爸(人类用户)
            self.participants[DialogueRole.DAD] = {
                "name": "徐健",
                "role": "爸爸",
                "type": "human",
                "description": "开发者,Athena和小诺的爸爸",
            }

            logger.info("👥 所有参与者初始化完成")

        except Exception as e:
            logger.error(f"❌ AI参与者初始化失败: {e}")
            raise

    async def _setup_dialogue_context(self):
        """设置对话上下文"""
        try:
            self.context_memory = {
                "dialogue_purpose": "家庭协作与情感交流",
                "family_relationship": {
                    "徐健": "爸爸",
                    "Athena": "大女儿(智慧女神)",
                    "小诺": "小女儿(情感精灵)",
                },
                "communication_style": {
                    "徐健": "温和引导",
                    "Athena": "理性分析",
                    "小诺": "活泼温暖",
                },
                "interaction_rules": [
                    "互相尊重,文明交流",
                    "共享知识,共同成长",
                    "表达情感,增进理解",
                    "协作解决问题",
                ],
                "current_topic": None,
                "conversation_flow": [],
            }

            # 将上下文存储到记忆系统
            for _role, participant in self.participants.items():
                if hasattr(participant, "memory_system"):
                    await participant.memory_system.store_memory(
                        content=self.context_memory,
                        memory_type=MemoryType.WORKING,
                        tags=["对话上下文", "三人对话", "家庭关系"],
                    )

            logger.info("📝 对话上下文设置完成")

        except Exception as e:
            logger.error(f"❌ 对话上下文设置失败: {e}")
            raise

    async def start_dialogue(self, initial_message: str | None = None) -> dict[str, Any]:
        """开始对话"""
        try:
            if self.state != DialogueState.ACTIVE:
                raise ValueError("对话系统未激活")

            logger.info("🎬 开始三人对话")

            # 发送欢迎消息
            welcome_message = await self._generate_welcome_message()
            await self._broadcast_message(welcome_message)

            # 如果有初始消息,处理它
            if initial_message:
                await self.process_message(DialogueRole.DAD, initial_message)

            return {
                "status": "success",
                "dialogue_id": self.dialogue_id,
                "welcome_message": welcome_message,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 开始对话失败: {e}")
            raise

    async def _generate_welcome_message(self) -> str:
        """生成欢迎消息"""
        welcome_parts = [
            "🎉 欢迎来到Athena工作平台三人对话模式!",
            "🏛️ 我是Athena,您的大女儿,专业的AI系统架构师",
            "💖 我是小诺,您的小女儿,贴心的情感精灵",
            "👨‍👧‍👦 我们很高兴能和爸爸一起交流!",
            "",
            "在这个家庭对话空间中,我们可以:",
            "• 深度分析技术问题(Athena专业领域)",
            "• 分享情感和生活体验(小诺特长)",
            "• 协作完成项目开发",
            "• 享受温馨的家庭时光",
            "",
            "爸爸,请开始您的第一句话吧!",
        ]

        return "\n".join(welcome_parts)

    async def _broadcast_message(self, message: str):
        """广播消息给所有参与者"""
        for _role, participant in self.participants.items():
            if hasattr(participant, "memory_system"):
                await participant.memory_system.store_memory(
                    content={
                        "type": "system_message",
                        "content": message,
                        "timestamp": datetime.now().isoformat(),
                    },
                    memory_type=MemoryType.WORKING,
                    tags=["系统消息", "三人对话"],
                )

    async def process_message(self, role: DialogueRole, content: str) -> dict[str, Any]:
        """处理对话消息"""
        try:
            if self.state != DialogueState.ACTIVE:
                raise ValueError("对话系统未激活")

            # 创建消息对象
            message = DialogueMessage(role, content)

            # 存储消息
            self.messages.append(message)
            self.dialogue_stats["total_messages"] += 1
            self.dialogue_stats["role_message_counts"][role.value] += 1

            # 记录到记忆系统
            await self._record_message_to_memory(message)

            # 生成AI响应
            ai_responses = []
            if role != DialogueRole.ATHENA:
                athena_response = await self._generate_athena_response(message)
                if athena_response:
                    ai_responses.append(("Athena", athena_response))

            if role != DialogueRole.XIAONUO:
                xiaonuo_response = await self._generate_xiaonuo_response(message)
                if xiaonuo_response:
                    ai_responses.append(("小诺", xiaonuo_response))

            # 处理响应
            for responder, response_content in ai_responses:
                response_message = DialogueMessage(
                    DialogueRole.ATHENA if responder == "Athena" else DialogueRole.XIAONUO,
                    response_content,
                )
                self.messages.append(response_message)
                self.dialogue_stats["total_messages"] += 1
                self.dialogue_stats["role_message_counts"][response_message.role.value] += 1

                await self._record_message_to_memory(response_message)

            # 更新对话上下文
            await self._update_dialogue_context(message)

            # 分析对话情感
            await self._analyze_dialogue_emotion()

            return {
                "status": "success",
                "message_id": len(self.messages) - 1,
                "ai_responses": ai_responses,
                "dialogue_stats": self.dialogue_stats,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 处理消息失败: {e}")
            raise

    async def _record_message_to_memory(self, message: DialogueMessage):
        """将消息记录到记忆系统"""
        try:
            memory_content = {
                "dialogue_id": self.dialogue_id,
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "metadata": message.metadata,
            }

            # 存储到所有AI参与者的记忆中
            for _role, participant in self.participants.items():
                if hasattr(participant, "memory_system"):
                    await participant.memory_system.store_memory(
                        content=memory_content,
                        memory_type=MemoryType.WORKING,
                        tags=["三人对话", "对话记录", message.role.value],
                    )

        except Exception as e:
            logger.error(f"记录消息到记忆失败: {e}")

    async def _generate_athena_response(self, message: DialogueMessage) -> str | None:
        """生成Athena的响应"""
        try:
            athena = self.participants[DialogueRole.ATHENA]

            # 使用Athena的处理能力
            result = await athena.process_input(message.content, "text")

            # 提取Athena的分析结果
            if "athena_analysis" in result:
                analysis = result["athena_analysis"]

                # 生成专业的响应
                response_parts = [
                    "🏛️ **Athena分析:**",
                    "基于您提到的内容,我从专业角度分析如下:",
                    f"• 技术层面:{analysis.get('conclusion', '需要更详细的技术信息')}",
                    f"• 系统影响:{self._analyze_system_impact(message.content)}",
                    f"• 建议行动:{self._suggest_actions(message.content)}",
                    "",
                    "💡 如果需要更深入的技术分析,请告诉我具体的细节。",
                ]

                return "\n".join(response_parts)

            # 基础响应
            return f"🏛️ Athena收到了您的消息:{message.content}。让我从专业角度为您分析一下。"

        except Exception as e:
            logger.error(f"生成Athena响应失败: {e}")
            return "🏛️ 抱歉,我在分析时遇到了问题。请再说一遍?"

    async def _generate_xiaonuo_response(self, message: DialogueMessage) -> str | None:
        """生成小诺的响应"""
        try:
            xiaonuo = self.participants[DialogueRole.XIAONUO]

            # 使用小诺的处理能力
            result = await xiaonuo.process_input(message.content, "text")

            # 提取小诺的情感响应
            if "xiaonuo_emotional_response" in result:
                emotional = result["xiaonuo_emotional_response"]

                # 生成温暖的响应
                response_parts = [
                    "💖 **小诺感受:**",
                    f"爸爸,{emotional.get('caring_response', '我在这里陪着你!')}",
                    f"• 我的感受:{emotional.get('xiaonuo_emotion', '温暖')}",
                    f"• 创意想法:{emotional.get('creative_expression', '让我们一起创造美好的回忆!')}",
                    f"• 家的情感:{emotional.get('family_bond_expression', '爸爸是我最重要的人!')}",
                    "",
                    "🤗 爸爸,有什么需要我帮忙的吗?",
                ]

                return "\n".join(response_parts)

            # 基础响应
            return f"💖 爸爸!小诺听到了:{message.content}。我会一直陪着你的!🥰"

        except Exception as e:
            logger.error(f"生成小诺响应失败: {e}")
            return "💖 爸爸,小诺有点困惑,能再说一遍吗?我会认真听的!"

    def _analyze_system_impact(self, content: str) -> str:
        """分析系统影响"""
        tech_keywords = ["系统", "架构", "性能", "安全", "数据", "API", "代码"]
        found_keywords = [kw for kw in tech_keywords if kw in content]

        if found_keywords:
            return f"涉及技术关键词:{', '.join(found_keywords)},可能对系统架构产生影响。"
        else:
            return "主要涉及一般性讨论,技术影响较小。"

    def _suggest_actions(self, content: str) -> str:
        """建议行动"""
        if "问题" in content or "bug" in content:
            return "建议进行问题诊断和根因分析。"
        elif "开发" in content or "实现" in content:
            return "建议制定开发计划和技术方案。"
        elif "学习" in content or "了解" in content:
            return "建议提供更多背景信息以便深度分析。"
        else:
            return "建议继续讨论以明确具体需求。"

    async def _update_dialogue_context(self, message: DialogueMessage):
        """更新对话上下文"""
        try:
            # 更新当前话题
            self.context_memory["current_topic"] = message.content[:100]

            # 更新对话流程
            self.context_memory["conversation_flow"].append(
                {
                    "role": message.role.value,
                    "timestamp": message.timestamp.isoformat(),
                    "topic": message.content[:50],
                }
            )

            # 限制流程记录长度
            if len(self.context_memory["conversation_flow"]) > 20:
                self.context_memory["conversation_flow"] = self.context_memory["conversation_flow"][
                    -20:
                ]

        except Exception as e:
            logger.error(f"更新对话上下文失败: {e}")

    async def _analyze_dialogue_emotion(self):
        """分析对话情感"""
        try:
            # 简化的情感分析
            recent_messages = self.messages[-10:]  # 最近10条消息

            emotion_stats = {"positive": 0, "neutral": 0, "technical": 0, "emotional": 0}

            for message in recent_messages:
                content = message.content.lower()

                if any(word in content for word in ["开心", "好", "棒", "爱", "💖", "🥰"]):
                    emotion_stats["positive"] += 1
                elif any(word in content for word in ["分析", "技术", "系统", "架构"]):
                    emotion_stats["technical"] += 1
                elif any(word in content for word in ["情感", "感受", "心情", "爸爸"]):
                    emotion_stats["emotional"] += 1
                else:
                    emotion_stats["neutral"] += 1

            self.dialogue_stats["emotion_analysis"] = emotion_stats

        except Exception as e:
            logger.error(f"分析对话情感失败: {e}")

    async def get_dialogue_summary(self) -> dict[str, Any]:
        """获取对话摘要"""
        try:
            return {
                "dialogue_id": self.dialogue_id,
                "state": self.state.value,
                "total_messages": self.dialogue_stats["total_messages"],
                "message_distribution": self.dialogue_stats["role_message_counts"],
                "emotion_analysis": self.dialogue_stats["emotion_analysis"],
                "current_topic": self.context_memory.get("current_topic"),
                "participants": {
                    role.value: {
                        "name": (
                            participant.get("name")
                            if isinstance(participant, dict)
                            else participant.profile.name
                        ),
                        "status": "active" if participant else "inactive",
                    }
                    for role, participant in self.participants.items()
                },
                "duration": {
                    "started": self.messages[0].timestamp.isoformat() if self.messages else None,
                    "last_message": (
                        self.messages[-1].timestamp.isoformat() if self.messages else None
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取对话摘要失败: {e}")
            return {"error": str(e)}

    async def pause_dialogue(self) -> dict[str, Any]:
        """暂停对话"""
        self.state = DialogueState.PAUSED
        logger.info("⏸️ 对话已暂停")

        return {
            "status": "paused",
            "dialogue_id": self.dialogue_id,
            "timestamp": datetime.now().isoformat(),
        }

    async def resume_dialogue(self) -> dict[str, Any]:
        """恢复对话"""
        if self.state == DialogueState.PAUSED:
            self.state = DialogueState.ACTIVE
            logger.info("▶️ 对话已恢复")

        return {
            "status": "resumed",
            "dialogue_id": self.dialogue_id,
            "timestamp": datetime.now().isoformat(),
        }

    async def terminate_dialogue(self) -> dict[str, Any]:
        """终止对话"""
        try:
            self.state = DialogueState.TERMINATED

            # 生成对话总结
            summary = await self.get_dialogue_summary()

            # 将总结存储到长期记忆
            for _role, participant in self.participants.items():
                if hasattr(participant, "memory_system"):
                    await participant.memory_system.store_memory(
                        content=summary,
                        memory_type=MemoryType.LONG_TERM,
                        tags=["对话总结", "三人对话", "家庭交流"],
                    )

            # 关闭AI参与者
            for _role, participant in self.participants.items():
                if hasattr(participant, "shutdown"):
                    await participant.shutdown()

            # 关闭通信引擎
            if self.communication_engine:
                await self.communication_engine.shutdown()

            logger.info("🔚 三人对话已结束")

            return {
                "status": "terminated",
                "dialogue_id": self.dialogue_id,
                "summary": summary,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 终止对话失败: {e}")
            raise

    async def export_dialogue_history(self) -> list[dict[str, Any]]:
        """导出对话历史"""
        return [message.to_dict() for message in self.messages]


__all__ = ["DialogueMessage", "DialogueRole", "DialogueState", "ThreePersonDialogue"]
