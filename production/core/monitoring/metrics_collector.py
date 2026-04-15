#!/usr/bin/env python3
"""
性能监控和指标收集系统
Performance Monitoring and Metrics Collection System

版本: 1.0.0
功能:
- 统一的指标收集接口
- Prometheus导出格式
- 性能基准对比
- 实时监控面板数据
"""

from __future__ import annotations
import logging
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """指标数据点"""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram, summary


@dataclass
class PerformanceSnapshot:
    """性能快照"""

    timestamp: datetime = field(default_factory=datetime.now)
    total_requests: int = 0
    avg_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    error_rate: float = 0.0
    requests_per_second: float = 0.0


class MetricsCollector:
    """
    指标收集器

    功能:
    1. 收集计数、计时、直方图等指标
    2. 支持标签分组
    3. 提供Prometheus导出格式
    4. 计算百分位数和速率
    """

    def __init__(self, max_history: int = 1000):
        """
        初始化指标收集器

        Args:
            max_history: 保留的历史数据点数量
        """
        self.max_history = max_history

        # 指标存储
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._summaries: dict[str, list[float]] = defaultdict(list)

        # 元数据
        self._metric_descriptions: dict[str, str] = {}
        self._metric_labels: dict[str, dict[str, str]] = {}

        # 时间窗口
        self._time_windows = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
        }

        logger.info("✅ 指标收集器初始化完成")

    def inc_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None):
        """
        增加计数器

        Args:
            name: 指标名称
            value: 增量值
            labels: 标签
        """
        key = self._make_key(name, labels)
        self._counters[key] += value
        self._update_labels(key, labels)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None):
        """
        设置仪表值

        Args:
            name: 指标名称
            value: 设置值
            labels: 标签
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value
        self._update_labels(key, labels)

    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None):
        """
        观察直方图值

        Args:
            name: 指标名称
            value: 观察值
            labels: 标签
        """
        key = self._make_key(name, labels)
        self._histograms[key].append({"value": value, "timestamp": datetime.now()})
        self._update_labels(key, labels)

    def observe_summary(self, name: str, value: float, labels: dict[str, str] | None = None):
        """
        观察摘要值(用于计算统计量)

        Args:
            name: 指标名称
            value: 观察值
            labels: 标签
        """
        key = self._make_key(name, labels)
        self._summaries[key].append(value)
        # 限制数量
        if len(self._summaries[key]) > self.max_history:
            self._summaries[key] = self._summaries[key][-self.max_history :]
        self._update_labels(key, labels)

    def set_description(self, name: str, description: str):
        """设置指标描述"""
        self._metric_descriptions[name] = description

    def _make_key(self, name: str, labels: dict[str, str]) -> str:
        """生成带标签的键"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _update_labels(self, key: str, labels: dict[str, str]):
        """更新标签信息"""
        if labels:
            self._metric_labels[key] = labels

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        """获取计数器值"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float:
        """获取仪表值"""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_histogram_stats(
        self, name: str, labels: dict[str, str] | None = None
    ) -> dict[str, float]:
        """
        获取直方图统计

        Returns:
            包含 count, sum, min, max, avg, p50, p95, p99 的字典
        """
        key = self._make_key(name, labels)
        if key not in self._histograms:
            return {}

        values = [item["value"] for item in self._histograms[key]]
        if not values:
            return {}

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "sum": sum(sorted_values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": self._percentile(sorted_values, 50),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99),
        }

    def get_summary_stats(
        self, name: str, labels: dict[str, str] | None = None
    ) -> dict[str, float]:
        """获取摘要统计"""
        key = self._make_key(name, labels)
        if key not in self._summaries:
            return {}

        values = self._summaries[key]
        if not values:
            return {}

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "sum": sum(sorted_values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": self._percentile(sorted_values, 50),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99),
        }

    @staticmethod
    def _percentile(sorted_data: list[float], p: int) -> float:
        """计算百分位数"""
        k = (len(sorted_data) - 1) * p / 100
        f = int(k)
        c = k - f
        if f + 1 < len(sorted_data):
            return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
        return sorted_data[f]

    def get_rate(
        self, name: str, window: str = "1m", labels: dict[str, str] | None = None
    ) -> float:
        """
        计算速率(每秒)

        Args:
            name: 指标名称
            window: 时间窗口 (1m, 5m, 15m, 1h)
            labels: 标签

        Returns:
            每秒速率
        """
        key = self._make_key(name, labels)
        if key not in self._histograms:
            return 0.0

        window_delta = self._time_windows.get(window, timedelta(minutes=1))
        cutoff_time = datetime.now() - window_delta

        # 计算窗口内的数据点
        values_in_window = [
            item for item in self._histograms[key] if item["timestamp"] >= cutoff_time
        ]

        if not values_in_window:
            return 0.0

        # 速率 = 数量 / 时间窗口(秒)
        return len(values_in_window) / window_delta.total_seconds()

    def export_prometheus(self) -> str:
        """
        导出Prometheus格式文本

        Returns:
            Prometheus文本格式
        """
        lines = []

        # 导出计数器
        for key, value in self._counters.items():
            name = key.split("{")[0] if "{" in key else key
            lines.append(f"# TYPE {name} counter")
            if name in self._metric_descriptions:
                lines.append(f"# HELP {name} {self._metric_descriptions[name]}")
            lines.append(f"{key} {value}")

        # 导出仪表
        for key, value in self._gauges.items():
            name = key.split("{")[0] if "{" in key else key
            lines.append(f"# TYPE {name} gauge")
            if name in self._metric_descriptions:
                lines.append(f"# HELP {name} {self._metric_descriptions[name]}")
            lines.append(f"{key} {value}")

        # 导出直方图
        for key in self._histograms:
            name = key.split("{")[0] if "{" in key else key
            stats = self.get_histogram_stats(name, self._metric_labels.get(key))

            lines.append(f"# TYPE {name} histogram")
            if name in self._metric_descriptions:
                lines.append(f"# HELP {name} {self._metric_descriptions[name]}")

            lines.append(f"{key}_count {stats.get('count', 0)}")
            lines.append(f"{key}_sum {stats.get('sum', 0)}")
            lines.append(f"{key}_bucket{{le=\"+Inf\"}} {stats.get('count', 0)}")

        return "\n".join(lines)

    def export_json(self) -> dict[str, Any]:
        """
        导出JSON格式

        Returns:
            JSON可序列化的字典
        """
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                key: self.get_histogram_stats(
                    key.split("{")[0] if "{" in key else key, self._metric_labels.get(key)
                )
                for key in self._histograms
            },
            "summaries": {
                key: self.get_summary_stats(
                    key.split("{")[0] if "{" in key else key, self._metric_labels.get(key)
                )
                for key in self._summaries
            },
            "timestamp": datetime.now().isoformat(),
        }

    def reset(self):
        """重置所有指标"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._summaries.clear()
        logger.info("🗑️ 指标已重置")


