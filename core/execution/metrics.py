#!/usr/bin/env python3
from __future__ import annotations
"""
执行模块监控指标收集器
Execution Module Metrics Collector

收集和导出执行模块的Prometheus监控指标。

功能：
- 任务统计（总数、成功、失败、速率）
- 性能指标（执行时间、等待时间）
- 资源使用（内存、CPU、工作线程）
- 队列状态（大小、等待任务数）

作者: Athena AI系统
版本: 2.0.0
创建时间: 2026-01-27
"""

import asyncio
import logging
from datetime import datetime

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    start_http_server,
)
from prometheus_client.exposition import generate_latest

logger = logging.getLogger(__name__)


class ExecutionMetrics:
    """
    执行模块监控指标收集器

    提供标准的Prometheus指标收集和导出功能。
    """

    def __init__(self, registry: CollectorRegistry | None = None):
        """
        初始化指标收集器

        Args:
            registry: Prometheus注册表，默认使用全局注册表
        """
        self.registry = registry or REGISTRY

        # 任务计数器
        self._task_total = Counter(
            'athena_execution_tasks_total',
            'Total number of tasks',
            ['instance', 'priority', 'status'],
            registry=self.registry
        )

        self._task_created = Counter(
            'athena_execution_tasks_created_total',
            'Total number of tasks created',
            ['instance'],
            registry=self.registry
        )

        self._task_started = Counter(
            'athena_execution_tasks_started_total',
            'Total number of tasks started',
            ['instance', 'priority'],
            registry=self.registry
        )

        self._task_completed = Counter(
            'athena_execution_tasks_completed_total',
            'Total number of tasks completed successfully',
            ['instance', 'priority'],
            registry=self.registry
        )

        self._task_failed = Counter(
            'athena_execution_tasks_failed_total',
            'Total number of tasks failed',
            ['instance', 'priority', 'error_type'],
            registry=self.registry
        )

        self._task_retried = Counter(
            'athena_execution_tasks_retried_total',
            'Total number of task retries',
            ['instance', 'priority'],
            registry=self.registry
        )

        # 队列指标
        self._queue_size = Gauge(
            'athena_execution_queue_size',
            'Current number of tasks in the queue',
            ['instance', 'priority'],
            registry=self.registry
        )

        self._queue_max_size = Gauge(
            'athena_execution_queue_max_size',
            'Maximum queue size',
            ['instance'],
            registry=self.registry
        )

        self._queue_waiting = Gauge(
            'athena_execution_queue_waiting',
            'Number of tasks waiting in queue',
            ['instance'],
            registry=self.registry
        )

        # 工作线程指标
        self._workers_active = Gauge(
            'athena_execution_workers_active',
            'Number of active worker threads',
            ['instance'],
            registry=self.registry
        )

        self._workers_idle = Gauge(
            'athena_execution_workers_idle',
            'Number of idle worker threads',
            ['instance'],
            registry=self.registry
        )

        self._workers_max = Gauge(
            'athena_execution_workers_max',
            'Maximum number of worker threads',
            ['instance'],
            registry=self.registry
        )

        # 性能指标
        self._task_duration = Histogram(
            'athena_execution_task_duration_seconds',
            'Task execution duration in seconds',
            ['instance', 'priority'],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0),
            registry=self.registry
        )

        self._task_wait_time = Histogram(
            'athena_execution_task_wait_time_seconds',
            'Task wait time in queue before execution',
            ['instance', 'priority'],
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0),
            registry=self.registry
        )

        # 资源指标
        self._memory_usage = Gauge(
            'athena_execution_memory_usage_bytes',
            'Memory usage in bytes',
            ['instance'],
            registry=self.registry
        )

        self._memory_max = Gauge(
            'athena_execution_memory_max_bytes',
            'Maximum memory limit in bytes',
            ['instance'],
            registry=self.registry
        )

        self._cpu_time = Counter(
            'athena_execution_cpu_time_seconds_total',
            'Total CPU time in seconds',
            ['instance'],
            registry=self.registry
        )

        # 健康状态
        self._health_up = Gauge(
            'athena_execution_health_up',
            'Health check status (1=healthy, 0=unhealthy)',
            ['instance', 'check_name'],
            registry=self.registry
        )

        # 信息指标
        self._info = Info(
            'athena_execution',
            'Athena execution module information',
            registry=self.registry
        )

        # 实例信息
        self.instance_id: str = "unknown"
        self.start_time: datetime = datetime.now()

    def set_instance_info(self, instance_id: str, version: str = "2.0.0"):
        """
        设置实例信息

        Args:
            instance_id: 实例ID
            version: 版本号
        """
        self.instance_id = instance_id
        self._info.info({
            'instance_id': instance_id,
            'version': version,
            'start_time': self.start_time.isoformat(),
        })

    # ========== 任务计数 ==========

    def inc_task_created(self, instance: str = "default"):
        """任务创建计数"""
        self._task_created.labels(instance=instance).inc()
        self._task_total.labels(instance=instance, priority="all", status="created").inc()

    def inc_task_started(self, priority: str, instance: str = "default"):
        """任务开始计数"""
        self._task_started.labels(instance=instance, priority=priority).inc()
        self._task_total.labels(instance=instance, priority=priority, status="started").inc()

    def inc_task_completed(self, priority: str, duration: float, instance: str = "default"):
        """
        任务完成计数

        Args:
            priority: 任务优先级
            duration: 执行时长（秒）
            instance: 实例ID
        """
        self._task_completed.labels(instance=instance, priority=priority).inc()
        self._task_total.labels(instance=instance, priority=priority, status="completed").inc()
        self._task_duration.labels(instance=instance, priority=priority).observe(duration)

    def inc_task_failed(
        self,
        priority: str,
        error_type: str = "unknown",
        duration: Optional[float] = None,
        instance: str = "default"
    ):
        """
        任务失败计数

        Args:
            priority: 任务优先级
            error_type: 错误类型
            duration: 执行时长（秒），可选
            instance: 实例ID
        """
        self._task_failed.labels(
            instance=instance,
            priority=priority,
            error_type=error_type
        ).inc()
        self._task_total.labels(instance=instance, priority=priority, status="failed").inc()

        if duration is not None:
            self._task_duration.labels(instance=instance, priority=priority).observe(duration)

    def inc_task_retried(self, priority: str, instance: str = "default"):
        """任务重试计数"""
        self._task_retried.labels(instance=instance, priority=priority).inc()

    # ========== 队列指标 ==========

    def set_queue_size(self, size: int, priority: str = "all", instance: str = "default"):
        """设置队列大小"""
        self._queue_size.labels(instance=instance, priority=priority).set(size)

    def set_queue_max_size(self, max_size: int, instance: str = "default"):
        """设置队列最大容量"""
        self._queue_max_size.labels(instance=instance).set(max_size)

    def set_queue_waiting(self, count: int, instance: str = "default"):
        """设置等待中的任务数"""
        self._queue_waiting.labels(instance=instance).set(count)

    # ========== 工作线程指标 ==========

    def set_workers(self, active: int, idle: int, max_workers: int, instance: str = "default"):
        """
        设置工作线程数量

        Args:
            active: 活跃线程数
            idle: 空闲线程数
            max_workers: 最大线程数
            instance: 实例ID
        """
        self._workers_active.labels(instance=instance).set(active)
        self._workers_idle.labels(instance=instance).set(idle)
        self._workers_max.labels(instance=instance).set(max_workers)

    # ========== 性能指标 ==========

    def observe_task_duration(self, duration: float, priority: str, instance: str = "default"):
        """
        记录任务执行时长

        Args:
            duration: 执行时长（秒）
            priority: 任务优先级
            instance: 实例ID
        """
        self._task_duration.labels(instance=instance, priority=priority).observe(duration)

    def observe_task_wait_time(self, wait_time: float, priority: str, instance: str = "default"):
        """
        记录任务等待时间

        Args:
            wait_time: 等待时间（秒）
            priority: 任务优先级
            instance: 实例ID
        """
        self._task_wait_time.labels(instance=instance, priority=priority).observe(wait_time)

    # ========== 资源指标 ==========

    def set_memory_usage(self, usage_bytes: int, instance: str = "default"):
        """设置内存使用量"""
        self._memory_usage.labels(instance=instance).set(usage_bytes)

    def set_memory_max(self, max_bytes: int, instance: str = "default"):
        """设置内存上限"""
        self._memory_max.labels(instance=instance).set(max_bytes)

    def inc_cpu_time(self, seconds: float, instance: str = "default"):
        """增加CPU时间计数"""
        self._cpu_time.labels(instance=instance).inc(seconds)

    # ========== 健康状态 ==========

    def set_health_status(self, check_name: str, healthy: bool, instance: str = "default"):
        """
        设置健康检查状态

        Args:
            check_name: 检查项名称
            healthy: 是否健康
            instance: 实例ID
        """
        value = 1 if healthy else 0
        self._health_up.labels(instance=instance, check_name=check_name).set(value)

    # ========== 指标导出 ==========

    def export_metrics(self) -> bytes:
        """
        导出Prometheus格式的指标

        Returns:
            bytes: Prometheus文本格式的指标
        """
        return generate_latest(self.registry)

    def start_metrics_server(self, port: int = 9090):
        """
        启动Prometheus指标HTTP服务器

        Args:
            port: HTTP端口
        """
        logger.info(f"启动Prometheus指标服务器，端口: {port}")
        start_http_server(port, registry=self.registry)


