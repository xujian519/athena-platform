#!/usr/bin/env python3
"""
优化版通信模块 - 类型定义
Optimized Communication Module - Type Definitions

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CompressionType(Enum):
    """压缩算法类型"""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    LZMA = "lzma"
    ZSTD = "zstd"
    AUTO = "auto"


class MessagePriority(Enum):
    """消息优先级"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BULK = 5


class DeliveryMode(Enum):
    """投递模式"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    BATCH = "batch"


@dataclass
class Message:
    """消息定义"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    payload: Any
    priority: MessagePriority = MessagePriority.NORMAL
    compression: CompressionType = CompressionType.AUTO
    delivery_mode: DeliveryMode = DeliveryMode.ASYNCHRONOUS
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: float | None = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    correlation_id: str | None = None


@dataclass
class BatchMessage:
    """批量消息"""
    batch_id: str
    messages: list[Message]
    batch_size: int
    compression_type: CompressionType
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompressionResult:
    """压缩结果"""
    original_size: int
    compressed_size: int
    compression_ratio: float
    compression_time: float
    algorithm: str


@dataclass
class CommunicationStats:
    """通信统计信息"""
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    compression_stats: dict[str, CompressionResult] = field(default_factory=dict)
    batch_stats: dict[str, Any] = field(default_factory=dict)
    delivery_stats: dict[str, int] = field(default_factory=dict)
    average_message_size: float = 0.0
    average_compression_ratio: float = 0.0
    message_rate: float = 0.0
    bandwidth_saved: float = 0.0


__all__ = [
    "CompressionType",
    "MessagePriority",
    "DeliveryMode",
    "Message",
    "BatchMessage",
    "CompressionResult",
    "CommunicationStats",
]
