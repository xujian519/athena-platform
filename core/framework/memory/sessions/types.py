#!/usr/bin/env python3
"""
会话记忆数据类型定义

定义会话记忆系统的核心数据结构。

作者: Athena平台团队
创建时间: 2026-04-21
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """会话状态"""

    ACTIVE = "active"  # 活跃
    SUSPENDED = "suspended"  # 暂停
    CLOSED = "closed"  # 关闭
    ARCHIVED = "archived"  # 已归档


class MessageRole(Enum):
    """消息角色"""

    USER = "user"  # 用户
    ASSISTANT = "assistant"  # 助手
    SYSTEM = "system"  # 系统
    TOOL = "tool"  # 工具


@dataclass
class SessionMessage:
    """会话消息"""

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    message_id: str = ""

    def __post_init__(self):
        """初始化后处理"""
        if not self.message_id:
            # 生成消息ID
            import uuid
            self.message_id = f"msg_{uuid.uuid4().hex[:8]}"

    def __hash__(self) -> int:
        """实现哈希方法，仅基于message_id"""
        return hash(self.message_id)

    def __eq__(self, other) -> bool:
        """实现相等比较，仅基于message_id"""
        if not isinstance(other, SessionMessage):
            return False
        return self.message_id == other.message_id


@dataclass
class SessionContext:
    """会话上下文"""

    session_id: str
    user_id: str
    agent_id: str
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)
    total_tokens: int = 0
    message_count: int = 0

    def update_activity(self) -> None:
        """更新活动时间"""
        self.last_activity = datetime.now()

    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """检查会话是否过期

        Args:
            timeout_seconds: 超时时间（秒）

        Returns:
            bool: 是否过期
        """
        delta = datetime.now() - self.last_activity
        return delta.total_seconds() > timeout_seconds


@dataclass
class SessionSummary:
    """会话摘要"""

    session_id: str
    title: str
    summary: str
    key_points: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0


@dataclass
class SessionMemory:
    """会话记忆"""

    context: SessionContext
    messages: list[SessionMessage] = field(default_factory=list)
    summary: Optional[SessionSummary] = None
    embeddings: dict[str, list[float] = field(default_factory=dict)

    def add_message(self, message: SessionMessage) -> None:
        """添加消息

        Args:
            message: 消息
        """
        self.messages.append(message)
        self.context.message_count += 1
        self.context.total_tokens += message.token_count
        self.context.update_activity()

    def get_recent_messages(
        self,
        count: int = 10,
        role: Optional[MessageRole] = None,
    ) -> list[SessionMessage]:
        """获取最近的消息

        Args:
            count: 消息数量
            role: 消息角色（None表示所有）

        Returns:
            list[SessionMessage]: 消息列表
        """
        messages = self.messages[-count:]

        if role:
            messages = [m for m in messages if m.role == role]

        return messages

    def calculate_tokens(self) -> int:
        """计算总token数

        Returns:
            int: 总token数
        """
        return sum(m.token_count for m in self.messages)


__all__ = [
    "SessionStatus",
    "MessageRole",
    "SessionMessage",
    "SessionContext",
    "SessionSummary",
    "SessionMemory",
]

