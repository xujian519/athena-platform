"""
Athena统一配置管理

> 版本: v2.1
> 更新: 2026-04-21
> 说明: 支持Athena、Patent和Neo4j三个数据库

配置分层加载顺序:
1. config/base/ - 基础配置（所有环境共享）
2. config/environments/{ENV}.yml - 环境配置
3. config/services/{SERVICE}.yml - 服务配置
4. 环境变量 - 运行时覆盖
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from typing import Literal, Optional
from pathlib import Path
import yaml
import os


class Settings(BaseSettings):
    """
    统一配置管理类
    
    支持三个数据库:
    1. Athena主库 - 系统数据
    2. Patent专利库 - 专利数据  
    3. Neo4j - 法律世界模型
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== 环境配置 ====================
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False

    # ==================== Athena主库配置 ====================
    database_host: str = "localhost"
    database_port: int = 5432
    database_user: str = "athena"
    database_password: str = "athena123"
    database_name: str = "athena"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600

    @property
    def database_url(self) -> str:
        """Athena主库连接URL"""
        return (
            f"postgresql://{self.database_user}:{self.database_password}@"
            f"{self.database_host}:{self.database_port}/{self.database_name}"
        )

    # ==================== Patent专利库配置 ====================
    patent_db_host: str = "localhost"
    patent_db_port: int = 5432
    patent_db_user: str = "athena"
    patent_db_password: str = ""
    patent_db_name: str = "patent_db"
    patent_db_pool_size: int = 10
    patent_db_max_overflow: int = 20
    patent_db_pool_timeout: int = 30
    patent_db_pool_recycle: int = 3600

    @property
    def patent_db_url(self) -> str:
        """Patent专利库连接URL"""
        pwd = self.patent_db_password or self.database_password
        return (
            f"postgresql://{self.patent_db_user}:{pwd}@"
            f"{self.patent_db_host}:{self.patent_db_port}/{self.patent_db_name}"
        )

    # ==================== Neo4j法律世界模型配置 ====================
    neo4j_host: str = "localhost"
    neo4j_port: int = 7687
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    @property
    def neo4j_bolt_url(self) -> str:
        """Neo4j Bolt协议URL"""
        pwd = self.neo4j_password or "neo4j"
        return f"bolt://{self.neo4j_user}:{pwd}@{self.neo4j_host}:{self.neo4j_port}"

    @property
    def neo4j_http_url(self) -> str:
        """Neo4j HTTP协议URL"""
        return f"http://{self.neo4j_host}:7474"

    # ==================== Redis配置 ====================
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis123"
    redis_db: int = 0
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    redis_max_connections: int = 50

    @property
    def redis_url(self) -> str:
        """Redis连接URL"""
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ==================== LLM配置 ====================
    llm_provider: Literal["openai", "anthropic", "deepseek", "glm", "ollama"] = "ollama"
    llm_api_key: str = ""
    llm_base_url: Optional[str] = None
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_timeout: int = 60
    llm_retry: int = 3

    # ==================== 配置验证 ====================
    @model_validator(mode='after')
    def validate_llm_config(self) -> "Settings":
        """验证LLM配置"""
        if self.llm_provider == "ollama":
            return self
        if not self.llm_api_key or len(self.llm_api_key) < 10:
            raise ValueError(
                f"LLM API key must be at least 10 characters for provider '{self.llm_provider}'"
            )
        return self

    # ==================== 配置加载方法 ====================
    @classmethod
    def load(
        cls,
        environment: str = None,
        service: str = None
    ) -> "Settings":
        """加载完整配置（支持继承）"""
        config = {}

        # 1. 加载基础配置
        base_dir = Path("config/base")
        if base_dir.exists():
            for yaml_file in sorted(base_dir.glob("*.yml")):
                try:
                    with open(yaml_file) as f:
                        file_config = yaml.safe_load(f)
                        if file_config:
                            config.update(file_config)
                except Exception as e:
                    print(f"警告: 无法加载基础配置 {yaml_file}: {e}")

        # 2. 加载环境配置
        env = environment or cls._get_environment()
        env_file = Path(f"config/environments/{env}.yml")
        if env_file.exists():
            try:
                with open(env_file) as f:
                    env_config = yaml.safe_load(f)
                    if env_config:
                        config.update(env_config)
            except Exception as e:
                print(f"警告: 无法加载环境配置 {env_file}: {e}")

        # 3. 加载服务配置（可选）
        if service:
            service_file = Path(f"config/services/{service}.yml")
            if service_file.exists():
                try:
                    with open(service_file) as f:
                        service_config = yaml.safe_load(f)
                        if service_config:
                            config.update(service_config)
                except Exception as e:
                    print(f"警告: 无法加载服务配置 {service_file}: {e}")

        # 4. 环境变量会自动覆盖
        return cls(**config)

    @staticmethod
    def _get_environment() -> str:
        """从环境变量获取当前环境"""
        return os.getenv("ATHENA_ENV", "development")

    # ==================== 单例模式 ====================
    _instance: Optional["Settings"] = None

    @classmethod
    def get_instance(cls) -> "Settings":
        """获取配置单例"""
        if cls._instance is None:
            cls._instance = cls.load()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例"""
        cls._instance = None


# ==================== 全局配置实例 ====================
_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    """获取全局配置实例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings.get_instance()
    return _settings_instance

# 向后兼容
settings = get_settings()

__all__ = [
    "Settings",
    "get_settings",
    "settings",
]
