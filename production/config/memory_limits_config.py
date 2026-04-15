#!/usr/bin/env python3
"""
Athena内存限制配置
Memory Limits Configuration for Athena Platform

此文件定义了整个平台的内存使用限制

作者: Claude (AI Assistant)
创建时间: 2026-01-16
版本: v1.0.0
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheLimits:
    """缓存限制配置"""
    # L1内存缓存限制
    l1_max_size_mb: int = 100  # 从500MB降至100MB
    l1_max_entries: int = 1000  # 最大条目数

    # L2 Redis缓存限制
    l2_max_size_mb: int = 500  # 从4GB降至500MB
    l2_default_ttl: int = 3600  # 默认1小时过期

    # L3磁盘缓存限制
    l3_max_size_gb: int = 10  # 从无限降至10GB

    # BGE嵌入服务缓存限制
    bge_cache_max_mb: int = 100  # 从无限制降至100MB
    bge_cache_max_entries: int = 100  # 最大条目数


@dataclass
class ModelLimits:
    """模型限制配置"""
    # 模型管理器设置
    max_loaded_models: int = 2  # 同时最多加载2个模型
    model_unload_timeout: int = 300  # 5分钟未使用则卸载

    # BGE模型设置
    bge_batch_size: int = 16  # 从32降至16，减少峰值内存
    bge_max_length: int = 512  # 最大序列长度

    # 设备选择
    prefer_mps: bool = True  # 优先使用MPS (Apple Silicon)
    fallback_to_cpu: bool = True  # MPS不可用时降级到CPU


@dataclass
class ServiceLimits:
    """服务限制配置"""
    # API服务
    api_max_workers: int = 4  # 最大工作进程数
    api_max_connections: int = 100  # 最大连接数

    # 向量数据库
    vector_db_connection_pool_size: int = 5  # 连接池大小
    vector_db_query_timeout: int = 30  # 查询超时(秒)

    # Redis
    redis_max_connections: int = 10  # 最大连接数


@dataclass
class MonitoringThresholds:
    """监控阈值配置"""
    # 内存警告阈值
    memory_warning_mb: int = 2048  # 2GB
    memory_critical_mb: int = 4096  # 4GB

    # 对象数量警告阈值
    object_count_warning: int = 500000  # 50万对象

    # 监控间隔
    monitor_interval_seconds: int = 60  # 每分钟检查一次


# 全局配置实例
CACHE_LIMITS = CacheLimits()
MODEL_LIMITS = ModelLimits()
SERVICE_LIMITS = ServiceLimits()
MONITORING_THRESHOLDS = MonitoringThresholds()


def print_configuration() -> Any:
    """打印当前配置"""
    print("\n" + "=" * 60)
    print("⚙️  Athena内存限制配置")
    print("=" * 60)

    print("\n📦 缓存限制:")
    print(f"  L1内存缓存: {CACHE_LIMITS.l1_max_size_mb} MB")
    print(f"  L2 Redis缓存: {CACHE_LIMITS.l2_max_size_mb} MB")
    print(f"  L3磁盘缓存: {CACHE_LIMITS.l3_max_size_gb} GB")
    print(f"  BGE缓存: {CACHE_LIMITS.bge_cache_max_mb} MB")

    print("\n🤖 模型限制:")
    print(f"  最大加载模型数: {MODEL_LIMITS.max_loaded_models}")
    print(f"  模型卸载超时: {MODEL_LIMITS.model_unload_timeout} 秒")
    print(f"  BGE批处理大小: {MODEL_LIMITS.bge_batch_size}")
    print(f"  BGE最大序列长度: {MODEL_LIMITS.bge_max_length}")

    print("\n🌐 服务限制:")
    print(f"  API最大工作进程: {SERVICE_LIMITS.api_max_workers}")
    print(f"  API最大连接数: {SERVICE_LIMITS.api_max_connections}")
    print(f"  向量数据库连接池: {SERVICE_LIMITS.vector_db_connection_pool_size}")
    print(f"  Redis最大连接数: {SERVICE_LIMITS.redis_max_connections}")

    print("\n📊 监控阈值:")
    print(f"  内存警告: {MONITORING_THRESHOLDS.memory_warning_mb} MB")
    print(f"  内存危急: {MONITORING_THRESHOLDS.memory_critical_mb} MB")
    print(f"  对象数警告: {MONITORING_THRESHOLDS.object_count_warning:,}")

    # 计算预期总内存使用
    expected_total = (
        CACHE_LIMITS.l1_max_size_mb +
        CACHE_LIMITS.l2_max_size_mb +
        (MODEL_LIMITS.max_loaded_models * 2000) +  # 每个模型约2GB
        500  # 其他开销
    )

    print(f"\n💾 预期总内存使用: ~{expected_total} MB ({expected_total/1024:.2f} GB)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_configuration()
