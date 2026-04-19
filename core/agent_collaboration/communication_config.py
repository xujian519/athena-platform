#!/usr/bin/env python3
from __future__ import annotations
"""
Agent通信系统配置
Communication System Configuration

通信系统的统一配置管理:
1. Redis连接配置
2. 消息队列配置
3. 健康检查配置
4. 故障转移配置
5. 监控配置

版本: v1.0.0
创建时间: 2026-01-18
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RedisConfig:
    """Redis配置"""

    url: str = "redis://127.0.0.1:6379/0"
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    decode_responses: bool = True


@dataclass
class MessageQueueConfig:
    """消息队列配置"""

    max_message_size: int = 10 * 1024 * 1024  # 10MB
    message_retention_hours: int = 24
    max_retries: int = 3
    retry_backoff_ms: int = 100
    consumer_timeout: int = 30
    block_timeout_ms: int = 1000


@dataclass
class HealthCheckConfig:
    """健康检查配置"""

    enabled: bool = True
    check_interval: int = 30  # 秒
    timeout: float = 5.0
    max_consecutive_failures: int = 3
    circuit_breaker_threshold: int = 5
    heartbeat_timeout: int = 60  # 秒


@dataclass
class FailoverConfig:
    """故障转移配置"""

    enabled: bool = True
    strategy: str = "redistribute"  # none, restart, redistribute, standby, circuit_breaker
    auto_recovery: bool = True
    recovery_check_interval: int = 60  # 秒
    standby_agents: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """监控配置"""

    enabled: bool = True
    prometheus_port: int = 9091
    metrics_export_interval: int = 10  # 秒
    log_level: str = "INFO"
    enable_tracing: bool = False


@dataclass
class CommunicationSystemConfig:
    """通信系统总配置"""

    redis: RedisConfig = field(default_factory=RedisConfig)
    message_queue: MessageQueueConfig = field(default_factory=MessageQueueConfig)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    failover: FailoverConfig = field(default_factory=FailoverConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "redis": {
                "url": self.redis.url,
                "max_connections": self.redis.max_connections,
                "socket_timeout": self.redis.socket_timeout,
            },
            "message_queue": {
                "max_message_size": self.message_queue.max_message_size,
                "message_retention_hours": self.message_queue.message_retention_hours,
                "max_retries": self.message_queue.max_retries,
            },
            "health_check": {
                "enabled": self.health_check.enabled,
                "check_interval": self.health_check.check_interval,
                "timeout": self.health_check.timeout,
            },
            "failover": {
                "enabled": self.failover.enabled,
                "strategy": self.failover.strategy,
                "auto_recovery": self.failover.auto_recovery,
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "prometheus_port": self.monitoring.prometheus_port,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommunicationSystemConfig":
        """从字典创建配置"""
        redis_config = data.get("redis", {})
        message_queue_config = data.get("message_queue", {})
        health_check_config = data.get("health_check", {})
        failover_config = data.get("failover", {})
        monitoring_config = data.get("monitoring", {})

        return cls(
            redis=RedisConfig(
                url=redis_config.get("url", "redis://127.0.0.1:6379/0"),
                max_connections=redis_config.get("max_connections", 50),
                socket_timeout=redis_config.get("socket_timeout", 5),
            ),
            message_queue=MessageQueueConfig(
                max_message_size=message_queue_config.get("max_message_size", 10 * 1024 * 1024),
                message_retention_hours=message_queue_config.get("message_retention_hours", 24),
                max_retries=message_queue_config.get("max_retries", 3),
            ),
            health_check=HealthCheckConfig(
                enabled=health_check_config.get("enabled", True),
                check_interval=health_check_config.get("check_interval", 30),
                timeout=health_check_config.get("timeout", 5.0),
            ),
            failover=FailoverConfig(
                enabled=failover_config.get("enabled", True),
                strategy=failover_config.get("strategy", "redistribute"),
                auto_recovery=failover_config.get("auto_recovery", True),
                standby_agents=failover_config.get("standby_agents", {}),
            ),
            monitoring=MonitoringConfig(
                enabled=monitoring_config.get("enabled", True),
                prometheus_port=monitoring_config.get("prometheus_port", 9091),
            ),
        )


# =============================================================================
# 默认配置
# =============================================================================

DEFAULT_CONFIG = CommunicationSystemConfig()

# 生产环境配置
PRODUCTION_CONFIG = CommunicationSystemConfig(
    redis=RedisConfig(url="redis://redis-cluster:6379/0", max_connections=100, socket_timeout=10),
    message_queue=MessageQueueConfig(
        max_message_size=50 * 1024 * 1024, message_retention_hours=168, max_retries=5  # 50MB  # 7天
    ),
    health_check=HealthCheckConfig(check_interval=15, timeout=10.0),
    monitoring=MonitoringConfig(prometheus_port=9091),
)

# 开发环境配置
DEVELOPMENT_CONFIG = CommunicationSystemConfig(
    redis=RedisConfig(url="redis://127.0.0.1:6379/1", max_connections=10),  # 使用测试数据库
    message_queue=MessageQueueConfig(
        max_message_size=5 * 1024 * 1024, message_retention_hours=1  # 5MB  # 1小时
    ),
    health_check=HealthCheckConfig(check_interval=60, timeout=10.0),  # 降低检查频率
    monitoring=MonitoringConfig(log_level="DEBUG"),
)
