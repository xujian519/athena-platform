#!/usr/bin/env python3
"""
配置设置管理
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from .environment import EnvironmentConfig, Environment


class Settings:
    """全局设置管理器"""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._env_config: EnvironmentConfig | None = None
        self._load_default_config()

    def _load_default_config(self):
        """加载默认配置"""
        self._config = {
            # 数据库配置
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'athena',
                'user': 'postgres',
                'password': 'password',
                'max_connections': 20,
                'connection_timeout': 30
            },

            # Redis配置
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': None,
                'max_connections': 20
            },

            # API配置
            'api': {
                'host': 'localhost',
                'port': 8000,
                'cors_origins': ['*'],
                'rate_limit': 100
            },

            # 日志配置
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/athena.log',
                'max_size': '10MB',
                'backup_count': 5
            },

            # 监控配置
            'monitoring': {
                'enabled': True,
                'system_interval': 30,
                'alert_interval': 10,
                'metrics_retention_days': 30
            },

            # 邮件配置
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'username': '',
                'password': '',
                'from_email': '',
                'from_name': 'Athena Platform'
            },

            # 服务配置
            'services': {
                'core_server': {
                    'command': 'python -m core.app',
                    'port': 8000,
                    'dependencies': [],
                    'health_check': 'http://localhost:8000/health'
                },
                'ai_service': {
                    'command': 'python -m services.ai_app',
                    'port': 8001,
                    'dependencies': ['core_server'],
                    'health_check': 'http://localhost:8001/health'
                },
                'patent_api': {
                    'command': 'python -m services.patent_api',
                    'port': 8002,
                    'dependencies': ['core_server'],
                    'health_check': 'http://localhost:8002/health'
                }
            },

            # 部署配置
            'deployments': {},

            # 健康检查配置
            'health_checks': {}
        }

        # 加载环境配置
        env_name = os.getenv('ATHENA_ENV', 'development')
        self._load_environment_config(env_name)

    def _load_environment_config(self, env_name: str):
        """加载环境配置"""
        # 先从环境变量加载
        self._env_config = EnvironmentConfig.from_env(env_name)

        # 如果环境变量配置为空，使用默认配置
        if not self._env_config.database_url:
            default_configs = EnvironmentConfig.get_default_configs()
            self._env_config = default_configs.get(env_name, default_configs['development'])

    def load_from_file(self, config_path: str):
        """从文件加载配置"""
        config_file = Path(config_path)

        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)

            # 合并配置
            self._merge_config(self._config, file_config)
            print(f"配置文件加载成功: {config_path}")
        else:
            print(f"配置文件不存在: {config_path}")

    def _merge_config(self, base: Dict, update: Dict):
        """递归合并配置"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的嵌套键）"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # 尝试从环境配置获取
                if hasattr(self._env_config, k):
                    return getattr(self._env_config, k)
                return default

        return value

    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        db_config = self.get('database', {})

        # 如果环境配置中有database_url，解析它
        if self._env_config and self._env_config.database_url:
            url = self._env_config.database_url
            # 简单解析postgresql://user:password@host:port/database
            if url.startswith('postgresql://'):
                url = url[13:]  # 移除 postgresql://
                if '@' in url:
                    auth, host_port_db = url.split('@', 1)
                    if ':' in auth:
                        user, password = auth.split(':', 1)
                        db_config['user'] = user
                        db_config['password'] = password
                    if '/' in host_port_db:
                        host_port, database = host_port_db.split('/', 1)
                        if ':' in host_port:
                            host, port = host_port.split(':', 1)
                            db_config['host'] = host
                            db_config['port'] = int(port)
                        else:
                            db_config['host'] = host_port
                        db_config['database'] = database

        return db_config

    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        redis_config = self.get('redis', {})

        # 如果环境配置中有redis_url，解析它
        if self._env_config and self._env_config.redis_url:
            url = self._env_config.redis_url
            # 简单解析 redis://host:port/db
            if url.startswith('redis://'):
                url = url[7:]  # 移除 redis://
                if '/' in url:
                    host_port, db = url.split('/', 1)
                    redis_config['db'] = int(db)
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                        redis_config['host'] = host
                        redis_config['port'] = int(port)
                    else:
                        redis_config['host'] = host_port

        return redis_config

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务配置"""
        services = self.get('services', {})
        return services.get(service_name, {})

    def get_python_path(self) -> str:
        """获取Python路径"""
        return os.getenv('PYTHONPATH', '/Users/xujian/Athena工作平台')

    @property
    def env(self) -> EnvironmentConfig:
        """获取环境配置"""
        return self._env_config

    @property
    def is_production(self) -> bool:
        """是否是生产环境"""
        return self._env_config.name == Environment.PRODUCTION.value

    @property
    def is_development(self) -> bool:
        """是否是开发环境"""
        return self._env_config.name == Environment.DEVELOPMENT.value


# 全局实例
settings = Settings()
config = settings  # 提供别名