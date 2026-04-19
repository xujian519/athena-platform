#!/usr/bin/env python3
from __future__ import annotations
"""
Agent协调器 - 向后兼容重定向
Agent Coordinator - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.agent_collaboration.agent_coordinator (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.agent_collaboration.agent_coordinator import AgentCoordinator

新导入方式:
    from core.agent_collaboration.agent_coordinator import (
        AgentCoordinator,
        TaskStatus,
        WorkflowType,
        TaskDefinition,
    )
    # 或者使用 get_agent_coordinator() 单例
    from core.agent_collaboration.agent_coordinator import get_agent_coordinator

    coordinator = get_agent_coordinator()
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

import warnings

# 导入重构后的模块
from .agent_coordinator import (
    AgentCoordinator,
    TaskDefinition,
    TaskExecution,
    TaskStatus,
    WorkflowType,
    get_agent_coordinator,
)

# 发出弃用警告
warnings.warn(
    "agent_coordinator.py 已重构为模块化目录 core.agent_collaboration.agent_coordinator/。"
    "请更新您的导入语句。详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
__all__ = [
    "AgentCoordinator",
    "get_agent_coordinator",
    "TaskStatus",
    "WorkflowType",
    "TaskDefinition",
    "TaskExecution",
]
