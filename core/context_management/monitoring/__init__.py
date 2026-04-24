#!/usr/bin/env python3
"""
上下文管理系统 - Prometheus监控模块
Context Management Monitoring - Prometheus metrics export

监控指标:
- 上下文操作计数器（create、read、update、delete）
- 操作延迟直方图（P50、P95、P99）
- 缓存命中率统计
- 当前活跃上下文数量
- 错误率统计

作者: Athena平台团队
创建时间: 2026-04-24
版本: v1.0.0 "Phase 4"
"""

from .metrics import (
    ContextMetrics,
    get_metrics_registry,
    start_metrics_server,
    stop_metrics_server,
)
from .integrations import (
    monitor_context_operation,
    monitor_context_manager,
    track_operation_latency,
    increment_operation_counter,
    record_error,
)

__all__ = [
    # 核心类
    "ContextMetrics",
    # 函数
    "get_metrics_registry",
    "start_metrics_server",
    "stop_metrics_server",
    # 装饰器和集成
    "monitor_context_operation",
    "monitor_context_manager",
    "track_operation_latency",
    "increment_operation_counter",
    "record_error",
]
