#!/usr/bin/env python3
"""
Athena 平台统一配置管理
Central Configuration Management for Athena Platform

提供统一的配置入口，支持环境变量、配置文件、默认值的优先级加载

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: 1.0.0
"""

from __future__ import annotations
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """运行环境"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "athena"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    decode_responses: bool = True


@dataclass
class QdrantConfig:
    """Qdrant向量数据库配置"""
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "athena_vectors"
    vector_size: int = 768
    timeout: int = 60


@dataclass
class AIModelConfig:
    """AI模型配置"""
    # GLM配置
    glm_api_key: str = ""
    glm_model: str = "glm-4"
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"

    # BGE嵌入配置
    bge_model_path: str = "/Users/xujian/Athena工作平台/models/BAAI/bge-m3"
    bge_device: str = "cpu"  # cpu, cuda, mps

    # 模型缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600


@dataclass
class SecurityConfig:
    """安全配置"""
    secret_key: str = "athena-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str | None = None
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class ServicePortsConfig:
    """服务端口配置"""
    api_gateway: int = 8000
    xiaonuo_api: int = 8004
    xiaonuo_control: int = 8005
    glm_vision: int = 8001
    multimodal_processor: int = 8002
    dolphin_parser: int = 8003


@dataclass
class MonitoringConfig:
    """监控配置"""
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    enable_grafana: bool = True
    grafana_port: int = 3000
    enable_jaeger: bool = True
    jaeger_port: int = 16686


class CentralConfig:
    """统一配置管理器"""

    def __init__(self, env: Environment | None = None):
        # 确定运行环境
        self.environment = env or self._detect_environment()

        # 项目根目录
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"

        # 加载配置
        self._load_configs()

        logger.info(f"✅ 配置管理器初始化完成 - 环境: {self.environment.value}")

    def _detect_environment(self) -> Environment:
        """自动检测运行环境"""
        env = os.getenv("ATHENA_ENV", os.getenv("ENVIRONMENT", "development"))
        try:
            return Environment(env.lower())
        except ValueError:
            return Environment.DEVELOPMENT

    def _load_configs(self) -> Any:
        """加载所有配置"""
        # 数据库配置
        self.database = self._load_database_config()

        # Redis配置
        self.redis = self._load_redis_config()

        # Qdrant配置
        self.qdrant = self._load_qdrant_config()

        # AI模型配置
        self.ai_models = self._load_ai_model_config()

        # 安全配置
        self.security = self._load_security_config()

        # 日志配置
        self.logging = self._load_logging_config()

        # 服务端口配置
        self.service_ports = self._load_service_ports_config()

        # 监控配置
        self.monitoring = self._load_monitoring_config()

    def _load_database_config(self) -> DatabaseConfig:
        """加载数据库配置"""
        return DatabaseConfig(
            host=self._get_env("DB_HOST", "localhost"),
            port=int(self._get_env("DB_PORT", "5432")),
            database=self._get_env("DB_NAME", "athena"),
            user=self._get_env("DB_USER", "postgres"),
            password=self._get_env("DB_PASSWORD", ""),
            pool_size=int(self._get_env("DB_POOL_SIZE", "20")),
            max_overflow=int(self._get_env("DB_MAX_OVERFLOW", "10")),
        )

    def _load_redis_config(self) -> RedisConfig:
        """加载Redis配置"""
        return RedisConfig(
            host=self._get_env("REDIS_HOST", "localhost"),
            port=int(self._get_env("REDIS_PORT", "6379")),
            db=int(self._get_env("REDIS_DB", "0")),
            password=self._get_env("REDIS_PASSWORD", None),
            max_connections=int(self._get_env("REDIS_MAX_CONNECTIONS", "50")),
        )

    def _load_qdrant_config(self) -> QdrantConfig:
        """加载Qdrant配置"""
        return QdrantConfig(
            host=self._get_env("QDRANT_HOST", "localhost"),
            port=int(self._get_env("QDRANT_PORT", "6333")),
            collection_name=self._get_env("QDRANT_COLLECTION", "athena_vectors"),
            vector_size=int(self._get_env("QDRANT_VECTOR_SIZE", "768")),
        )

    def _load_ai_model_config(self) -> AIModelConfig:
        """加载AI模型配置"""
        # 从配置文件读取API密钥
        api_key = self._get_env("GLM_API_KEY")
        if not api_key:
            # 尝试从配置文件读取
            llm_config_path = self.config_dir / "llm_config.json"
            if llm_config_path.exists():
                with open(llm_config_path) as f:
                    llm_config = json.load(f)
                    api_key = llm_config.get("zhipu_api_key", "")

        return AIModelConfig(
            glm_api_key=api_key,
            glm_model=self._get_env("GLM_MODEL", "glm-4"),
            bge_model_path=self._get_env(
                "BGE_MODEL_PATH",
                "/Users/xujian/Athena工作平台/models/BAAI/bge-m3"
            ),
            bge_device=self._get_env("BGE_DEVICE", "cpu"),
        )

    def _load_security_config(self) -> SecurityConfig:
        """加载安全配置"""
        return SecurityConfig(
            secret_key=self._get_env("SECRET_KEY", "athena-secret-key-change-in-production"),
            access_token_expire_minutes=int(self._get_env("ACCESS_TOKEN_EXPIRE", "30")),
        )

    def _load_logging_config(self) -> LoggingConfig:
        """加载日志配置"""
        log_path = self.project_root / "logs"
        return LoggingConfig(
            level=self._get_env("LOG_LEVEL", "INFO"),
            file_path=str(log_path / "athena.log") if log_path.exists() else None,
        )

    def _load_service_ports_config(self) -> ServicePortsConfig:
        """加载服务端口配置"""
        return ServicePortsConfig(
            api_gateway=int(self._get_env("API_GATEWAY_PORT", "8000")),
            xiaonuo_api=int(self._get_env("XIAONUO_API_PORT", "8004")),
            xiaonuo_control=int(self._get_env("XIAONUO_CONTROL_PORT", "8005")),
        )

    def _load_monitoring_config(self) -> MonitoringConfig:
        """加载监控配置"""
        return MonitoringConfig(
            enable_prometheus=self._get_env("ENABLE_PROMETHEUS", "true").lower() == "true",
            prometheus_port=int(self._get_env("PROMETHEUS_PORT", "9090")),
            enable_grafana=self._get_env("ENABLE_GRAFANA", "true").lower() == "true",
        )

    def _get_env(self, key: str, default: str = "") -> str:
        """获取环境变量，支持默认值"""
        return os.getenv(key, default)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        支持点号分隔的路径，如:
        - config.get("database.host")
        - config.get("redis.port")
        """
        keys = key.split(".")
        value = self

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value

    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return (
            f"postgresql://{self.database.user}:{self.database.password}"
            f"@{self.database.host}:{self.database.port}/{self.database.database}"
        )

    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.redis.password:
            return f"redis://:{self.redis.password}@{self.redis.host}:{self.redis.port}/{self.redis.db}"
        return f"redis://{self.redis.host}:{self.redis.port}/{self.redis.db}"

    def is_production(self) -> bool:
        """是否生产环境"""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """是否开发环境"""
        return self.environment == Environment.DEVELOPMENT

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "environment": self.environment.value,
            "infrastructure/infrastructure/database": {
                "host": self.database.host,
                "port": self.database.port,
                "infrastructure/infrastructure/database": self.database.database,
                "user": self.database.user,
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
            },
            "qdrant": {
                "host": self.qdrant.host,
                "port": self.qdrant.port,
            },
        }

    def __repr__(self) -> str:
        return f"CentralConfig(environment={self.environment.value})"


