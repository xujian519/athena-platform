#!/usr/bin/env python3
from __future__ import annotations
"""
通信模块增强监控
Enhanced Communication Monitoring

为持久化和WebSocket模块添加Prometheus监控指标。

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import logging
import time
from collections.abc import Callable
from functools import wraps

try:
    from prometheus_client import Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client未安装,增强监控将被禁用")

from core.communication.monitoring import CommunicationMetrics

logger = logging.getLogger(__name__)


class EnhancedCommunicationMetrics(CommunicationMetrics):
    """
    增强的通信模块监控指标

    扩展基础指标，添加持久化和WebSocket监控。
    """

    def __init__(self, namespace: str = "athena_comm", subsystem: str = "communication"):
        """初始化增强监控指标"""
        super().__init__(namespace, subsystem)

        if not PROMETHEUS_AVAILABLE:
            return

        # 持久化指标
        self._init_persistence_metrics()

        # WebSocket指标
        self._init_websocket_metrics()

        logger.info(f"📊 增强监控指标已初始化: {namespace}_{subsystem}")

    def _init_persistence_metrics(self) -> None:
        """初始化持久化相关指标"""
        if not PROMETHEUS_AVAILABLE:
            return

        # 持久化操作计数
        self.persistence_operations_total = Counter(
            "persistence_operations_total",
            "持久化操作总数",
            ["operation", "backend_type", "status"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 持久化操作延迟
        self.persistence_operation_duration = Histogram(
            "persistence_operation_seconds",
            "持久化操作延迟分布",
            ["operation", "backend_type"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 持久化队列大小
        self.persistence_queue_size = Gauge(
            "persistence_queue_size",
            "持久化队列大小",
            ["state"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 死信队列大小
        self.dead_letter_queue_size = Gauge(
            "dead_letter_queue_size",
            "死信队列大小",
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 消息重试计数
        self.message_retries_total = Counter(
            "message_retries_total",
            "消息重试总数",
            ["backend_type"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 消息恢复计数
        self.messages_recovered_total = Counter(
            "messages_recovered_total",
            "恢复的消息总数",
            ["recovery_type"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

    def _init_websocket_metrics(self) -> None:
        """初始化WebSocket相关指标"""
        if not PROMETHEUS_AVAILABLE:
            return

        # WebSocket连接计数
        self.websocket_connections_total = Counter(
            "websocket_connections_total",
            "WebSocket连接总数",
            ["status"],  # established, closed, rejected
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # 当前活跃WebSocket连接
        self.websocket_active_connections = Gauge(
            "websocket_active_connections",
            "当前活跃WebSocket连接数",
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # WebSocket消息计数
        self.websocket_messages_total = Counter(
            "websocket_messages_total",
            "WebSocket消息总数",
            ["message_type", "direction"],  # direction: sent, received
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # WebSocket消息延迟
        self.websocket_message_duration = Histogram(
            "websocket_message_seconds",
            "WebSocket消息处理延迟",
            ["message_type"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # WebSocket频道订阅计数
        self.websocket_channel_subscriptions = Gauge(
            "websocket_channel_subscriptions",
            "WebSocket频道订阅数",
            ["channel"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

        # WebSocket广播计数
        self.websocket_broadcasts_total = Counter(
            "websocket_broadcasts_total",
            "WebSocket广播总数",
            ["status"],
            namespace=self._namespace,
            subsystem=self._subsystem,
        )

    # ========== 持久化指标方法 ==========

    def record_persistence_operation(
        self,
        operation: str,
        backend_type: str,
        status: str = "success",
        duration: float | None = None,
    ) -> None:
        """
        记录持久化操作

        Args:
            operation: 操作类型（save, get, update, delete等）
            backend_type: 后端类型（redis, file, memory）
            status: 操作状态
            duration: 操作耗时（秒）
        """
        if not PROMETHEUS_AVAILABLE:
            return

        self.persistence_operations_total.labels(
            operation=operation, backend_type=backend_type, status=status
        ).inc()

        if duration is not None:
            self.persistence_operation_duration.labels(
                operation=operation, backend_type=backend_type
            ).observe(duration)

    def set_persistence_queue_size(self, state: str, size: int) -> None:
        """设置持久化队列大小"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.persistence_queue_size.labels(state=state).set(size)

    def set_dead_letter_queue_size(self, size: int) -> None:
        """设置死信队列大小"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.dead_letter_queue_size.set(size)

    def record_message_retry(self, backend_type: str) -> None:
        """记录消息重试"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.message_retries_total.labels(backend_type=backend_type).inc()

    def record_messages_recovered(self, recovery_type: str, count: int) -> None:
        """记录消息恢复"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.messages_recovered_total.labels(recovery_type=recovery_type).inc(count)

    # ========== WebSocket指标方法 ==========

    def record_websocket_connection(self, status: str) -> None:
        """
        记录WebSocket连接

        Args:
            status: 连接状态（established, closed, rejected）
        """
        if not PROMETHEUS_AVAILABLE:
            return

        self.websocket_connections_total.labels(status=status).inc()

        if status == "established":
            self.websocket_active_connections.inc()
        elif status in ("closed", "rejected"):
            self.websocket_active_connections.dec()

    def record_websocket_message(
        self, message_type: str, direction: str, duration: float | None = None
    ) -> None:
        """
        记录WebSocket消息

        Args:
            message_type: 消息类型
            direction: 方向（sent, received）
            duration: 处理耗时（秒）
        """
        if not PROMETHEUS_AVAILABLE:
            return

        self.websocket_messages_total.labels(
            message_type=message_type, direction=direction
        ).inc()

        if duration is not None:
            self.websocket_message_duration.labels(message_type=message_type).observe(
                duration
            )

    def set_websocket_channel_subscriptions(self, channel: str, count: int) -> None:
        """设置WebSocket频道订阅数"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.websocket_channel_subscriptions.labels(channel=channel).set(count)

    def record_websocket_broadcast(self, status: str = "success") -> None:
        """记录WebSocket广播"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.websocket_broadcasts_total.labels(status=status).inc()


# 全局增强指标实例
_enhanced_metrics_instance: EnhancedCommunicationMetrics | None = None


def get_enhanced_metrics() -> EnhancedCommunicationMetrics:
    """
    获取全局增强指标实例

    Returns:
        EnhancedCommunicationMetrics: 全局增强指标实例
    """
    global _enhanced_metrics_instance
    if _enhanced_metrics_instance is None:
        _enhanced_metrics_instance = EnhancedCommunicationMetrics()
    return _enhanced_metrics_instance


# ========== 装饰器 ==========


def track_persistence_operation(operation: str, backend_type: str = "unknown"):
    """
    跟踪持久化操作的装饰器

    用法:
        @track_persistence_operation("save", "redis")
        async def save_message(...):
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_enhanced_metrics()
            start = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start
                metrics.record_persistence_operation(operation, backend_type, status, duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_enhanced_metrics()
            start = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start
                metrics.record_persistence_operation(operation, backend_type, status, duration)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_websocket_message(message_type: str, direction: str = "sent"):
    """
    跟踪WebSocket消息的装饰器

    Args:
        message_type: 消息类型
        direction: 方向（sent, received）

    用法:
        @track_websocket_message("broadcast", "sent")
        async def broadcast_message(...):
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_enhanced_metrics()
            start = time.time()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metrics.record_websocket_message(message_type, direction, duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_enhanced_metrics()
            start = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metrics.record_websocket_message(message_type, direction, duration)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


__all__ = [
    "PROMETHEUS_AVAILABLE",
    "EnhancedCommunicationMetrics",
    "CommunicationMonitor",  # 别名
    "CommunicationMetrics",  # 别名
    "MetricsCollector",  # 便捷函数
    "get_enhanced_metrics",
    "get_monitor",  # 便捷函数
    "track_persistence_operation",
    "track_websocket_message",
]


# =============================================================================
# === 别名和便捷函数 ===
# =============================================================================

# 为保持兼容性，提供 CommunicationMonitor 作为别名
CommunicationMonitor = EnhancedCommunicationMetrics

# 为保持兼容性，提供 CommunicationMetrics 作为别名
CommunicationMetrics = EnhancedCommunicationMetrics


def get_monitor(
    namespace: str = "athena_comm",
    subsystem: str = "communication",
) -> EnhancedCommunicationMetrics:
    """
    获取或创建监控指标实例

    Args:
        namespace: Prometheus 命名空间
        subsystem: 子系统名称

    Returns:
        EnhancedCommunicationMetrics 实例
    """
    return get_enhanced_metrics(namespace, subsystem)


# 为保持兼容性，提供 MetricsCollector 作为函数
MetricsCollector = get_monitor
