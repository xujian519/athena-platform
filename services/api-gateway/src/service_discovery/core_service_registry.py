"""
Athena Service Discovery System - Core Service Registry
服务发现系统核心服务注册中心

Author: Athena AI Team
Version: 2.0.0
"""

import asyncio
import json
import logging
import secrets
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import aioredis
from aiohttp import web

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """服务协议类型"""

    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"
    GRAPHQL = "graphql"
    TCP = "tcp"


class HealthStatus(Enum):
    """健康状态"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class ServiceState(Enum):
    """服务状态"""

    REGISTERING = "registering"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEREGISTERING = "deregistering"


@dataclass
class ServiceInstance:
    """服务实例数据模型"""

    # 基础信息
    service_id: str  # 服务唯一标识
    service_name: str  # 服务名称
    version: str  # 服务版本
    namespace: str  # 命名空间

    # 网络信息
    host: str  # 服务主机
    port: int  # 服务端口
    protocol: ProtocolType  # 协议类型
    endpoints: list[str] = field(default_factory=list)  # 服务端点列表

    # 健康信息
    health_status: HealthStatus = HealthStatus.UNKNOWN
    last_heartbeat: datetime | None = None
    health_check_url: str | None = None

    # 负载均衡信息
    weight: int = 100  # 权重
    tags: list[str] = field(default_factory=list)  # 标签
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    # 状态信息
    state: ServiceState = ServiceState.REGISTERING

    # 时间戳
    registration_time: datetime = field(default_factory=datetime.now)
    updated_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data["protocol"] = self.protocol.value
        data["health_status"] = self.health_status.value
        data["state"] = self.state.value
        if self.last_heartbeat:
            data["last_heartbeat"] = self.last_heartbeat.isoformat()
        data["registration_time"] = self.registration_time.isoformat()
        data["updated_time"] = self.updated_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceInstance":
        """从字典创建实例"""
        if "protocol" in data and isinstance(data["protocol"], str):
            data["protocol"] = ProtocolType(data["protocol"])
        if "health_status" in data and isinstance(data["health_status"], str):
            data["health_status"] = HealthStatus(data["health_status"])
        if "state" in data and isinstance(data["state"], str):
            data["state"] = ServiceState(data["state"])
        if "last_heartbeat" in data and isinstance(data["last_heartbeat"], str):
            data["last_heartbeat"] = datetime.fromisoformat(data["last_heartbeat"])
        if "registration_time" in data and isinstance(data["registration_time"], str):
            data["registration_time"] = datetime.fromisoformat(data["registration_time"])
        if "updated_time" in data and isinstance(data["updated_time"], str):
            data["updated_time"] = datetime.fromisoformat(data["updated_time"])
        return cls(**data)


@dataclass
class HealthCheckConfig:
    """健康检查配置"""

    enabled: bool = True
    interval: int = 30  # 检查间隔(秒)
    timeout: int = 5  # 超时时间(秒)
    retries: int = 3  # 重试次数

    # 检查类型配置
    http_path: str = "/health"
    expected_codes: list[int] = field(default_factory=lambda: [200])
    headers: dict[str, str] = field(default_factory=dict)

    # 故障处理配置
    failure_threshold: int = 3  # 连续失败阈值
    success_threshold: int = 2  # 连续成功阈值
    deregister_after: int = 300  # 失效后注销时间(秒)


@dataclass
class ServiceConfig:
    """服务配置"""

    service_name: str
    version: str = "1.0.0"
    namespace: str = "default"
    config_data: dict[str, Any] = field(default_factory=dict)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    load_balance_algorithm: str = "round_robin"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class StorageBackend:
    """存储后端基类"""

    async def initialize(self):
        """初始化存储后端"""
        pass

    async def close(self):
        """关闭存储后端"""
        pass

    async def save_service_instance(self, instance: ServiceInstance) -> bool:
        """保存服务实例"""
        raise NotImplementedError

    async def get_service_instance(self, service_id: str) -> ServiceInstance | None:
        """获取服务实例"""
        raise NotImplementedError

    async def get_service_instances(
        self, service_name: str, namespace: str = "default"
    ) -> list[ServiceInstance]:
        """获取服务实例列表"""
        raise NotImplementedError

    async def delete_service_instance(self, service_id: str) -> bool:
        """删除服务实例"""
        raise NotImplementedError

    async def save_service_config(self, config: ServiceConfig) -> bool:
        """保存服务配置"""
        raise NotImplementedError

    async def get_service_config(
        self, service_name: str, namespace: str = "default"
    ) -> ServiceConfig | None:
        """获取服务配置"""
        raise NotImplementedError


class RedisStorageBackend(StorageBackend):
    """Redis存储后端"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None

    async def initialize(self):
        """初始化Redis连接"""
        self.redis = await aioredis.from_url(self.redis_url)
        logger.info(f"Connected to Redis: {self.redis_url}")

    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()

    async def save_service_instance(self, instance: ServiceInstance) -> bool:
        """保存服务实例到Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        key = f"service_instance:{instance.service_id}"
        data = json.dumps(instance.to_dict())

        pipe = self.redis.pipeline()
        pipe.set(key, data, ex=3600)  # 1小时过期
        pipe.sadd(
            f"service_instances:{instance.service_name}:{instance.namespace}", instance.service_id
        )
        await pipe.execute()

        return True

    async def get_service_instance(self, service_id: str) -> ServiceInstance | None:
        """从Redis获取服务实例"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        key = f"service_instance:{service_id}"
        data = await self.redis.get(key)

        if not data:
            return None

        return ServiceInstance.from_dict(json.loads(data))

    async def get_service_instances(
        self, service_name: str, namespace: str = "default"
    ) -> list[ServiceInstance]:
        """从Redis获取服务实例列表"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        set_key = f"service_instances:{service_name}:{namespace}"
        service_ids = await self.redis.smembers(set_key)

        instances = []
        for service_id in service_ids:
            instance = await self.get_service_instance(service_id)
            if instance:
                instances.append(instance)

        return instances

    async def delete_service_instance(self, service_id: str) -> bool:
        """从Redis删除服务实例"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        # 先获取实例信息
        instance = await self.get_service_instance(service_id)
        if not instance:
            return False

        pipe = self.redis.pipeline()
        pipe.delete(f"service_instance:{service_id}")
        pipe.srem(f"service_instances:{instance.service_name}:{instance.namespace}", service_id)
        await pipe.execute()

        return True

    async def save_service_config(self, config: ServiceConfig) -> bool:
        """保存服务配置到Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        key = f"service_config:{config.service_name}:{config.namespace}"
        data = json.dumps(
            {
                "service_name": config.service_name,
                "version": config.version,
                "namespace": config.namespace,
                "config_data": config.config_data,
                "health_check": asdict(config.health_check),
                "load_balance_algorithm": config.load_balance_algorithm,
                "metadata": config.metadata,
                "created_at": config.created_at.isoformat(),
                "updated_at": config.updated_at.isoformat(),
            }
        )

        await self.redis.set(key, data)
        return True

    async def get_service_config(
        self, service_name: str, namespace: str = "default"
    ) -> ServiceConfig | None:
        """从Redis获取服务配置"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        key = f"service_config:{service_name}:{namespace}"
        data = await self.redis.get(key)

        if not data:
            return None

        config_dict = json.loads(data)
        health_check = HealthCheckConfig(**config_dict.get("health_check", {}))

        return ServiceConfig(
            service_name=config_dict["service_name"],
            version=config_dict["version"],
            namespace=config_dict["namespace"],
            config_data=config_dict.get("config_data", {}),
            health_check=health_check,
            load_balance_algorithm=config_dict.get("load_balance_algorithm", "round_robin"),
            metadata=config_dict.get("metadata", {}),
            created_at=datetime.fromisoformat(config_dict["created_at"]),
            updated_at=datetime.fromisoformat(config_dict["updated_at"]),
        )


