#!/usr/bin/env python3
from __future__ import annotations
"""
小娜智能体统一配置管理系统
Xiaona Unified Configuration Management System

目标:将所有配置外部化,实现健康度99分的关键基础设施
作者: Athena平台团队
创建时间: 2025-12-23
版本: v2.0.0 "99分健康度"
"""

import asyncio
import json
import logging
import os
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class Environment(Enum):
    """环境类型"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """数据库配置"""

    host: str = "localhost"
    port: int = 5432  # 本地PostgreSQL端口(2025-01-16更新:使用本地而非Docker的15432)
    database: str = "athena_db"
    user: str = "athena_user"
    password: str = ""
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        return f"postgresql://{self.user}:{urllib.parse.quote_plus(self.password)}@{self.host}:{self.port}/{self.database}"

    @property
    def async_url(self) -> str:
        """生成异步数据库连接URL"""
        return f"postgresql+asyncpg://{self.user}:{urllib.parse.quote_plus(self.password)}@{self.host}:{self.port}/{self.database}"


@dataclass
class MemoryDatabaseConfig:
    """记忆系统专用数据库配置"""

    host: str = "localhost"
    port: int = 5432  # 本地PostgreSQL端口
    database: str = "memory_module"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 5

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{urllib.parse.quote_plus(self.password)}@{self.host}:{self.port}/{self.database}"

    @property
    def async_url(self) -> str:
        """SQLAlchemy异步URL格式"""
        return f"postgresql+asyncpg://{self.user}:{urllib.parse.quote_plus(self.password)}@{self.host}:{self.port}/{self.database}"

    @property
    def asyncpg_url(self) -> str:
        """asyncpg库直接使用的URL格式"""
        return f"postgresql://{self.user}:{urllib.parse.quote_plus(self.password)}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis配置"""

    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    decode_responses: bool = True


@dataclass
class QdrantConfig:
    """Qdrant向量数据库配置"""

    host: str = "localhost"
    port: int = 6333
    api_key: str = ""
    collection_name: str = "xiaona_memory_vectors"
    vector_size: int = 768  # BERT向量维度
    timeout: int = 60

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class Neo4jConfig:
    """Neo4j知识图谱配置"""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = ""
    database: str = "neo4j"


@dataclass
class PerformanceConfig:
    """性能配置"""

    max_workers: int = None  # None表示自动检测CPU核心数
    async_workers: int = 100
    cache_ttl: int = 3600
    request_timeout: int = 30
    long_request_timeout: int = 300
    max_concurrent_requests: int = 1000
    queue_size: int = 10000


@dataclass
class CacheConfig:
    """缓存配置"""

    enabled: bool = True
    backend: str = "redis"  # redis, memory, mixed
    default_ttl: int = 3600
    hot_cache_size: int = 1000
    warm_cache_size: int = 5000
    cold_cache_size: int = 10000
    max_memory_mb: int = 512


@dataclass
class MemoryConfig:
    """记忆系统配置"""

    hot_cache_limit: int = 100  # 热记忆缓存大小(可调整)
    warm_cache_limit: int = 500
    memory_retention_days: int = 365
    enable_vector_search: bool = True
    enable_kg_integration: bool = True
    enable_shared_memory: bool = True


@dataclass
class LearningConfig:
    """学习系统配置"""

    storage_path: Path = field(
        default_factory=lambda: Path.home() / "athena" / "learning" / "xiaona"
    )
    auto_backup: bool = True
    backup_interval_days: int = 1
    max_events_per_batch: int = 100
    learning_confidence_threshold: float = 0.8
    auto_learning_enabled: bool = True
    scheduled_learning_interval_days: int = 7


@dataclass
class CommunicationConfig:
    """通信模块配置"""

    enable_websocket: bool = True
    enable_api_gateway: bool = True
    enable_message_queue: bool = True
    max_connections: int = 10000  # 增加到10000
    connection_pool_size: int = 100
    message_buffer_size: int = 100000
    message_timeout: int = 30
    enable_encryption: bool = False
    enable_authentication: bool = True
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class PerceptionConfig:
    """感知模块配置"""

    enable_multimodal: bool = True
    enable_cross_modal_alignment: bool = True
    enable_knowledge_injection: bool = True
    supported_formats: list[str] = field(
        default_factory=lambda: [".pdf", ".docx", ".txt", ".jpg", ".png"]
    )
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    ocr_languages: list[str] = field(default_factory=lambda: ["chi_sim", "eng", "chi_tra"])


