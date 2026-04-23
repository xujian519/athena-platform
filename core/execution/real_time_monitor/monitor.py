#!/usr/bin/env python3
from __future__ import annotations
"""
实时执行监控系统 - 主监控类
Real-time Execution Monitoring System - Main Monitor

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import numpy as np
import psutil

from .resource_monitors import CPUMonitor, DiskMonitor, MemoryMonitor, NetworkMonitor
from .types import (
    Alert,
    AlertLevel,
    Metric,
    MetricType,
    MonitoringConfig,
    PerformanceSnapshot,
)

logger = logging.getLogger(__name__)


class RealTimeMonitor:
    """实时监控器 - 提供系统运行状态监控、性能分析和告警功能"""

    def __init__(self, config: MonitoringConfig | None = None):
        """初始化实时监控器

        Args:
            config: 监控配置对象
        """
        self.config = config or MonitoringConfig()

        # 指标存储
        self.metrics = defaultdict(deque)
        self.custom_metrics = {}

        # 告警管理
        self.alerts = {}
        self.alert_rules = {}
        self.alert_history = deque(maxlen=1000)

        # 性能数据
        self.performance_history = deque(maxlen=1000)
        self.performance_snapshots = deque(maxlen=100)

        # 监控状态
        self.is_running = False
        self.collector_task = None
        self.analyzer_task = None

        # WebSocket相关 (在websocket_handler中管理)
        self.websocket_clients = set()

        # 回调函数
        self.alert_callbacks = []

        # 资源监控器
        self.resource_monitors = {
            "cpu": CPUMonitor(),
            "memory": MemoryMonitor(),
            "disk": DiskMonitor(),
            "network": NetworkMonitor(),
        }

        # 初始化默认告警规则
        self._init_default_alert_rules()

    def _init_default_alert_rules(self) -> None:
        """初始化默认告警规则"""
        # CPU使用率告警
        self.add_alert_rule(
            "cpu_high",
            metric_name="cpu_percent",
            condition=lambda x: x > 80,
            level=AlertLevel.WARNING,
            message="CPU使用率过高: {value:.1f}%",
        )

        # 内存使用率告警
        self.add_alert_rule(
            "memory_high",
            metric_name="memory_percent",
            condition=lambda x: x > 85,
            level=AlertLevel.WARNING,
            message="内存使用率过高: {value:.1f}%",
        )

        # 磁盘使用率告警
        self.add_alert_rule(
            "disk_high",
            metric_name="disk_percent",
            condition=lambda x: x > 90,
            level=AlertLevel.ERROR,
            message="磁盘使用率过高: {value:.1f}%",
        )

        # 错误率告警
        self.add_alert_rule(
            "error_rate_high",
            metric_name="error_rate",
            condition=lambda x: x > 0.05,
            level=AlertLevel.ERROR,
            message="错误率过高: {value:.2%}",
        )

        # 响应时间告警
        self.add_alert_rule(
            "response_time_high",
            metric_name="response_time",
            condition=lambda x: x > 5.0,
            level=AlertLevel.WARNING,
            message="响应时间过长: {value:.2f}秒",
        )

    async def start(self):
        """启动监控系统"""
        logger.info("启动实时执行监控系统")
        self.is_running = True

        # 启动指标收集器
        self.collector_task = asyncio.create_task(self._collect_metrics())

        # 启动性能分析器
        self.analyzer_task = asyncio.create_task(self._analyze_performance())

        logger.info("监控系统已启动")

    async def stop(self):
        """停止监控系统"""
        logger.info("停止实时执行监控系统")
        self.is_running = False

        # 取消任务
        if self.collector_task:
            self.collector_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.collector_task

        if self.analyzer_task:
            self.analyzer_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.analyzer_task

    async def _collect_metrics(self):
        """收集指标"""
        last_collection = time.time()

        while self.is_running:
            try:
                current_time = time.time()

                # 收集系统指标
                if self.config.enable_system_monitoring:
                    await self._collect_system_metrics()

                # 收集性能指标
                if self.config.enable_performance_monitoring:
                    await self._collect_performance_metrics()

                # 清理过期数据
                if current_time - last_collection > 60:  # 每分钟清理一次
                    await self._cleanup_expired_data()
                    last_collection = current_time

                await asyncio.sleep(self.config.collection_interval)

            except Exception as e:
                logger.error(f"指标收集错误: {e}")

    async def _collect_system_metrics(self):
        """收集系统指标"""
        datetime.now()

        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        await self.record_metric(
            Metric(
                name="cpu_percent",
                metric_type=MetricType.GAUGE,
                description="CPU使用率",
                value=cpu_percent,
                unit="percent",
            )
        )

        # 内存指标
        memory = psutil.virtual_memory()
        await self.record_metric(
            Metric(
                name="memory_percent",
                metric_type=MetricType.GAUGE,
                description="内存使用率",
                value=memory.percent,
                unit="percent",
            )
        )

        await self.record_metric(
            Metric(
                name="memory_available",
                metric_type=MetricType.GAUGE,
                description="可用内存",
                value=memory.available / (1024**3),  # GB
                unit="GB",
            )
        )

        # 磁盘指标
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        await self.record_metric(
            Metric(
                name="disk_percent",
                metric_type=MetricType.GAUGE,
                description="磁盘使用率",
                value=disk_percent,
                unit="percent",
            )
        )

        # 网络指标
        network = psutil.net_io_counters()
        await self.record_metric(
            Metric(
                name="network_bytes_sent",
                metric_type=MetricType.COUNTER,
                description="网络发送字节数",
                value=network.bytes_sent,
                unit="bytes",
            )
        )

        await self.record_metric(
            Metric(
                name="network_bytes_recv",
                metric_type=MetricType.COUNTER,
                description="网络接收字节数",
                value=network.bytes_recv,
                unit="bytes",
            )
        )

    async def _collect_performance_metrics(self):
        """收集性能指标"""
        datetime.now()

        # 获取并发控制器统计(如果可用)
        try:
            from .fine_grained_concurrency import fine_grained_concurrency_controller

            stats = fine_grained_concurrency_controller.get_statistics()

            await self.record_metric(
                Metric(
                    name="active_tasks",
                    metric_type=MetricType.GAUGE,
                    description="活动任务数",
                    value=stats.active_tasks,
                )
            )

            await self.record_metric(
                Metric(
                    name="queued_tasks",
                    metric_type=MetricType.GAUGE,
                    description="排队任务数",
                    value=stats.queued_tasks,
                )
            )

            if stats.avg_execution_time > 0:
                await self.record_metric(
                    Metric(
                        name="avg_execution_time",
                        metric_type=MetricType.GAUGE,
                        description="平均执行时间",
                        value=stats.avg_execution_time,
                        unit="seconds",
                    )
                )

            # 计算错误率
            if stats.total_tasks > 0:
                error_rate = stats.failed_tasks / stats.total_tasks
                await self.record_metric(
                    Metric(
                        name="error_rate",
                        metric_type=MetricType.GAUGE,
                        description="任务错误率",
                        value=error_rate,
                        unit="ratio",
                    )
                )

        except ImportError:
            logger.warning("可选模块导入失败，使用降级方案")

    async def record_metric(self, metric: Metric):
        """记录指标

        Args:
            metric: 指标对象
        """
        timestamp = datetime.now()
        metric.timestamp = timestamp

        # 存储指标
        self.metrics[metric.name].append((timestamp, metric.value))

        # 限制历史数据大小
        max_size = int(self.config.retention_period / self.config.collection_interval)
        if len(self.metrics[metric.name]) > max_size:
            self.metrics[metric.name].popleft()

        # 检查告警规则
        if self.config.enable_alerts:
            await self._check_alert_rules(metric)

    async def _check_alert_rules(self, metric: Metric):
        """检查告警规则

        Args:
            metric: 指标对象
        """
        for rule_name, rule in self.alert_rules.items():
            if rule["metric_name"] == metric.name:
                try:
                    # 检查条件
                    if rule["condition"](metric.value):
                        await self._trigger_alert(
                            rule_name=rule_name,
                            metric_name=metric.name,
                            current_value=metric.value,
                            threshold=rule.get("threshold", metric.value),
                            level=rule["level"],
                            message=rule["message"].format(value=metric.value),
                        )
                    else:
                        # 如果告警已触发但条件不再满足,解决告警
                        if rule_name in self.alerts and not self.alerts[rule_name].resolved_at:
                            await self._resolve_alert(rule_name)

                except Exception as e:
                    logger.error(f"检查告警规则失败 {rule_name}: {e}")

    async def _trigger_alert(
        self,
        rule_name: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        level: AlertLevel,
        message: str,
    ):
        """触发告警"""
        # 检查冷却期
        now = datetime.now()
        if (
            rule_name in self.alerts
            and not self.alerts[rule_name].resolved_at
            and (now - self.alerts[rule_name].triggered_at).seconds < self.config.alert_cooldown
        ):
            return

        # 创建告警
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            name=rule_name,
            level=level,
            message=message,
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value,
            triggered_at=now,
        )

        # 保存告警
        self.alerts[rule_name] = alert
        self.alert_history.append(alert)

        # 执行回调
        await self._execute_alert_callbacks(alert)

        # 发送Webhook通知
        if self.config.webhook_url:
            await self._send_webhook_notification(alert)

        logger.warning(f"触发告警: {rule_name} - {message}")

    async def _resolve_alert(self, rule_name: str):
        """解决告警

        Args:
            rule_name: 规则名称
        """
        if rule_name in self.alerts:
            self.alerts[rule_name].resolved_at = datetime.now()

            logger.info(f"告警已解决: {rule_name}")

    async def _execute_alert_callbacks(self, alert: Alert):
        """执行告警回调

        Args:
            alert: 告警对象
        """
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"执行告警回调失败: {e}")

    async def _send_webhook_notification(self, alert: Alert):
        """发送Webhook通知

        Args:
            alert: 告警对象
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "triggered_at": alert.triggered_at.isoformat(),
                }

                async with session.post(self.config.webhook_url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info(f"Webhook通知发送成功: {alert.name}")
                    else:
                        logger.error(f"Webhook通知发送失败: {resp.status}")

        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")

    async def _analyze_performance(self):
        """分析性能"""
        while self.is_running:
            try:
                # 创建性能快照
                snapshot = await self._create_performance_snapshot()
                self.performance_snapshots.append(snapshot)
                self.performance_history.append(snapshot)

                # 分析性能趋势
                await self._analyze_performance_trends()

                await asyncio.sleep(5.0)  # 每5秒分析一次

            except Exception as e:
                logger.error(f"性能分析错误: {e}")

    async def _create_performance_snapshot(self) -> PerformanceSnapshot:
        """创建性能快照

        Returns:
            性能快照对象
        """
        # 获取最新指标值
        cpu_percent = self._get_latest_metric_value("cpu_percent", 0)
        memory_percent = self._get_latest_metric_value("memory_percent", 0)
        disk_percent = self._get_latest_metric_value("disk_percent", 0)

        network_sent = self._get_latest_metric_value("network_bytes_sent", 0)
        network_recv = self._get_latest_metric_value("network_bytes_recv", 0)

        active_tasks = self._get_latest_metric_value("active_tasks", 0)
        queued_tasks = self._get_latest_metric_value("queued_tasks", 0)
        error_rate = self._get_latest_metric_value("error_rate", 0)

        # 计算响应时间和吞吐量
        response_time = self._calculate_response_time()
        throughput = self._calculate_throughput()

        return PerformanceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage=disk_percent,
            network_io={"sent": network_sent, "recv": network_recv},
            active_tasks=active_tasks,
            queued_tasks=queued_tasks,
            response_time=response_time,
            throughput=throughput,
            error_rate=error_rate,
        )

    def _get_latest_metric_value(self, metric_name: str, default: float = 0) -> float:
        """获取最新指标值

        Args:
            metric_name: 指标名称
            default: 默认值

        Returns:
            指标值
        """
        if self.metrics.get(metric_name):
            return self.metrics[metric_name][-1][1]
        return default

    def _calculate_response_time(self) -> float:
        """计算响应时间

        Returns:
            响应时间(秒)
        """
        # 基于队列长度和活跃任务数估算
        queued = self._get_latest_metric_value("queued_tasks", 0)
        active = self._get_latest_metric_value("active_tasks", 1)

        if active == 0:
            return 0

        # 简单估算:队列长度 / 活跃任务数
        return queued / active

    def _calculate_throughput(self) -> float:
        """计算吞吐量

        Returns:
            吞吐量(任务/秒)
        """
        # 基于历史数据计算
        if len(self.performance_history) < 2:
            return 0

        # 计算最近一分钟的吞吐量
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_tasks = [s for s in self.performance_history if s.timestamp > one_minute_ago]

        if not recent_tasks:
            return 0

        return len(recent_tasks) / 60  # 任务/秒

    async def _analyze_performance_trends(self):
        """分析性能趋势"""
        if len(self.performance_history) < 10:
            return

        # 计算移动平均
        window_size = 10
        recent = list(self.performance_history)[-window_size:]

        # CPU趋势
        cpu_values = [s.cpu_percent for s in recent]
        cpu_trend = np.mean(np.diff(cpu_values))

        if cpu_trend > 5:
            logger.info("CPU使用率呈上升趋势")
        elif cpu_trend < -5:
            logger.info("CPU使用率呈下降趋势")

        # 内存趋势
        memory_values = [s.memory_percent for s in recent]
        memory_trend = np.mean(np.diff(memory_values))

        if memory_trend > 5:
            logger.info("内存使用率呈上升趋势")

        # 响应时间趋势
        response_times = [s.response_time for s in recent]
        response_trend = np.mean(np.diff(response_times))

        if response_trend > 0.5:
            logger.warning("响应时间呈上升趋势")

    async def _cleanup_expired_data(self):
        """清理过期数据"""
        cutoff_time = datetime.now() - timedelta(seconds=self.config.retention_period)

        # 清理指标数据
        for metric_name in list(self.metrics.keys()):
            self.metrics[metric_name] = deque(
                (timestamp, value)
                for timestamp, value in self.metrics[metric_name]
                if timestamp > cutoff_time
            )

        # 清理性能快照
        self.performance_snapshots = deque(
            snapshot for snapshot in self.performance_snapshots if snapshot.timestamp > cutoff_time
        )

    def add_alert_rule(
        self,
        rule_name: str,
        metric_name: str,
        condition: Callable[[float], bool],
        level: AlertLevel,
        message: str,
        threshold: Optional[float] = None,
    ):
        """添加告警规则

        Args:
            rule_name: 规则名称
            metric_name: 指标名称
            condition: 条件函数
            level: 告警级别
            message: 告警消息
            threshold: 阈值
        """
        self.alert_rules[rule_name] = {
            "metric_name": metric_name,
            "condition": condition,
            "level": level,
            "message": message,
            "threshold": threshold,
        }

    def remove_alert_rule(self, rule_name: str) -> None:
        """移除告警规则

        Args:
            rule_name: 规则名称
        """
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """添加告警回调

        Args:
            callback: 回调函数
        """
        self.alert_callbacks.append(callback)

    def get_metric_history(
        self,
        metric_name: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[tuple[datetime, float]]:
        """获取指标历史

        Args:
            metric_name: 指标名称
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            指标历史数据列表
        """
        if metric_name not in self.metrics:
            return []

        history = list(self.metrics[metric_name])

        # 过滤时间范围
        if start_time:
            history = [(ts, v) for ts, v in history if ts >= start_time]
        if end_time:
            history = [(ts, v) for ts, v in history if ts <= end_time]

        return history

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要

        Returns:
            性能摘要字典
        """
        if not self.performance_snapshots:
            return {}

        snapshots = list(self.performance_snapshots)

        # 计算统计值
        cpu_avg = np.mean([s.cpu_percent for s in snapshots])
        memory_avg = np.mean([s.memory_percent for s in snapshots])
        response_time_avg = np.mean([s.response_time for s in snapshots])
        throughput_avg = np.mean([s.throughput for s in snapshots])

        return {
            "cpu_avg": cpu_avg,
            "memory_avg": memory_avg,
            "avg_response_time": response_time_avg,
            "avg_throughput": throughput_avg,
            "total_alerts": len(self.alerts),
            "active_alerts": sum(1 for a in self.alerts.values() if not a.resolved_at),
            "monitoring_uptime": (
                (datetime.now() - snapshots[0].timestamp).seconds if snapshots else 0
            ),
        }
