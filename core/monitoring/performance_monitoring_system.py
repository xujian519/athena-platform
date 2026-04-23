#!/usr/bin/env python3
from __future__ import annotations
"""
完整性能监控体系
Comprehensive Performance Monitoring System

全方位的系统性能监控:
1. 实时性能指标采集
2. 多维度监控仪表板
3. 智能告警系统
4. 性能趋势分析
5. 根因分析
6. 自动化报告生成

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "完整监控"
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """指标类别"""

    PERFORMANCE = "performance"  # 性能指标
    AVAILABILITY = "availability"  # 可用性指标
    QUALITY = "quality"  # 质量指标
    RESOURCE = "resource"  # 资源指标
    BUSINESS = "business"  # 业务指标


class AlertSeverity(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """指标数据"""

    name: str
    category: MetricCategory
    value: float
    unit: str
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """告警规则"""

    rule_id: str
    name: str
    metric_name: str
    condition: Callable[[float], bool]
    severity: AlertSeverity
    message_template: str
    cooldown: float = 300  # 冷却时间(秒)
    last_triggered: datetime | None = None


@dataclass
class Alert:
    """告警"""

    alert_id: str
    rule: AlertRule
    metric_value: float
    triggered_at: datetime
    resolved: bool = False
    resolved_at: datetime | None = None
    acknowledged: bool = False


@dataclass
class PerformanceSnapshot:
    """性能快照"""

    timestamp: datetime
    metrics: dict[str, float]
    health_score: float
    alerts: list[str]


class PerformanceMonitoringSystem:
    """
    性能监控系统

    核心功能:
    1. 指标采集
    2. 实时监控
    3. 告警管理
    4. 趋势分析
    5. 仪表板
    6. 报告生成
    """

    def __init__(self):
        # 指标存储
        self.metrics_buffer: dict[str, deque[MetricData]] = defaultdict(lambda: deque(maxlen=10000))

        # 告警规则
        self.alert_rules: list[AlertRule] = []

        # 活跃告警
        self.active_alerts: dict[str, Alert] = {}

        # 告警历史
        self.alert_history: list[Alert] = []

        # 监控仪表板数据
        self.dashboard_data: dict[str, Any] = {}

        # 回调函数
        self.alert_callbacks: list[Callable] = []

        # 统计信息
        self.metrics = {
            "metrics_collected": 0,
            "alerts_triggered": 0,
            "alerts_resolved": 0,
            "false_alarms": 0,
        }

        # 初始化默认告警规则
        self._initialize_default_alert_rules()

        logger.info("📊 性能监控系统初始化完成")

    def _initialize_default_alert_rules(self) -> Any:
        """初始化默认告警规则"""
        default_rules = [
            AlertRule(
                rule_id="high_response_time",
                name="响应时间过高",
                metric_name="response_time",
                condition=lambda x: x > 5.0,  # 5秒
                severity=AlertSeverity.WARNING,
                message_template="响应时间超过5秒: {value:.2f}秒",
            ),
            AlertRule(
                rule_id="low_success_rate",
                name="成功率过低",
                metric_name="success_rate",
                condition=lambda x: x < 0.8,  # 80%
                severity=AlertSeverity.ERROR,
                message_template="成功率低于80%: {value:.1%}",
            ),
            AlertRule(
                rule_id="high_error_rate",
                name="错误率过高",
                metric_name="error_rate",
                condition=lambda x: x > 0.1,  # 10%
                severity=AlertSeverity.CRITICAL,
                message_template="错误率超过10%: {value:.1%}",
            ),
            AlertRule(
                rule_id="high_memory_usage",
                name="内存使用率过高",
                metric_name="memory_usage",
                condition=lambda x: x > 0.9,  # 90%
                severity=AlertSeverity.WARNING,
                message_template="内存使用率超过90%: {value:.1%}",
            ),
            AlertRule(
                rule_id="high_cpu_usage",
                name="CPU使用率过高",
                metric_name="cpu_usage",
                condition=lambda x: x > 0.8,  # 80%
                severity=AlertSeverity.WARNING,
                message_template="CPU使用率超过80%: {value:.1%}",
            ),
        ]

        self.alert_rules.extend(default_rules)

    async def collect_metric(
        self,
        name: str,
        value: float,
        category: MetricCategory,
        unit: str = "",
        labels: dict[str, str] | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """采集指标"""
        metric = MetricData(
            name=name,
            category=category,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            labels=labels or {},
            metadata=metadata or {},
        )

        self.metrics_buffer[name].append(metric)
        self.metrics["metrics_collected"] += 1

        # 检查告警
        await self._check_alerts(metric)

    async def _check_alerts(self, metric: MetricData):
        """检查告警条件"""
        for rule in self.alert_rules:
            # 检查规则是否匹配
            if rule.metric_name != metric.name:
                continue

            # 检查冷却时间
            if rule.last_triggered:
                time_since_last = (datetime.now() - rule.last_triggered).total_seconds()
                if time_since_last < rule.cooldown:
                    continue

            # 检查条件
            if rule.condition(metric.value):
                await self._trigger_alert(rule, metric)

    async def _trigger_alert(self, rule: AlertRule, metric: MetricData):
        """触发告警"""
        alert_id = f"alert_{int(time.time())}_{rule.rule_id}"

        alert = Alert(
            alert_id=alert_id, rule=rule, metric_value=metric.value, triggered_at=datetime.now()
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        rule.last_triggered = datetime.now()

        self.metrics["alerts_triggered"] += 1

        # 格式化消息
        message = rule.message_template.format(value=metric.value)

        logger.warning(f"🚨 告警触发: [{rule.severity.value.upper()}] " f"{rule.name} - {message}")

        # 调用回调
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"❌ 告警回调失败: {e}")

    async def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id not in self.active_alerts:
            logger.warning(f"⚠️ 告警不存在或已解决: {alert_id}")
            return

        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now()

        # 移到历史(保留记录)
        del self.active_alerts[alert_id]

        self.metrics["alerts_resolved"] += 1

        logger.info(f"✅ 告警已解决: {alert.rule.name}")

    async def get_dashboard_data(self) -> dict[str, Any]:
        """获取仪表板数据"""
        # 计算健康分数
        health_score = await self._calculate_health_score()

        # 聚合指标
        summary_metrics = await self._get_summary_metrics()

        # 活跃告警统计
        alert_stats = {
            "total": len(self.active_alerts),
            "by_severity": defaultdict(int),
            "recent": len(
                [
                    a
                    for a in self.active_alerts.values()
                    if (datetime.now() - a.triggered_at).total_seconds() < 3600
                ]
            ),
        }

        for alert in self.active_alerts.values():
            alert_stats["by_severity"][alert.rule.severity.value] += 1

        # 性能趋势
        trends = await self._get_performance_trends()

        self.dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "health_score": health_score,
            "metrics": summary_metrics,
            "alerts": alert_stats,
            "trends": trends,
            "uptime": await self._calculate_uptime(),
        }

        return self.dashboard_data

    async def _calculate_health_score(self) -> float:
        """计算健康分数(0-1)"""
        score = 1.0

        # 基于活跃告警扣分
        for alert in self.active_alerts.values():
            if alert.rule.severity == AlertSeverity.CRITICAL:
                score -= 0.3
            elif alert.rule.severity == AlertSeverity.ERROR:
                score -= 0.2
            elif alert.rule.severity == AlertSeverity.WARNING:
                score -= 0.1
            elif alert.rule.severity == AlertSeverity.INFO:
                score -= 0.05

        # 基于近期错误率
        if "error_rate" in self.metrics_buffer:
            recent_errors = list(self.metrics_buffer["error_rate"])[-100:]
            if recent_errors:
                avg_error_rate = sum(m.value for m in recent_errors) / len(recent_errors)
                score -= avg_error_rate * 0.5

        return max(0, min(score, 1))

    async def _get_summary_metrics(self) -> dict[str, Any]:
        """获取汇总指标"""
        summary = {}

        # 计算每个指标类别的汇总
        for metric_name, buffer in self.metrics_buffer.items():
            if not buffer:
                continue

            recent = list(buffer)[-100:]
            if recent:
                values = [m.value for m in recent]
                summary[metric_name] = {
                    "current": values[-1],
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        return summary

    async def _get_performance_trends(self) -> dict[str, str]:
        """获取性能趋势"""
        trends = {}

        for metric_name, buffer in self.metrics_buffer.items():
            if len(buffer) < 20:
                continue

            recent = list(buffer)[-100:]

            # 计算趋势(简单线性回归)
            values = [m.value for m in recent]
            n = len(values)

            x = list(range(n))
            y = values

            # 计算斜率
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y, strict=False))
            sum_x2 = sum(xi * xi for xi in x)

            if n * sum_x2 - sum_x**2 != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)

                # 判断趋势
                if slope > 0.01:
                    trends[metric_name] = "increasing"
                elif slope < -0.01:
                    trends[metric_name] = "decreasing"
                else:
                    trends[metric_name] = "stable"

        return trends

    async def _calculate_uptime(self) -> float:
        """计算系统可用时间"""
        # 简化实现:基于成功率和错误率
        if "success_rate" in self.metrics_buffer:
            recent = list(self.metrics_buffer["success_rate"])[-100:]
            if recent:
                return sum(m.value for m in recent) / len(recent)

        return 1.0  # 默认100%

    async def generate_report(
        self, duration: str = "1h", format: str = "summary"
    ) -> dict[str, Any]:
        """生成性能报告"""
        # 解析时长
        duration_seconds = self._parse_duration(duration)

        cutoff_time = datetime.now() - timedelta(seconds=duration_seconds)

        # 收集时间范围内的数据
        report_data = {
            "period": duration,
            "start_time": cutoff_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "summary": {},
            "metrics": {},
            "alerts": {"total": 0, "triggered": 0, "resolved": 0, "active": 0},
            "recommendations": [],
        }

        # 指标统计
        for metric_name, buffer in self.metrics_buffer.items():
            in_period = [m for m in buffer if m.timestamp >= cutoff_time]

            if in_period:
                values = [m.value for m in in_period]
                report_data["metrics"][metric_name] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        # 告警统计
        period_alerts = [a for a in self.alert_history if a.triggered_at >= cutoff_time]

        report_data["alerts"]["triggered"] = len(period_alerts)
        report_data["alerts"]["resolved"] = sum(1 for a in period_alerts if a.resolved)
        report_data["alerts"]["active"] = len(
            [a for a in self.active_alerts.values() if a.triggered_at >= cutoff_time]
        )

        # 生成建议
        report_data["recommendations"] = await self._generate_recommendations(report_data)

        return report_data

    def _parse_duration(self, duration: str) -> int:
        """解析时长字符串为秒数"""
        duration = duration.lower()

        if duration.endswith("s"):
            return int(duration[:-1])
        elif duration.endswith("m"):
            return int(duration[:-1]) * 60
        elif duration.endswith("h"):
            return int(duration[:-1]) * 3600
        elif duration.endswith("d"):
            return int(duration[:-1]) * 86400
        else:
            return 3600  # 默认1小时

    async def _generate_recommendations(self, report_data: dict[str, Any]) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 基于指标生成建议
        metrics = report_data.get("metrics", {})

        if "response_time" in metrics:
            avg_response_time = metrics["response_time"]["avg"]
            if avg_response_time > 3:
                recommendations.append(
                    f"平均响应时间较高({avg_response_time:.2f}秒),建议优化数据库查询或增加缓存"
                )

        if "success_rate" in metrics:
            avg_success_rate = metrics["success_rate"]["avg"]
            if avg_success_rate < 0.9:
                recommendations.append(
                    f"成功率为{avg_success_rate:.1%},建议检查错误日志并修复高频错误"
                )

        if "memory_usage" in metrics:
            avg_memory = metrics["memory_usage"]["avg"]
            if avg_memory > 0.8:
                recommendations.append(f"内存使用率{avg_memory:.1%}较高,建议进行内存优化或扩容")

        if "error_rate" in metrics:
            avg_error_rate = metrics["error_rate"]["avg"]
            if avg_error_rate > 0.05:
                recommendations.append(f"错误率{avg_error_rate:.1%}较高,建议检查系统稳定性")

        return recommendations

    def register_alert_callback(self, callback: Callable) -> Any:
        """注册告警回调"""
        self.alert_callbacks.append(callback)
        logger.info("📢 告警回调已注册")

    async def start_monitoring(self, interval: float = 60):
        """启动监控循环"""
        logger.info(f"🔄 启动监控循环 (间隔: {interval}秒)")

        while True:
            try:
                # 采集系统指标
                await self._collect_system_metrics()

                # 更新仪表板
                await self.get_dashboard_data()

                # 等待下次采集
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"❌ 监控循环异常: {e}")
                await asyncio.sleep(60)

    async def _collect_system_metrics(self):
        """采集系统指标"""
        # 简化实现:模拟系统指标采集
        import psutil

        # CPU使用率
        cpu_usage = psutil.cpu_percent() / 100
        await self.collect_metric(
            "cpu_usage", cpu_usage, MetricCategory.RESOURCE, "", labels={"host": "system"}
        )

        # 内存使用率
        memory = psutil.virtual_memory()
        await self.collect_metric(
            "memory_usage",
            memory.percent / 100,
            MetricCategory.RESOURCE,
            "",
            labels={"host": "system"},
        )

        # 磁盘使用率
        disk = psutil.disk_usage("/")
        await self.collect_metric(
            "disk_usage", disk.percent / 100, MetricCategory.RESOURCE, "", labels={"path": "/"}
        )

    async def get_monitoring_metrics(self) -> dict[str, Any]:
        """获取监控统计"""
        return {
            "collection": {
                "total_metrics": self.metrics["metrics_collected"],
                "metrics_tracked": len(self.metrics_buffer),
            },
            "alerts": {
                "total_triggered": self.metrics["alerts_triggered"],
                "total_resolved": self.metrics["alerts_resolved"],
                "active": len(self.active_alerts),
                "history": len(self.alert_history),
            },
            "rules": {"configured": len(self.alert_rules), "callbacks": len(self.alert_callbacks)},
        }


# 导出便捷函数
_monitoring_system: PerformanceMonitoringSystem | None = None


def get_monitoring_system() -> PerformanceMonitoringSystem:
    """获取监控系统单例"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = PerformanceMonitoringSystem()
    return _monitoring_system
