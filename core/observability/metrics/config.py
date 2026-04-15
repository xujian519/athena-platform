#!/usr/bin/env python3
from __future__ import annotations
"""
Prometheus配置
Prometheus Configuration

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

# =============================================================================
# Prometheus配置
# =============================================================================

PROMETHEUS_CONFIG = {
    # 服务配置
    "host": "0.0.0.0",
    "port": 9090,

    # 指标暴露路径
    "metrics_path": "/metrics",

    # 聚合窗口（秒）
    "aggregation_window": 60,

    # 是否启用默认指标
    "enable_default_metrics": True,

    # 指标保留时间（秒）
    "metrics_retention": 86400,  # 24小时
}


# =============================================================================
# 指标命名规范
# =============================================================================

METRICS_NAMING_CONVENTIONS = {
    # 单位后缀
    "units": {
        "seconds": "_seconds",
        "bytes": "_bytes",
        "percent": "_percent",
        "count": "_total",  # Counter
    },

    # 指标类型后缀
    "types": {
        "counter": "_total",
        "gauge": "_current",
        "histogram": "_bucket",
        "summary": "_summary",
    },

    # 示例
    "examples": {
        "http_requests_total": "HTTP请求总数（Counter）",
        "http_request_duration_seconds": "HTTP请求延迟（Histogram）",
        "active_connections": "活跃连接数（Gauge）",
    }
}


# =============================================================================
# 默认标签
# =============================================================================

DEFAULT_LABELS = {
    "service": "athena-platform",
    "environment": "production",
    "version": "1.0.0",
}


# =============================================================================
# 直方图默认分桶
# =============================================================================

DEFAULT_HISTOGRAM_BUCKETS = {
    "duration": (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')),
    "size": (1024, 10240, 102400, 1024000, 10240000, 102400000),
    "count": (1, 5, 10, 50, 100, 500, 1000, 5000, 10000),
}
