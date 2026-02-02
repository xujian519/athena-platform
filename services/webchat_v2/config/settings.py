#!/usr/bin/env python3
"""
配置管理
WebChat V2 Gateway配置

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.2
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# 获取webchat_v2目录的绝对路径
_WEBCHAT_V2_DIR = Path(__file__).parent.parent
_ENV_FILE = _WEBCHAT_V2_DIR / ".env"


class GatewaySettings(BaseSettings):
    """Gateway配置"""

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # WebSocket配置
    heartbeat_interval: int = 30
    max_message_size: int = 1048576  # 1MB
    max_connections: int = 1000

    # 安全配置
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # JWT配置
    jwt_secret: str = "webchat-v2-secret-key-change-in-production"
    jwt_expire_minutes: int = 1440  # 24小时

    # 身份配置
    default_user_id: str = "guest"
    admin_user_id: str = "xujian"

    # 模块配置
    enable_module_cache: bool = True
    module_health_check_interval: int = 60
    module_invoke_timeout: int = 30  # 模块调用超时时间（秒）

    # 持久化配置
    identity_persistence_path: str = "data/identities.json"

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "webchat_gateway.log"  # 日志文件名（不含目录）
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    # 使用新的ConfigDict替代deprecated的Config类
    # extra="ignore" 允许忽略根目录.env中的其他平台配置
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),  # 使用绝对路径指向webchat_v2/.env
        env_prefix="GATEWAY_",
        case_sensitive=False,
        extra="ignore",  # 忽略未定义的环境变量
    )


# 配置实例
settings = GatewaySettings()
