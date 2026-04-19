#!/usr/bin/env python3
"""
Athena平台统一配置管理器
Unified Configuration Manager for Athena Platform

创建时间: 2025-12-29
版本: v3.0.0
功能: 加载和管理统一配置,支持环境变量覆盖
技术决策: TD-001 - 统一图数据库选择为Neo4j
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AthenaConfig:
    """Athena平台配置类"""

    # 平台信息
    platform_name: str = "Athena工作平台"
    platform_version: str = "3.0.0"
    environment: str = "development"
    debug: bool = False

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "structured"
    log_path: str = "./logs"

    # API服务配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False

    # 数据库配置 - PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "athena"
    postgres_password: str = "changeme"
    postgres_database: str = "athena"
    postgres_pool_size: int = 10

    # 数据库配置 - Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "athena_vectors"

    # 数据库配置 - Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # 数据库配置 - Neo4j (TD-001: 统一图数据库)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_database: str = "neo4j"

    # AI模型配置
    embedding_model: str = "bge-m3"
    embedding_device: str = "api"  # 通过 API 服务 (localhost:8766)

    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_api_key: str = ""
    llm_temperature: float = 0.7

    # 任务配置
    task_soft_timeout: int = 300
    task_hard_timeout: int = 600

    # 存储配置
    storage_local_path: str = "./data"
    storage_temp_path: str = "./temp"

    # 安全配置
    jwt_secret: str = "changeme-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # 监控配置
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # 其他配置字段
    _extra: dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Path | None = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录,默认为 config/unified/
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config" / "unified"

        self.config_dir = Path(config_dir)
        self.environment = os.getenv("ENVIRONMENT", "development")

        # 配置文件路径
        self.base_config_path = self.config_dir / "base.yaml"
        self.env_config_path = self.config_dir / self.environment / "config.yaml"
        self.secrets_path = self.config_dir / "secrets" / f"{self.environment}.secrets"

        # 加载的配置
        self._config: dict[str, Any] = {}

    def load_config(self) -> AthenaConfig:
        """
        加载配置

        Returns:
            AthenaConfig: 配置对象
        """
        # 1. 加载基础配置
        self._config = self._load_yaml(self.base_config_path)

        # 2. 加载环境特定配置
        if self.env_config_path.exists():
            env_config = self._load_yaml(self.env_config_path)
            self._config = self._deep_merge(self._config, env_config)

        # 3. 加载敏感信息
        if self.secrets_path.exists():
            secrets = self._load_yaml(self.secrets_path)
            self._config = self._deep_merge(self._config, secrets)

        # 4. 展开环境变量占位符
        self._config = self._expand_env_vars(self._config)

        # 5. 应用环境变量覆盖
        self._apply_env_overrides()

        # 6. 创建配置对象
        return self._create_config_object()

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """加载YAML文件"""
        if not path.exists():
            return {}

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else {}

    def _expand_env_vars(self, data: Any) -> Any:
        """
        递归展开环境变量占位符

        Args:
            data: 配置数据(可以是dict、list或基本类型)

        Returns:
            展开后的数据
        """
        if isinstance(data, dict):
            return {k: self._expand_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._expand_env_vars(item) for item in data]
        elif isinstance(data, str):
            # 处理 ${VAR:default} 格式
            match = re.match(r"^\$\{([^:}]+)(?::([^}]*))?}\$", data)
            if match:
                env_var, default = match.groups()
                value = os.getenv(env_var)
                if value is not None:
                    # 尝试类型转换
                    return self._convert_type(value)
                return self._convert_type(default) if default is not None else data
            return data
        else:
            return data

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """深度合并字典"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_env_overrides(self) -> Any:
        """应用环境变量覆盖"""
        # 支持的环境变量前缀
        env_mappings = {
            # 平台配置
            "ENVIRONMENT": "environment",
            "DEBUG": "debug",
            # 日志配置
            "LOG_LEVEL": "log_level",
            # API配置
            "API_HOST": "api_host",
            "API_PORT": "api_port",
            "API_WORKERS": "api_workers",
            "API_RELOAD": "api_reload",
            # PostgreSQL配置
            "POSTGRES_HOST": "postgres_host",
            "POSTGRES_PORT": "postgres_port",
            "POSTGRES_USER": "postgres_user",
            "POSTGRES_PASSWORD": "postgres_password",
            "POSTGRES_DB": "postgres_database",
            "POSTGRES_POOL_SIZE": "postgres_pool_size",
            # Qdrant配置
            "QDRANT_HOST": "qdrant_host",
            "QDRANT_PORT": "qdrant_port",
            "QDRANT_COLLECTION": "qdrant_collection",
            # Redis配置
            "REDIS_HOST": "redis_host",
            "REDIS_PORT": "redis_port",
            "REDIS_DB": "redis_db",
            "REDIS_PASSWORD": "redis_password",
            # Neo4j配置 (TD-001: 统一图数据库)
            "NEO4J_URI": "neo4j_uri",
            "NEO4J_USERNAME": "neo4j_username",
            "NEO4J_PASSWORD": "neo4j_password",
            "NEO4J_DATABASE": "neo4j_database",
            # AI模型配置
            "EMBEDDING_MODEL": "embedding_model",
            "EMBEDDING_DEVICE": "embedding_device",
            "LLM_PROVIDER": "llm_provider",
            "LLM_MODEL": "llm_model",
            "LLM_API_KEY": "llm_api_key",
            "LLM_TEMPERATURE": "llm_temperature",
            # 安全配置
            "JWT_SECRET": "jwt_secret",
            "JWT_ALGORITHM": "jwt_algorithm",
            "JWT_EXPIRE_MINUTES": "jwt_expire_minutes",
            # 监控配置
            "PROMETHEUS_ENABLED": "prometheus_enabled",
            "PROMETHEUS_PORT": "prometheus_port",
        }

        # 应用环境变量
        for env_key, config_key in env_mappings.items():
            value = os.getenv(env_key)
            if value is not None:
                self._set_nested_value(config_key, value)

    def _set_nested_value(self, key: str, value: str) -> Any:
        """设置嵌套字典的值"""
        keys = key.split("_")
        current = self._config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # 类型转换
        current[keys[-1]] = self._convert_type(value)

    def _convert_type(self, value: str) -> Any:
        """自动类型转换"""
        # 布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # 数字
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # 字符串
        return value

    def _create_config_object(self) -> AthenaConfig:
        """创建配置对象"""
        # 展平字典
        flat_config = self._flatten_dict(self._config)

        # 创建配置对象
        return AthenaConfig(**flat_config)

    def _flatten_dict(
        self, d: dict[str, Any], parent_key: str = "", sep: str = "_"
    ) -> dict[str, Any]:
        """展平嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))

        return dict(items)


# 全局配置实例
_config_manager: ConfigManager | None = None
_config: AthenaConfig | None = None


def get_config(config_dir: Path | None = None, reload: bool = False) -> AthenaConfig:
    """
    获取配置对象(单例模式)

    Args:
        config_dir: 配置文件目录
        reload: 是否重新加载配置

    Returns:
        AthenaConfig: 配置对象
    """
    global _config_manager, _config

    if _config_manager is None or reload:
        _config_manager = ConfigManager(config_dir)
        _config = _config_manager.load_config()

    return _config


def reload_config() -> AthenaConfig:
    """重新加载配置"""
    return get_config(reload=True)


# 便捷访问函数
def get_platform_config() -> dict[str, Any]:
    """获取平台配置"""
    config = get_config()
    return {
        "name": config.platform_name,
        "version": config.platform_version,
        "environment": config.environment,
        "debug": config.debug,
    }


def get_database_config() -> dict[str, Any]:
    """获取数据库配置"""
    config = get_config()
    return {
        "postgres": {
            "host": config.postgres_host,
            "port": config.postgres_port,
            "user": config.postgres_user,
            "password": config.postgres_password,
            "database": config.postgres_database,
            "pool_size": config.postgres_pool_size,
        },
        "qdrant": {
            "url": f"http://{config.qdrant_host}:{config.qdrant_port}",
            "collection": config.qdrant_collection,
        },
        "redis": {
            "host": config.redis_host,
            "port": config.redis_port,
            "db": config.redis_db,
            "password": config.redis_password,
        },
        "neo4j": {  # TD-001: 统一图数据库
            "uri": config.neo4j_uri,
            "username": config.neo4j_username,
            "password": config.neo4j_password,
            "database": config.neo4j_database,
        },
    }


def get_model_config() -> dict[str, Any]:
    """获取AI模型配置"""
    config = get_config()
    return {
        "embedding": {
            "model": config.embedding_model,
            "device": config.embedding_device,
        },
        "llm": {
            "provider": config.llm_provider,
            "model": config.llm_model,
            "api_key": config.llm_api_key,
            "temperature": config.llm_temperature,
        },
    }


if __name__ == "__main__":
    # 测试配置加载
    import os

    # 设置环境
    os.environ["ENVIRONMENT"] = "development"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # 加载配置
    config = get_config()

    print("=== Athena平台配置测试 ===")
    print(f"平台名称: {config.platform_name}")
    print(f"环境: {config.environment}")
    print(f"调试模式: {config.debug}")
    print(f"日志级别: {config.log_level}")
    print(f"API地址: {config.api_host}:{config.api_port}")
    print(f"PostgreSQL: {config.postgres_host}:{config.postgres_port}/{config.postgres_database}")
    print(f"Redis: {config.redis_host}:{config.redis_port}")
    print(f"Qdrant: {config.qdrant_host}:{config.qdrant_port}")
    print(f"嵌入模型: {config.embedding_model}")
    print(f"LLM: {config.llm_provider}/{config.llm_model}")
