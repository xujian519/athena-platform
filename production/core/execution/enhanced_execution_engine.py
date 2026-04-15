#!/usr/bin/env python3
"""
增强执行引擎
Enhanced Execution Engine

基于BaseModule的标准化执行引擎,支持统一接口和任务模型
使用统一的类型定义(从 shared_types.py 导入)。

作者: Athena AI系统
创建时间: 2025-12-11
版本: 2.0.0
更新时间: 2026-01-27
"""

from __future__ import annotations
import asyncio
import inspect
import logging
import multiprocessing
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from ..base_module import BaseModule

# 从统一的 shared_types.py 导入类型定义
from .shared_types import (
    ActionType,
    Task,
    TaskPriority,
    TaskQueue,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)


# 最大队列大小常量
MAX_QUEUE_SIZE = 5000


class EnhancedExecutionEngine(BaseModule):
    """
    增强执行引擎

    继承BaseModule,提供标准化的接口和任务管理
    """

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        """
        初始化增强执行引擎

        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        # 提取执行引擎专用配置
        execution_config = config or {}
        max_workers = execution_config.get("max_workers", multiprocessing.cpu_count())
        max_concurrent = execution_config.get("max_concurrent", 10)
        task_timeout = execution_config.get("task_timeout", 300.0)

        # 初始化基类
        super().__init__(agent_id, config)

        # 执行引擎配置
        self.max_workers = max_workers
        self.max_concurrent = max_concurrent
        self.task_timeout = task_timeout

        # 任务队列和存储
        self._task_queue = TaskQueue(max_size=10000)
        self._running_tasks: dict[str, Task] = {}
        self._completed_tasks: dict[str, Task] = {}

        # 执行器注册表
        self._executors: dict[str, Callable] = {}
        self._executor_registry: dict[str, Callable] = {}

        # 工作流管理
        self._workflows: dict[str, Any] = {}

        # 统计信息
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
            "queue_size": 0,
        }

        # 信号控制
        self._shutdown_event = asyncio.Event()
        self._worker_tasks: list[asyncio.Task] = []

        # 线程池（延迟初始化）
        self._thread_pool: ThreadPoolExecutor | None = None

        # 注册默认执行器
        self._register_default_executors()

    def _get_thread_pool(self) -> ThreadPoolExecutor:
        """获取或创建线程池"""
        if self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._thread_pool

    def _register_default_executors(self) -> None:
        """注册默认执行器"""
        # 函数调用执行器
        self._executors["function_call"] = self._execute_function_call

        # API调用执行器
        self._executors["api_call"] = self._execute_api_call

        # 工作流执行器
        self._executors["workflow"] = self._execute_workflow

        # 命令执行器
        self._executors["command"] = self._execute_command

    async def _on_initialize(self) -> bool:
        """初始化逻辑"""
        try:
            # 启动工作线程
            for i in range(self.max_concurrent):
                worker_task = asyncio.create_task(self._worker(f"worker_{i}"))
                self._worker_tasks.append(worker_task)

            self.logger.info(f"✅ 增强执行引擎初始化成功,工作线程数: {len(self._worker_tasks)}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 增强执行引擎初始化失败: {e}")
            return False

    async def _on_start(self) -> bool:
        """启动逻辑"""
        try:
            self.logger.info("🚀 启动增强执行引擎")

            # 启动任务调度器
            asyncio.create_task(self._task_scheduler())

            return True

        except Exception as e:
            self.logger.error(f"❌ 增强执行引擎启动失败: {e}")
            return False

    async def _on_stop(self) -> bool:
        """停止逻辑"""
        try:
            self.logger.info("🛑 停止增强执行引擎")

            # 设置关闭事件
            self._shutdown_event.set()

            # 等待工作线程完成
            if self._worker_tasks:
                await asyncio.gather(*self._worker_tasks, return_exceptions=True)

            # 关闭线程池
            if self._thread_pool is not None:
                self._thread_pool.shutdown(wait=True)
                self._thread_pool = None

            self.logger.info("✅ 增强执行引擎已停止")
            return True

        except Exception as e:
            self.logger.error(f"❌ 增强执行引擎停止失败: {e}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭逻辑"""
        try:
            # 清理资源
            self._task_queue.clear()
            self._running_tasks.clear()
            self._completed_tasks.clear()
            self._workflows.clear()
            self._executors.clear()
            self._executor_registry.clear()

            self.logger.info("✅ 增强执行引擎已关闭")
            return True

        except Exception as e:
            self.logger.error(f"❌ 增强执行引擎关闭失败: {e}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查工作线程状态
            active_workers = sum(1 for task in self._worker_tasks if not task.done())

            # 检查队列大小
            queue_size = self._task_queue.size()

            # 检查运行任务数量
            running_count = len(self._running_tasks)

            # 基本健康检查
            healthy = (
                active_workers > 0
                and queue_size < MAX_QUEUE_SIZE
                and running_count <= self.max_concurrent
            )

            self.logger.debug(
                f"健康检查: 工作线程={active_workers}, 队列={queue_size}, 运行中={running_count}"
            )

            return healthy

        except Exception as e:
            self.logger.error(f"❌ 健康检查失败: {e}")
            return False

    async def execute_task(self, task: Task) -> TaskResult:
        """
        执行任务

        Args:
            task: 标准任务对象

        Returns:
            TaskResult: 任务执行结果
        """
        result = TaskResult(task_id=task.task_id, status=TaskStatus.RUNNING)

        try:
            # 验证任务
            if not await self._validate_task(task):
                raise ValueError(f"任务验证失败: {task.task_id}")

            # 执行任务
            task.start()
            self._running_tasks[task.task_id] = task

            # 选择执行器
            executor = self._select_executor(task)
            if not executor:
                raise RuntimeError(f"未找到合适的执行器: {task.action_type}")

            # 执行任务
            start_time = time.time()

            try:
                if inspect.iscoroutinefunction(executor):
                    result_data = await executor(task)
                else:
                    result_data = await asyncio.get_event_loop().run_in_executor(
                        self._get_thread_pool(), executor, task
                    )

                execution_time = time.time() - start_time

                # 创建成功结果
                task.complete(True, result_data)
                result.status = TaskStatus.COMPLETED
                result.result = result_data
                result.duration = execution_time
                result.end_time = datetime.now()

                self.logger.info(f"✅ 任务执行完成: {task.name}")

            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = str(e)

                # 创建失败结果
                task.complete(False, error=error_msg)
                result.status = TaskStatus.FAILED
                result.error = error_msg
                result.duration = execution_time
                result.end_time = datetime.now()

                self.logger.error(f"❌ 任务执行失败: {task.name} - {error_msg}")

            finally:
                # 从运行任务中移除
                self._running_tasks.pop(task.task_id, None)
                self._completed_tasks[task.task_id] = task

                # 更新统计
                self._update_stats(task, result.status == TaskStatus.COMPLETED)

            return result

        except Exception as e:
            self.logger.error(f"❌ 执行任务失败: {e}")
            result.status = TaskStatus.FAILED
            result.error = str(e)
            return result

    async def _validate_task(self, task: Task) -> bool:
        """验证任务"""
        try:
            # 基本字段检查
            if not task.task_id or not task.name:
                return False

            # 检查执行器
            action_type_str = task.action_type.value if isinstance(task.action_type, ActionType) else str(task.action_type)
            if action_type_str not in self._executors:
                # 尝试使用默认执行器
                if "function_call" not in self._executors:
                    return False

            # 检查依赖
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id not in self._completed_tasks:
                        return False
                    dep_task = self._completed_tasks[dep_id]
                    if dep_task.status != TaskStatus.COMPLETED:
                        return False

            return True

        except Exception as e:
            self.logger.error(f"❌ 任务验证异常: {e}")
            return False

    async def _task_scheduler(self):
        """任务调度器"""
        while not self._shutdown_event.is_set():
            try:
                # 从队列获取任务
                task = self._task_queue.dequeue()
                if task is None:
                    await asyncio.sleep(0.1)
                    continue

                # 检查依赖
                if not task.can_start(self._completed_tasks):
                    # 重新入队
                    self._task_queue.enqueue(task)
                    await asyncio.sleep(0.1)
                    continue

                # 检查并发限制
                if len(self._running_tasks) >= self.max_concurrent:
                    # 重新入队
                    self._task_queue.enqueue(task)
                    await asyncio.sleep(0.1)
                    continue

                # 执行任务
                asyncio.create_task(self._execute_task_internal(task))

            except Exception as e:
                self.logger.error(f"❌ 任务调度器异常: {e}")
                await asyncio.sleep(1)

    async def _execute_task_internal(self, task: Task):
        """内部任务执行"""
        task_id = task.task_id

        try:
            # 标记任务开始
            task.start()
            self._running_tasks[task_id] = task

            self.logger.info(f"🚀 开始执行任务: {task.name} ({task_id[:8]}...)")

            # 选择执行器
            executor = self._select_executor(task)
            if not executor:
                raise RuntimeError(f"未找到合适的执行器: {task.action_type}")

            # 执行任务
            start_time = time.time()
            result = await self.execute_with_metrics(
                f"execute_task_{task.action_type}", executor, task
            )
            execution_time = time.time() - start_time

            # 完成任务
            task.complete(success=True, data=result)

            # 移动到完成列表
            self._completed_tasks[task_id] = task
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

            # 更新统计
            self._update_stats(task, success=True)

            self.logger.info(
                f"✅ 任务执行成功: {task.name} ({task_id[:8]}...), 耗时: {execution_time:.2f}s"
            )

        except Exception as e:
            # 任务失败
            error_msg = f"任务执行失败: {e!s}"
            self.logger.error(f"❌ {error_msg}")

            task.complete(success=False, error=error_msg)

            # 移动到完成列表
            self._completed_tasks[task_id] = task
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

            # 更新统计
            self._update_stats(task, success=False)

            # 检查是否需要重试
            if task.retry():
                # 重新入队
                self._task_queue.enqueue(task)
                self.logger.info(f"🔄 任务重试: {task.name} (第{task.retry_count}次)")

    def _select_executor(self, task: Task) -> Callable | None:
        """选择执行器"""
        action_type_str = task.action_type.value if isinstance(task.action_type, ActionType) else str(task.action_type)

        # 优先使用 action_type
        if action_type_str in self._executors:
            return self._executors[action_type_str]

        # 如果有 function，使用函数调用执行器
        if task.function is not None:
            return self._executors.get("function_call")

        # 默认执行器
        return self._executors.get("function_call")

    async def _execute_function_call(self, task: Task) -> Any:
        """执行函数调用"""
        try:
            # 使用 Task 的 function 字段
            if task.function is not None:
                func = task.function
                args = task.args
                kwargs = task.kwargs

                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(self._get_thread_pool(), lambda: func(*args, **kwargs))

            # 兼容旧的 action_data 方式
            func_name = task.action_data.get("function") if task.action_data else None
            if func_name:
                args = task.action_data.get("args", [])
                kwargs = task.action_data.get("kwargs", {})

                if func_name == "print":
                    message = args[0] if args else kwargs.get("message", "")
                    logger.info(f"[{self.agent_id}] {message}")
                    return {"printed": True, "message": message}

                # 注册的自定义函数
                elif func_name in self._executor_registry:
                    func = self._executor_registry[func_name]
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(self._get_thread_pool(), func, *args, **kwargs)

            raise ValueError("未指定要执行的函数")

        except Exception as e:
            self.logger.error(f"❌ 函数调用执行失败: {e}")
            raise

    async def _execute_api_call(self, task: Task) -> Any:
        """执行API调用"""
        try:
            import aiohttp

            # 优先使用 action_data
            data = task.action_data if task.action_data else task.kwargs
            url = data.get("url") if data else None
            if not url or not isinstance(url, str):
                raise ValueError("url 参数缺失或无效")

            method = data.get("method", "GET") if data else "GET"
            request_data = data.get("data", {}) if data else {}
            headers = data.get("headers", {}) if data else {}

            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=request_data, headers=headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json(),
                        "headers": dict(response.headers),
                    }

        except Exception as e:
            self.logger.error(f"❌ API调用执行失败: {e}")
            raise

    async def _execute_workflow(self, task: Task) -> Any:
        """执行工作流"""
        try:
            steps = task.action_data.get("steps", []) if task.action_data else []
            results = []

            for i, step in enumerate(steps):
                step_task = Task(
                    task_id=f"{task.task_id}_step_{i}",
                    name=f"{task.name}_step_{i}",
                    action_type=ActionType.FUNCTION_CALL,
                    action_data=step.get("data", {}),
                    priority=task.priority,
                )

                step_result = await self.execute_task(step_task)
                results.append(step_result)

            return {"workflow_completed": True, "results": results}

        except Exception as e:
            self.logger.error(f"❌ 工作流执行失败: {e}")
            raise

    async def _execute_command(self, task: Task) -> Any:
        """执行命令"""
        try:
            import asyncio.subprocess

            data = task.action_data if task.action_data else task.kwargs
            command = data.get("command") if data else None
            if not command:
                raise ValueError("缺少命令")

            cwd = data.get("cwd") if data else None

            if isinstance(command, str):
                import shlex
                command = shlex.split(command)

            process = await asyncio.subprocess.create_subprocess_exec(
                *command, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }

        except Exception as e:
            self.logger.error(f"❌ 命令执行失败: {e}")
            raise

    async def _worker(self, worker_id: str):
        """工作线程"""
        self.logger.debug(f"🏃 工作线程启动: {worker_id}")

        while not self._shutdown_event.is_set():
            try:
                # 等待任务或关闭事件
                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"❌ 工作线程异常 [{worker_id}]: {e}")

        self.logger.debug(f"🛑 工作线程停止: {worker_id}")

    def _update_stats(self, task: Task, success: bool) -> None:
        """
        更新统计信息

        Args:
            task: 任务对象
            success: 是否成功
        """
        self._stats["total_tasks"] += 1

        if success:
            self._stats["completed_tasks"] += 1

            # 更新平均执行时间
            if task.started_at and task.completed_at:
                execution_time = (task.completed_at - task.started_at).total_seconds()
                total_time = self._stats["average_execution_time"] * (self._stats["completed_tasks"] - 1)
                total_time += execution_time
                self._stats["average_execution_time"] = total_time / self._stats["completed_tasks"]
        else:
            self._stats["failed_tasks"] += 1

        self._stats["queue_size"] = self._task_queue.size()

    def register_executor(self, name: str, func: Callable) -> None:
        """
        注册执行器

        Args:
            name: 执行器名称
            func: 执行函数
        """
        self._executor_registry[name] = func
        self.logger.info(f"📝 注册执行器: {name}")

    def get_task(self, task_id: str) -> Task | None:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            Optional[Task]: 任务对象
        """
        # 查找运行中的任务
        if task_id in self._running_tasks:
            return self._running_tasks[task_id]

        # 查找完成的任务
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]

        # 查找队列中的任务
        return self._task_queue.get_task(task_id)

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            dict[str, Any]: 统计信息
        """
        return {
            "engine_id": self.module_id,
            "agent_id": self.agent_id,
            "stats": self._stats.copy(),
            "queue_info": self._task_queue.get_summary(),
            "running_tasks": len(self._running_tasks),
            "completed_tasks": len(self._completed_tasks),
            "registered_executors": list(self._executor_registry.keys()),
            "workers": {
                "total": len(self._worker_tasks),
                "active": sum(1 for task in self._worker_tasks if not task.done()),
            },
        }

    async def create_workflow(self, name: str, tasks_data: list[dict]) -> str:
        """
        创建工作流

        Args:
            name: 工作流名称
            tasks_data: 任务数据列表

        Returns:
            str: 工作流ID
        """
        try:
            workflow_id = str(uuid.uuid4())
            workflow_tasks = []

            for i, task_data in enumerate(tasks_data):
                # 获取优先级
                priority_value = task_data.get("priority", TaskPriority.NORMAL.value)
                try:
                    priority = TaskPriority(priority_value)
                except ValueError:
                    priority = TaskPriority.NORMAL

                task = Task(
                    task_id=f"{workflow_id}_task_{i}",
                    name=task_data.get("name", f"{name}_step_{i}"),
                    action_type=ActionType.FUNCTION_CALL,
                    action_data=task_data.get("data", {}),
                    priority=priority,
                )
                workflow_tasks.append(task)

            # 创建工作流任务
            workflow_task = Task(
                task_id=workflow_id,
                name=name,
                action_type=ActionType.WORKFLOW,
                action_data={
                    "steps": [
                        {"action": t.action_type, "data": t.action_data} for t in workflow_tasks
                    ]
                },
                priority=TaskPriority.HIGH,
            )

            # 添加依赖关系
            for i, task in enumerate(workflow_tasks):
                if i > 0:
                    task.dependencies.append(workflow_tasks[i - 1].task_id)

            # 存储工作流信息
            self._workflows[workflow_id] = {
                "id": workflow_id,
                "name": name,
                "tasks": workflow_tasks,
                "created_at": datetime.now(),
            }

            # 执行工作流
            await self.execute_task(workflow_task)

            self.logger.info(f"🔀 工作流创建成功: {name} ({workflow_id[:8]}...)")
            return workflow_id

        except Exception as e:
            self.logger.error(f"❌ 创建工作流失败: {e}")
            raise
