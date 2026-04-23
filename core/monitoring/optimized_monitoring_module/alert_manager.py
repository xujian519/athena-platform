#!/usr/bin/env python3
from __future__ import annotations
"""
优化版监控告警模块 - 告警管理器
Optimized Monitoring and Alerting Module - Alert Manager

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from .collector import MetricsCollector
from .types import Alert, AlertLevel, AlertRule, AlertStatus, MetricValue

logger = logging.getLogger(__name__)


class AlertManager:
    """告警管理器

    负责管理告警规则、评估告警条件和触发告警。
    """

    def __init__(self, metrics_collector: MetricsCollector, config: Optional[dict[str, Any]] = None):
        """初始化告警管理器

        Args:
            metrics_collector: 指标收集器实例
            config: 配置字典
        """
        self.metrics_collector = metrics_collector
        self.config = config or {}
        self.rules: dict[str, AlertRule] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.alert_callbacks: list[Callable[[Alert], None]] = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=2)

        # 配置
        self.evaluation_interval = self.config.get("evaluation_interval", 30)  # 30秒评估一次
        self.max_alert_history = self.config.get("max_alert_history", 1000)

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则

        Args:
            rule: 告警规则对象
        """
        self.rules[rule.id] = rule
        logger.info(f"添加告警规则: {rule.name}")

    def remove_rule(self, rule_id: str) -> None:
        """删除告警规则

        Args:
            rule_id: 规则ID
        """
        if rule_id in self.rules:
            rule_name = self.rules[rule_id].name
            del self.rules[rule_id]
            logger.info(f"删除告警规则: {rule_name}")

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """添加告警回调

        Args:
            callback: 回调函数
        """
        self.alert_callbacks.append(callback)

    async def start(self):
        """启动告警管理器"""
        self.running = True

        # 加载默认规则
        self._load_default_rules()

        # 启动评估循环
        asyncio.create_task(self._evaluation_loop())

        logger.info("告警管理器启动成功")

    async def stop(self):
        """停止告警管理器"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("告警管理器停止成功")

    async def _evaluation_loop(self):
        """评估循环"""
        while self.running:
            try:
                await self._evaluate_rules()
                await asyncio.sleep(self.evaluation_interval)
            except Exception as e:
                logger.error(f"告警评估失败: {e}")
                await asyncio.sleep(self.evaluation_interval)

    async def _evaluate_rules(self):
        """评估所有规则"""
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            try:
                await self._evaluate_rule(rule)
            except Exception as e:
                logger.error(f"评估规则 {rule.name} 失败: {e}")

    async def _evaluate_rule(self, rule: AlertRule):
        """评估单个规则

        Args:
            rule: 告警规则对象
        """
        # 获取指标值
        metric = self.metrics_collector.get_metric(rule.metric_name, rule.labels)
        if not metric:
            return

        # 检查条件
        triggered = self._check_condition(metric.value, rule.condition, rule.threshold)

        alert_id = f"{rule.id}_{hash(rule.labels)}"

        if triggered:
            # 检查是否已经激活
            if alert_id not in self.active_alerts:
                # 检查持续时间
                if self._check_duration(rule, metric):
                    await self._trigger_alert(rule, metric)
            else:
                # 更新现有告警
                alert = self.active_alerts[alert_id]
                alert.metric_values.append(metric)
        else:
            # 检查是否需要解决告警
            if alert_id in self.active_alerts:
                await self._resolve_alert(alert_id)

    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """检查条件

        Args:
            value: 指标值
            condition: 条件运算符
            threshold: 阈值

        Returns:
            是否满足条件
        """
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        else:
            return False

    def _check_duration(self, rule: AlertRule, metric: MetricValue) -> bool:
        """检查持续时间

        Args:
            rule: 告警规则
            metric: 指标值

        Returns:
            是否满足持续时间要求
        """
        if rule.duration.total_seconds() <= 0:
            return True

        # 获取历史指标
        history = self.metrics_collector.get_metrics_history(
            rule.metric_name, rule.labels, start_time=datetime.now() - rule.duration
        )

        # 检查所有历史值是否都满足条件
        for hist_metric in history:
            if not self._check_condition(hist_metric.value, rule.condition, rule.threshold):
                return False

        return True

    async def _trigger_alert(self, rule: AlertRule, metric: MetricValue):
        """触发告警

        Args:
            rule: 告警规则
            metric: 触发告警的指标值
        """
        alert_id = f"{rule.id}_{hash(rule.labels)}"

        alert = Alert(
            id=alert_id,
            rule_id=rule.id,
            name=rule.name,
            description=rule.description,
            level=rule.level,
            status=AlertStatus.ACTIVE,
            message=f"{rule.name}: {rule.metric_name} {rule.condition} {rule.threshold}, 当前值: {metric.value}",
            timestamp=datetime.now(),
            metric_values=[metric],
            labels=rule.labels,
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # 限制历史记录数量
        if len(self.alert_history) > self.max_alert_history:
            self.alert_history = self.alert_history[-self.max_alert_history:]

        # 更新规则统计
        rule.last_triggered = datetime.now()
        rule.trigger_count += 1

        logger.warning(f"触发告警: {alert.message}")

        # 调用回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")

    async def _resolve_alert(self, alert_id: str):
        """解决告警

        Args:
            alert_id: 告警ID
        """
        if alert_id not in self.active_alerts:
            return

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()

        del self.active_alerts[alert_id]

        logger.info(f"解决告警: {alert.name}")

        # 调用回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")

    def _load_default_rules(self) -> Any:
        """加载默认规则"""
        default_rules = [
            AlertRule(
                id="cpu_high",
                name="CPU使用率过高",
                description="CPU使用率超过80%",
                metric_name="system_cpu_usage",
                condition=">",
                threshold=80,
                level=AlertLevel.WARNING,
            ),
            AlertRule(
                id="memory_high",
                name="内存使用率过高",
                description="内存使用率超过85%",
                metric_name="system_memory_usage",
                condition=">",
                threshold=85,
                level=AlertLevel.WARNING,
            ),
            AlertRule(
                id="disk_high",
                name="磁盘使用率过高",
                description="磁盘使用率超过90%",
                metric_name="system_disk_usage",
                condition=">",
                threshold=90,
                level=AlertLevel.ERROR,
            ),
            AlertRule(
                id="process_count_high",
                name="进程数过多",
                description="系统进程数超过500",
                metric_name="system_process_count",
                condition=">",
                threshold=500,
                level=AlertLevel.WARNING,
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)
