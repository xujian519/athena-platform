#!/usr/bin/env python3
"""
Athena通信系统 - 统一类型定义
Unified Type Definitions for Communication System

本模块提供通信系统中所有核心数据类型的统一定义,
解决类型不一致问题,确保模块间互操作性。

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# =============================================================================
# 枚举类型定义
# =============================================================================


class MessagePriority(Enum):
    """
    消息优先级枚举 - 统一定义

    优先级从高到低排列,数字越小优先级越高。
    此定义整合了之前分散在多个文件中的优先级定义。
    """

    CRITICAL = 0  # 关键任务,最高优先级(原 communication_engine.py)
    HIGH = 1  # 高优先级
    NORMAL = 2  # 普通优先级(默认值)
    LOW = 3  # 低优先级
    BULK = 4  # 批量处理,最低优先级


class MessageType(Enum):
    """
    消息类型枚举 - 统一定义

    整合了多个模块中的消息类型定义。
    """

    # 基础消息类型
    TEXT = "text"  # 文本消息
    IMAGE = "image"  # 图片消息
    FILE = "file"  # 文件消息
    SYSTEM = "system"  # 系统消息

    # 功能消息类型
    COMMAND = "command"  # 命令消息
    EVENT = "event"  # 事件消息
    NOTIFICATION = "notification"  # 通知消息
    RESPONSE = "response"  # 响应消息

    # 协作消息类型
    TASK = "task"  # 任务消息
    COORDINATION = "coordination"  # 协调消息
    STATUS_UPDATE = "status_update"  # 状态更新

    # 广播类型
    BROADCAST = "broadcast"  # 广播消息

    # 错误类型
    ERROR = "error"  # 错误消息

    # AI响应类型
    AI_RESPONSE = "ai_response"  # AI响应

    # 协作相关
    COLLABORATION_REQUEST = "collaboration_request"  # 协作请求
    COLLABORATION_RESPONSE = "collaboration_response"  # 协作响应

    # 任务相关
    TASK_CREATED = "task_created"  # 任务已创建
    TASK_UPDATED = "task_updated"  # 任务已更新
    TASK_COMPLETED = "task_completed"  # 任务已完成

    # 系统
    HEARTBEAT = "heartbeat"  # 心跳消息


class MessageStatus(Enum):
    """
    消息状态枚举 - 统一定义
    """

    PENDING = "pending"  # 等待中
    QUEUED = "queued"  # 已排队
    PROCESSING = "processing"  # 处理中
    SENT = "sent"  # 已发送
    DELIVERED = "delivered"  # 已投递
    FAILED = "failed"  # 失败
    TIMEOUT = "timeout"  # 超时
    CANCELLED = "cancelled"  # 已取消


class ChannelType(Enum):
    """
    通道类型枚举 - 统一定义
    """

    DIRECT = "direct"  # 直接通道(点对点)
    GROUP = "group"  # 组通道(多对多)
    BROADCAST = "broadcast"  # 广播通道(一对多)
    TOPIC = "topic"  # 主题通道(发布/订阅)
    AGENT = "agent"  # 智能体通道
    API = "api"  # API通道
    WEBSOCKET = "websocket"  # WebSocket通道
    HTTP = "http"  # HTTP通道
    QUEUE = "queue"  # 队列通道


class DeliveryMode(Enum):
    """
    投递模式枚举
    """

    SYNCHRONOUS = "sync"  # 同步投递
    ASYNCHRONOUS = "async"  # 异步投递
    BATCH = "batch"  # 批量投递


class CommunicationChannel(Enum):
    """
    通信渠道枚举(用于通信管理器)
    """

    CHAT = "chat"
    EMAIL = "email"
    TELEPHONE = "telephone"
    VIDEO = "video"
    DOCUMENT = "document"
    API = "api"


# =============================================================================
# 兼容性别名
# =============================================================================

# 向后兼容的别名
TaskPriority = MessagePriority  # agent_collaboration使用
Priority = MessagePriority  # message_bus使用


# =============================================================================
# 数据类定义
# =============================================================================


@dataclass
class Message:
    """
    统一的消息数据结构

    整合了多个模块中的消息定义,提供完整的消息属性。
    """

    # 基本标识
    id: str = ""
    type: MessageType = MessageType.TEXT
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING

    # 发送者和接收者
    sender: str = ""
    receiver: str = ""

    # 消息内容
    content: Any = None

    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)

    # 元数据和扩展
    metadata: dict[str, Any] = field(default_factory=dict)

    # 回复和关联
    reply_to: str | None = None  # 回复的消息ID
    correlation_id: str | None = None  # 关联ID(用于追踪对话)
    expires_at: datetime | None = None  # 过期时间

    # 重试相关
    retry_count: int = 0
    max_retries: int = 3

    # 通道和路由
    channel: str = "default"
    channel_type: ChannelType = ChannelType.DIRECT

    # 性能追踪
    delivery_time: float = 0.0  # 投递耗时(秒)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": str(self.content) if self.content is not None else None,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "reply_to": self.reply_to,
            "correlation_id": self.correlation_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "channel": self.channel,
            "channel_type": self.channel_type.value,
            "delivery_time": self.delivery_time,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """从字典创建消息"""
        return cls(
            id=data.get("id", ""),
            type=MessageType(data.get("type", MessageType.TEXT.value)),
            priority=MessagePriority(data.get("priority", MessagePriority.NORMAL.value)),
            status=MessageStatus(data.get("status", MessageStatus.PENDING.value)),
            sender=data.get("sender", ""),
            receiver=data.get("receiver", ""),
            content=data.get("content"),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if data.get("timestamp")
                else datetime.now()
            ),
            metadata=data.get("metadata", {}),
            reply_to=data.get("reply_to"),
            correlation_id=data.get("correlation_id"),
            expires_at=(
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            ),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            channel=data.get("channel", "default"),
            channel_type=ChannelType(data.get("channel_type", ChannelType.DIRECT.value)),
            delivery_time=data.get("delivery_time", 0.0),
        )

    def is_expired(self) -> bool:
        """检查消息是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """增加重试计数"""
        self.retry_count += 1