class ServiceRegistry:
    """服务注册中心"""

    def __init__(self, storage_backend: StorageBackend):
        self.storage = storage_backend
        self.registered_services: dict[str, ServiceInstance] = {}  # 内存缓存
        self.service_callbacks: dict[str, list[Callable]] = {}  # 服务变更回调
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化服务注册中心"""
        await self.storage.initialize()
        # 从存储中加载现有服务
        await self._load_existing_services()
        logger.info("Service Registry initialized successfully")

    async def close(self):
        """关闭服务注册中心"""
        await self.storage.close()
        logger.info("Service Registry closed")

    async def register_service(self, instance: ServiceInstance) -> bool:
        """注册服务"""
        async with self._lock:
            try:
                # 设置服务状态
                instance.state = ServiceState.ACTIVE
                instance.registration_time = datetime.now()
                instance.updated_time = datetime.now()

                # 保存到存储
                success = await self.storage.save_service_instance(instance)
                if not success:
                    return False

                # 更新内存缓存
                self.registered_services[instance.service_id] = instance

                # 触发回调
                await self._trigger_service_callbacks(instance.service_name, "register", instance)

                logger.info(f"Service registered: {instance.service_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to register service {instance.service_id}: {e}")
                return False

    async def deregister_service(self, service_id: str) -> bool:
        """注销服务"""
        async with self._lock:
            try:
                instance = self.registered_services.get(service_id)
                if not instance:
                    return False

                # 设置服务状态
                instance.state = ServiceState.DEREGISTERING

                # 从存储中删除
                success = await self.storage.delete_service_instance(service_id)
                if not success:
                    return False

                # 从内存缓存中删除
                del self.registered_services[service_id]

                # 触发回调
                await self._trigger_service_callbacks(instance.service_name, "deregister", instance)

                logger.info(f"Service deregistered: {service_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to deregister service {service_id}: {e}")
                return False

    async def discover_services(
        self, service_name: str, namespace: str = "default", healthy_only: bool = True
    ) -> list[ServiceInstance]:
        """发现服务"""
        try:
            # 先从缓存中获取
            cached_instances = [
                instance
                for instance in self.registered_services.values()
                if instance.service_name == service_name and instance.namespace == namespace
            ]

            if not cached_instances:
                # 从存储中获取
                cached_instances = await self.storage.get_service_instances(service_name, namespace)
                # 更新缓存
                for instance in cached_instances:
                    self.registered_services[instance.service_id] = instance

            # 过滤健康状态
            if healthy_only:
                cached_instances = [
                    instance
                    for instance in cached_instances
                    if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
                ]

            return cached_instances

        except Exception as e:
            logger.error(f"Failed to discover services {service_name}: {e}")
            return []

    async def update_service_instance(self, service_id: str, updates: dict) -> bool:
        """更新服务实例"""
        async with self._lock:
            try:
                instance = self.registered_services.get(service_id)
                if not instance:
                    return False

                # 更新字段
                for key, value in updates.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)

                instance.updated_time = datetime.now()

                # 保存到存储
                success = await self.storage.save_service_instance(instance)
                if not success:
                    return False

                # 触发回调
                await self._trigger_service_callbacks(instance.service_name, "update", instance)

                return True

            except Exception as e:
                logger.error(f"Failed to update service {service_id}: {e}")
                return False

    async def get_service_instance(self, service_id: str) -> ServiceInstance | None:
        """获取单个服务实例"""
        # 先从缓存获取
        if service_id in self.registered_services:
            return self.registered_services[service_id]

        # 从存储获取
        instance = await self.storage.get_service_instance(service_id)
        if instance:
            self.registered_services[service_id] = instance

        return instance

    def add_service_callback(self, service_name: str, callback: Callable):
        """添加服务变更回调"""
        if service_name not in self.service_callbacks:
            self.service_callbacks[service_name] = []
        self.service_callbacks[service_name].append(callback)

    def remove_service_callback(self, service_name: str, callback: Callable):
        """移除服务变更回调"""
        if service_name in self.service_callbacks:
            try:
                self.service_callbacks[service_name].remove(callback)
            except ValueError:
                pass

    async def _load_existing_services(self):
        """加载现有服务"""
        # 这里需要从存储中加载所有服务实例
        # 由于Redis没有直接获取所有键的API，我们需要使用模式匹配
        pass

    async def _trigger_service_callbacks(
        self, service_name: str, action: str, instance: ServiceInstance
    ):
        """触发服务变更回调"""
        callbacks = self.service_callbacks.get(service_name, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(action, instance)
                else:
                    callback(action, instance)
            except Exception as e:
                logger.error(f"Service callback failed: {e}")


class ServiceDiscoveryAPI:
    """服务发现API"""

    def __init__(self, registry: ServiceRegistry, host: str = "0.0.0.0", port: int = 8080):
        self.registry = registry
        self.host = host
        self.port = port
        self.app = None
        self.runner = None
        self.site = None

    async def start(self):
        """启动API服务"""
        from aiohttp import web

        self.app = web.Application()
        self.setup_routes()

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        logger.info(f"Service Discovery API started on {self.host}:{self.port}")

    async def stop(self):
        """停止API服务"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Service Discovery API stopped")

    def setup_routes(self):
        """设置路由"""
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_post("/services/register", self.register_service)
        self.app.router.add_delete("/services/{service_id}", self.deregister_service)
        self.app.router.add_get("/services/{service_name}/discover", self.discover_services)
        self.app.router.add_put("/services/{service_id}", self.update_service)
        self.app.router.add_get("/services/{service_id}", self.get_service)
        self.app.router.add_get("/services", self.list_services)

    async def health_check(self, request):
        """健康检查"""
        return web.json_response(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service_count": len(self.registry.registered_services),
            }
        )

    async def register_service(self, request):
        """注册服务"""
        try:
            data = await request.json()

            # 生成服务ID
            service_id = data.get("service_id") or secrets.token_hex(16)

            # 创建服务实例
            instance = ServiceInstance(
                service_id=service_id,
                service_name=data["service_name"],
                version=data.get("version", "1.0.0"),
                namespace=data.get("namespace", "default"),
                host=data["host"],
                port=data["port"],
                protocol=ProtocolType(data.get("protocol", "http")),
                endpoints=data.get("endpoints", []),
                weight=data.get("weight", 100),
                tags=data.get("tags", []),
                metadata=data.get("metadata", {}),
                health_check_url=data.get("health_check_url"),
            )

            success = await self.registry.register_service(instance)

            if success:
                return web.json_response(
                    {
                        "success": True,
                        "service_id": service_id,
                        "message": "Service registered successfully",
                    }
                )
            else:
                return web.json_response(
                    {"success": False, "message": "Failed to register service"}, status=500
                )

        except Exception as e:
            return web.json_response({"success": False, "message": str(e)}, status=400)

    async def deregister_service(self, request):
        """注销服务"""
        service_id = request.match_info["service_id"]

        success = await self.registry.deregister_service(service_id)

        if success:
            return web.json_response(
                {"success": True, "message": "Service deregistered successfully"}
            )
        else:
            return web.json_response(
                {"success": False, "message": "Service not found or deregistration failed"},
                status=404,
            )

    async def discover_services(self, request):
        """发现服务"""
        service_name = request.match_info["service_name"]
        namespace = request.query.get("namespace", "default")
        healthy_only = request.query.get("healthy_only", "true").lower() == "true"

        instances = await self.registry.discover_services(service_name, namespace, healthy_only)

        return web.json_response(
            {
                "service_name": service_name,
                "namespace": namespace,
                "instances": [instance.to_dict() for instance in instances],
                "count": len(instances),
            }
        )

    async def update_service(self, request):
        """更新服务"""
        service_id = request.match_info["service_id"]

        try:
            updates = await request.json()
            success = await self.registry.update_service_instance(service_id, updates)

            if success:
                return web.json_response(
                    {"success": True, "message": "Service updated successfully"}
                )
            else:
                return web.json_response(
                    {"success": False, "message": "Service not found or update failed"}, status=404
                )

        except Exception as e:
            return web.json_response({"success": False, "message": str(e)}, status=400)

    async def get_service(self, request):
        """获取服务实例"""
        service_id = request.match_info["service_id"]

        instance = await self.registry.get_service_instance(service_id)

        if instance:
            return web.json_response(instance.to_dict())
        else:
            return web.json_response({"error": "Service not found"}, status=404)

    async def list_services(self, request):
        """列出所有服务"""
        namespace = request.query.get("namespace", "default")

        # 按服务名分组
        services = {}
        for instance in self.registry.registered_services.values():
            if instance.namespace == namespace:
                service_key = f"{instance.service_name}:{instance.namespace}"
                if service_key not in services:
                    services[service_key] = []
                services[service_key].append(instance.to_dict())

        return web.json_response(
            {
                "services": services,
                "total_services": len(services),
                "total_instances": len(self.registry.registered_services),
            }
        )


# 工厂函数
async def create_service_discovery(config: dict) -> ServiceRegistry:
    """创建服务发现实例"""
    # 根据配置创建存储后端
    storage_type = config.get("storage", {}).get("type", "redis")

    if storage_type == "redis":
        redis_url = config["storage"]["redis_url"]
        storage = RedisStorageBackend(redis_url)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")

    # 创建服务注册中心
    registry = ServiceRegistry(storage)
    await registry.initialize()

    return registry


# 使用示例
async def main():
    """主函数示例"""
    # 配置
    config = {
        "storage": {"type": "redis", "redis_url": "redis://localhost:6379"},
        "api": {"host": "0.0.0.0", "port": 8080},
    }

    # 创建服务发现
    registry = await create_service_discovery(config)

    # 创建API服务
    api = ServiceDiscoveryAPI(registry, **config["api"])
    await api.start()

    try:
        # 保持服务运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await api.stop()
        await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
