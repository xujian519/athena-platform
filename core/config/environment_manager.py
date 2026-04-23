#!/usr/bin/env python3
from __future__ import annotations
"""
Athena平台环境变量管理器
Environment Manager for Athena Platform

统一管理所有环境变量,提供类型安全的环境变量访问接口

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """环境类型枚举"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """数据库配置"""

    host: str
    port: int
    name: str
    user: str
    password: str
    ssl_mode: str = "prefer"
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30

    @property
    def connection_string(self) -> str:
        """生成数据库连接字符串"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}"


@dataclass
class RedisConfig:
    """Redis配置"""

    host: str
    port: int
    password: Optional[str] = None
    db: int = 0
    ssl_enabled: bool = False


@dataclass
class AIModelConfig:
    """AI模型配置"""

    glm_api_key: Optional[str] = None
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    model_path: Path | None = None
    bert_model_path: Path | None = None
    bge_model_path: Path | None = None


@dataclass
class SecurityConfig:
    """安全配置"""

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    cors_origins: Optional[list[str]] = None
    api_key_header: str = "X-API-Key"

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = []


@dataclass
class MonitoringConfig:
    """监控配置"""

    prometheus_port: int = 9090
    grafana_port: int = 3001
    grafana_username: str = "admin"
    grafana_password: str = ""
    log_level: str = "INFO"
    alert_webhook_url: Optional[str] = None
    alert_email: Optional[str] = None


