"""
Athena工作平台 - 统一配置管理（第2阶段重构版本）
Unified Configuration Management (Phase 2 Refactored Version)

基于Pydantic Settings的类型安全配置管理
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Literal, Optional
from pathlib import Path
import yaml


class UnifiedSettings(BaseSettings):
    """统一配置管理

    支持配置加载顺序:
    1. 环境变量 (最高优先级)
    2. 服务特定配置
    3. 环境配置
    4. 基础配置 (默认值)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 忽略额外的字段
    )

    # ============================================================================
    # 环境配置
    # ============================================================================
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False

    # ============================================================================
    # 数据库配置
    # ============================================================================
    # 主数据库
    database_host: str = "localhost"
    database_port: int = 5432
    database_user: str = "athena"
    database_password: str = "athena123"
    database_name: str = "athena"

    # 连接池配置
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600

    @property
    def database_url(self) -> str:
        """生成数据库连接URL"""
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    # ============================================================================
    # Redis配置
    # ============================================================================
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # 连接池配置
    redis_pool_size: int = 10
    redis_max_connections: int = 50

    @property
    def redis_url(self) -> str:
        """生成Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ============================================================================
    # Qdrant向量数据库配置
    # ============================================================================
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_https: bool = False
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "athena_vectors"
    qdrant_vector_size: int = 768
    qdrant_distance: str = "Cosine"

    # ============================================================================
    # LLM配置
    # ============================================================================
    llm_default_provider: Literal["openai", "anthropic", "deepseek"] = "anthropic"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # ============================================================================
    # 日志配置
    # ============================================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # ============================================================================
    # 验证器
    # ============================================================================
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """验证环境配置"""
        allowed = ["development", "test", "production"]
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v):
        """验证LLM温度参数"""
        if not 0 <= v <= 2:
            raise ValueError("llm_temperature must be between 0 and 2")
        return v

    # ============================================================================
    # 从YAML文件加载配置
    # ============================================================================
    @classmethod
    def from_yaml_dict(cls, config_dict: dict) -> "UnifiedSettings":
        """从字典创建配置（支持嵌套配置）

        Args:
            config_dict: 配置字典，支持嵌套结构

        Returns:
            UnifiedSettings实例
        """
        # 展开嵌套配置
        flat_config = {}

        for key, value in config_dict.items():
            if isinstance(value, dict):
                # 展开嵌套字典 (database.host -> database_host)
                for sub_key, sub_value in value.items():
                    flat_config[f"{key}_{sub_key}"] = sub_value
            else:
                flat_config[key] = value

        return cls(**flat_config)

    # ============================================================================
    # 单例模式
    # ============================================================================
    _instance: Optional["UnifiedSettings"] = None

    @classmethod
    def get_instance(cls) -> "UnifiedSettings":
        """获取配置单例

        Returns:
            UnifiedSettings实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例（主要用于测试）"""
        cls._instance = None


# 全局配置实例
unified_settings = UnifiedSettings.get_instance()


# 便捷访问函数
def get_unified_settings() -> UnifiedSettings:
    """获取全局配置实例

    Returns:
        UnifiedSettings实例
    """
    return unified_settings
