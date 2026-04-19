#!/usr/bin/env python3
from __future__ import annotations
"""
优化版监控告警模块 - 向后兼容重定向
Optimized Monitoring and Alerting Module - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.monitoring.optimized_monitoring_module (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.monitoring.optimized_monitoring_module import (
        MetricType,
        AlertLevel,
        AlertStatus,
        MetricValue,
        AlertRule,
        Alert,
        MetricsCollector,
        SystemMetricsCollector,
        AlertManager,
        PerformanceAnalyzer,
        OptimizedMonitoringModule,
        create_monitoring_module,
        create_alert_rule,
    )

新导入方式:
    from core.monitoring.optimized_monitoring_module import (
        MetricType,
        AlertLevel,
        AlertStatus,
        MetricValue,
        AlertRule,
        Alert,
        MetricsCollector,
        SystemMetricsCollector,
        AlertManager,
        PerformanceAnalyzer,
        OptimizedMonitoringModule,
        create_monitoring_module,
        create_alert_rule,
    )

⚠️  注意: 导入语句保持不变，但代码现在从模块化目录加载。
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

import warnings

# 导入重构后的模块
from .optimized_monitoring_module import (
    Alert,
    AlertLevel,
    AlertManager,
    AlertRule,
    AlertStatus,
    MetricsCollector,
    MetricType,
    MetricValue,
    OptimizedMonitoringModule,
    PerformanceAnalyzer,
    SystemMetricsCollector,
    create_alert_rule,
    create_monitoring_module,
)

# 发出弃用警告
warnings.warn(
    "optimized_monitoring_module.py 已重构为模块化目录 "
    "core.monitoring.optimized_monitoring_module/。"
    "导入接口保持不变，代码现在从模块化目录加载。"
    "详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
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
