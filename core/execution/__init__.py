#!/usr/bin/env python3
"""
执行模块 - 统一导出接口
Execution Module - Unified Export Interface

本模块作为执行模块的统一入口,导出所有公共接口。
所有类型定义统一从 shared_types.py 导入,确保类型一致性。

作者: Athena平台团队
版本: v2.0.0
更新时间: 2026-01-27
"""

import logging

# 从统一的 shared_types.py 导入所有类型定义
from .shared_types import (
    ActionType,
    DeadlockDetectedError,
    DependencyCycleError,
    ExecutionError,
    ResourceRequirement,
    ResourceType,
    ResourceUsage,
    Task,
    TaskExecutionError,
    TaskPriority,
    TaskQueue,
    TaskResult,
    TaskStatus,
    TaskTimeoutError,
    TaskType,
    TaskValidationError,
    Workflow,
)

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    执行引擎基类

    提供任务执行的基础接口,支持初始化、执行、关闭等生命周期管理。
    """

    def __init__(self, agent_id: str, config: dict | None = None):
        """
        初始化执行引擎

        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

    async def initialize(self):
        """初始化执行引擎"""
        logger.info(f"⚡ 启动执行引擎: {self.agent_id}")
        self.initialized = True

    async def execute(self, _actions):
        """
        执行动作

        Args:
            _actions: 要执行的动作列表

        Returns:
            执行结果字典
        """
        return {"results": []}

    def register_callback(self, event_type: str, callback) -> None:
        """
        注册回调函数

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        """关闭执行引擎"""
        logger.info(f"🔄 关闭执行引擎: {self.agent_id}")
        self.initialized = False

    @classmethod
    async def initialize_global(cls):
        """初始化全局实例"""
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", {})
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        """关闭全局实例"""
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance


__all__ = [
    # 类型定义
    "ActionType",
    "TaskStatus",
    "TaskPriority",
    "TaskType",
    "ResourceType",
    # 核心类
    "Task",
    "TaskQueue",
    "TaskResult",
    "ResourceRequirement",
    "ResourceUsage",
    "Workflow",
    "ExecutionEngine",
    # 异常
    "ExecutionError",
    "TaskExecutionError",
    "TaskTimeoutError",
    "DeadlockDetectedError",
    "DependencyCycleError",
    "TaskValidationError",
]
