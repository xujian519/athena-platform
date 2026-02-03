#!/usr/bin/env python3
"""
Athena通信系统 - 性能指标收集
Performance Metrics for Communication System

实现通信性能指标收集功能。

主要功能:
1. 消息统计
2. 性能指标收集
3. 连接统计
4. 队列统计
5. 指标导出

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """
    通信性能指标
    """

    # 消息统计
    total_messages: int = 0
    sent_messages: int = 0
    received_messages: int = 0
    failed_messages: int = 0
    timed_out_messages: int = 0

    # 性能指标
    avg_send_time: float = 0.0
    avg_receive_time: float = 0.0
    avg_processing_time: float = 0.0

    # 百分位数
    p95_processing_time: float = 0.0
    p99_processing_time: float = 0.0

    # 连接统计
    active_connections: int = 0
    peak_connections: int = 0
    total_connections: int = 0

    # 队列统计
    queue_size: int = 0
    peak_queue_size: int = 0
    dropped_messages: int = 0

    # 时间窗口
    window_start: datetime = field(default_factory=datetime.now)
    window_end: datetime | None = None

    # 内部统计(用于计算百分位数)
    _processing_times: deque = field(default_factory=lambda: deque(maxlen=1000))

    def record_send(self, duration: float) -> Any:
        """记录发送时间"""
        self.sent_messages += 1
        self.total_messages += 1
        # 指数移动平均
        self.avg_send_time = 0.9 * self.avg_send_time + 0.1 * duration

    def record_receive(self, duration: float) -> Any:
        """记录接收时间"""
        self.received_messages += 1
        self.total_messages += 1
        self.avg_receive_time = 0.9 * self.avg_receive_time + 0.1 * duration

    def record_processing(self, duration: float) -> Any:
        """记录处理时间"""
        self.total_messages += 1
        self.avg_processing_time = 0.9 * self.avg_processing_time + 0.1 * duration

        # 记录用于百分位数计算
        self._processing_times.append(duration)

        # 更新百分位数
        if len(self._processing_times) >= 100:
            sorted_times = sorted(self._processing_times)
            self.p95_processing_time = sorted_times[int(len(sorted_times) * 0.95)]
            self.p99_processing_time = sorted_times[int(len(sorted_times) * 0.99)]

    def record_failure(self, reason: str = "unknown") -> Any:
        """记录失败"""
        self.failed_messages += 1
        if reason == "timeout":
            self.timed_out_messages += 1

    def record_connection(self, active: bool) -> Any:
        """记录连接"""
        if active:
            self.active_connections += 1
            self.total_connections += 1
            if self.active_connections > self.peak_connections:
                self.peak_connections = self.active_connections
        else:
            self.active_connections = max(0, self.active_connections - 1)

    def update_queue_size(self, size: int) -> None:
        """更新队列大小"""
        self.queue_size = size
        if size > self.peak_queue_size:
            self.peak_queue_size = size

    def record_dropped(self, count: int = 1) -> Any:
        """记录丢弃的消息"""
        self.dropped_messages += count

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_messages == 0:
            return 1.0
        successful = self.total_messages - self.failed_messages
        return successful / self.total_messages

    def get_throughput(self) -> float:
        """获取吞吐量(消息/秒)"""
        if self.window_end:
            duration = (self.window_end - self.window_start).total_seconds()
        else:
            duration = (datetime.now() - self.window_start).total_seconds()

        if duration > 0:
            return self.total_messages / duration
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_messages": self.total_messages,
            "sent_messages": self.sent_messages,
            "received_messages": self.received_messages,
            "failed_messages": self.failed_messages,
            "timed_out_messages": self.timed_out_messages,
            "success_rate": self.get_success_rate(),
            "avg_send_time": self.avg_send_time,
            "avg_receive_time": self.avg_receive_time,
            "avg_processing_time": self.avg_processing_time,
            "p95_processing_time": self.p95_processing_time,
            "p99_processing_time": self.p99_processing_time,
            "active_connections": self.active_connections,
            "peak_connections": self.peak_connections,
            "total_connections": self.total_connections,
            "queue_size": self.queue_size,
            "peak_queue_size": self.peak_queue_size,
            "dropped_messages": self.dropped_messages,
            "throughput": self.get_throughput(),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat() if self.window_end else None,
        }

    def reset_window(self) -> Any:
        """重置统计窗口"""
        self.window_start = datetime.now()
        self.window_end = None
        self.total_messages = 0
        self.sent_messages = 0
        self.received_messages = 0
        self.failed_messages = 0
        self.timed_out_messages = 0
        self._processing_times.clear()

        logger.debug("性能指标窗口已重置")

    def export_prometheus(self) -> str:
        """
        导出Prometheus格式指标

        Returns:
            Prometheus格式的指标字符串
        """
        lines = []

        # 消息统计
        lines.append("# HELP communication_messages_total Total number of messages")
        lines.append("# TYPE communication_messages_total counter")
        lines.append(f"communication_messages_total {self.total_messages}")

        lines.append("# HELP communication_sent_messages_total Total number of sent messages")
        lines.append("# TYPE communication_sent_messages_total counter")
        lines.append(f"communication_sent_messages_total {self.sent_messages}")

        lines.append("# HELP communication_failed_messages_total Total number of failed messages")
        lines.append("# TYPE communication_failed_messages_total counter")
        lines.append(f"communication_failed_messages_total {self.failed_messages}")

        # 性能指标
        lines.append("# HELP communication_send_time_seconds Average send time in seconds")
        lines.append("# TYPE communication_send_time_seconds gauge")
        lines.append(f"communication_send_time_seconds {self.avg_send_time:.4f}")

        lines.append(
            "# HELP communication_processing_time_seconds Average processing time in seconds"
        )
        lines.append("# TYPE communication_processing_time_seconds gauge")
        lines.append(f"communication_processing_time_seconds {self.avg_processing_time:.4f}")

        # 连接统计
        lines.append(
            "# HELP communication_active_connections Current number of active connections"
        )
        lines.append("# TYPE communication_active_connections gauge")
        lines.append(f"communication_active_connections {self.active_connections}")

        return "\n".join(lines)


class MetricsCollector:
    """
    指标收集器

    自动收集和聚合性能指标。
    """

    def __init__(self, window_size: int = 60):
        """
        初始化指标收集器

        Args:
            window_size: 时间窗口大小(秒)
        """
        self.window_size = window_size
        self.metrics = PerformanceMetrics()
        self._is_running = False

    def start(self) -> None:
        """启动指标收集"""
        self._is_running = True
        self.metrics.window_start = datetime.now()
        logger.info("指标收集器已启动")

    def stop(self) -> None:
        """停止指标收集"""
        self._is_running = False
        self.metrics.window_end = datetime.now()
        logger.info("指标收集器已停止")

    def get_metrics(self) -> PerformanceMetrics:
        """获取当前指标"""
        return self.metrics

    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式指标"""
        return self.metrics.export_prometheus()

    def reset(self) -> Any:
        """重置指标"""
        self.metrics.reset_window()

    def is_running(self) -> bool:
        """检查是否在运行"""
        return self._is_running


# =============================================================================
# 便捷函数
# =============================================================================


def create_collector(window_size: int = 60) -> MetricsCollector:
    """创建指标收集器"""
    return MetricsCollector(window_size)


_default_collector: MetricsCollector | None = None


def get_default_collector() -> MetricsCollector:
    """获取默认指标收集器"""
    global _default_collector
    if _default_collector is None:
        _default_collector = MetricsCollector()
        _default_collector.start()
    return _default_collector


# =============================================================================
# 导出
# =============================================================================

# 为保持兼容性，提供 MetricsAPI 作为别名
MetricsAPI = MetricsCollector

__all__ = [
    "MetricsCollector",
    "MetricsAPI",  # 别名
    "PerformanceMetrics",
    "create_collector",
    "get_default_collector",
]
