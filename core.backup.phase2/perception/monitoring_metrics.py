#!/usr/bin/env python3
from __future__ import annotations
"""
感知模块监控指标系统
Perception Module Monitoring Metrics System

提供全面的性能监控、健康检查和指标收集功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import contextlib
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil

from . import BaseProcessor, InputType

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    """指标值"""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    labels: dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class Alert:
    """告警信息"""

    level: AlertLevel
    message: str
    metric_name: str
    threshold: float
    actual_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class HealthStatus:
    """健康状态"""

    processor_id: str
    status: str  # healthy, degraded, unhealthy
    last_check: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0
    error_rate: float = 0.0
    uptime: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = defaultdict(float)
        self.histograms: dict[str, list[float]] = defaultdict(list)
        self.timers: dict[str, list[float]] = defaultdict(list)
        self.lock = threading.RLock()

    def increment_counter(
        self, name: str, value: float = 1.0, labels: dict[str, str] | None = None
    ) -> Any:
        """增加计数器"""
        with self.lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
            self._record_metric(name, value, MetricType.COUNTER, labels)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """设置仪表值"""
        with self.lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
            self._record_metric(name, value, MetricType.GAUGE, labels)

    def record_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> Any:
        """记录直方图"""
        with self.lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(value)
            # 限制历史记录数量
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-500:]
            self._record_metric(name, value, MetricType.HISTOGRAM, labels)

    def record_timer(self, name: str, duration: float, labels: dict[str, str] | None = None) -> Any:
        """记录计时器"""
        with self.lock:
            key = self._make_key(name, labels)
            self.timers[key].append(duration)
            # 限制历史记录数量
            if len(self.timers[key]) > 1000:
                self.timers[key] = self.timers[key][-500:]
            self._record_metric(name, duration, MetricType.TIMER, labels)

    def _make_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        """生成指标键"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _record_metric(
        self, name: str, value: float, metric_type: MetricType, labels: dict[str, str] | None = None
    ) -> Any:
        """记录指标"""
        metric = MetricValue(name=name, value=value, metric_type=metric_type, labels=labels or {})
        self.metrics[name].append(metric)

    def get_metric_summary(self, name: str) -> dict[str, Any]:
        """获取指标摘要"""
        with self.lock:
            if name not in self.metrics:
                return {}

            values = [m.value for m in self.metrics[name]]
            if not values:
                return {}

            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": statistics.mean(values),
                "median": statistics.median(values),
                "sum": sum(values),
                "latest": values[-1] if values else None,
                "rate": len(values)
                / max(1, (datetime.now() - self.metrics[name][0].timestamp).total_seconds()),
            }

    def get_all_metrics(self) -> dict[str, Any]:
        """获取所有指标"""
        with self.lock:
            result = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {},
                "timers": {},
                "summaries": {},
            }

            # 计算直方图统计
            for name, values in self.histograms.items():
                if values:
                    result["histograms"][name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": statistics.mean(values),
                        "p50": statistics.median(values),
                        "p95": self._percentile(values, 0.95),
                        "p99": self._percentile(values, 0.99),
                    }

            # 计算计时器统计
            for name, values in self.timers.items():
                if values:
                    result["timers"][name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": statistics.mean(values),
                        "p50": statistics.median(values),
                        "p95": self._percentile(values, 0.95),
                        "p99": self._percentile(values, 0.99),
                    }

            return result

    def _percentile(self, values: list[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


class PerceptionMonitor:
    """感知模块监控器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # 监控配置
        self.enabled = self.config.get("enabled", True)
        self.collect_interval = self.config.get("collect_interval", 10)  # 秒
        self.health_check_interval = self.config.get("health_check_interval", 30)  # 秒

        # 指标收集器
        self.metrics_collector = MetricsCollector()

        # 处理器健康状态
        self.processor_health: dict[str, HealthStatus] = {}

        # 告警系统
        self.alerts: list[Alert] = []
        self.alert_rules = self._init_alert_rules()

        # 系统资源监控
        self.system_metrics = {
            "cpu_percent": deque(maxlen=60),
            "memory_percent": deque(maxlen=60),
            "disk_usage": deque(maxlen=60),
        }

        # 启动监控任务
        self.monitor_tasks: list[asyncio.Task] = []
        self.is_monitoring = False

        logger.info("📊 感知模块监控器初始化完成")

    def _init_alert_rules(self) -> dict[str, dict[str, Any]]:
        """初始化告警规则"""
        return {
            "error_rate": {
                "threshold": 0.1,  # 10%
                "level": AlertLevel.WARNING,
                "message": "处理器错误率过高",
            },
            "response_time": {
                "threshold": 5.0,  # 5秒
                "level": AlertLevel.WARNING,
                "message": "处理器响应时间过长",
            },
            "cpu_usage": {
                "threshold": 80.0,  # 80%
                "level": AlertLevel.WARNING,
                "message": "CPU使用率过高",
            },
            "memory_usage": {
                "threshold": 85.0,  # 85%
                "level": AlertLevel.WARNING,
                "message": "内存使用率过高",
            },
            "disk_usage": {
                "threshold": 90.0,  # 90%
                "level": AlertLevel.ERROR,
                "message": "磁盘空间不足",
            },
        }

    async def start_monitoring(self, processors: list[BaseProcessor]):
        """启动监控"""
        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return

        self.is_monitoring = True

        # 初始化处理器健康状态
        for processor in processors:
            self.processor_health[processor.processor_id] = HealthStatus(
                processor_id=processor.processor_id, status="healthy"
            )

        # 启动监控任务
        self.monitor_tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._check_processor_health(processors)),
            asyncio.create_task(self._evaluate_alerts()),
        ]

        logger.info(f"🚀 监控已启动,监控 {len(processors)} 个处理器")

    async def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False

        # 取消监控任务
        for task in self.monitor_tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        self.monitor_tasks.clear()
        logger.info("⏹️ 监控已停止")

    async def _collect_system_metrics(self):
        """收集系统指标(异步非阻塞版本)"""
        while self.is_monitoring:
            try:
                # CPU使用率 - 使用interval=None进行非阻塞测量
                # 第一次调用返回0,后续调用基于上次调用以来的时间计算
                cpu_percent = psutil.cpu_percent(interval=None)
                self.system_metrics["cpu_percent"].append(cpu_percent)
                self.metrics_collector.set_gauge("system_cpu_percent", cpu_percent)

                # 内存使用率 - 非阻塞
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                self.system_metrics["memory_percent"].append(memory_percent)
                self.metrics_collector.set_gauge("system_memory_percent", memory_percent)

                # 磁盘使用率 - 非阻塞(通常变化不频繁)
                disk = psutil.disk_usage("/")
                disk_percent = disk.percent
                self.system_metrics["disk_usage"].append(disk_percent)
                self.metrics_collector.set_gauge("system_disk_percent", disk_percent)

                await asyncio.sleep(self.collect_interval)

            except Exception as e:
                logger.error(f"收集系统指标失败: {e}")
                await asyncio.sleep(self.collect_interval)

    async def _check_processor_health(self, processors: list[BaseProcessor]):
        """检查处理器健康状态"""
        while self.is_monitoring:
            try:
                for processor in processors:
                    health = self.processor_health[processor.processor_id]

                    # 模拟健康检查(实际应该调用处理器的健康检查方法)
                    start_time = time.time()

                    # 这里可以调用实际的健康检查
                    is_healthy = True  # await processor.health_check()

                    response_time = time.time() - start_time
                    health.last_check = datetime.now()
                    health.response_time = response_time

                    # 记录响应时间
                    self.metrics_collector.record_timer(
                        "processor_response_time",
                        response_time,
                        {"processor": processor.processor_id},
                    )

                    # 更新健康状态
                    if is_healthy and response_time < 1.0:
                        health.status = "healthy"
                    elif is_healthy and response_time < 3.0:
                        health.status = "degraded"
                    else:
                        health.status = "unhealthy"

                    # 记录健康状态指标
                    health_status_code = (
                        1
                        if health.status == "healthy"
                        else 0.5 if health.status == "degraded" else 0
                    )
                    self.metrics_collector.set_gauge(
                        "processor_health_status",
                        health_status_code,
                        {"processor": processor.processor_id},
                    )

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"检查处理器健康状态失败: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def _evaluate_alerts(self):
        """评估告警"""
        while self.is_monitoring:
            try:
                # 检查系统指标告警
                if self.system_metrics["cpu_percent"]:
                    latest_cpu = self.system_metrics["cpu_percent"][-1]
                    if latest_cpu > self.alert_rules["cpu_usage"]["threshold"]:
                        self._create_alert(
                            level=self.alert_rules["cpu_usage"]["level"],
                            metric_name="cpu_usage",
                            threshold=self.alert_rules["cpu_usage"]["threshold"],
                            actual_value=latest_cpu,
                            message=f"CPU使用率 {latest_cpu:.1f}% 超过阈值 {self.alert_rules['cpu_usage']['threshold']}%",
                        )

                if self.system_metrics["memory_percent"]:
                    latest_memory = self.system_metrics["memory_percent"][-1]
                    if latest_memory > self.alert_rules["memory_usage"]["threshold"]:
                        self._create_alert(
                            level=self.alert_rules["memory_usage"]["level"],
                            metric_name="memory_usage",
                            threshold=self.alert_rules["memory_usage"]["threshold"],
                            actual_value=latest_memory,
                            message=f"内存使用率 {latest_memory:.1f}% 超过阈值 {self.alert_rules['memory_usage']['threshold']}%",
                        )

                if self.system_metrics["disk_usage"]:
                    latest_disk = self.system_metrics["disk_usage"][-1]
                    if latest_disk > self.alert_rules["disk_usage"]["threshold"]:
                        self._create_alert(
                            level=self.alert_rules["disk_usage"]["level"],
                            metric_name="disk_usage",
                            threshold=self.alert_rules["disk_usage"]["threshold"],
                            actual_value=latest_disk,
                            message=f"磁盘使用率 {latest_disk:.1f}% 超过阈值 {self.alert_rules['disk_usage']['threshold']}%",
                        )

                # 检查处理器告警
                for health in self.processor_health.values():
                    # 响应时间告警
                    if health.response_time > self.alert_rules["response_time"]["threshold"]:
                        self._create_alert(
                            level=self.alert_rules["response_time"]["level"],
                            metric_name="response_time",
                            threshold=self.alert_rules["response_time"]["threshold"],
                            actual_value=health.response_time,
                            message=f"处理器 {health.processor_id} 响应时间 {health.response_time:.2f}s 过长",
                        )

                await asyncio.sleep(60)  # 每分钟评估一次告警

            except Exception as e:
                logger.error(f"评估告警失败: {e}")
                await asyncio.sleep(60)

    def _create_alert(
        self,
        level: AlertLevel,
        metric_name: str,
        threshold: float,
        actual_value: float,
        message: str,
    ) -> Any:
        """创建告警"""
        alert = Alert(
            level=level,
            message=message,
            metric_name=metric_name,
            threshold=threshold,
            actual_value=actual_value,
        )

        # 避免重复告警
        recent_similar = any(
            a.metric_name == metric_name
            and a.level == level
            and not a.resolved
            and (datetime.now() - a.timestamp).seconds < 300  # 5分钟内
            for a in self.alerts
        )

        if not recent_similar:
            self.alerts.append(alert)
            logger.warning(f"🚨 {level.value.upper()}: {message}")

    def record_processing_event(
        self,
        processor_id: str,
        input_type: InputType,
        success: bool,
        processing_time: float,
        confidence: float = 0.0,
    ):
        """记录处理事件"""
        labels = {
            "processor": processor_id,
            "input_type": input_type.value,
            "status": "success" if success else "error",
        }

        # 记录处理计数
        self.metrics_collector.increment_counter("processing_total", 1.0, labels)

        # 记录处理时间
        self.metrics_collector.record_timer("processing_duration", processing_time, labels)

        # 记录置信度
        if confidence > 0:
            self.metrics_collector.record_histogram("processing_confidence", confidence, labels)

        # 记录错误
        if not success:
            self.metrics_collector.increment_counter("processing_errors", 1.0, labels)

    def get_monitoring_dashboard(self) -> dict[str, Any]:
        """获取监控仪表板数据"""
        return {
            "system_status": {
                "cpu_percent": list(self.system_metrics["cpu_percent"])[-10:],
                "memory_percent": list(self.system_metrics["memory_percent"])[-10:],
                "disk_percent": (
                    list(self.system_metrics["disk_usage"])[-1]
                    if self.system_metrics["disk_usage"]
                    else 0
                ),
            },
            "processor_health": {
                pid: {
                    "status": health.status,
                    "last_check": health.last_check.isoformat(),
                    "response_time": health.response_time,
                    "uptime": health.uptime,
                }
                for pid, health in self.processor_health.items()
            },
            "metrics": self.metrics_collector.get_all_metrics(),
            "recent_alerts": [
                {
                    "level": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in sorted(self.alerts, key=lambda a: a.timestamp, reverse=True)[:10]
            ],
            "alert_counts": {
                level: sum(1 for a in self.alerts if a.level == level and not a.resolved)
                for level in AlertLevel
            },
        }

    def get_performance_report(self, time_range: int = 3600) -> dict[str, Any]:
        """获取性能报告"""
        cutoff_time = datetime.now() - timedelta(seconds=time_range)

        # 过滤最近的指标
        recent_metrics = {}
        for name, metric_deque in self.metrics_collector.metrics.items():
            recent_metrics[name] = [m for m in metric_deque if m.timestamp >= cutoff_time]

        # 生成报告
        report = {
            "time_range_seconds": time_range,
            "total_requests": 0,
            "avg_response_time": 0,
            "error_rate": 0,
            "top_processors": {},
            "processor_breakdown": {},
        }

        total_requests = 0
        total_errors = 0
        response_times = []

        for name, metrics in recent_metrics.items():
            if name == "processing_total":
                for metric in metrics:
                    if metric.labels.get("status") == "success":
                        total_requests += metric.value
                    else:
                        total_errors += metric.value

                        # 按处理器分组统计
                        processor = metric.labels.get("processor", "unknown")
                        if processor not in report["processor_breakdown"]:
                            report["processor_breakdown"][processor] = {
                                "requests": 0,
                                "errors": 0,
                                "response_time": [],
                            }
                        report["processor_breakdown"][processor]["errors"] += metric.value

            elif name == "processing_duration":
                response_times.extend(m.value for m in metrics)

                # 按处理器收集响应时间
                for metric in metrics:
                    processor = metric.labels.get("processor", "unknown")
                    if processor not in report["processor_breakdown"]:
                        report["processor_breakdown"][processor] = {
                            "requests": 0,
                            "errors": 0,
                            "response_time": [],
                        }
                    report["processor_breakdown"][processor]["response_time"].append(metric.value)

        # 计算总体指标
        report["total_requests"] = int(total_requests)
        report["avg_response_time"] = statistics.mean(response_times) if response_times else 0
        report["error_rate"] = total_errors / max(total_requests + total_errors, 1)

        # 计算每个处理器的平均响应时间
        for _processor, data in report["processor_breakdown"].items():
            if data["response_time"]:
                data["avg_response_time"] = statistics.mean(data["response_time"])
                data["p95_response_time"] = self._percentile(data["response_time"], 0.95)
            else:
                data["avg_response_time"] = 0
                data["p95_response_time"] = 0

        return report


# 全局监控器实例
_global_monitor: PerceptionMonitor | None = None


async def get_global_monitor(config: dict[str, Any] | None = None) -> PerceptionMonitor:
    """获取全局监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerceptionMonitor(config)
    return _global_monitor


# 监控装饰器
def monitor_performance(processor_id: str) -> Any:
    """性能监控装饰器"""

    def decorator(func) -> None:
        async def wrapper(self, *args, **kwargs):
            start_time = time.time()
            success = True
            confidence = 0.0

            try:
                result = await func(self, *args, **kwargs)
                if hasattr(result, "confidence"):
                    confidence = result.confidence
                return result
            except Exception as e:
                success = False
                logger.error(f"处理器 {processor_id} 执行失败: {e}")
                raise
            finally:
                processing_time = time.time() - start_time

                # 获取监控器并记录事件
                try:
                    monitor = await get_global_monitor()
                    input_type = args[0] if len(args) > 0 else "unknown"

                    # 转换input_type为InputType枚举
                    if isinstance(input_type, str):
                        try:
                            input_type_enum = InputType(input_type.lower())
                        except ValueError:
                            input_type_enum = InputType.UNKNOWN
                    else:
                        input_type_enum = InputType.UNKNOWN

                    monitor.record_processing_event(
                        processor_id=processor_id,
                        input_type=input_type_enum,
                        success=success,
                        processing_time=processing_time,
                        confidence=confidence,
                    )
                except Exception as monitor_error:
                    logger.debug(f"监控记录失败: {monitor_error}")

        return wrapper

    return decorator
