"""
统一服务注册中心
Unified Service Registry Center
"""
import asyncio
import logging
from typing import Optional, List

from core.service_registry.models import (
    ServiceInstance,
    ServiceRegistration,
    ServiceStatus,
    HealthCheckConfig,
    LoadBalanceStrategy
)
from core.service_registry.storage import ServiceRegistryStorage
from core.service_registry.health_checker import HealthChecker
from core.service_registry.discovery import ServiceDiscovery


logger = logging.getLogger(__name__)


class ServiceRegistryCenter:
    """统一服务注册中心"""

    def __init__(
        self,
        storage: Optional[ServiceRegistryStorage] = None,
        auto_health_check: bool = True,
        health_check_interval: int = 30
    ):
        """初始化服务注册中心

        Args:
            storage: 存储实例
            auto_health_check: 是否自动健康检查
            health_check_interval: 健康检查间隔（秒）
        """
        self.storage = storage or ServiceRegistryStorage()
        self.discovery = ServiceDiscovery(storage=self.storage)
        self.health_checker = HealthChecker(storage=self.storage)

        self.auto_health_check = auto_health_check
        self.health_check_interval = health_check_interval
        self._health_check_task: Optional[asyncio.Task] = None

        logger.info("✅ 服务注册中心初始化完成")

    async def register_service(
        self,
        registration: ServiceRegistration,
        ttl: int = 300
    ) -> bool:
        """注册服务

        Args:
            registration: 服务注册信息
            ttl: 过期时间（秒）

        Returns:
            是否注册成功
        """
        try:
            instance = registration.to_service_instance()
            success = await self.storage.register_instance(instance, ttl)

            if success:
                logger.info(
                    f"✅ 服务已注册: {registration.service_name}/"
                    f"{registration.instance_id} @ {instance.address}"
                )

            return success

        except Exception as e:
            logger.error(f"❌ 注册服务失败: {e}")
            return False

    async def deregister_service(
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
            success = await self.discovery.deregister(service_name, instance_id)

            if success:
                logger.info(f"✅ 服务已注销: {service_name}/{instance_id}")

            return success

        except Exception as e:
            logger.error(f"❌ 注销服务失败: {e}")
            return False

    async def send_heartbeat(
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
        return await self.discovery.heartbeat(service_name, instance_id)

    async def discover_service(
        self,
        service_name: str,
        strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
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
        return await self.discovery.discover(service_name, strategy, healthy_only)

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
        return await self.discovery.get_all_instances(service_name, healthy_only)

    async def get_all_services(self) -> List[str]:
        """获取所有服务名称

        Returns:
            服务名称列表
        """
        return await self.discovery.get_service_names()

    async def get_service_statistics(self, service_name: str) -> dict:
        """获取服务统计信息

        Args:
            service_name: 服务名称

        Returns:
            统计信息字典
        """
        try:
            all_instances = await self.get_all_instances(service_name, healthy_only=False)
            healthy_instances = await self.get_all_instances(service_name, healthy_only=True)

            return {
                "service_name": service_name,
                "total_instances": len(all_instances),
                "healthy_instances": len(healthy_instances),
                "unhealthy_instances": len(all_instances) - len(healthy_instances),
                "instances": [
                    {
                        "instance_id": inst.instance_id,
                        "address": inst.address,
                        "status": inst.status.value,
                        "last_heartbeat": inst.last_heartbeat.isoformat()
                    }
                    for inst in all_instances
                ]
            }

        except Exception as e:
            logger.error(f"❌ 获取服务统计失败: {e}")
            return {}

    async def get_registry_statistics(self) -> dict:
        """获取注册中心统计信息

        Returns:
            统计信息字典
        """
        try:
            services = await self.get_all_services()

            total_instances = 0
            healthy_instances = 0

            service_stats = {}

            for service_name in services:
                stats = await self.get_service_statistics(service_name)
                service_stats[service_name] = stats
                total_instances += stats["total_instances"]
                healthy_instances += stats["healthy_instances"]

            return {
                "total_services": len(services),
                "total_instances": total_instances,
                "healthy_instances": healthy_instances,
                "unhealthy_instances": total_instances - healthy_instances,
                "services": service_stats
            }

        except Exception as e:
            logger.error(f"❌ 获取注册中心统计失败: {e}")
            return {}

    async def check_health(self, service_name: Optional[str] = None) -> dict:
        """执行健康检查

        Args:
            service_name: 服务名称（可选，不指定则检查所有服务）

        Returns:
            检查结果字典
        """
        try:
            results = await self.health_checker.check_all_instances(service_name)

            total = len(results)
            healthy = sum(1 for r in results.values() if r.healthy)
            unhealthy = total - healthy

            return {
                "total_checked": total,
                "healthy": healthy,
                "unhealthy": unhealthy,
                "details": {
                    instance_key: {
                        "healthy": result.healthy,
                        "message": result.message,
                        "response_time_ms": result.response_time_ms
                    }
                    for instance_key, result in results.items()
                }
            }

        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return {}

    async def cleanup_expired(self, timeout_seconds: int = 300) -> int:
        """清理过期实例

        Args:
            timeout_seconds: 超时时间（秒）

        Returns:
            清理的数量
        """
        return await self.discovery.cleanup_expired(timeout_seconds)

    def start_health_check(self):
        """启动后台健康检查"""
        if self._health_check_task is not None:
            logger.warning("⚠️ 健康检查任务已在运行")
            return

        async def health_check_loop():
            logger.info("🔄 启动后台健康检查")
            while True:
                try:
                    await self.check_health()
                    await asyncio.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"❌ 后台健康检查出错: {e}")
                    await asyncio.sleep(self.health_check_interval)

        self._health_check_task = asyncio.create_task(health_check_loop())
        logger.info(f"✅ 后台健康检查已启动（间隔: {self.health_check_interval}秒）")

    def stop_health_check(self):
        """停止后台健康检查"""
        if self._health_check_task is not None:
            self._health_check_task.cancel()
            self._health_check_task = None
            logger.info("✅ 后台健康检查已停止")

    async def close(self):
        """关闭注册中心"""
        self.stop_health_check()
        logger.info("✅ 服务注册中心已关闭")


# 便捷函数
_registry_instance: Optional[ServiceRegistryCenter] = None


def get_registry() -> ServiceRegistryCenter:
    """获取注册中心实例（单例模式）"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistryCenter()
    return _registry_instance
