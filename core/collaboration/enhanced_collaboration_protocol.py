#!/usr/bin/env python3
from __future__ import annotations
"""
增强协作协议
Enhanced Collaboration Protocol

提供智能体间的高级协作能力:
1. 消息传递协议 - 标准化消息格式
2. 事件订阅机制 - 智能体事件系统
3. 共享上下文 - 协作上下文管理
4. 协议版本控制 - 向后兼容
5. 错误处理和重试 - 可靠通信
6. 性能监控 - 协作性能追踪

作者: Athena平台团队
创建时间: 2025-12-26
版本: v2.0.0 "协议升级"
"""

import asyncio
import logging
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""

    REQUEST = "request"  # 请求
    RESPONSE = "response"  # 响应
    NOTIFICATION = "notification"  # 通知
    EVENT = "event"  # 事件
    BROADCAST = "broadcast"  # 广播
    STREAM = "stream"  # 流式数据


class MessagePriority(Enum):
    """消息优先级"""

    CRITICAL = 0  # 关键
    HIGH = 1  # 高
    NORMAL = 2  # 正常
    LOW = 3  # 低


class CollaborationProtocol(Enum):
    """协作协议版本"""

    V1_BASIC = "v1.0"  # 基础协议
    V2_ENHANCED = "v2.0"  # 增强协议
    V3_ADVANCED = "v3.0"  # 高级协议


@dataclass
class Message:
    """标准化消息"""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    protocol_version: str = CollaborationProtocol.V2_ENHANCED.value

    # 发送者和接收者
    sender_id: str = ""
    receiver_id: str = ""  # 空字符串表示广播
    reply_to: str | None = None

    # 内容
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    retry_until: datetime | None = None

    # 状态追踪
    correlation_id: str | None = None
    conversation_id: str | None = None

    # 重试
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "type": self.type.value,
            "priority": self.priority.value,
            "protocol_version": self.protocol_version,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "reply_to": self.reply_to,
            "action": self.action,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "correlation_id": self.correlation_id,
            "conversation_id": self.conversation_id,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """从字典创建"""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            type=MessageType(data.get("type", MessageType.REQUEST.value)),
            priority=MessagePriority(data.get("priority", MessagePriority.NORMAL.value)),
            protocol_version=data.get("protocol_version", CollaborationProtocol.V2_ENHANCED.value),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            reply_to=data.get("reply_to"),
            action=data.get("action", ""),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            correlation_id=data.get("correlation_id"),
            conversation_id=data.get("conversation_id"),
            retry_count=data.get("retry_count", 0),
        )


@dataclass
class EventSubscription:
    """事件订阅"""

    subscription_id: str
    subscriber_id: str
    event_type: str
    filter_criteria: dict[str, Any] = field(default_factory=dict)
    callback: Callable | None = None
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


@dataclass
class SharedContext:
    """共享上下文"""

    context_id: str
    participants: list[str] = field(default_factory=list)
    shared_data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None


