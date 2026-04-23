#!/usr/bin/env python3

"""
感知模块性能监控
Perception Module Performance Monitoring

提供实时性能监控、指标收集和性能分析功能。

作者: Athena AI系统
创建时间: 2026-01-24
版本: 1.0.0
"""

import asyncio
import contextlib
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    # 请求统计
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    requests_in_progress: int = 0

    # 延迟统计 (秒)
    average_latency: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    min_latency: float = float("inf")
    max_latency: float = 0.0

    # 吞吐量统计
    throughput_per_second: float = 0.0
    throughput_per_minute: float = 0.0

    # 资源使用
    cache_hit_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # 时间窗口
    window_start: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """
    性能监控器

    负责收集、分析和报告感知模块的性能指标。
    """

    def __init__(
        self, window_size: int = 1000, update_interval: float = 1.0, enable_alerts: bool = True
    ):
        """
        初始化性能监控器

        Args:
            window_size: 滑动窗口大小(请求数)
            update_interval: 更新间隔(秒)
            enable_alerts: 是否启用告警
        """
        self.window_size = window_size
        self.update_interval = update_interval
        self.enable_alerts = enable_alerts

        # 滑动窗口数据
        self.latencies = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        self.success_flags = deque(maxlen=window_size)

        # 性能指标
        self.metrics = PerformanceMetrics()

        # 告警配置
        self.alert_thresholds = {
            "p95_latency": 5.0,  # P95延迟超过5秒告警
            "error_rate": 0.05,  # 错误率超过5%告警
            "memory_usage": 0.8,  # 内存使用超过80%告警
        }

        # 监控状态
        self.is_monitoring = False
        self._monitor_task = None

        logger.info("📊 性能监控器初始化完成")

    async def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.metrics.window_start = datetime.now()
        self._monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info("📊 性能监控已启动")

    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task

        logger.info("📊 性能监控已停止")

    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                self._update_metrics()
                await self._check_alerts()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")

    def record_request(self, latency: float, success: bool, metadata: Optional[dict[str, Any]] = None):
        """
        记录请求

        Args:
            latency: 请求延迟(秒)
            success: 是否成功
            metadata: 元数据
        """
        now = datetime.now()

        self.latencies.append(latency)
        self.timestamps.append(now)
        self.success_flags.append(success)

        # 更新基本计数
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        self.metrics.last_update = now

        # 定期更新完整指标
        if self.metrics.total_requests % 100 == 0:
            self._update_metrics()

    def _update_metrics(self):
        """更新性能指标"""
        if not self.latencies:
            return

        latencies = list(self.latencies)
        sorted_latencies = sorted(latencies)

        # 延迟统计
        self.metrics.average_latency = sum(latencies) / len(latencies)
        self.metrics.p50_latency = sorted_latencies[int(len(sorted_latencies) * 0.5)]
        self.metrics.p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        self.metrics.p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        self.metrics.min_latency = min(latencies)
        self.metrics.max_latency = max(latencies)

        # 吞吐量计算
        elapsed = (datetime.now() - self.metrics.window_start).total_seconds()
        if elapsed > 0:
            self.metrics.throughput_per_second = self.metrics.total_requests / elapsed
            self.metrics.throughput_per_minute = self.metrics.total_requests / (elapsed / 60)

    async def _check_alerts(self):
        """检查告警条件"""
        if not self.enable_alerts:
            return

        alerts = []

        # 检查P95延迟
        if self.metrics.p95_latency > self.alert_thresholds["p95_latency"]:
            alerts.append(
                {
                    "type": "high_latency",
                    "severity": "warning",
                    "message": f"P95延迟过高: {self.metrics.p95_latency:.2f}s",
                    "value": self.metrics.p95_latency,
                    "threshold": self.alert_thresholds["p95_latency"],
                }
            )

        # 检查错误率
        if self.metrics.total_requests > 0:
            error_rate = self.metrics.failed_requests / self.metrics.total_requests
            if error_rate > self.alert_thresholds["error_rate"]:
                alerts.append(
                    {
                        "type": "high_error_rate",
                        "severity": "critical",
                        "message": f"错误率过高: {error_rate:.2%}",
                        "value": error_rate,
                        "threshold": self.alert_thresholds["error_rate"],
                    }
                )

        # 发送告警
        for alert in alerts:
            await self._send_alert(alert)

    async def _send_alert(self, alert: dict[str, Any]):
        """发送告警"""
        logger.warning(f"⚠️ 性能告警: {alert['message']}")

    def get_metrics(self) -> dict[str, Any]:
        """获取当前性能指标"""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / max(self.metrics.total_requests, 1)
            ),
            "error_rate": (self.metrics.failed_requests / max(self.metrics.total_requests, 1)),
            "latency": {
                "average": self.metrics.average_latency * 1000,  # 转换为毫秒
                "p50": self.metrics.p50_latency * 1000,
                "p95": self.metrics.p95_latency * 1000,
                "p99": self.metrics.p99_latency * 1000,
                "min": (
                    self.metrics.min_latency * 1000
                    if self.metrics.min_latency != float("inf")
                    else 0
                ),
                "max": self.metrics.max_latency * 1000,
            },
            "throughput": {
                "per_second": self.metrics.throughput_per_second,
                "per_minute": self.metrics.throughput_per_minute,
            },
            "resources": {
                "cache_hit_rate": self.metrics.cache_hit_rate,
                "memory_usage_mb": self.metrics.memory_usage_mb,
                "cpu_usage_percent": self.metrics.cpu_usage_percent,
            },
            "window": {
                "start": self.metrics.window_start.isoformat(),
                "last_update": self.metrics.last_update.isoformat(),
                "size": len(self.latencies),
            },
        }

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        return {
            "summary": {
                "total_time": (datetime.now() - self.metrics.window_start).total_seconds(),
                "total_requests": self.metrics.total_requests,
                "average_latency_ms": self.metrics.average_latency * 1000,
                "p95_latency_ms": self.metrics.p95_latency * 1000,
                "throughput_rps": self.metrics.throughput_per_second,
                "error_rate": self.metrics.failed_requests / max(self.metrics.total_requests, 1),
            },
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 延迟建议
        if self.metrics.p95_latency > 3.0:
            recommendations.append("考虑启用缓存以降低P95延迟")

        if self.metrics.p95_latency > 5.0:
            recommendations.append("考虑增加并发处理能力")

        # 错误率建议
        if self.metrics.total_requests > 0:
            error_rate = self.metrics.failed_requests / self.metrics.total_requests
            if error_rate > 0.05:
                recommendations.append("错误率过高,建议检查日志并修复常见错误")

        # 吞吐量建议
        if self.metrics.throughput_per_second < 10:
            recommendations.append("吞吐量较低,考虑优化处理流程")

        return recommendations


class PerformanceTracker:
    """性能追踪器(上下文管理器)"""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
        self.metadata = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency = time.time() - self.start_time
        success = exc_type is None

        self.monitor.record_request(
            latency,
            success,
            {"operation": self.operation_name, "error": str(exc_val) if exc_val else None},
        )


def track_performance(monitor: PerformanceMonitor, operation_name: str):
    """性能追踪装饰器"""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            with PerformanceTracker(monitor, operation_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


# 全局性能监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


# 导出
__all__ = [
    "PerformanceMetrics",
    "PerformanceMonitor",
    "PerformanceTracker",
    "get_global_monitor",
    "track_performance",
]

