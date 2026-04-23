#!/usr/bin/env python3
from __future__ import annotations
"""
并行化模式执行器 (Parallelization Pattern)
基于《智能体设计》并行化模式的实现

功能:
- 并发执行独立任务
- 资源管理和负载均衡
- 异步结果收集和聚合
- 故障处理和重试机制

应用场景:
- 小娜: 批量专利分析
- 小诺: 多个系统同时优化
- 云熙: 并行目标跟踪
- 小宸: 多内容并行生成

实施优先级: ⭐⭐⭐⭐ (高)
预期收益: 大幅提升处理效率

作者: Athena AI系统
版本: 2.0.0
更新时间: 2026-01-27
"""

import asyncio
import json
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# 从统一的 shared_types.py 导入类型定义
from .shared_types import (
    TaskPriority,
    TaskStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class ParallelTask:
    """并行任务 - 扩展自统一Task类，添加并行执行特有属性"""

    # 基础任务属性
    id: str
    name: str
    coroutine: Callable  # 要执行的协程函数
    args: tuple = ()
    kwargs: dict | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: float = 300  # 5分钟超时
    retry_count: int = 0
    max_retries: int = 2
    dependencies: Optional[list[str]] = None
    estimated_time: float = 0  # 预估执行时间(秒)
    result: Any = None
    error: Exception | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: TaskStatus = TaskStatus.PENDING

    def __post_init__(self):
        """初始化后处理"""
        if self.kwargs is None:
            self.kwargs = {}
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class ExecutionResult:
    """执行结果"""

    task_id: str
    task_name: str
    success: bool
    result: Any = None
    error: Exception | None = None
    execution_time: float = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)


