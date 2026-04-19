#!/usr/bin/env python3
from __future__ import annotations
"""
Athena通信系统 - Agent协作兼容层
Agent Collaboration Compatibility Layer

提供向后兼容的接口,逐步迁移到统一类型系统。

主要功能:
1. 保持旧TaskMessage/ResponseMessage接口兼容
2. 提供MessageBus兼容包装器
3. 支持类型转换和适配

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import inspect
import logging
from collections.abc import Callable
from typing import Any

from ..types import (
    ChannelType,
    create_message_id,
)
from ..types import (
    Message as UnifiedMessage,
)
from ..types import (
    MessagePriority as UnifiedPriority,
)
from ..types import (
    MessageType as UnifiedMessageType,
)

logger = logging.getLogger(__name__)

# =============================================================================
# 兼容性别名
# =============================================================================

TaskPriority = UnifiedPriority
Priority = UnifiedPriority

# =============================================================================
# 兼容性消息类
# =============================================================================


class TaskMessage(UnifiedMessage):
    """
    任务消息 - 兼容层

    保持与旧TaskMessage的接口兼容,内部使用统一Message类型。
    """

    def __init__(
        self,
        task_id: str = "",
        sender_id: str = "",
        recipient_id: str | None = None,
        task_type: str = "",
        content: dict[str, Any] | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        deadline: str | None = None,
        **kwargs,
    ):
        # 转换为统一类型
        metadata = {"task_type": task_type, "deadline": deadline}
        # 添加额外元数据
        for key, value in kwargs.items():
            if key not in [
                "task_id",
                "sender_id",
                "recipient_id",
                "task_type",
                "content",
                "priority",
                "deadline",
            ]:
                metadata[key] = value

        super().__init__(
            id=task_id or create_message_id(),
            sender=sender_id,
            receiver=recipient_id or "",
            type=UnifiedMessageType.TASK,
            content=content or {},
            priority=priority,
            channel_type=ChannelType.DIRECT,
            metadata=metadata,
        )
        self.task_type = task_type
        self.deadline = deadline

    @property
    def task_id(self) -> str:
        """任务ID(兼容属性)"""
        return self.id

    @property
    def sender_id(self) -> str:
        """发送者ID(兼容属性)"""
        return self.sender

    @property
    def recipient_id(self) -> str:
        """接收者ID(兼容属性)"""
        return self.receiver

    def to_dict(self) -> dict[str, Any]:
        """转换为字典(兼容旧接口)"""
        return {
            "task_id": self.id,
            "sender_id": self.sender,
            "recipient_id": self.receiver,
            "message_type": "task",
            "task_type": self.task_type,
            "content": self.content,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "deadline": self.deadline,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskMessage":
        """从字典创建TaskMessage"""
        return cls(
            task_id=data.get("task_id", ""),
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id"),
            task_type=data.get("task_type", ""),
            content=data.get("content"),
            priority=UnifiedPriority(data.get("priority", 2)),
            deadline=data.get("deadline"),
        )


class ResponseMessage(UnifiedMessage):
    """响应消息 - 兼容层"""

    def __init__(
        self,
        task_id: str = "",
        sender_id: str = "",
        recipient_id: str = "",
        success: bool = True,
        content: dict[str, Any] | None = None,
        error_message: str | None = None,
        execution_time: float = 0.0,
    ):
        response_content = {
            "task_id": task_id,
            "success": success,
            "content": content or {},
            "error_message": error_message,
            "execution_time": execution_time,
        }

        super().__init__(
            id=task_id or create_message_id(),
            sender=sender_id,
            receiver=recipient_id,
            type=UnifiedMessageType.RESPONSE,
            content=response_content,
            priority=TaskPriority.NORMAL,
            channel_type=ChannelType.DIRECT,
        )
        self.success = success
        self.error_message = error_message
        self.execution_time = execution_time

    @property
    def task_id(self) -> str:
        """任务ID(兼容属性)"""
        return self.metadata.get("task_id", self.id)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典(兼容旧接口)"""
        return {
            "task_id": self.id,
            "sender_id": self.sender,
            "recipient_id": self.receiver,
            "message_type": "response",
            "success": self.success,
            "content": self.content,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# 兼容性MessageBus包装器
# =============================================================================


class AgentMessageBus:
    """
    Agent消息总线 - 兼容层

    保持与旧MessageBus的接口兼容,内部可以委托给UnifiedMessageBus。
    提供平滑的迁移路径。
    """

    def __init__(self, unified_bus=None):
        """
        初始化Agent消息总线

        Args:
            unified_bus: 统一消息总线实例(可选)
        """
        self._unified_bus = unified_bus
        self.subscribers: dict[str, list[Callable]] = {}
        self.message_history: list[UnifiedMessage] = []
        self._max_history = 1000

        logger.info("Agent消息总线(兼容层)初始化完成")

    async def start(self):
        """启动消息总线"""
        if self._unified_bus:
            await self._unified_bus.start()
        logger.info("Agent消息总线已启动")

    async def stop(self):
        """停止消息总线"""
        if self._unified_bus:
            await self._unified_bus.stop()
        logger.info("Agent消息总线已停止")

    def subscribe(self, agent_id: str, callback: Callable) -> Any:
        """
        订阅消息

        Args:
            agent_id: Agent ID
            callback: 回调函数
        """
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
        logger.info(f"Agent {agent_id} 已订阅消息")

    def unsubscribe(self, agent_id: str) -> Any:
        """
        取消订阅

        Args:
            agent_id: Agent ID
        """
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
            logger.info(f"Agent {agent_id} 已取消订阅")

    async def send_message(self, message: TaskMessage | ResponseMessage | UnifiedMessage):
        """
        发送任务消息

        Args:
            message: 任务消息
        """
        # 记录历史
        self._add_to_history(message)

        # 如果有统一总线,委托发送
        if self._unified_bus:
            await self._unified_bus.send(message)

        # 通知订阅者
        await self._notify_subscribers(message)

        logger.info(f"发送任务消息: {message.id} -> {message.receiver}")

    async def send_response(self, response: ResponseMessage):
        """
        发送响应消息

        Args:
            response: 响应消息
        """
        await self.send_message(response)

    async def broadcast(self, message: UnifiedMessage):
        """
        广播消息

        Args:
            message: 消息
        """
        self._add_to_history(message)

        if self._unified_bus:
            await self._unified_bus.broadcast(message)

        await self._notify_subscribers(message)

    def get_message_history(self, limit: int = 100) -> list[dict]:
        """
        获取消息历史

        Args:
            limit: 返回数量限制

        Returns:
            消息历史列表
        """
        history = self.message_history[-limit:]
        return [
            (
                msg.to_dict()
                if hasattr(msg, "to_dict")
                else {
                    "id": msg.id,
                    "sender": msg.sender,
                    "type": msg.type.value,
                    "timestamp": msg.timestamp.isoformat(),
                }
            )
            for msg in history
        ]

    def _add_to_history(self, message: UnifiedMessage) -> Any:
        """添加到历史记录"""
        self.message_history.append(message)
        if len(self.message_history) > self._max_history:
            self.message_history = self.message_history[-self._max_history :]

    async def _notify_subscribers(self, message: UnifiedMessage):
        """通知订阅者"""
        for agent_id, callbacks in self.subscribers.items():
            # 过滤:不发送给自己
            if message.sender == agent_id:
                continue

            # 过滤:检查接收者
            if message.receiver and message.receiver != agent_id:
                continue

            # 调用回调
            for callback in callbacks:
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"订阅者回调错误 {agent_id}: {e}")


