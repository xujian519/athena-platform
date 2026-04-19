#!/usr/bin/env python3
from __future__ import annotations
"""
消息持久化基础接口
Base Message Persistence Interface

定义消息持久化的抽象接口，所有持久化实现必须遵循此接口。

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.communication.types import Message

logger = logging.getLogger(__name__)


class MessageState(str, Enum):
    """消息状态枚举"""

    PENDING = "pending"  # 等待处理
    QUEUED = "queued"  # 已排队
    PROCESSING = "processing"  # 处理中
    SENT = "sent"  # 已发送
    DELIVERED = "delivered"  # 已投递
    ACKNOWLEDGED = "acknowledged"  # 已确认
    FAILED = "failed"  # 失败
    TIMEOUT = "timeout"  # 超时
    CANCELLED = "cancelled"  # 已取消
    DEAD_LETTER = "dead_letter"  # 死信


@dataclass
class PersistedMessage:
    """持久化消息数据结构"""

    message: Message  # 原始消息
    state: MessageState  # 当前状态
    attempt_count: int = 0  # 尝试次数
    max_attempts: int = 3  # 最大尝试次数
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    expires_at: datetime | None = None  # 过期时间
    error_message: str | None = None  # 错误信息
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "message": self.message.to_dict(),
            "state": self.state.value,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersistedMessage":
        """从字典创建"""
        return cls(
            message=Message.from_dict(data["message"]),
            state=MessageState(data["state"]),
            attempt_count=data.get("attempt_count", 0),
            max_attempts=data.get("max_attempts", 3),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            ),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
        )


class BaseMessagePersistence(ABC):
    """
    消息持久化抽象基类

    定义所有持久化实现必须遵循的接口。
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化持久化后端

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化持久化后端

        Returns:
            是否初始化成功
        """
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        关闭持久化后端

        Returns:
            是否关闭成功
        """
        pass

    @abstractmethod
    async def save_message(
        self, message: Message, state: MessageState = MessageState.PENDING
    ) -> bool:
        """
        保存消息

        Args:
            message: 要保存的消息
            state: 消息状态

        Returns:
            是否保存成功
        """
        pass

    @abstractmethod
    async def get_message(self, message_id: str) -> PersistedMessage | None:
        """
        获取消息

        Args:
            message_id: 消息ID

        Returns:
            持久化消息，如果不存在返回None
        """
        pass

    @abstractmethod
    async def update_message_state(
        self, message_id: str, state: MessageState, error_message: str | None = None
    ) -> bool:
        """
        更新消息状态

        Args:
            message_id: 消息ID
            state: 新状态
            error_message: 错误信息（可选）

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    async def increment_attempt(self, message_id: str) -> bool:
        """
        增加消息尝试次数

        Args:
            message_id: 消息ID

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    async def delete_message(self, message_id: str) -> bool:
        """
        删除消息

        Args:
            message_id: 消息ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    async def get_messages_by_state(
        self, state: MessageState, limit: int = 100
    ) -> list[PersistedMessage]:
        """
        按状态获取消息

        Args:
            state: 消息状态
            limit: 最大返回数量

        Returns:
            持久化消息列表
        """
        pass

    @abstractmethod
    async def get_expired_messages(self) -> list[PersistedMessage]:
        """
        获取所有过期消息

        Returns:
            过期消息列表
        """
        pass

    @abstractmethod
    async def get_failed_messages(self) -> list[PersistedMessage]:
        """
        获取所有失败消息

        Returns:
            失败消息列表
        """
        pass

    @abstractmethod
    async def move_to_dead_letter(
        self, message_id: str, reason: str
    ) -> bool:
        """
        将消息移至死信队列

        Args:
            message_id: 消息ID
            reason: 移动原因

        Returns:
            是否移动成功
        """
        pass

    @abstractmethod
    async def get_dead_letter_messages(self) -> list[PersistedMessage]:
        """
        获取死信队列中的所有消息

        Returns:
            死信消息列表
        """
        pass

    @abstractmethod
    async def clear_dead_letter(self, older_than: datetime | None = None) -> int:
        """
        清理死信队列

        Args:
            older_than: 清理早于此时间的消息，None表示清理全部

        Returns:
            清理的消息数量
        """
        pass

    @abstractmethod
    async def get_queue_size(self, state: MessageState | None = None) -> int:
        """
        获取队列大小

        Args:
            state: 消息状态，None表示所有状态

        Returns:
            队列大小
        """
        pass

    async def cleanup_expired_messages(self) -> int:
        """
        清理过期消息的便捷方法

        Returns:
            清理的消息数量
        """
        expired = await self.get_expired_messages()
        count = 0
        for msg in expired:
            if await self.delete_message(msg.message.id):
                count += 1
        return count

    async def retry_failed_messages(self, max_retries: int = 3) -> int:
        """
        重试失败消息的便捷方法

        Args:
            max_retries: 最大重试次数

        Returns:
            重试的消息数量
        """
        failed = await self.get_failed_messages()
        count = 0
        for msg in failed:
            if msg.attempt_count < max_retries:
                await self.update_message_state(msg.message.id, MessageState.PENDING)
                count += 1
        return count


class InMemoryPersistence(BaseMessagePersistence):
    """
    内存持久化实现

    用于测试和开发环境，不提供真正的持久化。
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._messages: dict[str, PersistedMessage] = {}
        self._state_index: dict[MessageState, set[str]] = {
            state: set() for state in MessageState
        }
        self.logger.info("使用内存持久化（仅用于测试）")

    async def initialize(self) -> bool:
        """初始化"""
        self.logger.info("内存持久化初始化完成")
        return True

    async def shutdown(self) -> bool:
        """关闭"""
        self._messages.clear()
        for state_set in self._state_index.values():
            state_set.clear()
        self.logger.info("内存持久化已关闭")
        return True

    async def save_message(
        self, message: Message, state: MessageState = MessageState.PENDING
    ) -> bool:
        """保存消息"""
        persisted = PersistedMessage(message=message, state=state)
        self._messages[message.id] = persisted
        self._state_index[state].add(message.id)
        return True

    async def get_message(self, message_id: str) -> PersistedMessage | None:
        """获取消息"""
        return self._messages.get(message_id)

    async def update_message_state(
        self, message_id: str, state: MessageState, error_message: str | None = None
    ) -> bool:
        """更新消息状态"""
        if message_id not in self._messages:
            return False

        persisted = self._messages[message_id]

        # 从旧状态索引中移除
        self._state_index[persisted.state].discard(message_id)

        # 更新状态
        persisted.state = state
        persisted.updated_at = datetime.now()
        if error_message:
            persisted.error_message = error_message

        # 添加到新状态索引
        self._state_index[state].add(message_id)

        return True

    async def increment_attempt(self, message_id: str) -> bool:
        """增加尝试次数"""
        if message_id not in self._messages:
            return False

        persisted = self._messages[message_id]
        persisted.attempt_count += 1
        persisted.updated_at = datetime.now()
        return True

    async def delete_message(self, message_id: str) -> bool:
        """删除消息"""
        if message_id not in self._messages:
            return False

        persisted = self._messages[message_id]
        self._state_index[persisted.state].discard(message_id)
        del self._messages[message_id]
        return True

    async def get_messages_by_state(
        self, state: MessageState, limit: int = 100
    ) -> list[PersistedMessage]:
        """按状态获取消息"""
        message_ids = list(self._state_index.get(state, set()))[:limit]
        return [self._messages[mid] for mid in message_ids if mid in self._messages]

    async def get_expired_messages(self) -> list[PersistedMessage]:
        """获取过期消息"""
        now = datetime.now()
        expired = []
        for msg in self._messages.values():
            if msg.expires_at and msg.expires_at < now:
                expired.append(msg)
        return expired

    async def get_failed_messages(self) -> list[PersistedMessage]:
        """获取失败消息"""
        return await self.get_messages_by_state(MessageState.FAILED, limit=1000)

    async def move_to_dead_letter(
        self, message_id: str, reason: str
    ) -> bool:
        """移至死信队列"""
        if message_id not in self._messages:
            return False

        await self.update_message_state(
            message_id, MessageState.DEAD_LETTER, error_message=reason
        )
        self._messages[message_id].metadata["dead_letter_reason"] = reason
        return True

    async def get_dead_letter_messages(self) -> list[PersistedMessage]:
        """获取死信消息"""
        return await self.get_messages_by_state(MessageState.DEAD_LETTER, limit=1000)

    async def clear_dead_letter(self, older_than: datetime | None = None) -> int:
        """清理死信队列"""
        dead_letters = await self.get_dead_letter_messages()
        count = 0

        for msg in dead_letters:
            if older_than is None or msg.updated_at < older_than:
                if await self.delete_message(msg.message.id):
                    count += 1

        return count

    async def get_queue_size(self, state: MessageState | None = None) -> int:
        """获取队列大小"""
        if state is None:
            return len(self._messages)
        return len(self._state_index.get(state, set()))


__all__ = [
    "MessageState",
    "PersistedMessage",
    "BaseMessagePersistence",
    "BasePersistenceBackend",  # 别名
    "PersistenceConfig",
    "InMemoryPersistence",
]


# =============================================================================
# === 别名和兼容性 ===
# =============================================================================

# 为保持兼容性，提供 BasePersistenceBackend 作为别名
BasePersistenceBackend = BaseMessagePersistence


# =============================================================================
# === 配置类 ===
# =============================================================================

@dataclass
class PersistenceConfig:
    """持久化配置"""
    backend: str = "memory"  # memory, redis, file
    backend_config: dict[str, Any] = field(default_factory=dict)
    max_size: int = 10000
    enable_compression: bool = False
    enable_encryption: bool = False
    ttl: int | None = None  # 消息生存时间（秒）