class MetricsCollector:
    """
    指标收集器

    定期收集系统指标并更新到Prometheus。
    """

    def __init__(
        self,
        metrics: ExecutionMetrics,
        interval: int = 10,
        instance: str = "default"
    ):
        """
        初始化指标收集器

        Args:
            metrics: 指标对象
            interval: 收集间隔（秒）
            instance: 实例ID
        """
        self.metrics = metrics
        self.interval = interval
        self.instance = instance
        self.running = False
        self.task: asyncio.Task | None = None

    async def start(self):
        """启动指标收集"""
        if self.running:
            logger.warning("指标收集器已在运行")
            return

        self.running = True
        logger.info(f"启动指标收集器，间隔: {self.interval}秒")

        self.task = asyncio.create_task(self._collect_loop())

    async def stop(self):
        """停止指标收集"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("指标收集器已停止")

    async def _collect_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                await self._collect_metrics()
            except Exception as e:
                logger.error(f"指标收集失败: {e}")

            await asyncio.sleep(self.interval)

    async def _collect_metrics(self):
        """收集指标"""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # 内存使用
        memory_info = process.memory_info()
        self.metrics.set_memory_usage(memory_info.rss, instance=self.instance)

        # CPU时间
        cpu_times = process.cpu_times()
        self.metrics.inc_cpu_time(
            cpu_times.user + cpu_times.system,
            instance=self.instance
        )


# 全局指标实例
_global_metrics: ExecutionMetrics | None = None


def get_metrics() -> ExecutionMetrics:
    """
    获取全局指标实例

    Returns:
        ExecutionMetrics: 指标对象
    """
    global _global_metrics

    if _global_metrics is None:
        _global_metrics = ExecutionMetrics()

    return _global_metrics


def setup_metrics(
    instance_id: str,
    version: str = "2.0.0",
    metrics_port: Optional[int] = None
) -> ExecutionMetrics:
    """
    设置监控指标

    Args:
        instance_id: 实例ID
        version: 版本号
        metrics_port: Prometheus metrics端口，如果提供则启动HTTP服务器

    Returns:
        ExecutionMetrics: 指标对象
    """
    global _global_metrics

    if _global_metrics is None:
        _global_metrics = ExecutionMetrics()

    _global_metrics.set_instance_info(instance_id, version)

    if metrics_port:
        _global_metrics.start_metrics_server(metrics_port)

    logger.info(f"监控指标已设置，实例ID: {instance_id}")

    return _global_metrics


if __name__ == "__main__":
    # 测试指标收集
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 设置指标
        metrics = setup_metrics(
            instance_id="test_instance",
            metrics_port=9090
        )

        # 模拟指标更新
        metrics.inc_task_created("test")
        metrics.set_queue_size(100, "all", "test")
        metrics.set_queue_max_size(10000, "test")
        metrics.set_workers(10, 5, 20, "test")

        print("Prometheus metrics服务器已启动，端口: 9090")
        print("访问 http://localhost:9090 查看指标")

        # 保持运行
        asyncio.run(asyncio.sleep(3600))

    except KeyboardInterrupt:
        print("\n停止指标服务器")
        sys.exit(0)
