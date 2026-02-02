#!/usr/bin/env python3
"""
通信模块 - 消息持久化
Communication Module - Message Persistence

提供消息持久化功能，支持多种后端存储：
- Redis：高性能内存数据库
- 文件系统：本地持久化
- 内存：默认实现（用于测试）

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

from .base_persistence import BaseMessagePersistence, MessageState
from .persistence_manager import PersistenceManager
from .queue_recovery import QueueRecoveryManager

__all__ = [
    "BaseMessagePersistence",
    "MessageState",
    "PersistenceManager",
    "QueueRecoveryManager",
]
