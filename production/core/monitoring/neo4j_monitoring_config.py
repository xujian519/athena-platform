#!/usr/bin/env python3
"""
Neo4j监控配置
Neo4j Monitoring Configuration

技术决策: TD-001 - Neo4j统一图数据库

监控内容:
1. 连接池监控
2. 查询性能监控
3. 数据库健康监控
4. 索引使用监控
5. 事务监控
6. 慢查询监控

作者: Athena平台团队
创建时间: 2026-01-26
版本: v1.0.0
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from core.monitoring.performance_monitoring_system import (
    AlertRule,
    AlertSeverity,
    MetricCategory,
)


@dataclass
class Neo4jMonitoringConfig:
    """
    Neo4j监控配置

    定义Neo4j的监控指标、告警规则和阈值
    """

    # 监控间隔
    metric_collection_interval: float = 30.0  # 秒
    health_check_interval: float = 60.0  # 秒
    slow_query_threshold: float = 1.0  # 秒

    # 性能阈值
    query_latency_p95_threshold: float = 500.0  # 毫秒
    query_latency_p99_threshold: float = 1000.0  # 毫秒
    connection_pool_usage_threshold: float = 0.8  # 80%
    transaction_timeout_threshold: float = 30.0  # 秒

    # 数据库健康阈值
    database_size_warning: float = 100.0  # GB
    database_size_critical: float = 500.0  # GB
    memory_usage_warning: float = 0.7  # 70%
    memory_usage_critical: float = 0.9  # 90%

    # 监控启用状态
    enable_query_monitoring: bool = True
    enable_connection_monitoring: bool = True
    enable_transaction_monitoring: bool = True
    enable_index_monitoring: bool = True
    enable_slow_query_monitoring: bool = True


def get_neo4j_alert_rules(config: Neo4jMonitoringConfig | None = None) -> list[AlertRule]:
    """
    获取Neo4j告警规则

    Args:
        config: 监控配置

    Returns:
        告警规则列表
    """
    if config is None:
        config = Neo4jMonitoringConfig()

    rules = []

    # 1. 查询延迟告警
    rules.append(
        AlertRule(
            rule_id="neo4j_query_latency_p95",
            name="Neo4j查询延迟P95过高",
            metric_name="neo4j_query_latency_p95",
            condition=lambda x: x > config.query_latency_p95_threshold,
            severity=AlertSeverity.WARNING,
            message_template="Neo4j查询延迟P95过高: {value:.2f}ms (阈值: {threshold:.2f}ms)",
            cooldown=300,
        )
    )

    rules.append(
        AlertRule(
            rule_id="neo4j_query_latency_p99",
            name="Neo4j查询延迟P99过高",
            metric_name="neo4j_query_latency_p99",
            condition=lambda x: x > config.query_latency_p99_threshold,
            severity=AlertSeverity.ERROR,
            message_template="Neo4j查询延迟P99过高: {value:.2f}ms (阈值: {threshold:.2f}ms)",
            cooldown=180,
        )
    )

    # 2. 连接池使用率告警
    rules.append(
        AlertRule(
            rule_id="neo4j_connection_pool_usage",
            name="Neo4j连接池使用率过高",
            metric_name="neo4j_connection_pool_usage_ratio",
            condition=lambda x: x > config.connection_pool_usage_threshold,
            severity=AlertSeverity.WARNING,
            message_template="Neo4j连接池使用率过高: {value:.1%} (阈值: {threshold:.1%})",
            cooldown=300,
        )
    )

    # 3. 事务超时告警
    rules.append(
        AlertRule(
            rule_id="neo4j_transaction_timeout",
            name="Neo4j事务超时",
            metric_name="neo4j_transaction_duration_max",
            condition=lambda x: x > config.transaction_timeout_threshold,
            severity=AlertSeverity.CRITICAL,
            message_template="Neo4j事务超时: {value:.2f}秒 (阈值: {threshold:.2f}秒)",
            cooldown=60,
        )
    )

    # 4. 数据库大小告警
    rules.append(
        AlertRule(
            rule_id="neo4j_database_size_warning",
            name="Neo4j数据库大小警告",
            metric_name="neo4j_database_size_gb",
            condition=lambda x: x > config.database_size_warning,
            severity=AlertSeverity.WARNING,
            message_template="Neo4j数据库大小过大: {value:.2f}GB (警告阈值: {threshold:.2f}GB)",
            cooldown=3600,
        )
    )

    rules.append(
        AlertRule(
            rule_id="neo4j_database_size_critical",
            name="Neo4j数据库大小严重",
            metric_name="neo4j_database_size_gb",
            condition=lambda x: x > config.database_size_critical,
            severity=AlertSeverity.CRITICAL,
            message_template="Neo4j数据库大小严重: {value:.2f}GB (严重阈值: {threshold:.2f}GB)",
            cooldown=1800,
        )
    )

    # 5. 连接失败告警
    rules.append(
        AlertRule(
            rule_id="neo4j_connection_failure",
            name="Neo4j连接失败",
            metric_name="neo4j_connection_failure_rate",
            condition=lambda x: x > 0.05,  # 5%失败率
            severity=AlertSeverity.CRITICAL,
            message_template="Neo4j连接失败率过高: {value:.1%}",
            cooldown=60,
        )
    )

    # 6. 慢查询告警
    rules.append(
        AlertRule(
            rule_id="neo4j_slow_query",
            name="Neo4j慢查询",
            metric_name="neo4j_slow_query_count",
            condition=lambda x: x > 10,  # 超过10个慢查询
            severity=AlertSeverity.WARNING,
            message_template="Neo4j慢查询数量过多: {value}个",
            cooldown=300,
        )
    )

    # 7. 索引缺失告警
    rules.append(
        AlertRule(
            rule_id="neo4j_index_usage",
            name="Neo4j索引使用率过低",
            metric_name="neo4j_index_usage_ratio",
            condition=lambda x: x < 0.3,  # 低于30%
            severity=AlertSeverity.WARNING,
            message_template="Neo4j索引使用率过低: {value:.1%} (可能需要优化索引)",
            cooldown=3600,
        )
    )

    # 8. 内存使用告警
    rules.append(
        AlertRule(
            rule_id="neo4j_memory_usage_warning",
            name="Neo4j内存使用警告",
            metric_name="neo4j_memory_usage_ratio",
            condition=lambda x: x > config.memory_usage_warning,
            severity=AlertSeverity.WARNING,
            message_template="Neo4j内存使用过高: {value:.1%} (警告阈值: {threshold:.1%})",
            cooldown=600,
        )
    )

    rules.append(
        AlertRule(
            rule_id="neo4j_memory_usage_critical",
            name="Neo4j内存使用严重",
            metric_name="neo4j_memory_usage_ratio",
            condition=lambda x: x > config.memory_usage_critical,
            severity=AlertSeverity.CRITICAL,
            message_template="Neo4j内存使用严重: {value:.1%} (严重阈值: {threshold:.1%})",
            cooldown=300,
        )
    )

    return rules


def get_neo4j_metric_definitions() -> dict[str, Any]:
    """
    获取Neo4j监控指标定义

    Returns:
        指标定义字典
    """
    return {
        # 查询性能指标
        "neo4j_query_latency_p95": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "ms",
            "description": "Neo4j查询延迟P95",
            "labels": ["query_type"],
        },
        "neo4j_query_latency_p99": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "ms",
            "description": "Neo4j查询延迟P99",
            "labels": ["query_type"],
        },
        "neo4j_query_latency_avg": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "ms",
            "description": "Neo4j查询延迟平均值",
            "labels": ["query_type"],
        },
        "neo4j_query_count_total": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "count",
            "description": "Neo4j查询总数",
            "labels": ["query_type", "status"],
        },

        # 连接池指标
        "neo4j_connection_pool_active": {
            "category": MetricCategory.RESOURCE,
            "unit": "connections",
            "description": "Neo4j活跃连接数",
        },
        "neo4j_connection_pool_idle": {
            "category": MetricCategory.RESOURCE,
            "unit": "connections",
            "description": "Neo4j空闲连接数",
        },
        "neo4j_connection_pool_usage_ratio": {
            "category": MetricCategory.RESOURCE,
            "unit": "ratio",
            "description": "Neo4j连接池使用率",
        },
        "neo4j_connection_failure_rate": {
            "category": MetricCategory.AVAILABILITY,
            "unit": "ratio",
            "description": "Neo4j连接失败率",
        },

        # 事务指标
        "neo4j_transaction_duration_avg": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "ms",
            "description": "Neo4j事务平均持续时间",
        },
        "neo4j_transaction_duration_max": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "ms",
            "description": "Neo4j事务最大持续时间",
        },
        "neo4j_transaction_count_total": {
            "category": MetricCategory.BUSINESS,
            "unit": "count",
            "description": "Neo4j事务总数",
            "labels": ["status"],
        },
        "neo4j_transaction_rollback_rate": {
            "category": MetricCategory.QUALITY,
            "unit": "ratio",
            "description": "Neo4j事务回滚率",
        },

        # 数据库健康指标
        "neo4j_database_size_gb": {
            "category": MetricCategory.RESOURCE,
            "unit": "GB",
            "description": "Neo4j数据库大小",
        },
        "neo4j_memory_usage_ratio": {
            "category": MetricCategory.RESOURCE,
            "unit": "ratio",
            "description": "Neo4j内存使用率",
            "labels": ["memory_type"],
        },
        "neo4j_cpu_usage_ratio": {
            "category": MetricCategory.RESOURCE,
            "unit": "ratio",
            "description": "Neo4j CPU使用率",
        },
        "neo4j_disk_io_wait_ratio": {
            "category": MetricCategory.RESOURCE,
            "unit": "ratio",
            "description": "Neo4j磁盘IO等待率",
        },

        # 索引指标
        "neo4j_index_count_total": {
            "category": MetricCategory.RESOURCE,
            "unit": "count",
            "description": "Neo4j索引总数",
            "labels": ["index_type"],
        },
        "neo4j_index_usage_ratio": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "ratio",
            "description": "Neo4j索引使用率",
            "labels": ["index_name"],
        },
        "neo4j_index_size_gb": {
            "category": MetricCategory.RESOURCE,
            "unit": "GB",
            "description": "Neo4j索引大小",
            "labels": ["index_name"],
        },

        # 慢查询指标
        "neo4j_slow_query_count": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "count",
            "description": "Neo4j慢查询数量",
            "labels": ["time_range"],
        },
        "neo4j_slow_query_latency_avg": {
            "category": MetricCategory.PERFORMANCE,
            "unit": "ms",
            "description": "Neo4j慢查询平均延迟",
            "labels": ["time_range"],
        },

        # 数据统计指标
        "neo4j_node_count_total": {
            "category": MetricCategory.BUSINESS,
            "unit": "count",
            "description": "Neo4j节点总数",
            "labels": ["label"],
        },
        "neo4j_edge_count_total": {
            "category": MetricCategory.BUSINESS,
            "unit": "count",
            "description": "Neo4j边总数",
            "labels": ["relationship_type"],
        },
        "neo4j_database_count": {
            "category": MetricCategory.RESOURCE,
            "unit": "count",
            "description": "Neo4j数据库数量",
        },
    }


def get_neo4j_dashboard_config() -> dict[str, Any]:
    """
    获取Neo4j监控仪表板配置

    Returns:
        仪表板配置字典
    """
    return {
        "dashboard_id": "neo4j_monitoring",
        "dashboard_title": "Neo4j监控仪表板",
        "dashboard_description": "Neo4j图数据库性能和健康监控",
        "refresh_interval": 30,  # 秒
        "panels": [
            {
                "panel_id": "neo4j_overview",
                "panel_title": "Neo4j概览",
                "panel_type": "summary",
                "metrics": [
                    "neo4j_query_count_total",
                    "neo4j_connection_pool_active",
                    "neo4j_database_size_gb",
                    "neo4j_node_count_total",
                ],
                "layout": {"x": 0, "y": 0, "w": 12, "h": 4},
            },
            {
                "panel_id": "neo4j_query_performance",
                "panel_title": "查询性能",
                "panel_type": "timeseries",
                "metrics": [
                    "neo4j_query_latency_p95",
                    "neo4j_query_latency_p99",
                    "neo4j_query_latency_avg",
                ],
                "layout": {"x": 0, "y": 4, "w": 12, "h": 6},
            },
            {
                "panel_id": "neo4j_connection_pool",
                "panel_title": "连接池状态",
                "panel_type": "gauge",
                "metrics": [
                    "neo4j_connection_pool_active",
                    "neo4j_connection_pool_idle",
                    "neo4j_connection_pool_usage_ratio",
                ],
                "layout": {"x": 12, "y": 4, "w": 6, "h": 6},
            },
            {
                "panel_id": "neo4j_transaction_stats",
                "panel_title": "事务统计",
                "panel_type": "timeseries",
                "metrics": [
                    "neo4j_transaction_duration_avg",
                    "neo4j_transaction_duration_max",
                    "neo4j_transaction_count_total",
                ],
                "layout": {"x": 18, "y": 4, "w": 6, "h": 6},
            },
            {
                "panel_id": "neo4j_database_health",
                "panel_title": "数据库健康",
                "panel_type": "gauge",
                "metrics": [
                    "neo4j_database_size_gb",
                    "neo4j_memory_usage_ratio",
                    "neo4j_cpu_usage_ratio",
                ],
                "layout": {"x": 0, "y": 10, "w": 12, "h": 6},
            },
            {
                "panel_id": "neo4j_index_stats",
                "panel_title": "索引统计",
                "panel_type": "table",
                "metrics": [
                    "neo4j_index_count_total",
                    "neo4j_index_usage_ratio",
                    "neo4j_index_size_gb",
                ],
                "layout": {"x": 12, "y": 10, "w": 12, "h": 6},
            },
            {
                "panel_id": "neo4j_slow_queries",
                "panel_title": "慢查询监控",
                "panel_type": "timeseries",
                "metrics": [
                    "neo4j_slow_query_count",
                    "neo4j_slow_query_latency_avg",
                ],
                "layout": {"x": 0, "y": 16, "w": 12, "h": 6},
            },
            {
                "panel_id": "neo4j_data_stats",
                "panel_title": "数据统计",
                "panel_type": "counter",
                "metrics": [
                    "neo4j_node_count_total",
                    "neo4j_edge_count_total",
                    "neo4j_database_count",
                ],
                "layout": {"x": 12, "y": 16, "w": 12, "h": 6},
            },
        ],
    }


# 默认配置实例
default_neo4j_monitoring_config = Neo4jMonitoringConfig()

# 默认告警规则
default_neo4j_alert_rules = get_neo4j_alert_rules()

# 默认指标定义
default_neo4j_metric_definitions = get_neo4j_metric_definitions()

# 默认仪表板配置
default_neo4j_dashboard_config = get_neo4j_dashboard_config()
