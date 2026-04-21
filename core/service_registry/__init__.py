"""
服务注册中心模块
Service Registry Module

提供统一的服务注册、发现和健康检查功能
"""

from core.service_registry.models import (
    ServiceInstance,
    ServiceStatus,
    ServiceRegistration,
    HealthCheckConfig,
    LoadBalanceStrategy
)
from core.service_registry.storage import (
    ServiceRegistryStorage,
    get_storage
)
from core.service_registry.health_checker import (
    HealthChecker,
    HealthCheckResult,
    get_health_checker
)
from core.service_registry.discovery import (
    ServiceDiscovery,
    get_discovery,
    NoHealthyInstanceError
)
from core.service_registry.registry import (
    ServiceRegistryCenter,
    get_registry
)

__all__ = [
    # Models
    "ServiceInstance",
    "ServiceStatus",
    "ServiceRegistration",
    "HealthCheckConfig",
    "LoadBalanceStrategy",

    # Storage
    "ServiceRegistryStorage",
    "get_storage",

    # Health Checker
    "HealthChecker",
    "HealthCheckResult",
    "get_health_checker",

    # Discovery
    "ServiceDiscovery",
    "get_discovery",
    "NoHealthyInstanceError",

    # Registry
    "ServiceRegistryCenter",
    "get_registry",
]

__version__ = "1.0.0"
__author__ = "Claude Code (OMC)"
