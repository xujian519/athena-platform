"""
意图识别服务 - 依赖注入容器

管理意图识别服务的复杂依赖关系,实现松耦合的架构。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

from __future__ import annotations
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

# ========================================================================
# 服务容器
# ========================================================================


class ServiceContainer:
    """
    服务容器(依赖注入容器)

    管理服务的创建、注册和生命周期。
    """

    def __init__(self):
        """初始化容器"""
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}
        self._singletons: dict[str, Any] = {}
        self._logger = logging.getLogger("intent.container")

    def register(
        self, name: str, factory: Callable | None = None, singleton: bool = True
    ) -> None:
        """
        注册服务

        Args:
            name: 服务名称
            factory: 工厂函数(可选)
            singleton: 是否为单例
        """
        if factory:
            self._factories[name] = factory
        else:
            # 如果没有提供工厂函数,后续通过set_service设置
            pass

        if singleton:
            self._singletons["key"] = None  # 延迟初始化

        self._logger.debug(f"注册服务: {name}")

    def set_service(self, name: str, instance: Any) -> None:
        """
        直接设置服务实例

        Args:
            name: 服务名称
            instance: 服务实例
        """
        self._services[name] = instance
        self._logger.debug(f"设置服务实例: {name}")

    def get(self, name: str) -> Any:
        """
        获取服务

        Args:
            name: 服务名称

        Returns:
            服务实例

        Raises:
            KeyError: 服务未注册
        """
        # 首先检查直接设置的服务
        if name in self._services:
            return self._services[name]

        # 检查单例服务
        if name in self._singletons:
            if self._singletons[name] is None:
                # 延迟初始化
                if name in self._factories:
                    self._singletons[name] = self._factories[name](self)
                else:
                    raise KeyError(f"服务 {name} 没有工厂函数")
            return self._singletons[name]

        # 尝试创建非单例服务
        if name in self._factories:
            return self._factories[name](self)

        raise KeyError(f"服务未注册: {name}")

    def has(self, name: str) -> bool:
        """
        检查服务是否存在

        Args:
            name: 服务名称

        Returns:
            是否存在
        """
        return name in self._services or name in self._factories or name in self._singletons

    def clear(self) -> None:
        """清空所有服务"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._logger.debug("清空服务容器")


# ========================================================================
# 全局容器实例
# ========================================================================

_global_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """
    获取全局服务容器

    Returns:
        全局服务容器实例
    """
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container


def reset_container() -> None:
    """重置全局容器"""
    global _global_container
    _global_container = None


# ========================================================================
# 装饰器
# ========================================================================


def inject(*service_names: str) -> Any:
    """
    依赖注入装饰器

    自动从容器注入依赖服务。

    Args:
        *service_names: 要注入的服务名称

    Returns:
        装饰器函数

    示例:
        @inject('config', 'logger')
        def my_function(config, logger):
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            container = get_container()

            # 获取要注入的服务
            injected_args = {}
            for name in service_names:
                if container.has(name):
                    injected_args[name] = container.get(name)

            # 合并参数
            all_kwargs = {**injected_args, **kwargs}

            return func(*args, **all_kwargs)

        return wrapper

    return decorator


def inject_method(*service_names: str) -> Any:
    """
    方法依赖注入装饰器

    用于类方法的依赖注入。

    Args:
        *service_names: 要注入的服务名称

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            container = get_container()

            injected_args = {}
            for name in service_names:
                if container.has(name):
                    injected_args[name] = container.get(name)

            all_kwargs = {**injected_args, **kwargs}

            return func(self, *args, **all_kwargs)

        return wrapper

    return decorator


# ========================================================================
# 服务定位器
# ========================================================================


class ServiceLocator:
    """
    服务定位器

    提供类型安全的服务访问接口。
    """

    def __init__(self, container: ServiceContainer | None = None):
        """
        初始化服务定位器

        Args:
            container: 服务容器(可选)
        """
        self._container = container or get_container()

    def get_config(self) -> Any:
        """获取配置服务"""
        return self._container.get("config")

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 日志记录器名称

        Returns:
            日志记录器实例
        """
        return logging.getLogger(name)

    def get_embedding_service(self) -> Any:
        """获取嵌入服务"""
        return self._container.get("embedding_service")

    def get_nlp_service(self) -> Any:
        """获取NLP服务"""
        return self._container.get("nlp_service")

    def get_cache_service(self) -> Any:
        """获取缓存服务"""
        return self._container.get("cache_service")


# ========================================================================
# 配置管理器
# ========================================================================


class IntentServiceConfig:
    """
    意图识别服务配置管理器

    集中管理所有服务的配置。
    """

    def __init__(self, config_dict: dict | None = None):
        """
        初始化配置管理器

        Args:
            config_dict: 配置字典
        """
        self.config = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键(支持点号分隔)
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键(支持点号分隔)
            value: 配置值
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def update(self, other: dict) -> None:
        """
        更新配置

        Args:
            other: 其他配置字典
        """

        def _deep_update(base: dict, updates: dict) -> dict:
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    _deep_update(base[key], value)
                else:
                    base[key] = value
            return base

        _deep_update(self.config, other)


# ========================================================================
# 服务工厂函数
# ========================================================================


def create_embedding_service(container: ServiceContainer) -> Any:
    """
    创建嵌入服务

    Args:
        container: 服务容器

    Returns:
        嵌入服务实例
    """
    # 这里可以延迟导入以避免循环依赖
    from core.embedding.unified_embedding_service import get_unified_embedding_service

    return get_unified_embedding_service()


def create_nlp_service(container: ServiceContainer) -> Any:
    """
    创建NLP服务

    Args:
        container: 服务容器

    Returns:
        NLP服务实例
    """
    from core.nlp.stable_semantic_similarity import get_stable_semantic_similarity

    return get_stable_semantic_similarity()


def create_cache_service(container: ServiceContainer) -> Any:
    """
    创建缓存服务

    Args:
        container: 服务容器

    Returns:
        缓存服务实例
    """
    from core.intent.utils import SimpleCache

    config = container.get("config")
    max_size = config.get("cache.embedding.max_size", 1000)
    ttl = config.get("cache.embedding.ttl", 3600)

    return SimpleCache(max_size=max_size, ttl=ttl)


# ========================================================================
# 容器初始化
# ========================================================================


def initialize_container(config: dict | None | None = None) -> ServiceContainer:
    """
    初始化服务容器

    注册所有默认服务。

    Args:
        config: 配置字典

    Returns:
        初始化后的容器
    """
    container = get_container()

    # 注册配置
    from core.intent.config_loader import IntentConfig

    intent_config = IntentConfig()
    container.set_service("config", intent_config)

    # 注册服务工厂
    container.register("embedding_service", create_embedding_service, singleton=True)
    container.register("nlp_service", create_nlp_service, singleton=True)
    container.register("cache_service", create_cache_service, singleton=True)

    # 注册配置管理器
    container.set_service("service_config", IntentServiceConfig(config))

    return container


# ========================================================================
# 导出
# ========================================================================

__all__ = [
    "IntentServiceConfig",
    "ServiceContainer",
    "ServiceLocator",
    "get_container",
    "initialize_container",
    "inject",
    "inject_method",
    "reset_container",
]
