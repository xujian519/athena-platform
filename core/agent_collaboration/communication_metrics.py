#!/usr/bin/env python3
from __future__ import annotations
"""
Agent通信系统Prometheus监控指标
Communication Metrics for Prometheus

提供完整的通信系统监控:
1. 消息发送/接收计数
2. 消息处理延迟
3. 错误率和成功率
4. 队列深度和消费者健康度
5. 系统资源使用

版本: v1.0.0
创建时间: 2026-01-18
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 指标定义
# =============================================================================


class CommunicationMetrics:
    """
    通信系统监控指标

    覆盖所有关键通信操作的性能和状态
    """

    # 消息计数器
    message_sent_total = Counter(
        "agent_message_sent_total",
        "发送消息总数",
        ["agent_id", "message_type", "channel", "status"],
        registry=CollectorRegistry(),
    )

    message_received_total = Counter(
        "agent_message_received_total",
        "接收消息总数",
        ["agent_id", "message_type", "channel"],
        registry=CollectorRegistry(),
    )

    message_confirmed_total = Counter(
        "agent_message_confirmed_total",
        "确认消息总数",
        ["agent_id", "channel"],
        registry=CollectorRegistry(),
    )

    message_failed_total = Counter(
        "agent_message_failed_total",
        "失败消息总数",
        ["agent_id", "message_type", "failure_reason"],
        registry=CollectorRegistry(),
    )

    # 延迟指标
    message_processing_duration = Histogram(
        "agent_message_processing_duration_seconds",
        "消息处理耗时(秒)",
        ["agent_id", "message_type", "operation"],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=CollectorRegistry(),
    )

    message_queue_latency = Histogram(
        "agent_message_queue_latency_seconds",
        "消息队列延迟(秒)",
        ["channel"],
        buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
        registry=CollectorRegistry(),
    )

    # 队列状态
    queue_depth = Gauge(
        "agent_message_queue_depth",
        "消息队列深度",
        ["channel", "queue_type"],
        registry=CollectorRegistry(),
    )

    pending_messages = Gauge(
        "agent_pending_messages", "待处理消息数", ["agent_id"], registry=CollectorRegistry()
    )

    # 消费者状态
    consumer_health = Gauge(
        "agent_consumer_health",
        "消费者健康度(0-1)",
        ["agent_id", "consumer_id"],
        registry=CollectorRegistry(),
    )

    consumer_message_count = Gauge(
        "agent_consumer_message_count",
        "消费者处理消息数",
        ["agent_id", "consumer_id"],
        registry=CollectorRegistry(),
    )

    consumer_error_rate = Gauge(
        "agent_consumer_error_rate",
        "消费者错误率(0-1)",
        ["agent_id", "consumer_id"],
        registry=CollectorRegistry(),
    )

    # 系统资源
    active_connections = Gauge(
        "agent_active_connections", "活跃连接数", ["connection_type"], registry=CollectorRegistry()
    )

    buffer_usage = Gauge(
        "agent_buffer_usage_bytes",
        "缓冲区使用量(字节)",
        ["buffer_type"],
        registry=CollectorRegistry(),
    )

    # 协调器指标
    coordinator_task_duration = Summary(
        "agent_coordinator_task_duration_seconds",
        "协调器任务处理耗时",
        ["task_type", "workflow_type"],
        registry=CollectorRegistry(),
    )

    coordinator_queue_size = Gauge(
        "agent_coordinator_queue_size", "协调器任务队列大小", registry=CollectorRegistry()
    )

    coordinator_active_tasks = Gauge(
        "agent_coordinator_active_tasks", "协调器活跃任务数", registry=CollectorRegistry()
    )


# =============================================================================
# 指标收集器装饰器
# =============================================================================


def track_message_send(agent_id: str = "unknown") -> Any:
    """追踪消息发送"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)

                # 提取参数
                message = kwargs.get("message") or (args[0] if args else None)
                channel = kwargs.get("channel", "main")

                if message:
                    message_type = type(message).__name__
                    CommunicationMetrics.message_sent_total.labels(
                        agent_id=agent_id, message_type=message_type, channel=channel, status=status
                    ).inc()

                    # 记录处理时间
                    duration = time.time() - start_time
                    CommunicationMetrics.message_processing_duration.labels(
                        agent_id=agent_id, message_type=message_type, operation="send"
                    ).observe(duration)

                return result

            except Exception as e:
                status = "failed"
                logger.error(f"消息发送失败: {e}")

                # 记录失败
                message = kwargs.get("message") or (args[0] if args else None)
                if message:
                    message_type = type(message).__name__
                    CommunicationMetrics.message_sent_total.labels(
                        agent_id=agent_id,
                        message_type=message_type,
                        channel=kwargs.get("channel", "main"),
                        status=status,
                    ).inc()

                    CommunicationMetrics.message_failed_total.labels(
                        agent_id=agent_id,
                        message_type=message_type,
                        failure_reason=type(e).__name__,
                    ).inc()

                raise

        return wrapper

    return decorator


