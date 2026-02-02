"""
依赖注入容器
Dependency Injection Container

管理伦理框架组件的创建、配置和生命周期。
实现控制反转(IoC)原则,提供松耦合的组件管理。

支持的功能:
- 单例模式组件管理
- 工厂模式组件创建
- 配置驱动的组件初始化
- 依赖解析和注入
- 生命周期管理
"""

import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

from .config.config_loader import ConfigLoader, EthicsConfig

# 核心模块导入
from .constitution import AthenaConstitution
from .constraints import ConstraintEnforcer, EthicalConstraint
from .evaluator import EthicsEvaluator
from .monitoring import EthicsMonitor
from .monitoring_prometheus import PrometheusMonitor
from .sensitive_data_filter import SensitiveDataFilter
from .wittgenstein_guard import WittgensteinGuard

# ============================================================================
# 类型定义
# ============================================================================

T = TypeVar("T")


class LifecycleType(Enum):
    """组件生命周期类型"""

    SINGLETON = "singleton"  # 单例,整个容器生命周期内只创建一次
    TRANSIENT = "transient"  # 瞬态,每次请求都创建新实例
    SCOPED = "scoped"  # 作用域,在同一作用域内是同一实例


@dataclass
class ServiceDescriptor:
    """服务描述符

    定义如何创建和配置一个服务
    """

    service_type: type[Any]  # 服务类型
    factory: Callable[..., Any]  # 工厂函数
    instance: Any | None = None  # 单例实例
    lifecycle: LifecycleType = LifecycleType.SINGLETON
    dependencies: list = field(default_factory=list)  # 依赖的服务类型列表
    config_key: str | None = None  # 配置键


# ============================================================================
# 容器接口
# ============================================================================


