#!/usr/bin/env python3
from __future__ import annotations
"""
Agent通信系统
Communication System for Multi-Agent Collaboration

负责Agent间的消息传递和协调通信
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举"""

    TASK = "task"
    RESPONSE = "response"
    COORDINATION = "coordination"
    STATUS_UPDATE = "status_update"
    ERROR = "error"


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskMessage:
    """任务消息"""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str | None = None  # None表示广播
    message_type: MessageType = MessageType.TASK
    task_type: str = ""  # search, analysis, creative等
    content: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "task_type": self.task_type,
            "content": self.content,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "deadline": self.deadline,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskMessage":
        """从字典创建消息对象"""
        task_id_value = data.get("task_id")
        task_id: str = task_id_value if task_id_value else str(uuid.uuid4())  # type: ignore[assignment]

        return cls(
            task_id=task_id,
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id"),
            message_type=MessageType(data.get("message_type", "task")),
            task_type=data.get("task_type", ""),
            content=data.get("content", {}),
            priority=TaskPriority(data.get("priority", 2)),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            deadline=data.get("deadline"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ResponseMessage:
    """响应消息"""

    task_id: str = ""
    sender_id: str = ""
    recipient_id: str = ""
    message_type: MessageType = MessageType.RESPONSE
    success: bool = True
    content: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "success": self.success,
            "content": self.content,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class MessageBus:
    """消息总线 - 负责Agent间的通信"""

    def __init__(self):
        self.subscribers: dict[str, list[Callable[..., Any]]] = {}
        self.message_queue: asyncio.Queue[Any] = asyncio.Queue()
        self.running = False
        self.message_history: list[dict[str, Any]] = []
        self.max_history = 1000

    async def start(self):
        """启动消息总线"""
        self.running = True
        logger.info("📡 Agent消息总线启动")
        asyncio.create_task(self._process_messages())

    async def stop(self):
        """停止消息总线"""
        self.running = False
        logger.info("📡 Agent消息总线停止")

    def subscribe(self, agent_id: str, callback: Callable[..., Any]) -> Any:
        """订阅消息"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
        logger.info(f"📢 Agent {agent_id} 已订阅消息总线")

    def unsubscribe(self, agent_id: str) -> Any:
        """取消订阅"""
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
            logger.info(f"📢 Agent {agent_id} 已取消订阅")

    async def send_message(self, message: TaskMessage):
        """发送任务消息"""
        await self.message_queue.put(message)
        logger.debug(f"📤 发送消息: {message.task_id} -> {message.recipient_id or '广播'}")

    async def send_response(self, response: ResponseMessage):
        """发送响应消息"""
        await self.message_queue.put(response)
        logger.debug(f"📤 发送响应: {response.task_id} <- {response.sender_id}")

    async def _process_messages(self):
        """处理消息队列"""
        while self.running:
            try:
                # 等待消息
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)

                # 记录消息历史
                self._record_message(message)

                # 分发消息
                await self._dispatch_message(message)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ 消息处理错误: {e}")

    async def _dispatch_message(self, message: Any) -> None:
        """分发消息给订阅者"""
        if isinstance(message, TaskMessage):
            # 任务消息
            if message.recipient_id:
                # 指定接收者
                if message.recipient_id in self.subscribers:
                    for callback in self.subscribers[message.recipient_id]:
                        await self._safe_call(callback, message)
            else:
                # 广播消息
                for agent_id, callbacks in self.subscribers.items():
                    if agent_id != message.sender_id:  # 不发送给自己
                        for callback in callbacks:
                            await self._safe_call(callback, message)

        elif isinstance(message, ResponseMessage):
            # 响应消息 - 发送给指定接收者
            if message.recipient_id in self.subscribers:
                for callback in self.subscribers[message.recipient_id]:
                    await self._safe_call(callback, message)

    async def _safe_call(self, callback: Callable[..., Any], message: Any) -> None:
        """安全调用回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
        except Exception as e:
            logger.error(f"❌ 回调函数执行失败: {e}")

    def _record_message(self, message: Any) -> None:
        """记录消息历史"""
        message_dict = (
            message.to_dict()
            if hasattr(message, "to_dict")
            else {"timestamp": datetime.now().isoformat(), "type": "unknown"}
        )

        self.message_history.append(message_dict)

        # 限制历史记录数量
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history :]

    def get_message_history(
        self, agent_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """获取消息历史"""
        history = self.message_history

        if agent_id:
            # 过滤特定Agent的消息
            history = [
                msg
                for msg in history
                if msg.get("sender_id") == agent_id or msg.get("recipient_id") == agent_id
            ]

        return history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """获取消息总线统计信息"""
        return {
            "subscribers_count": len(self.subscribers),
            "subscribers": list(self.subscribers.keys()),
            "queue_size": self.message_queue.qsize(),
            "message_history_count": len(self.message_history),
            "running": self.running,
        }


# 全局消息总线实例
_message_bus = None


def get_message_bus() -> MessageBus:
    """获取全局消息总线实例"""
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus
