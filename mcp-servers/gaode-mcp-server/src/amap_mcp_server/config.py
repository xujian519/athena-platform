"""
配置管理
Configuration Management
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings

class AmapApiConfig(BaseSettings):
    """高德地图API配置"""

    # API基础配置
    api_key: str = Field(..., env='AMAP_API_KEY')
    secret_key: Optional[str] = Field(default='', env='AMAP_SECRET_KEY')
    base_url: str = Field(default='https://restapi.amap.com', env='AMAP_BASE_URL')

    # 性能配置
    timeout: int = Field(default=30, env='AMAP_TIMEOUT')
    max_retries: int = Field(default=3, env='AMAP_MAX_RETRIES')
    retry_delay: float = Field(default=1.0, env='AMAP_RETRY_DELAY')

    # 限流配置
    rate_limit_requests_per_minute: int = Field(default=100, env='AMAP_RATE_LIMIT_RPM')
    rate_limit_requests_per_second: int = Field(default=2, env='AMAP_RATE_LIMIT_RPS')

    # 缓存配置
    cache_enabled: bool = Field(default=True, env='AMAP_CACHE_ENABLED')
    cache_ttl: int = Field(default=300, env='AMAP_CACHE_TTL')  # 5分钟

    class Config:
        env_prefix = 'AMAP_'
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'

class McpServerConfig(BaseSettings):
    """MCP服务器配置"""

    # 服务器基础配置
    name: str = Field(default='gaode-mcp-server', env='MCP_SERVER_NAME')
    version: str = Field(default='1.0.0', env='MCP_SERVER_VERSION')
    description: str = Field(
        default='高德地图MCP服务器 - 为AI模型提供地理空间智能服务',
        env='MCP_SERVER_DESCRIPTION'
    )

    # 日志配置
    log_level: str = Field(default='INFO', env='MCP_LOG_LEVEL')
    log_file: Optional[str] = Field(default=None, env='MCP_LOG_FILE')

    # 服务器配置
    host: str = Field(default='localhost', env='MCP_HOST')
    port: int = Field(default=8080, env='MCP_PORT')

    # 安全配置
    allowed_origins: list = Field(default=['*'], env='MCP_ALLOWED_ORIGINS')

    class Config:
        env_prefix = 'MCP_'
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'

class CacheConfig(BaseSettings):
    """缓存配置"""

    # Redis配置
    redis_host: str = Field(default='localhost', env='REDIS_HOST')
    redis_port: int = Field(default=6379, env='REDIS_PORT')
    redis_db: int = Field(default=0, env='REDIS_DB')
    redis_password: Optional[str] = Field(default=None, env='REDIS_PASSWORD')

    # 缓存策略
    cache_strategy: str = Field(default='redis', env='CACHE_STRATEGY')  # redis, memory
    max_cache_size: int = Field(default=1000, env='MAX_CACHE_SIZE')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'

class AppConfig:
    """应用配置"""

    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / 'config'

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        # 加载各模块配置
        self.amap = AmapApiConfig()
        self.mcp_server = McpServerConfig()
        self.cache = CacheConfig()

    def validate(self) -> bool:
        """验证配置完整性"""
        if not self.amap.api_key:
            raise ValueError('AMAP_API_KEY 未设置')

        # SECRET_KEY是可选的，某些API服务不需要
        # if not self.amap.secret_key:
        #     raise ValueError("AMAP_SECRET_KEY 未设置")

        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'amap': self.amap.dict(),
            'mcp_server': self.mcp_server.dict(),
            'cache': self.cache.dict()
        }

# 全局配置实例
config = AppConfig()