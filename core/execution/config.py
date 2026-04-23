#!/usr/bin/env python3
from __future__ import annotations
"""
Athena执行系统 - 统一配置管理
Unified Configuration Management for Execution System

提供执行系统的统一配置管理功能,包括:
1. 配置数据类定义
2. 配置加载和验证
3. 配置持久化和恢复
4. 环境变量支持

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# 执行配置数据类
# =============================================================================


@dataclass
class ExecutionConfig:
    """
    执行系统核心配置

    统一管理所有执行相关的配置参数,避免硬编码分散在代码中。
    """

    # 并发控制
    max_concurrent_tasks: int = 10
    max_queue_size: int = 1000
    max_workers: int = 10

    # 超时配置
    default_timeout: float = 300.0  # 默认超时(秒) - 5分钟
    task_timeout: float = 600.0  # 任务超时(秒) - 10分钟
    deadlock_timeout: float = 30.0  # 死锁检测超时(秒)
    starvation_timeout: float = 60.0  # 饥饿检测超时(秒)

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0  # 重试延迟(秒)
    retry_backoff_factor: float = 2.0  # 退避因子

    # 资源限制
    max_memory_mb: int = 2048  # 最大内存使用(MB)
    max_cpu_usage: float = 0.8  # 最大CPU使用率
    queue_memory_limit_mb: int = 512  # 队列内存限制(MB)

    # 监控和日志
    enable_monitoring: bool = True
    enable_metrics: bool = True
    enable_performance_tracking: bool = True
    metrics_collection_interval: float = 1.0  # 指标收集间隔(秒)

    # 调度配置
    scheduling_strategy: str = "priority_fifo"  # priority_fifo, round_robin, load_balance
    load_balance_threshold: float = 0.8  # 负载均衡阈值
    adaptive_scheduling: bool = True

    # 死锁和饥饿检测
    enable_deadlock_detection: bool = True
    enable_starvation_detection: bool = True
    enable_fair_scheduling: bool = True
    quantum_size: float = 0.1  # 时间片大小(秒)
    aging_factor: float = 0.1  # 老化因子

    # 缓存配置
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600  # 缓存过期时间(秒)
    cache_max_size: int = 1000  # 缓存最大条目数

    # 持久化
    enable_persistence: bool = False
    persistence_path: str = "data/execution_state.json"
    auto_save_interval: float = 60.0  # 自动保存间隔(秒)

    def validate(self) -> list[str]:
        """
        验证配置有效性

        Returns:
            错误信息列表,空列表表示配置有效
        """
        errors = []

        # 验证数值范围
        if self.max_concurrent_tasks <= 0:
            errors.append("max_concurrent_tasks必须大于0")

        if self.max_queue_size <= 0:
            errors.append("max_queue_size必须大于0")

        if self.default_timeout <= 0:
            errors.append("default_timeout必须大于0")

        if self.max_retries < 0:
            errors.append("max_retries不能为负数")

        if not 0 < self.max_cpu_usage <= 1.0:
            errors.append("max_cpu_usage必须在(0, 1]范围内")

        if self.retry_backoff_factor < 1.0:
            errors.append("retry_backoff_factor必须>=1.0")

        # 验证调度策略
        valid_strategies = ["priority_fifo", "round_robin", "load_balance"]
        if self.scheduling_strategy not in valid_strategies:
            errors.append(f"scheduling_strategy必须是{valid_strategies}之一")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "ExecutionConfig":
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
    def from_env(cls) -> "ExecutionConfig":
        """
        从环境变量创建配置

        支持的环境变量前缀: ATHENA_EXEC_
        """
        config = cls()

        # 环境变量映射
        env_mapping = {
            "ATHENA_EXEC_MAX_CONCURRENT_TASKS": ("max_concurrent_tasks", int),
            "ATHENA_EXEC_MAX_QUEUE_SIZE": ("max_queue_size", int),
            "ATHENA_EXEC_MAX_WORKERS": ("max_workers", int),
            "ATHENA_EXEC_DEFAULT_TIMEOUT": ("default_timeout", float),
            "ATHENA_EXEC_TASK_TIMEOUT": ("task_timeout", float),
            "ATHENA_EXEC_MAX_RETRIES": ("max_retries", int),
            "ATHENA_EXEC_MAX_MEMORY_MB": ("max_memory_mb", int),
            "ATHENA_EXEC_MAX_CPU_USAGE": ("max_cpu_usage", float),
            "ATHENA_EXEC_SCHEDULING_STRATEGY": ("scheduling_strategy", str),
            "ATHENA_EXEC_ENABLE_MONITORING": ("enable_monitoring", lambda x: x.lower() == "true"),
            "ATHENA_EXEC_ENABLE_METRICS": ("enable_metrics", lambda x: x.lower() == "true"),
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
            path: 文件路径,默认使用persistence_path

        Returns:
            是否保存成功
        """
        save_path = path or self.persistence_path

        try:
            # 确保目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            import json

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存到: {save_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    @classmethod
    def load_from_file(cls, path: str) -> Optional["ExecutionConfig"]:
        """
        从文件加载配置

        Args:
            path: 配置文件路径

        Returns:
            配置对象,失败返回None
        """
        try:
            import json

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

    def __init__(self, config: ExecutionConfig | None = None):
        self.config = config or ExecutionConfig()
        self._config_path: Optional[str] = None
        self._observers = []

    def load_config(self, path: str) -> bool:
        """
        从文件加载配置

        Args:
            path: 配置文件路径

        Returns:
            是否加载成功
        """
        config = ExecutionConfig.load_from_file(path)
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
            save_path = self.config.persistence_path

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

    def get_config(self) -> ExecutionConfig:
        """获取当前配置"""
        return self.config

    def register_observer(self, callback) -> None:
        """
        注册配置变更观察者

        Args:
            callback: 配置变更时的回调函数
        """
        self._observers.append(callback)

    def _notify_observers(self) -> Any:
        """通知所有观察者配置已变更"""
        for observer in self._observers:
            try:
                observer(self.config)
            except Exception as e:
                logger.error(f"通知观察者失败: {e}")


# =============================================================================
# 全局配置实例
# =============================================================================

# 全局配置管理器实例
_global_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        # 尝试从环境变量创建配置
        config = ExecutionConfig.from_env()

        # 尝试从默认路径加载配置
        if Path(config.persistence_path).exists():
            loaded_config = ExecutionConfig.load_from_file(config.persistence_path)
            if loaded_config:
                config = loaded_config

        _global_config_manager = ConfigManager(config)

    return _global_config_manager


def get_config() -> ExecutionConfig:
    """获取当前配置"""
    return get_config_manager().get_config()


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "ConfigManager",
    "ExecutionConfig",
    "get_config",
    "get_config_manager",
]
