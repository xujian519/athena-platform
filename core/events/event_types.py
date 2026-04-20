#!/usr/bin/env python3
"""
事件类型定义

定义所有事件的数据结构和序列化方法。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import logging
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""

    # 代理生命周期事件
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"

    # 工具执行事件
    TOOL_EXECUTION_STARTED = "tool_execution_started"
    TOOL_EXECUTION_COMPLETED = "tool_execution_completed"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"

    # 消息传递事件
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    MESSAGE_ERROR = "message_error"

    # 系统事件
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"


@dataclass
class BaseEvent:
    """事件基类

    所有事件的基类，提供通用的事件属性和方法。
    """

    event_type: str = field(default_factory=lambda: "base_event")
    event_id: str = field(default_factory=lambda: "")
    timestamp: float = field(default_factory=time.time)
    source: str = "athena_platform"

    def __post_init__(self):
        """初始化后处理"""
        if not self.event_id:
            # 生成唯一事件 ID
            import uuid
            self.event_id = f"{self.event_type}_{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典

        Returns:
            dict: 事件数据的字典表示
        """
        from dataclasses import asdict

        data = asdict(self)
        data["event_class"] = self.__class__.__name__
        return data

    def to_json(self) -> str:
        """序列化为 JSON

        Returns:
            str: JSON 字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseEvent":
        """从字典反序列化

        Args:
            data: 事件数据字典

        Returns:
            BaseEvent: 事件对象
        """
        # 移除 event_class 字段（如果存在）
        data.pop("event_class", None)
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "BaseEvent":
        """从 JSON 反序列化

        Args:
            json_str: JSON 字符串

        Returns:
            BaseEvent: 事件对象
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


# ========================================
# 代理生命周期事件
# ========================================


@dataclass
class AgentLifecycleEvent(BaseEvent):
    """代理生命周期事件基类"""

    agent_id: str = field(default_factory=lambda: "")
    agent_type: str = field(default_factory=lambda: "")  # 例如: "xiaona", "xiaonuo", "yunxi"
    agent_name: str | None = None
    session_id: str | None = None
    event_type: str = "agent_lifecycle"  # 覆盖基类


@dataclass
class AgentStarted(AgentLifecycleEvent):
    """代理启动事件"""

    event_type: str = EventType.AGENT_STARTED.value
    startup_time: float = field(default_factory=time.time)
    capabilities: list[str] = field(default_factory=list)


@dataclass
class AgentStopped(AgentLifecycleEvent):
    """代理停止事件"""

    event_type: str = EventType.AGENT_STOPPED.value
    shutdown_time: float = field(default_factory=time.time)
    reason: str | None = None  # 停止原因


@dataclass
class AgentError(AgentLifecycleEvent):
    """代理错误事件"""

    event_type: str = EventType.AGENT_ERROR.value
    error_time: float = field(default_factory=time.time)
    error_type: str | None = None  # 错误类型
    error_message: str = ""  # 错误消息
    traceback: str | None = None  # 堆栈跟踪


# ========================================
# 工具执行事件
# ========================================


@dataclass
class ToolExecutionEvent(BaseEvent):
    """工具执行事件基类"""

    tool_id: str = field(default_factory=lambda: "")  # 工具标识
    tool_name: str = field(default_factory=lambda: "")  # 工具名称
    agent_id: str = field(default_factory=lambda: "")  # 执行工具的代理 ID
    tool_use_id: str | None = None  # 工具使用 ID


@dataclass
class ToolExecutionStarted(ToolExecutionEvent):
    """工具执行开始事件"""

    event_type: str = EventType.TOOL_EXECUTION_STARTED.value
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionCompleted(ToolExecutionEvent):
    """工具执行完成事件"""

    event_type: str = EventType.TOOL_EXECUTION_COMPLETED.value
    parameters: dict[str, Any] = field(default_factory=dict)
    result: Any = None  # 执行结果
    execution_time: float = 0.0  # 执行耗时（秒）


@dataclass
class ToolExecutionFailed(ToolExecutionEvent):
    """工具执行失败事件"""

    event_type: str = EventType.TOOL_EXECUTION_FAILED.value
    parameters: dict[str, Any] = field(default_factory=dict)
    error_type: str | None = None  # 错误类型
    error_message: str = ""  # 错误消息
    execution_time: float = 0.0  # 执行耗时（秒）


# ========================================
# 消息传递事件
# ========================================


@dataclass
class MessageEvent(BaseEvent):
    """消息传递事件基类"""

    message_id: str = field(default_factory=lambda: "")  # 消息唯一标识
    sender_id: str = field(default_factory=lambda: "")  # 发送者 ID
    receiver_id: str | None = None  # 接收者 ID（广播时为 None）
    message_type: str = "text"  # 消息类型: text, command, etc.


@dataclass
class MessageReceived(MessageEvent):
    """收到消息事件"""

    event_type: str = EventType.MESSAGE_RECEIVED.value
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageSent(MessageEvent):
    """发送消息事件"""

    event_type: str = EventType.MESSAGE_SENT.value
    content: str = ""
    delivery_status: str = "pending"  # pending, delivered, failed


@dataclass
class MessageError(MessageEvent):
    """消息错误事件"""

    event_type: str = EventType.MESSAGE_ERROR.value
    error_type: str | None = None
    error_message: str = ""


# ========================================
# 系统事件
# ========================================


@dataclass
class SystemEvent(BaseEvent):
    """系统事件基类"""

    system_id: str = "athena_platform"
    component: str = ""  # 组件名称


@dataclass
class SystemStartup(SystemEvent):
    """系统启动事件"""

    event_type: str = EventType.SYSTEM_STARTUP.value
    startup_time: float = field(default_factory=time.time)
    components: list[str] = field(default_factory=list)


@dataclass
class SystemShutdown(SystemEvent):
    """系统关闭事件"""

    event_type: str = EventType.SYSTEM_SHUTDOWN.value
    shutdown_time: float = field(default_factory=time.time)
    reason: str | None = None  # 关闭原因


@dataclass
class SystemError(SystemEvent):
    """系统错误事件"""

    event_type: str = EventType.SYSTEM_ERROR.value
    error_time: float = field(default_factory=time.time)
    component: str = ""
    error_type: str | None = None
    error_message: str = ""
    traceback: str | None = None


# ========================================
# 导出
# ========================================

__all__ = [
    "EventType",
    "BaseEvent",
    "AgentLifecycleEvent",
    "AgentStarted",
    "AgentStopped",
    "AgentError",
    "ToolExecutionEvent",
    "ToolExecutionStarted",
    "ToolExecutionCompleted",
    "ToolExecutionFailed",
    "MessageEvent",
    "MessageReceived",
    "MessageSent",
    "MessageError",
    "SystemEvent",
    "SystemStartup",
    "SystemShutdown",
    "SystemError",
]
