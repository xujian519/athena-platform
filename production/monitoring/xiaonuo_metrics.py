#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺Prometheus指标收集器
Xiaonuo Prometheus Metrics Collector

提供生产级指标收集：
- 请求指标
- 任务指标
- 性能指标
- 资源指标
- 业务指标

作者: Athena团队
创建时间: 2026-02-09
版本: v1.0.0
"""

import time
import psutil
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Summary,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("警告: prometheus_client未安装，指标收集将被禁用")


# =============================================================================
# 指标定义
# =============================================================================

if PROMETHEUS_AVAILABLE:
    # 请求指标
    request_count = Counter(
        'xiaonuo_requests_total',
        '请求总数',
        ['method', 'endpoint', 'status']
    )

    request_duration = Histogram(
        'xiaonuo_request_duration_seconds',
        '请求处理时间',
        ['method', 'endpoint']
    )

    request_errors = Counter(
        'xiaonuo_request_errors_total',
        '请求错误总数',
        ['method', 'endpoint', 'error_type']
    )

    # 任务指标
    task_count = Counter(
        'xiaonuo_tasks_total',
        '任务总数',
        ['task_type', 'status']
    )

    task_duration = Histogram(
        'xiaonuo_task_duration_seconds',
        '任务执行时间',
        ['task_type']
    )

    task_queue_size = Gauge(
        'xiaonuo_task_queue_size',
        '任务队列大小',
        ['queue_name']
    )

    # 性能指标
    response_time = Summary(
        'xiaonuo_response_time_seconds',
        '响应时间'
    )

    memory_usage = Gauge(
        'xiaonuo_memory_usage_bytes',
        '内存使用量',
        ['type']
    )

    cpu_usage = Gauge(
        'xiaonuo_cpu_usage_percent',
        'CPU使用率'
    )

    # 协作指标
    collaboration_requests = Counter(
        'xiaonuo_collaboration_requests_total',
        '协作请求总数',
        ['agent', 'action']
    )

    collaboration_duration = Histogram(
        'xiaonuo_collaboration_duration_seconds',
        '协作请求处理时间',
        ['agent']
    )

    # 业务指标
    coordination_count = Counter(
        'xiaonuo_coordination_total',
        '协调操作总数',
        ['operation', 'result']
    )

    memory_operations = Counter(
        'xiaonuo_memory_operations_total',
        '记忆操作总数',
        ['operation', 'memory_type']
    )

    # 系统指标
    uptime = Gauge(
        'xiaonuo_uptime_seconds',
        '服务运行时间'
    )

    active_connections = Gauge(
        'xiaonuo_active_connections',
        '活跃连接数'
    )

else:
    # 如果Prometheus不可用，创建空函数
    def _noop(*args, **kwargs):
        pass

    request_count = request_duration = request_errors = _noop
    task_count = task_duration = task_queue_size = _noop
    response_time = memory_usage = cpu_usage = _noop
    collaboration_requests = collaboration_duration = _noop
    coordination_count = memory_operations = _noop
    uptime = active_connections = _noop


# =============================================================================
# 指标收集器类
# =============================================================================

class XiaonuoMetricsCollector:
    """小诺指标收集器"""

    def __init__(self, enabled: bool = True):
        """
        初始化指标收集器

        参数:
            enabled: 是否启用指标收集
        """
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        self.start_time = time.time()

        if self.enabled:
            self._init_metrics()

    def _init_metrics(self):
        """初始化指标"""
        # 设置运行时间
        uptime.set(0)

    def update_uptime(self):
        """更新运行时间"""
        if self.enabled:
            uptime.set(time.time() - self.start_time)

    def update_resource_usage(self):
        """更新资源使用情况"""
        if not self.enabled:
            return

        process = psutil.Process()

        # 内存使用
        mem_info = process.memory_info()
        memory_usage.labels(type='rss').set(mem_info.rss)
        memory_usage.labels(type='vms').set(mem_info.vms)

        # CPU使用
        cpu_usage.set(process.cpu_percent())

    def record_request(self, method: str, endpoint: str, status: str, duration: float):
        """
        记录请求

        参数:
            method: HTTP方法
            endpoint: 端点路径
            status: 状态码
            duration: 处理时间
        """
        if self.enabled:
            request_count.labels(method=method, endpoint=endpoint, status=status).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_request_error(self, method: str, endpoint: str, error_type: str):
        """
        记录请求错误

        参数:
            method: HTTP方法
            endpoint: 端点路径
            error_type: 错误类型
        """
        if self.enabled:
            request_errors.labels(method=method, endpoint=endpoint, error_type=error_type).inc()

    def record_task(self, task_type: str, status: str, duration: float):
        """
        记录任务

        参数:
            task_type: 任务类型
            status: 任务状态
            duration: 执行时间
        """
        if self.enabled:
            task_count.labels(task_type=task_type, status=status).inc()
            task_duration.labels(task_type=task_type).observe(duration)

    def update_task_queue_size(self, queue_name: str, size: int):
        """
        更新任务队列大小

        参数:
            queue_name: 队列名称
            size: 队列大小
        """
        if self.enabled:
            task_queue_size.labels(queue_name=queue_name).set(size)

    def record_collaboration(self, agent: str, action: str, duration: float):
        """
        记录协作请求

        参数:
            agent: 协作智能体名称
            action: 操作类型
            duration: 处理时间
        """
        if self.enabled:
            collaboration_requests.labels(agent=agent, action=action).inc()
            collaboration_duration.labels(agent=agent).observe(duration)

    def record_coordination(self, operation: str, result: str):
        """
        记录协调操作

        参数:
            operation: 操作类型
            result: 操作结果
        """
        if self.enabled:
            coordination_count.labels(operation=operation, result=result).inc()

    def record_memory_operation(self, operation: str, memory_type: str):
        """
        记录记忆操作

        参数:
            operation: 操作类型
            memory_type: 记忆类型
        """
        if self.enabled:
            memory_operations.labels(operation=operation, memory_type=memory_type).inc()

    def update_active_connections(self, count: int):
        """
        更新活跃连接数

        参数:
            count: 连接数
        """
        if self.enabled:
            active_connections.set(count)

    def get_metrics(self) -> bytes:
        """
        获取Prometheus格式的指标

        返回:
            bytes: Prometheus格式的指标数据
        """
        if not self.enabled:
            return b""

        # 更新运行时间和资源使用
        self.update_uptime()
        self.update_resource_usage()

        # 生成指标
        return generate_latest()


# =============================================================================
# 装饰器
# =============================================================================

def track_request(metric_collector: XiaonuoMetricsCollector):
    """
    请求追踪装饰器

    参数:
        metric_collector: 指标收集器实例
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not metric_collector.enabled:
                return await func(*args, **kwargs)

            start_time = time.time()
            method = kwargs.get('method', 'unknown')
            endpoint = kwargs.get('endpoint', func.__name__)

            try:
                result = await func(*args, **kwargs)
                status = 'success'
                return result
            except Exception as e:
                status = 'error'
                error_type = type(e).__name__
                metric_collector.record_request_error(method, endpoint, error_type)
                raise
            finally:
                duration = time.time() - start_time
                metric_collector.record_request(method, endpoint, status, duration)

        return wrapper
    return decorator


def track_task(metric_collector: XiaonuoMetricsCollector, task_type: str):
    """
    任务追踪装饰器

    参数:
        metric_collector: 指标收集器实例
        task_type: 任务类型
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not metric_collector.enabled:
                return await func(*args, **kwargs)

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                status = 'completed'
                return result
            except Exception as e:
                status = 'failed'
                raise
            finally:
                duration = time.time() - start_time
                metric_collector.record_task(task_type, status, duration)

        return wrapper
    return decorator


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 创建指标收集器
    collector = XiaonuoMetricsCollector()

    # 模拟记录一些指标
    collector.record_request("GET", "/api/v1/status", "200", 0.1)
    collector.record_task("coordination", "completed", 1.5)
    collector.record_collaboration("xiaona", "analyze", 2.0)
    collector.record_coordination("schedule", "success")

    # 获取指标
    metrics = collector.get_metrics()
    print(f"Content-Type: {CONTENT_TYPE_LATEST}")
    print(metrics.decode())
