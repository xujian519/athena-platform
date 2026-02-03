#!/usr/bin/env python3
"""
API配置管理模块
API Configuration Management

版本: 1.0.0
功能:
- 集中管理所有敏感配置
- 从环境变量加载配置
- 配置验证和默认值
- 支持配置热更新
"""

import logging
import os
import secrets
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置"""

    # Neo4j配置
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # PostgreSQL配置
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "athena"
    postgres_user: str = "athena"
    postgres_password: str = ""

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0

    def __post_init__(self):
        """初始化后验证必需配置"""
        if not self.neo4j_password and not os.getenv("NEO4J_PASSWORD"):
            logger.warning("⚠️ NEO4J_PASSWORD未设置,使用开发环境默认值")

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量创建配置"""
        return cls(
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "neo4j_password"),
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_database=os.getenv("POSTGRES_DATABASE", "athena"),
            postgres_user=os.getenv("POSTGRES_USER", "athena"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD"),
            redis_db=int(os.getenv("REDIS_DB", "0")),
        )

    def get_postgres_url(self) -> str:
        """获取PostgreSQL连接URL"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )

    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@dataclass
class LLMConfig:
    """LLM配置"""

    # ZhipuAI配置
    zhipuai_api_key: str | None = None
    zhipuai_model: str = "glm-4-flash"
    zhipuai_temperature: float = 0.1
    zhipuai_max_tokens: int = 500

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """从环境变量创建配置"""
        return cls(
            zhipuai_api_key=os.getenv("ZHIPUAI_API_KEY"),
            zhipuai_model=os.getenv("ZHIPUAI_MODEL", "glm-4-flash"),
            zhipuai_temperature=float(os.getenv("ZHIPUAI_TEMPERATURE", "0.1")),
            zhipuai_max_tokens=int(os.getenv("ZHIPUAI_MAX_TOKENS", "500")),
        )


@dataclass
class QdrantConfig:
    """Qdrant向量数据库配置"""

    url: str = "http://localhost:6333"
    api_key: str | None = None

    @classmethod
    def from_env(cls) -> "QdrantConfig":
        """从环境变量创建配置"""
        return cls(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )


@dataclass
class SecurityConfig:
    """安全配置"""

    # 速率限制
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # CORS
    cors_origins: list = field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"]
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    cors_allow_headers: list = field(default_factory=lambda: ["*"])

    # CSRF
    csrf_enabled: bool = True
    csrf_secret: str = ""

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # 请求大小限制
    max_request_size_mb: int = 10

    def __post_init__(self):
        """初始化后验证"""
        if self.csrf_enabled and not self.csrf_secret:
            # 生成默认密钥(仅用于开发环境)
            import secrets

            self.csrf_secret = secrets.token_urlsafe(32)
            logger.warning("⚠️ CSRF_SECRET未设置,使用自动生成的密钥(仅开发环境)")

        if not self.jwt_secret_key:
            self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
            if not self.jwt_secret_key:
                self.jwt_secret_key = secrets.token_urlsafe(32)
                logger.warning("⚠️ JWT_SECRET_KEY未设置,使用自动生成的密钥(仅开发环境)")

    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """从环境变量创建配置"""
        return cls(
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            rate_limit_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
            cors_origins=(
                os.getenv("CORS_ORIGINS", "").split(",")
                if os.getenv("CORS_ORIGINS")
                else ["http://localhost:3000"]
            ),
            csrf_enabled=os.getenv("CSRF_ENABLED", "true").lower() == "true",
            csrf_secret=os.getenv("CSRF_SECRET", ""),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            max_request_size_mb=int(os.getenv("MAX_REQUEST_SIZE_MB", "10")),
        )


@dataclass
class MonitoringConfig:
    """监控配置"""

    # Prometheus
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # 结构化日志
    structured_logging_enabled: bool = True
    log_level: str = "INFO"

    # 性能监控
    performance_monitoring_enabled: bool = True
    metrics_export_interval_seconds: int = 60

    @classmethod
    def from_env(cls) -> "MonitoringConfig":
        """从环境变量创建配置"""
        return cls(
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
            structured_logging_enabled=os.getenv("STRUCTURED_LOGGING_ENABLED", "true").lower()
            == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            performance_monitoring_enabled=os.getenv(
                "PERFORMANCE_MONITORING_ENABLED", "true"
            ).lower()
            == "true",
            metrics_export_interval_seconds=int(os.getenv("METRICS_EXPORT_INTERVAL", "60")),
        )


@dataclass
class APIConfig:
    """API总配置"""

    database: DatabaseConfig = field(default_factory=DatabaseConfig.from_env)
    llm: LLMConfig = field(default_factory=LLMConfig.from_env)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig.from_env)
    security: SecurityConfig = field(default_factory=SecurityConfig.from_env)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig.from_env)

    # API设置
    api_title: str = "Athena动态提示词系统"
    api_version: str = "2.1.0"
    api_description: str = "企业级AI智能提示词生成系统"
    debug_mode: bool = False

    def __post_init__(self):
        """初始化后设置"""
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def from_env(cls) -> "APIConfig":
        """从环境变量创建完整配置"""
        return cls(
            database=DatabaseConfig.from_env(),
            llm=LLMConfig.from_env(),
            qdrant=QdrantConfig.from_env(),
            security=SecurityConfig.from_env(),
            monitoring=MonitoringConfig.from_env(),
        )

    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置有效性

        Returns:
            (is_valid, errors): 是否有效和错误列表
        """
        errors = []

        # 验证数据库配置
        if not self.database.neo4j_password:
            errors.append("NEO4J_PASSWORD未设置(生产环境必需)")

        if not self.database.postgres_password and not self.debug_mode:
            errors.append("POSTGRES_PASSWORD未设置(生产环境必需)")

        # 验证LLM配置
        if not self.llm.zhipuai_api_key:
            errors.append("ZHIPUAI_API_KEY未设置(LLM回退功能需要)")

        # 验证安全配置
        if self.security.rate_limit_per_minute < 1:
            errors.append("RATE_LIMIT_PER_MINUTE必须大于0")

        return len(errors) == 0, errors

    def get_config_summary(self) -> dict[str, Any]:
        """获取配置摘要(隐藏敏感信息)"""
        return {
            "api_version": self.api_version,
            "debug_mode": self.debug_mode,
            "database": {
                "neo4j_uri": self.database.neo4j_uri,
                "postgres_host": self.database.postgres_host,
                "redis_host": self.database.redis_host,
            },
            "llm": {
                "model": self.llm.zhipuai_model,
                "api_key_configured": bool(self.llm.zhipuai_api_key),
            },
            "qdrant": {"url": self.qdrant.url, "api_key_configured": bool(self.qdrant.api_key)},
            "security": {
                "rate_limit_enabled": self.security.rate_limit_enabled,
                "csrf_enabled": self.security.csrf_enabled,
                "cors_origins_count": len(self.security.cors_origins),
            },
            "monitoring": {
                "prometheus_enabled": self.monitoring.prometheus_enabled,
                "structured_logging_enabled": self.monitoring.structured_logging_enabled,
            },
        }


# 全局配置单例
_global_config: APIConfig | None = None


def get_config() -> APIConfig:
    """
    获取全局配置实例

    Returns:
        APIConfig实例
    """
    global _global_config

    if _global_config is None:
        _global_config = APIConfig.from_env()
        logger.info("✅ API配置已加载")

    return _global_config


def reload_config() -> APIConfig:
    """
    重新加载配置

    Returns:
        新的配置实例
    """
    global _global_config

    _global_config = APIConfig.from_env()
    logger.info("🔄 API配置已重新加载")

    return _global_config


def validate_config() -> tuple[bool, list[str]]:
    """
    验证当前配置

    Returns:
        (is_valid, errors): 是否有效和错误列表
    """
    config = get_config()
    return config.validate()


# 便捷函数
def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    return get_config().database


def get_llm_config() -> LLMConfig:
    """获取LLM配置"""
    return get_config().llm


def get_security_config() -> SecurityConfig:
    """获取安全配置"""
    return get_config().security


def get_monitoring_config() -> MonitoringConfig:
    """获取监控配置"""
    return get_config().monitoring


def get_qdrant_config() -> QdrantConfig:
    """获取Qdrant配置"""
    return get_config().qdrant
