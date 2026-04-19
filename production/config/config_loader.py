"""
Athena工作平台 - 统一配置加载器
Unified Configuration Loader for Athena Platform

版本: 1.0.0
更新时间: 2024-12-24

功能特性:
1. 支持多环境配置加载 (development/staging/production)
2. 环境变量优先级覆盖
3. 敏感信息加密存储
4. 配置验证和错误提示
5. 配置热重载支持
"""

from __future__ import annotations
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

# 尝试导入python-dotenv（如未安装则提供替代方案）
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# 配置日志
logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConfigurationError(Exception):
    """配置错误异常类"""
    pass


class MissingRequiredVariableError(ConfigurationError):
    """缺少必需的环境变量异常"""
    def __init__(self, variable_name: str, section: str = ""):
        self.variable_name = variable_name
        self.section = section
        message = f"缺少必需的环境变量: {variable_name}"
        if section:
            message += f" (章节: {section})"
        super().__init__(message)


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    read_replica_host: str | None = None
    read_replica_port: int | None = None
    read_replica_enabled: bool = False

    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def read_replica_url(self) -> str | None:
        """生成只读副本连接URL"""
        if self.read_replica_enabled and self.read_replica_host:
            port = self.read_replica_port or self.port
            return f"postgresql://{self.user}:{self.password}@{self.read_replica_host}:{port}/{self.database}"
        return None


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str
    port: int
    password: str
    db: int = 0
    cluster_mode: bool = False
    cluster_nodes: str | None = None
    sentinel_enabled: bool = False
    sentinel_master_name: str | None = None
    sentinel_nodes: str | None = None

    @property
    def url(self) -> str:
        """生成Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class QdrantConfig:
    """Qdrant向量数据库配置"""
    host: str
    port: int
    api_key: str | None = None
    collection: str = "athena_vectors"
    grpc_port: int | None = None
    cloud_url: str | None = None
    cloud_api_key: str | None = None
    vector_dimension: int = 768
    similarity_threshold: float = 0.75
    search_limit: int = 100


@dataclass
class AIModelConfig:
    """AI模型配置"""
    # GLM配置
    glm_api_key: str | None = None
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    glm_model: str = "glm-4"
    glm_max_tokens: int = 4000
    glm_temperature: float = 0.7

    # OpenAI配置
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7

    # DeepSeek配置
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Gemini配置
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-pro"


@dataclass
class SecurityConfig:
    """安全配置"""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    jwt_refresh_expire_days: int = 30
    encryption_key: str | None = None
    cors_origins: str = "*"
    api_key_required: bool = True
    api_rate_limit_enabled: bool = True
    api_rate_limit_per_minute: int = 100
    ssl_enabled: bool = False
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True


@dataclass
class StorageConfig:
    """存储配置"""
    upload_path: str
    temp_path: str
    cache_path: str
    max_upload_size: int = 104857600  # 100MB

    # OSS配置
    oss_enabled: bool = False
    oss_access_key_id: str | None = None
    oss_access_key_secret: str | None = None
    oss_bucket: str | None = None
    oss_endpoint: str | None = None

    # AWS S3配置
    aws_s3_enabled: bool = False
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "cn-north-1"
    aws_s3_bucket: str | None = None


@dataclass
class MonitoringConfig:
    """监控配置"""
    log_path: str
    log_level: str = "INFO"
    log_format: str = "json"
    log_max_bytes: int = 104857600  # 100MB
    log_backup_count: int = 30

    # Prometheus
    prometheus_enabled: bool = False
    prometheus_port: int = 9090

    # Sentry
    sentry_enabled: bool = False
    sentry_dsn: str | None = None
    sentry_environment: str = "production"

    # Grafana
    grafana_enabled: bool = False
    grafana_port: int = 3001


@dataclass
class AlertConfig:
    """告警配置"""
    enabled: bool = False
    severity_threshold: str = "warning"

    # 邮件告警
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    email_to: str | None = None

    # Webhook告警
    webhook_url: str | None = None

    # 钉钉告警
    dingtalk_webhook_url: str | None = None

    # 企业微信告警
    wework_webhook_url: str | None = None


@dataclass
class MicroserviceConfig:
    """微服务配置"""
    yunpat_url: str
    yunpat_port: int = 8020
    yunpat_default_llm: str = "deepseek-chat"

    xianuo_url: str | None = None
    xianuo_port: int = 8021

    crawler_url: str | None = None
    crawler_port: int = 8022

    optimization_url: str | None = None
    optimization_port: int = 8023

    visualization_url: str | None = None
    visualization_port: int = 8024

    collaboration_url: str | None = None
    collaboration_port: int = 8025


@dataclass
class FeatureConfig:
    """功能开关配置"""
    advanced_search: bool = True
    knowledge_graph: bool = True
    patent_analysis: bool = True
    legal_ai: bool = True
    nlp_enhanced: bool = True
    multimodal: bool = True

    browser_automation_enabled: bool = True
    browser_headless: bool = True

    mcp_enabled: bool = True


@dataclass
class AthenaConfig:
    """Athena平台统一配置类"""

    # 基础配置
    env: str = "development"
    athena_home: str = "/app/athena"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    timezone: str = "Asia/Shanghai"

    # 子配置
    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(
        host="localhost", port=5432, user="postgres",
        password="", database="athena_db"
    ))
    redis: RedisConfig = field(default_factory=lambda: RedisConfig(
        host="localhost", port=6379, password="", db=0
    ))
    qdrant: QdrantConfig = field(default_factory=lambda: QdrantConfig(
        host="localhost", port=6333, collection="athena_vectors"
    ))
    ai_models: AIModelConfig = field(default_factory=AIModelConfig)
    security: SecurityConfig = field(default_factory=lambda: SecurityConfig(
        jwt_secret_key="change-this-secret-key"
    ))
    storage: StorageConfig = field(default_factory=lambda: StorageConfig(
        upload_path="./uploads", temp_path="./temp", cache_path="./cache"
    ))
    monitoring: MonitoringConfig = field(default_factory=lambda: MonitoringConfig(
        log_path="./logs"
    ))
    alerts: AlertConfig = field(default_factory=AlertConfig)
    microservices: MicroserviceConfig = field(default_factory=lambda: MicroserviceConfig(
        yunpat_url="http://localhost:8020"
    ))
    features: FeatureConfig = field(default_factory=FeatureConfig)

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.env.lower() == "development"

    @property
    def is_staging(self) -> bool:
        """是否为预发布环境"""
        return self.env.lower() == "staging"

    @property
    def pythonpath(self) -> str:
        """Python路径"""
        return self.athena_home


class ConfigLoader:
    """
    统一配置加载器

    使用示例:
        # 加载默认环境配置
        config = ConfigLoader.load()

        # 加载指定环境配置
        config = ConfigLoader.load(env="production")

        # 验证配置
        ConfigLoader.validate(config)
    """

    # 支持的环境类型
    SUPPORTED_ENVS = {"development", "staging", "production", "testing"}

    # 环境变量文件映射
    ENV_FILES = {
        "development": ".env.development",
        "staging": ".env.staging",
        "production": ".env.production.unified",
        "testing": ".env.testing",
    }

    @classmethod
    def _get_env_file(cls, env: str) -> Path:
        """获取环境变量文件路径"""
        # 获取项目根目录
        root_dir = Path(__file__).parent.parent.absolute()

        # 尝试多个可能的文件位置
        env_filename = cls.ENV_FILES.get(env, f".env.{env}")

        possible_paths = [
            root_dir / env_filename,
            root_dir / f".env.{env}",
            root_dir / "config" / f".env.{env}",
            root_dir / "production" / "config" / f"{env}" / ".env",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # 如果都没找到，返回默认路径
        return root_dir / env_filename

    @classmethod
    def _load_env_file(cls, env_file: Path) -> bool:
        """加载环境变量文件"""
        if not env_file.exists():
            logger.warning(f"环境变量文件不存在: {env_file}")
            return False

        if DOTENV_AVAILABLE:
            load_dotenv(env_file, override=True)
            logger.info(f"已加载环境变量文件: {env_file}")
            return True
        else:
            # 回退方案：手动解析.env文件
            logger.warning("python-dotenv未安装，使用简单的.env解析器")
            cls._parse_simple_env(env_file)
            return True

    @classmethod
    def _parse_simple_env(cls, env_file: Path) -> None:
        """简单的.env文件解析器（回退方案）"""
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 移除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # 设置环境变量（如果尚未设置）
                    if key not in os.environ:
                        os.environ[key] = value

    @classmethod
    def _get_env_var(cls, key: str, default: Any = None, required: bool = False) -> Any:
        """
        获取环境变量值

        Args:
            key: 环境变量名
            default: 默认值
            required: 是否必需

        Returns:
            环境变量值

        Raises:
            MissingRequiredVariableError: 当必需变量缺失时
        """
        value = os.environ.get(key, default)

        if required and value is None:
            raise MissingRequiredVariableError(key)

        # 类型转换
        if isinstance(default, bool) and isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int) and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        elif isinstance(default, float) and isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default

        return value

    @classmethod
    def load(cls, env: str | None = None, config_file: str | None = None) -> AthenaConfig:
        """
        加载配置

        Args:
            env: 环境类型 (development/staging/production/testing)
                   如果为None，则从ATHENA_ENV环境变量读取

            config_file: 自定义配置文件路径（可选）

        Returns:
            AthenaConfig: 配置对象
        """
        # 确定环境类型
        if env is None:
            env = cls._get_env_var("ATHENA_ENV", "development")
        elif env not in cls.SUPPORTED_ENVS:
            raise ConfigurationError(f"不支持的环境类型: {env}，支持的类型: {cls.SUPPORTED_ENVS}")

        # 加载环境变量文件
        if config_file:
            env_file = Path(config_file)
        else:
            env_file = cls._get_env_file(env)

        cls._load_env_file(env_file)

        # 构建配置对象
        config = cls._build_config(env)

        logger.info(f"已加载 {env} 环境配置")
        return config

    @classmethod
    def _build_config(cls, env: str) -> AthenaConfig:
        """构建配置对象"""
        return AthenaConfig(
            # 基础配置
            env=cls._get_env_var("ATHENA_ENV", env),
            athena_home=cls._get_env_var("ATHENA_HOME", "/app/athena"),
            debug=cls._get_env_var("DEBUG", False),
            log_level=cls._get_env_var("LOG_LEVEL", "INFO"),
            host=cls._get_env_var("HOST", "0.0.0.0"),
            port=cls._get_env_var("PORT", 8000),
            workers=cls._get_env_var("WORKERS", 4),
            timezone=cls._get_env_var("TZ", "Asia/Shanghai"),

            # 数据库配置
            database=DatabaseConfig(
                host=cls._get_env_var("POSTGRES_HOST", "localhost"),
                port=cls._get_env_var("POSTGRES_PORT", 5432),
                user=cls._get_env_var("POSTGRES_USER", "postgres"),
                password=cls._get_env_var("POSTGRES_PASSWORD", ""),
                database=cls._get_env_var("POSTGRES_DB", "athena_db"),
                pool_size=cls._get_env_var("POSTGRES_POOL_SIZE", 50),
                max_overflow=cls._get_env_var("POSTGRES_MAX_OVERFLOW", 100),
                pool_timeout=cls._get_env_var("POSTGRES_POOL_TIMEOUT", 30),
                pool_recycle=cls._get_env_var("POSTGRES_POOL_RECYCLE", 3600),
                pool_pre_ping=cls._get_env_var("POSTGRES_POOL_PRE_PING", True),
                read_replica_host=cls._get_env_var("POSTGRES_READ_REPLICA_HOST", None),
                read_replica_port=cls._get_env_var("POSTGRES_READ_REPLICA_PORT", None),
                read_replica_enabled=cls._get_env_var("POSTGRES_READ_REPLICA_ENABLED", False),
            ),

            # Redis配置
            redis=RedisConfig(
                host=cls._get_env_var("REDIS_HOST", "localhost"),
                port=cls._get_env_var("REDIS_PORT", 6379),
                password=cls._get_env_var("REDIS_PASSWORD", ""),
                db=cls._get_env_var("REDIS_DB", 0),
                cluster_mode=cls._get_env_var("REDIS_CLUSTER_MODE", False),
                cluster_nodes=cls._get_env_var("REDIS_CLUSTER_NODES", None),
                sentinel_enabled=cls._get_env_var("REDIS_SENTINEL_ENABLED", False),
                sentinel_master_name=cls._get_env_var("REDIS_SENTINEL_MASTER_NAME", None),
                sentinel_nodes=cls._get_env_var("REDIS_SENTINEL_NODES", None),
            ),

            # Qdrant配置
            qdrant=QdrantConfig(
                host=cls._get_env_var("QDRANT_HOST", "localhost"),
                port=cls._get_env_var("QDRANT_PORT", 6333),
                api_key=cls._get_env_var("QDRANT_API_KEY", None),
                collection=cls._get_env_var("QDRANT_COLLECTION", "athena_vectors"),
                grpc_port=cls._get_env_var("QDRANT_GRPC_PORT", None),
                cloud_url=cls._get_env_var("QDRANT_CLOUD_URL", None),
                cloud_api_key=cls._get_env_var("QDRANT_CLOUD_API_KEY", None),
                vector_dimension=cls._get_env_var("VECTOR_DIMENSION", 768),
                similarity_threshold=cls._get_env_var("VECTOR_SIMILARITY_THRESHOLD", 0.75),
                search_limit=cls._get_env_var("VECTOR_SEARCH_LIMIT", 100),
            ),

            # AI模型配置
            ai_models=AIModelConfig(
                glm_api_key=cls._get_env_var("GLM_API_KEY", None),
                glm_base_url=cls._get_env_var("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                glm_model=cls._get_env_var("GLM_MODEL", "glm-4"),
                glm_max_tokens=cls._get_env_var("GLM_MAX_TOKENS", 4000),
                glm_temperature=cls._get_env_var("GLM_TEMPERATURE", 0.7),
                openai_api_key=cls._get_env_var("OPENAI_API_KEY", None),
                openai_base_url=cls._get_env_var("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                openai_model=cls._get_env_var("OPENAI_MODEL", "gpt-4-turbo-preview"),
                openai_max_tokens=cls._get_env_var("OPENAI_MAX_TOKENS", 4000),
                openai_temperature=cls._get_env_var("OPENAI_TEMPERATURE", 0.7),
                deepseek_api_key=cls._get_env_var("DEEPSEEK_API_KEY", None),
                deepseek_base_url=cls._get_env_var("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                deepseek_model=cls._get_env_var("DEEPSEEK_MODEL", "deepseek-chat"),
                gemini_api_key=cls._get_env_var("GEMINI_API_KEY", None),
                gemini_model=cls._get_env_var("GEMINI_MODEL", "gemini-pro"),
            ),

            # 安全配置
            security=SecurityConfig(
                jwt_secret_key=cls._get_env_var("JWT_SECRET_KEY", "change-this-secret-key"),
                jwt_algorithm=cls._get_env_var("JWT_ALGORITHM", "HS256"),
                jwt_expire_hours=cls._get_env_var("JWT_EXPIRE_HOURS", 24),
                jwt_refresh_expire_days=cls._get_env_var("JWT_REFRESH_EXPIRE_DAYS", 30),
                encryption_key=cls._get_env_var("ENCRYPTION_KEY", None),
                cors_origins=cls._get_env_var("CORS_ORIGINS", "*"),
                api_key_required=cls._get_env_var("API_KEY_REQUIRED", True),
                api_rate_limit_enabled=cls._get_env_var("API_RATE_LIMIT_ENABLED", True),
                api_rate_limit_per_minute=cls._get_env_var("API_RATE_LIMIT_PER_MINUTE", 100),
                ssl_enabled=cls._get_env_var("SSL_ENABLED", False),
                session_cookie_secure=cls._get_env_var("SESSION_COOKIE_SECURE", True),
                session_cookie_httponly=cls._get_env_var("SESSION_COOKIE_HTTPONLY", True),
            ),

            # 存储配置
            storage=StorageConfig(
                upload_path=cls._get_env_var("UPLOAD_PATH", "./uploads"),
                temp_path=cls._get_env_var("TEMP_PATH", "./temp"),
                cache_path=cls._get_env_var("CACHE_PATH", "./cache"),
                max_upload_size=cls._get_env_var("MAX_UPLOAD_SIZE", 104857600),
                oss_enabled=cls._get_env_var("OSS_ENABLED", False),
                oss_access_key_id=cls._get_env_var("OSS_ACCESS_KEY_ID", None),
                oss_access_key_secret=cls._get_env_var("OSS_ACCESS_KEY_SECRET", None),
                oss_bucket=cls._get_env_var("OSS_BUCKET", None),
                oss_endpoint=cls._get_env_var("OSS_ENDPOINT", None),
                aws_s3_enabled=cls._get_env_var("AWS_S3_ENABLED", False),
                aws_access_key_id=cls._get_env_var("AWS_ACCESS_KEY_ID", None),
                aws_secret_access_key=cls._get_env_var("AWS_SECRET_ACCESS_KEY", None),
                aws_region=cls._get_env_var("AWS_REGION", "cn-north-1"),
                aws_s3_bucket=cls._get_env_var("AWS_S3_BUCKET", None),
            ),

            # 监控配置
            monitoring=MonitoringConfig(
                log_path=cls._get_env_var("LOG_PATH", "./logs"),
                log_level=cls._get_env_var("LOG_LEVEL", "INFO"),
                log_format=cls._get_env_var("LOG_FORMAT", "json"),
                log_max_bytes=cls._get_env_var("LOG_MAX_BYTES", 104857600),
                log_backup_count=cls._get_env_var("LOG_BACKUP_COUNT", 30),
                prometheus_enabled=cls._get_env_var("PROMETHEUS_ENABLED", False),
                prometheus_port=cls._get_env_var("PROMETHEUS_PORT", 9090),
                sentry_enabled=cls._get_env_var("SENTRY_ENABLED", False),
                sentry_dsn=cls._get_env_var("SENTRY_DSN", None),
                sentry_environment=cls._get_env_var("SENTRY_ENVIRONMENT", env),
                grafana_enabled=cls._get_env_var("GRAFANA_ENABLED", False),
                grafana_port=cls._get_env_var("GRAFANA_PORT", 3001),
            ),

            # 告警配置
            alerts=AlertConfig(
                enabled=cls._get_env_var("ALERT_ENABLED", False),
                severity_threshold=cls._get_env_var("ALERT_SEVERITY_THRESHOLD", "warning"),
                smtp_host=cls._get_env_var("SMTP_HOST", None),
                smtp_port=cls._get_env_var("SMTP_PORT", 587),
                smtp_username=cls._get_env_var("SMTP_USERNAME", None),
                smtp_password=cls._get_env_var("SMTP_PASSWORD", None),
                email_to=cls._get_env_var("ALERT_EMAIL_TO", None),
                webhook_url=cls._get_env_var("ALERT_WEBHOOK_URL", None),
                dingtalk_webhook_url=cls._get_env_var("DINGTALK_WEBHOOK_URL", None),
                wework_webhook_url=cls._get_env_var("WEWORK_WEBHOOK_URL", None),
            ),

            # 微服务配置
            microservices=MicroserviceConfig(
                yunpat_url=cls._get_env_var("YUNPAT_URL", "http://localhost:8020"),
                yunpat_port=cls._get_env_var("YUNPAT_PORT", 8020),
                yunpat_default_llm=cls._get_env_var("YUNPAT_DEFAULT_LLM", "deepseek-chat"),
                xianuo_url=cls._get_env_var("XIANUO_URL", None),
                xianuo_port=cls._get_env_var("XIANUO_PORT", 8021),
                crawler_url=cls._get_env_var("CRAWLER_URL", None),
                crawler_port=cls._get_env_var("CRAWLER_PORT", 8022),
                optimization_url=cls._get_env_var("OPTIMIZATION_URL", None),
                optimization_port=cls._get_env_var("OPTIMIZATION_PORT", 8023),
                visualization_url=cls._get_env_var("VISUALIZATION_URL", None),
                visualization_port=cls._get_env_var("VISUALIZATION_PORT", 8024),
                collaboration_url=cls._get_env_var("COLLABORATION_URL", None),
                collaboration_port=cls._get_env_var("COLLABORATION_PORT", 8025),
            ),

            # 功能开关配置
            features=FeatureConfig(
                advanced_search=cls._get_env_var("FEATURE_ADVANCED_SEARCH", True),
                knowledge_graph=cls._get_env_var("FEATURE_KNOWLEDGE_GRAPH", True),
                patent_analysis=cls._get_env_var("FEATURE_PATENT_ANALYSIS", True),
                legal_ai=cls._get_env_var("FEATURE_LEGAL_AI", True),
                nlp_enhanced=cls._get_env_var("FEATURE_NLP_ENHANCED", True),
                multimodal=cls._get_env_var("FEATURE_MULTIMODAL", True),
                browser_automation_enabled=cls._get_env_var("BROWSER_AUTOMATION_ENABLED", True),
                browser_headless=cls._get_env_var("BROWSER_HEADLESS", True),
                mcp_enabled=cls._get_env_var("MCP_ENABLED", True),
            ),
        )

    @classmethod
    def validate(cls, config: AthenaConfig, strict: bool = False) -> list[str]:
        """
        验证配置

        Args:
            config: 配置对象
            strict: 是否严格模式（严格模式下会将警告也视为错误）

        Returns:
            list[str]: 错误列表（空列表表示验证通过）
        """
        errors = []
        warnings = []

        # 生产环境必须验证的配置
        if config.is_production:
            # 数据库配置验证
            if not config.database.password or config.database.password == "CHANGE_THIS_TO_STRONG_PASSWORD":
                errors.append("生产环境必须设置数据库密码")

            if config.database.pool_size < 10:
                warnings.append("生产环境建议数据库连接池大小至少为10")

            # Redis配置验证
            if config.redis.password == "CHANGE_THIS_TO_STRONG_REDIS_PASSWORD":
                errors.append("生产环境必须设置Redis密码")

            # 安全配置验证
            if config.security.jwt_secret_key in [
                "change-this-secret-key",
                "CHANGE_THIS_TO_SECURE_RANDOM_STRING_MIN_64_CHARS"
            ]:
                errors.append("生产环境必须设置JWT密钥")

            if len(config.security.jwt_secret_key) < 32:
                errors.append("JWT密钥长度必须至少32个字符")

            if config.debug:
                errors.append("生产环境必须关闭DEBUG模式")

            if config.log_level == "DEBUG":
                warnings.append("生产环境建议日志级别设置为WARNING或ERROR")

            # CORS配置验证
            if config.security.cors_origins == "*":
                errors.append("生产环境必须限制CORS来源域名")

            # SSL配置验证
            if not config.security.ssl_enabled:
                warnings.append("生产环境强烈建议启用SSL")

        # 通用验证
        # 确保路径存在或可创建
        for path_name, path_value in [
            ("上传路径", config.storage.upload_path),
            ("临时路径", config.storage.temp_path),
            ("缓存路径", config.storage.cache_path),
            ("日志路径", config.monitoring.log_path),
        ]:
            if not path_value:
                warnings.append(f"{path_name}未配置")

        # AI模型配置验证
        ai_models_count = sum([
            bool(config.ai_models.glm_api_key),
            bool(config.ai_models.openai_api_key),
            bool(config.ai_models.deepseek_api_key),
        ])

        if ai_models_count == 0:
            warnings.append("未配置任何AI模型API密钥")

        # 存储配置验证
        if config.storage.oss_enabled and not config.storage.oss_access_key_id:
            errors.append("启用了OSS但未配置access_key_id")

        # 监控配置验证
        if config.monitoring.sentry_enabled and not config.monitoring.sentry_dsn:
            errors.append("启用了Sentry但未配置DSN")

        # 告警配置验证
        if config.alerts.enabled:
            if not any([
                config.alerts.email_to,
                config.alerts.webhook_url,
                config.alerts.dingtalk_webhook_url,
                config.alerts.wework_webhook_url,
            ]):
                warnings.append("启用了告警但未配置任何告警接收方式")

        # 合并错误和警告
        if strict:
            errors.extend(warnings)

        return errors

    @classmethod
    def print_config(cls, config: AthenaConfig, hide_secrets: bool = True) -> None:
        """
        打印配置信息（用于调试）

        Args:
            config: 配置对象
            hide_secrets: 是否隐藏敏感信息
        """
        def mask_value(value: Any, key: str = "") -> str:
            """遮蔽敏感信息"""
            if not hide_secrets:
                return str(value)

            # 敏感字段列表
            sensitive_keywords = [
                "password", "secret", "key", "token",
                "api_key", "access_key", "private_key"
            ]

            if any(keyword in key.lower() for keyword in sensitive_keywords):
                if value and len(str(value)) > 8:
                    return f"{str(value)[:4]}...{str(value)[-4:]}"
                return "***"

            return str(value)

        print("=" * 60)
        print(f"Athena配置 - {config.env.upper()}环境")
        print("=" * 60)
        print(f"Athena Home: {config.athena_home}")
        print(f"Debug: {config.debug}")
        print(f"Log Level: {config.log_level}")
        print(f"Host: {config.host}:{config.port}")
        print(f"Workers: {config.workers}")
        print()
        print("--- 数据库配置 ---")
        print(f"Host: {config.database.host}:{config.database.port}")
        print(f"Database: {config.database.database}")
        print(f"User: {config.database.user}")
        print(f"Password: {mask_value(config.database.password)}")
        print(f"Pool Size: {config.database.pool_size}")
        print()
        print("--- Redis配置 ---")
        print(f"Host: {config.redis.host}:{config.redis.port}")
        print(f"Password: {mask_value(config.redis.password)}")
        print(f"DB: {config.redis.db}")
        print()
        print("--- AI模型配置 ---")
        print(f"GLM API Key: {mask_value(config.ai_models.glm_api_key)}")
        print(f"OpenAI API Key: {mask_value(config.ai_models.openai_api_key)}")
        print(f"DeepSeek API Key: {mask_value(config.ai_models.deepseek_api_key)}")
        print()
        print("--- 安全配置 ---")
        print(f"JWT Secret: {mask_value(config.security.jwt_secret_key)}")
        print(f"CORS Origins: {config.security.cors_origins}")
        print(f"SSL Enabled: {config.security.ssl_enabled}")
        print()
        print("=" * 60)


# 全局配置缓存
_global_config: AthenaConfig | None = None


def get_config(env: str | None = None, reload: bool = False) -> AthenaConfig:
    """
    获取全局配置（单例模式）

    Args:
        env: 环境类型（首次加载时指定）
        reload: 是否重新加载

    Returns:
        AthenaConfig: 配置对象
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = ConfigLoader.load(env)

    return _global_config


