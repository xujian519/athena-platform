#!/usr/bin/env python3
"""
NLP生产环境配置（小团队版）
NLP Production Configuration for Small Team

针对2-3人小团队的优化配置

作者: 系统管理员
创建时间: 2026-01-25
"""

from __future__ import annotations
from typing import Any

# ============================================================================
# NLP服务配置（小团队优化版）
# ============================================================================

NLP_PRODUCTION_CONFIG: dict[str, Any] = {
    # ========== 缓存配置 ==========
    "cache": {
        "max_cache_size": 200,          # 最大缓存200条（2-3人足够）
        "cache_ttl_seconds": 1800,      # 缓存30分钟
        "enable_cache": True,           # 启用缓存
    },

    # ========== 模型配置 ==========
    "models": {
        "max_loaded_models": 1,         # 同时最多加载1个模型
        "auto_unload": True,            # 启用自动卸载
        "model_idle_timeout": 600,      # 模型10分钟不使用自动卸载
    },

    # ========== 内存保护 ==========
    "memory": {
        "enable_memory_monitor": True,  # 启用内存监控
        "memory_warning_threshold": 70,  # 70%内存使用告警
        "memory_critical_threshold": 85, # 85%内存使用严重告警
        "auto_cleanup": True,           # 自动清理
    },

    # ========== 请求限制 ==========
    "requests": {
        "max_concurrent_requests": 5,   # 最多5个并发请求（2-3人足够）
        "request_timeout": 60,          # 请求超时60秒
        "queue_size": 10,               # 请求队列大小10
    },

    # ========== 日志配置 ==========
    "logging": {
        "level": "INFO",                # 日志级别
        "enable_performance_log": True, # 启用性能日志
        "log_memory_usage": True,       # 记录内存使用
    },

    # ========== 监控配置 ==========
    "monitoring": {
        "enable_health_check": True,    # 启用健康检查
        "health_check_interval": 300,   # 每5分钟健康检查
        "enable_metrics": True,         # 启用指标采集
    },
}


# ============================================================================
# 环境变量配置
# ============================================================================

def get_nlp_config() -> dict[str, Any]:
    """获取NLP配置（支持环境变量覆盖）"""
    import os

    config = NLP_PRODUCTION_CONFIG.copy()

    # 环境变量覆盖
    if os.getenv("NLP_CACHE_SIZE"):
        config["cache"]["max_cache_size"] = int(os.getenv("NLP_CACHE_SIZE"))

    if os.getenv("NLP_MAX_MODELS"):
        config["models"]["max_loaded_models"] = int(os.getenv("NLP_MAX_MODELS"))

    if os.getenv("NLP_MEMORY_THRESHOLD"):
        config["memory"]["memory_warning_threshold"] = int(os.getenv("NLP_MEMORY_THRESHOLD"))

    return config


# ============================================================================
# 快速验证
# ============================================================================

def validate_config(config: dict[str, Any]) -> bool:
    """验证配置是否合理"""
    errors = []

    # 检查缓存大小
    if config["cache"]["max_cache_size"] > 1000:
        errors.append("缓存大小过大，建议不超过1000")

    # 检查模型数量
    if config["models"]["max_loaded_models"] > 3:
        errors.append("同时加载的模型数过多，建议不超过3")

    # 检查内存阈值
    if config["memory"]["memory_warning_threshold"] > 90:
        errors.append("内存告警阈值过高，建议不超过90%")

    if errors:
        print("⚠️ 配置警告:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


if __name__ == "__main__":
    import json

    print("=" * 60)
    print("📋 NLP生产环境配置（小团队版）")
    print("=" * 60)

    config = get_nlp_config()

    print("\n📊 当前配置:")
    print(json.dumps(config, indent=2, ensure_ascii=False))

    print("\n✅ 配置验证:")
    if validate_config(config):
        print("配置验证通过！")
    else:
        print("配置有问题，请检查")

    print("\n" + "=" * 60)
