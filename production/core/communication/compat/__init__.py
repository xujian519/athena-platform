#!/usr/bin/env python3
"""
通信系统兼容层
Compatibility Layer for Communication System

提供向后兼容的接口,支持平滑迁移到统一架构。
"""

from __future__ import annotations
from .agent_communication import (
    AgentMessageBus,
    MessageBus,
    Priority,
    ResponseMessage,
    TaskMessage,
    TaskPriority,
    create_message_bus,
    create_response_message,
    create_task_message,
)

__all__ = [
    "AgentMessageBus",
    "MessageBus",
    "Priority",
    "ResponseMessage",
    "TaskMessage",
    "TaskPriority",
    "create_message_bus",
    "create_response_message",
    "create_task_message",
]
