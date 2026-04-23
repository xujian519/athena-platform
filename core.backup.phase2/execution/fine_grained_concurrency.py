from __future__ import annotations
"""
细粒度并发控制器
支持任务级、资源级和操作级的精细化并发控制
"""

import asyncio
import heapq
import inspect
import logging
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, suppress
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class ConcurrencyLevel(Enum):
    """并发级别"""

    TASK = "task"  # 任务级
    RESOURCE = "resource"  # 资源级
    OPERATION = "operation"  # 操作级
    CRITICAL_SECTION = "critical_section"  # 临界区


class LockType(Enum):
    """锁类型"""

    READ = "read"  # 读锁(共享)
    WRITE = "write"  # 写锁(排他)
    UPDATE = "update"  # 更新锁(意向)
    INTENT_SHARED = "is"  # 意向共享
    INTENT_EXCLUSIVE = "ix"  # 意向排他


class Priority(Enum):
    """任务优先级"""

    CRITICAL = 5  # 关键任务
    HIGH = 4  # 高优先级
    NORMAL = 3  # 普通优先级
    LOW = 2  # 低优先级
    BACKGROUND = 1  # 后台任务


@dataclass
class ConcurrencyConfig:
    """并发配置"""

    max_concurrent_tasks: int = 100
    max_concurrent_operations: int = 1000
    max_concurrent_resources: dict[str, int] = field(
        default_factory=lambda: {
            "cpu": psutil.cpu_count() or 4,  # 默认4核,如果cpu_count()返回None
            "memory": 10,  # 并发内存操作
            "io": 50,  # 并发IO操作
            "network": 30,  # 并发网络操作
            "gpu": 2,  # GPU操作
        }
    )
    deadlock_timeout: float = 30.0  # 死锁检测超时
    starvation_timeout: float = 60.0  # 饥饿检测超时
    enable_fair_scheduling: bool = True
    enable_deadlock_detection: bool = True
    enable_starvation_detection: bool = True
    quantum_size: float = 0.1  # 时间片大小(秒)
    aging_factor: float = 0.1  # 老化因子


@dataclass
class TaskRequest:
    """任务请求"""

    task_id: str
    task_func: Callable
    args: tuple
    kwargs: dict
    priority: Priority
    resource_requirements: dict[str, float] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    timeout: float | None = None
    created_at: datetime = field(default_factory=datetime.now)
    wait_time: float = 0.0
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceLock:
    """资源锁"""

    resource_id: str
    lock_type: LockType
    owner_id: str
    acquired_at: datetime
    expires_at: datetime | None = None
    shared_owners: set[str] = field(default_factory=set)
    wait_queue: deque = field(default_factory=deque)


