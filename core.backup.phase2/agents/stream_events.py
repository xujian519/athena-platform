#!/usr/bin/env python3
"""
Agent Loop 流式事件定义

参考 OpenHarness 的流式事件模式，定义 Agent Loop 的流式事件类型。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Union


@dataclass(frozen=True)
class AssistantTextDelta:
    """增量助手文本（流式响应）"""

    text: str


@dataclass(frozen=True)
class AssistantTurnComplete:
    """完成的助手回合"""

    message: str  # 完整消息
    tool_calls: list[dict] = field(default_factory=list)  # 工具调用列表
    usage: dict[str, Any] = field(default_factory=dict)  # 使用量统计


@dataclass(frozen=True)
class ToolExecutionStarted:
    """工具执行开始事件"""

    tool_id: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str | None = None


@dataclass(frozen=True)
class ToolExecutionCompleted:
    """工具执行完成事件"""

    tool_id: str
    tool_name: str
    output: str
    is_error: bool = False
    execution_time: float = 0.0


@dataclass(frozen=True)
class ErrorEvent:
    """错误事件"""

    message: str
    recoverable: bool = True
    error_type: str | None = None


@dataclass(frozen=True)
class StatusEvent:
    """状态事件（系统消息）"""

    message: str
    level: Literal["info", "warning", "error"] = "info"


@dataclass(frozen=True)
class ThinkingDelta:
    """思考过程增量（Scratchpad）"""

    thought: str
    is_summary: bool = False  # 是否为摘要


# 流式事件联合类型（Python 3.9 兼容）
StreamEvent = Union[
    AssistantTextDelta,
    AssistantTurnComplete,
    ToolExecutionStarted,
    ToolExecutionCompleted,
    ErrorEvent,
    StatusEvent,
    ThinkingDelta,
]


async def stream_event_to_dict_async(event: StreamEvent) -> dict[str, Any]:
    """异步将流式事件转换为字典
    
    Args:
        event: 流式事件

    Returns:
        dict: 事件字典
    """
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, stream_event_to_dict, event)


def stream_event_to_dict(event: StreamEvent) -> dict[str, Any]:
    """将流式事件转换为字典

    Args:
        event: 流式事件

    Returns:
        dict: 事件字典
    """
    if isinstance(event, AssistantTextDelta):
        return {
            "type": "assistant_delta",
            "text": event.text,
        }
    elif isinstance(event, AssistantTurnComplete):
        return {
            "type": "assistant_complete",
            "message": event.message,
            "tool_calls": event.tool_calls,
            "usage": event.usage,
        }
    elif isinstance(event, ToolExecutionStarted):
        return {
            "type": "tool_started",
            "tool_id": event.tool_id,
            "tool_name": event.tool_name,
            "tool_input": event.tool_input,
            "tool_use_id": event.tool_use_id,
        }
    elif isinstance(event, ToolExecutionCompleted):
        return {
            "type": "tool_completed",
            "tool_id": event.tool_id,
            "tool_name": event.tool_name,
            "output": event.output,
            "is_error": event.is_error,
            "execution_time": event.execution_time,
        }
    elif isinstance(event, ErrorEvent):
        return {
            "type": "error",
            "message": event.message,
            "recoverable": event.recoverable,
            "error_type": event.error_type,
        }
    elif isinstance(event, StatusEvent):
        return {
            "type": "status",
            "message": event.message,
            "level": event.level,
        }
    elif isinstance(event, ThinkingDelta):
        return {
            "type": "thinking_delta",
            "thought": event.thought,
            "is_summary": event.is_summary,
        }
    else:
        return {
            "type": "unknown",
            "data": str(event),
        }


async def stream_event_to_json_async(event: StreamEvent) -> str:
    """异步将流式事件转换为 JSON
    
    Args:
        event: 流式事件

    Returns:
        str: JSON 字符串
    """
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, stream_event_to_json, event)


def stream_event_to_json(event: StreamEvent) -> str:
    """将流式事件转换为 JSON

    Args:
        event: 流式事件

    Returns:
        str: JSON 字符串
    """
    return json.dumps(stream_event_to_dict(event), ensure_ascii=False)


__all__ = [
    "AssistantTextDelta",
    "AssistantTurnComplete",
    "ToolExecutionStarted",
    "ToolExecutionCompleted",
    "ErrorEvent",
    "StatusEvent",
    "ThinkingDelta",
    "StreamEvent",
    "stream_event_to_dict",
    "stream_event_to_dict_async",
    "stream_event_to_json",
    "stream_event_to_json_async",
]
