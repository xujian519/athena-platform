#!/usr/bin/env python3
from __future__ import annotations
"""
轻量级通信引擎
Lightweight Communication Engine

小娜通信模块的轻量级实现,减少外部依赖
提供基础的消息传递和通信能力
"""

import logging
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""

    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    BROADCAST = "broadcast"


@dataclass
class Message:
    """消息数据结构"""

    id: str
    type: MessageType
    sender: str
    receiver: str
    content: Any
    timestamp: datetime
    metadata: dict | None = None


class LightweightCommunicationEngine:
    """轻量级通信引擎"""

    def __init__(self):
        """初始化轻量级通信引擎"""
        self.name = "LightweightCommunicationEngine"
        self.version = "1.0.0"
        self.participants: set[str] = set()
        self.channels: dict[str, set[str]] = defaultdict(set)
        self.message_queue: deque = deque(maxlen=10000)
        self.message_handlers: dict[str, Callable] = {}
        self.statistics = {
            "messages_sent": 0,
            "messages_received": 0,
            "broadcasts_sent": 0,
            "errors": 0,
        }

    async def register_participant(self, participant_id: str) -> bool:
        """注册参与者"""
        try:
            self.participants.add(participant_id)
            logger.info(f"参与者 {participant_id} 注册成功")
            return True
        except Exception as e:
            logger.error(f"注册参与者失败: {e}")
            return False

    async def unregister_participant(self, participant_id: str) -> bool:
        """注销参与者"""
        try:
            self.participants.discard(participant_id)
            # 从所有频道中移除
            for channel_participants in self.channels.values():
                channel_participants.discard(participant_id)
            logger.info(f"参与者 {participant_id} 注销成功")
            return True
        except Exception as e:
            logger.error(f"注销参与者失败: {e}")
            return False

    async def join_channel(self, participant_id: str, channel: str) -> bool:
        """加入频道"""
        try:
            if participant_id not in self.participants:
                logger.error(f"参与者 {participant_id} 未注册")
                return False
            self.channels[channel].add(participant_id)
            logger.info(f"参与者 {participant_id} 加入频道 {channel}")
            return True
        except Exception as e:
            logger.error(f"加入频道失败: {e}")
            return False

    async def leave_channel(self, participant_id: str, channel: str) -> bool:
        """离开频道"""
        try:
            self.channels[channel].discard(participant_id)
            if not self.channels[channel]:
                del self.channels[channel]
            logger.info(f"参与者 {participant_id} 离开频道 {channel}")
            return True
        except Exception as e:
            logger.error(f"离开频道失败: {e}")
            return False

    async def send_message(self, message: Message) -> bool:
        """发送消息"""
        try:
            # 验证发送者
            if message.sender not in self.participants:
                logger.error(f"发送者 {message.sender} 未注册")
                return False

            # 验证接收者
            if message.receiver not in self.participants:
                logger.error(f"接收者 {message.receiver} 未注册")
                return False

            # 添加到消息队列
            self.message_queue.append(message)
            self.statistics["messages_sent"] += 1

            # 调用消息处理器
            if message.receiver in self.message_handlers:
                await self.message_handlers[message.receiver](message)

            logger.debug(f"消息 {message.id} 发送成功")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.statistics["errors"] += 1
            return False

    async def broadcast(
        self,
        sender: str,
        channel: str,
        content: Any,
        message_type: MessageType = MessageType.BROADCAST,
    ) -> int:
        """广播消息"""
        try:
            if sender not in self.participants:
                logger.error(f"发送者 {sender} 未注册")
                return 0

            if channel not in self.channels:
                logger.error(f"频道 {channel} 不存在")
                return 0

            participants = self.channels[channel].copy()
            participants.discard(sender)  # 不给自己发送

            success_count = 0
            for participant in participants:
                message = Message(
                    id=str(uuid.uuid4()),
                    type=message_type,
                    sender=sender,
                    receiver=participant,
                    content=content,
                    timestamp=datetime.now(),
                    metadata={"channel": channel},
                )
                if await self.send_message(message):
                    success_count += 1

            self.statistics["broadcasts_sent"] += 1
            logger.info(
                f"频道 {channel} 广播完成,成功发送 {success_count}/{len(participants)} 条消息"
            )
            return success_count
        except Exception as e:
            logger.error(f"广播失败: {e}")
            return 0

    async def receive_messages(self, participant_id: str, limit: int = 10) -> list[Message]:
        """接收消息"""
        try:
            messages = []
            queue_copy = list(self.message_queue)

            for message in queue_copy:
                if message.receiver == participant_id and len(messages) < limit:
                    messages.append(message)
                    self.message_queue.remove(message)
                    self.statistics["messages_received"] += 1

            return messages
        except Exception as e:
            logger.error(f"接收消息失败: {e}")
            return []

    def register_message_handler(self, participant_id: str, handler: Callable) -> bool:
        """注册消息处理器"""
        try:
            self.message_handlers[participant_id] = handler
            logger.info(f"为参与者 {participant_id} 注册消息处理器")
            return True
        except Exception as e:
            logger.error(f"注册消息处理器失败: {e}")
            return False

    def get_participants(self) -> list[str]:
        """获取所有参与者"""
        return list(self.participants)

    def get_channels(self) -> dict[str, list[str]]:
        """获取所有频道"""
        return {channel: list(participants) for channel, participants in self.channels.items()}

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.statistics,
            "total_participants": len(self.participants),
            "total_channels": len(self.channels),
            "queue_size": len(self.message_queue),
        }

    async def clear_queue(self) -> bool:
        """清空消息队列"""
        try:
            self.message_queue.clear()
            logger.info("消息队列已清空")
            return True
        except Exception as e:
            logger.error(f"清空队列失败: {e}")
            return False

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "engine": self.name,
            "version": self.version,
            "participants": len(self.participants),
            "channels": len(self.channels),
            "queue_size": len(self.message_queue),
            "statistics": self.statistics,
        }


# =============================================================================
# === 便捷函数 ===
# =============================================================================

# 全局引擎实例
_global_lightweight_engine: LightweightCommunicationEngine | None = None


def get_lightweight_engine() -> LightweightCommunicationEngine:
    """
    获取或创建轻量级通信引擎实例

    Returns:
        LightweightCommunicationEngine 实例
    """
    global _global_lightweight_engine

    if _global_lightweight_engine is None:
        _global_lightweight_engine = LightweightCommunicationEngine()

    return _global_lightweight_engine


__all__ = [
    "MessageType",
    "Message",
    "LightweightCommunicationEngine",
    "get_lightweight_engine",
]
