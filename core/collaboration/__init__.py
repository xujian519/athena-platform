#!/usr/bin/env python3
from __future__ import annotations
"""
多智能体协作框架模块
Multi-Agent Collaboration Framework Module

提供完整的多智能体协作功能,包括:
- 智能体注册和管理
- 任务分配和协调
- 多种协作模式
- 冲突检测和解决
- 资源管理和调度
"""

from .collaboration_manager import (
    CollaborationOrchestrator,
    # 协作管理相关类
    CollaborationTemplate,
    Conflict,
    WorkflowStep,
)
from .collaboration_patterns import (
    # 协作模式相关类
    CollaborationPattern,
    CollaborationPatternFactory,
    ConsensusCollaborationPattern,
    HierarchicalCollaborationPattern,
    ParallelCollaborationPattern,
    SequentialCollaborationPattern,
)
from .multi_agent_collaboration import (
    Agent,
    # 核心数据类
    AgentCapability,
    # 核心枚举类
    AgentStatus,
    CollaborationSession,
    CollaborationStrategy,
    ConflictResolutionStrategy,
    Message,
    # 核心功能类
    MessageBroker,
    MessageType,
    MultiAgentCollaborationFramework,
    Priority,
    ResourceManager,
    Task,
    TaskStatus,
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Athena AI Team"

# 导出的主要接口
__all__ = [
    "Agent",
    # 数据类
    "AgentCapability",
    # 枚举类
    "AgentStatus",
    "CollaborationOrchestrator",
    "CollaborationPattern",
    "CollaborationPatternFactory",
    "CollaborationSession",
    "CollaborationStrategy",
    "CollaborationTemplate",
    "Conflict",
    "ConflictResolutionStrategy",
    "ConsensusCollaborationPattern",
    "HierarchicalCollaborationPattern",
    "Message",
    # 核心类
    "MessageBroker",
    "MessageType",
    "MultiAgentCollaborationFramework",
    "ParallelCollaborationPattern",
    "Priority",
    "ResourceManager",
    "SequentialCollaborationPattern",
    "Task",
    "TaskStatus",
    "WorkflowStep",
]


# 便捷函数
def create_collaboration_framework() -> MultiAgentCollaborationFramework:
    """创建协作框架实例"""
    return MultiAgentCollaborationFramework()


def create_agent(agent_id: str, name: str, capabilities: list[AgentCapability], **kwargs) -> Agent:
    """创建智能体实例"""
    return Agent(id=agent_id, name=name, capabilities=capabilities, **kwargs)


def create_task(
    title: str, description: str = "", required_capabilities: list[str] | None = None, **kwargs
) -> Task:
    """创建任务实例"""
    return Task(
        title=title,
        description=description,
        required_capabilities=required_capabilities or [],
        **kwargs,
    )


def create_collaboration_pattern(
    pattern_type: str, framework: MultiAgentCollaborationFramework
) -> CollaborationPattern | None:
    """创建协作模式实例"""
    return CollaborationPatternFactory.create_pattern(pattern_type, framework)


def get_available_patterns() -> list[str]:
    """获取可用的协作模式列表"""
    return CollaborationPatternFactory.get_available_patterns()


# 模块级别的配置
DEFAULT_MAX_AGENTS = 50
DEFAULT_MAX_TASKS = 100
DEFAULT_MESSAGE_QUEUE_SIZE = 1000
DEFAULT_CONFLICT_RESOLUTION_STRATEGY = ConflictResolutionStrategy.PRIORITY_BASED
