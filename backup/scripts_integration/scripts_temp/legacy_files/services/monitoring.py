#!/usr/bin/env python3
"""
监控服务
提供系统监控、性能指标和告警功能
"""

import time
import psutil
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import json

from core.config import config
from utils.logger import ScriptLogger


@dataclass
class MetricValue:
    """指标值"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    labels: Dict[str, str] = None


@dataclass
class Alert:
    """告警"""
    id: str
    name: str
    level: str  # info, warning, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: datetime | None = None


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.metrics: Dict[str, deque] = {}
        self.logger = ScriptLogger("MetricsCollector")

    def add_metric(self, metric: MetricValue):
        """添加指标"""
        if metric.name not in self.metrics:
            self.metrics[metric.name] = deque(maxlen=self.max_points)

        self.metrics[metric.name].append(metric)

    def get_metrics(self, name: str,
                   start_time: datetime | None = None,
                   end_time: datetime | None = None) -> List[MetricValue]:
        """获取指标"""
        if name not in self.metrics:
            return []

        metrics = list(self.metrics[name])

        # 时间过滤
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]

        return metrics

    def get_latest(self, name: str) -> MetricValue | None:
        """获取最新指标值"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        return self.metrics[name][-1]

    def get_average(self, name: str,
                   duration_minutes: int = 5) -> float | None:
        """获取平均值"""
        start_time = datetime.now() - timedelta(minutes=duration_minutes)
        metrics = self.get_metrics(name, start_time=start_time)

        if not metrics:
            return None

        return sum(m.value for m in metrics) / len(metrics)

    def clear_metrics(self, name: str = None):
        """清除指标"""
        if name:
            if name in self.metrics:
                del self.metrics[name]
        else:
            self.metrics.clear()