# 全局配置实例
_global_config: CentralConfig | None = None


def get_config(env: Environment | None = None) -> CentralConfig:
    """
    获取全局配置实例（单例模式）

    Args:
        env: 运行环境，如果为None则自动检测

    Returns:
        CentralConfig: 配置实例
    """
    global _global_config

    if _global_config is None:
        _global_config = CentralConfig(env)

    return _global_config


def reload_config(env: Environment | None = None) -> CentralConfig:
    """
    重新加载配置

    Args:
        env: 运行环境

    Returns:
        CentralConfig: 新的配置实例
    """
    global _global_config
    _global_config = CentralConfig(env)
    return _global_config


# 便捷函数
def get_database_url() -> str:
    """获取数据库连接URL"""
    return get_config().get_database_url()


def get_redis_url() -> str:
    """获取Redis连接URL"""
    return get_config().get_redis_url()


def is_production() -> bool:
    """是否生产环境"""
    return get_config().is_production()


def is_development() -> bool:
    """是否开发环境"""
    return get_config().is_development()


if __name__ == "__main__":
    # 测试配置管理器
    config = get_config()

    print("🔧 Athena 平台统一配置管理")
    print("=" * 60)
    print(f"运行环境: {config.environment.value}")
    print(f"项目根目录: {config.project_root}")
    print()
    print("📊 数据库配置:")
    print(f"  主机: {config.database.host}:{config.database.port}")
    print(f"  数据库: {config.database.database}")
    print(f"  连接池: {config.database.pool_size}")
    print()
    print("📦 Redis配置:")
    print(f"  主机: {config.redis.host}:{config.redis.port}")
    print()
    print("🧠 AI模型配置:")
    print(f"  GLM模型: {config.ai_models.glm_model}")
    print(f"  BGE路径: {config.ai_models.bge_model_path}")
    print()
    print("🔌 服务端口:")
    print(f"  小诺API: {config.service_ports.xiaonuo_api}")
    print(f"  小诺控制: {config.service_ports.xiaonuo_control}")
    print()
    print("✅ 配置加载完成！")
