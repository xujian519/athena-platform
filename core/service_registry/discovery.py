"""
服务发现
Service Discovery
"""
import random
import logging
from typing import Optional, List
from abc import ABC, abstractmethod

from core.service_registry.models import (
    ServiceInstance,
    ServiceStatus,
    LoadBalanceStrategy
)
from core.service_registry.storage import ServiceRegistryStorage


logger = logging.getLogger(__name__)


class NoHealthyInstanceError(Exception):
    """没有健康实例异常"""
    pass


class LoadBalancer(ABC):
    """负载均衡器抽象基类"""

    @abstractmethod
    async def select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """选择一个实例

        Args:
            instances: 实例列表

        Returns:
            选中的实例

        Raises:
            NoHealthyInstanceError: 没有健康实例
        """
        pass


class RoundRobinBalancer(LoadBalancer):
    """轮询负载均衡器"""

    def __init__(self):
        self.counter = 0

    async def select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """选择下一个实例"""
        if not instances:
            raise NoHealthyInstanceError("没有可用的健康实例")

        instance = instances[self.counter % len(instances)]
        self.counter += 1
        return instance


class RandomBalancer(LoadBalancer):
    """随机负载均衡器"""

    async def select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """随机选择实例"""
        if not instances:
            raise NoHealthyInstanceError("没有可用的健康实例")

        return random.choice(instances)


class LeastConnectionBalancer(LoadBalancer):
    """最少连接负载均衡器"""

    def __init__(self):
        self.connections: dict[str, int] = {}

    async def select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """选择连接数最少的实例"""
        if not instances:
            raise NoHealthyInstanceError("没有可用的健康实例")

        # 获取连接数最少的实例
        instance = min(
            instances,
            key=lambda i: self.connections.get(i.instance_id, 0)
        )

        # 增加连接计数
        self.connections[instance.instance_id] = self.connections.get(instance.instance_id, 0) + 1

        return instance

    def release_connection(self, instance_id: str):
        """释放连接"""
        if instance_id in self.connections:
            self.connections[instance_id] -= 1
            if self.connections[instance_id] <= 0:
                del self.connections[instance_id]


class ServiceDiscovery:
    """服务发现"""

    def __init__(
        self,
        storage: Optional[ServiceRegistryStorage] = None,
        default_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    ):
        """初始化服务发现

        Args:
            storage: 存储实例
            default_strategy: 默认负载均衡策略
        """
        self.storage = storage or ServiceRegistryStorage()
        self.default_strategy = default_strategy

        # 初始化负载均衡器
        self.balancers = {
            LoadBalanceStrategy.ROUND_ROBIN: RoundRobinBalancer(),
            LoadBalanceStrategy.RANDOM: RandomBalancer(),
            LoadBalanceStrategy.LEAST_CONNECTION: LeastConnectionBalancer(),
        }

    def _get_balancer(self, strategy: LoadBalanceStrategy) -> LoadBalancer:
        """获取负载均衡器"""
        return self.balancers.get(strategy, self.balancers[LoadBalanceStrategy.ROUND_ROBIN])

    async def register(
        self,
        service_name: str,
        instance_id: str,
        host: str,
        port: int,
        metadata: Optional[dict] = None,
        ttl: int = 300
    ) -> bool:
        """注册服务

        Args:
            service_name: 服务名称
            instance_id: 实例ID
            host: 主机地址
            port: 端口
            metadata: 元数据
            ttl: 过期时间（秒）

        Returns:
            是否注册成功
        """
        try:
            from core.service_registry.models import ServiceRegistration

            registration = ServiceRegistration(
                service_name=service_name,
                instance_id=instance_id,
                host=host,
                port=port,
                metadata=metadata or {}
            )

            instance = registration.to_service_instance()
            return await self.storage.register_instance(instance, ttl)

        except Exception as e:
            logger.error(f"❌ 注册服务失败: {e}")
            return False

    async def deregister(
        self,
        service_name: str,
        instance_id: str
    ) -> bool:
        """注销服务

        Args:
            service_name: 服务名称
            instance_id: 实例ID

        Returns:
            是否注销成功
        """
        try:
            return await self.storage.deregister_instance(service_name, instance_id)
        except Exception as e:
            logger.error(f"❌ 注销服务失败: {e}")
            return False

    async def heartbeat(
        self,
        service_name: str,
        instance_id: str
    ) -> bool:
        """发送心跳

        Args:
            service_name: 服务名称
            instance_id: 实例ID

        Returns:
            是否成功
        """
        try:
            return await self.storage.heartbeat(service_name, instance_id)
        except Exception as e:
            logger.error(f"❌ 发送心跳失败: {e}")
            return False

    async def discover(
        self,
        service_name: str,
        strategy: Optional[LoadBalanceStrategy] = None,
        healthy_only: bool = True
    ) -> Optional[ServiceInstance]:
        """发现服务

        Args:
            service_name: 服务名称
            strategy: 负载均衡策略
            healthy_only: 是否只返回健康实例

        Returns:
            服务实例或None
        """
        try:
            # 获取所有实例
            status = ServiceStatus.HEALTHY if healthy_only else None
            instances = await self.storage.get_all_instances(service_name, status)

            if not instances:
                logger.warning(f"⚠️ 没有找到服务实例: {service_name}")
                return None

            # 使用负载均衡器选择实例
            balancer = self._get_balancer(strategy or self.default_strategy)
            instance = await balancer.select(instances)

            logger.debug(
                f"✅ 发现服务: {service_name} -> {instance.address} "
                f"({strategy or self.default_strategy.value})"
            )

            return instance

        except NoHealthyInstanceError:
            logger.warning(f"⚠️ 没有健康的实例: {service_name}")
            return None
        except Exception as e:
            logger.error(f"❌ 发现服务失败: {e}")
            return None

    async def get_all_instances(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """获取所有服务实例

        Args:
            service_name: 服务名称
            healthy_only: 是否只返回健康实例

        Returns:
            服务实例列表
        """
        try:
            status = ServiceStatus.HEALTHY if healthy_only else None
            return await self.storage.get_all_instances(service_name, status)
        except Exception as e:
            logger.error(f"❌ 获取所有实例失败: {e}")
            return []

    async def get_service_names(self) -> List[str]:
        """获取所有服务名称

        Returns:
            服务名称列表
        """
        try:
            return await self.storage.get_all_services()
        except Exception as e:
            logger.error(f"❌ 获取服务名称失败: {e}")
            return []

    async def get_service_count(self, service_name: str, healthy_only: bool = True) -> int:
        """获取服务实例数量

        Args:
            service_name: 服务名称
            healthy_only: 是否只统计健康实例

        Returns:
            实例数量
        """
        try:
            if healthy_only:
                instances = await self.get_all_instances(service_name, healthy_only=True)
                return len(instances)
            else:
                return await self.storage.get_service_count(service_name)
        except Exception as e:
            logger.error(f"❌ 获取实例数量失败: {e}")
            return 0

    async def cleanup_expired(self, timeout_seconds: int = 300) -> int:
        """清理过期实例

        Args:
            timeout_seconds: 超时时间（秒）

        Returns:
            清理的数量
        """
        try:
            return await self.storage.cleanup_expired_instances(timeout_seconds)
        except Exception as e:
            logger.error(f"❌ 清理过期实例失败: {e}")
            return 0


# 便捷函数
_discovery_instance: Optional[ServiceDiscovery] = None


def get_discovery() -> ServiceDiscovery:
    """获取服务发现实例（单例模式）"""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = ServiceDiscovery()
    return _discovery_instance
