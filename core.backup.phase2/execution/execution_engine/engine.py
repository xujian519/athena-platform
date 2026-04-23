#!/usr/bin/env python3
from __future__ import annotations
"""
执行引擎 - 主引擎类
Execution Engine - Main Engine

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from contextlib import suppress
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from ..types import ActionType, Task, TaskPriority, TaskStatus
from .action_executor import ActionExecutor
from .scheduler import TaskScheduler
from .task_types import EngineTask, TaskResult, Workflow
from .workflow import WorkflowEngine

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """执行引擎 - 完整实现

    提供任务执行、工作流管理、并发控制和结果处理功能。
    """

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        """初始化执行引擎

        Args:
            agent_id: 智能体ID
            config: 配置字典
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

        # 核心组件
        self.action_executor = ActionExecutor()
        self.task_scheduler = TaskScheduler(max_concurrent=self.config.get("max_concurrent", 10))
        self.workflow_engine = WorkflowEngine(self.action_executor)

        # 存储和状态
        self.tasks: dict[str, Task] = {}
        self.task_results: dict[str, TaskResult] = {}
        self.active_workflows: dict[str, asyncio.Task] = {}

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_workflows": 0,
            "active_workflows": 0,
            "avg_execution_time": 0.0,
        }

        # 事件回调
        self._callbacks = defaultdict(list)

        logger.info(f"⚡ 创建执行引擎: {self.agent_id}")

    async def initialize(self):
        """初始化执行引擎"""
        logger.info(f"🚀 启动执行引擎: {self.agent_id}")

        try:
            # 启动任务处理循环
            asyncio.create_task(self._task_processing_loop())

            self.initialized = True

            # 触发初始化事件
            await self._trigger_callbacks(
                "initialized", {"agent_id": self.agent_id, "timestamp": datetime.now()}
            )

            logger.info(f"✅ 执行引擎初始化完成: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ 执行引擎初始化失败 {self.agent_id}: {e}")
            raise

    async def execute_task(self, task: Task) -> str:
        """执行单个任务

        Args:
            task: 任务对象

        Returns:
            任务ID
        """
        if not self.initialized:
            raise RuntimeError("执行引擎未初始化")

        # 保存任务
        self.tasks[task.id] = task
        self.stats["total_tasks"] += 1

        # 调度任务
        await self.task_scheduler.schedule_task(task)

        logger.info(f"📋 任务已调度: {task.name}")
        return task.id

    async def execute_actions(self, actions: list[dict[str, Any]]) -> list[str]:
        """执行多个动作

        Args:
            actions: 动作字典列表

        Returns:
            任务ID列表
        """
        task_ids = []

        for action in actions:
            # 创建任务
            action_type_value = action.get("type", "custom")
            # 确保 action_type 是字符串
            if isinstance(action_type_value, ActionType):
                action_type_str = action_type_value.value
            else:
                action_type_str = str(action_type_value)

            task = EngineTask(
                task_id=str(uuid.uuid4()),
                name=action.get("name", f"Task_{len(task_ids)}"),
                action_type=action_type_str,
                action_data=action,
                priority=TaskPriority(action.get("priority", TaskPriority.NORMAL.value)),
            )

            # 执行任务
            task_id = await self.execute_task(task)
            task_ids.append(task_id)

        return task_ids

    async def create_workflow(
        self,
        name: str,
        tasks_data: list[dict[str, Any]],        parallel: bool = False,
        max_concurrent: int = 5,
    ) -> str:
        """创建工作流

        Args:
            name: 工作流名称
            tasks_data: 任务数据列表
            parallel: 是否并行执行
            max_concurrent: 最大并发数

        Returns:
            工作流ID
        """
        workflow_id = str(uuid.uuid4())

        # 创建任务列表
        tasks = []
        for task_data in tasks_data:
            # 获取 action_type 并转换为字符串
            action_type_value = task_data.get("type", "custom")
            if isinstance(action_type_value, ActionType):
                action_type_str = action_type_value.value
            else:
                action_type_str = str(action_type_value)

            task = EngineTask(
                task_id=str(uuid.uuid4()),
                name=task_data.get("name", f"Task_{len(tasks)}"),
                action_type=action_type_str,
                action_data=task_data.get("data", {}),
                priority=TaskPriority(task_data.get("priority", TaskPriority.NORMAL.value)),
                dependencies=task_data.get("dependencies", []),
            )
            tasks.append(task)

        # 创建工作流
        workflow_timeout = tasks_data[-1].get("timeout") if tasks_data else None
        workflow = Workflow(
            id=workflow_id,
            name=name,
            tasks=tasks,
            parallel=parallel,
            max_concurrent=max_concurrent,
            timeout=workflow_timeout,
        )

        # 注册工作流
        await self.workflow_engine.create_workflow(workflow)
        self.stats["total_workflows"] += 1

        logger.info(f"🔗 工作流已创建: {name}")
        return workflow_id

    async def execute_workflow(self, workflow_id: str) -> list[TaskResult]:
        """执行工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            任务结果列表
        """
        if not self.initialized:
            raise RuntimeError("执行引擎未初始化")

        # 创建执行任务
        execution_task = asyncio.create_task(self.workflow_engine.execute_workflow(workflow_id))
        self.active_workflows[workflow_id] = execution_task
        self.stats["active_workflows"] += 1

        try:
            # 执行工作流
            results = await execution_task

            # 更新统计
            completed = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
            failed = sum(1 for r in results if r.status == TaskStatus.FAILED)

            self.stats["completed_tasks"] += completed
            self.stats["failed_tasks"] += failed

            # 计算平均执行时间
            if results:
                avg_time = sum(r.duration or 0 for r in results) / len(results)
                total_tasks = self.stats["completed_tasks"] + self.stats["failed_tasks"]
                if total_tasks > 0:
                    self.stats["avg_execution_time"] = (
                        self.stats["avg_execution_time"] * (total_tasks - len(results)) + avg_time
                    ) / total_tasks

            logger.info(f"✅ 工作流执行完成: {workflow_id} ({completed}/{len(results)} 成功)")
            return results

        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {workflow_id} - {e!s}")
            raise

        finally:
            # 清理
            self.active_workflows.pop(workflow_id, None)
            self.stats["active_workflows"] = max(0, self.stats["active_workflows"] - 1)

    async def get_task_result(self, task_id: str) -> TaskResult | None:
        """获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            任务结果对象
        """
        return self.task_results.get(task_id)

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态
        """
        result = self.task_results.get(task_id)
        return result.status if result else None

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        if task_id in self.task_results:
            self.task_results[task_id].status = TaskStatus.CANCELLED
            logger.info(f"🚫 任务已取消: {task_id}")
            return True
        return False

    async def get_statistics(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        scheduler_status = self.task_scheduler.get_status()

        return {
            "agent_id": self.agent_id,
            "statistics": self.stats.copy(),
            "scheduler": scheduler_status,
            "active_workflows": list(self.active_workflows.keys()),
            "total_task_results": len(self.task_results),
            "success_rate": (
                self.stats["completed_tasks"] / self.stats["total_tasks"]
                if self.stats["total_tasks"] > 0
                else 0
            ),
        }

    async def _task_processing_loop(self):
        """任务处理循环"""
        while self.initialized:
            try:
                # 获取下一个任务
                task = await self.task_scheduler.get_next_task()
                if not task:
                    await asyncio.sleep(0.1)
                    continue

                # 检查是否超时
                scheduled_at = getattr(task, "scheduled_at", None)
                if scheduled_at and scheduled_at > datetime.now():
                    # 还未到执行时间,重新放回队列
                    await self.task_scheduler.schedule_task(task)
                    await asyncio.sleep(0.1)
                    continue

                # 执行任务
                async with self.task_scheduler.acquire_slot(task.id):
                    result = await self.action_executor.execute_action(task)
                    self.task_results[task.id] = result

                    # 触发任务完成事件
                    await self._trigger_callbacks(
                        "task_completed",
                        {
                            "task_id": task.id,
                            "status": result.status.value,
                            "duration": result.duration,
                        },
                    )

            except Exception as e:
                logger.error(f"任务处理错误: {e}")
                await asyncio.sleep(1)

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self._callbacks[event_type].append(callback)

    async def _trigger_callbacks(self, event_type: str, data: dict[str, Any]):
        """触发回调

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        for callback in self._callbacks[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")

    async def shutdown(self):
        """关闭执行引擎"""
        logger.info(f"🔄 关闭执行引擎: {self.agent_id}")

        try:
            # 取消所有活跃工作流
            for _workflow_id, task in list(self.active_workflows.items()):
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

            # 保存状态
            await self._save_state()

            self.initialized = False

            # 触发关闭事件
            await self._trigger_callbacks(
                "shutdown", {"agent_id": self.agent_id, "timestamp": datetime.now()}
            )

            logger.info(f"✅ 执行引擎已关闭: {self.agent_id}")

        except Exception as e:
            logger.error(f"关闭执行引擎失败: {e}")
            raise

        finally:
            # 确保线程池被关闭
            if hasattr(self, "action_executor"):
                try:
                    self.action_executor.thread_pool.shutdown(wait=True)
                    logger.debug(f"线程池已关闭: {self.agent_id}")
                except Exception as e:
                    logger.error(f"关闭线程池失败: {e}")

    async def _save_state(self):
        """保存状态"""
        try:
            data_dir = Path("data/execution")
            data_dir.mkdir(parents=True, exist_ok=True)

            # 保存任务结果
            if self.task_results:
                results_file = data_dir / f"{self.agent_id}_task_results.json"
                with open(results_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {tid: asdict(result) for tid, result in self.task_results.items()},
                        f,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )

            logger.info(f"执行状态已保存: {len(self.task_results)}个任务结果")

        except Exception as e:
            logger.error(f"保存状态失败: {e}")

    @classmethod
    async def initialize_global(cls, config: dict[str, Any] | None = None):
        """初始化全局实例"""
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", config)
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        """关闭全局实例"""
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance
