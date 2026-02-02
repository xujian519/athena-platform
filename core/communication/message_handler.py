#!/usr/bin/env python3
"""
消息处理器 - 兼容性实现
Message Handler - Compatibility Implementation

为优化后的系统提供消息处理功能的兼容性接口
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""

    TEXT = "text"
    COMMAND = "command"
    EVENT = "event"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class MessagePriority(Enum):
    """消息优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """消息数据结构"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.TEXT
    priority: MessagePriority = MessagePriority.NORMAL
    sender: str = ""
    receiver: str = ""
    content: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: str | None = None
    expires_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3


class MessageHandler:
    """消息处理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.message_handlers: dict[str, Callable] = {}
        self.message_queue = asyncio.Queue()
        self.processed_messages: dict[str, Message] = {}
        self.failed_messages: dict[str, Message] = {}
        self.initialized = False
        self.running = False
        self.max_queue_size = self.config.get("max_queue_size", 1000)
        self.batch_size = self.config.get("batch_size", 10)
        self.batch_timeout = self.config.get("batch_timeout", 1.0)

    async def initialize(self):
        """初始化消息处理器"""
        if self.initialized:
            return

        try:
            self.running = True

            # 启动消息处理循环
            asyncio.create_task(self._message_processor())

            self.initialized = True
            logger.info("✅ 消息处理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 消息处理器初始化失败: {e}")
            raise

    async def shutdown(self):
        """关闭消息处理器"""
        self.running = False
        logger.info("消息处理器已关闭")

    def register_handler(self, message_type: str, handler: Callable) -> Any:
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        logger.info(f"注册消息处理器: {message_type}")

    def unregister_handler(self, message_type: str) -> Any:
        """注销消息处理器"""
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            logger.info(f"注销消息处理器: {message_type}")

    async def send_message(
        self,
        receiver: str,
        content: Any,
        message_type: MessageType = MessageType.TEXT,
        priority: MessagePriority = MessagePriority.NORMAL,
        sender: str = "",
        reply_to: str | None = None,
        metadata: dict[str, Any] | None = None,
        expires_in: int | None = None,
    ) -> str:
        """
        发送消息

        Args:
            receiver: 接收者
            content: 消息内容
            message_type: 消息类型
            priority: 消息优先级
            sender: 发送者
            reply_to: 回复的消息ID
            metadata: 元数据
            expires_in: 过期时间(秒)

        Returns:
            消息ID
        """
        message = Message(
            type=message_type,
            priority=priority,
            sender=sender,
            receiver=receiver,
            content=content,
            metadata=metadata or {},
            reply_to=reply_to,
        )

        if expires_in:
            message.expires_at = datetime.now() + timedelta(seconds=expires_in)

        await self.message_queue.put(message)
        logger.debug(f"发送消息: {message.id} -> {receiver}")

        return message.id

    async def broadcast_message(
        self,
        content: Any,
        message_type: MessageType = MessageType.TEXT,
        priority: MessagePriority = MessagePriority.NORMAL,
        sender: str = "",
        receivers: list["key"] = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        广播消息

        Args:
            content: 消息内容
            message_type: 消息类型
            priority: 消息优先级
            sender: 发送者
            receivers: 接收者列表,None表示广播给所有
            metadata: 元数据

        Returns:
            消息ID列表
        """
        if not receivers:
            # 广播给所有注册的接收者
            receivers = list(self.message_handlers.keys())

        message_ids = []
        for receiver in receivers:
            message_id = await self.send_message(
                receiver=receiver,
                content=content,
                message_type=message_type,
                priority=priority,
                sender=sender,
                metadata=metadata,
            )
            message_ids.append(message_id)

        return message_ids

    async def get_message(self, message_id: str) -> Message | None:
        """获取消息"""
        return self.processed_messages.get(message_id)

    async def get_message_status(self, message_id: str) -> str | None:
        """获取消息状态"""
        if message_id in self.processed_messages:
            return "processed"
        elif message_id in self.failed_messages:
            return "failed"
        else:
            return "pending"

    async def _message_processor(self):
        """消息处理循环"""
        while self.running:
            try:
                # 批量处理消息
                messages = await self._get_message_batch()

                if messages:
                    await self._process_message_batch(messages)

            except Exception as e:
                logger.error(f"消息处理循环异常: {e}")
                await asyncio.sleep(1)

    async def _get_message_batch(self) -> list[Message]:
        """获取消息批次"""
        messages = []
        timeout = self.batch_timeout

        try:
            # 获取第一个消息
            message = await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
            messages.append(message)

            # 尝试获取更多消息
            while len(messages) < self.batch_size:
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
                    messages.append(message)
                except asyncio.TimeoutError:
                    break

        except asyncio.TimeoutError:
            logger.warning(f"连接或超时错误: {e}")

        return messages

    async def _process_message_batch(self, messages: list[Message]):
        """处理消息批次"""
        for message in messages:
            await self._process_single_message(message)

    async def _process_single_message(self, message: Message):
        """处理单个消息"""
        try:
            # 检查消息是否过期
            if message.expires_at and datetime.now() > message.expires_at:
                logger.debug(f"消息已过期: {message.id}")
                return

            # 查找处理器
            handler = None
            if message.type.value in self.message_handlers:
                handler = self.message_handlers[message.type.value]
            elif "default" in self.message_handlers:
                handler = self.message_handlers["default"]

            if handler:
                try:
                    # 调用处理器
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        # 在线程池中运行同步处理器
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, handler, message)

                    # 记录处理成功
                    self.processed_messages[message.id] = message
                    logger.debug(f"消息处理成功: {message.id}")

                except Exception as e:
                    logger.error(f"消息处理失败: {message.id} - {e}")
                    await self._handle_message_failure(message, str(e))
            else:
                logger.warning(f"未找到消息处理器: {message.type.value}")
                await self._handle_message_failure(message, "未找到处理器")

        except Exception as e:
            logger.error(f"消息处理异常: {message.id} - {e}")
            await self._handle_message_failure(message, str(e))

    async def _handle_message_failure(self, message: Message, error: str):
        """处理消息失败"""
        message.retry_count += 1

        if message.retry_count <= message.max_retries:
            # 重新入队
            await self.message_queue.put(message)
            logger.info(f"消息重新入队 ({message.retry_count}/{message.max_retries}): {message.id}")
        else:
            # 标记为失败
            self.failed_messages[message.id] = message
            logger.error(f"消息最终失败: {message.id} - {error}")

    async def send_command(
        self,
        receiver: str,
        command: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        sender: str = "",
    ) -> str:
        """发送命令消息"""
        content = {"command": command, "args": args or [], "kwargs": kwargs or {}}

        return await self.send_message(
            receiver=receiver,
            content=content,
            message_type=MessageType.COMMAND,
            priority=MessagePriority.HIGH,
            sender=sender,
        )

    async def send_response(
        self, receiver: str, original_message_id: str, content: Any, sender: str = ""
    ) -> str:
        """发送响应消息"""
        return await self.send_message(
            receiver=receiver,
            content=content,
            message_type=MessageType.RESPONSE,
            reply_to=original_message_id,
            sender=sender,
        )

    async def send_notification(
        self, receiver: str, title: str, content: Any, level: str = "info", sender: str = ""
    ) -> str:
        """发送通知消息"""
        message_content = {"title": title, "content": content, "level": level}

        return await self.send_message(
            receiver=receiver,
            content=message_content,
            message_type=MessageType.NOTIFICATION,
            sender=sender,
        )

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_messages = len(self.processed_messages) + len(self.failed_messages)
        queue_size = self.message_queue.qsize()

        # 按类型统计
        type_counts = {}
        for message in self.processed_messages.values():
            type_name = message.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total_processed": len(self.processed_messages),
            "total_failed": len(self.failed_messages),
            "queue_size": queue_size,
            "success_rate": (
                len(self.processed_messages) / total_messages if total_messages > 0 else 0
            ),
            "type_distribution": type_counts,
            "registered_handlers": list(self.message_handlers.keys()),
        }


# 兼容性函数
def create_message_handler(config: dict[str, Any] | None = None) -> MessageHandler:
    """创建消息处理器实例"""
    return MessageHandler(config)


# 向后兼容
MessageHandler = MessageHandler
