#!/usr/bin/env python3
from __future__ import annotations
"""
Agent协调器 - 公共接口
Agent Coordinator - Public Interface

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.0.0

此模块提供Agent协调器的公共接口导出。
重构后的模块位于 agent_coordinator/ 目录下。
"""

# 导入核心类
from .core import AgentCoordinator, get_agent_coordinator
from .types import TaskDefinition, TaskExecution, TaskStatus, WorkflowType

# 导出公共接口
__all__ = [
    # 核心类
    "AgentCoordinator",
    "get_agent_coordinator",
    # 数据类型
    "TaskStatus",
    "WorkflowType",
    "TaskDefinition",
    "TaskExecution",
]