def init_config(env: str | None = None) -> AthenaConfig:
    """
    初始化配置（应用启动时调用）

    Args:
        env: 环境类型

    Returns:
        AthenaConfig: 配置对象
    """
    logger.info(f"正在初始化Athena配置 - 环境: {env or '默认'}")

    config = ConfigLoader.load(env)

    # 生产环境验证
    if config.is_production:
        errors = ConfigLoader.validate(config, strict=False)
        if errors:
            logger.error("配置验证失败:")
            for error in errors:
                logger.error(f"  - {error}")
            raise ConfigurationError(f"配置验证失败: {'; '.join(errors)}")

    return config


# 便捷函数
def is_production() -> bool:
    """是否为生产环境"""
    return get_config().is_production


def is_development() -> bool:
    """是否为开发环境"""
    return get_config().is_development


def get_database_url() -> str:
    """获取数据库连接URL"""
    return get_config().database.url


def get_redis_url() -> str:
    """获取Redis连接URL"""
    return get_config().redis.url


if __name__ == "__main__":
    # 测试代码
    import sys

    print("Athena配置加载器测试")
    print("=" * 60)

    # 加载配置
    env = sys.argv[1] if len(sys.argv) > 1 else "development"
    config = ConfigLoader.load(env)

    # 打印配置
    ConfigLoader.print_config(config)

    # 验证配置
    errors = ConfigLoader.validate(config, strict=False)
    if errors:
        print("\n验证警告:")
        for error in errors:
            print(f"  ⚠️  {error}")
    else:
        print("\n✅ 配置验证通过")
