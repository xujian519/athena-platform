
"""
Task Tool系统数据模型

定义所有核心数据模型，包括任务状态、模型选择、任务输入/输出等。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 任务待执行
    RUNNING = "running"  # 任务执行中
    COMPLETED = "completed"  # 任务完成
    FAILED = "failed"  # 任务失败
    CANCELLED = "cancelled"  # 任务已取消


class ModelChoice(Enum):
    """模型选择枚举"""

    HAIKU = "haiku"  # Claude Haiku (快速模型)
    SONNET = "sonnet"  # Claude Sonnet (任务模型)
    OPUS = "opus"  # Claude Opus (主模型)


@dataclass
class TaskInput:
    """任务输入数据类

    Attributes:
        prompt: 任务提示词
        tools: 可用工具列表
        context: 额外的上下文信息
        agent_type: 代理类型（用于模型选择）
        fork_context: Fork上下文信息
    """

    prompt: str
    tools: Optional[list[str]] = field(default_factory=list)
    context: Optional[dict[str, Any]] = field(default_factory=dict)
    agent_type: Optional[str] = None
    fork_context: Optional[ForkContext ] = None  # noqa: F821 - Forward reference, resolved at runtime


@dataclass
class ForkContext:
    """Fork上下文信息"""

    session_id: str = ""
    parent_task_id: str = ""
    fork_point: str = ""
    metadata: Optional[dict[str, Any]] = field(default_factory=dict)


@dataclass
class TaskOutput:
    """任务输出数据类

    Attributes:
        content: 输出内容
        tool_uses: 工具使用次数
        duration: 执行时长（秒）
        success: 是否成功
        error: 错误信息（如果失败）
        metadata: 元数据
    """

    content: str
    tool_uses: int = 0
    duration: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = field(default_factory=dict)


@dataclass
class TaskRecord:
    """任务记录数据类

    用于持久化存储任务信息

    Attributes:
        task_id: 任务ID
        agent_id: 代理ID
        model: 使用的模型
        status: 任务状态
        input: 任务输入
        output: 任务输出
        created_at: 创建时间（ISO 8601格式）
        updated_at: 更新时间（ISO 8601格式）
        error_message: 错误信息
    """

    task_id: str
    agent_id: str
    model: str
    status: TaskStatus
    input: TaskInput
    output: Optional[TaskOutput ] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "model": self.model,
            "status": self.status.value,
            "input": {
                "prompt": self.input.prompt,
                "tools": self.input.tools,
                "context": self.input.context,
            },
            "output": {
                "content": self.output.content,
                "tool_uses": self.output.tool_uses,
                "duration": self.output.duration,
                "success": self.output.success,
                "error": self.output.error,
            }
            if self.output
            else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message,
        }


@dataclass
class BackgroundTask:
    """后台任务数据类

    用于管理异步执行的后台任务

    Attributes:
        task_id: 任务ID
        status: 任务状态
        future: 异步Future对象
        agent_id: 代理ID
        created_at: 创建时间（ISO 8601格式）
        updated_at: 更新时间（ISO 8601格式）
        input_data: 任务输入
    """

    task_id: str
    status: TaskStatus
    future: Any  # concurrent.futures.Future
    agent_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    input_data: Optional[TaskInput ] = None

    def update_status(self, new_status: TaskStatus) -> str:
        """更新任务状态"""
        self.status = new_status
        self.updated_at = datetime.utcnow().isoformat() + "Z"