class IContainer(ABC):
    """容器接口

    定义依赖注入容器的核心功能
    """

    @abstractmethod
    def register(
        self,
        service_type: type[T],
        factory: Callable[..., T] | None = None,
        lifecycle: LifecycleType = LifecycleType.SINGLETON,
    ) -> None:
        """注册服务

        Args:
            service_type: 服务类型
            factory: 工厂函数,如果为None则使用服务类型的构造函数
            lifecycle: 生命周期类型
        """
        pass

    @abstractmethod
    def register_instance(self, service_type: type[T], instance: T) -> None:
        """注册服务实例

        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        pass

    @abstractmethod
    def resolve(self, service_type: type[T]) -> T:
        """解析服务

        Args:
            service_type: 服务类型

        Returns:
            服务实例

        Raises:
            KeyError: 服务未注册
        """
        pass

    @abstractmethod
    def is_registered(self, service_type: type[T]) -> bool:
        """检查服务是否已注册

        Args:
            service_type: 服务类型

        Returns:
            是否已注册
        """
        pass


# ============================================================================
# 依赖注入容器实现
# ============================================================================


class EthicsContainer(IContainer):
    """伦理框架依赖注入容器

    集中管理所有伦理框架组件的创建和依赖关系。
    线程安全,支持单例、瞬态和作用域生命周期。

    使用示例:
        ```python
        # 创建容器
        container = EthicsContainer()

        # 使用默认配置初始化
        container.initialize()

        # 解析服务
        constitution = container.resolve(AthenaConstitution)
        evaluator = container.resolve(EthicsEvaluator)
        monitor = container.resolve(EthicsMonitor)

        # 或者使用工厂方法
        evaluator = container.create_evaluator(constitution)
        ```
    """

    def __init__(self, config: EthicsConfig | None = None):
        """初始化容器

        Args:
            config: 伦理框架配置,如果为None则使用默认配置加载器
        """
        self._services: dict[type[Any], ServiceDescriptor] = {}
        self._lock = threading.RLock()
        self._config: Optional[EthicsConfig] = config
        self._initialized: bool = False

        # 注册自身
        self.register_instance(EthicsContainer, self)
        self.register_instance(IContainer, self)

    # ========================================================================
    # IContainer 接口实现
    # ========================================================================

    def register(
        self,
        service_type: type[T],
        factory: Callable[..., T] | None = None,
        lifecycle: LifecycleType = LifecycleType.SINGLETON,
    ) -> None:
        """注册服务

        Args:
            service_type: 服务类型
            factory: 工厂函数
            lifecycle: 生命周期类型
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type, factory=factory, lifecycle=lifecycle
            )
            self._services[service_type] = descriptor

    def register_instance(self, service_type: type[T], instance: T) -> None:
        """注册服务实例

        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type, instance=instance, lifecycle=LifecycleType.SINGLETON
            )
            self._services[service_type] = descriptor

    def resolve(self, service_type: type[T]) -> T:
        """解析服务

        根据生命周期类型返回实例:
        - SINGLETON: 返回已存在的单例实例或创建新实例
        - TRANSIENT: 每次都创建新实例
        - SCOPED: 在当前作用域内返回同一实例

        Args:
            service_type: 服务类型

        Returns:
            服务实例

        Raises:
            KeyError: 服务未注册
        """
        with self._lock:
            if service_type not in self._services:
                # 尝试自动注册
                if service_type == EthicsConfig:
                    self._register_config()
                elif service_type == ConfigLoader:
                    self._register_config_loader()
                else:
                    raise KeyError(f"服务 {service_type.__name__} 未注册")

            descriptor = self._services[service_type]

            if descriptor.lifecycle == LifecycleType.SINGLETON:
                if descriptor.instance is None:
                    descriptor.instance = self._create_instance(descriptor)
                return descriptor.instance

            elif descriptor.lifecycle == LifecycleType.TRANSIENT:
                return self._create_instance(descriptor)

            else:  # SCOPED
                # TODO: 实现作用域生命周期
                if descriptor.instance is None:
                    descriptor.instance = self._create_instance(descriptor)
                return descriptor.instance

    def is_registered(self, service_type: type[T]) -> bool:
        """检查服务是否已注册

        Args:
            service_type: 服务类型

        Returns:
            是否已注册
        """
        return service_type in self._services

    # ========================================================================
    # 工厂方法
    # ========================================================================

    def create_constitution(self) -> AthenaConstitution:
        """创建宪法

        Returns:
            AthenaConstitution实例
        """
        return self.resolve(AthenaConstitution)

    def create_wittgenstein_guard(self) -> WittgensteinGuard:
        """创建维特根斯坦守卫

        Returns:
            WittgensteinGuard实例
        """
        return WittgensteinGuard()

    def create_evaluator(
        self, constitution: AthenaConstitution | None = None
    ) -> EthicsEvaluator:
        """创建评估器

        Args:
            constitution: 宪法实例,如果为None则从容器解析

        Returns:
            伦理评估器实例
        """
        if constitution is None:
            constitution = self.create_constitution()

        # 获取配置
        config = self._get_config()

        # 创建评估器
        return EthicsEvaluator(
            constitution=constitution,
            wittgenstein_guard=self.create_wittgenstein_guard(),
            max_history_size=config.max_history_size if config else 1000,
        )

    def create_constraint(self, evaluator: EthicsEvaluator | None = None) -> EthicalConstraint:
        """创建约束

        Args:
            evaluator: 评估器实例,如果为None则从容器解析

        Returns:
            约束实例
        """
        if evaluator is None:
            evaluator = self.create_evaluator()

        return EthicalConstraint(evaluator=evaluator)

    def create_constraint_enforcer(
        self, constraint: EthicalConstraint | None = None
    ) -> ConstraintEnforcer:
        """创建约束执行器

        Args:
            constraint: 约束实例,如果为None则从容器解析

        Returns:
            约束执行器实例
        """
        if constraint is None:
            constraint = self.create_constraint()

        return ConstraintEnforcer(constraint=constraint)

    def create_monitor(self, evaluator: EthicsEvaluator | None = None) -> EthicsMonitor:
        """创建监控器

        Args:
            evaluator: 评估器实例,如果为None则从容器解析

        Returns:
            监控器实例
        """
        if evaluator is None:
            evaluator = self.create_evaluator()

        return EthicsMonitor(evaluator=evaluator)

    def create_sensitive_filter(self) -> SensitiveDataFilter:
        """创建敏感信息过滤器

        Returns:
            敏感信息过滤器实例
        """
        return SensitiveDataFilter()

    def create_prometheus_monitor(
        self, port: int = 9091, enable_endpoint: bool = True
    ) -> PrometheusMonitor:
        """创建Prometheus监控器

        Args:
            port: Prometheus metrics端点端口
            enable_endpoint: 是否启动HTTP端点

        Returns:
            Prometheus监控器实例
        """
        return PrometheusMonitor(port=port, enable_endpoint=enable_endpoint)

    # ========================================================================
    # 容器初始化和配置
    # ========================================================================

    def initialize(self, config: EthicsConfig | None = None) -> None:
        """初始化容器,注册所有默认服务

        Args:
            config: 伦理框架配置,如果为None则使用默认配置
        """
        with self._lock:
            if self._initialized:
                return

            # 设置配置
            if config is not None:
                self._config = config

            # 注册核心服务
            self._register_core_services()

            # 注册可选服务
            self._register_optional_services()

            self._initialized = True

    def reload_config(self) -> None:
        """重新加载配置"""
        with self._lock:
            # 清除配置相关的单例
            if ConfigLoader in self._services:
                self._services[ConfigLoader].instance = None
            if EthicsConfig in self._services:
                self._services[EthicsConfig].instance = None

            # 重新创建配置加载器
            config_loader = self.resolve(ConfigLoader)
            self._config = config_loader.load_config()

    # ========================================================================
    # 内部方法
    # ========================================================================

    def _get_config(self) -> EthicsConfig | None:
        """获取配置

        Returns:
            伦理框架配置
        """
        if self._config is None and ConfigLoader in self._services:
            config_loader = self.resolve(ConfigLoader)
            self._config = config_loader.load_config()
        return self._config

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例

        Args:
            descriptor: 服务描述符

        Returns:
            服务实例
        """
        factory = descriptor.factory

        if factory is None:
            # 使用服务类型的默认构造函数
            factory = descriptor.service_type

        # 尝试从容器注入依赖
        try:
            instance = factory()
        except TypeError:
            # 如果需要参数,尝试从容器解析
            instance = self._create_with_dependencies(descriptor)

        return instance

    def _create_with_dependencies(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例并注入依赖

        Args:
            descriptor: 服务描述符

        Returns:
            服务实例
        """
        # 对于复杂的服务,使用特定的工厂方法
        if descriptor.service_type == EthicsEvaluator:
            return self.create_evaluator()
        elif descriptor.service_type == EthicalConstraint:
            return self.create_constraint()
        elif descriptor.service_type == ConstraintEnforcer:
            return self.create_constraint_enforcer()
        elif descriptor.service_type == EthicsMonitor:
            return self.create_monitor()
        elif descriptor.service_type == PrometheusMonitor:
            return self.create_prometheus_monitor()
        else:
            # 尝试直接创建
            return descriptor.service_type()

    def _register_core_services(self) -> None:
        """注册核心服务"""
        # 宪法 - 单例
        self.register(AthenaConstitution, lifecycle=LifecycleType.SINGLETON)

        # 维特根斯坦守卫 - 单例
        self.register(
            WittgensteinGuard,
            factory=self.create_wittgenstein_guard,
            lifecycle=LifecycleType.SINGLETON,
        )

        # 评估器 - 单例
        self.register(
            EthicsEvaluator, factory=self.create_evaluator, lifecycle=LifecycleType.SINGLETON
        )

        # 约束 - 单例
        self.register(
            EthicalConstraint, factory=self.create_constraint, lifecycle=LifecycleType.SINGLETON
        )

        # 约束执行器 - 单例
        self.register(
            ConstraintEnforcer,
            factory=self.create_constraint_enforcer,
            lifecycle=LifecycleType.SINGLETON,
        )

        # 监控器 - 单例
        self.register(EthicsMonitor, factory=self.create_monitor, lifecycle=LifecycleType.SINGLETON)

        # 敏感信息过滤器 - 单例
        self.register(
            SensitiveDataFilter,
            factory=self.create_sensitive_filter,
            lifecycle=LifecycleType.SINGLETON,
        )

    def _register_optional_services(self) -> None:
        """注册可选服务"""
        # Prometheus监控器 - 单例
        self.register(
            PrometheusMonitor,
            factory=self.create_prometheus_monitor,
            lifecycle=LifecycleType.SINGLETON,
        )

    def _register_config(self) -> None:
        """注册配置"""
        if self._config is not None:
            self.register_instance(EthicsConfig, self._config)

    def _register_config_loader(self) -> None:
        """注册配置加载器"""
        self.register(ConfigLoader, lifecycle=LifecycleType.SINGLETON)

    def get_container_info(self) -> dict[str, Any]:
        """获取容器信息

        Returns:
            容器状态信息字典
        """
        return {
            "initialized": self._initialized,
            "registered_services": list(self._services.keys()),
            "config_loaded": self._config is not None,
            "service_count": len(self._services),
        }


# ============================================================================
# 全局容器实例
# ============================================================================

_global_container: EthicsContainer | None = None
_container_lock = threading.Lock()


def get_container(config: EthicsConfig | None = None) -> EthicsContainer:
    """获取全局容器实例

    Args:
        config: 伦理框架配置,仅在首次调用时使用

    Returns:
        全局容器实例
    """
    global _global_container

    with _container_lock:
        if _global_container is None:
            _global_container = EthicsContainer(config)
            _global_container.initialize(config)

        return _global_container


def reset_container() -> None:
    """重置全局容器

    主要用于测试环境
    """
    global _global_container

    with _container_lock:
        _global_container = None


# ============================================================================
# 便捷函数
# ============================================================================


def create_evaluator(config: EthicsConfig | None = None) -> EthicsEvaluator:
    """创建伦理评估器

    Args:
        config: 可选配置

    Returns:
        评估器实例
    """
    container = get_container(config)
    return container.create_evaluator()


def create_monitor(config: EthicsConfig | None = None) -> EthicsMonitor:
    """创建伦理监控器

    Args:
        config: 可选配置

    Returns:
        监控器实例
    """
    container = get_container(config)
    return container.create_monitor()


def create_constraint_enforcer(config: EthicsConfig | None = None) -> ConstraintEnforcer:
    """创建约束执行器

    Args:
        config: 可选配置

    Returns:
        约束执行器实例
    """
    container = get_container(config)
    return container.create_constraint_enforcer()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 容器实现
    "EthicsContainer",
    # 容器接口
    "IContainer",
    # 生命周期
    "LifecycleType",
    "ServiceDescriptor",
    "create_constraint_enforcer",
    # 便捷函数
    "create_evaluator",
    "create_monitor",
    # 全局函数
    "get_container",
    "reset_container",
]