class EnhancedCollaborationProtocol:
    """
    增强协作协议

    核心功能:
    1. 消息传递 - 可靠的消息传递
    2. 事件订阅 - 发布-订阅模式
    3. 共享上下文 - 智能体间共享数据
    4. 协议兼容 - 版本管理
    5. 错误处理 - 自动重试
    6. 性能监控 - 消息追踪
    """

    def __init__(self):
        # 消息队列(每个智能体一个队列)
        self.message_queues: dict[str, deque[Message]] = defaultdict(lambda: deque(maxlen=10000))

        # 事件订阅
        self.event_subscriptions: dict[str, list[EventSubscription]] = defaultdict(list)

        # 共享上下文
        self.shared_contexts: dict[str, SharedContext] = {}

        # 消息处理器注册
        self.message_handlers: dict[str, Callable] = {}

        # 性能统计
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_failed": 0,
            "events_published": 0,
            "avg_message_latency": 0.0,
            "retry_count": 0,
        }

        # 消息历史(用于追踪)
        self.message_history: deque[Message] = deque(maxlen=10000)

        logger.info("🤝 增强协作协议初始化完成")

    async def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        action: str,
        payload: dict[str, Any],        message_type: MessageType = MessageType.REQUEST,
        priority: MessagePriority = MessagePriority.NORMAL,
        **kwargs,
    ) -> str:
        """发送消息"""
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            action=action,
            payload=payload,
            type=message_type,
            priority=priority,
            **kwargs,
        )

        # 添加到接收者队列
        self.message_queues[receiver_id].append(message)

        # 记录消息
        self.message_history.append(message)
        self.metrics["messages_sent"] += 1

        logger.debug(
            f"📤 消息已发送: {sender_id} -> {receiver_id} " f"({action}, priority: {priority.name})"
        )

        return message.message_id

    async def broadcast_message(
        self,
        sender_id: str,
        action: str,
        payload: dict[str, Any],        exclude: list[str] | None = None,
    ) -> list[str]:
        """广播消息"""
        message_ids = []
        exclude = exclude or []

        # 获取所有已注册的智能体
        for agent_id in self.message_queues:
            if agent_id != sender_id and agent_id not in exclude:
                message_id = await self.send_message(
                    sender_id=sender_id,
                    receiver_id=agent_id,
                    action=action,
                    payload=payload,
                    message_type=MessageType.BROADCAST,
                )
                message_ids.append(message_id)

        logger.info(f"📢 广播消息: {sender_id} -> {len(message_ids)} 个智能体")

        return message_ids

    async def receive_messages(
        self, agent_id: str, limit: int = 10, timeout: float = 1.0
    ) -> list[Message]:
        """接收消息"""
        queue = self.message_queues[agent_id]
        messages = []

        # 等待消息(带超时)
        start_time = datetime.now()
        while len(messages) < limit and (datetime.now() - start_time).total_seconds() < timeout:
            if queue:
                msg = queue.popleft()
                messages.append(msg)
                self.metrics["messages_received"] += 1
            else:
                await asyncio.sleep(0.01)

        return messages

    async def subscribe_event(
        self,
        subscriber_id: str,
        event_type: str,
        callback: Callable | None = None,
        filter_criteria: dict[str, Any] | None = None,
    ) -> str:
        """订阅事件"""
        subscription = EventSubscription(
            subscription_id=str(uuid.uuid4()),
            subscriber_id=subscriber_id,
            event_type=event_type,
            filter_criteria=filter_criteria or {},
            callback=callback,
        )

        self.event_subscriptions[event_type].append(subscription)

        logger.info(f"📬 事件订阅: {subscriber_id} -> {event_type}")

        return subscription.subscription_id

    async def publish_event(
        self, publisher_id: str, event_type: str, event_data: dict[str, Any]
    ) -> int:
        """发布事件"""
        # 获取订阅者
        subscriptions = self.event_subscriptions.get(event_type, [])

        notified_count = 0

        for subscription in subscriptions:
            if not subscription.active:
                continue

            # 检查过滤条件
            if subscription.filter_criteria:
                if not all(event_data.get(k) == v for k, v in subscription.filter_criteria.items()):
                    continue

            # 发送通知
            notification = Message(
                sender_id=publisher_id,
                receiver_id=subscription.subscriber_id,
                action=f"event:{event_type}",
                payload=event_data,
                type=MessageType.EVENT,
            )

            self.message_queues[subscription.subscriber_id].append(notification)

            # 如果有回调函数,执行它
            if subscription.callback:
                try:
                    await subscription.callback(event_data)
                except Exception as e:
                    logger.error(f"事件回调失败: {e}")

            notified_count += 1

        self.metrics["events_published"] += 1

        logger.info(f"📢 事件发布: {event_type} -> {notified_count} 个订阅者")

        return notified_count

    async def create_shared_context(
        self,
        context_id: str,
        participants: list[str],
        initial_data: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
    ) -> SharedContext:
        """创建共享上下文"""
        import datetime as dt

        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + dt.timedelta(seconds=ttl_seconds)

        context = SharedContext(
            context_id=context_id,
            participants=participants,
            shared_data=initial_data or {},
            expires_at=expires_at,
        )

        self.shared_contexts[context_id] = context

        # 通知参与者
        for participant_id in participants:
            await self.send_message(
                sender_id="system",
                receiver_id=participant_id,
                action="context_created",
                payload={"context_id": context_id, "participants": participants},
            )

        logger.info(f"📝 共享上下文创建: {context_id} ({len(participants)} 参与者)")

        return context

    async def update_shared_context(
        self, context_id: str, updates: dict[str, Any], updater_id: str
    ) -> bool:
        """更新共享上下文"""
        if context_id not in self.shared_contexts:
            return False

        context = self.shared_contexts[context_id]

        # 检查权限
        if updater_id not in context.participants:
            logger.warning(f"未授权的上下文更新: {updater_id} -> {context_id}")
            return False

        # 更新数据
        context.shared_data.update(updates)
        context.updated_at = datetime.now()

        # 通知其他参与者
        for participant_id in context.participants:
            if participant_id != updater_id:
                await self.send_message(
                    sender_id="system",
                    receiver_id=participant_id,
                    action="context_updated",
                    payload={"context_id": context_id, "updates": updates, "updater": updater_id},
                )

        logger.debug(f"📝 共享上下文更新: {context_id} by {updater_id}")

        return True

    async def get_shared_context(
        self, context_id: str, requester_id: str
    ) -> SharedContext | None:
        """获取共享上下文"""
        context = self.shared_contexts.get(context_id)

        if not context:
            return None

        # 检查权限
        if requester_id not in context.participants:
            logger.warning(f"未授权的上下文访问: {requester_id} -> {context_id}")
            return None

        # 检查是否过期
        if context.expires_at and datetime.now() > context.expires_at:
            logger.info(f"共享上下文已过期: {context_id}")
            del self.shared_contexts[context_id]
            return None

        return context

    def register_message_handler(self, action: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[action] = handler
        logger.debug(f"📝 消息处理器已注册: {action}")

    async def process_message(self, message: Message) -> Any | None:
        """处理消息"""
        handler = self.message_handlers.get(message.action)

        if handler:
            try:
                result = await handler(message)
                return result
            except Exception as e:
                logger.error(f"消息处理失败: {message.action} - {e}")
                self.metrics["messages_failed"] += 1
                return None
        else:
            logger.warning(f"未找到消息处理器: {message.action}")
            return None

    async def get_protocol_metrics(self) -> dict[str, Any]:
        """获取协议指标"""
        return {
            "messages": {
                "sent": self.metrics["messages_sent"],
                "received": self.metrics["messages_received"],
                "failed": self.metrics["messages_failed"],
                "success_rate": (
                    (self.metrics["messages_sent"] - self.metrics["messages_failed"])
                    / max(self.metrics["messages_sent"], 1)
                ),
            },
            "events": {
                "published": self.metrics["events_published"],
                "subscriptions": sum(len(subs) for subs in self.event_subscriptions.values()),
            },
            "contexts": {
                "active": len(self.shared_contexts),
                "total_participants": sum(
                    len(ctx.participants) for ctx in self.shared_contexts.values()
                ),
            },
            "performance": {
                "avg_latency": self.metrics["avg_message_latency"],
                "queue_sizes": {
                    agent_id: len(queue) for agent_id, queue in self.message_queues.items()
                },
            },
        }


# 导出便捷函数
_collaboration_protocol: EnhancedCollaborationProtocol | None = None


def get_collaboration_protocol() -> EnhancedCollaborationProtocol:
    """获取协作协议单例"""
    global _collaboration_protocol
    if _collaboration_protocol is None:
        _collaboration_protocol = EnhancedCollaborationProtocol()
    return _collaboration_protocol
