"""
服务注册存储层
Service Registry Storage Layer
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from core.service_registry.models import ServiceInstance, ServiceStatus


logger = logging.getLogger(__name__)


class ServiceRegistryStorage:
    """服务注册存储（基于Redis）"""

    # Redis键前缀
    INSTANCE_PREFIX = "service:instances:"
    INDEX_KEY = "service:index"
    HEALTH_KEY_PREFIX = "service:health:"

    def __init__(self, redis_client=None):
        """初始化存储

        Args:
            redis_client: Redis客户端实例（可选）
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis模块未安装，请安装: pip install redis")

        self.redis = redis_client
        if self.redis is None:
            # 默认连接配置
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5
            )

        # 测试连接
        try:
            self.redis.ping()
            logger.info("✅ 服务注册存储连接成功")
        except Exception as e:
            logger.error(f"❌ 服务注册存储连接失败: {e}")
            raise

    def _get_instance_key(self, service_name: str) -> str:
        """获取服务实例存储键"""
        return f"{self.INSTANCE_PREFIX}{service_name}"

    def _get_health_key(self, service_name: str, instance_id: str) -> str:
        """获取健康检查存储键"""
        return f"{self.HEALTH_KEY_PREFIX}{service_name}:{instance_id}"

    async def register_instance(self, instance: ServiceInstance, ttl: int = 300) -> bool:
        """注册服务实例

        Args:
            instance: 服务实例
            ttl: 过期时间（秒），默认5分钟

        Returns:
            是否注册成功
        """
        try:
            key = self._get_instance_key(instance.service_name)

            # 存储实例数据
            self.redis.hset(
                key,
                instance.instance_id,
                instance.to_json()
            )

            # 设置过期时间
            self.redis.expire(key, ttl)

            # 添加到服务索引
            self.redis.sadd(self.INDEX_KEY, instance.service_name)

            # 存储健康状态
            health_key = self._get_health_key(instance.service_name, instance.instance_id)
            self.redis.setex(
                health_key,
                ttl,
                instance.status.value
            )

            logger.info(f"✅ 服务实例已注册: {instance.service_name}/{instance.instance_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 注册服务实例失败: {e}")
            return False

    async def deregister_instance(self, service_name: str, instance_id: str) -> bool:
        """注销服务实例

        Args:
            service_name: 服务名称
            instance_id: 实例ID

        Returns:
            是否注销成功
        """
        try:
            key = self._get_instance_key(service_name)

            # 删除实例
            result = self.redis.hdel(key, instance_id)

            # 删除健康状态
            health_key = self._get_health_key(service_name, instance_id)
            self.redis.delete(health_key)

            # 如果服务没有实例了，从索引中移除
            if not self.redis.hexists(key, instance_id):
                # 检查是否还有其他实例
                if self.redis.hlen(key) == 0:
                    self.redis.srem(self.INDEX_KEY, service_name)

            logger.info(f"✅ 服务实例已注销: {service_name}/{instance_id}")
            return result > 0

        except Exception as e:
            logger.error(f"❌ 注销服务实例失败: {e}")
            return False

    async def get_instance(
        self,
        service_name: str,
        instance_id: str
    ) -> Optional[ServiceInstance]:
        """获取服务实例

        Args:
            service_name: 服务名称
            instance_id: 实例ID

        Returns:
            服务实例或None
        """
        try:
            key = self._get_instance_key(service_name)
            data = self.redis.hget(key, instance_id)

            if not data:
                return None

            return ServiceInstance.from_json(data)

        except Exception as e:
            logger.error(f"❌ 获取服务实例失败: {e}")
            return None

    async def get_all_instances(
        self,
        service_name: str,
        status: Optional[ServiceStatus] = None
    ) -> List[ServiceInstance]:
        """获取服务的所有实例

        Args:
            service_name: 服务名称
            status: 过滤状态（可选）

        Returns:
            服务实例列表
        """
        try:
            key = self._get_instance_key(service_name)
            instances_data = self.redis.hgetall(key)

            instances = []
            for instance_id, data in instances_data.items():
                instance = ServiceInstance.from_json(data)

                # 状态过滤
                if status is None or instance.status == status:
                    instances.append(instance)

            return instances

        except Exception as e:
            logger.error(f"❌ 获取所有实例失败: {e}")
            return []

    async def update_instance(self, instance: ServiceInstance) -> bool:
        """更新服务实例

        Args:
            instance: 服务实例

        Returns:
            是否更新成功
        """
        try:
            key = self._get_instance_key(instance.service_name)

            # 更新实例数据
            self.redis.hset(
                key,
                instance.instance_id,
                instance.to_json()
            )

            # 更新健康状态
            health_key = self._get_health_key(instance.service_name, instance.instance_id)
            self.redis.setex(
                health_key,
                300,  # 5分钟TTL
                instance.status.value
            )

            logger.debug(f"✅ 服务实例已更新: {instance.service_name}/{instance.instance_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 更新服务实例失败: {e}")
            return False

    async def heartbeat(self, service_name: str, instance_id: str, ttl: int = 300) -> bool:
        """更新心跳

        Args:
            service_name: 服务名称
            instance_id: 实例ID
            ttl: 过期时间（秒）

        Returns:
            是否更新成功
        """
        try:
            # 获取实例
            instance = await self.get_instance(service_name, instance_id)
            if not instance:
                logger.warning(f"⚠️ 实例不存在: {service_name}/{instance_id}")
                return False

            # 更新心跳时间
            instance.touch()

            # 更新存储
            return await self.update_instance(instance)

        except Exception as e:
            logger.error(f"❌ 更新心跳失败: {e}")
            return False

    async def get_all_services(self) -> List[str]:
        """获取所有服务名称

        Returns:
            服务名称列表
        """
        try:
            return list(self.redis.smembers(self.INDEX_KEY))
        except Exception as e:
            logger.error(f"❌ 获取服务列表失败: {e}")
            return []

    async def get_service_count(self, service_name: str) -> int:
        """获取服务实例数量

        Args:
            service_name: 服务名称

        Returns:
            实例数量
        """
        try:
            key = self._get_instance_key(service_name)
            return self.redis.hlen(key)
        except Exception as e:
            logger.error(f"❌ 获取实例数量失败: {e}")
            return 0

    async def cleanup_expired_instances(self, timeout_seconds: int = 300) -> int:
        """清理过期实例

        Args:
            timeout_seconds: 超时时间（秒）

        Returns:
            清理的实例数量
        """
        try:
            cleaned = 0
            services = await self.get_all_services()

            for service_name in services:
                instances = await self.get_all_instances(service_name)
                for instance in instances:
                    if instance.is_expired(timeout_seconds):
                        await self.deregister_instance(service_name, instance.instance_id)
                        cleaned += 1
                        logger.info(f"✅ 清理过期实例: {service_name}/{instance.instance_id}")

            return cleaned

        except Exception as e:
            logger.error(f"❌ 清理过期实例失败: {e}")
            return 0


# 便捷函数
_storage_instance: Optional[ServiceRegistryStorage] = None


def get_storage() -> ServiceRegistryStorage:
    """获取存储实例（单例模式）"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = ServiceRegistryStorage()
    return _storage_instance
