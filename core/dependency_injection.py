#!/usr/bin/env python3
"""
依赖注入容器
Dependency Injection Container

版本: 1.0.0
功能:
- 管理服务单例
- 自动依赖解析
- 生命周期管理
- 替代全局单例模式
"""

import asyncio
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

logger = logging.getLogger(__name__)


T = TypeVar("T")


class ServiceLifetime(Enum):
    """服务生命周期"""

    SINGLETON = "singleton"  # 单例,全局唯一
    SCOPED = "scoped"  # 作用域内唯一
    TRANSIENT = "transient"  # 每次创建新实例


@dataclass
class ServiceDescriptor:
    """服务描述符"""

    factory: Callable[[], Any]
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    dependencies: list[str] = field(default_factory=list)


class ServiceContainer:
    """
    服务容器

    管理所有服务的创建和依赖注入
    """

    def __init__(self):
        """初始化容器"""
        # 服务注册表
        self._services: dict[str, ServiceDescriptor] = {}

        # 单例缓存
        self._singletons: dict[str, Any] = {}

        # 作用域缓存(每个请求一个)
        self._scoped: dict[str, Any] = {}

        logger.info("✅ 服务容器初始化完成")

    def register(
        self,
        name: str,
        factory: Callable[[], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        dependencies: list[str] | None = None,
    ) -> None:
        """
        注册服务

        Args:
            name: 服务名称
            factory: 工厂函数
            lifetime: 生命周期
            dependencies: 依赖的服务名称列表
        """
        self._services[name] = ServiceDescriptor(
            factory=factory, lifetime=lifetime, dependencies=dependencies or []
        )
        logger.info(f"✅ 已注册服务: {name} ({lifetime.value})")

    def register_singleton(
        self, name: str, factory: Callable[[], T], dependencies: list[str] | None = None
    ) -> None:
        """注册单例服务"""
        self.register(name, factory, ServiceLifetime.SINGLETON, dependencies)

    def register_scoped(
        self, name: str, factory: Callable[[], T], dependencies: list[str] | None = None
    ) -> None:
        """注册作用域服务"""
        self.register(name, factory, ServiceLifetime.SCOPED, dependencies)

    def register_transient(
        self, name: str, factory: Callable[[], T], dependencies: list[str] | None = None
    ) -> None:
        """注册瞬态服务"""
        self.register(name, factory, ServiceLifetime.TRANSIENT, dependencies)

    def get(self, name: str) -> Any:
        """
        获取服务实例

        Args:
            name: 服务名称

        Returns:
            服务实例
        """
        if name not in self._services:
            raise ValueError(f"服务未注册: {name}")

        descriptor = self._services[name]

        # 根据生命周期返回实例
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._get_singleton(name, descriptor)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return self._get_scoped(name, descriptor)
        else:  # TRANSIENT
            return self._create_instance(name, descriptor)

    def _get_singleton(self, name: str, descriptor: ServiceDescriptor) -> Any:
        """获取单例实例"""
        if name not in self._singletons:
            self._singletons[name] = self._create_instance(name, descriptor)
        return self._singletons[name]

    def _get_scoped(self, name: str, descriptor: ServiceDescriptor) -> Any:
        """获取作用域实例"""
        if name not in self._scoped:
            self._scoped[name] = self._create_instance(name, descriptor)
        return self._scoped[name]

    def _create_instance(self, name: str, descriptor: ServiceDescriptor) -> Any:
        """创建新实例"""
        # 解析依赖
        dependencies = {dep_name: self.get(dep_name) for dep_name in descriptor.dependencies}

        # 调用工厂函数
        instance = descriptor.factory(**dependencies)
        logger.debug(f"✅ 创建服务实例: {name}")
        return instance

    @asynccontextmanager
    async def scope(self):
        """
        创建作用域上下文

        Usage:
            async with container.scope():
                service1 = container.get("service1")
                service2 = container.get("service1")  # 同一实例
        """
        old_scoped = self._scoped.copy()
        self._scoped = {}
        try:
            yield self
        finally:
            # 清理作用域资源
            await self._cleanup_scoped()
            self._scoped = old_scoped

    async def _cleanup_scoped(self):
        """清理作用域资源"""
        for name, instance in self._scoped.items():
            # 如果有close方法,调用它
            if hasattr(instance, "close"):
                try:
                    if asyncio.iscoroutinefunction(instance.close):
                        await instance.close()
                    else:
                        instance.close()
                except Exception as e:
                    logger.warning(f"⚠️ 清理服务失败 {name}: {e}")

    async def shutdown(self):
        """关闭容器,清理所有资源"""
        logger.info("🛑 关闭服务容器...")

        # 清理作用域
        await self._cleanup_scoped()

        # 清理单例
        for name, instance in self._singletons.items():
            if hasattr(instance, "close"):
                try:
                    if asyncio.iscoroutinefunction(instance.close):
                        await instance.close()
                    else:
                        instance.close()
                except Exception as e:
                    logger.warning(f"⚠️ 清理单例失败 {name}: {e}")

        self._singletons.clear()
        logger.info("✅ 服务容器已关闭")


# 全局容器
_global_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """
    获取全局服务容器

    Returns:
        ServiceContainer实例
    """
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container


def reset_container():
    """重置容器(用于测试)"""
    global _global_container
    _global_container = None


# ============================================================================
# 预配置的服务工厂
# ============================================================================


def _create_scenario_identifier(**deps) -> Any:
    """创建场景识别器"""
    from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized

    return ScenarioIdentifierOptimized(
        enable_llm_fallback=True, cache_size=1024, enable_metrics=True
    )


def _create_scenario_rule_retriever(**deps) -> Any:
    """创建规则检索器"""
    from core.legal_world_model.scenario_rule_retriever_async import AsyncScenarioRuleRetriever

    db_manager = deps.get("db_manager")
    if not db_manager:
        raise ValueError("db_manager依赖未找到")
    return AsyncScenarioRuleRetriever(db_manager=db_manager, enable_preload=True)


def _create_capability_invoker(**deps) -> Any:
    """创建能力调用器"""
    from core.capabilities.capability_invoker_optimized import CapabilityInvokerOptimized

    return CapabilityInvokerOptimized()


def _create_prompt_cache(**deps) -> Any:
    """创建提示词缓存"""
    from core.capabilities.prompt_template_cache import PromptTemplateCache

    return PromptTemplateCache(max_size=1000, ttl_seconds=3600)


def _create_metrics_collector(**deps) -> Any:
    """创建指标收集器"""
    from core.monitoring.metrics_collector import MetricsCollector

    return MetricsCollector(max_history=1000)


def _create_rate_limiter(**deps) -> Any:
    """创建速率限制器"""
    from core.middleware.rate_limit import MemoryRateLimiter, RateLimitConfig

    return MemoryRateLimiter(RateLimitConfig())


def initialize_container(container: ServiceContainer | None = None) -> ServiceContainer:
    """
    初始化服务容器,注册所有服务

    Args:
        container: 服务容器(None使用全局容器)

    Returns:
        初始化后的容器
    """
    if container is None:
        container = get_container()

    # 注册所有核心服务
    container.register_singleton("scenario_identifier", _create_scenario_identifier)
    container.register_singleton(
        "scenario_rule_retriever", _create_scenario_rule_retriever, ["db_manager"]
    )
    container.register_singleton("capability_invoker", _create_capability_invoker)
    container.register_singleton("prompt_cache", _create_prompt_cache)
    container.register_singleton("metrics_collector", _create_metrics_collector)
    container.register_singleton("rate_limiter", _create_rate_limiter)

    logger.info("✅ 服务容器初始化完成,已注册6个核心服务")

    return container


# 便捷函数
def get_service(name: str) -> Any:
    """获取服务"""
    container = get_container()
    return container.get(name)


async def with_scope(func):
    """在作用域中执行函数"""
    container = get_container()
    async with container.scope():
        return await func()
