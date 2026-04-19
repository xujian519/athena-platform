from __future__ import annotations
"""
Athena统一环境变量配置管理模块
提供安全的环境变量获取和验证机制
"""
import os
import secrets


class SecurityConfigError(Exception):
    """安全配置错误"""
    pass


def get_env_var(
    key: str,
    default: str | None = None,
    required: bool = True,
    min_length: int | None = None
) -> str:
    """
    安全获取环境变量

    Args:
        key: 环境变量名称
        default: 默认值（如果提供且不是必需的）
        required: 是否必需（默认True）
        min_length: 最小长度要求（用于密码等）

    Returns:
        环境变量的值

    Raises:
        SecurityConfigError: 如果环境变量未设置或不符合要求
    """
    value = os.getenv(key, default)

    if required and not value:
        raise SecurityConfigError(
            f"环境变量 {key} 未设置。请在.env文件中配置该变量。"
        )

    if value and min_length and len(value) < min_length:
        raise SecurityConfigError(
            f"环境变量 {key} 的值长度必须至少为 {min_length} 个字符"
        )

    return value


def get_database_url() -> str:
    """获取数据库连接URL"""
    db_host = get_env_var("DB_HOST", "localhost")
    db_port = get_env_var("DB_PORT", "5432")
    db_user = get_env_var("DB_USER", "postgres")
    db_password = get_env_var("DB_PASSWORD", required=True, min_length=8)
    db_name = get_env_var("DB_NAME", "athena")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def get_redis_url() -> str:
    """获取Redis连接URL"""
    redis_host = get_env_var("REDIS_HOST", "localhost")
    redis_port = get_env_var("REDIS_PORT", "6379")
    redis_password = get_env_var("REDIS_PASSWORD", required=False)

    if redis_password:
        return f"redis://:{redis_password}@{redis_host}:{redis_port}"
    return f"redis://{redis_host}:{redis_port}"


def get_jwt_secret() -> str:
    """获取JWT密钥（必须至少32个字符）"""
    return get_env_var("JWT_SECRET", required=True, min_length=32)


def get_api_key(service_name: str) -> str:
    """
    获取指定服务的API密钥

    Args:
        service_name: 服务名称（如'OPENAI', 'ZHIPU', 'DEEPSEEK'等）

    Returns:
        API密钥
    """
    key = get_env_var(f"{service_name}_API_KEY", required=True)
    return key


def generate_secure_secret(length: int = 32) -> str:
    """
    生成安全的随机密钥

    Args:
        length: 密钥长度（默认32字节）

    Returns:
        十六进制格式的密钥
    """
    return secrets.token_hex(length)


def get_neo4j_config() -> dict:
    """获取Neo4j配置"""
    return {
        "uri": get_env_var("NEO4J_URI", "bolt://localhost:7687"),
        "username": get_env_var("NEO4J_USERNAME", "neo4j"),
        "password": get_env_var("NEO4J_PASSWORD", required=True, min_length=8)
    }


def get_qdrant_config() -> dict:
    """获取Qdrant配置"""
    return {
        "url": get_env_var("QDRANT_URL", "http://localhost:6333"),
        "api_key": get_env_var("QDRANT_API_KEY", required=False)
    }


def validate_security_config() -> dict:
    """
    验证所有安全配置是否完整

    Returns:
        包含验证结果和缺失配置的字典
    """
    required_vars = [
        "DB_PASSWORD",
        "JWT_SECRET"
    ]

    missing_vars = []
    weak_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif len(value) < 32 and "SECRET" in var:
            weak_vars.append(var)

    return {
        "valid": len(missing_vars) == 0 and len(weak_vars) == 0,
        "missing": missing_vars,
        "weak": weak_vars
    }


# 便捷的配置获取函数
class Config:
    """配置类，提供便捷的配置访问"""

    # 数据库配置
    DATABASE_URL = get_database_url()
    REDIS_URL = get_redis_url()

    # 安全配置
    JWT_SECRET = get_jwt_secret()

    # Neo4j配置
    NEO4J = get_neo4j_config()

    # Qdrant配置
    QDRANT = get_qdrant_config()

    # API密钥
    OPENAI_API_KEY = get_api_key("OPENAI") if os.getenv("OPENAI_API_KEY") else None
    ZHIPU_API_KEY = get_api_key("ZHIPU") if os.getenv("ZHIPU_API_KEY") else None
    DEEPSEEK_API_KEY = get_api_key("DEEPSEEK") if os.getenv("DEEPSEEK_API_KEY") else None


# 导出函数
__all__ = [
    "get_env_var",
    "get_database_url",
    "get_redis_url",
    "get_jwt_secret",
    "get_api_key",
    "generate_secure_secret",
    "get_neo4j_config",
    "get_qdrant_config",
    "validate_security_config",
    "Config",
    "SecurityConfigError"
]
