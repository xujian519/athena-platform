"""
统一Agent数据类型定义

整合两套架构的数据模型，提供统一的类型系统。
兼容传统架构的简单类型和新一代架构的完整类型。

Author: Athena Team
Version: 1.0.0
Date: 2026-04-24
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ============ 状态枚举 ============


class AgentStatus(Enum):
    """智能体状态枚举"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class MessageType(Enum):
    """消息类型枚举"""
    TASK = "task"
    QUERY = "query"
    NOTIFY = "notify"
    RESPONSE = "response"


# ============ 数据模型 ============


@dataclass
class AgentCapability:
    """智能体能力描述"""
    name: str
    description: str
    parameters: Optional[dict[str, Any]] = field(default_factory=dict)
    examples: Optional[list[dict[str, Any]]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "examples": self.examples
        }


@dataclass
class AgentMetadata:
    """智能体元数据"""
    name: str
    version: str
    description: str
    author: str
    created_at: datetime = field(default_factory=datetime.now)
    tags: Optional[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }


# ============ 新一代架构请求/响应模型 ============


@dataclass
class AgentRequest:
    """新一代架构请求模型"""
    request_id: str
    action: str
    parameters: Optional[dict[str, Any]] = field(default_factory=dict)
    context: Optional[dict[str, Any]] = field(default_factory=dict)
    metadata: Optional[dict[str, Any]] = field(default_factory=dict)
    trace_headers: Optional[dict[str, str]] = field(default_factory=dict)  # 跨服务追踪
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "action": self.action,
            "parameters": self.parameters,
            "context": self.context,
            "metadata": self.metadata,
            "trace_headers": self.trace_headers,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentResponse:
    """新一代架构响应模型"""
    request_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms
        }

    @classmethod
    def error_response(cls, request_id: str, error: str, **kwargs) -> "AgentResponse":
        """创建错误响应"""
        return cls(request_id=request_id, success=False, error=error, **kwargs)

    @classmethod
    def success_response(cls, request_id: str, data: Any = None, **kwargs) -> "AgentResponse":
        """创建成功响应"""
        return cls(request_id=request_id, success=True, data=data, **kwargs)


# ============ 传统架构消息模型 ============


@dataclass
class TaskMessage:
    """传统架构任务消息"""
    sender_id: str
    recipient_id: str
    task_type: str
    content: dict[str, Any]
    task_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "task_type": self.task_type,
            "content": self.content,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ResponseMessage:
    """传统架构响应消息"""
    task_id: str
    content: Any
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "content": self.content,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


# ============ 健康状态模型 ============


@dataclass
class HealthStatus:
    """健康状态"""
    status: AgentStatus
    message: str = ""
    details: Optional[dict[str, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def is_healthy(self) -> bool:
        """是否健康"""
        return self.status in [AgentStatus.READY, AgentStatus.BUSY]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "healthy": self.is_healthy()
        }


# ============ 消息转换工具 ============


class MessageConverter:
    """消息格式转换器 - 支持两种消息格式互转"""

    @staticmethod
    def task_to_request(task: TaskMessage) -> AgentRequest:
        """传统任务消息转新请求格式"""
        return AgentRequest(
            request_id=task.task_id,
            action=task.task_type,
            parameters=task.content,
            context={
                "sender_id": task.sender_id,
                "recipient_id": task.recipient_id
            },
            metadata=task.metadata,
            timestamp=task.timestamp
        )

    @staticmethod
    def request_to_task(request: AgentRequest, recipient_id: str = "") -> TaskMessage:
        """新请求格式转传统任务消息"""
        context = request.context or {}
        return TaskMessage(
            sender_id=context.get("sender_id", "system"),
            recipient_id=recipient_id or context.get("recipient_id", ""),
            task_type=request.action,
            content=request.parameters or {},
            task_id=request.request_id,
            timestamp=request.timestamp,
            metadata=request.metadata or {}
        )

    @staticmethod
    def response_to_task_response(response: AgentResponse) -> ResponseMessage:
        """新响应格式转传统响应消息"""
        return ResponseMessage(
            task_id=response.request_id,
            content=response.data,
            success=response.success,
            error=response.error,
            timestamp=response.timestamp,
            metadata=response.metadata
        )

    @staticmethod
    def task_response_to_response(task_response: ResponseMessage) -> AgentResponse:
        """传统响应消息转新响应格式"""
        return AgentResponse(
            request_id=task_response.task_id,
            success=task_response.success,
            data=task_response.content,
            error=task_response.error,
            timestamp=task_response.timestamp,
            metadata=task_response.metadata
        )


# ============ 简单响应类（向后兼容） ============


class SimpleAgentResponse:
    """简单响应类 - 向后兼容传统架构"""

    def __init__(self, content: str, success: Optional[bool] = None, metadata: Optional[dict[str, Any]] = None):
        self.content = content
        self.success = success
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {"content": self.content, "success": self.success, "metadata": self.metadata}

    @classmethod
    def error(cls, error_message: str) -> "SimpleAgentResponse":
        """创建错误响应"""
        return cls(content=error_message, success=False, metadata={"error": True})

    @classmethod
    def success_response(cls, content: str, **metadata) -> "SimpleAgentResponse":
        """创建成功响应"""
        return cls(content=content, success=True, metadata=metadata)


# ============ 导出 ============

__all__ = [
    # 状态枚举
    "AgentStatus",
    "MessageType",
    # 数据模型
    "AgentCapability",
    "AgentMetadata",
    # 新一代架构模型
    "AgentRequest",
    "AgentResponse",
    # 传统架构模型
    "TaskMessage",
    "ResponseMessage",
    # 健康状态
    "HealthStatus",
    # 转换工具
    "MessageConverter",
    # 简单响应
    "SimpleAgentResponse",
]