@dataclass
class ConcurrencyStats:
    """并发统计"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_wait_time: float = 0.0
    avg_execution_time: float = 0.0
    active_tasks: int = 0
    queued_tasks: int = 0
    resource_usage: dict[str, float] = field(default_factory=dict)
    lock_contentions: int = 0
    deadlocks_detected: int = 0
    starvations_detected: int = 0


class FineGrainedConcurrencyController:
    """细粒度并发控制器"""

    def __init__(self, config: ConcurrencyConfig | None = None):
        self.config = config or ConcurrencyConfig()

        # 任务管理
        self.task_queue = []
        self.active_tasks = {}
        self.task_dependencies = defaultdict(set)
        self.task_results = {}

        # 锁管理
        self.resource_locks = {}
        self.lock_table = {}  # 锁表
        self.lock_graph = defaultdict(set)  # 锁依赖图

        # 资源管理
        self.resource_usage = defaultdict(float)
        self.resource_limits = self.config.max_concurrent_resources.copy()

        # 并发控制
        self.semaphores = {
            "task": asyncio.Semaphore(self.config.max_concurrent_tasks),
            "operation": asyncio.Semaphore(self.config.max_concurrent_operations),
        }

        for resource, limit in self.config.max_concurrent_resources.items():
            self.semaphores[resource] = asyncio.Semaphore(limit)

        # 监控和检测
        self.stats = ConcurrencyStats()
        self.deadlock_detector = DeadlockDetector(self)
        self.starvation_detector = StarvationDetector(self)

        # 调度器
        self.scheduler = TaskScheduler(self)

        # 执行器
        self.executor = ThreadPoolExecutor(max_workers=(psutil.cpu_count() or 4) * 2)

        # 事件循环
        self.is_running = False
        self.monitor_task = None

    async def start(self):
        """启动并发控制器"""
        logger.info("启动细粒度并发控制器")
        self.is_running = True

        # 启动监控任务
        self.monitor_task = asyncio.create_task(self._monitor_system())

        # 启动调度器
        await self.scheduler.start()

    async def stop(self):
        """停止并发控制器"""
        logger.info("停止细粒度并发控制器")
        self.is_running = False

        # 取消监控任务
        if self.monitor_task:
            self.monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.monitor_task

        # 停止调度器
        await self.scheduler.stop()

        # 等待所有任务完成
        await self._wait_for_completion()

        # 关闭执行器
        self.executor.shutdown(wait=True)

    async def submit_task(
        self,
        task_func: Callable,
        *args,
        priority: Priority = Priority.NORMAL,
        resources: dict[str, float] | None = None,
        dependencies: list[str] | None = None,
        timeout: float | None = None,
        **kwargs,
    ) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())

        task = TaskRequest(
            task_id=task_id,
            task_func=task_func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            resource_requirements=resources or {},
            dependencies=dependencies or [],
            timeout=timeout,
        )

        # 添加依赖关系
        for dep_id in task.dependencies:
            self.task_dependencies[task_id].add(dep_id)

        # 添加到任务队列
        heapq.heappush(self.task_queue, (-priority.value, time.time(), task))
        self.stats.total_tasks += 1
        self.stats.queued_tasks += 1

        logger.debug(f"提交任务: {task_id}, 优先级: {priority.name}")
        return task_id

    async def acquire_lock(
        self,
        resource_id: str,
        lock_type: LockType = LockType.WRITE,
        owner_id: str | None = None,
        timeout: float | None = None,
    ) -> bool:
        """获取资源锁"""
        owner_id = owner_id or str(uuid.uuid4())
        timeout = timeout or self.config.deadlock_timeout

        async with asyncio.timeout(timeout):
            while True:
                # 检查是否可以获取锁
                if await self._can_acquire_lock(resource_id, lock_type, owner_id):
                    await self._grant_lock(resource_id, lock_type, owner_id)
                    return True

                # 检查死锁
                if self.config.enable_deadlock_detection:
                    if await self.deadlock_detector.detect_deadlock(owner_id):
                        logger.warning(f"检测到死锁,所有者: {owner_id}")
                        await self.deadlock_detector.resolve_deadlock(owner_id)
                        return False

                # 等待锁释放
                await asyncio.sleep(0.01)

    async def release_lock(self, resource_id: str, owner_id: str):
        """释放资源锁"""
        lock = self.lock_table.get(resource_id)
        if not lock:
            logger.warning(f"锁不存在: {resource_id}")
            return

        if lock.owner_id != owner_id and owner_id not in lock.shared_owners:
            logger.warning(f"无权释放锁: {resource_id}, 所有者: {owner_id}")
            return

        # 更新锁状态
        if lock.lock_type == LockType.READ:
            lock.shared_owners.discard(owner_id)
            if not lock.shared_owners:
                del self.lock_table[resource_id]
        else:
            del self.lock_table[resource_id]

        # 处理等待队列
        if lock.wait_queue:
            next_owner = lock.wait_queue.popleft()
            await self._grant_lock(resource_id, lock.lock_type, next_owner)

    async def _can_acquire_lock(self, resource_id: str, lock_type: LockType, owner_id: str) -> bool:
        """检查是否可以获取锁"""
        existing_lock = self.lock_table.get(resource_id)

        if not existing_lock:
            return True

        # 读锁兼容性
        if lock_type == LockType.READ:
            return existing_lock.lock_type == LockType.READ and existing_lock.owner_id != owner_id

        # 写锁需要等待
        return False

    async def _grant_lock(self, resource_id: str, lock_type: LockType, owner_id: str):
        """授予锁"""
        lock = ResourceLock(
            resource_id=resource_id,
            lock_type=lock_type,
            owner_id=owner_id,
            acquired_at=datetime.now(),
        )

        if lock_type == LockType.READ:
            lock.shared_owners.add(owner_id)

        self.lock_table[resource_id] = lock
        logger.debug(f"授予锁: {resource_id}, 类型: {lock_type.value}, 所有者: {owner_id}")

    @asynccontextmanager
    async def resource_lock(self, resource_id: str, lock_type: LockType = LockType.WRITE):
        """资源锁上下文管理器"""
        owner_id = str(uuid.uuid4())
        acquired = await self.acquire_lock(resource_id, lock_type, owner_id)

        if not acquired:
            raise RuntimeError(f"无法获取锁: {resource_id}")

        try:
            yield
        finally:
            await self.release_lock(resource_id, owner_id)

    async def execute_with_resources(
        self, task_func: Callable, *args, resources: dict[str, float] | None = None, **kwargs
    ) -> Any:
        """使用指定资源执行任务"""
        resources = resources or {}

        # 获取资源信号量
        semaphores = []
        for resource, _amount in resources.items():
            if resource in self.semaphores:
                semaphores.append(self.semaphores[resource])

        # 等待资源
        for semaphore in semaphores:
            await semaphore.acquire()

        try:
            # 执行任务
            if inspect.iscoroutinefunction(task_func):
                return await task_func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(self.executor, task_func, *args, **kwargs)
        finally:
            # 释放资源
            for semaphore in semaphores:
                semaphore.release()

    async def get_task_result(self, task_id: str, timeout: float | None = None) -> Any:
        """获取任务结果"""
        start_time = time.time()

        while task_id not in self.task_results:
            if timeout and (time.time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"任务超时: {task_id}")

            # 简单等待,让调度器有机会执行任务
            await asyncio.sleep(0.01)

        result = self.task_results[task_id]
        del self.task_results[task_id]
        return result

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 从队列中移除
        for i, (_, _, task) in enumerate(self.task_queue):
            if task.task_id == task_id:
                del self.task_queue[i]
                heapq.heapify(self.task_queue)
                self.stats.queued_tasks -= 1
                logger.info(f"取消队列中的任务: {task_id}")
                return True

        # 检查是否在执行
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if hasattr(task, "cancel"):
                task.cancel()
                logger.info(f"取消执行中的任务: {task_id}")
                return True

        return False

    async def _monitor_system(self):
        """监控系统状态"""
        while self.is_running:
            try:
                # 更新资源使用情况
                await self._update_resource_usage()

                # 检测死锁
                if self.config.enable_deadlock_detection:
                    await self.deadlock_detector.check_all_locks()

                # 检测饥饿
                if self.config.enable_starvation_detection:
                    await self.starvation_detector.check_starvation()

                # 更新统计
                self._update_statistics()

                # 动态调整
                await self._adjust_parameters()

                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"监控错误: {e}", exc_info=True)
                # 监控错误不应中断整个系统,记录后继续运行
                # 如果是关键错误(如系统资源耗尽),需要触发告警
                if "Resource" in str(type(e).__name__) or "Memory" in str(type(e).__name__):
                    # 资源相关错误,触发告警
                    logger.critical(f"资源告警: {e}")

    async def _update_resource_usage(self):
        """更新资源使用情况"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent()
        self.resource_usage["cpu"] = cpu_percent / 100.0

        # 内存使用率
        memory = psutil.virtual_memory()
        self.resource_usage["memory"] = memory.percent / 100.0

        # 任务并发度
        self.resource_usage["tasks"] = len(self.active_tasks)

        # 锁竞争
        self.stats.lock_contentions = sum(len(lock.wait_queue) for lock in self.lock_table.values())

    def _update_statistics(self) -> Any:
        """更新统计信息"""
        self.stats.active_tasks = len(self.active_tasks)
        self.stats.queued_tasks = len(self.task_queue)
        self.stats.resource_usage = dict(self.resource_usage)

        # 计算平均等待时间和执行时间
        if self.stats.completed_tasks > 0:
            total_wait = sum(t.wait_time for t in self.task_results.values())
            total_exec = sum(t.execution_time for t in self.task_results.values())

            self.stats.avg_wait_time = total_wait / self.stats.completed_tasks
            self.stats.avg_execution_time = total_exec / self.stats.completed_tasks

    async def _adjust_parameters(self):
        """动态调整参数"""
        # 基于负载调整并发限制
        if self.resource_usage.get("cpu", 0) > 0.9:
            # CPU高负载,减少并发
            new_limit = max(1, int(self.config.max_concurrent_tasks * 0.8))
            self.semaphores["task"] = asyncio.Semaphore(new_limit)
        elif self.resource_usage.get("cpu", 0) < 0.5:
            # CPU低负载,可以增加并发
            new_limit = min(200, int(self.config.max_concurrent_tasks * 1.2))
            self.semaphores["task"] = asyncio.Semaphore(new_limit)

    async def _wait_for_completion(self):
        """等待所有任务完成"""
        while self.active_tasks:
            await asyncio.sleep(0.1)

    def get_statistics(self) -> ConcurrencyStats:
        """获取统计信息"""
        return self.stats

    def get_lock_status(self) -> dict[str, Any]:
        """获取锁状态"""
        return {
            "total_locks": len(self.lock_table),
            "lock_types": {
                lock_type.value: sum(
                    1 for lock in self.lock_table.values() if lock.lock_type == lock_type
                )
                for lock_type in LockType
            },
            "waiting_requests": sum(len(lock.wait_queue) for lock in self.lock_table.values()),
        }


