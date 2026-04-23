"""
配置验证器
Configuration Validator

验证配置的完整性和正确性
"""
from pydantic import BaseModel, validator, Field
from typing import Dict, Any, Optional
from core.config.settings import Settings


class DatabaseConfigValidator(BaseModel):
    """数据库配置验证器"""

    host: str
    port: int
    user: str
    password: str
    name: str
    pool_size: int = 20
    max_overflow: int = 10

    @validator("port")
    def validate_port(cls, v):
        """验证端口号"""
        if not 1 <= v <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return v

    @validator("pool_size")
    def validate_pool_size(cls, v):
        """验证连接池大小"""
        if v <= 0:
            raise ValueError("pool_size must be positive")
        return v

    @validator("password")
    def validate_password(cls, v):
        """验证密码"""
        if not v or len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class RedisConfigValidator(BaseModel):
    """Redis配置验证器"""

    host: str
    port: int
    db: int
    password: str = ""
    pool_size: int = 10

    @validator("port")
    def validate_port(cls, v):
        """验证端口号"""
        if not 1 <= v <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return v

    @validator("db")
    def validate_db(cls, v):
        """验证数据库编号"""
        if not 0 <= v <= 15:
            raise ValueError("db must be between 0 and 15")
        return v


class LLMConfigValidator(BaseModel):
    """LLM配置验证器"""

    default_provider: str
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 4096

    @validator("temperature")
    def validate_temperature(cls, v):
        """验证温度参数"""
        if not 0 <= v <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return v

    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        """验证最大token数"""
        if v <= 0:
            raise ValueError("max_tokens must be positive")
        return v

    @validator("api_key")
    def validate_api_key(cls, v):
        """验证API密钥"""
        if not v or len(v) < 10:
            raise ValueError("api_key must be at least 10 characters")
        return v


class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_settings(settings: Settings) -> bool:
        """验证Settings实例

        Args:
            settings: Settings实例

        Returns:
            验证是否通过
        """
        try:
            # 验证数据库配置
            DatabaseConfigValidator(
                host=settings.database_host,
                port=settings.database_port,
                user=settings.database_user,
                password=settings.database_password,
                name=settings.database_name,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow
            )

            # 验证Redis配置
            RedisConfigValidator(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                pool_size=settings.redis_pool_size
            )

            # 生产环境需要验证LLM API密钥
            if settings.environment == "production":
                if not settings.llm_api_key or len(settings.llm_api_key) < 10:
                    raise ValueError("Production environment requires valid LLM API key")

            return True

        except Exception as e:
            print(f"配置验证失败: {e}")
            return False

    @staticmethod
    def validate_config_dict(config: Dict[str, Any]) -> bool:
        """验证配置字典

        Args:
            config: 配置字典

        Returns:
            验证是否通过
        """
        try:
            settings = Settings.from_yaml_dict(config)
            return ConfigValidator.validate_settings(settings)
        except Exception as e:
            print(f"配置字典验证失败: {e}")
            return False

    @staticmethod
    def validate_yaml_file(yaml_path: str) -> bool:
        """验证YAML配置文件

        Args:
            yaml_path: YAML文件路径

        Returns:
            验证是否通过
        """
        try:
            settings = Settings.from_yaml(yaml_path)
            return ConfigValidator.validate_settings(settings)
        except Exception as e:
            print(f"YAML文件验证失败: {e}")
            return False


# 便捷函数
def validate_settings(settings: Optional[Settings] = None) -> bool:
    """验证配置

    Args:
        settings: Settings实例，如果为None则使用全局实例

    Returns:
        验证是否通过
    """
    if settings is None:
        from core.config.settings import settings as global_settings
        settings = global_settings

    return ConfigValidator.validate_settings(settings)
