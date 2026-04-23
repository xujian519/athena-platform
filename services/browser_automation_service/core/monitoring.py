#!/usr/bin/env python3
"""
监控模块
Monitoring Module for Browser Automation Service

提供性能指标收集、健康检查、分布式追踪等功能

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import asyncio
import time
from collections import defaultdict
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Metric:
    """指标数据类"""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """性能统计数据"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration: float = 0
    min_duration: float = float("inf")
    max_duration: float = 0

    @property
    def avg_duration(self) -> float:
        """平均持续时间"""
        if self.total_requests == 0:
            return 0
        return self.total_duration / self.total_requests

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """错误率"""
        return 100 - self.success_rate

    def update(self, duration: float, success: bool) -> None:
        """更新统计"""
        self.total_requests += 1
        self.total_duration += duration
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_metrics: int = 10000):
        """
        初始化指标收集器

        Args:
            max_metrics: 最大指标数量
        """
        self._metrics: list[Metric] = []
        self._max_metrics = max_metrics
        self._counters: defaultdict[str, int] = defaultdict(int)
        self._gauges: defaultdict[str, float] = defaultdict(float)
        self._histograms: defaultdict[str, list[float] = defaultdict(list)

    def add_metric(self, metric: Metric) -> None:
        """添加指标"""
        self._metrics.append(metric)

        # 限制内存使用
        if len(self._metrics) > self._max_metrics:
            self._metrics = self._metrics[-self._max_metrics // 2:]

    def increment(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """增加计数器"""
        key = self._make_key(name, tags)
        self._counters[key] += value

    def set_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """设置仪表"""
        key = self._make_key(name, tags)
        self._gauges[key] = value

    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """记录直方图"""
        key = self._make_key(name, tags)
        self._histograms[key].append(value)

        # 限制样本数量
        if len(self._histograms[key]) > 1000:
            self._histograms[key] = self._histograms[key][-500:]

    def _make_key(self, name: str, tags: dict[str, str] | None) -> str:
        """生成指标键"""
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{name}@{tag_str}"
        return name

    def get_counter(self, name: str, tags: dict[str, str] | None = None) -> int:
        """获取计数器值"""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0)

    def get_gauge(self, name: str, tags: dict[str, str] | None = None) -> float:
        """获取仪表值"""
        key = self._make_key(name, tags)
        return self._gauges.get(key, 0)

    def get_histogram_stats(
        self,
        name: str,
        tags: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """获取直方图统计"""
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])

        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """获取所有指标"""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self._histograms.keys()
            },
            "recent_metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "tags": m.tags,
                }
                for m in self._metrics[-100:]
            ],
        }


