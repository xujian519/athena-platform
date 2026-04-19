#!/usr/bin/env python3
"""
统一配置管理
Unified Configuration Management

使用Pydantic进行类型验证和配置管理

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.1
"""

from __future__ import annotations
from enum import Enum
from pathlib import Path
from typing import Any

# 尝试使用pydantic-settings,如果不存在则使用pydantic v1兼容模式
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings

    PYDANTIC_V2 = False

try:
    from pydantic import Field, field_validator
except ImportError:
    from pydantic import Field


class Environment(str, Enum):
    """运行环境"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class PerceptionConfig(BaseSettings):
    """感知模块配置"""

    # 基础配置
    max_text_length: int = Field(default=10000, gt=0, description="最大文本长度")
    max_batch_size: int = Field(default=100, gt=0, description="批处理最大数量")

    # 功能开关
    enable_sentiment_analysis: bool = True
    enable_entity_extraction: bool = True
    enable_keyword_extraction: bool = True
    enable_language_detection: bool = True

    # 性能配置
    cache_enabled: bool = True
    cache_size: int = Field(default=1000, gt=0, description="缓存大小")
    cache_ttl: int = Field(default=3600, gt=0, description="缓存生存时间(秒)")

    # 并发配置
    max_concurrent_requests: int = Field(default=100, gt=0, description="最大并发请求数")
    request_timeout: int = Field(default=30, gt=0, description="请求超时时间(秒)")

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(env_prefix="PERCEPTION_", env_file=".env", extra="ignore")
    else:

        class Config:
            env_prefix = "PERCEPTION_"
            env_file = ".env"


class AgentConfig(BaseSettings):
    """智能体配置"""

    # 基础配置
    heartbeat_interval: int = Field(30, gt=0, description="心跳间隔(秒)")
    task_timeout: int = Field(300, gt=0, description="任务超时时间(秒)")

    # 搜索配置
    search_max_concurrent: int = Field(3, gt=0, description="最大并发搜索数")
    search_timeout: int = Field(60, gt=0, description="搜索超时时间(秒)")
    search_cache_size: int = Field(200, gt=0, description="搜索缓存大小")

    # 性能配置
    performance_metrics_enabled: bool = True
    performance_history_size: int = Field(1000, gt=0, description="性能历史记录数量")

    class Config:
        env_prefix = "AGENT_"
        env_file = ".env"
        extra = "ignore"


class IntentConfig(BaseSettings):
    """意图识别配置"""

    # 模型配置
    model_path: str = Field("models/intent", description="模型路径")
    model_version: str = Field("latest", description="模型版本")

    # 分类配置
    confidence_threshold: float = Field(0.7, gt=0, le=1, description="置信度阈值")
    max_top_k: int = Field(5, gt=0, description="最大返回候选数")

    # 性能配置
    batch_inference_enabled: bool = True
    max_batch_size: int = Field(32, gt=0, description="最大推理批次")

    class Config:
        env_prefix = "INTENT_"
        env_file = ".env"
        extra = "ignore"


class SecurityConfig(BaseSettings):
    """安全配置"""

    # 安全级别
    security_level: str = Field("high", description="安全级别: low/medium/high/strict")

    # 限制配置
    max_input_length: int = Field(50000, gt=0, description="最大输入长度")
    max_output_length: int = Field(100000, gt=0, description="最大输出长度")

    # 速率限制
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = Field(60, gt=0, description="每分钟请求限制")
    rate_limit_per_hour: int = Field(1000, gt=0, description="每小时请求限制")

    # 功能开关
    enable_xss_protection: bool = True
    enable_sql_injection_protection: bool = True
    enable_template_injection_protection: bool = True

    @field_validator("security_level", mode="before")
    @classmethod
    def validate_security_level(cls, v) -> str:
        valid_levels = ["low", "medium", "high", "strict"]
        if v not in valid_levels:
            raise ValueError(f"security_level must be one of {valid_levels}")
        return v

    class Config:
        env_prefix = "SECURITY_"
        env_file = ".env"
        extra = "ignore"


class LoggingConfig(BaseSettings):
    """日志配置"""

    level: str = Field("INFO", description="日志级别")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 文件配置
    file_enabled: bool = True
    file_path: str = Field("logs/athena.log", description="日志文件路径")
    max_bytes: int = Field(10485760, gt=0, description="日志文件最大大小(10MB)")
    backup_count: int = Field(5, ge=0, description="日志备份数量")

    # 结构化日志
    json_enabled: bool = False

    @field_validator("level", mode="before")
    @classmethod
    def validate_level(cls, v) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"level must be one of {valid_levels}")
        return v.upper()

    class Config:
        env_prefix = "LOGGING_"
        env_file = ".env"
        extra = "ignore"


class DatabaseConfig(BaseSettings):
    """
    数据库配置

    PostgreSQL配置说明:
    - 使用本地PostgreSQL 17.7 (Homebrew安装)
    - 不使用Docker容器中的PostgreSQL
    - 服务端口: 5432
    - 主要数据库: athena, patent_db, patent_rules, xiaonuo_db
    """

    # PostgreSQL (本地17.7版本,不使用Docker)
    postgres_host: str = Field("localhost", description="PostgreSQL主机 (本地)")
    postgres_port: int = Field(5432, gt=0, le=65535, description="PostgreSQL端口")
    postgres_db: str = Field("athena", description="数据库名")
    postgres_user: str = Field("xiaonuo", description="用户名")
    postgres_password: str = Field("", description="密码")
    postgres_min_connections: int = Field(5, gt=0, description="最小连接数")
    postgres_max_connections: int = Field(20, gt=0, description="最大连接数")

    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis
    redis_host: str = Field("localhost", description="Redis主机")
    redis_port: int = Field(6379, gt=0, le=65535, description="Redis端口")
    redis_db: int = Field(0, ge=0, description="Redis数据库")
    redis_password: str = Field(None, description="Redis密码")

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Neo4j 图数据库 (v3.0.0 - 统一使用Neo4j,已弃用NebulaGraph)
    neo4j_uri: str = Field("bolt://localhost:7687", description="Neo4j连接URI")
    neo4j_username: str = Field("neo4j", description="Neo4j用户名")
    neo4j_password: str = Field("athena_neo4j_2024", description="Neo4j密码")
    neo4j_database: str = Field("neo4j", description="Neo4j数据库名称")

    @property
    def neo4j_bolt_uri(self) -> str:
        """获取Neo4j Bolt URI"""
        return self.neo4j_uri

    @property
    def neo4j_http_uri(self) -> str:
        """获取Neo4j HTTP URI"""
        return self.neo4j_uri.replace("bolt://", "http://").replace(":7687", ":7474")

    # Qdrant
    qdrant_url: str = Field("http://localhost:6333", description="Qdrant向量数据库URL")
    qdrant_collection: str = Field("unified_legal_vectors", description="Qdrant集合名称")
    qdrant_api_key: str = Field(None, description="Qdrant API密钥")

    class Config:
        env_prefix = "DB_"
        env_file = ".env"
        extra = "ignore"


class ServiceConfig(BaseSettings):
    """服务配置"""

    # API服务
    api_host: str = Field("0.0.0.0", description="API监听地址")
    api_port: int = Field(8000, gt=0, le=65535, description="API监听端口")
    api_workers: int = Field(1, gt=0, description="API工作进程数")

    # WebSocket
    websocket_enabled: bool = True
    websocket_port: int = Field(8001, gt=0, le=65535, description="WebSocket端口")

    class Config:
        env_prefix = "SERVICE_"
        env_file = ".env"
        extra = "ignore"


class MultimodalConfig(BaseSettings):
    """多模态文件系统配置"""

    # 服务配置
    base_url: str = Field("http://localhost:8001", description="多模态文件系统基础URL")
    username: str = Field("athena_platform", description="认证用户名")
    password: str = Field("", description="认证密码")

    # 安全配置
    max_upload_size: int = Field(100 * 1024 * 1024, gt=0, description="最大上传文件大小(字节)")
    max_filename_length: int = Field(255, gt=0, description="最大文件名长度")
    allowed_file_types: list[str] = Field(
        default=["image", "document", "audio", "video", "data"], description="允许的文件类型列表"
    )

    # 超时配置
    request_timeout: int = Field(30, gt=0, description="请求超时时间(秒)")
    upload_timeout: int = Field(300, gt=0, description="上传超时时间(秒)")

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = Field(3600, gt=0, description="缓存生存时间(秒)")
    cache_dir: str = Field("/tmp/athena_cache", description="缓存目录")

    @property
    def max_upload_size_mb(self) -> int:
        """获取最大上传大小(MB)"""
        return self.max_upload_size // (1024 * 1024)

    class Config:
        env_prefix = "MULTIMODAL_"
        env_file = ".env"
        extra = "ignore"


class ApplicationConfig(BaseSettings):
    """应用主配置"""

    # 环境配置
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # 应用信息
    app_name: str = Field("Athena工作平台", description="应用名称")
    app_version: str = Field("2.0.0", description="应用版本")
    app_description: str = Field("智能专利分析与检索系统", description="应用描述")

    # 子配置
    perception: PerceptionConfig = Field(default_factory=PerceptionConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    intent: IntentConfig = Field(default_factory=IntentConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    service: ServiceConfig = Field(default_factory=ServiceConfig)
    multimodal: MultimodalConfig = Field(default_factory=MultimodalConfig)

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_postgres_url(self) -> str:
        """获取PostgreSQL连接URL"""
        return self.database.postgres_url

    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        return self.database.redis_url

    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == Environment.DEVELOPMENT

    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == Environment.PRODUCTION


# 全局配置实例
_config: ApplicationConfig | None = None


def get_config() -> ApplicationConfig:
    """
    获取全局配置实例

    Returns:
        ApplicationConfig: 配置实例
    """
    global _config
    if _config is None:
        _config = ApplicationConfig()
    return _config


def reload_config() -> ApplicationConfig:
    """
    重新加载配置

    Returns:
        ApplicationConfig: 新的配置实例
    """
    global _config
    _config = ApplicationConfig()
    return _config


def setup_logging(config: LoggingConfig | None = None) -> Any:
    """
    设置日志系统

    Args:
        config: 日志配置,如果为None则使用全局配置
    """
    import logging
    import logging.handlers

    if config is None:
        config = get_config().logging

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 创建格式化器
    if config.json_enabled:
        try:
            from pythonjsonlogger import jsonlogger

            formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        except ImportError:
            formatter = logging.Formatter(config.format)
    else:
        formatter = logging.Formatter(config.format)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器
    if config.file_enabled:
        # 确保日志目录存在
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            config.file_path, maxBytes=config.max_bytes, backupCount=config.backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


# 便捷函数
def get_perception_config() -> PerceptionConfig:
    """获取感知模块配置"""
    return get_config().perception


def get_agent_config() -> AgentConfig:
    """获取智能体配置"""
    return get_config().agent


def get_intent_config() -> IntentConfig:
    """获取意图识别配置"""
    return get_config().intent


def get_security_config() -> SecurityConfig:
    """获取安全配置"""
    return get_config().security


def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    return get_config().database


def get_service_config() -> ServiceConfig:
    """获取服务配置"""
    return get_config().service


def get_multimodal_config() -> MultimodalConfig:
    """获取多模态文件系统配置"""
    return get_config().multimodal
