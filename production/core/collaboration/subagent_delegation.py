#!/usr/bin/env python3
from __future__ import annotations
"""
子代理委托系统 - 隔离上下文并行执行

基于 Hermes Agent 的设计理念，实现子代理委托和结果汇总。
支持最多3个子代理并行执行，隔离上下文。

核心特性:
1. 隔离上下文并行执行
2. 结果汇总和整合
3. 最多3个子代理并行
4. 任务分解和分配

作者: Athena平台团队
创建时间: 2026-03-19
版本: v1.0.0
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

MAX_CONCURRENT_SUBAGENTS = 3


class SubagentStatus(Enum):
    """子代理状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """任务优先级"""

    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class SubagentTask:
    """子代理任务"""

    task_id: str
    name: str
    description: str
    handler: Callable[..., Any] | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout: float = 300.0  # 5分钟超时
    status: SubagentStatus = SubagentStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    execution_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "timeout": self.timeout,
            "status": self.status.value,
            "result": str(self.result)[:500] if self.result else None,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time": self.execution_time,
        }


@dataclass
class DelegationResult:
    """委托结果"""

    delegation_id: str
    parent_task: str
    subagent_tasks: list[SubagentTask]
    aggregated_result: Any = None
    success: bool = True
    total_execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "parent_task": self.parent_task,
            "subagent_tasks": [t.to_dict() for t in self.subagent_tasks],
            "success": self.success,
            "total_execution_time": self.total_execution_time,
            "created_at": self.created_at.isoformat(),
        }