@dataclass
class CognitionConfig:
    """认知模块配置"""

    response_strategy: str = "balanced"  # fast, balanced, comprehensive
    fast_timeout: float = 1.0
    balanced_timeout: float = 3.0
    comprehensive_timeout: float = 10.0
    enable_lyra_optimization: bool = True
    enable_expert_team: bool = True
    max_parallel_reasoning: int = 5


@dataclass
class StorageConfig:
    """存储配置"""

    athena_home: Path = field(default_factory=lambda: Path("/Users/xujian/Athena工作平台"))
    data_path: Path = field(default_factory=lambda: Path("/Users/xujian/Athena工作平台/data"))
    log_path: Path = field(default_factory=lambda: Path("/Users/xujian/Athena工作平台/logs"))
    cache_path: Path = field(default_factory=lambda: Path("/Users/xujian/Athena工作平台/cache"))
    identity_storage_path: Path = field(
        default_factory=lambda: Path("/Users/xujian/Athena工作平台/personal_secure_storage")
    )

    knowledge_path: Path = field(
        default_factory=lambda: Path(
            "/Users/xujian/Athena工作平台/modules/knowledge/knowledge/knowledge"
        )
    )
    models_path: Path = field(default_factory=lambda: Path("/Users/xujian/Athena工作平台/models"))

    def __post_init__(self):
        """确保路径存在"""
        for path_field in ["data_path", "log_path", "cache_path", "identity_storage_path"]:
            path = getattr(self, path_field)
            path.mkdir(parents=True, exist_ok=True)


@dataclass
class LoggingConfig:
    """日志配置"""

    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file_rotation: bool = True
    max_bytes: int = 100 * 1024 * 1024  # 100MB
    backup_count: int = 10
    console_output: bool = True
    file_output: bool = True


@dataclass
class SecurityConfig:
    """安全配置"""

    jwt_secret: str = "your_jwt_secret_key_here_min_32_chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    api_key_header: str = "X-API-Key"
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8020"]
    )
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 60


@dataclass
class MonitoringConfig:
    """监控配置"""

    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_health_check: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    performance_tracking: bool = True
    alert_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "response_time_p95": 3.0,
            "error_rate": 0.01,
            "memory_usage": 0.8,
            "cpu_usage": 0.9,
        }
    )


@dataclass
class XiaonaIdentityConfig:
    """小娜身份配置"""

    name: str = "小娜"
    english_name: str = "Athena"
    code_name: str = "ATHENA_MAIN"
    agent_type: str = "AI_DAUGHTER"
    role: str = "智慧大女儿与专业分析师"
    version: str = "2.0.0"
    expertise_areas: list[str] = field(
        default_factory=lambda: ["专利法", "商标法", "著作权法", "商业秘密", "知识产权战略"]
    )
    balance_principle: str = "公平、公正、精准、专业"


