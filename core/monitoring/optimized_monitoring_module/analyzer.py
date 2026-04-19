#!/usr/bin/env python3
from __future__ import annotations
"""
优化版监控告警模块 - 性能分析器
Optimized Monitoring and Alerting Module - Performance Analyzer

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from .collector import MetricsCollector

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """性能分析器

    负责分析指标趋势、检测异常和生成性能报告。
    """

    def __init__(self, metrics_collector: MetricsCollector, config: dict[str, Any] | None = None):
        """初始化性能分析器

        Args:
            metrics_collector: 指标收集器实例
            config: 配置字典
        """
        self.metrics_collector = metrics_collector
        self.config = config or {}

    def analyze_trend(
        self,
        metric_name: str,
        labels: dict[str, str] | None = None,
        period: timedelta = timedelta(hours=1),
    ) -> dict[str, Any]:
        """分析指标趋势

        Args:
            metric_name: 指标名称
            labels: 标签字典
            period: 分析周期

        Returns:
            趋势分析结果
        """
        end_time = datetime.now()
        start_time = end_time - period

        history = self.metrics_collector.get_metrics_history(
            metric_name, labels, start_time, end_time
        )

        if len(history) < 2:
            return {"trend": "insufficient_data"}

        values = [m.value for m in history]
        timestamps = [m.timestamp.timestamp() for m in history]

        # 计算趋势
        slope = np.polyfit(timestamps, values, 1)[0]

        trend = "stable"
        if slope > 0.1:
            trend = "increasing"
        elif slope < -0.1:
            trend = "decreasing"

        # 计算变化率
        change_rate = (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0

        return {
            "trend": trend,
            "slope": slope,
            "change_rate": change_rate,
            "current_value": values[-1],
            "average_value": statistics.mean(values),
            "min_value": min(values),
            "max_value": max(values),
            "data_points": len(values),
        }

    def detect_anomalies(
        self,
        metric_name: str,
        labels: dict[str, str] | None = None,
        period: timedelta = timedelta(hours=1),
    ) -> list[dict[str, Any]]:
        """检测异常

        Args:
            metric_name: 指标名称
            labels: 标签字典
            period: 分析周期

        Returns:
            异常列表
        """
        end_time = datetime.now()
        start_time = end_time - period

        history = self.metrics_collector.get_metrics_history(
            metric_name, labels, start_time, end_time
        )

        if len(history) < 10:
            return []

        values = [m.value for m in history]

        # 使用IQR方法检测异常
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        anomalies = []
        for _i, metric in enumerate(history):
            if metric.value < lower_bound or metric.value > upper_bound:
                anomalies.append(
                    {
                        "timestamp": metric.timestamp,
                        "value": metric.value,
                        "type": "low" if metric.value < lower_bound else "high",
                        "deviation": abs(metric.value - (q1 + q3) / 2),
                    }
                )

        return anomalies

    def generate_performance_report(
        self, period: timedelta = timedelta(hours=24)
    ) -> dict[str, Any]:
        """生成性能报告

        Args:
            period: 报告周期

        Returns:
            性能报告字典
        """
        end_time = datetime.now()
        start_time = end_time - period

        # 获取所有指标名称
        metric_names = set()
        with self.metrics_collector.lock:
            for key in self.metrics_collector.metrics:
                metric_names.add(key.split("[")[0])  # 去掉标签部分

        report = {
            "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "metrics": {},
        }

        for metric_name in metric_names:
            try:
                # 趋势分析
                trend = self.analyze_trend(metric_name, period=period)

                # 异常检测
                anomalies = self.detect_anomalies(metric_name, period=period)

                # 统计信息
                stats = self.metrics_collector.get_metric_stats(metric_name)

                report["metrics"][metric_name] = {
                    "trend": trend,
                    "anomalies": anomalies,
                    "statistics": stats,
                }
            except Exception as e:
                logger.error(f"生成指标 {metric_name} 报告失败: {e}")

        return report