# =============================================================================
# 便捷函数
# =============================================================================


def create_task_message(
    task_id: str,
    sender_id: str,
    recipient_id: str | None = None,
    task_type: str = "",
    content: dict[str, Any] | None = None,
    priority: TaskPriority = TaskPriority.NORMAL,
) -> TaskMessage:
    """创建任务消息"""
    return TaskMessage(
        task_id=task_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        task_type=task_type,
        content=content,
        priority=priority,
    )


def create_response_message(
    task_id: str,
    sender_id: str,
    recipient_id: str,
    success: bool = True,
    content: dict[str, Any] | None = None,
) -> ResponseMessage:
    """创建响应消息"""
    return ResponseMessage(
        task_id=task_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        success=success,
        content=content,
    )


def create_message_bus(unified_bus=None) -> AgentMessageBus:
    """创建Agent消息总线"""
    return AgentMessageBus(unified_bus)


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 兼容性MessageBus
    "AgentMessageBus",
    "MessageBus",  # 别名
    "Priority",
    "ResponseMessage",
    # 兼容性消息类
    "TaskMessage",
    # 兼容性别名
    "TaskPriority",
    "create_message_bus",
    "create_response_message",
    # 便捷函数
    "create_task_message",
]

# 别名
MessageBus = AgentMessageBus
