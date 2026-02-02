#!/usr/bin/env python3
"""
执行引擎 - 工作流引擎
Execution Engine - Workflow Engine

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
from typing import Any

from ..types import Task, TaskStatus
from .action_executor import ActionExecutor
from .task_types import TaskResult, Workflow

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流引擎

    负责管理和执行工作流。
    """

    def __init__(self, action_executor: ActionExecutor):
        """初始化工作流引擎

        Args:
            action_executor: 动作执行器实例
        """
        self.action_executor = action_executor
        self.workflows: dict[str, Workflow] = {}
        self.workflow_results: dict[str, list[TaskResult]] = {}

    async def create_workflow(self, workflow: Workflow) -> str:
        """创建工作流

        Args:
            workflow: 工作流对象

        Returns:
            工作流ID
        """
        self.workflows[workflow.id] = workflow
        logger.info(f"工作流已创建: {workflow.name}")
        return workflow.id

    async def execute_workflow(self, workflow_id: str) -> list[TaskResult]:
        """执行工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            任务结果列表
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")

        workflow = self.workflows[workflow_id]
        results: list[TaskResult] = []

        logger.info(f"🔄 开始执行工作流: {workflow.name}")

        try:
            if workflow.parallel:
                # 并行执行
                tasks = []
                for task in workflow.tasks:
                    tasks.append(self._execute_task_with_dependencies(task, workflow))

                gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理异常结果
                for result in gathered_results:
                    if isinstance(result, Exception):
                        results.append(
                            TaskResult(
                                task_id="unknown", status=TaskStatus.FAILED, error=str(result)
                            )
                        )
                    elif isinstance(result, TaskResult):
                        results.append(result)
                    else:
                        results.append(
                            TaskResult(
                                task_id="unknown", status=TaskStatus.FAILED, error="无效的结果类型"
                            )
                        )
            else:
                # 串行执行
                for task in workflow.tasks:
                    result = await self._execute_task_with_dependencies(task, workflow)
                    results.append(result)

                    # 如果任务失败且工作流不允许继续,停止执行
                    if result.status == TaskStatus.FAILED:
                        logger.warning(f"工作流因任务失败而停止: {task.name}")
                        break

        except Exception as e:
            logger.error(f"工作流执行失败: {workflow.name} - {e!s}")
            results.append(
                TaskResult(task_id="workflow_error", status=TaskStatus.FAILED, error=str(e))
            )

        self.workflow_results[workflow_id] = results
        logger.info(f"✅ 工作流执行完成: {workflow.name}")
        return results

    async def _execute_task_with_dependencies(self, task: Task, workflow: Workflow) -> TaskResult:
        """执行任务(考虑依赖关系)

        Args:
            task: 任务对象
            workflow: 工作流对象

        Returns:
            任务结果
        """
        # 检查依赖
        for _dep_id in task.dependencies:
            # 这里简化实现,实际需要更复杂的依赖检查
            pass

        return await self.action_executor.execute_action(task)

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """获取工作流状态

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流状态字典
        """
        if workflow_id not in self.workflows:
            return {"status": "not_found"}

        workflow = self.workflows[workflow_id]
        results = self.workflow_results.get(workflow_id, [])

        completed = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == TaskStatus.FAILED)

        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "total_tasks": len(workflow.tasks),
            "completed_tasks": completed,
            "failed_tasks": failed,
            "success_rate": completed / len(workflow.tasks) if workflow.tasks else 0,
        }
