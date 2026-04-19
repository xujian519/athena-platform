#!/usr/bin/env python3
"""
特性开关配置
Feature Flags Configuration

用于控制各种优化特性的启用/禁用

作者: Athena平台团队
创建时间: 2026-03-17
版本: v1.0.0
"""

from typing import Any

# 特性开关定义
FEATURE_FLAGS: dict[str, Any] = {
    # 第1周优化 - 缓存集成
    "enable_intent_cache": True,  # 启用意图识别缓存
    "intent_cache_ttl": 3600,  # 意图缓存TTL(秒), 1小时
    "intent_cache_threshold": 0.85,  # 语义相似度阈值

    "enable_tool_cache": True,  # 启用工具选择缓存
    "tool_cache_ttl": 1800,  # 工具缓存TTL(秒), 30分钟
    "enable_tool_cache_warmup": True,  # 启用工具缓存预热

    "enable_recovery_monitoring": True,  # 启用错误恢复监控
    "recovery_rate_target": 0.90,  # 恢复成功率目标
    "enable_recovery_dashboard": True,  # 启用恢复仪表板
    "enable_unified_cache": True,  # 启用统一缓存接口

    # 第2周优化 - 索引和异步
    "enable_neo4j_indexes": True,  # 启用Neo4j复合索引
    "enable_hnsw_search": True,  # 启用HNSW向量检索
    "enable_async_queries": True,  # 启用异步查询

    # 性能目标
    "performance_targets": {
        "intent_accuracy": 0.93,  # 意图识别准确率目标
        "tool_accuracy": 0.88,  # 工具选择准确率目标
        "kg_query_latency_ms": 40,  # 知识图谱查询延迟目标
        "cache_hit_rate": 0.92,  # 缓存命中率目标
        "recovery_rate": 0.90,  # 错误恢复成功率目标
        "throughput_qps": 110,  # 系统吞吐量目标
    },
}


def is_feature_enabled(feature_name: str) -> bool:
    """
    检查特性是否启用

    Args:
        feature_name: 特性名称

    Returns:
        特性是否启用
    """
    return FEATURE_FLAGS.get(feature_name, False)


def get_feature_config(feature_name: str, default: Any = None) -> Any:
    """
    获取特性配置值

    Args:
        feature_name: 特性名称
        default: 默认值

    Returns:
        特性配置值
    """
    return FEATURE_FLAGS.get(feature_name, default)


def update_feature_flag(feature_name: str, value: Any) -> None:
    """
    更新特性开关

    Args:
        feature_name: 特性名称
        value: 新值
    """
    FEATURE_FLAGS[feature_name] = value


def get_all_feature_flags() -> dict[str, Any]:
    """
    获取所有特性开关

    Returns:
        所有特性开关的字典
    """
    return FEATURE_FLAGS.copy()


# 导出
__all__ = [
    "FEATURE_FLAGS",
    "is_feature_enabled",
    "get_feature_config",
    "update_feature_flag",
    "get_all_feature_flags",
]