class SubagentDelegationManager:
    """
    子代理委托管理器

    管理子代理的创建、执行和结果汇总。
    """

    def __init__(self, max_concurrent: int = MAX_CONCURRENT_SUBAGENTS):
        """
        初始化委托管理器

        Args:
            max_concurrent: 最大并发子代理数
        """
        self.max_concurrent = max_concurrent
        self.active_tasks: dict[str, SubagentTask] = {}
        self.delegation_history: list[DelegationResult] = []

        # 注册的任务处理器
        self.handlers: dict[str, Callable] = {}

        logger.info(f"🤖 SubagentDelegationManager 初始化完成 (最大并发: {max_concurrent})")

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        注册任务处理器

        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.handlers[task_type] = handler
        logger.info(f"✅ 已注册处理器: {task_type}")

    def create_task(
        self,
        name: str,
        description: str,
        task_type: str,
        parameters: dict[str, Any] | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout: float = 300.0,
    ) -> SubagentTask:
        """
        创建子代理任务

        Args:
            name: 任务名称
            description: 任务描述
            task_type: 任务类型
            parameters: 任务参数
            priority: 优先级
            timeout: 超时时间(秒)

        Returns:
            SubagentTask: 创建的任务
        """
        task_id = f"subtask_{uuid.uuid4().hex[:8]}"

        task = SubagentTask(
            task_id=task_id,
            name=name,
            description=description,
            parameters=parameters or {},
            priority=priority,
            timeout=timeout,
        )

        # 设置处理器
        if task_type in self.handlers:
            task.handler = self.handlers[task_type]
        else:
            logger.warning(f"⚠️ 未找到任务类型处理器: {task_type}")

        return task

    async def delegate(
        self,
        parent_task: str,
        subtasks: list[SubagentTask],
        aggregation_strategy: str = "combine",
    ) -> DelegationResult:
        """
        委托任务给子代理

        Args:
            parent_task: 父任务描述
            subtasks: 子任务列表
            aggregation_strategy: 结果聚合策略 (combine, best, vote)

        Returns:
            DelegationResult: 委托结果
        """
        # 限制并发数
        if len(subtasks) > self.max_concurrent:
            logger.warning(
                f"⚠️ 子任务数量 {len(subtasks)} 超过最大并发数 {self.max_concurrent}, "
                f"将分批执行"
            )

        delegation_id = f"delegation_{uuid.uuid4().hex[:8]}"
        logger.info(
            f"📤 开始委托: {delegation_id} "
            f"(父任务: {parent_task[:50]}..., 子任务数: {len(subtasks)})"
        )

        # 并行执行子任务
        start_time = datetime.now()

        for task in subtasks:
            task.status = SubagentStatus.RUNNING
            task.started_at = start_time
            self.active_tasks[task.task_id] = task

        # 使用信号量限制并发
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_with_semaphore(task: SubagentTask) -> SubagentTask:
            async with semaphore:
                return await self._execute_task(task)

        # 并行执行所有子任务
        results = await asyncio.gather(
            *[run_with_semaphore(task) for task in subtasks],
            return_exceptions=True,
        )

        # 更新任务状态
        for task, result in zip(subtasks, results, strict=False):
            if isinstance(result, Exception):
                task.status = SubagentStatus.FAILED
                task.error = str(result)
            else:
                task = result  # type: ignore

            task.completed_at = datetime.now()
            task.execution_time = (task.completed_at - start_time).total_seconds()

            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]

        # 聚合结果
        aggregated_result = self._aggregate_results(subtasks, aggregation_strategy)

        total_time = (datetime.now() - start_time).total_seconds()

        delegation_result = DelegationResult(
            delegation_id=delegation_id,
            parent_task=parent_task,
            subagent_tasks=subtasks,
            aggregated_result=aggregated_result,
            success=all(t.status == SubagentStatus.COMPLETED for t in subtasks),
            total_execution_time=total_time,
        )

        self.delegation_history.append(delegation_result)

        logger.info(
            f"📥 委托完成: {delegation_id} "
            f"(成功: {delegation_result.success}, 耗时: {total_time:.2f}s)"
        )

        return delegation_result

    async def _execute_task(self, task: SubagentTask) -> SubagentTask:
        """
        执行单个任务

        Args:
            task: 子代理任务

        Returns:
            SubagentTask: 执行后的任务
        """
        if task.handler is None:
            task.status = SubagentStatus.FAILED
            task.error = "未找到任务处理器"
            return task

        try:
            logger.debug(f"🔄 执行子任务: {task.name} (ID: {task.task_id})")

            # 设置超时
            result = await asyncio.wait_for(
                self._call_handler(task.handler, task.parameters),
                timeout=task.timeout,
            )

            task.result = result
            task.status = SubagentStatus.COMPLETED

            logger.debug(f"✅ 子任务完成: {task.name}")

        except asyncio.TimeoutError:
            task.status = SubagentStatus.TIMEOUT
            task.error = f"任务超时 (>{task.timeout}s)"
            logger.warning(f"⏰ 子任务超时: {task.name}")

        except Exception as e:
            task.status = SubagentStatus.FAILED
            task.error = str(e)
            logger.error(f"❌ 子任务失败: {task.name} - {e}")

        return task

    async def _call_handler(self, handler: Callable, parameters: dict[str, Any]) -> Any:
        """
        调用处理器

        Args:
            handler: 处理函数
            parameters: 参数

        Returns:
            Any: 执行结果
        """
        if asyncio.iscoroutinefunction(handler):
            return await handler(**parameters)
        else:
            return handler(**parameters)

    def _aggregate_results(
        self,
        tasks: list[SubagentTask],
        strategy: str,
    ) -> Any:
        """
        聚合子任务结果

        Args:
            tasks: 子任务列表
            strategy: 聚合策略

        Returns:
            Any: 聚合后的结果
        """
        successful_tasks = [t for t in tasks if t.status == SubagentStatus.COMPLETED]

        if not successful_tasks:
            return {"error": "所有子任务都失败了", "tasks": [t.to_dict() for t in tasks]}

        if strategy == "combine":
            # 合并所有结果
            return {
                "type": "combined",
                "results": [{"task_name": t.name, "result": t.result} for t in successful_tasks],
                "total_tasks": len(tasks),
                "successful_tasks": len(successful_tasks),
            }

        elif strategy == "best":
            # 选择最佳结果 (基于结果质量评分)
            best_task = max(
                successful_tasks,
                key=lambda t: self._score_result(t.result),
                default=successful_tasks[0] if successful_tasks else None,
            )
            return {
                "type": "best",
                "best_result": best_task.result if best_task else None,
                "task_name": best_task.name if best_task else None,
            }

        elif strategy == "vote":
            # 投票选择 (适用于分类/选择任务)
            results = [t.result for t in successful_tasks]
            return {
                "type": "voted",
                "results": results,
                "count": len(results),
            }

        else:
            # 默认返回所有结果
            return [t.result for t in successful_tasks]

    def _score_result(self, result: Any) -> float:
        """评估结果质量"""
        if result is None:
            return 0.0

        # 简单评分逻辑
        if isinstance(result, dict):
            return len(result) * 0.1
        elif isinstance(result, list):
            return len(result) * 0.1
        elif isinstance(result, str):
            return min(1.0, len(result) / 1000)

        return 0.5

    def get_active_tasks(self) -> list[dict[str, Any]]:
        """获取活动任务列表"""
        return [t.to_dict() for t in self.active_tasks.values()]

    def get_delegation_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取委托历史"""
        return [d.to_dict() for d in self.delegation_history[-limit:]]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_delegations = len(self.delegation_history)
        successful_delegations = sum(1 for d in self.delegation_history if d.success)
        total_subtasks = sum(len(d.subagent_tasks) for d in self.delegation_history)

        return {
            "total_delegations": total_delegations,
            "successful_delegations": successful_delegations,
            "success_rate": (
                successful_delegations / total_delegations if total_delegations > 0 else 0
            ),
            "total_subtasks": total_subtasks,
            "active_tasks": len(self.active_tasks),
            "max_concurrent": self.max_concurrent,
        }


# ========================================
# 全局委托管理器实例
# ========================================
_global_delegation_manager: SubagentDelegationManager | None = None


def get_delegation_manager(
    max_concurrent: int = MAX_CONCURRENT_SUBAGENTS,
) -> SubagentDelegationManager:
    """获取全局子代理委托管理器"""
    global _global_delegation_manager
    if _global_delegation_manager is None:
        _global_delegation_manager = SubagentDelegationManager(max_concurrent)
    return _global_delegation_manager


__all__ = [
    "DelegationResult",
    "SubagentDelegationManager",
    "SubagentStatus",
    "SubagentTask",
    "TaskPriority",
    "get_delegation_manager",
    "MAX_CONCURRENT_SUBAGENTS",
]
