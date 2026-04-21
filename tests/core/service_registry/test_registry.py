#!/usr/bin/env python3
"""
服务注册中心测试（简化版）
Tests for core.service_registry.registry
"""

import pytest


class TestServiceRegistry:
    """测试ServiceRegistry类"""

    def test_import_registry(self):
        """测试导入注册表模块"""
        from core.service_registry.registry import ServiceRegistry
        assert ServiceRegistry is not None

    def test_registry_singleton(self):
        """测试单例模式"""
        from core.service_registry.registry import get_service_registry
        registry1 = get_service_registry()
        registry2 = get_service_registry()
        assert registry1 is registry2

    def test_registry_has_methods(self):
        """测试注册表方法存在"""
        from core.service_registry.registry import get_service_registry
        registry = get_service_registry()
        # 验证核心方法存在
        assert hasattr(registry, 'register')
        assert hasattr(registry, 'get_service')


class TestServiceInfo:
    """测试ServiceInfo模型"""

    def test_import_models(self):
        """测试导入模型"""
        from core.service_registry.models import ServiceInfo, ServiceStatus
        assert ServiceInfo is not None
        assert ServiceStatus is not None

    def test_service_status_enum(self):
        """测试服务状态枚举"""
        from core.service_registry.models import ServiceStatus
        # 验证状态值存在
        assert hasattr(ServiceStatus, 'HEALTHY')
        assert hasattr(ServiceStatus, 'UNHEALTHY')