class ParallelExecutor:
    """并行执行器"""

    def __init__(
        self,
        max_workers: int = 10,
        max_concurrent_tasks: int = 20,
        timeout: float = 600,  # 10分钟默认超时
    ):
        self.max_workers = max_workers
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = timeout

        # 任务管理
        self.tasks: dict[str, ParallelTask] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running_tasks: set[str] = set()
        self.completed_tasks: dict[str, ExecutionResult] = {}

        # 信号量和控制
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # 统计信息
        self.stats: dict[str, float | int] = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time": 0.0,
            "parallel_efficiency": 0.0,
        }

    async def submit_task(
        self,
        task_id: str,
        task_name: str,
        coroutine: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        dependencies: Optional[list[str]] = None,
        max_retries: int = 2,
    ) -> bool:
        """提交并行任务"""

        if kwargs is None:
            kwargs = {}
        if dependencies is None:
            dependencies = []

        if task_id in self.tasks:
            logger.warning(f"任务 {task_id} 已存在")
            return False

        task = ParallelTask(
            id=task_id,
            name=task_name,
            coroutine=coroutine,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout or self.default_timeout,
            dependencies=dependencies,
            max_retries=max_retries,
        )

        self.tasks[task_id] = task
        # 注意：priority值越小优先级越高，所以取负值用于优先队列
        await self.task_queue.put((-task.priority.value, task_id))

        self.stats["total_tasks"] += 1
        logger.info(f"任务 {task_id} ({task_name}) 已提交")

        return True

    async def execute_all(self) -> dict[str, ExecutionResult]:
        """执行所有任务"""
        start_time = datetime.now()

        logger.info(f"开始并行执行 {len(self.tasks)} 个任务")

        # 启动工作协程
        workers = [
            asyncio.create_task(self._worker(f"worker_{i}")) for i in range(self.max_workers)
        ]

        # 等待所有任务完成
        await self._wait_for_completion()

        # 停止工作协程
        for worker in workers:
            worker.cancel()

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # 更新统计信息
        self.stats["total_execution_time"] = total_time
        self._calculate_parallel_efficiency()

        logger.info(f"所有任务执行完成,总耗时: {total_time:.2f}秒")

        return self.completed_tasks

    async def _worker(self, worker_name: str):
        """工作协程"""
        logger.info(f"工作协程 {worker_name} 启动")

        while True:
            try:
                # 获取任务
                _, task_id = await self.task_queue.get()

                if task_id == "STOP":
                    break

                task = self.tasks[task_id]

                # 检查依赖
                if not self._check_dependencies(task):
                    # 依赖未满足,重新排队
                    await self.task_queue.put((-task.priority.value, task_id))
                    await asyncio.sleep(1)  # 短暂等待
                    continue

                # 执行任务
                async with self.semaphore:
                    if task_id not in self.running_tasks:
                        self.running_tasks.add(task_id)
                        try:
                            result = await self._execute_task(task)

                            # 如果 result 是 None,表示任务正在重试,不添加到 completed_tasks
                            if result is not None:
                                self.completed_tasks[task_id] = result

                                if result.success:
                                    self.stats["completed_tasks"] += 1
                                else:
                                    self.stats["failed_tasks"] += 1

                        except Exception as e:
                            logger.error(f"任务 {task_id} 执行失败: {e}")
                            self.stats["failed_tasks"] += 1

                        finally:
                            self.running_tasks.discard(task_id)

                self.task_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作协程 {worker_name} 出错: {e}")

        logger.info(f"工作协程 {worker_name} 停止")

    def _check_dependencies(self, task: ParallelTask) -> bool:
        """检查任务依赖是否满足"""
        dependencies = task.dependencies or []
        for dep_id in dependencies:
            if dep_id not in self.completed_tasks:
                return False
            if not self.completed_tasks[dep_id].success:
                return False
        return True

    async def _execute_task(
        self, task: ParallelTask
    ) -> ExecutionResult | None:  # 允许返回 None(重试时)
        """执行单个任务"""
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()

        logger.info(f"开始执行任务 {task.id} ({task.name})")

        try:
            # 执行任务
            async with asyncio.timeout(task.timeout):
                if task.args or task.kwargs:
                    result = await task.coroutine(*task.args, **(task.kwargs or {}))
                else:
                    result = await task.coroutine()

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()

            execution_time = (task.end_time - task.start_time).total_seconds()

            logger.info(f"任务 {task.id} 执行成功,耗时: {execution_time:.2f}秒")

            return ExecutionResult(
                task_id=task.id,
                task_name=task.name,
                success=True,
                result=result,
                execution_time=execution_time,
                start_time=task.start_time,
                end_time=task.end_time,
            )

        except asyncio.TimeoutError:
            task.error = Exception(f"任务超时 ({task.timeout}秒)")
            task.status = TaskStatus.FAILED
            task.end_time = datetime.now()

            logger.warning(f"任务 {task.id} 执行超时")

        except Exception as e:
            task.error = e
            task.status = TaskStatus.FAILED
            task.end_time = datetime.now()

            # 重试机制
            if task.retry_count < task.max_retries:
                logger.warning(
                    f"任务 {task.id} 执行失败,准备重试 ({task.retry_count + 1}/{task.max_retries})"
                )
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                await self.task_queue.put((-task.priority.value, task.id))
                return None  # 重试时不返回结果

            logger.error(f"任务 {task.id} 执行失败: {e}")

        execution_time = (task.end_time - task.start_time).total_seconds()

        return ExecutionResult(
            task_id=task.id,
            task_name=task.name,
            success=False,
            error=task.error,
            execution_time=execution_time,
            start_time=task.start_time,
            end_time=task.end_time,
        )

    async def _wait_for_completion(self):
        """等待所有任务完成"""
        while self.running_tasks or not self.task_queue.empty():
            await asyncio.sleep(0.1)

        # 停止工作协程
        for _ in range(self.max_workers):
            await self.task_queue.put(("STOP", "STOP"))

    def _calculate_parallel_efficiency(self) -> None:
        """计算并行效率"""
        if self.stats["total_tasks"] > 0:
            # 简单的并行效率计算
            actual_time = self.stats["total_execution_time"]
            estimated_sequential_time = sum(
                task.estimated_time or 60 for task in self.tasks.values()
            )

            if estimated_sequential_time > 0:
                self.stats["parallel_efficiency"] = (
                    min(estimated_sequential_time / actual_time, self.stats["total_tasks"])
                    / self.stats["total_tasks"]
                )

    async def execute_in_batches(
        self, batch_size: int = 5, delay_between_batches: float = 1.0
    ) -> dict[str, ExecutionResult]:
        """批量执行任务"""

        all_results = {}
        task_ids = list(self.tasks.keys())

        for i in range(0, len(task_ids), batch_size):
            batch_ids = task_ids[i : i + batch_size]

            logger.info(f"执行批次 {i//batch_size + 1}: {len(batch_ids)} 个任务")

            # 清空已完成任务
            self.completed_tasks.clear()
            self.running_tasks.clear()

            # 创建新队列只包含当前批次任务
            self.task_queue = asyncio.PriorityQueue()
            for task_id in batch_ids:
                task = self.tasks[task_id]
                await self.task_queue.put((-task.priority.value, task_id))

            # 执行当前批次
            batch_results = await self.execute_all()
            all_results.update(batch_results)

            # 批次间延迟
            if i + batch_size < len(task_ids):
                await asyncio.sleep(delay_between_batches)

        return all_results

    async def monitor_execution(self) -> dict[str, Any]:
        """监控执行状态"""
        while True:
            status = {
                "pending_tasks": len(self.tasks)
                - len(self.completed_tasks)
                - len(self.running_tasks),
                "running_tasks": len(self.running_tasks),
                "completed_tasks": len(self.completed_tasks),
                "failed_tasks": self.stats["failed_tasks"],
                "success_rate": (
                    self.stats["completed_tasks"]
                    / max(1, self.stats["completed_tasks"] + self.stats["failed_tasks"])
                ),
                "queue_size": self.task_queue.qsize(),
                "stats": self.stats,
            }

            # 在实际应用中,这里可以将状态发送到监控系统
            logger.info(f"执行状态: {json.dumps(status, indent=2, ensure_ascii=False)}")

            await asyncio.sleep(10)  # 每10秒更新一次状态

    def get_execution_report(self) -> dict[str, Any]:
        """获取执行报告"""
        successful_tasks = [r for r in self.completed_tasks.values() if r.success]
        failed_tasks = [r for r in self.completed_tasks.values() if not r.success]

        report = {
            "summary": {
                "total_tasks": self.stats["total_tasks"],
                "successful_tasks": len(successful_tasks),
                "failed_tasks": len(failed_tasks),
                "success_rate": (len(successful_tasks) / max(1, len(self.completed_tasks))),
                "total_execution_time": self.stats["total_execution_time"],
                "parallel_efficiency": self.stats["parallel_efficiency"],
            },
            "successful_tasks": [
                {"task_id": r.task_id, "task_name": r.task_name, "execution_time": r.execution_time}
                for r in successful_tasks
            ],
            "failed_tasks": [
                {
                    "task_id": r.task_id,
                    "task_name": r.task_name,
                    "error": str(r.error),
                    "execution_time": r.execution_time,
                }
                for r in failed_tasks
            ],
        }

        return report


# 使用示例
async def example_parallel_usage():
    """并行化模式使用示例"""

    executor = ParallelExecutor(max_workers=5, max_concurrent_tasks=10)

    # 示例任务函数
    async def example_task_1():
        await asyncio.sleep(2)
        return "任务1结果"

    async def example_task_2(data):
        await asyncio.sleep(3)
        return f"任务2结果: {data}"

    async def example_task_3():
        await asyncio.sleep(1)
        return {"status": "completed", "data": [1, 2, 3]}

    # 提交任务
    await executor.submit_task("task_1", "示例任务1", example_task_1, priority=TaskPriority.HIGH)

    await executor.submit_task(
        "task_2", "示例任务2", example_task_2, args=("测试数据",), priority=TaskPriority.NORMAL
    )

    await executor.submit_task("task_3", "示例任务3", example_task_3, priority=TaskPriority.LOW)

    # 执行所有任务
    results = await executor.execute_all()

    # 输出结果
    for task_id, result in results.items():
        print(f"任务 {task_id}: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"  结果: {result.result}")

    # 获取执行报告
    report = executor.get_execution_report()
    print(f"\n执行报告: {json.dumps(report, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    asyncio.run(example_parallel_usage())
