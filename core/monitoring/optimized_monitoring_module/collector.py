#!/usr/bin/env python3
from __future__ import annotations
"""
优化版监控告警模块 - 指标收集器
Optimized Monitoring and Alerting Module - Metrics Collector

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import statistics
import threading
from collections import defaultdict, deque
from datetime import datetime
from typing import Any

import numpy as np

from .types import MetricType, MetricValue


class MetricsCollector:
    """指标收集器

    负责收集、存储和检索各种类型的指标。
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """初始化指标收集器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = defaultdict(float)
        self.histograms: dict[str, list[float]] = defaultdict(list)
        self.timers: dict[str, list[float]] = defaultdict(list)
        self.lock = threading.RLock()

        # 收集器配置
        self.collection_interval = self.config.get("collection_interval", 10)
        self.retention_period = self.config.get("retention_period", 3600)  # 1小时

    def record_counter(self, name: str, value: float = 1, labels: dict[str, str] | None = None) -> Any:
        """记录计数器

        Args:
            name: 指标名称
            value: 增量值(默认1)
            labels: 标签字典
        """
        with self.lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
            self._add_to_metrics(name, self.counters[key], labels, MetricType.COUNTER)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """设置仪表盘值

        Args:
            name: 指标名称
            value: 指标值
            labels: 标签字典
        """
        with self.lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
            self._add_to_metrics(name, value, labels, MetricType.GAUGE)

    def record_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> Any:
        """记录直方图

        Args:
            name: 指标名称
            value: 指标值
            labels: 标签字典
        """
        with self.lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(value)
            # 保留最近1000个值
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
            self._add_to_metrics(name, value, labels, MetricType.HISTOGRAM)

    def record_timer(self, name: str, duration: float, labels: dict[str, str] | None = None) -> Any:
        """记录计时器

        Args:
            name: 指标名称
            duration: 持续时间(秒)
            labels: 标签字典
        """
        with self.lock:
            key = self._make_key(name, labels)
            self.timers[key].append(duration)
            # 保留最近1000个值
            if len(self.timers[key]) > 1000:
                self.timers[key] = self.timers[key][-1000:]
            self._add_to_metrics(name, duration, labels, MetricType.TIMER)

    def get_metric(self, name: str, labels: dict[str, str] | None = None) -> MetricValue | None:
        """获取最新指标值

        Args:
            name: 指标名称
            labels: 标签字典

        Returns:
            最新的指标值,如果不存在返回None
        """
        with self.lock:
            key = self._make_key(name, labels)
            if self.metrics.get(key):
                return self.metrics[key][-1]
            return None

    def get_metrics_history(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[MetricValue]:
        """获取指标历史

        Args:
            name: 指标名称
            labels: 标签字典
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            指标历史列表
        """
        with self.lock:
            key = self._make_key(name, labels)
            if key not in self.metrics:
                return []

            history = list(self.metrics[key])

            # 时间过滤
            if start_time:
                history = [m for m in history if m.timestamp >= start_time]
            if end_time:
                history = [m for m in history if m.timestamp <= end_time]

            return history

    def get_metric_stats(self, name: str, labels: dict[str, str] | None = None) -> dict[str, float]:
        """获取指标统计信息

        Args:
            name: 指标名称
            labels: 标签字典

        Returns:
            统计信息字典
        """
        with self.lock:
            key = self._make_key(name, labels)

            if self.timers.get(key):
                values = self.timers[key]
                return {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "p95": np.percentile(values, 95),
                    "p99": np.percentile(values, 99),
                }
            elif self.histograms.get(key):
                values = self.histograms[key]
                return {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "sum": sum(values),
                }
            elif key in self.gauges:
                return {"value": self.gauges[key]}
            elif key in self.counters:
                return {"value": self.counters[key]}
            else:
                return {}

    def _make_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        """生成指标键

        Args:
            name: 指标名称
            labels: 标签字典

        Returns:
            唯一的键字符串
        """
        if not labels:
            return name
        label_str = ",".join([f"{k}={v}" for k, v in sorted(labels.items())])
        return f"{name}[{label_str}]"

    def _add_to_metrics(
        self, name: str, value: float, labels: dict[str, str], metric_type: MetricType
    ) -> Any:
        """添加到指标时间序列

        Args:
            name: 指标名称
            value: 指标值
            labels: 标签字典
            metric_type: 指标类型
        """
        metric = MetricValue(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metric_type=metric_type,
        )
        key = self._make_key(name, labels)
        self.metrics[key].append(metric)
