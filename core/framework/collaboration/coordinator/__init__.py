"""
Coordinator模式 - 多Agent协调调度系统

本模块实现智能协调调度功能，支持：
- 多Agent协调调度
- 任务分配和负载均衡
- Agent间通信协调
- 冲突解决机制
- 状态同步管理

Author: P2 Development Team
Date: 2026-04-20
"""

__all__ = [
    "Coordinator",
    "TaskScheduler",
    "LoadBalancer",
    "ConflictResolver",
    "StateSynchronizer",
]