def track_message_receive(agent_id: str = "unknown") -> Any:
    """追踪消息接收"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # 记录接收
                channel = kwargs.get("channel", "main")
                if isinstance(result, list):
                    for msg in result:
                        if hasattr(msg, "envelope"):
                            message_type = msg.envelope.message_type
                            CommunicationMetrics.message_received_total.labels(
                                agent_id=agent_id, message_type=message_type, channel=channel
                            ).inc()

                # 记录处理时间
                duration = time.time() - start_time
                CommunicationMetrics.message_processing_duration.labels(
                    agent_id=agent_id, message_type="receive", operation="receive"
                ).observe(duration)

                return result

            except Exception as e:
                logger.error(f"消息接收失败: {e}")
                raise

        return wrapper

    return decorator


def track_message_confirm(agent_id: str = "unknown") -> Any:
    """追踪消息确认"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = await func(*args, **kwargs)

                if result:
                    channel = kwargs.get("channel", "main")
                    CommunicationMetrics.message_confirmed_total.labels(
                        agent_id=agent_id, channel=channel
                    ).inc()

                return result

            except Exception as e:
                logger.error(f"消息确认失败: {e}")
                raise

        return wrapper

    return decorator


# =============================================================================
# 指标报告器
# =============================================================================


class MetricsReporter:
    """
    Prometheus指标报告器

    收集和格式化所有通信系统指标
    """

    def __init__(self):
        self.metrics = CommunicationMetrics

    def update_queue_metrics(
        self, channel: str, queue_depth: int, pending_count: int, buffer_size: int
    ):
        """更新队列指标"""
        self.metrics.queue_depth.labels(channel=channel, queue_type="main").set(queue_depth)

        self.metrics.queue_depth.labels(channel=channel, queue_type="pending").set(pending_count)

        self.metrics.buffer_usage.labels(buffer_type="queue").set(buffer_size)

    def update_consumer_metrics(
        self,
        agent_id: str,
        consumer_id: str,
        health_score: float,
        message_count: int,
        error_count: int,
        total_messages: int,
    ):
        """更新消费者指标"""
        self.metrics.consumer_health.labels(agent_id=agent_id, consumer_id=consumer_id).set(
            health_score
        )

        self.metrics.consumer_message_count.labels(agent_id=agent_id, consumer_id=consumer_id).set(
            message_count
        )

        if total_messages > 0:
            error_rate = error_count / total_messages
            self.metrics.consumer_error_rate.labels(agent_id=agent_id, consumer_id=consumer_id).set(
                error_rate
            )

    def update_coordinator_metrics(self, queue_size: int, active_tasks: int):
        """更新协调器指标"""
        self.metrics.coordinator_queue_size.set(queue_size)
        self.metrics.coordinator_active_tasks.set(active_tasks)

    def export_metrics(self) -> bytes:
        """导出Prometheus格式的指标"""
        return generate_latest(self.metrics.message_sent_total.registry)  # type: ignore[attr-defined]

    def get_text_metrics(self) -> str:
        """获取文本格式的指标"""
        return self.export_metrics().decode("utf-8")


# =============================================================================
# 健康检查
# =============================================================================


class CommunicationHealthChecker:
    """
    通信系统健康检查器

    监控通信系统整体健康状态
    """

    def __init__(self, metrics: type[CommunicationMetrics]):  # type: ignore[assignment]
        self.metrics = metrics
        self.health_thresholds = {
            "max_error_rate": 0.05,  # 5%错误率
            "max_queue_depth": 10000,  # 最大队列深度
            "min_health_score": 0.7,  # 最低健康分
            "max_latency_p99": 5.0,  # P99延迟(秒)
        }

    def check_health(self) -> dict[str, Any]:
        """
        执行健康检查

        Returns:
            Dict: 健康状态报告
        """
        health_status: dict[str, Any] = {
            "status": "healthy",
            "checks": [],
            "timestamp": time.time(),
        }

        # 检查1: 错误率
        total_sent = self.metrics.message_sent_total._value.get((), 0)  # type: ignore[attr-defined, call-arg]
        total_failed = self.metrics.message_failed_total._value.get((), 0)  # type: ignore[attr-defined, call-arg]

        if total_sent > 0:
            error_rate = total_failed / total_sent  # type: ignore[unknown-variable-type]
            check = {
                "name": "error_rate",
                "status": (
                    "pass" if error_rate < self.health_thresholds["max_error_rate"] else "fail"
                ),
                "value": error_rate,
                "threshold": self.health_thresholds["max_error_rate"],
            }
            health_status["checks"].append(check)  # type: ignore[attr-defined]

            if check["status"] == "fail":
                health_status["status"] = "unhealthy"

        # 检查2: 队列深度
        # 这里需要从实际队列获取数据
        # 简化示例

        # 检查3: 消费者健康度
        # 从Gauge获取当前值

        # 检查4: 延迟
        # 从Histogram获取P99延迟

        return health_status


# =============================================================================
# 全局实例
# =============================================================================

_metrics_reporter: MetricsReporter | None = None
_health_checker: CommunicationHealthChecker | None = None


def get_metrics_reporter() -> MetricsReporter:
    """获取指标报告器实例"""
    global _metrics_reporter
    if _metrics_reporter is None:
        _metrics_reporter = MetricsReporter()
    return _metrics_reporter


def get_health_checker() -> CommunicationHealthChecker:
    """获取健康检查器实例"""
    global _health_checker
    if _health_checker is None:
        _health_checker = CommunicationHealthChecker(CommunicationMetrics)
    return _health_checker
