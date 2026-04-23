#!/usr/bin/env python3
from __future__ import annotations
"""
小诺优化监控模块
Xiaonuo Optimization Monitoring Module

提供优化系统的监控、指标收集和告警功能。

作者: Athena平台团队
创建时间: 2025-12-27
"""

import json
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """指标数据点"""

    timestamp: float
    value: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class AlertRule:
    """告警规则"""

    name: str
    metric_name: str
    condition: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    threshold: float
    duration_seconds: int = 60  # 持续时间
    severity: str = "WARNING"  # WARNING, CRITICAL
    enabled: bool = True
    callback: Callable | None = None


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_points: int = 1000):
        """
        初始化指标收集器

        Args:
            max_points: 每个指标保留的最大数据点数
        """
        self._metrics: dict[str, deque] = {}
        self._max_points = max_points
        self._lock = Lock()

    def record(self, metric_name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """
        记录指标

        Args:
            metric_name: 指标名称
            value: 指标值
            tags: 标签
        """
        with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = deque(maxlen=self._max_points)

            point = MetricPoint(timestamp=time.time(), value=value, tags=tags or {})
            self._metrics[metric_name].append(point)

    def get_metric(
        self, metric_name: str, duration_seconds: int | None = None
    ) -> list[MetricPoint]:
        """
        获取指标数据

        Args:
            metric_name: 指标名称
            duration_seconds: 时间范围(秒)

        Returns:
            指标数据点列表
        """
        with self._lock:
            if metric_name not in self._metrics:
                return []

            points = list(self._metrics[metric_name])

            if duration_seconds:
                cutoff = time.time() - duration_seconds
                points = [p for p in points if p.timestamp >= cutoff]

            return points

    def get_aggregated(
        self, metric_name: str, duration_seconds: int = 300, aggregation: str = "avg"
    ) -> float | None:
        """
        获取聚合指标

        Args:
            metric_name: 指标名称
            duration_seconds: 时间范围
            aggregation: 聚合方式 (avg, sum, min, max, count)

        Returns:
            聚合值
        """
        points = self.get_metric(metric_name, duration_seconds)

        if not points:
            return None

        values = [p.value for p in points]

        if aggregation == "avg":
            return sum(values) / len(values)
        elif aggregation == "sum":
            return sum(values)
        elif aggregation == "min":
            return min(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "count":
            return len(values)
        else:
            return None

    def get_all_metrics(self) -> list[str]:
        """获取所有指标名称"""
        with self._lock:
            return list(self._metrics.keys())

    def clear_metric(self, metric_name: str) -> None:
        """清除指标数据"""
        with self._lock:
            if metric_name in self._metrics:
                self._metrics[metric_name].clear()


class AlertManager:
    """告警管理器"""

    def __init__(self):
        """初始化告警管理器"""
        self._rules: list[AlertRule] = []
        self._alert_states: dict[str, dict] = {}
        self._lock = Lock()
        self._alert_callbacks: list[Callable] = []

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        with self._lock:
            self._rules.append(rule)
            logger.info(f"添加告警规则: {rule.name}")

    def remove_rule(self, rule_name: str) -> None:
        """移除告警规则"""
        with self._lock:
            self._rules = [r for r in self._rules if r.name != rule_name]
            if rule_name in self._alert_states:
                del self._alert_states[rule_name]
            logger.info(f"移除告警规则: {rule_name}")

    def add_alert_callback(self, callback: Callable) -> None:
        """添加告警回调"""
        self._alert_callbacks.append(callback)

    def check_rules(self, metrics_collector: MetricsCollector) -> list[dict[str, Any]]:
        """
        检查告警规则

        Args:
            metrics_collector: 指标收集器

        Returns:
            触发的告警列表
        """
        triggered_alerts = []

        with self._lock:
            for rule in self._rules:
                if not rule.enabled:
                    continue

                # 获取当前指标值
                current_value = metrics_collector.get_aggregated(
                    rule.metric_name, rule.duration_seconds, "avg"
                )

                if current_value is None:
                    continue

                # 检查条件
                triggered = self._evaluate_condition(current_value, rule.condition, rule.threshold)

                # 更新告警状态
                now = time.time()
                if rule.name not in self._alert_states:
                    self._alert_states[rule.name] = {
                        "triggered": False,
                        "first_seen": None,
                        "count": 0,
                    }

                state = self._alert_states[rule.name]

                if triggered:
                    if not state["triggered"]:
                        # 首次触发
                        state["triggered"] = True
                        state["first_seen"] = now
                        state["count"] = 1
                    else:
                        # 持续触发
                        state["count"] += 1

                        # 检查是否达到告警持续时间
                        duration = now - state["first_seen"]
                        if duration >= rule.duration_seconds:
                            alert = {
                                "rule_name": rule.name,
                                "metric_name": rule.metric_name,
                                "current_value": current_value,
                                "threshold": rule.threshold,
                                "condition": rule.condition,
                                "duration": duration,
                                "severity": rule.severity,
                                "timestamp": now,
                            }
                            triggered_alerts.append(alert)

                            # 调用回调
                            if rule.callback:
                                try:
                                    rule.callback(alert)
                                except Exception as e:
                                    logger.error(f"告警回调执行失败: {e}")

                            # 触发全局回调
                            for callback in self._alert_callbacks:
                                try:
                                    callback(alert)
                                except Exception as e:
                                    logger.error(f"全局告警回调执行失败: {e}")
                else:
                    # 恢复正常
                    if state["triggered"]:
                        logger.info(f"告警恢复: {rule.name}")
                        state["triggered"] = False
                        state["key"] = None
                        state["count"] = 0

        return triggered_alerts

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """评估条件"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return value == threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        else:
            return False

    def get_alert_states(self) -> dict[str, dict]:
        """获取告警状态"""
        with self._lock:
            return self._alert_states.copy()


class OptimizationMonitor:
    """优化系统监控器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化监控器

        Args:
            config: 配置字典
        """
        config = config or {}

        # 初始化组件
        self.metrics = MetricsCollector(max_points=config.get("max_points", 1000))
        self.alerts = AlertManager()

        # 配置
        self.enabled = config.get("enabled", True)
        self.stats_interval = config.get("stats_interval_seconds", 60)

        # 内部统计
        self._start_time = time.time()
        self._total_requests = 0
        self._total_optimizations = 0
        self._total_failures = 0

        # 设置默认告警规则
        self._setup_default_alerts(config)

        logger.info("优化监控器已初始化")

    def _setup_default_alerts(self, config: dict[str, Any]) -> None:
        """设置默认告警规则"""
        alerts_config = config.get("alerts", {})

        # 优化失败率告警
        failure_rate_threshold = alerts_config.get("optimization_failure_rate", 0.05)
        self.alerts.add_rule(
            AlertRule(
                name="optimization_failure_rate",
                metric_name="optimization.failure_rate",
                condition="gt",
                threshold=failure_rate_threshold,
                duration_seconds=300,
                severity="WARNING",
            )
        )

        # 缓存命中率告警
        cache_hit_threshold = alerts_config.get("cache_hit_rate_threshold", 0.5)
        self.alerts.add_rule(
            AlertRule(
                name="cache_hit_rate",
                metric_name="validation.cache_hit_rate",
                condition="lt",
                threshold=cache_hit_threshold,
                duration_seconds=300,
                severity="WARNING",
            )
        )

        # 响应时间告警
        response_time_threshold = alerts_config.get("validation_response_time_ms", 500)
        self.alerts.add_rule(
            AlertRule(
                name="validation_response_time",
                metric_name="validation.response_time_ms",
                condition="gt",
                threshold=response_time_threshold,
                duration_seconds=60,
                severity="WARNING",
            )
        )

    def record_request(
        self, optimized: bool, success: bool, processing_time: float, cache_hit: bool = False
    ) -> None:
        """
        记录请求指标

        Args:
            optimized: 是否执行优化
            success: 是否成功
            processing_time: 处理时间(秒)
            cache_hit: 是否命中缓存
        """
        if not self.enabled:
            return

        self._total_requests += 1

        if optimized:
            self._total_optimizations += 1

        if not success:
            self._total_failures += 1

        # 记录指标
        self.metrics.record("request.total", self._total_requests)

        self.metrics.record("request.processing_time_ms", processing_time * 1000)

        if cache_hit:
            self.metrics.record("validation.cache_hit", 1)

        # 计算并记录失败率
        if self._total_requests > 0:
            failure_rate = self._total_failures / self._total_requests
            self.metrics.record("optimization.failure_rate", failure_rate)

        # 计算并记录缓存命中率
        cache_metrics = self.metrics.get_metric("validation.cache_hit", 300)
        if cache_metrics:
            cache_hit_rate = sum(p.value for p in cache_metrics) / len(cache_metrics)
            self.metrics.record("validation.cache_hit_rate", cache_hit_rate)

    def record_validation(self, response_time_ms: float, cache_hit: bool) -> None:
        """
        记录验证指标

        Args:
            response_time_ms: 响应时间(毫秒)
            cache_hit: 是否命中缓存
        """
        if not self.enabled:
            return

        self.metrics.record("validation.response_time_ms", response_time_ms)

        self.metrics.record("validation.cache_hit", 1 if cache_hit else 0)

    def record_tool_discovery(self, num_tools: int, processing_time_ms: float) -> None:
        """
        记录工具发现指标

        Args:
            num_tools: 发现的工具数量
            processing_time_ms: 处理时间(毫秒)
        """
        if not self.enabled:
            return

        self.metrics.record("tool_discovery.num_tools", num_tools)

        self.metrics.record("tool_discovery.processing_time_ms", processing_time_ms)

    def record_prediction(self, num_predictions: int, high_risk_count: int) -> None:
        """
        记录预测指标

        Args:
            num_predictions: 预测数量
            high_risk_count: 高风险数量
        """
        if not self.enabled:
            return

        self.metrics.record("prediction.count", num_predictions)

        self.metrics.record("prediction.high_risk_count", high_risk_count)

    def check_alerts(self) -> list[dict[str, Any]]:
        """
        检查告警

        Returns:
            触发的告警列表
        """
        if not self.enabled:
            return []

        return self.alerts.check_rules(self.metrics)

    def get_metrics_summary(self) -> dict[str, Any]:
        """
        获取指标摘要

        Returns:
            指标摘要字典
        """
        if not self.enabled:
            return {"enabled": False}

        uptime = time.time() - self._start_time

        summary = {
            "enabled": True,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "total_requests": self._total_requests,
            "total_optimizations": self._total_optimizations,
            "total_failures": self._total_failures,
            "optimization_rate": (
                self._total_optimizations / self._total_requests if self._total_requests > 0 else 0
            ),
            "failure_rate": (
                self._total_failures / self._total_requests if self._total_requests > 0 else 0
            ),
            "metrics": {},
        }

        # 添加关键指标的聚合值
        for metric_name in ["request.processing_time_ms", "validation.response_time_ms"]:
            avg_value = self.metrics.get_aggregated(metric_name, 300, "avg")
            max_value = self.metrics.get_aggregated(metric_name, 300, "max")
            min_value = self.metrics.get_aggregated(metric_name, 300, "min")

            if avg_value is not None:
                summary["metrics"][metric_name] = {
                    "avg_5min": avg_value,
                    "max_5min": max_value,
                    "min_5min": min_value,
                }

        return summary

    def get_health_status(self) -> dict[str, Any]:
        """
        获取健康状态

        Returns:
            健康状态字典
        """
        if not self.enabled:
            return {"status": "disabled"}

        triggered_alerts = self.check_alerts()
        critical_alerts = [a for a in triggered_alerts if a["severity"] == "CRITICAL"]
        warning_alerts = [a for a in triggered_alerts if a["severity"] == "WARNING"]

        if critical_alerts:
            status = "critical"
        elif warning_alerts:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "alerts": {
                "critical": len(critical_alerts),
                "warning": len(warning_alerts),
                "total": len(triggered_alerts),
            },
            "uptime_hours": (time.time() - self._start_time) / 3600,
        }

    def log_metrics_summary(self) -> None:
        """记录指标摘要到日志"""
        if not self.enabled:
            return

        summary = self.get_metrics_summary()

        logger.info("=" * 60)
        logger.info("优化系统监控摘要:")
        logger.info(f"  运行时间: {summary['uptime_hours']:.2f}小时")
        logger.info(f"  总请求数: {summary['total_requests']}")
        logger.info(f"  优化次数: {summary['total_optimizations']}")
        logger.info(f"  失败次数: {summary['total_failures']}")
        logger.info(f"  优化率: {summary['optimization_rate']:.1%}")
        logger.info(f"  失败率: {summary['failure_rate']:.1%}")

        if "request.processing_time_ms" in summary["metrics"]:
            metrics = summary["metrics"]["request.processing_time_ms"]
            logger.info(f"  平均响应时间: {metrics['avg_5min']:.2f}ms")
            logger.info(f"  最大响应时间: {metrics['max_5min']:.2f}ms")

        logger.info("=" * 60)

    def export_metrics(self, output_format: str = "json") -> str:
        """
        导出指标数据

        Args:
            output_format: 输出格式 (json, prometheus)

        Returns:
            格式化的指标字符串
        """
        summary = self.get_metrics_summary()

        if output_format == "json":
            return json.dumps(summary, indent=2, ensure_ascii=False)

        elif output_format == "prometheus":
            lines = []
            lines.append("# HELP xiaonuo_optimization_requests_total Total number of requests")
            lines.append("# TYPE xiaonuo_optimization_requests_total counter")
            lines.append(f"xiaonuo_optimization_requests_total {summary['total_requests']}")

            lines.append("# HELP xiaonuo_optimization_failures_total Total number of failures")
            lines.append("# TYPE xiaonuo_optimization_failures_total counter")
            lines.append(f"xiaonuo_optimization_failures_total {summary['total_failures']}")

            return "\n".join(lines)

        else:
            raise ValueError(f"不支持的输出格式: {output_format}")


# 单例实例
_monitor_instance: OptimizationMonitor | None = None
_monitor_lock = Lock()


def get_optimization_monitor(config: dict[str, Any] | None = None) -> OptimizationMonitor:
    """
    获取优化监控器单例

    Args:
        config: 配置字典

    Returns:
        优化监控器实例
    """
    global _monitor_instance

    with _monitor_lock:
        if _monitor_instance is None:
            _monitor_instance = OptimizationMonitor(config)

        return _monitor_instance
