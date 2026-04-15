#!/usr/bin/env python3
"""
性能优化配置加载器
Performance Configuration Loader

从YAML文件加载性能优化配置并应用到系统中

作者: Athena AI Team
创建时间: 2026-01-11
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


class PerformanceConfigLoader:
    """性能配置加载器"""

    def __init__(self, config_path: str = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径,默认为项目根目录下的config/performance_optimization_config.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "performance_optimization_config.yaml"

        self.config_path = Path(config_path)
        self.config = None

    def load_config(self) -> dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典
        """
        if not YAML_AVAILABLE:
            logger.warning("YAML模块未安装,使用默认配置")
            return self._get_default_config()

        if not self.config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_path},使用默认配置")
            return self._get_default_config()

        try:
            with open(self.config_path, encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            logger.info(f"✅ 配置文件已加载: {self.config_path}")
            return self.config

        except Exception as e:
            logger.error(f"加载配置文件失败: {e},使用默认配置")
            return self._get_default_config()

    def apply_config(self, config: dict[str, Any] | None = None) -> Any:
        """
        应用配置到系统

        Args:
            config: 配置字典,如果为None则使用已加载的配置
        """
        if config is None:
            config = self.config or self.load_config()

        try:
            # 应用并发控制配置
            self._apply_concurrency_config(config.get("concurrency_control", {}))

            # 应用批处理配置
            self._apply_batch_config(config.get("batch_processing", {}))

            # 应用数据库连接池配置
            self._apply_database_config(config.get("database_pool", {}))

            # 应用任务队列配置
            self._apply_task_queue_config(config.get("task_queue", {}))

            logger.info("✅ 配置已应用到系统")

        except Exception as e:
            logger.error(f"应用配置失败: {e}")

    def _apply_concurrency_config(self, config: dict[str, Any]) -> Any:
        """应用并发控制配置"""
        from core.performance.concurrency_control import get_limiter, get_rate_limiter

        # API请求限流器
        api_config = config.get("api_requests", {})
        if api_config:
            api_limiter = get_limiter(
                "api_requests",
                max_concurrent=api_config.get("max_concurrent", 100)
            )
            logger.info(f"   API限流器: max_concurrent={api_config.get('max_concurrent', 100)}")

        # 数据库查询限流器
        db_config = config.get("db_queries", {})
        if db_config:
            db_limiter = get_limiter(
                "db_queries",
                max_concurrent=db_config.get("max_concurrent", 50)
            )
            logger.info(f"   数据库限流器: max_concurrent={db_config.get('max_concurrent', 50)}")

        # 外部API限流器
        external_config = config.get("external_api", {})
        if external_config:
            rate_limiter = get_rate_limiter(
                "external_api",
                rate=external_config.get("rate", 100),
                per=external_config.get("per", 1.0)
            )
            logger.info(f"   外部API限流器: rate={external_config.get('rate', 100)}/1s")

    def _apply_batch_config(self, config: dict[str, Any]) -> Any:
        """应用批处理配置"""
        ai_models_config = config.get("ai_models", {})
        if ai_models_config:
            logger.info(f"   批处理配置: batch_size={ai_models_config.get('batch_size', 32)}")
            # 批处理配置会在创建BatchProcessor实例时应用

    def _apply_database_config(self, config: dict[str, Any]) -> Any:
        """应用数据库连接池配置"""
        postgresql_config = config.get("postgresql", {})
        if postgresql_config:
            logger.info(f"   数据库连接池: pool_size={postgresql_config.get('pool_size', 50)}")
            # 连接池配置会在创建连接池时应用

    def _apply_task_queue_config(self, config: dict[str, Any]) -> Any:
        """应用任务队列配置"""
        background_config = config.get("background_tasks", {})
        if background_config:
            logger.info(f"   任务队列: max_workers={background_config.get('max_workers', 50)}")
            # 任务队列配置会在创建AsyncTaskQueue实例时应用

    def get_scenario_config(self, scenario: str) -> dict[str, Any]:
        """
        获取场景化配置

        Args:
            scenario: 场景名称(low_latency, high_throughput, resource_constrained)

        Returns:
            场景配置字典
        """
        config = self.config or self.load_config()
        scenarios = config.get("scenarios", {})

        if scenario not in scenarios:
            logger.warning(f"场景不存在: {scenario}")
            return {}

        return scenarios[scenario]

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "global": {
                "environment": "production",
                "auto_tuning_enabled": True,
                "metrics_sampling_interval": 60
            },
            "concurrency_control": {
                "api_requests": {
                    "max_concurrent": 100,
                    "timeout": 30
                },
                "db_queries": {
                    "max_concurrent": 50,
                    "timeout": 10
                },
                "external_api": {
                    "rate": 100,
                    "per": 1.0,
                    "burst": 200
                }
            },
            "batch_processing": {
                "ai_models": {
                    "batch_size": 32,
                    "min_batch_size": 8,
                    "max_batch_size": 64,
                    "timeout_ms": 100,
                    "adaptive_batching": True,
                    "device": "mps"
                }
            },
            "database_pool": {
                "postgresql": {
                    "pool_size": 50,
                    "max_overflow": 20,
                    "pool_timeout": 10,
                    "pool_recycle": 1800,
                    "pool_use_lifo": True
                }
            }
        }

    def get_param(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置参数

        Args:
            key_path: 配置键路径,用点分隔,例如 "concurrency_control.api_requests.max_concurrent"
            default: 默认值

        Returns:
            配置值
        """
        config = self.config or self.load_config()

        keys = key_path.split(".")
        value = config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default

        return value if value is not None else default


# 便捷函数
_config_loader_instance: PerformanceConfigLoader | None = None


def get_config_loader(config_path: str = None) -> PerformanceConfigLoader:
    """获取配置加载器实例"""
    global _config_loader_instance

    if _config_loader_instance is None:
        _config_loader_instance = PerformanceConfigLoader(config_path)

    return _config_loader_instance


def load_performance_config(config_path: str = None) -> dict[str, Any]:
    """
    加载性能配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    loader = get_config_loader(config_path)
    return loader.load_config()


def apply_performance_config(config_path: str = None) -> Any:
    """
    应用性能配置

    Args:
        config_path: 配置文件路径
    """
    loader = get_config_loader(config_path)
    config = loader.load_config()
    loader.apply_config(config)


if __name__ == "__main__":
    # 测试配置加载
    logging.basicConfig(level=logging.INFO)

    loader = PerformanceConfigLoader()
    config = loader.load_config()

    print("\n📋 配置内容:")
    print(f"环境: {config.get('global', {}).get('environment')}")
    print(f"API并发限制: {config.get('concurrency_control', {}).get('api_requests', {}).get('max_concurrent')}")
    print(f"批大小: {config.get('batch_processing', {}).get('ai_models', {}).get('batch_size')}")

    # 应用配置
    print("\n🔧 应用配置...")
    loader.apply_config()

    # 获取场景配置
    print("\n📊 场景配置:")
    for scenario_name in ["low_latency", "high_throughput", "resource_constrained"]:
        scenario = loader.get_scenario_config(scenario_name)
        if scenario:
            print(f"{scenario_name}: {scenario.get('description', 'N/A')}")
