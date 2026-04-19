#!/usr/bin/env python3
from __future__ import annotations
"""
实时执行监控系统 - 向后兼容重定向
Real-time Execution Monitoring System - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.execution.real_time_monitor (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.execution.real_time_monitor import (
        RealTimeMonitor,
        MetricType,
        AlertLevel,
        Metric,
        Alert,
        PerformanceSnapshot,
        MonitoringConfig,
        CPUMonitor,
        MemoryMonitor,
        DiskMonitor,
        NetworkMonitor,
        ResourceMonitor,
        real_time_monitor,
        start_real_time_monitoring,
        stop_real_time_monitoring,
        record_custom_metric,
        get_monitoring_summary,
    )

新导入方式:
    from core.execution.real_time_monitor import (
        RealTimeMonitor,
        MetricType,
        AlertLevel,
        Metric,
        Alert,
        PerformanceSnapshot,
        MonitoringConfig,
        CPUMonitor,
        MemoryMonitor,
        DiskMonitor,
        NetworkMonitor,
        ResourceMonitor,
        real_time_monitor,
        start_real_time_monitoring,
        stop_real_time_monitoring,
        record_custom_metric,
        get_monitoring_summary,
    )

⚠️  注意: 导入语句保持不变，但代码现在从模块化目录加载。
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

import warnings

# 导入重构后的模块
from .real_time_monitor import (
    Alert,
    AlertLevel,
    CPUMonitor,
    DiskMonitor,
    MemoryMonitor,
    Metric,
    MetricType,
    MonitoringConfig,
    NetworkMonitor,
    PerformanceSnapshot,
    RealTimeMonitor,
    ResourceMonitor,
    ResourceStatus,
    _RealTimeMonitorWithWebSocket,
    get_monitoring_summary,
    real_time_monitor,
    record_custom_metric,
    start_real_time_monitoring,
    stop_real_time_monitoring,
)

# 发出弃用警告
warnings.warn(
    "real_time_monitor.py 已重构为模块化目录 "
    "core.execution.real_time_monitor/。"
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
    "ResourceStatus",
    "Metric",
    "Alert",
    "PerformanceSnapshot",
    "MonitoringConfig",
    # 资源监控器
    "ResourceMonitor",
    "CPUMonitor",
    "MemoryMonitor",
    "DiskMonitor",
    "NetworkMonitor",
    # 主监控类
    "RealTimeMonitor",
    "_RealTimeMonitorWithWebSocket",
    # 全局实例和便捷函数
    "real_time_monitor",
    "start_real_time_monitoring",
    "stop_real_time_monitoring",
    "record_custom_metric",
    "get_monitoring_summary",
]