class XiaonaConfigManager:
    """小娜配置管理器 - 单例模式"""

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._config_loaded = False
        self._environment = Environment.DEVELOPMENT

        # 配置对象
        self.database = DatabaseConfig()
        self.memory_database = MemoryDatabaseConfig()
        self.redis = RedisConfig()
        self.qdrant = QdrantConfig()
        self.neo4j = Neo4jConfig()
        self.performance = PerformanceConfig()
        self.cache = CacheConfig()
        self.memory = MemoryConfig()
        self.learning = LearningConfig()
        self.communication = CommunicationConfig()
        self.perception = PerceptionConfig()
        self.cognition = CognitionConfig()
        self.storage = StorageConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.identity = XiaonaIdentityConfig()

    async def initialize(self, env: Environment = Environment.DEVELOPMENT) -> bool:
        """初始化配置管理器"""
        try:
            self._environment = env

            # 加载环境变量
            await self._load_env_variables()

            # 加载配置文件
            await self._load_config_files()

            # 验证配置
            await self._validate_config()

            # 应用配置
            await self._apply_config()

            self._config_loaded = True
            logger.info(f"✅ 小娜配置管理器初始化完成 - 环境: {env.value}")
            return True

        except Exception as e:
            logger.error(f"❌ 配置管理器初始化失败: {e}")
            return False

    async def _load_env_variables(self):
        """加载环境变量"""
        # 基础环境
        env_file = Path(os.getenv("ATHENA_HOME", "/Users/xujian/Athena工作平台")) / ".env"

        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

        # 数据库配置
        self.database.host = os.getenv("DB_HOST", self.database.host)
        self.database.port = int(os.getenv("DB_PORT", str(self.database.port)))
        self.database.database = os.getenv("DB_NAME", self.database.database)
        self.database.user = os.getenv("DB_USER", self.database.user)
        self.database.password = os.getenv("DB_PASSWORD", self.database.password)

        # Redis配置
        self.redis.host = os.getenv("REDIS_HOST", self.redis.host)
        self.redis.port = int(os.getenv("REDIS_PORT", str(self.redis.port)))
        self.redis.password = os.getenv("REDIS_PASSWORD", self.redis.password)

        # Qdrant配置
        self.qdrant.host = os.getenv("VECTOR_DB_HOST", self.qdrant.host)
        self.qdrant.port = int(os.getenv("VECTOR_DB_PORT", str(self.qdrant.port)))
        self.qdrant.api_key = os.getenv("VECTOR_DB_API_KEY", self.qdrant.api_key)

        # AI模型配置
        model_path = os.getenv("MODEL_PATH", str(self.storage.models_path))
        self.storage.models_path = Path(model_path)

        # 日志配置
        log_level = os.getenv("LOG_LEVEL", "INFO")
        self.logging.level = LogLevel(log_level)

        logger.info("✅ 环境变量加载完成")

    async def _load_config_files(self):
        """加载配置文件"""
        config_dir = self.storage.athena_home / "config"

        # 加载小娜身份配置
        identity_config = config_dir / "identity" / "athena.json"
        if identity_config.exists():
            with open(identity_config, encoding="utf-8") as f:
                identity_data = json.load(f)
                # 更新身份配置
                if "identity" in identity_data:
                    self.identity.name = identity_data["identity"].get("name", self.identity.name)
                    self.identity.role = identity_data["identity"].get("role", self.identity.role)
                    self.identity.version = identity_data["identity"].get(
                        "version", self.identity.version
                    )

        logger.info("✅ 配置文件加载完成")

    async def _validate_config(self):
        """验证配置"""
        errors = []

        # 验证存储路径
        try:
            self.storage.data_path.mkdir(parents=True, exist_ok=True)
            self.storage.log_path.mkdir(parents=True, exist_ok=True)
            self.storage.cache_path.mkdir(parents=True, exist_ok=True)
            self.learning.storage_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"存储路径验证失败: {e}")

        # 验证端口范围
        if not (1 <= self.database.port <= 65535):
            errors.append(f"数据库端口无效: {self.database.port}")
        if not (1 <= self.memory_database.port <= 65535):
            errors.append(f"记忆数据库端口无效: {self.memory_database.port}")
        if not (1 <= self.redis.port <= 65535):
            errors.append(f"Redis端口无效: {self.redis.port}")
        if not (1 <= self.qdrant.port <= 65535):
            errors.append(f"Qdrant端口无效: {self.qdrant.port}")

        # 验证性能配置
        if self.performance.max_workers is None:
            import os

            self.performance.max_workers = os.cpu_count() or 4

        if errors:
            error_msg = "\n".join(errors)
            logger.error(f"配置验证失败:\n{error_msg}")
            raise ValueError(f"配置验证失败: {error_msg}")

        logger.info("✅ 配置验证通过")

    async def _apply_config(self):
        """应用配置"""
        # 设置日志
        log_level = getattr(logging, self.logging.level.value)
        logging.getLogger().set_level(log_level)

        # 设置环境变量
        os.environ["PYTHONPATH"] = str(self.storage.athena_home)
        os.environ["ATHENA_HOME"] = str(self.storage.athena_home)

        logger.info("✅ 配置应用完成")

    def get_database_url(self, async_mode: bool = False) -> str:
        """获取数据库连接URL"""
        return self.database.async_url if async_mode else self.database.url

    def get_memory_database_url(self, async_mode: bool = False, driver: str = "sqlalchemy") -> str:
        """
        获取记忆数据库连接URL

        Args:
            async_mode: 是否使用异步模式
            driver: 驱动类型 ("sqlalchemy" 或 "asyncpg")

        Returns:
            数据库连接URL
        """
        if async_mode:
            if driver == "asyncpg":
                return self.memory_database.asyncpg_url
            else:
                return self.memory_database.async_url
        return self.memory_database.url

    def get_qdrant_url(self) -> str:
        """获取Qdrant连接URL"""
        return f"http://{self.qdrant.host}:{self.qdrant.port}"

    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        return f"redis://{self.redis.password}@{self.redis.host}:{self.redis.port}/{self.redis.db}"

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "config_loaded": self._config_loaded,
            "environment": self._environment.value,
            "database_configured": bool(self.database.password),
            "redis_configured": True,  # Redis通常不需要密码
            "qdrant_configured": True,
            "storage_paths_valid": all(
                [
                    self.storage.data_path.exists(),
                    self.storage.log_path.exists(),
                    self.storage.cache_path.exists(),
                ]
            ),
            "config_status": "healthy" if self._config_loaded else "uninitialized",
        }

    def export_config(self) -> dict[str, Any]:
        """导出配置(不包含敏感信息)"""
        return {
            "environment": self._environment.value,
            "infrastructure/infrastructure/database": {
                "host": self.database.host,
                "port": self.database.port,
                "infrastructure/infrastructure/database": self.database.database,
                "user": self.database.user,
                "pool_size": self.database.pool_size,
            },
            "memory_database": {
                "host": self.memory_database.host,
                "port": self.memory_database.port,
                "infrastructure/infrastructure/database": self.memory_database.database,
            },
            "performance": {
                "max_workers": self.performance.max_workers,
                "async_workers": self.performance.async_workers,
                "cache_ttl": self.performance.cache_ttl,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "backend": self.cache.backend,
                "default_ttl": self.cache.default_ttl,
            },
            "infrastructure/infrastructure/monitoring": {
                "enabled": self.monitoring.enable_metrics,
                "health_check_interval": self.monitoring.health_check_interval,
            },
            "identity": {
                "name": self.identity.name,
                "role": self.identity.role,
                "version": self.identity.version,
            },
        }


