#!/usr/bin/env python3
"""
Agent协调器 - 数据类型定义
Agent Coordinator - Type Definitions

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.0.0
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(Enum):
    """工作流类型"""

    SEQUENTIAL = "sequential"  # 串行执行
    PARALLEL = "parallel"  # 并行执行
    PIPELINE = "pipeline"  # 流水线执行
    COLLABORATIVE = "collaborative"  # 协作执行


@dataclass
class TaskDefinition:
    """任务定义"""

    task_id: str
    workflow_type: WorkflowType
    task_type: str
    content: dict[str, Any]
    required_agents: list[str]
    dependencies: list[str] | None = None
    priority: int = 2
    deadline: str | None = None
    created_at: str | None = None


@dataclass
class TaskExecution:
    """任务执行状态"""

    task_definition: TaskDefinition
    status: TaskStatus = TaskStatus.PENDING
    assigned_agents: list[str] | None = None
    results: dict[str, Any] | None = None
    start_time: str | None = None
    end_time: str | None = None
    error_message: str | None = None