class TracingManager:
    """追踪管理器"""

    def __init__(self):
        """初始化追踪管理器"""
        self._spans: dict[str, dict] = {}
        self._current_span: str | None = None

    @asynccontextmanager
    async def span(
        self,
        operation_name: str,
        parent_span_id: str | None = None,
        tags: dict[str, Any] | None = None,
    ):
        """
        创建追踪span

        Args:
            operation_name: 操作名称
            parent_span_id: 父span ID
            tags: 标签

        Yields:
            str: span ID
        """
        import uuid

        span_id = f"SPAN-{uuid.uuid4().hex[:16]}"
        start_time = time.monotonic()

        span_data = {
            "span_id": span_id,
            "operation": operation_name,
            "parent_id": parent_span_id,
            "start_time": start_time,
            "tags": tags or {},
            "status": "started",
        }

        self._spans[span_id] = span_data
        parent = self._current_span
        self._current_span = span_id

        try:
            yield span_id

            span_data["status"] = "success"
            span_data["duration_ms"] = (time.monotonic() - start_time) * 1000

        except Exception as e:
            span_data["status"] = "error"
            span_data["error"] = str(e)
            span_data["duration_ms"] = (time.monotonic() - start_time) * 1000
            raise

        finally:
            self._current_span = parent

    def get_span(self, span_id: str) -> dict | None:
        """获取span数据"""
        return self._spans.get(span_id)

    def get_current_span(self) -> str | None:
        """获取当前span ID"""
        return self._current_span

    def get_all_spans(self) -> list[dict]:
        """获取所有spans"""
        return list(self._spans.values())

    def clear_spans(self) -> None:
        """清除所有spans"""
        self._spans.clear()


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        """初始化性能监控器"""
        self.metrics = MetricsCollector()
        self.stats = defaultdict(lambda: PerformanceStats())
        self.tracing = TracingManager()

    @asynccontextmanager
    async def monitor(
        self,
        operation: str,
        tags: dict[str, str] | None = None,
    ):
        """
        监控操作性能

        Args:
            operation: 操作名称
            tags: 标签

        Yields:
            None
        """
        start_time = time.monotonic()
        success = True

        self.metrics.increment(
            f"{operation}.started",
            tags=tags,
        )

        try:
            yield

        except Exception as e:
            success = False
            self.metrics.increment(
                f"{operation}.errors",
                tags={**(tags or {}), "error_type": type(e).__name__},
            )
            raise

        finally:
            duration = time.monotonic() - start_time

            # 更新统计
            self.stats[operation].update(duration, success)

            # 记录指标
            self.metrics.add_metric(
                Metric(
                    name=f"{operation}.duration",
                    value=duration * 1000,  # 转换为毫秒
                    tags=tags or {},
                )
            )

            self.metrics.record_histogram(
                f"{operation}.duration",
                duration * 1000,
                tags=tags,
            )

            if success:
                self.metrics.increment(f"{operation}.success", tags=tags)
            else:
                self.metrics.increment(f"{operation}.failure", tags=tags)

    def get_stats(self, operation: str) -> dict[str, Any]:
        """获取操作统计"""
        stats = self.stats[operation]
        return {
            "total_requests": stats.total_requests,
            "successful_requests": stats.successful_requests,
            "failed_requests": stats.failed_requests,
            "avg_duration_ms": stats.avg_duration * 1000,
            "min_duration_ms": stats.min_duration * 1000
            if stats.min_duration != float("inf")
            else 0,
            "max_duration_ms": stats.max_duration * 1000,
            "success_rate": stats.success_rate,
            "error_rate": stats.error_rate,
        }

    def get_all_stats(self) -> dict[str, Any]:
        """获取所有统计"""
        return {
            "operations": {
                op: self.get_stats(op) for op in self.stats.keys()
            },
            "metrics": self.metrics.get_all_metrics(),
            "spans": self.tracing.get_all_spans(),
        }


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        """初始化健康检查器"""
        self._checks: dict[str, Callable] = {}
        self._last_check_time: float = 0
        self._last_check_results: dict[str, Any] = {}

    def register_check(
        self,
        name: str,
        check_func: Callable,
    ) -> None:
        """
        注册健康检查

        Args:
            name: 检查名称
            check_func: 检查函数（返回bool或tuple[bool, str]）
        """
        self._checks[name] = check_func

    async def check_health(self) -> dict[str, Any]:
        """
        执行健康检查

        Returns:
            dict: 健康状态
        """
        self._last_check_time = time.monotonic()
        results = {}

        all_healthy = True

        for name, check_func in self._checks.items():
            try:
                result = check_func()
                if asyncio.iscoroutine(result):
                    result = await result

                if isinstance(result, tuple):
                    healthy, message = result
                else:
                    healthy = bool(result)
                    message = "OK" if healthy else "Failed"

                results[name] = {
                    "healthy": healthy,
                    "message": message,
                }

                if not healthy:
                    all_healthy = False

            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "message": f"检查失败: {e}",
                }
                all_healthy = False

        self._last_check_results = results

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_last_check(self) -> dict[str, Any]:
        """获取最后一次检查结果"""
        return {
            "results": self._last_check_results,
            "time_since_last_check": time.monotonic() - self._last_check_time,
        }


# 全局实例
_performance_monitor: PerformanceMonitor | None = None
_health_checker: HealthChecker | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_health_checker() -> HealthChecker:
    """获取全局健康检查器"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


# 导出
__all__ = [
    "Metric",
    "PerformanceStats",
    "MetricsCollector",
    "TracingManager",
    "PerformanceMonitor",
    "HealthChecker",
    "get_performance_monitor",
    "get_health_checker",
]
