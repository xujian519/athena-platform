"""
Athena Service Discovery System - Simple Test
简化的服务发现系统测试

Author: Athena AI Team
Version: 2.0.0
"""

import asyncio
from dataclasses import dataclass
from enum import Enum


# 简化的核心数据结构
class ProtocolType(Enum):
    HTTP = "http"
    GRPC = "grpc"
    GRAPHQL = "graphql"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceInstance:
    service_id: str
    service_name: str
    host: str
    port: int
    protocol: ProtocolType
    health_status: HealthStatus = HealthStatus.UNKNOWN
    weight: int = 100
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class SimpleServiceRegistry:
    """简化的服务注册中心"""

    def __init__(self):
        self.services: dict[str, ServiceInstance] = {}

    async def register_service(self, instance: ServiceInstance) -> bool:
        """注册服务"""
        self.services[instance.service_id] = instance
        print(f"✅ Service registered: {instance.service_id}")
        return True

    async def discover_services(self, service_name: str) -> list[ServiceInstance]:
        """发现服务"""
        instances = [
            instance for instance in self.services.values() if instance.service_name == service_name
        ]
        return instances


class SimpleLoadBalancer:
    """简化的负载均衡器"""

    def __init__(self):
        self.current_index = 0

    async def select_instance(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """简单的轮询选择"""
        if not instances:
            raise ValueError("No instances available")

        selected = instances[self.current_index % len(instances)]
        self.current_index += 1
        return selected


class AthenaServiceDiscovery:
    """简化的Athena服务发现系统"""

    def __init__(self):
        self.registry = SimpleServiceRegistry()
        self.load_balancer = SimpleLoadBalancer()

    async def initialize(self):
        """初始化系统"""
        print("🚀 Athena Service Discovery initializing...")

        # 注册示例服务
        services = [
            ServiceInstance(
                service_id="user-service-1",
                service_name="user-service",
                host="localhost",
                port=9001,
                protocol=ProtocolType.HTTP,
            ),
            ServiceInstance(
                service_id="user-service-2",
                service_name="user-service",
                host="localhost",
                port=9002,
                protocol=ProtocolType.HTTP,
            ),
            ServiceInstance(
                service_id="order-service-1",
                service_name="order-service",
                host="localhost",
                port=9003,
                protocol=ProtocolType.HTTP,
            ),
        ]

        for service in services:
            await self.registry.register_service(service)

        print("✅ Athena Service Discovery initialized successfully")

    async def route_request(self, service_name: str) -> ServiceInstance | None:
        """路由请求"""
        instances = await self.registry.discover_services(service_name)
        if not instances:
            print(f"❌ No instances found for service: {service_name}")
            return None

        selected = await self.load_balancer.select_instance(instances)
        print(f"🎯 Routed request to: {selected.service_id}")
        return selected


async def main():
    """主函数测试"""
    print("=" * 60)
    print("🎯 Athena Service Discovery System - Simple Test")
    print("=" * 60)

    # 创建服务发现系统
    discovery = AthenaServiceDiscovery()
    await discovery.initialize()

    print("\n📋 Testing service discovery:")
    print("-" * 40)

    # 测试服务发现
    user_services = await discovery.registry.discover_services("user-service")
    print(f"User service instances: {len(user_services)}")
    for instance in user_services:
        print(f"  - {instance.service_id} ({instance.host}:{instance.port})")

    # 测试负载均衡
    print("\n⚖️ Testing load balancing (5 requests):")
    print("-" * 40)

    for i in range(5):
        selected = await discovery.route_request("user-service")
        if selected:
            print(f"Request {i + 1}: {selected.service_id} at {selected.host}:{selected.port}")

    print("\n✅ All tests completed successfully!")
    print("🎯 Athena Service Discovery System is ready!")


if __name__ == "__main__":
    asyncio.run(main())
