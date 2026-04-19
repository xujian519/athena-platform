#!/usr/bin/env python3
"""
生产环境配置模块

提供生产环境的告警配置、日志收集配置等
"""

from __future__ import annotations
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# 告警配置
# =============================================================================

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric: str
    condition: str  # gt, lt, eq, gte, lte
    threshold: float
    level: str  # info, warning, error, critical
    description: str = ""
    enabled: bool = True
    cooldown: int = 300  # 冷却时间（秒）
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class NotificationChannel:
    """通知渠道配置"""
    name: str
    type: str  # email, webhook, log, console
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


# 默认告警规则
DEFAULT_ALERT_RULES = [
    AlertRule(
        name="high_response_time",
        metric="response_time",
        condition="gt",
        threshold=5.0,
        level="warning",
        description="API响应时间超过5秒",
        cooldown=600
    ),
    AlertRule(
        name="critical_response_time",
        metric="response_time",
        condition="gt",
        threshold=10.0,
        level="critical",
        description="API响应时间超过10秒",
        cooldown=300
    ),
    AlertRule(
        name="high_error_rate",
        metric="error_rate",
        condition="gt",
        threshold=0.05,
        level="warning",
        description="错误率超过5%",
        cooldown=600
    ),
    AlertRule(
        name="critical_error_rate",
        metric="error_rate",
        condition="gt",
        threshold=0.1,
        level="critical",
        description="错误率超过10%",
        cooldown=300
    ),
    AlertRule(
        name="low_request_rate",
        metric="request_rate",
        condition="lt",
        threshold=0.1,
        level="info",
        description="请求速率过低（可能服务异常）",
        cooldown=900
    ),
    AlertRule(
        name="high_memory_usage",
        metric="memory_usage",
        condition="gt",
        threshold=0.85,
        level="warning",
        description="内存使用率超过85%",
        cooldown=600
    ),
    AlertRule(
        name="critical_memory_usage",
        metric="memory_usage",
        condition="gt",
        threshold=0.95,
        level="critical",
        description="内存使用率超过95%",
        cooldown=300
    ),
    AlertRule(
        name="high_cpu_usage",
        metric="cpu_usage",
        condition="gt",
        threshold=0.8,
        level="warning",
        description="CPU使用率超过80%",
        cooldown=600
    ),
    AlertRule(
        name="disk_space_low",
        metric="disk_usage",
        condition="gt",
        threshold=0.9,
        level="critical",
        description="磁盘使用率超过90%",
        cooldown=1800
    ),
]


# =============================================================================
# 日志配置
# =============================================================================

@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_dir: str = "/var/log/xiaonuo"
    max_bytes: int = 100 * 1024 * 1024  # 100MB
    backup_count: int = 10
    json_logs: bool = True  # 生产环境使用JSON格式日志
    log_to_file: bool = True
    log_to_console: bool = True

    # 特定模块的日志级别
    module_levels: dict[str, str] = field(default_factory=lambda: {
        "uvicorn": "INFO",
        "fastapi": "INFO",
        "aiohttp": "WARNING",
        "transformers": "WARNING",
    })


# =============================================================================
# 监控配置
# =============================================================================

@dataclass
class MetricsConfig:
    """指标配置"""
    enabled: bool = True
    port: int = 9090  # Prometheus metrics端口
    path: str = "/metrics"
    # 指标收集间隔
    collect_interval: int = 15  # 秒
    # 历史数据保留
    retention_days: int = 30


# =============================================================================
# 健康检查配置
# =============================================================================

@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    enabled: bool = True
    interval: int = 30  # 检查间隔（秒）
    timeout: int = 10  # 超时时间（秒）
    # 依赖服务
    dependencies: list[str] = field(default_factory=lambda: [
        "xiaona:8001",
        "knowledge_graph:8100",
        "multimodal:8200",
    ])
    # 失败阈值
    failure_threshold: int = 3  # 连续失败多少次认为不健康
    recovery_threshold: int = 2  # 连续成功多少次认为恢复健康


# =============================================================================
# 完整生产配置
# =============================================================================

