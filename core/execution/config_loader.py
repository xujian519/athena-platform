#!/usr/bin/env python3
from __future__ import annotations
"""
执行模块配置加载器
Execution Module Configuration Loader

加载和管理执行模块的生产环境配置。

功能：
- 支持YAML配置文件
- 支持环境变量覆盖
- 配置验证
- 热重载（可选）

作者: Athena AI系统
版本: 2.0.0
创建时间: 2026-01-27
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ExecutionEngineConfig:
    """执行引擎配置"""
    agent_id: str = "athena_production_agent"
    max_workers: int = 20
    min_workers: int = 5
    worker_idle_timeout: int = 300
    max_concurrent_tasks: int = 100
    queue_max_size: int = 10000
    task_timeout: float = 600.0
    task_shutdown_timeout: float = 120.0
    initialization_timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    retry_backoff_max: float = 60.0
    retry_jitter: bool = True
    enable_resource_monitoring: bool = True
    max_memory_mb: int = 4096
    max_cpu_percent: float = 80.0
    gc_threshold: float = 0.8


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    executor_level: str = "WARNING"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    enable_file_logging: bool = True
    log_dir: str = "/var/log/athena/execution"
    log_file: str = "execution.log"
    max_bytes: int = 104857600  # 100MB
    backup_count: int = 10
    enable_task_logging: bool = True
    task_log_file: str = "tasks.log"
    enable_error_log: bool = True
    error_log_file: str = "errors.log"
    enable_performance_log: bool = True
    performance_log_file: str = "performance.log"
    performance_log_interval: int = 60


@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    metrics_collection_interval: int = 10
    metrics_port: int = 9090
    health_port: int = 8080
    enable_metrics_endpoint: bool = True
    enable_health_endpoint: bool = True
    alert_thresholds: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    enabled: bool = True
    interval: int = 30
    timeout: int = 10
    failure_threshold: int = 3
    recovery_threshold: int = 2
    checks: list = field(default_factory=list)


@dataclass
class ShutdownConfig:
    """优雅关闭配置"""
    timeout: int = 120
    task_wait_timeout: int = 60
    force_kill_timeout: int = 30
    save_state: bool = True
    state_path: str = "/var/lib/athena/state/shutdown.json"


@dataclass
class ExecutionConfig:
    """执行模块完整配置"""
    execution_engine: ExecutionEngineConfig = field(default_factory=ExecutionEngineConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    shutdown: ShutdownConfig = field(default_factory=ShutdownConfig)


class ConfigLoader:
    """
    配置加载器

    支持从YAML文件加载配置，并允许通过环境变量覆盖。
    """

    def __init__(
        self,
        config_path: str | None = None,
        env_prefix: str = "ATHENA_EXECUTION"
    ):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，默认为 config/production.yaml
            env_prefix: 环境变量前缀
        """
        self.env_prefix = env_prefix
        self.config_path = config_path or self._find_config_file()
        self.config: ExecutionConfig = ExecutionConfig()

    def _find_config_file(self) -> str:
        """
        查找配置文件

        按优先级查找：
        1. 环境变量指定的配置文件
        2. config/production.yaml
        3. config/default.yaml
        4. 使用默认配置
        """
        # 检查环境变量
        env_config = os.getenv("ATHENA_CONFIG_PATH")
        if env_config and Path(env_config).exists():
            logger.info(f"使用环境变量指定的配置文件: {env_config}")
            return env_config

        # 检查生产配置
        prod_config = Path("config/production.yaml")
        if prod_config.exists():
            logger.info(f"使用生产配置文件: {prod_config}")
            return str(prod_config)

        # 检查默认配置
        default_config = Path("config/default.yaml")
        if default_config.exists():
            logger.info(f"使用默认配置文件: {default_config}")
            return str(default_config)

        logger.warning("未找到配置文件，使用默认配置")
        return ""

    def load(self) -> ExecutionConfig:
        """
        加载配置

        Returns:
            ExecutionConfig: 加载的配置对象
        """
        if self.config_path and Path(self.config_path).exists():
            self._load_from_file()

        self._load_from_env()
        self._validate_config()
        self._setup_logging()

        return self.config

    def _load_from_file(self):
        """从YAML文件加载配置"""
        try:
            with open(self.config_path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            logger.info(f"从文件加载配置: {self.config_path}")

            # 解析各部分配置
            if 'execution_engine' in data:
                self.config.execution_engine = ExecutionEngineConfig(
                    **data['execution_engine']
                )

            if 'logging' in data:
                self.config.logging = LoggingConfig(**data['logging'])

            if 'monitoring' in data:
                monitoring_data = data['monitoring']
                self.config.monitoring = MonitoringConfig(
                    **{k: v for k, v in monitoring_data.items()
                       if k != 'alert_thresholds'}
                )
                self.config.monitoring.alert_thresholds = monitoring_data.get(
                    'alert_thresholds', {}
                )

            if 'health_check' in data:
                self.config.health_check = HealthCheckConfig(**data['health_check'])

            if 'shutdown' in data:
                self.config.shutdown = ShutdownConfig(**data['shutdown'])

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.warning("使用默认配置")

    def _load_from_env(self):
        """从环境变量加载配置（覆盖文件配置）"""
        env_mappings = {
            # 执行引擎
            'EXECUTION_ENGINE__MAX_WORKERS': ('execution_engine', 'max_workers', int),
            'EXECUTION_ENGINE__MIN_WORKERS': ('execution_engine', 'min_workers', int),
            'EXECUTION_ENGINE__MAX_CONCURRENT_TASKS': ('execution_engine', 'max_concurrent_tasks', int),
            'EXECUTION_ENGINE__TASK_TIMEOUT': ('execution_engine', 'task_timeout', float),
            'EXECUTION_ENGINE__MAX_RETRIES': ('execution_engine', 'max_retries', int),
            'EXECUTION_ENGINE__MAX_MEMORY_MB': ('execution_engine', 'max_memory_mb', int),
            'EXECUTION_ENGINE__MAX_CPU_PERCENT': ('execution_engine', 'max_cpu_percent', float),

            # 日志
            'LOGGING__LEVEL': ('logging', 'level', str),
            'LOGGING__LOG_DIR': ('logging', 'log_dir', str),
            'LOGGING__ENABLE_FILE_LOGGING': ('logging', 'enable_file_logging', bool),

            # 监控
            'MONITORING__ENABLED': ('monitoring', 'enabled', bool),
            'MONITORING__METRICS_PORT': ('monitoring', 'metrics_port', int),
            'MONITORING__HEALTH_PORT': ('monitoring', 'health_port', int),
        }

        for env_key, (section, attr, type_func) in env_mappings.items():
            full_env_key = f"{self.env_prefix}__{env_key}"
            value = os.getenv(full_env_key)

            if value is not None:
                try:
                    converted_value = type_func(value)
                    section_obj = getattr(self.config, section)
                    setattr(section_obj, attr, converted_value)
                    logger.debug(f"从环境变量覆盖配置: {full_env_key}={value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"环境变量值转换失败: {full_env_key}={value}, {e}")

    def _validate_config(self):
        """验证配置"""
        errors = []
        warnings = []

        # 验证执行引擎配置
        engine = self.config.execution_engine
        if engine.max_workers < engine.min_workers:
            errors.append("max_workers 必须大于或等于 min_workers")

        if engine.max_concurrent_tasks <= 0:
            errors.append("max_concurrent_tasks 必须大于0")

        if engine.task_timeout <= 0:
            errors.append("task_timeout 必须大于0")

        if engine.max_memory_mb <= 0:
            errors.append("max_memory_mb 必须大于0")

        if not (0.0 <= engine.max_cpu_percent <= 100.0):
            errors.append("max_cpu_percent 必须在0-100之间")

        if engine.max_retries < 0:
            errors.append("max_retries 必须大于或等于0")

        # 验证日志配置
        log_config = self.config.logging
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_config.level.upper() not in valid_log_levels:
            errors.append(f"日志级别必须是: {', '.join(valid_log_levels)}")

        # 验证监控配置
        monitoring = self.config.monitoring
        if monitoring.enabled:
            if not (1024 <= monitoring.metrics_port <= 65535):
                errors.append("metrics_port 必须在1024-65535之间")

            if not (1024 <= monitoring.health_port <= 65535):
                errors.append("health_port 必须在1024-65535之间")

        # 输出验证结果
        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        if warnings:
            warning_msg = "配置警告:\n" + "\n".join(f"  - {w}" for w in warnings)
            logger.warning(warning_msg)

        logger.info("配置验证通过")

    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.logging

        # 设置日志级别
        log_level = getattr(logging, log_config.level.upper(), logging.INFO)

        # 配置根日志器
        logging.basicConfig(
            level=log_level,
            format=log_config.format,
            datefmt=log_config.date_format,
        )

        # 如果启用文件日志
        if log_config.enable_file_logging:
            try:
                # 确保日志目录存在
                log_dir = Path(log_config.log_dir)
                log_dir.mkdir(parents=True, exist_ok=True)

                # 主日志处理器
                from logging.handlers import RotatingFileHandler
                main_handler = RotatingFileHandler(
                    log_dir / log_config.log_file,
                    maxBytes=log_config.max_bytes,
                    backupCount=log_config.backup_count,
                    encoding='utf-8'
                )
                main_handler.setFormatter(logging.Formatter(
                    log_config.format,
                    datefmt=log_config.date_format
                ))
                logging.getLogger().addHandler(main_handler)

                # 错误日志处理器
                if log_config.enable_error_log:
                    error_handler = RotatingFileHandler(
                        log_dir / log_config.error_log_file,
                        maxBytes=log_config.max_bytes,
                        backupCount=log_config.backup_count,
                        encoding='utf-8'
                    )
                    error_handler.setLevel(logging.ERROR)
                    error_handler.setFormatter(logging.Formatter(
                        log_config.format,
                        datefmt=log_config.date_format
                    ))
                    logging.getLogger().addHandler(error_handler)

                logger.info(f"日志文件已配置: {log_dir}")

            except Exception as e:
                logger.warning(f"无法设置文件日志: {e}")

    def get_dict(self) -> dict[str, Any]:
        """将配置转换为字典"""
        from dataclasses import asdict
        return asdict(self.config)

    def reload(self) -> ExecutionConfig:
        """重新加载配置"""
        logger.info("重新加载配置...")
        return self.load()


# 全局配置加载器实例
_config_loader: ConfigLoader | None = None
_config: ExecutionConfig | None = None


def load_config(
    config_path: str | None = None,
    env_prefix: str = "ATHENA_EXECUTION"
) -> ExecutionConfig:
    """
    加载配置（单例模式）

    Args:
        config_path: 配置文件路径
        env_prefix: 环境变量前缀

    Returns:
        ExecutionConfig: 配置对象
    """
    global _config_loader, _config

    if _config is None:
        _config_loader = ConfigLoader(config_path, env_prefix)
        _config = _config_loader.load()

    return _config


def get_config() -> ExecutionConfig | None:
    """
    获取已加载的配置

    Returns:
        ExecutionConfig: 配置对象，如果未加载则返回None
    """
    return _config


def reload_config() -> ExecutionConfig:
    """
    重新加载配置

    Returns:
        ExecutionConfig: 重新加载的配置对象
    """
    global _config

    if _config_loader is None:
        raise RuntimeError("配置未初始化，请先调用 load_config()")

    _config = _config_loader.reload()
    return _config


if __name__ == "__main__":
    # 测试配置加载
    import sys

    try:
        config = load_config()
        print("配置加载成功！")
        print(f"执行引擎: max_workers={config.execution_engine.max_workers}")
        print(f"日志级别: {config.logging.level}")
        print(f"监控: {config.monitoring.enabled}")

    except Exception as e:
        print(f"配置加载失败: {e}", file=sys.stderr)
        sys.exit(1)