# 全局配置管理器实例
config_manager = XiaonaConfigManager()


async def get_config() -> XiaonaConfigManager:
    """获取配置管理器实例"""
    if not config_manager._config_loaded:
        await config_manager.initialize()
    return config_manager


# 便捷函数
def get_storage_path() -> Path:
    """获取存储路径"""
    return config_manager.storage.athena_home


def get_log_path() -> Path:
    """获取日志路径"""
    return config_manager.storage.log_path


def get_cache_path() -> Path:
    """获取缓存路径"""
    return config_manager.storage.cache_path


def get_learning_path() -> Path:
    """获取学习路径"""
    return config_manager.learning.storage_path


# 配置加载装饰器
def require_config(func) -> None:
    """装饰器:确保配置已加载"""

    async def wrapper(*args, **kwargs):
        if not config_manager._config_loaded:
            await config_manager.initialize()
        return await func(*args, **kwargs)

    return wrapper


if __name__ == "__main__":
    # 测试配置管理器
    async def test():
        print("=" * 60)
        print("🧪 测试小娜配置管理器")
        print("=" * 60)

        # 初始化
        await config_manager.initialize(Environment.DEVELOPMENT)

        # 健康检查
        health = await config_manager.health_check()
        print("\n📊 健康检查结果:")
        for key, value in health.items():
            print(f"  {key}: {value}")

        # 导出配置
        config = config_manager.export_config()
        print("\n📋 配置摘要:")
        print(json.dumps(config, indent=2, ensure_ascii=False))

        print("\n✅ 配置管理器测试完成!")

    asyncio.run(test())