@dataclass
class TaskMessage(Message):
    """
    任务消息 - 继承自Message,添加任务特定属性
    """

    task_type: str = ""  # 任务类型(search, analysis, creative等)
    task_id: str = ""  # 任务ID
    deadline: datetime | None = None  # 任务截止时间

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "task_type": self.task_type,
                "task_id": self.task_id,
                "deadline": self.deadline.isoformat() if self.deadline else None,
            }
        )
        return base_dict


@dataclass
class ResponseMessage(Message):
    """
    响应消息 - 继承自Message,添加响应特定属性
    """

    success: bool = True
    error_message: str | None = None
    execution_time: float = 0.0
    original_message_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "success": self.success,
                "error_message": self.error_message,
                "execution_time": self.execution_time,
                "original_message_id": self.original_message_id,
            }
        )
        return base_dict


@dataclass
class Channel:
    """
    通信通道数据结构
    """

    id: str
    type: ChannelType
    participants: set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def join(self, participant: str) -> bool:
        """参与者加入通道"""
        self.participants.add(participant)
        return True

    def leave(self, participant: str) -> bool:
        """参与者离开通道"""
        self.participants.discard(participant)
        return True

    def has_participant(self, participant: str) -> bool:
        """检查参与者是否在通道中"""
        return participant in self.participants

    def get_stats(self) -> dict[str, Any]:
        """获取通道统计"""
        return {
            "id": self.id,
            "type": self.type.value,
            "participants": len(self.participants),
            "active": self.is_active,
            "age_seconds": (datetime.now() - self.created_at).total_seconds(),
        }


# =============================================================================
# 工具函数
# =============================================================================


