#!/usr/bin/env python3
from __future__ import annotations
"""
Athena通信系统 - 统一配置管理
Unified Configuration Management for Communication System

提供通信系统的统一配置管理功能,包括:
1. 配置数据类定义
2. 配置加载和验证
3. 配置持久化和恢复
4. 环境变量支持

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import json
import logging
import os
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# 配置数据类
# =============================================================================


@dataclass
class CommunicationConfig:
    """
    通信系统核心配置

    统一管理所有通信相关的配置参数,避免硬编码分散在代码中。
    """

    # 连接配置
    max_connections: int = 1000
    connection_timeout: float = 30.0  # 连接超时(秒)
    connection_backlog: int = 100  # 连接队列大小

    # 队列配置
    max_queue_size: int = 10000
    message_timeout: float = 60.0  # 消息超时(秒)
    queue_retry_limit: int = 3  # 队列重试限制

    # 批处理配置
    batch_size: int = 10
    batch_timeout: float = 1.0  # 批处理超时(秒)
    batch_max_wait: float = 5.0  # 批处理最大等待时间(秒)

    # 压缩配置
    enable_compression: bool = True
    compression_threshold: int = 1024  # 压缩阈值(字节)
    compression_algorithm: str = "gzip"  # gzip, lz4, zstd

    # WebSocket配置
    ws_host: str = "0.0.0.0"
    ws_port: int = 8092
    ws_ping_interval: float = 30.0  # ping间隔(秒)
    ws_ping_timeout: float = 10.0  # ping超时(秒)
    ws_max_message_size: int = 1024 * 1024  # 最大消息大小(1MB)

    # 安全配置
    enable_auth: bool = True
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # JWT过期时间(秒)

    # 速率限制配置
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100  # 时间窗口内最大请求数
    rate_limit_window: int = 60  # 时间窗口(秒)
    rate_limit_burst: int = 10  # 突发请求限制

    # 性能配置
    worker_count: int = 4  # 工作线程数
    io_threads: int = 2  # IO线程数
    max_concurrent_tasks: int = 20  # 最大并发任务数

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json, text
    log_file: Optional[str] = None
    log_max_size: int = 10 * 1024 * 1024  # 日志文件最大大小(10MB)
    log_backup_count: int = 5

    # 监控配置
    enable_metrics: bool = True
    metrics_port: int = 9091
    metrics_path: str = "/metrics"

    # 调试配置
    debug_mode: bool = False
    trace_enabled: bool = False
    profiling_enabled: bool = False

    def validate(self) -> list[str]:
        """
        验证配置有效性

        Returns:
            错误信息列表,空列表表示配置有效
        """
        errors = []

        # 验证数值范围
        if self.max_connections <= 0:
            errors.append("max_connections必须大于0")

        if self.connection_timeout <= 0:
            errors.append("connection_timeout必须大于0")

        if self.max_queue_size <= 0:
            errors.append("max_queue_size必须大于0")

        if self.message_timeout <= 0:
            errors.append("message_timeout必须大于0")

        if self.batch_size <= 0:
            errors.append("batch_size必须大于0")

        if self.batch_timeout <= 0:
            errors.append("batch_timeout必须大于0")

        if not 1 <= self.ws_port <= 65535:
            errors.append("ws_port必须在1-65535范围内")

        if self.rate_limit_requests <= 0:
            errors.append("rate_limit_requests必须大于0")

        if self.rate_limit_window <= 0:
            errors.append("rate_limit_window必须大于0")

        if self.worker_count <= 0:
            errors.append("worker_count必须大于0")

        # 验证枚举值
        valid_compression = ["gzip", "lz4", "zstd", "none"]
        if self.compression_algorithm not in valid_compression:
            errors.append(f"compression_algorithm必须是{valid_compression}之一")

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level必须是{valid_log_levels}之一")

        valid_log_formats = ["json", "text"]
        if self.log_format not in valid_log_formats:
            errors.append(f"log_format必须是{valid_log_formats}之一")

        # 验证依赖关系
        if self.enable_auth and not self.jwt_secret:
            errors.append("启用认证时必须设置jwt_secret")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "CommunicationConfig":
        """
        从字典创建配置

        只使用已定义的字段,忽略额外的字段
        """
        # 获取数据类字段
        field_names = {f.name for f in cls.__dataclass_fields__.values()}

        # 过滤有效字段
        filtered_config = {k: v for k, v in config.items() if k in field_names}

        return cls(**filtered_config)

    @classmethod
    def from_env(cls) -> "CommunicationConfig":
        """
        从环境变量创建配置

        支持的环境变量前缀: ATHENA_COMM_
        """
        config = cls()

        # 环境变量映射
        env_mapping = {
            "ATHENA_COMM_MAX_CONNECTIONS": ("max_connections", int),
            "ATHENA_COMM_CONNECTION_TIMEOUT": ("connection_timeout", float),
            "ATHENA_COMM_MAX_QUEUE_SIZE": ("max_queue_size", int),
            "ATHENA_COMM_MESSAGE_TIMEOUT": ("message_timeout", float),
            "ATHENA_COMM_BATCH_SIZE": ("batch_size", int),
            "ATHENA_COMM_BATCH_TIMEOUT": ("batch_timeout", float),
            "ATHENA_COMM_ENABLE_COMPRESSION": ("enable_compression", lambda x: x.lower() == "true"),
            "ATHENA_COMM_COMPRESSION_THRESHOLD": ("compression_threshold", int),
            "ATHENA_COMM_COMPRESSION_ALGORITHM": ("compression_algorithm", str),
            "ATHENA_COMM_WS_HOST": ("ws_host", str),
            "ATHENA_COMM_WS_PORT": ("ws_port", int),
            "ATHENA_COMM_ENABLE_AUTH": ("enable_auth", lambda x: x.lower() == "true"),
            "ATHENA_COMM_JWT_SECRET": ("jwt_secret", str),
            "ATHENA_COMM_RATE_LIMIT_ENABLED": ("rate_limit_enabled", lambda x: x.lower() == "true"),
            "ATHENA_COMM_RATE_LIMIT_REQUESTS": ("rate_limit_requests", int),
            "ATHENA_COMM_RATE_LIMIT_WINDOW": ("rate_limit_window", int),
            "ATHENA_COMM_LOG_LEVEL": ("log_level", str),
            "ATHENA_COMM_DEBUG_MODE": ("debug_mode", lambda x: x.lower() == "true"),
        }

        # 应用环境变量
        for env_var, (field_name, converter) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    setattr(config, field_name, converter(value))
                    logger.info(f"从环境变量设置配置: {field_name} = {value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"环境变量{env_var}值无效: {value}, 错误: {e}")

        return config

    def save_to_file(self, path: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            path: 文件路径

        Returns:
            是否保存成功
        """
        save_path = path or "config/communication_config.json"

        try:
            # 确保目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存到: {save_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    @classmethod
    def load_from_file(cls, path: str) -> "CommunicationConfig | None":
        """
        从文件加载配置

        Args:
            path: 配置文件路径

        Returns:
            配置对象,失败返回None
        """
        try:
            with open(path, encoding="utf-8") as f:
                config_dict = json.load(f)

            config = cls.from_dict(config_dict)
            logger.info(f"配置已从文件加载: {path}")
            return config

        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {path}")
            return None
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return None


