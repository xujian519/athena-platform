#!/usr/bin/env python3
# 启用延迟类型注解评估，支持|联合类型语法
from __future__ import annotations

"""
执行引擎 - 任务类型定义
Execution Engine - Task Type Definitions

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..types import ActionType, Task, TaskStatus


@dataclass
class EngineTask(Task):
    """执行引擎专用任务类,扩展自统一的 Task 类

    添加执行引擎特有的属性。
    """

    # 执行引擎特有属性(使用不同的字段名避免类型冲突)
    _action_type_enum: ActionType | None = field(default=None, init=False, compare=False)
    action_data: dict[str, Any] = field(default_factory=dict)
    scheduled_at: datetime | None = None

    def __post_init__(self):
        """初始化后处理"""
        # 调用父类的 __post_init__
        if hasattr(super(), "__post_init__"):
            super().__post_init__()

        # 将 action_type 字符串转换为 ActionType 枚举存储
        if self.action_type and isinstance(self.action_type, str):
            try:
                self._action_type_enum = ActionType(self.action_type)
            except (ValueError, KeyError):
                # 如果无法转换,使用默认值
                self._action_type_enum = ActionType.CUSTOM

    @property
    def action_type_enum(self) -> ActionType:
        """获取 ActionType 枚举值"""
        if self._action_type_enum is None:
            self._action_type_enum = ActionType.CUSTOM
        return self._action_type_enum

    # 兼容性属性:id 映射到 task_id
    @property
    def id(self) -> str:
        """id 属性别名,用于向后兼容"""
        return self.task_id

    @id.setter
    def id(self, value: str):
        """id 设置器,用于向后兼容"""
        self.task_id = value


@dataclass
class TaskResult:
    """任务结果

    表示单个任务的执行结果。
    """

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration: Optional[float] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)


@dataclass
class Workflow:
    """工作流

    表示一组要执行的任务序列。
    """

    id: str
    name: str
    tasks: list[Task] = field(default_factory=list)
    parallel: bool = False
    max_concurrent: int = 5
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