class EnvironmentManager:
    """环境变量管理器"""

    def __init__(self):
        self._env_cache: dict[str, Any] = {}
        self._initialize_defaults()

    def _initialize_defaults(self) -> Any:
        """初始化默认值"""
        # 确保必要的环境变量有默认值
        default_values = {
            "ATHENA_ENV": "development",
            "ATHENA_HOME": str(Path.home() / "Athena工作平台"),
            "LOG_LEVEL": "INFO",
            "DEBUG": "false",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "athena_db",
            "DB_USER": "athena_user",
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "YUNPAT_PORT": "8020",
            "XIANUO_PORT": "8021",
            "CRAWLER_PORT": "8022",
            "MAX_WORKERS": "4",
            "MAX_CONNECTIONS": "1000",
            "CACHE_TTL_SECONDS": "3600",
            "CACHE_MAX_SIZE": "1000",
        }

        for key, default_value in default_values.items():
            if key not in os.environ:
                os.environ[key] = default_value

    def get(self, key: str, default: Any = None, cast_type: type = str) -> Any:
        """获取环境变量值"""
        if key in self._env_cache:
            return self._env_cache[key]

        value = os.getenv(key, default)
        if value is None:
            return None

        # 类型转换
        try:
            if cast_type == bool:
                # 如果已经是布尔值，直接返回
                if isinstance(value, bool):
                    result = value
                else:
                    result = value.lower() in ("true", "1", "yes", "on")
            elif cast_type == int:
                result = int(value)
            elif cast_type == float:
                result = float(value)
            elif cast_type == Path:
                result = Path(value)
            elif cast_type == list:
                # 如果已经是列表，直接返回
                if isinstance(value, list):
                    result = value
                else:
                    result = [item.strip() for item in value.split(",") if item.strip()]
            else:
                result = cast_type(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"环境变量 {key} 类型转换失败: {e}")
            result = default

        self._env_cache[key] = result
        return result

    def get_str(self, key: str, default: str = "") -> str:
        """获取字符串类型环境变量"""
        return self.get(key, default, str)

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数类型环境变量"""
        return self.get(key, default, int)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔类型环境变量"""
        return self.get(key, default, bool)

    def get_path(self, key: str, default: str | Path | None = None) -> Path | None:
        """获取路径类型环境变量"""
        if default is None:
            default_path = None
        elif isinstance(default, str):
            default_path = Path(default)
        else:
            default_path = default

        return self.get(key, default_path, Path)

    def get_list(self, key: str, default: Optional[list[str]] = None) -> list[str]:
        """获取列表类型环境变量"""
        if default is None:
            default = []
        return self.get(key, default, list)

    @property
    def environment_type(self) -> EnvironmentType:
        """获取当前环境类型"""
        env_str = self.get_str("ATHENA_ENV", "development").lower()
        try:
            return EnvironmentType(env_str)
        except ValueError:
            logger.warning(f"无效的环境类型: {env_str},使用默认值 development")
            return EnvironmentType.DEVELOPMENT

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment_type == EnvironmentType.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment_type == EnvironmentType.TESTING

    @property
    def is_staging(self) -> bool:
        """是否为预发布环境"""
        return self.environment_type == EnvironmentType.STAGING

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment_type == EnvironmentType.PRODUCTION

    @property
    def athena_home(self) -> Path:
        """Athena平台根目录"""
        return self.get_path("ATHENA_HOME", Path.home() / "Athena工作平台")

    @property
    def data_path(self) -> Path:
        """数据目录"""
        return self.athena_home / "data"

    @property
    def config_path(self) -> Path:
        """配置目录"""
        return self.athena_home / "config"

    @property
    def logs_path(self) -> Path:
        """日志目录"""
        return self.athena_home / "logs"

    @property
    def uploads_path(self) -> Path:
        """上传文件目录"""
        return self.athena_home / "uploads"

    @property
    def cache_path(self) -> Path:
        """缓存目录"""
        return self.athena_home / "cache"

    @property
    def models_path(self) -> Path:
        """模型目录"""
        return self.athena_home / "models"

    @property
    def backup_path(self) -> Path:
        """备份目录"""
        return self.athena_home / "backups"

    @property
    def debug(self) -> bool:
        """调试模式"""
        return self.get_bool("DEBUG", self.is_development)

    @property
    def log_level(self) -> str:
        """日志级别"""
        if self.is_production:
            return self.get_str("LOG_LEVEL", "INFO")
        else:
            return self.get_str("LOG_LEVEL", "DEBUG")

    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        return DatabaseConfig(
            host=self.get_str("DB_HOST"),
            port=self.get_int("DB_PORT", 5432),
            name=self.get_str("DB_NAME"),
            user=self.get_str("DB_USER"),
            password=self.get_str("DB_PASSWORD"),
            ssl_mode=self.get_str("DB_SSL_MODE", "prefer" if self.is_production else "disable"),
            pool_size=self.get_int("DB_POOL_SIZE", 20 if self.is_production else 5),
            max_overflow=self.get_int("DB_MAX_OVERFLOW", 30 if self.is_production else 10),
            pool_timeout=self.get_int("DB_POOL_TIMEOUT", 30),
        )

    def get_redis_config(self) -> RedisConfig:
        """获取Redis配置"""
        return RedisConfig(
            host=self.get_str("REDIS_HOST"),
            port=self.get_int("REDIS_PORT", 6379),
            password=self.get_str("REDIS_PASSWORD") or None,
            db=self.get_int("REDIS_DB", 0),
            ssl_enabled=self.get_bool("REDIS_SSL_ENABLED", self.is_production),
        )

    def get_ai_model_config(self) -> AIModelConfig:
        """获取AI模型配置"""
        return AIModelConfig(
            glm_api_key=self.get_str("GLM_API_KEY") or None,
            glm_base_url=self.get_str("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            openai_api_key=self.get_str("OPENAI_API_KEY") or None,
            openai_base_url=self.get_str("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model_path=self.get_path("MODEL_PATH", self.models_path),
            bert_model_path=self.get_path("BERT_MODEL_PATH", self.models_path / "chinese_bert"),
            bge_model_path=self.get_path("BGE_MODEL_PATH", self.models_path / "BAAI/bge-m3"),
        )

    def get_security_config(self) -> SecurityConfig:
        """获取安全配置"""
        jwt_secret = self.get_str("JWT_SECRET")
        if not jwt_secret and not self.is_development:
            raise ValueError("生产环境必须设置JWT_SECRET环境变量")

        return SecurityConfig(
            jwt_secret=jwt_secret or "development-secret-key-change-in-production",
            jwt_algorithm=self.get_str("JWT_ALGORITHM", "HS256"),
            jwt_expire_hours=self.get_int("JWT_EXPIRE_HOURS", 24),
            cors_origins=self.get_list("CORS_ORIGINS"),
            api_key_header=self.get_str("API_KEY_HEADER", "X-API-Key"),
        )

    def get_monitoring_config(self) -> MonitoringConfig:
        """获取监控配置"""
        return MonitoringConfig(
            prometheus_port=self.get_int("PROMETHEUS_PORT", 9090),
            grafana_port=self.get_int("GRAFANA_PORT", 3001),
            grafana_username=self.get_str("GRAFANA_USERNAME", "admin"),
            grafana_password=self.get_str("GRAFANA_PASSWORD", ""),
            log_level=self.log_level,
            alert_webhook_url=self.get_str("ALERT_WEBHOOK_URL") or None,
            alert_email=self.get_str("ALERT_EMAIL") or None,
        )

    def get_service_port(self, service_name: str) -> int:
        """获取服务端口"""
        port_map = {
            "yunpat": "YUNPAT_PORT",
            "apps/apps/xiaonuo": "XIANUO_PORT",
            "crawler": "CRAWLER_PORT",
            "prometheus": "PROMETHEUS_PORT",
            "grafana": "GRAFANA_PORT",
        }

        env_key = port_map.get(service_name.lower(), f"{service_name.upper()}_PORT")
        return self.get_int(env_key)

    def get_identity_config(self) -> dict[str, Path]:
        """获取身份系统配置"""
        return {
            "xiaonuo_config_file": self.config_path / "identity" / "xiaonuo_pisces_princess.json",
            "identity_storage_path": self.data_path / "identity_permanent_storage",
        }

    def validate_required_configs(self) -> list[str]:
        """验证必需的配置项"""
        missing_configs = []

        # 检查基础路径
        required_paths = [
            ("ATHENA_HOME", self.athena_home),
        ]

        for key, path in required_paths:
            if not path.exists():
                missing_configs.append(f"{key}: {path} (路径不存在)")

        # 检查生产环境必需配置
        if self.is_production:
            required_vars = [
                "DB_PASSWORD",
                "JWT_SECRET",
                "GRAFANA_PASSWORD",
            ]

            for var in required_vars:
                if not self.get_str(var):
                    missing_configs.append(f"{var}: (未设置)")

        return missing_configs

    def create_directories(self) -> None:
        """创建必要的目录"""
        directories = [
            self.athena_home,
            self.data_path,
            self.config_path,
            self.logs_path,
            self.uploads_path,
            self.cache_path,
            self.models_path,
            self.backup_path,
            self.data_path / "identity_permanent_storage",
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"确保目录存在: {directory}")
            except Exception as e:
                logger.error(f"创建目录失败 {directory}: {e}")

    def get_summary(self) -> dict[str, Any]:
        """获取环境配置摘要"""
        return {
            "environment": self.environment_type.value,
            "athena_home": str(self.athena_home),
            "debug": self.debug,
            "log_level": self.log_level,
            "paths": {
                "data": str(self.data_path),
                "config": str(self.config_path),
                "logs": str(self.logs_path),
                "uploads": str(self.uploads_path),
                "cache": str(self.cache_path),
                "models": str(self.models_path),
                "backup": str(self.backup_path),
            },
            "services": {
                "yunpat_port": self.get_service_port("yunpat"),
                "xiaonuo_port": self.get_service_port("apps/apps/xiaonuo"),
                "crawler_port": self.get_service_port("crawler"),
            },
            "validation_errors": self.validate_required_configs(),
        }


# 全局环境管理器实例
env_manager = EnvironmentManager()


def get_env_manager() -> EnvironmentManager:
    """获取全局环境管理器实例"""
    return env_manager


def init_environment() -> Any:
    """初始化环境配置"""
    logger.info("初始化Athena平台环境配置")

    # 创建必要目录
    env_manager.create_directories()

    # 验证配置
    validation_errors = env_manager.validate_required_configs()
    if validation_errors:
        error_msg = "环境配置验证失败:\n" + "\n".join(validation_errors)
        if env_manager.is_production:
            raise ValueError(error_msg)
        else:
            logger.warning(error_msg)

    # 打印环境摘要
    summary = env_manager.get_summary()
    logger.info(f"环境配置摘要: {summary}")

    logger.info("环境配置初始化完成")


# 装饰器:确保环境已初始化
def ensure_environment_initialized(func) -> None:
    """装饰器:确保环境已初始化"""

    def wrapper(*args, **kwargs) -> Any:
        if not hasattr(env_manager, "_initialized"):
            init_environment()
            env_manager._initialized = True
        return func(*args, **kwargs)

    return wrapper


if __name__ == "__main__":
    # 测试环境管理器
    init_environment()

    # 打印配置摘要
    import json

    summary = env_manager.get_summary()
    print("环境配置摘要:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