@dataclass
class ProductionConfig:
    """生产环境完整配置"""

    # 环境
    environment: str = "production"  # development, staging, production
    debug: bool = False

    # 服务
    service_name: str = "xiaonuo_unified_gateway"
    service_version: str = "5.0.0"
    host: str = "0.0.0.0"
    port: int = 8100

    # 告警配置
    alert_rules: list[AlertRule] = field(default_factory=lambda: DEFAULT_ALERT_RULES.copy())
    notification_channels: list[NotificationChannel] = field(default_factory=list)

    # 日志配置
    logging: LogConfig = field(default_factory=LogConfig)

    # 指标配置
    metrics: MetricsConfig = field(default_factory=MetricsConfig)

    # 健康检查配置
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)

    # 性能配置
    max_connections: int = 1000
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 300  # 5分钟

    # 缓存配置
    cache_ttl: int = 3600  # 1小时
    cache_max_size: int = 10000

    @classmethod
    def from_env(cls) -> "ProductionConfig":
        """从环境变量加载配置"""
        env = os.getenv("ENVIRONMENT", "production")
        debug = os.getenv("DEBUG", "false").lower() == "true"

        # 日志配置
        log_config = LogConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_dir=os.getenv("LOG_DIR", "/var/log/xiaonuo"),
            json_logs=os.getenv("JSON_LOGS", "true").lower() == "true",
        )

        # 指标配置
        metrics_config = MetricsConfig(
            enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            port=int(os.getenv("METRICS_PORT", "9090")),
        )

        # 健康检查配置
        health_config = HealthCheckConfig(
            enabled=os.getenv("HEALTH_CHECK_ENABLED", "true").lower() == "true",
            dependencies=os.getenv("HEALTH_DEPENDENCIES", "").split(",") if os.getenv("HEALTH_DEPENDENCIES") else [],
        )

        # 通知渠道配置
        notification_channels = []
        if os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true":
            notification_channels.append(NotificationChannel(
                name="email",
                type="email",
                config={
                    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                    "from_addr": os.getenv("ALERT_FROM", "alerts@athena-platform.com"),
                    "to_addrs": os.getenv("ALERT_TO", "xujian519@gmail.com").split(","),
                }
            ))
        if os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true":
            notification_channels.append(NotificationChannel(
                name="webhook",
                type="webhook",
                config={
                    "url": os.getenv("ALERT_WEBHOOK_URL", ""),
                }
            ))

        return cls(
            environment=env,
            debug=debug,
            logging=log_config,
            metrics=metrics_config,
            health_check=health_config,
            notification_channels=notification_channels,
        )

    @classmethod
    def from_file(cls, config_path: str) -> "ProductionConfig":
        """从JSON配置文件加载"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return cls.from_env()

        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)

        # 解析告警规则
        alert_rules = []
        for rule_data in data.get("alert_rules", []):
            alert_rules.append(AlertRule(**rule_data))

        # 解析通知渠道
        notification_channels = []
        for channel_data in data.get("notification_channels", []):
            notification_channels.append(NotificationChannel(**channel_data))

        # 解析日志配置
        logging_config = LogConfig(**data.get("logging", {}))

        # 解析指标配置
        metrics_config = MetricsConfig(**data.get("metrics", {}))

        # 解析健康检查配置
        health_config = HealthCheckConfig(**data.get("health_check", {}))

        return cls(
            environment=data.get("environment", "production"),
            debug=data.get("debug", False),
            alert_rules=alert_rules,
            notification_channels=notification_channels,
            logging=logging_config,
            metrics=metrics_config,
            health_check=health_config,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "alert_rules": [
                {
                    "name": r.name,
                    "metric": r.metric,
                    "condition": r.condition,
                    "threshold": r.threshold,
                    "level": r.level,
                    "description": r.description,
                    "enabled": r.enabled,
                    "cooldown": r.cooldown,
                }
                for r in self.alert_rules
            ],
            "notification_channels": [
                {
                    "name": c.name,
                    "type": c.type,
                    "enabled": c.enabled,
                    "config": c.config,
                }
                for c in self.notification_channels
            ],
            "logging": {
                "level": self.logging.level,
                "log_dir": self.logging.log_dir,
                "json_logs": self.logging.json_logs,
            },
            "metrics": {
                "enabled": self.metrics.enabled,
                "port": self.metrics.port,
            },
            "health_check": {
                "enabled": self.health_check.enabled,
                "dependencies": self.health_check.dependencies,
            },
        }

    def save(self, config_path: str) -> Any:
        """保存配置到文件"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"配置已保存到: {config_path}")


# =============================================================================
# 配置管理器
# =============================================================================

class ProductionConfigManager:
    """生产环境配置管理器"""

    def __init__(self, config_path: str | None = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path or os.getenv(
            "PRODUCTION_CONFIG_PATH",
            "/etc/xiaonuo/production_config.json"
        )
        self.config: ProductionConfig | None = None

    def load_config(self) -> ProductionConfig:
        """加载配置"""
        # 优先从配置文件加载
        config_file = Path(self.config_path)
        if config_file.exists():
            logger.info(f"从文件加载配置: {self.config_path}")
            self.config = ProductionConfig.from_file(self.config_path)
        else:
            logger.info("从环境变量加载配置")
            self.config = ProductionConfig.from_env()

        return self.config

    def get_config(self) -> ProductionConfig:
        """获取当前配置"""
        if self.config is None:
            self.config = self.load_config()
        return self.config

    def update_alert_rules(self, rules: list[AlertRule]) -> None:
        """更新告警规则"""
        config = self.get_config()
        config.alert_rules = rules
        if self.config_path:
            config.save(self.config_path)

    def add_notification_channel(self, channel: NotificationChannel) -> None:
        """添加通知渠道"""
        config = self.get_config()
        config.notification_channels.append(channel)
        if self.config_path:
            config.save(self.config_path)

    def reload(self) -> ProductionConfig:
        """重新加载配置"""
        self.config = None
        return self.load_config()


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "AlertRule",
    "NotificationChannel",
    "LogConfig",
    "MetricsConfig",
    "HealthCheckConfig",
    "ProductionConfig",
    "ProductionConfigManager",
    "DEFAULT_ALERT_RULES",
]


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 创建默认配置
    config = ProductionConfig()
    print("默认配置:")
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))

    # 保存配置
    config.save("/tmp/production_config_example.json")

    # 从文件加载
    manager = ProductionConfigManager("/tmp/production_config_example.json")
    loaded_config = manager.load_config()
    print("\n加载的配置:")
    print(json.dumps(loaded_config.to_dict(), indent=2, ensure_ascii=False))