# 全局单例
_metrics_collector: MetricsCollector | None = None
_collector_lock = threading.Lock()


def get_metrics_collector(max_history: int = 1000) -> MetricsCollector:
    """
    获取全局指标收集器实例

    Args:
        max_history: 保留的历史数据点数量

    Returns:
        MetricsCollector实例
    """
    global _metrics_collector

    with _collector_lock:
        if _metrics_collector is None:
            _metrics_collector = MetricsCollector(max_history=max_history)

        return _metrics_collector


def reset_metrics_collector():
    """重置全局指标收集器(用于测试)"""
    global _metrics_collector

    with _collector_lock:
        if _metrics_collector:
            _metrics_collector.reset()
        _metrics_collector = None


# 装饰器
def track_time(
    metric_name: str,
    labels: dict[str, str] | None = None,
    collector: MetricsCollector | None = None,
):
    """
    跟踪函数执行时间

    Args:
        metric_name: 指标名称
        labels: 标签
        collector: 指标收集器(None使用全局)

    Returns:
        装饰器
    """
    if collector is None:
        collector = get_metrics_collector()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                collector.observe_histogram(metric_name, elapsed_ms, labels)

        return wrapper

    return decorator


def track_counter(
    metric_name: str,
    labels: dict[str, str] | None = None,
    collector: MetricsCollector | None = None,
):
    """
    跟踪函数调用次数

    Args:
        metric_name: 指标名称
        labels: 标签
        collector: 指标收集器(None使用全局)

    Returns:
        装饰器
    """
    if collector is None:
        collector = get_metrics_collector()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector.inc_counter(metric_name, 1.0, labels)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def track_operation(
    name: str, labels: dict[str, str] | None = None, collector: MetricsCollector | None = None
):
    """
    跟踪操作的时间上下文管理器

    Args:
        name: 操作名称
        labels: 标签
        collector: 指标收集器

    Usage:
        with track_operation("database_query", {"table": "users"}):
            # 执行操作
            pass
    """
    if collector is None:
        collector = get_metrics_collector()

    start_time = time.time()
    try:
        yield
    finally:
        elapsed_ms = (time.time() - start_time) * 1000
        collector.observe_histogram(f"{name}_duration_ms", elapsed_ms, labels)
        collector.inc_counter(f"{name}_total", 1.0, labels)


