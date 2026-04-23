"""
服务注册中心测试
"""

import pytest
from core.service_registry import (
    ServiceHealth,
    ServiceInfo,
    ServiceStatus,
    get_discovery_api,
    get_service_registry,
)


class TestServiceRegistry:
    """测试服务注册表"""

    def test_register_service(self):
        """测试注册服务"""
        registry = get_service_registry()

        service = ServiceInfo(
            id="test-service-001",
            name="test-service",
            type="test",
            host="localhost",
            port=8001,
            health_check_url="http://localhost:8001/health"
        )

        result = registry.register(service)
        assert result is True

        # 验证服务已注册
        retrieved = registry.get_service("test-service-001")
        assert retrieved is not None
        assert retrieved.name == "test-service"

    def test_deregister_service(self):
        """测试注销服务"""
        registry = get_service_registry()

        service = ServiceInfo(
            id="test-service-002",
            name="test-service",
            type="test",
            host="localhost",
            port=8002,
            health_check_url="http://localhost:8002/health"
        )

        registry.register(service)
        result = registry.deregister("test-service-002")
        assert result is True

        # 验证服务已注销
        retrieved = registry.get_service("test-service-002")
        assert retrieved is None

    def test_find_services(self):
        """测试查找服务"""
        registry = get_service_registry()

        # 注册多个服务
        for i in range(3):
            service = ServiceInfo(
                id=f"test-service-{i:03d}",
                name="test-service",
                type="test",
                host="localhost",
                port=8000 + i,
                health_check_url=f"http://localhost:{8000 + i}/health",
                tags=["tag1", "tag2"]
            )
            registry.register(service)

        # 按名称查找
        services = registry.find_services(name="test-service")
        assert len(services) >= 3

        # 按类型查找
        services = registry.find_services(service_type="test")
        assert len(services) >= 3

    def test_update_health(self):
        """测试更新健康状态"""
        registry = get_service_registry()

        service = ServiceInfo(
            id="test-service-003",
            name="test-service",
            type="test",
            host="localhost",
            port=8003,
            health_check_url="http://localhost:8003/health"
        )

        registry.register(service)

        # 更新健康状态
        health = ServiceHealth(status=ServiceStatus.RUNNING)
        result = registry.update_health("test-service-003", health)
        assert result is True

        # 验证更新
        retrieved = registry.get_service("test-service-003")
        assert retrieved.health.status == ServiceStatus.RUNNING


class TestDiscoveryAPI:
    """测试服务发现API"""

    def test_discover_service(self):
        """测试发现服务"""
        registry = get_service_registry()
        api = get_discovery_api()

        # 注册测试服务
        service = ServiceInfo(
            id="test-service-004",
            name="test-service",
            type="test",
            host="localhost",
            port=8004,
            health_check_url="http://localhost:8004/health"
        )
        registry.register(service)

        # 发现服务（不要求健康，避免异步问题）
        import asyncio
        discovered = asyncio.run(
            api.discover("test-service", healthy_only=False)
        )

        assert discovered is not None
        assert discovered.name == "test-service"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