class DeadlockDetector:
    """死锁检测器"""

    def __init__(self, controller: FineGrainedConcurrencyController):
        self.controller = controller
        self.detection_interval = 5.0  # 检测间隔(秒)

    async def detect_deadlock(self, owner_id: str) -> bool:
        """检测特定所有者是否陷入死锁"""
        # 构建等待图
        wait_graph = self._build_wait_graph()

        # 检查环路
        return self._has_cycle(wait_graph, owner_id)

    async def check_all_locks(self):
        """检查所有锁的死锁情况"""
        owners = {lock.owner_id for lock in self.controller.lock_table.values()}
        owners.update(
            owner for lock in self.controller.lock_table.values() for owner in lock.shared_owners
        )

        for owner_id in owners:
            if await self.detect_deadlock(owner_id):
                logger.warning(f"检测到死锁: {owner_id}")
                await self.resolve_deadlock(owner_id)

    async def resolve_deadlock(self, owner_id: str):
        """解决死锁"""
        # 找到所有者的锁
        owned_locks = [
            lock
            for lock in self.controller.lock_table.values()
            if lock.owner_id == owner_id or owner_id in lock.shared_owners
        ]

        if not owned_locks:
            return

        # 选择牺牲者(持有锁最少的)
        victim_lock = min(owned_locks, key=lambda l: len(l.shared_owners))

        # 释放锁
        await self.controller.release_lock(victim_lock.resource_id, owner_id)

        self.controller.stats.deadlocks_detected += 1
        logger.info(f"解决死锁,释放锁: {victim_lock.resource_id}")

    def _build_wait_graph(self) -> dict[str, set[str]]:
        """构建等待图"""
        graph = defaultdict(set)

        for _resource_id, lock in self.controller.lock_table.items():
            # 等待该资源的所有者
            for waiter in lock.wait_queue:
                graph[waiter].add(lock.owner_id)
                for shared_owner in lock.shared_owners:
                    graph[waiter].add(shared_owner)

        return graph

    def _has_cycle(self, graph: dict[str, set[str]], start: str) -> bool:
        """检查图中是否有环路"""
        visited = set()
        stack = set()

        def dfs(node: str) -> bool:
            if node in stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            stack.add(node)

            for neighbor in graph.get(node, set()):
                if dfs(neighbor):
                    return True

            stack.remove(node)
            return False

        return dfs(start)


