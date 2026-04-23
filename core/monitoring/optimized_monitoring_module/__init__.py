#!/usr/bin/env python3
from __future__ import annotations
"""
优化版监控告警模块 - 公共接口
Optimized Monitoring and Alerting Module - Public Interface

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

提供全方位的系统监控、性能分析和智能告警功能。
"""
import logging
from typing import Any

from .alert_manager import AlertManager
from .analyzer import PerformanceAnalyzer
from .collector import MetricsCollector
from .module import OptimizedMonitoringModule
from .system_collector import SystemMetricsCollector
from .types import Alert, AlertLevel, AlertRule, AlertStatus, MetricType, MetricValue

logger = logging.getLogger(__name__)


# 便捷函数
def create_monitoring_module(
    agent_id: str, config: Optional[dict[str, Any]] = None
) -> OptimizedMonitoringModule:
    """创建监控模块

    Args:
        agent_id: 智能体ID
        config: 配置字典

    Returns:
        监控模块实例
    """
    return OptimizedMonitoringModule(agent_id, config)


def create_alert_rule(
    id: str,
    name: str,
    metric_name: str,
    condition: str,
    threshold: float,
    level: AlertLevel = AlertLevel.WARNING,
    description: str = "",
) -> AlertRule:
    """创建告警规则

    Args:
        id: 规则ID
        name: 规则名称
        metric_name: 监控的指标名称
        condition: 条件运算符
        threshold: 阈值
        level: 告警级别
        description: 规则描述

    Returns:
        告警规则对象
    """
    return AlertRule(
        id=id,
        name=name,
        description=description,
        metric_name=metric_name,
        condition=condition,
        threshold=threshold,
        level=level,
    )


# 测试代码
if __name__ == "__main__":
    async def test_monitoring():
        """测试监控模块"""
        monitoring = create_monitoring_module("test_monitoring")

        if await monitoring.initialize():
            if await monitoring.start():
                # 记录一些测试指标
                monitoring.record_metric("test_metric", 100, MetricType.GAUGE)
                monitoring.record_metric("test_counter", 1, MetricType.COUNTER)

                # 添加告警规则
                rule = create_alert_rule(
                    id="test_rule",
                    name="测试告警",
                    metric_name="test_metric",
                    condition=">",
                    threshold=50,
                    level=AlertLevel.WARNING,
                )
                monitoring.add_alert_rule(rule)

                # 等待告警触发
                await asyncio.sleep(60)

                # 获取监控状态
                status = monitoring.get_monitoring_status()
                logger.info(f"监控状态: {status}")

                await monitoring.stop()
            await monitoring.shutdown()

    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_monitoring())


# 导出公共接口
__all__ = [
    # 类型定义
    "MetricType",
    "AlertLevel",
    "AlertStatus",
    "MetricValue",
    "AlertRule",
    "Alert",
    # 核心类
    "MetricsCollector",
    "SystemMetricsCollector",
    "AlertManager",
    "PerformanceAnalyzer",
    "OptimizedMonitoringModule",
    # 便捷函数
    "create_monitoring_module",
    "create_alert_rule",
]
