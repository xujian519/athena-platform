"""
服务注册中心

> 版本: v1.0
> 更新: 2026-04-21

统一的服务注册、发现和健康检查系统
"""

from .models import (
    ServiceStatus,
    ServiceHealth,
    ServiceInfo,
    ServiceRegistry as ServiceRegistryModel,
)
from .registry import ServiceRegistry, get_service_registry
from .health_check import HealthChecker, get_health_checker
from .discovery import DiscoveryAPI, get_discovery_api

__all__ = [
    # Models
    "ServiceStatus",
    "ServiceHealth",
    "ServiceInfo",
    "ServiceRegistryModel",
    # Registry
    "ServiceRegistry",
    "get_service_registry",
    # Health Check
    "HealthChecker",
    "get_health_checker",
    # Discovery
    "DiscoveryAPI",
    "get_discovery_api",
]