class MonitoringService:
    """监控服务"""

    def __init__(self):
        self.logger = ScriptLogger("MonitoringService")
        self.metrics_collector = MetricsCollector()
        self.alerts: Dict[str, Alert] = {}
        self.alert_callbacks: List[Callable] = []
        self.rules: Dict[str, Dict] = {}
        self.running = False

        # 系统监控配置
        self.system_metrics_interval = config.get('monitoring.system_interval', 30)
        self.alert_check_interval = config.get('monitoring.alert_interval', 10)

    def add_alert_callback(self, callback: Callable):
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def add_rule(self, rule_id: str, rule_config: Dict):
        """添加告警规则"""
        self.rules[rule_id] = {
            'metric': rule_config['metric'],
            'condition': rule_config['condition'],  # gt, lt, eq
            'threshold': rule_config['threshold'],
            'duration': rule_config.get('duration', 60),  # 持续时间(秒)
            'level': rule_config.get('level', 'warning'),
            'message': rule_config.get('message', ''),
            'enabled': rule_config.get('enabled', True)
        }
        self.logger.info(f"添加告警规则: {rule_id}")

    def remove_rule(self, rule_id: str):
        """移除告警规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.logger.info(f"移除告警规则: {rule_id}")

    async def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.add_metric(MetricValue(
                name='system_cpu_percent',
                value=cpu_percent,
                unit='percent',
                timestamp=datetime.now()
            ))

            # 内存使用率
            memory = psutil.virtual_memory()
            self.metrics_collector.add_metric(MetricValue(
                name='system_memory_percent',
                value=memory.percent,
                unit='percent',
                timestamp=datetime.now()
            ))
            self.metrics_collector.add_metric(MetricValue(
                name='system_memory_used',
                value=memory.used / 1024 / 1024 / 1024,  # GB
                unit='GB',
                timestamp=datetime.now()
            ))

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.used / disk.total * 100
            self.metrics_collector.add_metric(MetricValue(
                name='system_disk_percent',
                value=disk_percent,
                unit='percent',
                timestamp=datetime.now()
            ))

            # 网络IO
            net_io = psutil.net_io_counters()
            self.metrics_collector.add_metric(MetricValue(
                name='network_bytes_sent',
                value=net_io.bytes_sent,
                unit='bytes',
                timestamp=datetime.now()
            ))
            self.metrics_collector.add_metric(MetricValue(
                name='network_bytes_recv',
                value=net_io.bytes_recv,
                unit='bytes',
                timestamp=datetime.now()
            ))

            # 进程数
            process_count = len(psutil.pids())
            self.metrics_collector.add_metric(MetricValue(
                name='system_process_count',
                value=process_count,
                unit='count',
                timestamp=datetime.now()
            ))

        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")

    async def check_alert_rules(self):
        """检查告警规则"""
        for rule_id, rule in self.rules.items():
            if not rule['enabled']:
                continue

            try:
                # 获取指标
                latest_metric = self.metrics_collector.get_latest(rule['metric'])
                if not latest_metric:
                    continue

                # 检查条件
                triggered = False
                if rule['condition'] == 'gt' and latest_metric.value > rule['threshold']:
                    triggered = True
                elif rule['condition'] == 'lt' and latest_metric.value < rule['threshold']:
                    triggered = True
                elif rule['condition'] == 'eq' and latest_metric.value == rule['threshold']:
                    triggered = True

                if triggered:
                    # 检查是否已经存在未解决的告警
                    if rule_id not in self.alerts or not self.alerts[rule_id].resolved:
                        # 创建或更新告警
                        message = rule['message'] or f"{rule['metric']} {rule['condition']} {rule['threshold']}"

                        alert = Alert(
                            id=rule_id,
                            name=rule_id,
                            level=rule['level'],
                            message=message,
                            timestamp=datetime.now(),
                            resolved=False
                        )

                        self.alerts[rule_id] = alert
                        self.logger.warning(f"触发告警: {rule_id} - {message}")

                        # 调用回调
                        for callback in self.alert_callbacks:
                            try:
                                await callback(alert)
                            except Exception as e:
                                self.logger.error(f"告警回调失败: {e}")

                else:
                    # 恢复告警
                    if rule_id in self.alerts and not self.alerts[rule_id].resolved:
                        self.alerts[rule_id].resolved = True
                        self.alerts[rule_id].resolved_at = datetime.now()
                        self.logger.info(f"告警恢复: {rule_id}")

            except Exception as e:
                self.logger.error(f"检查告警规则 {rule_id} 失败: {e}")

    async def start_monitoring(self):
        """开始监控"""
        self.running = True
        self.logger.info("开始系统监控...")

        # 添加默认告警规则
        self._add_default_rules()

        while self.running:
            try:
                # 收集系统指标
                await self.collect_system_metrics()

                # 检查告警规则
                await self.check_alert_rules()

                # 等待下次收集
                await asyncio.sleep(self.system_metrics_interval)

            except Exception as e:
                self.logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(5)

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        self.logger.info("停止系统监控")

    def _add_default_rules(self):
        """添加默认告警规则"""
        default_rules = {
            'high_cpu': {
                'metric': 'system_cpu_percent',
                'condition': 'gt',
                'threshold': 80,
                'level': 'warning',
                'message': 'CPU使用率过高'
            },
            'high_memory': {
                'metric': 'system_memory_percent',
                'condition': 'gt',
                'threshold': 85,
                'level': 'warning',
                'message': '内存使用率过高'
            },
            'high_disk': {
                'metric': 'system_disk_percent',
                'condition': 'gt',
                'threshold': 90,
                'level': 'critical',
                'message': '磁盘使用率过高'
            }
        }

        for rule_id, rule_config in default_rules.items():
            if rule_id not in self.rules:
                self.add_rule(rule_id, rule_config)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}

        # 系统指标
        for metric_name in ['system_cpu_percent', 'system_memory_percent', 'system_disk_percent']:
            latest = self.metrics_collector.get_latest(metric_name)
            if latest:
                summary[metric_name] = {
                    'current': latest.value,
                    'unit': latest.unit,
                    'timestamp': latest.timestamp.isoformat()
                }

                # 5分钟平均值
                avg_5m = self.metrics_collector.get_average(metric_name, 5)
                if avg_5m is not None:
                    summary[metric_name]['avg_5m'] = avg_5m

        return summary

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts.values() if not alert.resolved]

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """获取告警历史"""
        start_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts.values()
            if alert.timestamp >= start_time
        ]

    def generate_monitoring_report(self) -> str:
        """生成监控报告"""
        metrics_summary = self.get_metrics_summary()
        active_alerts = self.get_active_alerts()

        report = [
            "=" * 60,
            "📊 系统监控报告",
            "=" * 60,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📈 系统指标:",
            "-" * 40
        ]

        # 系统指标
        if 'system_cpu_percent' in metrics_summary:
            cpu = metrics_summary['system_cpu_percent']
            report.append(f"CPU使用率:     {cpu['current']:.1f}% (平均: {cpu.get('avg_5m', 0):.1f}%)")

        if 'system_memory_percent' in metrics_summary:
            memory = metrics_summary['system_memory_percent']
            report.append(f"内存使用率:   {memory['current']:.1f}% (平均: {memory.get('avg_5m', 0):.1f}%)")

        if 'system_disk_percent' in metrics_summary:
            disk = metrics_summary['system_disk_percent']
            report.append(f"磁盘使用率:   {disk['current']:.1f}%")

        # 告警信息
        report.append("")
        report.append("🚨 告警信息:")
        report.append(f"活跃告警数: {len(active_alerts)}")

        if active_alerts:
            report.append("-" * 40)
            for alert in active_alerts:
                level_icon = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'critical': '🔴'
                }.get(alert.level, '❓')

                report.append(
                    f"{level_icon} {alert.name}: {alert.message} "
                    f"({alert.level}) - {alert.timestamp.strftime('%H:%M:%S')}"
                )

        report.append("=" * 60)
        return "\n".join(report)


# 全局实例
monitoring_service = MonitoringService()