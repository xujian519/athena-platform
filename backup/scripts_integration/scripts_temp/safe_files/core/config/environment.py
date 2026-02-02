#!/usr/bin/env python3
"""
环境配置管理
处理不同环境的配置差异
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass


class Environment(Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentConfig:
    """环境配置"""
    name: str
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = ""
    redis_url: str = ""

    # API配置
    api_host: str = "localhost"
    api_port: int = 8000

    # 监控配置
    enable_monitoring: bool = True
    health_check_interval: int = 30

    # 邮件配置
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    # 其他配置
    max_connections: int = 100
    request_timeout: int = 30

    @classmethod
    def from_env(cls, env_name: str) -> 'EnvironmentConfig':
        """从环境变量创建配置"""
        return cls(
            name=env_name,
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            database_url=os.getenv('DATABASE_URL', ''),
            redis_url=os.getenv('REDIS_URL', ''),
            api_host=os.getenv('API_HOST', 'localhost'),
            api_port=int(os.getenv('API_PORT', '8000')),
            enable_monitoring=os.getenv('ENABLE_MONITORING', 'true').lower() == 'true',
            health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
            smtp_server=os.getenv('SMTP_SERVER', ''),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=os.getenv('SMTP_USERNAME', ''),
            smtp_password=os.getenv('SMTP_PASSWORD', ''),
            max_connections=int(os.getenv('MAX_CONNECTIONS', '100')),
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', '30'))
        )

    @classmethod
    def get_default_configs(cls) -> Dict[str, 'EnvironmentConfig']:
        """获取默认环境配置"""
        return {
            Environment.DEVELOPMENT.value: cls(
                name=Environment.DEVELOPMENT.value,
                debug=True,
                log_level="DEBUG",
                database_url="postgresql://postgres:password@localhost:5432/athena_dev",
                redis_url="redis://localhost:6379/0",
                api_host="localhost",
                api_port=8000,
                enable_monitoring=True,
                health_check_interval=10
            ),
            Environment.TESTING.value: cls(
                name=Environment.TESTING.value,
                debug=True,
                log_level="INFO",
                database_url="postgresql://postgres:password@localhost:5432/athena_test",
                redis_url="redis://localhost:6379/1",
                api_host="localhost",
                api_port=8001,
                enable_monitoring=False,
                health_check_interval=60
            ),
            Environment.STAGING.value: cls(
                name=Environment.STAGING.value,
                debug=False,
                log_level="INFO",
                database_url="postgresql://postgres:password@db-staging:5432/athena",
                redis_url="redis://redis-staging:6379/0",
                api_host="staging.athena.com",
                api_port=443,
                enable_monitoring=True,
                health_check_interval=30
            ),
            Environment.PRODUCTION.value: cls(
                name=Environment.PRODUCTION.value,
                debug=False,
                log_level="WARNING",
                database_url="postgresql://postgres:password@db-prod:5432/athena",
                redis_url="redis://redis-prod:6379/0",
                api_host="api.athena.com",
                api_port=443,
                enable_monitoring=True,
                health_check_interval=60
            )
        }