def convert_priority(value: Any) -> MessagePriority:
    """
    将各种优先级表示转换为统一的MessagePriority

    支持的输入格式:
    - MessagePriority枚举
    - 整数 (0-4)
    - 字符串 ('critical', 'high', 'normal', 'low', 'bulk')

    Args:
        value: 优先级值

    Returns:
        MessagePriority枚举

    Raises:
        ValueError: 如果无法转换
    """
    if isinstance(value, MessagePriority):
        return value

    if isinstance(value, int):
        try:
            return MessagePriority(value)
        except ValueError:
            raise ValueError(f"无效的优先级整数: {value},必须在0-4范围内") from None

    if isinstance(value, str):
        value_map = {
            "critical": MessagePriority.CRITICAL,
            "high": MessagePriority.HIGH,
            "normal": MessagePriority.NORMAL,
            "low": MessagePriority.LOW,
            "bulk": MessagePriority.BULK,
            "urgent": MessagePriority.HIGH,  # 兼容别名
            "medium": MessagePriority.NORMAL,  # 兼容别名
        }
        value_lower = value.lower()
        if value_lower in value_map:
            return value_map[value_lower]
        raise ValueError(f"无效的优先级字符串: {value}")

    raise ValueError(f"无法转换优先级类型: {type(value)}")


def convert_message_type(value: Any) -> MessageType:
    """
    将各种消息类型表示转换为统一的MessageType

    Args:
        value: 消息类型值

    Returns:
        MessageType枚举

    Raises:
        ValueError: 如果无法转换
    """
    if isinstance(value, MessageType):
        return value

    if isinstance(value, str):
        try:
            return MessageType(value)
        except ValueError:
            # 尝试常见别名
            alias_map = {
                "msg": MessageType.TEXT,
                "cmd": MessageType.COMMAND,
                "evt": MessageType.EVENT,
            }
            value_lower = value.lower()
            if value_lower in alias_map:
                return alias_map[value_lower]
            raise ValueError(f"无效的消息类型字符串: {value}") from None

    raise ValueError(f"无法转换消息类型: {type(value)}")


def create_message_id() -> str:
    """
    生成唯一的消息ID

    Returns:
        消息ID字符串(格式: msg_<timestamp>_<random>)
    """
    import uuid

    timestamp = int(datetime.now().timestamp() * 1000)
    unique_id = uuid.uuid4().hex[:8]
    return f"msg_{timestamp}_{unique_id}"


def validate_message(message: Message) -> tuple[bool, str | None]:
    """
    验证消息的基本有效性

    Args:
        message: 要验证的消息

    Returns:
        (是否有效, 错误信息)元组
    """
    # 检查基本字段
    if not message.id:
        return False, "消息ID不能为空"

    if not message.sender:
        return False, "发送者不能为空"

    if not message.receiver and message.channel_type not in [
        ChannelType.BROADCAST,
        ChannelType.TOPIC,
    ]:
        return False, "接收者不能为空(广播和主题通道除外)"

    # 检查消息是否过期
    if message.is_expired():
        return False, "消息已过期"

    # 检查内容
    if message.content is None and message.type not in [MessageType.SYSTEM, MessageType.HEARTBEAT]:
        return False, "消息内容不能为空"

    return True, None


# =============================================================================
# 异常定义
# =============================================================================


class CommunicationError(Exception):
    """通信错误基类"""

    pass


class MessageValidationError(CommunicationError):
    """消息验证错误"""

    pass


class MessageExpiredError(CommunicationError):
    """消息已过期错误"""

    pass


class MessageSendError(CommunicationError):
    """消息发送错误"""

    pass


class ChannelNotFoundError(CommunicationError):
    """通道不存在错误"""

    pass


class AuthenticationError(CommunicationError):
    """认证错误"""

    pass


class RateLimitError(CommunicationError):
    """速率限制错误"""

    pass


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "AuthenticationError",
    "Channel",
    "ChannelNotFoundError",
    "ChannelType",
    "CommunicationChannel",
    # 异常
    "CommunicationError",
    "DeliveryMode",
    # 数据类
    "Message",
    "MessageExpiredError",
    # 枚举
    "MessagePriority",
    "MessageSendError",
    "MessageStatus",
    "MessageType",
    "MessageValidationError",
    "Priority",
    "RateLimitError",
    "ResponseMessage",
    "TaskMessage",
    # 兼容性别名
    "TaskPriority",
    "convert_message_type",
    # 工具函数
    "convert_priority",
    "create_message_id",
    "validate_message",
]
