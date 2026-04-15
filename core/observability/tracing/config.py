#!/usr/bin/env python3
from __future__ import annotations
"""
OpenTelemetry配置
OpenTelemetry Configuration

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

# =============================================================================
# OpenTelemetry配置
# =============================================================================

OPENTELEMETRY_CONFIG = {
    # 服务配置
    "service_name": "athena-platform",
    "environment": "production",  # development | staging | production

    # 采样配置
    "sample_rate": 1.0,  # 1.0 = 100%采样, 0.1 = 10%采样

    # 导出器配置
    "exporter": "console",  # console | jaeger | otlp
    "jaeger_endpoint": "http://localhost:14250/api/traces",
    "otlp_endpoint": "localhost:4317",

    # 批量导出配置
    "enable_batch_export": True,
    "batch_export_schedule_delay": 5000,  # 毫秒
    "batch_export_max_queue_size": 2048,
    "batch_export_max_export_batch_size": 512,

    # 其他配置
    "enable_auto_instrumentation": False,  # 是否启用自动插桩
    "trace_id_ratio_based": 1.0,  # 基于Trace ID的采样率
}


# =============================================================================
# 环境特定配置
# =============================================================================

ENVIRONMENT_CONFIG = {
    "development": {
        "sample_rate": 1.0,  # 开发环境：100%采样
        "exporter": "console",
        "enable_batch_export": False,
    },

    "staging": {
        "sample_rate": 0.5,  # 测试环境：50%采样
        "exporter": "jaeger",
        "enable_batch_export": True,
    },

    "production": {
        "sample_rate": 0.1,  # 生产环境：10%采样
        "exporter": "jaeger",
        "enable_batch_export": True,
        "batch_export_schedule_delay": 5000,
        "batch_export_max_queue_size": 2048,
    }
}


def get_config(env: str = None) -> dict:
    """
    获取环境特定配置

    Args:
        env: 环境名称

    Returns:
        配置字典
    """
    if env is None:
        env = OPENTELEMETRY_CONFIG.get("environment", "development")

    # 合并基础配置和环境特定配置
    base_config = OPENTELEMETRY_CONFIG.copy()
    env_config = ENVIRONMENT_CONFIG.get(env, {})

    base_config.update(env_config)
    base_config["environment"] = env

    return base_config
