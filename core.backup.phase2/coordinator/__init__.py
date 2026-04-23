#!/usr/bin/env python3
"""Coordinator模式 - 多Agent协调调度系统

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

Coordinator模式提供多Agent系统的协调和管理功能。

主要功能:
- Agent注册和注销
- 任务分配和负载均衡
- 优先级调度
- Agent间通信协调
- 冲突解决机制
- 状态同步管理

使用示例:
    ```python
    from core.coordinator import Coordinator, CoordinatorConfig, AgentInfo

    # 创建Coordinator
    config = CoordinatorConfig(
        max_concurrent_tasks=10,
        enable_load_balancing=True,
    )
    coordinator = Coordinator(config)

    # 注册Agent
    agent = AgentInfo(
        agent_id="agent-001",
        name="测试Agent",
        capabilities=["task_a", "task_b"],
    )
    coordinator.register_agent(agent)

    # 提交任务
    assignment = coordinator.submit_task(
        task_id="task-001",
        task_type="task_a",
        payload={"data": "test"},
        priority=1,
    )
    ```
"""

from __future__ import annotations

from .advanced import (
    AdvancedCoordinator,
    TaskDependency,
    TaskRetryConfig,
)
from .base import (
    AgentInfo,
    AgentStatus,
    ConflictInfo,
    ConflictResolutionStrategy,
    ConflictType,
    Coordinator,
    CoordinatorConfig,
    Message,
    MessagePriority,
    TaskAssignment,
    get_coordinator,
)
from .scheduler import (
    LeastLoadedStrategy,
    PriorityStrategy,
    RoundRobinStrategy,
    SchedulingStrategy,
    StrategyFactory,
    WeightedStrategy,
)

__all__ = [
    # 基础类
    "AgentInfo",
    "AgentStatus",
    "ConflictInfo",
    "ConflictResolutionStrategy",
    "ConflictType",
    "Coordinator",
    "CoordinatorConfig",
    "Message",
    "MessagePriority",
    "TaskAssignment",
    "get_coordinator",
    # 调度策略
    "SchedulingStrategy",
    "RoundRobinStrategy",
    "LeastLoadedStrategy",
    "PriorityStrategy",
    "WeightedStrategy",
    "StrategyFactory",
    # 高级功能
    "AdvancedCoordinator",
    "TaskDependency",
    "TaskRetryConfig",
]

__version__ = "1.0.0"
__author__ = "Athena平台团队"
