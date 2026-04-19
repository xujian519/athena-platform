#!/usr/bin/env python3
from __future__ import annotations
"""
优化版监控告警模块 - 主模块类
Optimized Monitoring and Alerting Module - Main Module

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging

# 添加项目路径
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base_module import BaseModule

from .alert_manager import AlertManager
from .analyzer import PerformanceAnalyzer
from .collector import MetricsCollector
from .system_collector import SystemMetricsCollector
from .types import Alert, AlertLevel, AlertRule, MetricType, MetricValue

logger = logging.getLogger(__name__)


class OptimizedMonitoringModule(BaseModule):
    """优化版监控模块

    提供全方位的系统监控、性能分析和智能告警功能。
    """

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        """初始化监控模块

        Args:
            agent_id: 智能体ID
            config: 配置字典
        """
        super().__init__(agent_id, config)

        # 配置
        self.collection_interval = self.config.get("collection_interval", 10)
        self.retention_period = self.config.get("retention_period", 3600)
        self.evaluation_interval = self.config.get("evaluation_interval", 30)

        # 核心组件
        self.metrics_collector = MetricsCollector(self.config)
        self.system_collector = SystemMetricsCollector(self.metrics_collector)
        self.alert_manager = AlertManager(self.metrics_collector, self.config)
        self.performance_analyzer = PerformanceAnalyzer(self.metrics_collector, self.config)

        # 运行状态
        self.monitoring_active = False
        self.background_tasks: list[asyncio.Task] = []

        # 统计信息
        self.metrics_count = 0
        self.alerts_count = 0
        self.anomaly_count = 0

    async def _on_initialize(self) -> bool:
        """初始化监控模块"""
        try:
            # 设置告警回调
            self.alert_manager.add_alert_callback(self._on_alert)

            logger.info(f"✅ 监控模块初始化成功: {self.agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 监控模块初始化失败: {e}")
            return False

    async def _on_start(self) -> bool:
        """启动监控模块"""
        try:
            # 启动系统指标收集
            await self.system_collector.start()

            # 启动告警管理器
            await self.alert_manager.start()

            # 启动监控任务
            self.monitoring_active = True
            self.background_tasks.append(asyncio.create_task(self._monitoring_loop()))

            logger.info(f"✅ 监控模块启动成功: {self.agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 监控模块启动失败: {e}")
            return False

    async def _on_stop(self) -> bool:
        """停止监控模块"""
        try:
            self.monitoring_active = False

            # 取消后台任务
            for task in self.background_tasks:
                task.cancel()
            self.background_tasks.clear()

            # 停止告警管理器
            await self.alert_manager.stop()

            # 停止系统指标收集
            await self.system_collector.stop()

            logger.info(f"✅ 监控模块停止成功: {self.agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 监控模块停止失败: {e}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭监控模块"""
        try:
            # 确保已经停止
            if self.monitoring_active:
                await self._on_stop()

            logger.info(f"✅ 监控模块关闭成功: {self.agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 监控模块关闭失败: {e}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查各个组件状态
            if not self.monitoring_active:
                return False

            # 检查指标收集器
            return bool(self.metrics_collector.metrics)

        except Exception as e:
            logger.error(f"监控模块健康检查失败: {e}")
            return False

    async def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 记录监控指标
                self.metrics_collector.set_gauge("monitoring_metrics_count", self.metrics_count)
                self.metrics_collector.set_gauge("monitoring_alerts_count", self.alerts_count)
                self.metrics_collector.set_gauge("monitoring_anomaly_count", self.anomaly_count)

                # 更新统计
                self.metrics_count = len(self.metrics_collector.metrics)
                self.alerts_count = len(self.alert_manager.active_alerts)

                await asyncio.sleep(60)  # 每分钟更新一次

            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(60)

    def _on_alert(self, alert: Alert) -> Any:
        """处理告警

        Args:
            alert: 告警对象
        """
        self.alerts_count += 1

        # 根据告警级别处理
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(f"严重告警: {alert.message}")
        elif alert.level == AlertLevel.ERROR:
            logger.error(f"错误告警: {alert.message}")
        elif alert.level == AlertLevel.WARNING:
            logger.warning(f"警告告警: {alert.message}")
        else:
            logger.info(f"信息告警: {alert.message}")

    # 公共接口
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: dict[str, str] | None = None,
    ):
        """记录指标

        Args:
            name: 指标名称
            value: 指标值
            metric_type: 指标类型
            labels: 标签字典
        """
        if metric_type == MetricType.COUNTER:
            self.metrics_collector.record_counter(name, value, labels)
        elif metric_type == MetricType.GAUGE:
            self.metrics_collector.set_gauge(name, value, labels)
        elif metric_type == MetricType.HISTOGRAM:
            self.metrics_collector.record_histogram(name, value, labels)
        elif metric_type == MetricType.TIMER:
            self.metrics_collector.record_timer(name, value, labels)

    def get_metric(self, name: str, labels: dict[str, str] | None = None) -> MetricValue | None:
        """获取指标

        Args:
            name: 指标名称
            labels: 标签字典

        Returns:
            指标值对象
        """
        return self.metrics_collector.get_metric(name, labels)

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
        return self.metrics_collector.get_metrics_history(name, labels, start_time, end_time)

    def add_alert_rule(self, rule: AlertRule) -> None:
        """添加告警规则

        Args:
            rule: 告警规则对象
        """
        self.alert_manager.add_rule(rule)

    def remove_alert_rule(self, rule_id: str) -> None:
        """删除告警规则

        Args:
            rule_id: 规则ID
        """
        self.alert_manager.remove_rule(rule_id)

    def get_active_alerts(self) -> list[Alert]:
        """获取活跃告警

        Returns:
            活跃告警列表
        """
        return list(self.alert_manager.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> list[Alert]:
        """获取告警历史

        Args:
            limit: 返回数量限制

        Returns:
            告警历史列表
        """
        return self.alert_manager.alert_history[-limit:]

    def analyze_trend(
        self,
        metric_name: str,
        labels: dict[str, str] | None = None,
        period: timedelta = timedelta(hours=1),
    ) -> dict[str, Any]:
        """分析趋势

        Args:
            metric_name: 指标名称
            labels: 标签字典
            period: 分析周期

        Returns:
            趋势分析结果
        """
        return self.performance_analyzer.analyze_trend(metric_name, labels, period)

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
        anomalies = self.performance_analyzer.detect_anomalies(metric_name, labels, period)
        self.anomaly_count = len(anomalies)
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
        return self.performance_analyzer.generate_performance_report(period)

    def get_monitoring_status(self) -> dict[str, Any]:
        """获取监控状态

        Returns:
            监控状态字典
        """
        return {
            "monitoring_active": self.monitoring_active,
            "metrics_count": self.metrics_count,
            "active_alerts": self.alerts_count,
            "alert_rules": len(self.alert_manager.rules),
            "anomaly_count": self.anomaly_count,
            "collection_interval": self.collection_interval,
            "evaluation_interval": self.evaluation_interval,
        }
