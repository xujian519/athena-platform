"""
性能优化模块 - Performance Optimization Module

提供多级缓存、查询批处理、性能监控和报告等功能
"""

# 性能监控(原有)
from __future__ import annotations
from core.performance.monitor import (
    Alert,
    AlertLevel,
    Colors,
    # 数据类
    Metric,
    # 枚举
    MetricType,
    # 核心类
    PerformanceMonitor,
    TerminalReporter,
    generate_report,
    # 便捷函数
    get_performance_monitor,
    get_terminal_reporter,
    increment_counter,
    observe_histogram,
    print_dashboard,
    set_gauge,
    show_live_dashboard,
    track_time,
)

# 查询优化(新增)
from core.performance.query_optimizer import (
    CacheLevel,
    LRUCache,
    MultiLevelCache,
    PerformanceMetrics,
    PerformanceOptimizer,
    QueryBatcher,
    get_global_optimizer,
    monitor_performance,
    optimized_query,
)

__all__ = [
    "Alert",
    "AlertLevel",
    # ===== 查询优化(新增) =====
    "CacheLevel",
    "Colors",
    "LRUCache",
    # 数据类
    "Metric",
    # ===== 性能监控(原有) =====
    # 枚举
    "MetricType",
    "MultiLevelCache",
    "PerformanceMetrics",
    # 核心类
    "PerformanceMonitor",
    "PerformanceOptimizer",
    "QueryBatcher",
    "TerminalReporter",
    "generate_report",
    "get_global_optimizer",
    # 便捷函数
    "get_performance_monitor",
    "get_terminal_reporter",
    "increment_counter",
    "monitor_performance",
    "observe_histogram",
    "optimized_query",
    "print_dashboard",
    "set_gauge",
    "show_live_dashboard",
    "track_time",
]
