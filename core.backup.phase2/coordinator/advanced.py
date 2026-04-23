#!/usr/bin/env python3
"""Coordinator高级功能

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

提供Coordinator的高级功能:
- 任务依赖管理
- 任务超时处理
- 失败重试机制
- 任务链执行
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .base import Coordinator, TaskAssignment

logger = logging.getLogger(__name__)


@dataclass
class TaskDependency:
    """任务依赖关系

    Attributes:
        task_id: 任务ID
        depends_on: 依赖的任务ID列表
        wait_mode: 等待模式 (all/any)
    """

    task_id: str
    depends_on: list[str]
    wait_mode: str = "all"  # all: 等待所有依赖完成, any: 任一依赖完成即可


@dataclass
class TaskRetryConfig:
    """任务重试配置

    Attributes:
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        backoff_factor: 退避因子
        max_delay: 最大延迟（秒）
    """

    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0


class AdvancedCoordinator:
    """高级Coordinator

    在基础Coordinator功能之上添加:
    - 任务依赖管理
    - 任务超时处理
    - 失败重试机制
    - 任务链执行
    """

    def __init__(self, coordinator: Coordinator):
        """初始化高级Coordinator

        Args:
            coordinator: 基础Coordinator实例
        """
        self._coordinator = coordinator
        self._lock = threading.RLock()

        # 依赖管理
        self._dependencies: dict[str, TaskDependency] = {}
        self._completed_tasks: set[str] = set()

        # 重试管理
        self._retry_configs: dict[str, TaskRetryConfig] = {}
        self._retry_queue: deque[TaskAssignment] = deque()

        # 超时管理
        self._timeout_tasks: dict[str, datetime] = {}
        self._timeout_check_interval = 30  # 秒
        self._timeout_monitor_running = False

        logger.info("高级Coordinator初始化完成")

    # ========================================================================
    # 依赖管理
    # ========================================================================

    def add_dependency(self, dependency: TaskDependency) -> bool:
        """添加任务依赖

        Args:
            dependency: 任务依赖对象

        Returns:
            bool: 是否成功添加
        """
        with self._lock:
            if dependency.task_id in self._dependencies:
                logger.warning(f"任务依赖已存在: {dependency.task_id}")
                return False

            self._dependencies[dependency.task_id] = dependency
            logger.info(f"添加任务依赖: {dependency.task_id} 依赖 {dependency.depends_on}")
            return True

    def check_dependencies(self, task_id: str) -> bool:
        """检查任务依赖是否满足

        Args:
            task_id: 任务ID

        Returns:
            bool: 依赖是否满足
        """
        with self._lock:
            dependency = self._dependencies.get(task_id)
            if not dependency:
                return True

            if dependency.wait_mode == "all":
                return all(d in self._completed_tasks for d in dependency.depends_on)
            else:  # wait_mode == "any"
                return any(d in self._completed_tasks for d in dependency.depends_on)

    def mark_task_completed(self, task_id: str) -> None:
        """标记任务完成

        Args:
            task_id: 任务ID
        """
        with self._lock:
            self._completed_tasks.add(task_id)

            # 检查是否有等待此任务的任务
            ready_tasks = []
            for tid, dep in self._dependencies.items():
                if task_id in dep.depends_on and self.check_dependencies(tid):
                    ready_tasks.append(tid)

            # 清理已完成的依赖
            for tid in ready_tasks:
                del self._dependencies[tid]

            if ready_tasks:
                logger.info(f"依赖满足，任务可执行: {ready_tasks}")

    # ========================================================================
    # 重试机制
    # ========================================================================

    def set_retry_config(self, task_id: str, config: TaskRetryConfig) -> None:
        """设置任务重试配置

        Args:
            task_id: 任务ID
            config: 重试配置
        """
        with self._lock:
            self._retry_configs[task_id] = config

    def schedule_retry(self, assignment: TaskAssignment) -> bool:
        """安排任务重试

        Args:
            assignment: 任务分配对象

        Returns:
            bool: 是否可以重试
        """
        with self._lock:
            config = self._retry_configs.get(assignment.task_id)
            if not config:
                return False

            # 检查重试次数
            retry_count = assignment.metadata.get("retry_count", 0)
            if retry_count >= config.max_retries:
                logger.warning(f"任务达到最大重试次数: {assignment.task_id}")
                return False

            # 计算延迟时间
            delay = min(
                config.retry_delay * (config.backoff_factor**retry_count),
                config.max_delay,
            )

            # 更新重试信息
            assignment.metadata["retry_count"] = retry_count + 1
            assignment.metadata["retry_at"] = datetime.now() + timedelta(seconds=delay)
            assignment.status = "retrying"

            self._retry_queue.append(assignment)
            logger.info(f"安排任务重试: {assignment.task_id}，延迟 {delay:.1f} 秒")

            return True

    def get_ready_retries(self) -> list[TaskAssignment]:
        """获取可以重试的任务

        Returns:
            list[TaskAssignment]: 可重试任务列表
        """
        with self._lock:
            now = datetime.now()
            ready = []

            while self._retry_queue:
                assignment = self._retry_queue[0]
                retry_at = assignment.metadata.get("retry_at")

                if not retry_at or retry_at <= now:
                    ready.append(self._retry_queue.popleft())
                else:
                    break

            return ready

    # ========================================================================
    # 超时处理
    # ========================================================================

    def set_timeout(self, task_id: str, timeout_seconds: int) -> None:
        """设置任务超时

        Args:
            task_id: 任务ID
            timeout_seconds: 超时时间（秒）
        """
        with self._lock:
            self._timeout_tasks[task_id] = datetime.now() + timedelta(
                seconds=timeout_seconds
            )

    def check_timeouts(self) -> list[str]:
        """检查超时任务

        Returns:
            list[str]: 超时任务ID列表
        """
        with self._lock:
            now = datetime.now()
            timeout_tasks = []

            for task_id, deadline in self._timeout_tasks.items():
                if now > deadline:
                    timeout_tasks.append(task_id)

            # 清理超时任务
            for task_id in timeout_tasks:
                del self._timeout_tasks[task_id]

            if timeout_tasks:
                logger.warning(f"检测到超时任务: {timeout_tasks}")

            return timeout_tasks

    def start_timeout_monitor(self) -> None:
        """启动超时监控线程"""
        if self._timeout_monitor_running:
            logger.warning("超时监控已在运行")
            return

        self._timeout_monitor_running = True
        thread = threading.Thread(target=self._timeout_monitor_loop, daemon=True)
        thread.start()
        logger.info("超时监控已启动")

    def stop_timeout_monitor(self) -> None:
        """停止超时监控线程"""
        self._timeout_monitor_running = False
        logger.info("超时监控已停止")

    def _timeout_monitor_loop(self) -> None:
        """超时监控循环"""
        while self._timeout_monitor_running:
            try:
                time.sleep(self._timeout_check_interval)
                if self._timeout_monitor_running:
                    timeout_tasks = self.check_timeouts()
                    for task_id in timeout_tasks:
                        # 标记任务超时
                        assignment = self._coordinator.get_task_assignment(task_id)
                        if assignment and assignment.status == "pending":
                            self._coordinator.fail_task(
                                task_id,
                                assignment.agent_id,
                                "任务执行超时",
                            )
            except Exception as e:
                logger.error(f"超时监控错误: {e}")

    # ========================================================================
    # 任务链
    # ========================================================================

    def create_task_chain(
        self,
        tasks: list[dict[str, Any]],
    ) -> list[str]:
        """创建任务链

        Args:
            tasks: 任务列表，每个任务包含task_id, task_type, payload等

        Returns:
            list[str]: 任务ID列表
        """
        with self._lock:
            task_ids = []

            for i, task_def in enumerate(tasks):
                task_id = task_def.get("task_id") or f"chain_task_{i}"

                # 创建依赖关系（每个任务依赖前一个任务）
                if i > 0:
                    dependency = TaskDependency(
                        task_id=task_id,
                        depends_on=[task_ids[i - 1]],
                        wait_mode="all",
                    )
                    self.add_dependency(dependency)

                task_ids.append(task_id)

            logger.info(f"创建任务链: {task_ids}")
            return task_ids

    # ========================================================================
    # 状态查询
    # ========================================================================

    def get_pending_dependencies(self) -> list[TaskDependency]:
        """获取待处理的依赖

        Returns:
            list[TaskDependency]: 待处理依赖列表
        """
        with self._lock:
            return list(self._dependencies.values())

    def get_retry_queue_size(self) -> int:
        """获取重试队列大小

        Returns:
            int: 重试队列中的任务数量
        """
        with self._lock:
            return len(self._retry_queue)

    def get_timeout_task_count(self) -> int:
        """获取超时任务数量

        Returns:
            int: 超时任务数量
        """
        with self._lock:
            return len(self._timeout_tasks)
