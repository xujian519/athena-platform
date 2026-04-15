#!/usr/bin/env python3
from __future__ import annotations
"""
通信模块监控指标
Communication Module Monitoring Metrics

提供Prometheus格式的监控指标收集和暴露

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Summary,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client未安装,监控功能将被禁用")

logger = logging.getLogger(__name__)


class CommunicationMetrics:
    """
    通信模块监控指标收集器

    收集以下类型的指标:
    - Counter: 计数器(单调递增)
    - Histogram: 直方图(分布统计)
    - Gauge: 仪表盘(可增可减)
    - Summary: 摘要(统计摘要)
    """

    def __init__(self, namespace: str = "athena_comm", subsystem: str = "communication"):
        """
        初始化监控指标收集器

        Args:
            namespace: 指标命名空间
            subsystem: 子系统名称
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus不可用,监控指标将被禁用")
            self._enabled = False
            return

        self._enabled = True
        self._namespace = namespace
        self._subsystem = subsystem

        # 消息指标
        self._init_message_metrics()

        # 连接池指标
        self._init_pool_metrics()

        # 性能指标
        self._init_performance_metrics()

        # 错误指标
        self._init_error_metrics()

        logger.info(f"📊 监控指标已初始化: {namespace}_{subsystem}")

    def _init_message_metrics(self) -> None:
        """初始化消息相关指标"""
        if not self._enabled:
            return

        # 消息发送总数
        self.message_sent_total = Counter(
            "message_sent_total",
            "发送消息总数",
            ["channel_type", "status"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 消息接收总数
        self.message_received_total = Counter(
            "message_received_total",
            "接收消息总数",
            ["channel_type"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 消息批处理总数
        self.message_batches_total = Counter(
            "message_batches_total",
            "批处理消息总数",
            ["status"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 当前队列大小
        self.message_queue_size = Gauge(
            "message_queue_size",
            "消息队列当前大小",
            ["receiver_id"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 批处理大小
        self.batch_size = Histogram(
            "batch_size",
            "批处理大小分布",
            buckets=[10, 50, 100, 500, 1000, 5000],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

    def _init_pool_metrics(self) -> None:
        """初始化连接池相关指标"""
        if not self._enabled:
            return

        # 连接获取总数
        self.connection_acquired_total = Counter(
            "connection_acquired_total",
            "从连接池获取连接总数",
            ["pool_name", "status"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 连接释放总数
        self.connection_released_total = Counter(
            "connection_released_total",
            "释放连接回连接池总数",
            ["pool_name"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 连接创建总数
        self.connection_created_total = Counter(
            "connection_created_total",
            "创建新连接总数",
            ["pool_name"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 当前活跃连接数
        self.active_connections = Gauge(
            "active_connections",
            "当前活跃连接数",
            ["pool_name"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 当前空闲连接数
        self.idle_connections = Gauge(
            "idle_connections",
            "当前空闲连接数",
            ["pool_name"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 连接等待时间
        self.connection_wait_time = Histogram(
            "connection_wait_seconds",
            "获取连接等待时间分布",
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 健康检查结果
        self.health_check_result = Counter(
            "health_check_total",
            "健康检查执行总数",
            ["pool_name", "result"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

    def _init_performance_metrics(self) -> None:
        """初始化性能相关指标"""
        if not self._enabled:
            return

        # 消息处理延迟
        self.message_processing_duration = Histogram(
            "message_processing_seconds",
            "消息处理时间分布",
            ["operation_type"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 批处理延迟
        self.batch_processing_duration = Histogram(
            "batch_processing_seconds",
            "批处理时间分布",
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 系统吞吐量
        self.throughput = Gauge(
            "messages_per_second",
            "系统吞吐量(消息/秒)",
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

    def _init_error_metrics(self) -> None:
        """初始化错误相关指标"""
        if not self._enabled:
            return

        # 错误总数
        self.errors_total = Counter(
            "errors_total",
            "错误总数",
            ["error_type", "component"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 验证失败总数
        self.validation_failures_total = Counter(
            "validation_failures_total",
            "输入验证失败总数",
            ["validation_type", "field"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 超时总数
        self.timeouts_total = Counter(
            "timeouts_total",
            "超时总数",
            ["operation_type"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

    # ========== 消息指标方法 ==========

    def record_message_sent(self, channel_type: str, status: str = "success") -> None:
        """记录发送消息"""
        if self._enabled:
            self.message_sent_total.labels(channel_type=channel_type, status=status).inc()

    def record_message_received(self, channel_type: str) -> None:
        """记录接收消息"""
        if self._enabled:
            self.message_received_total.labels(channel_type=channel_type).inc()

    def record_batch_processed(self, batch_size: int, status: str = "success") -> None:
        """记录批处理完成"""
        if self._enabled:
            self.message_batches_total.labels(status=status).inc()
            self.batch_size.observe(batch_size)

    def set_queue_size(self, receiver_id: str, size: int) -> None:
        """设置队列大小"""
        if self._enabled:
            self.message_queue_size.labels(receiver_id=receiver_id).set(size)

    # ========== 连接池指标方法 ==========
    async def record_connection_acquired(
        self, pool_name: str, wait_time: float | None = None, status: str = "success"
    ) -> None:
        """记录获取连接"""
        if self._enabled:
            self.connection_acquired_total.labels(pool_name=pool_name, status=status).inc()
            if wait_time is not None:
                self.connection_wait_time.observe(wait_time)

    def record_connection_released(self, pool_name: str) -> None:
        """记录释放连接"""
        if self._enabled:
            self.connection_released_total.labels(pool_name=pool_name).inc()

    def record_connection_created(self, pool_name: str) -> None:
        """记录创建连接"""
        if self._enabled:
            self.connection_created_total.labels(pool_name=pool_name).inc()

    def set_active_connections(self, pool_name: str, count: int) -> None:
        """设置活跃连接数"""
        if self._enabled:
            self.active_connections.labels(pool_name=pool_name).set(count)

    def set_idle_connections(self, pool_name: str, count: int) -> None:
        """设置空闲连接数"""
        if self._enabled:
            self.idle_connections.labels(pool_name=pool_name).set(count)

    def record_health_check(self, pool_name: str, success: bool) -> None:
        """记录健康检查结果"""
        if self._enabled:
            result = "success" if success else "failure"
            self.health_check_result.labels(pool_name=pool_name, result=result).inc()

    # ========== 性能指标方法 ==========

    @contextmanager
    def record_message_processing(self, operation_type: str):
        """记录消息处理时间上下文管理器"""
        if not self._enabled:
            yield
            return

        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.message_processing_duration.labels(operation_type=operation_type).observe(duration)

    @contextmanager
    def record_batch_processing(self):
        """记录批处理时间上下文管理器"""
        if not self._enabled:
            yield
            return

        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.batch_processing_duration.observe(duration)

    def set_throughput(self, messages_per_second: float) -> None:
        """设置系统吞吐量"""
        if self._enabled:
            self.throughput.set(messages_per_second)

    # ========== 错误指标方法 ==========

    def record_error(self, error_type: str, component: str) -> None:
        """记录错误"""
        if self._enabled:
            self.errors_total.labels(error_type=error_type, component=component).inc()

    def record_validation_failure(self, validation_type: str, field: str) -> None:
        """记录验证失败"""
        if self._enabled:
            self.validation_failures_total.labels(
                validation_type=validation_type, field=field
            ).inc()

    def record_timeout(self, operation_type: str) -> None:
        """记录超时"""
        if self._enabled:
            self.timeouts_total.labels(operation_type=operation_type).inc()

    # ========== 工具方法 ==========

    def is_enabled(self) -> bool:
        """检查监控是否启用"""
        return self._enabled

    def get_metrics_text(self) -> bytes:
        """
        获取Prometheus格式的指标文本

        Returns:
            bytes: Prometheus格式的指标数据
        """
        if not self._enabled:
            return b""

        return generate_latest()

    @staticmethod
    def get_content_type() -> str:
        """
        获取指标内容的MIME类型

        Returns:
            str: MIME类型
        """
        if not PROMETHEUS_AVAILABLE:
            return "text/plain"

        return CONTENT_TYPE_LATEST


# 全局指标实例
_metrics_instance: CommunicationMetrics | None = None


def get_metrics() -> CommunicationMetrics:
    """
    获取全局指标实例

    Returns:
        CommunicationMetrics: 全局指标实例
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = CommunicationMetrics()
    return _metrics_instance


def init_metrics(
    namespace: str = "athena_comm", subsystem: str = "communication"
) -> CommunicationMetrics:
    """
    初始化全局指标实例

    Args:
        namespace: 指标命名空间
        subsystem: 子系统名称

    Returns:
        CommunicationMetrics: 指标实例
    """
    global _metrics_instance
    _metrics_instance = CommunicationMetrics(namespace, subsystem)
    return _metrics_instance


# ========== 装饰器 ==========


def track_message_processing(operation_type: str):
    """
    跟踪消息处理时间的装饰器

    用法:
        @track_message_processing("send_message")
        async def send_message(...):
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics()
            with metrics.record_message_processing(operation_type):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics()
            with metrics.record_message_processing(operation_type):
                return func(*args, **kwargs)

        # 检测函数是否为协程函数
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_errors(component: str, error_type: str = "unknown"):
    """
    跟踪错误的装饰器

    用法:
        @track_errors("communication_engine", "connection_error")
        async def connect_to_server(...):
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception:
                metrics = get_metrics()
                metrics.record_error(error_type, component)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                metrics = get_metrics()
                metrics.record_error(error_type, component)
                raise

        # 检测函数是否为协程函数
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 导出
__all__ = [
    "PROMETHEUS_AVAILABLE",
    "CommunicationMetrics",
    "get_metrics",
    "init_metrics",
    "track_errors",
    "track_message_processing",
]
