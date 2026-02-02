"""
自主控制系统配置
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class LogLevel(Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'

@dataclass
class DatabaseConfig:
    """数据库配置"""
    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str = 'athena_autonomous'
    postgres_user: str = 'athena'
    postgres_password: str = 'athena_password'

    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = None

@dataclass
class SecurityConfig:
    """安全配置"""
    secret_key: str = 'athena-autonomous-control-secret-key-2024'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 30
    enable_authentication: bool = True  # 生产环境设为True

    # IP白名单
    allowed_ips: List[str] = None

    # API访问限制
    rate_limit_per_minute: int = 100

@dataclass
class AgentConfig:
    """Agent配置"""
    athena_model: str = 'gpt-4'
    xiaonuo_model: str = 'gpt-3.5-turbo'
    max_concurrent_tasks: int = 10
    task_timeout_minutes: int = 60

    # 情感参数
    emotional_update_rate: float = 0.3
    empathy_threshold: float = 0.7
    confidence_threshold: float = 0.8

@dataclass
class DecisionEngineConfig:
    """决策引擎配置"""
    max_decision_options: int = 5
    confidence_threshold: float = 0.7
    learning_rate: float = 0.1
    experience_decay_days: int = 30

    # 决策类型权重
    decision_weights: Dict[str, float] = None

@dataclass
class PlatformConfig:
    """平台管理配置"""
    docker_compose_file: str = 'docker-compose.yml'
    service_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 10
    auto_restart_enabled: bool = True
    max_restart_attempts: int = 3

@dataclass
class LoggingConfig:
    """日志配置"""
    level: LogLevel = LogLevel.INFO
    log_file: str = 'documentation/logs/autonomous_control.log'
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_console_output: bool = True

@dataclass
class MonitoringConfig:
    """监控配置"""
    enable_metrics: bool = True
    metrics_port: int = 9095
    health_check_interval_seconds: int = 60
    alert_thresholds: Dict[str, float] = None

class AutonomousControlConfig:
    """自主控制系统总配置"""

    def __init__(self):
        # 服务配置
        self.host = '0.0.0.0'
        self.port = 8090
        self.debug = False

        # 各模块配置
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        self.agent = AgentConfig()
        self.decision_engine = DecisionEngineConfig()
        self.platform = PlatformConfig()
        self.logging = LoggingConfig()
        self.monitoring = MonitoringConfig()

        # 初始化默认值
        self._init_defaults()

    def _init_defaults(self) -> Any:
        """初始化默认值"""
        # 安全配置默认值
        if self.security.allowed_ips is None:
            self.security.allowed_ips = ['127.0.0.1', 'localhost']

        # 决策引擎默认权重
        if self.decision_engine.decision_weights is None:
            self.decision_engine.decision_weights = {
                'platform_control': 0.3,
                'service_management': 0.25,
                'task_planning': 0.25,
                'error_recovery': 0.2
            }

        # 监控阈值默认值
        if self.monitoring.alert_thresholds is None:
            self.monitoring.alert_thresholds = {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'error_rate': 5.0,
                'response_time': 5.0
            }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AutonomousControlConfig':
        """从字典创建配置"""
        config = cls()

        # 更新服务配置
        if 'service' in config_dict:
            service_config = config_dict['service']
            config.host = service_config.get('host', config.host)
            config.port = service_config.get('port', config.port)
            config.debug = service_config.get('debug', config.debug)

        # 更新各模块配置
        for module_name in ['database', 'security', 'agent', 'decision_engine', 'platform', 'logging', 'monitoring']:
            if module_name in config_dict:
                module_config = getattr(config, module_name)
                for key, value in config_dict[module_name].items():
                    if hasattr(module_config, key):
                        setattr(module_config, key, value)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'service': {
                'host': self.host,
                'port': self.port,
                'debug': self.debug
            },
            'database': {
                'postgres_host': self.database.postgres_host,
                'postgres_port': self.database.postgres_port,
                'postgres_db': self.database.postgres_db,
                'postgres_user': self.database.postgres_user,
                'redis_host': self.database.redis_host,
                'redis_port': self.database.redis_port,
                'redis_db': self.database.redis_db
            },
            'security': {
                'enable_authentication': self.security.enable_authentication,
                'access_token_expire_minutes': self.security.access_token_expire_minutes,
                'allowed_ips': self.security.allowed_ips,
                'rate_limit_per_minute': self.security.rate_limit_per_minute
            },
            'agent': {
                'athena_model': self.agent.athena_model,
                'xiaonuo_model': self.agent.xiaonuo_model,
                'max_concurrent_tasks': self.agent.max_concurrent_tasks,
                'task_timeout_minutes': self.agent.task_timeout_minutes,
                'emotional_update_rate': self.agent.emotional_update_rate,
                'empathy_threshold': self.agent.empathy_threshold,
                'confidence_threshold': self.agent.confidence_threshold
            },
            'decision_engine': {
                'max_decision_options': self.decision_engine.max_decision_options,
                'confidence_threshold': self.decision_engine.confidence_threshold,
                'learning_rate': self.decision_engine.learning_rate,
                'experience_decay_days': self.decision_engine.experience_decay_days,
                'decision_weights': self.decision_engine.decision_weights
            },
            'platform': {
                'docker_compose_file': self.platform.docker_compose_file,
                'service_check_interval_seconds': self.platform.service_check_interval_seconds,
                'health_check_timeout_seconds': self.platform.health_check_timeout_seconds,
                'auto_restart_enabled': self.platform.auto_restart_enabled,
                'max_restart_attempts': self.platform.max_restart_attempts
            },
            'logging': {
                'level': self.logging.level.value,
                'log_file': self.logging.log_file,
                'max_file_size_mb': self.logging.max_file_size_mb,
                'backup_count': self.logging.backup_count,
                'enable_console_output': self.logging.enable_console_output
            },
            'monitoring': {
                'enable_metrics': self.monitoring.enable_metrics,
                'metrics_port': self.monitoring.metrics_port,
                'health_check_interval_seconds': self.monitoring.health_check_interval_seconds,
                'alert_thresholds': self.monitoring.alert_thresholds
            }
        }

    def validate(self) -> List[str]:
        """验证配置的有效性"""
        errors = []

        # 验证端口范围
        if not (1 <= self.port <= 65535):
            errors.append('端口号必须在1-65535范围内')

        # 验证决策阈值
        if not (0 <= self.decision_engine.confidence_threshold <= 1):
            errors.append('决策置信度阈值必须在0-1范围内')

        # 验证情感参数
        if not (0 <= self.agent.emotional_update_rate <= 1):
            errors.append('情感更新率必须在0-1范围内')

        # 验证日志级别
        if self.logging.level not in LogLevel:
            errors.append('无效的日志级别')

        return errors

# 全局配置实例
config = AutonomousControlConfig()