class PerformanceMonitor:
    """
    性能监控器

    提供高级监控功能:
    1. 性能快照对比
    2. 基准测试
    3. 异常检测
    """

    def __init__(self, collector: MetricsCollector | None = None):
        """
        初始化性能监控器

        Args:
            collector: 指标收集器
        """
        self.collector = collector or get_metrics_collector()
        self.baselines: dict[str, float] = {}

    def take_snapshot(self, metric_name: str) -> PerformanceSnapshot:
        """
        获取性能快照

        Args:
            metric_name: 指标名称

        Returns:
            性能快照
        """
        stats = self.collector.get_histogram_stats(metric_name)

        return PerformanceSnapshot(
            total_requests=int(stats.get("count", 0)),
            avg_response_time_ms=stats.get("avg", 0.0),
            p50_response_time_ms=stats.get("p50", 0.0),
            p95_response_time_ms=stats.get("p95", 0.0),
            p99_response_time_ms=stats.get("p99", 0.0),
        )

    def set_baseline(self, metric_name: str, value: float):
        """设置基准值"""
        self.baselines[metric_name] = value

    def compare_to_baseline(self, metric_name: str) -> dict[str, Any]:
        """
        与基准对比

        Args:
            metric_name: 指标名称

        Returns:
            对比结果
        """
        if metric_name not in self.baselines:
            return {"error": f"No baseline set for {metric_name}"}

        stats = self.collector.get_histogram_stats(metric_name)
        current = stats.get("avg", 0.0)
        baseline = self.baselines[metric_name]

        change_pct = 0 if baseline == 0 else (current - baseline) / baseline * 100

        return {
            "metric": metric_name,
            "current": current,
            "baseline": baseline,
            "change": current - baseline,
            "change_percent": round(change_pct, 2),
            "status": "ok" if abs(change_pct) < 10 else "warning",
        }

    def detect_anomalies(
        self, metric_name: str, threshold_std: float = 2.0
    ) -> list[dict[str, Any]]:
        """
        检测异常值(基于标准差)

        Args:
            metric_name: 指标名称
            threshold_std: 标准差倍数阈值

        Returns:
            异常值列表
        """
        key = metric_name
        if key not in self.collector._histograms:
            return []

        values = [item["value"] for item in self.collector._histograms[key]]
        if len(values) < 10:
            return []

        import statistics

        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0

        if stdev == 0:
            return []

        anomalies = []
        upper_limit = mean + threshold_std * stdev
        lower_limit = mean - threshold_std * stdev

        for item in self.collector._histograms[key]:
            value = item["value"]
            if value > upper_limit or value < lower_limit:
                anomalies.append(
                    {
                        "value": value,
                        "timestamp": item["timestamp"].isoformat(),
                        "type": "high" if value > upper_limit else "low",
                        "deviation": round((value - mean) / stdev, 2) if stdev > 0 else 0,
                    }
                )

        return anomalies