class StarvationDetector:
    """饥饿检测器"""

    def __init__(self, controller: FineGrainedConcurrencyController):
        self.controller = controller

    async def check_starvation(self):
        """检查任务饥饿"""
        current_time = datetime.now()
        starvation_timeout = timedelta(seconds=self.controller.config.starvation_timeout)

        # 检查任务队列中的任务
        for _, _task_time, task in self.controller.task_queue:
            wait_time = current_time - task.created_at
            if wait_time > starvation_timeout:
                logger.warning(f"检测到任务饥饿: {task.task_id}, 等待时间: {wait_time}")
                await self._resolve_starvation(task)
                self.controller.stats.starvations_detected += 1

    async def _resolve_starvation(self, task: TaskRequest):
        """解决饥饿问题"""
        # 提高任务优先级
        task.priority = Priority.HIGH

        # 重新插入队列
        heapq.heappush(self.controller.task_queue, (-task.priority.value, time.time(), task))


class TaskScheduler:
    """任务调度器"""

    def __init__(self, controller: FineGrainedConcurrencyController):
        self.controller = controller
        self.is_running = False
        self.scheduler_task = None

    async def start(self):
        """启动调度器"""
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._schedule_loop())

    async def stop(self):
        """停止调度器"""
        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.scheduler_task

    async def _schedule_loop(self):
        """调度循环"""
        while self.is_running:
            try:
                # 检查是否有可执行的任务
                if self.controller.task_queue:
                    # 获取最高优先级任务
                    _, _, task = heapq.heappop(self.controller.task_queue)

                    # 检查依赖
                    if await self._check_dependencies(task):
                        # 执行任务
                        await self._execute_task(task)
                    else:
                        # 依赖未满足,重新入队
                        heapq.heappush(
                            self.controller.task_queue, (-task.priority.value, time.time(), task)
                        )

                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"调度错误: {e}")

    async def _check_dependencies(self, task: TaskRequest) -> bool:
        """检查任务依赖是否满足"""
        return all(dep_id in self.controller.task_results for dep_id in task.dependencies)

    async def _execute_task(self, task: TaskRequest):
        """执行任务"""
        task_id = task.task_id
        start_time = time.time()

        # 计算等待时间
        task.wait_time = start_time - task.created_at.timestamp()

        # 添加到活动任务
        self.controller.active_tasks[task_id] = task
        self.controller.stats.queued_tasks -= 1

        try:
            # 获取任务信号量
            async with self.controller.semaphores["task"]:
                # 执行任务
                if task.timeout:
                    result = await asyncio.wait_for(
                        self.controller.execute_with_resources(
                            task.task_func,
                            *task.args,
                            **task.kwargs,
                            resources=task.resource_requirements,
                        ),
                        timeout=task.timeout,
                    )
                else:
                    result = await self.controller.execute_with_resources(
                        task.task_func,
                        *task.args,
                        **task.kwargs,
                        resources=task.resource_requirements,
                    )

                # 保存结果
                self.controller.task_results[task_id] = result
                self.controller.stats.completed_tasks += 1

        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, 错误: {e}")
            self.controller.task_results[task_id] = e
            self.controller.stats.failed_tasks += 1

        finally:
            # 计算执行时间
            task.execution_time = time.time() - start_time

            # 从活动任务中移除
            del self.controller.active_tasks[task_id]


# 创建全局细粒度并发控制器实例
fine_grained_concurrency_controller = FineGrainedConcurrencyController()


# 便捷函数
async def submit_concurrent_task(
    task_func: Callable,
    *args,
    priority: Priority = Priority.NORMAL,
    resources: dict[str, float] | None = None,
    **kwargs,
) -> str:
    """提交并发任务"""
    return await fine_grained_concurrency_controller.submit_task(
        task_func, *args, priority=priority, resources=resources, **kwargs
    )


async def get_concurrency_stats() -> dict[str, Any]:
    """获取并发统计信息"""
    stats = fine_grained_concurrency_controller.get_statistics()
    lock_status = fine_grained_concurrency_controller.get_lock_status()

    return {
        "task_stats": asdict(stats),
        "lock_status": lock_status,
        "resource_usage": stats.resource_usage,
    }
