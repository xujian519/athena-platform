#!/usr/bin/env python3
"""
Athena通信系统 - 消息追踪模块
Message Tracking for Communication System

实现完整的消息生命周期追踪功能。

主要功能:
1. 消息事件记录
2. 追踪管理
3. 追踪查询
4. 清理策略
5. 追踪统计

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from .types import MessageStatus

logger = logging.getLogger(__name__)


class MessageEventType(Enum):
    """消息事件类型"""

    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRIED = "retried"
    CANCELLED = "cancelled"


@dataclass
class MessageTraceEvent:
    """消息追踪事件"""

    event_type: MessageEventType
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "event": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


@dataclass
class MessageTrace:
    """
    统一的消息追踪记录
    """

    message_id: str
    created_at: datetime = field(default_factory=datetime.now)
    events: list[MessageTraceEvent] = field(default_factory=list)
    completed_at: datetime | None = None
    status: MessageStatus = MessageStatus.PENDING
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_event(
        self, event_type: MessageEventType, details: dict[str, Any] | None = None
    ) -> None:
        """添加追踪事件"""
        self.events.append(
            MessageTraceEvent(
                event_type=event_type, timestamp=datetime.now(), details=details or {}
            )
        )

    def complete(self, status: MessageStatus, error: str | None = None) -> Any:
        """完成追踪"""
        self.completed_at = datetime.now()
        self.status = status
        self.error = error

    @property
    def duration(self) -> float:
        """获取持续时间(秒)"""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return (datetime.now() - self.created_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "duration": self.duration,
            "error": self.error,
            "events": [e.to_dict() for e in self.events],
            "metadata": self.metadata,
        }


class MessageTraceManager:
    """
    消息追踪管理器
    """

    def __init__(self, max_traces: int = 10000):
        """
        初始化追踪管理器

        Args:
            max_traces: 最大追踪记录数
        """
        self.max_traces = max_traces
        self._traces: dict[str, MessageTrace] = {}
        self._counter = 0

    def create_trace(self, message_id: str, metadata: dict[str, Any] | None = None) -> MessageTrace:
        """
        创建消息追踪

        Args:
            message_id: 消息ID
            metadata: 元数据

        Returns:
            消息追踪对象
        """
        trace = MessageTrace(message_id=message_id, metadata=metadata or {})

        # 添加创建事件
        trace.add_event(MessageEventType.CREATED)

        self._traces[message_id] = trace
        self._counter += 1

        # 限制追踪记录数量
        if len(self._traces) > self.max_traces:
            self._cleanup_old_traces()

        return trace

    def get_trace(self, message_id: str) -> MessageTrace | None:
        """获取消息追踪"""
        return self._traces.get(message_id)

    def record_event(
        self, message_id: str, event_type: MessageEventType, details: dict[str, Any]) | None = None
    ):
        """
        记录消息事件

        Args:
            message_id: 消息ID
            event_type: 事件类型
            details: 事件详情
        """
        trace = self._traces.get(message_id)
        if trace:
            trace.add_event(event_type, details)
        else:
            logger.warning(f"未找到消息追踪: {message_id}")

    def complete_trace(self, message_id: str, status: MessageStatus, error: str | None = None):
        """
        完成消息追踪

        Args:
            message_id: 消息ID
            status: 最终状态
            error: 错误信息
        """
        trace = self._traces.get(message_id)
        if trace:
            trace.complete(status, error)
        else:
            logger.warning(f"未找到消息追踪: {message_id}")

    def _cleanup_old_traces(self, max_age: float = 3600) -> Any:
        """
        清理旧的追踪记录

        Args:
            max_age: 最大保留时间(秒)
        """
        now = datetime.now()
        to_remove = []

        for message_id, trace in self._traces.items():
            # 移除已完成且超时的追踪
            if trace.completed_at:
                age = (now - trace.completed_at).total_seconds()
                if age > max_age:
                    to_remove.append(message_id)
            # 移除创建时间过长的未完成追踪
            else:
                age = (now - trace.created_at).total_seconds()
                if age > max_age * 2:  # 未完成的保留时间加倍
                    to_remove.append(message_id)

        for message_id in to_remove:
            del self._traces[message_id]

        if to_remove:
            logger.debug(f"清理了 {len(to_remove)} 条消息追踪记录")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = len(self._traces)
        completed = sum(1 for t in self._traces.values() if t.completed_at is not None)
        failed = sum(1 for t in self._traces.values() if t.status == MessageStatus.FAILED)

        return {
            "total_traces": total,
            "active_traces": total - completed,
            "completed_traces": completed,
            "failed_traces": failed,
            "success_rate": (completed - failed) / total if total > 0 else 1.0,
        }


# =============================================================================
# 便捷函数
# =============================================================================


def create_trace_manager(max_traces: int = 10000) -> MessageTraceManager:
    """创建消息追踪管理器"""
    return MessageTraceManager(max_traces)


_default_manager: MessageTraceManager | None = None


def get_default_manager() -> MessageTraceManager:
    """获取默认追踪管理器"""
    global _default_manager
    if _default_manager is None:
        _default_manager = MessageTraceManager()
    return _default_manager


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "MessageEventType",
    "MessageTrace",
    "MessageTraceEvent",
    "MessageTraceManager",
    "create_trace_manager",
    "get_default_manager",
]
