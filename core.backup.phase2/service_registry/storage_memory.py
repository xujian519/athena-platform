"""
服务注册内存存储（用于演示和测试）
Service Registry In-Memory Storage (for Demo and Testing)
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from core.service_registry.models import ServiceInstance, ServiceStatus


logger = logging.getLogger(__name__)


class InMemoryServiceRegistryStorage:
    """内存服务注册存储（用于演示）"""

    def __init__(self):
        """初始化内存存储"""
        self.instances: Dict[str, Dict[str, ServiceInstance]] = {}
        self.services: set = set()
        self._lock = asyncio.Lock()

        logger.info("✅ 内存存储初始化完成")

    async def register_instance(self, instance: ServiceInstance, ttl: int = 300) -> bool:
        """注册服务实例"""
        async with self._lock:
            try:
                service_name = instance.service_name
                instance_id = instance.instance_id

                # 创建服务存储
                if service_name not in self.instances:
                    self.instances[service_name] = {}
                    self.services.add(service_name)

                # 存储实例
                self.instances[service_name][instance_id] = instance

                logger.info(f"✅ 服务实例已注册: {service_name}/{instance_id}")
                return True

            except Exception as e:
                logger.error(f"❌ 注册服务实例失败: {e}")
                return False

    async def deregister_instance(self, service_name: str, instance_id: str) -> bool:
        """注销服务实例"""
        async with self._lock:
            try:
                if service_name in self.instances and instance_id in self.instances[service_name]:
                    del self.instances[service_name][instance_id]

                    # 如果服务没有实例了，从索引中移除
                    if not self.instances[service_name]:
                        del self.instances[service_name]
                        self.services.discard(service_name)

                    logger.info(f"✅ 服务实例已注销: {service_name}/{instance_id}")
                    return True

                return False

            except Exception as e:
                logger.error(f"❌ 注销服务实例失败: {e}")
                return False

    async def get_instance(
        self,
        service_name: str,
        instance_id: str
    ) -> Optional[ServiceInstance]:
        """获取服务实例"""
        if service_name in self.instances and instance_id in self.instances[service_name]:
            return self.instances[service_name][instance_id]
        return None

    async def get_all_instances(
        self,
        service_name: str,
        status: Optional[ServiceStatus] = None
    ) -> List[ServiceInstance]:
        """获取所有服务实例"""
        if service_name not in self.instances:
            return []

        instances = list(self.instances[service_name].values())

        # 状态过滤
        if status is not None:
            instances = [i for i in instances if i.status == status]

        return instances

    async def update_instance(self, instance: ServiceInstance) -> bool:
        """更新服务实例"""
        async with self._lock:
            try:
                service_name = instance.service_name
                instance_id = instance.instance_id

                if service_name in self.instances and instance_id in self.instances[service_name]:
                    self.instances[service_name][instance_id] = instance
                    logger.debug(f"✅ 服务实例已更新: {service_name}/{instance_id}")
                    return True

                return False

            except Exception as e:
                logger.error(f"❌ 更新服务实例失败: {e}")
                return False

    async def heartbeat(self, service_name: str, instance_id: str, ttl: int = 300) -> bool:
        """更新心跳"""
        instance = await self.get_instance(service_name, instance_id)
        if not instance:
            logger.warning(f"⚠️ 实例不存在: {service_name}/{instance_id}")
            return False

        # 更新心跳时间
        instance.touch()

        # 更新存储
        return await self.update_instance(instance)

    async def get_all_services(self) -> List[str]:
        """获取所有服务名称"""
        return list(self.services)

    async def get_service_count(self, service_name: str) -> int:
        """获取服务实例数量"""
        if service_name in self.instances:
            return len(self.instances[service_name])
        return 0

    async def cleanup_expired_instances(self, timeout_seconds: int = 300) -> int:
        """清理过期实例"""
        cleaned = 0

        async with self._lock:
            for service_name in list(self.instances.keys()):
                instances = await self.get_all_instances(service_name)
                for instance in instances:
                    if instance.is_expired(timeout_seconds):
                        await self.deregister_instance(service_name, instance.instance_id)
                        cleaned += 1
                        logger.info(f"✅ 清理过期实例: {service_name}/{instance.instance_id}")

        return cleaned