# =============================================================================
# 配置管理器
# =============================================================================


class ConfigManager:
    """
    配置管理器

    提供配置的加载、保存、验证和热更新功能。
    """

    def __init__(self, config: CommunicationConfig | None = None):
        self.config = config or CommunicationConfig()
        self._config_path: Optional[str] = None
        self._observers: list[Callable[[CommunicationConfig], None]] = []

    def load_config(self, path: str) -> bool:
        """
        从文件加载配置

        Args:
            path: 配置文件路径

        Returns:
            是否加载成功
        """
        config = CommunicationConfig.load_from_file(path)
        if config:
            self.config = config
            self._config_path = path
            self._notify_observers()
            return True
        return False

    def save_config(self, path: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            path: 文件路径

        Returns:
            是否保存成功
        """
        save_path = path or self._config_path
        if not save_path:
            save_path = "config/communication_config.json"

        success = self.config.save_to_file(save_path)
        if success:
            self._config_path = save_path
        return success

    def update_config(self, **kwargs) -> bool:
        """
        更新配置

        Args:
            **kwargs: 要更新的配置项

        Returns:
            是否更新成功
        """
        try:
            # 更新配置
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    logger.warning(f"未知的配置项: {key}")

            # 验证配置
            errors = self.config.validate()
            if errors:
                logger.error(f"配置验证失败: {errors}")
                return False

            # 通知观察者
            self._notify_observers()
            return True

        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False

    def get_config(self) -> CommunicationConfig:
        """获取当前配置"""
        return self.config

    def register_observer(self, callback: Callable[[CommunicationConfig], None]) -> Any:
        """
        注册配置变更观察者

        Args:
            callback: 配置变更时的回调函数
        """
        self._observers.append(callback)

    def unregister_observer(self, callback: Callable[[CommunicationConfig], None]) -> Any:
        """
        注销配置变更观察者

        Args:
            callback: 要注销的回调函数
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> Any:
        """通知所有观察者配置已变更"""
        for observer in self._observers:
            try:
                observer(self.config)
            except Exception as e:
                logger.error(f"通知观察者失败: {e}")

    def reload(self) -> bool:
        """
        重新加载配置

        Returns:
            是否重新加载成功
        """
        if self._config_path:
            return self.load_config(self._config_path)
        return False


# =============================================================================
# 全局配置实例
# =============================================================================

_global_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        # 尝试从环境变量创建配置
        config = CommunicationConfig.from_env()

        # 尝试从默认路径加载配置
        default_path = "config/communication_config.json"
        if Path(default_path).exists():
            loaded_config = CommunicationConfig.load_from_file(default_path)
            if loaded_config:
                config = loaded_config

        _global_config_manager = ConfigManager(config)

    return _global_config_manager


def get_config() -> CommunicationConfig:
    """获取当前配置"""
    return get_config_manager().get_config()


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "CommunicationConfig",
    "ConfigManager",
    "get_config",
    "get_config_manager",
]
