#!/usr/bin/env python3
"""
WebSocket消息协议
WebSocket Message Protocol

定义WebSocket消息的格式和处理协议。

消息格式:
{
    "type": "message|broadcast|subscribe|unsubscribe|ping|pong|system|error",
    "id": "unique_message_id",
    "timestamp": "ISO_8601_timestamp",
    "data": {...}
}

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class WebSocketMessageType(str, Enum):
    """WebSocket消息类型"""

    # 基础消息
    MESSAGE = "message"  # 普通消息
    BROADCAST = "broadcast"  # 广播消息
    DIRECT = "direct"  # 直接消息

    # 订阅
    SUBSCRIBE = "subscribe"  # 订阅频道
    UNSUBSCRIBE = "unsubscribe"  # 取消订阅

    # 心跳
    PING = "ping"  # PING
    PONG = "pong"  # PONG

    # 系统
    SYSTEM = "system"  # 系统消息
    ERROR = "error"  # 错误消息


@dataclass
class WebSocketMessage:
    """WebSocket消息数据结构"""

    type: WebSocketMessageType
    data: dict[str, Any]
    id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "id": self.id,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebSocketMessage":
        """从字典创建"""
        return cls(
            type=WebSocketMessageType(data["type"]),
            id=data.get("id", f"msg_{uuid.uuid4().hex}"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
        )


class MessageProtocol:
    """
    WebSocket消息协议处理器

    负责消息的序列化和反序列化。
    """

    def __init__(self):
        """初始化消息协议"""
        self.logger = logging.getLogger(f"{__name__}.MessageProtocol")

    async def parse_message(
        self, raw_message: str | bytes
    ) -> WebSocketMessage:
        """
        解析原始消息

        Args:
            raw_message: 原始消息（字符串或字节）

        Returns:
            WebSocket消息对象

        Raises:
            json.JSONDecodeError: JSON解析失败
            ValueError: 消息格式无效
        """
        # 解码字节
        if isinstance(raw_message, bytes):
            raw_message = raw_message.decode("utf-8")

        # 解析JSON
        data = json.loads(raw_message)

        # 验证必需字段
        if "type" not in data:
            raise ValueError("消息缺少type字段")

        # 创建消息对象
        return WebSocketMessage.from_dict(data)

    def create_message(
        self,
        message_type: WebSocketMessageType,
        data: dict[str, Any],
        message_id: str | None = None,
    ) -> str:
        """
        创建消息

        Args:
            message_type: 消息类型
            data: 消息数据
            message_id: 消息ID（可选）

        Returns:
            序列化后的消息字符串
        """
        message = WebSocketMessage(
            type=message_type,
            data=data,
            id=message_id or f"msg_{uuid.uuid4().hex}",
        )
        return self.serialize(message)

    def serialize(self, message: WebSocketMessage) -> str:
        """
        序列化消息

        Args:
            message: WebSocket消息对象

        Returns:
            JSON字符串
        """
        return json.dumps(message.to_dict(), ensure_ascii=False)

    # 便捷方法

    def create_text_message(self, text: str, sender: str | None = None) -> str:
        """创建文本消息"""
        return self.create_message(
            WebSocketMessageType.MESSAGE,
            {"content_type": "text", "text": text, "sender": sender},
        )

    def create_ping_message(self) -> str:
        """创建PING消息"""
        return self.create_message(
            WebSocketMessageType.PING, {"timestamp": datetime.now().isoformat()}
        )

    def create_pong_message(self) -> str:
        """创建PONG消息"""
        return self.create_message(
            WebSocketMessageType.PONG, {"timestamp": datetime.now().isoformat()}
        )

    def create_error_message(
        self, code: str, message: str, details: dict[str, Any] | None = None
    ) -> str:
        """创建错误消息"""
        data = {"code": code, "message": message}
        if details:
            data["details"] = details
        return self.create_message(WebSocketMessageType.ERROR, data)

    def create_broadcast_message(
        self, content: Any, sender: str | None = None
    ) -> str:
        """创建广播消息"""
        return self.create_message(
            WebSocketMessageType.BROADCAST,
            {"content": content, "sender": sender},
        )

    def create_system_notification(
        self, notification_type: str, message: str, data: dict[str, Any] | None = None
    ) -> str:
        """创建系统通知"""
        payload = {"type": notification_type, "message": message}
        if data:
            payload["data"] = data
        return self.create_message(WebSocketMessageType.SYSTEM, payload)


# 预定义的系统通知类型
class SystemNotificationType:
    """系统通知类型"""

    WELCOME = "welcome"
    CONNECTION_ESTABLISHED = "connection_establishled"
    CONNECTION_CLOSED = "connection_closed"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


__all__ = [
    "WebSocketMessageType",
    "MessageType",  # 别名
    "WebSocketMessage",
    "MessageProtocol",
    "SystemNotificationType",
]


# =============================================================================
# === 别名和兼容性 ===
# =============================================================================

# 为保持兼容性，提供 MessageType 作为别名
MessageType = WebSocketMessageType
