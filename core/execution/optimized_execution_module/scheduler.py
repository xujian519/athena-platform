#!/usr/bin/env python3
"""
优化版执行模块 - 智能任务调度器
Optimized Execution Module - Intelligent Task Scheduler

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import multiprocessing
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from typing import Any

import psutil

from core.logging_config import setup_logging

from .resource_monitor import ResourceMonitor
from .task_queue import TaskPriorityQueue
from .types import ResourceUsage, Task, TaskStatus

logger = setup_logging()


class IntelligentScheduler:
    """智能任务调度器 - 支持优先级调度、资源感知、依赖管理"""

    def __init__(self, config: dict[str, Any]):
        """初始化智能任务调度器

        Args:
            config: 配置字典
        """
        self.config = config
        self.max_concurrent_tasks = config.get("max_concurrent_tasks", multiprocessing.cpu_count())
        self.task_queue = TaskPriorityQueue()
        self.running_tasks = {}
        self.completed_tasks = {}
        self.failed_tasks = {}

        # 资源监控
        self.resource_monitor = ResourceMonitor()
        self.available_resources = ResourceUsage(
            cpu_cores=multiprocessing.cpu_count(),
            memory_mb=psutil.virtual_memory().total // (1024 * 1024),
            disk_io_mb_s=100.0,
            network_mbps=1000.0,
            gpu_memory_mb=self._get_gpu_memory(),
        )

        # 调度策略配置
        self.scheduling_strategy = config.get(
            "scheduling_strategy", "priority_fifo"
        )  # priority_fifo, round_robin, load_balance
        self.load_balance_threshold = config.get("load_balance_threshold", 0.8)  # 80%负载阈值
        self.adaptive_scheduling = config.get("adaptive_scheduling", True)

        # 线程池和进程池
        self.thread_pool = ThreadPoolExecutor(
            max_workers=config.get("max_thread_workers", self.max_concurrent_tasks)
        )
        self.process_pool = ProcessPoolExecutor(
            max_workers=config.get("max_process_workers", min(4, multiprocessing.cpu_count() // 2))
        )

        # 依赖关系管理
        self.dependency_graph = {}
        self.task_dependencies = defaultdict(set)

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
            "cpu_utilization": 0.0,
            "memory_utilization": 0.0,
            "queue_size": 0,
            "throughput": 0.0,  # 任务/秒
        }

        logger.info("📋 智能任务调度器初始化完成")

    def _get_gpu_memory(self) -> float:
        """获取GPU内存总量

        Returns:
            GPU内存总量(MB),如果不可用则返回0
        """
        try:
            import torch

            if torch.cuda.is_available():
                return torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
        except ImportError as e:
            logger.warning(f"可选模块导入失败，使用降级方案: {e}")
        return 0.0

    async def submit_task(self, task: Task) -> bool:
        """提交任务

        Args:
            task: 要提交的任务对象

        Returns:
            是否提交成功
        """
        try:
            # 验证依赖关系
            if not self._validate_dependencies(task):
                logger.error(f"任务 {task.task_id} 依赖关系验证失败")
                return False

            # 检查资源需求
            if not self._check_resource_availability(task):
                logger.warning(f"任务 {task.task_id} 资源不足,加入队列等待")
                # 仍然放入队列,等待资源可用
                pass

            # 添加到队列
            self.task_queue.put(task)
            self.stats["total_tasks"] += 1
            self.stats["queue_size"] = self.task_queue.size()

            # 尝试调度
            await self._schedule_tasks()

            logger.debug(f"✅ 任务 {task.task_id} 已提交到队列")
            return True

        except Exception as e:
            logger.error(f"❌ 任务提交失败 {task.task_id}: {e}")
            return False

    def _validate_dependencies(self, task: Task) -> bool:
        """验证任务依赖关系

        Args:
            task: 要验证的任务

        Returns:
            依赖关系是否有效
        """
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks and dep_id not in self.dependency_graph:
                logger.error(f"任务 {task.task_id} 依赖不存在的任务 {dep_id}")
                return False
        return True

    def _check_resource_availability(self, task: Task) -> bool:
        """检查资源可用性

        Args:
            task: 要检查的任务

        Returns:
            资源是否可用
        """
        current_usage = self.resource_monitor.get_current_usage()
        available_cpu = self.available_resources.cpu_cores - current_usage.cpu_cores
        available_memory = self.available_resources.memory_mb - current_usage.memory_mb

        return (
            available_cpu >= task.estimated_cpu_usage
            and available_memory >= task.estimated_memory_usage
        )

    async def _schedule_tasks(self):
        """调度任务执行"""
        while (
            len(self.running_tasks) < self.max_concurrent_tasks and not self.task_queue.is_empty()
        ):
            task = self.task_queue.get()
            if not task:
                break

            # 检查依赖是否完成
            if not self._check_dependencies_completed(task):
                # 依赖未完成,重新放回队列
                self.task_queue.put(task)
                break

            # 检查资源可用性
            if not self._check_resource_availability(task):
                # 资源不足,重新放回队列
                self.task_queue.put(task)
                break

            # 执行任务
            await self._execute_task(task)

    def _check_dependencies_completed(self, task: Task) -> bool:
        """检查任务依赖是否完成

        Args:
            task: 要检查的任务

        Returns:
            所有依赖是否都已完成
        """
        return all(dep_id in self.completed_tasks for dep_id in task.dependencies)

    async def _execute_task(self, task: Task):
        """执行任务

        Args:
            task: 要执行的任务
        """
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.running_tasks[task.task_id] = task

            # 更新统计
            self.stats["queue_size"] = self.task_queue.size()

            logger.info(f"🚀 开始执行任务: {task.task_id}")

            # 选择执行方式
            if self._should_use_process_pool(task):
                future = self.process_pool.submit(task.function, *task.args, **task.kwargs)
            else:
                future = self.thread_pool.submit(task.function, *task.args, **task.kwargs)

            # 设置超时
            if task.timeout:
                future = asyncio.wrap_future(future)
                try:
                    result = await asyncio.wait_for(future, timeout=task.timeout)
                except asyncio.TimeoutError:
                    task.status = TaskStatus.TIMEOUT
                    task.error = f"任务超时 ({task.timeout}s)"
                    self._handle_task_completion(task, False)
                    return
            else:
                result = await asyncio.wrap_future(future)

            # 任务完成
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 1.0

            self._handle_task_completion(task, True)
            logger.info(f"✅ 任务完成: {task.task_id}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._handle_task_completion(task, False)
            logger.error(f"❌ 任务失败 {task.task_id}: {e}")

    def _should_use_process_pool(self, task: Task) -> bool:
        """判断是否应该使用进程池

        Args:
            task: 要判断的任务

        Returns:
            是否应该使用进程池
        """
        # CPU密集型任务使用进程池
        return task.estimated_cpu_usage > 0.7

    def _handle_task_completion(self, task: Task, success: bool) -> Any:
        """处理任务完成

        Args:
            task: 完成的任务
            success: 是否成功完成

        Returns:
            任务结果
        """
        # 从运行队列移除
        self.running_tasks.pop(task.task_id, None)

        if success:
            self.completed_tasks[task.task_id] = task
            self.stats["completed_tasks"] += 1
        else:
            self.failed_tasks[task.task_id] = task
            self.stats["failed_tasks"] += 1

            # 重试机制
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.error = None
                self.task_queue.put(task)
                logger.info(f"🔄 任务重试 {task.task_id} (第 {task.retry_count} 次)")

        # 更新平均执行时间
        if task.started_at and task.completed_at:
            execution_time = (task.completed_at - task.started_at).total_seconds()
            completed = self.stats["completed_tasks"]
            current_avg = self.stats["average_execution_time"]
            new_avg = (current_avg * (completed - 1) + execution_time) / completed
            self.stats["average_execution_time"] = new_avg

        # 计算吞吐量
        total_tasks = self.stats["completed_tasks"] + self.stats["failed_tasks"]
        if total_tasks > 0:
            self.stats["throughput"] = total_tasks / max(
                1,
                (
                    datetime.now()
                    - min(
                        (task.started_at for task in self.completed_tasks.values()),
                        default=datetime.now(),
                    )
                ).total_seconds(),
            )

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 要取消的任务ID

        Returns:
            是否成功取消
        """
        # 从队列移除
        if self.task_queue.remove(task_id):
            task = self._get_task_from_memory(task_id)
            if task:
                task.status = TaskStatus.CANCELLED
            return True

        # 从运行任务取消
        if task_id in self.running_tasks:
            # 注意:实际的线程/进程取消比较复杂,这里简化处理
            task = self.running_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            return True

        return False

    def _get_task_from_memory(self, task_id: str) -> Task | None:
        """从内存获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象,如果未找到则返回None
        """
        # 这里需要从队列或其他地方获取任务,简化实现
        return None

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息,如果未找到则返回None
        """
        task = None
        location = None

        # 在各个位置查找任务
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            location = "running"
        elif task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            location = "completed"
        elif task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            location = "failed"

        if task:
            return {
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status.value,
                "priority": task.priority.value,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.error,
                "retry_count": task.retry_count,
                "location": location,
            }

        return None

    def get_scheduler_stats(self) -> dict[str, Any]:
        """获取调度器统计信息

        Returns:
            包含调度器统计信息的字典
        """
        # 更新资源利用率
        current_usage = self.resource_monitor.get_current_usage()
        self.stats["cpu_utilization"] = current_usage.cpu_cores / self.available_resources.cpu_cores
        self.stats["memory_utilization"] = (
            current_usage.memory_mb / self.available_resources.memory_mb
        )
        self.stats["queue_size"] = self.task_queue.size()

        return {
            "scheduler_stats": self.stats.copy(),
            "resource_utilization": {
                "cpu": f"{self.stats['cpu_utilization']:.1%}",
                "memory": f"{self.stats['memory_utilization']:.1%}",
                "running_tasks": len(self.running_tasks),
                "max_concurrent": self.max_concurrent_tasks,
            },
            "queue_stats": {
                "pending_tasks": self.task_queue.size(),
                "completed_tasks": self.stats["completed_tasks"],
                "failed_tasks": self.stats["failed_tasks"],
                "average_execution_time": f"{self.stats['average_execution_time']:.3f}s",
                "throughput": f"{self.stats['throughput']:.2f} tasks/s",
            },
        }
