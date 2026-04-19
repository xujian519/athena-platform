"""
Athena Service Discovery - Plugin Integration
服务发现系统与Athena插件系统集成

Author: Athena AI Team
Version: 2.0.0
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime

from .core_service_registry import (
    HealthCheckConfig,
    ProtocolType,
    ServiceInstance,
    ServiceRegistry,
    create_service_discovery,
)
from .health_check import HealthCheckManager, HealthStatus, create_health_check_manager
from .load_balancing import (
    LoadBalancingManager,
    RequestContext,
    ServiceMetrics,
    create_load_balancing_manager,
)

logger = logging.getLogger(__name__)


class ServiceDiscoveryPlugin(ABC):
    """服务发现插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass

    @abstractmethod
    async def initialize(self, config: dict) -> bool:
        """初始化插件"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """关闭插件"""
        pass

    @abstractmethod
    async def on_service_register(self, instance: ServiceInstance) -> None:
        """服务注册回调"""
        pass

    @abstractmethod
    async def on_service_deregister(self, instance: ServiceInstance) -> None:
        """服务注销回调"""
        pass

    @abstractmethod
    async def on_health_change(
        self, service_id: str, old_status: HealthStatus, new_status: HealthStatus
    ) -> None:
        """健康状态变更回调"""
        pass


class MCPServiceDiscoveryPlugin(ServiceDiscoveryPlugin):
    """MCP服务发现插件"""

    def __init__(self):
        self.name = "mcp-service-discovery"
        self.version = "1.0.0"
        self.registry: ServiceRegistry | None = None
        self.health_manager: HealthCheckManager | None = None
        self.config = {}
        self.mcp_services = {}

    async def initialize(self, config: dict) -> bool:
        """初始化MCP服务发现插件"""
        try:
            self.config = config

            # 创建服务注册中心和健康检查管理器
            registry_config = config.get("registry", {})
            self.registry = await create_service_discovery(registry_config)
            self.health_manager = create_health_check_manager(self.registry)

            # 启动健康检查管理器
            await self.health_manager.start()

            # 加载MCP服务配置
            await self._load_mcp_services()

            # 注册回调
            self.registry.add_service_callback(self._on_service_change)
            self.health_manager.add_status_callback(self._on_health_status_change)

            logger.info("MCP服务发现插件初始化完成")
            return True

        except Exception as e:
            logger.error(f"MCP服务发现插件初始化失败: {e}")
            return False

    async def shutdown(self) -> None:
        """关闭插件"""
        try:
            if self.health_manager:
                await self.health_manager.stop()
            if self.registry:
                await self.registry.close()
            logger.info("MCP服务发现插件已关闭")
        except Exception as e:
            logger.error(f"关闭MCP服务发现插件失败: {e}")

    async def _load_mcp_services(self):
        """加载MCP服务配置"""
        config_path = self.config.get("mcp_config_path", "config/athena_mcp_config.json")

        try:
            with open(config_path, encoding="utf-8") as f:
                mcp_config = json.load(f)

            for service_name, service_config in mcp_config.get("mcp_services", {}).items():
                if service_config.get("status") == "active":
                    await self._register_mcp_service(service_name, service_config)

            logger.info(f"已加载 {len(self.mcp_services)} 个MCP服务")

        except FileNotFoundError:
            logger.warning(f"MCP配置文件未找到: {config_path}")
        except Exception as e:
            logger.error(f"加载MCP配置失败: {e}")

    async def _register_mcp_service(self, service_name: str, service_config: dict):
        """注册MCP服务"""
        try:
            # 获取服务启动信息
            startup_config = service_config.get("startup", {})

            # 创建服务实例
            instance = ServiceInstance(
                service_id=f"mcp-{service_name}",
                service_name=service_name,
                namespace="mcp",
                host="localhost",
                port=startup_config.get("port", 0),
                protocol=ProtocolType.TCP,  # MCP通常使用stdio协议
                endpoints=[f"mcp://{service_name}"],
                metadata={
                    "type": "mcp",
                    "description": service_config.get("description", ""),
                    "capabilities": service_config.get("tools", {}).keys(),
                    "config": service_config,
                },
            )

            # 注册服务
            success = await self.registry.register_service(instance)
            if success:
                self.mcp_services[service_name] = {"instance": instance, "config": service_config}

                # 配置健康检查
                await self._setup_health_check(service_name, instance, service_config)

                logger.info(f"MCP服务已注册: {service_name}")
            else:
                logger.error(f"MCP服务注册失败: {service_name}")

        except Exception as e:
            logger.error(f"注册MCP服务失败 {service_name}: {e}")

    async def _setup_health_check(
        self, service_name: str, instance: ServiceInstance, service_config: dict
    ):
        """设置健康检查"""
        try:
            # 从监控配置中获取健康检查配置
            monitoring_config = service_config.get("monitoring", {})
            health_config = HealthCheckConfig(
                enabled=monitoring_config.get("health_check_enabled", True),
                interval=monitoring_config.get("health_check_interval", 30),
                timeout=monitoring_config.get("health_check_timeout", 10),
                failure_threshold=monitoring_config.get("failure_threshold", 3),
            )

            # 启动健康检查
            if self.health_manager and health_config.enabled:
                await self.health_manager.start_health_check(instance, health_config)
                logger.info(f"已启动健康检查: {service_name}")

        except Exception as e:
            logger.error(f"设置健康检查失败 {service_name}: {e}")

    async def _on_service_change(self, action: str, instance: ServiceInstance):
        """服务变更回调"""
        try:
            if action == "register":
                await self.on_service_register(instance)
            elif action == "deregister":
                await self.on_service_deregister(instance)
        except Exception as e:
            logger.error(f"服务变更回调失败: {e}")

    async def _on_health_status_change(
        self, service_id: str, old_status: HealthStatus, new_status: HealthStatus
    ):
        """健康状态变更回调"""
        try:
            await self.on_health_change(service_id, old_status, new_status)
        except Exception as e:
            logger.error(f"健康状态变更回调失败: {e}")

    async def on_service_register(self, instance: ServiceInstance) -> None:
        """服务注册回调"""
        logger.info(f"Plugin: Service registered - {instance.service_id}")

    async def on_service_deregister(self, instance: ServiceInstance) -> None:
        """服务注销回调"""
        logger.info(f"Plugin: Service deregistered - {instance.service_id}")

    async def on_health_change(
        self, service_id: str, old_status: HealthStatus, new_status: HealthStatus
    ) -> None:
        """健康状态变更回调"""
        logger.info(
            f"Plugin: Health status changed - {service_id}: {old_status.value} -> {new_status.value}"
        )


class KubernetesServiceDiscoveryPlugin(ServiceDiscoveryPlugin):
    """Kubernetes服务发现插件"""

    def __init__(self):
        self.name = "kubernetes-service-discovery"
        self.version = "1.0.0"
        self.registry: ServiceRegistry | None = None
        self.health_manager: HealthCheckManager | None = None
        self.config = {}
        self.k8s_client = None

    async def initialize(self, config: dict) -> bool:
        """初始化Kubernetes服务发现插件"""
        try:
            self.config = config

            # 创建服务注册中心和健康检查管理器
            registry_config = config.get("registry", {})
            self.registry = await create_service_discovery(registry_config)
            self.health_manager = create_health_check_manager(self.registry)

            # 启动健康检查管理器
            await self.health_manager.start()

            # 初始化Kubernetes客户端
            await self._initialize_k8s_client()

            # 开始监听Kubernetes服务
            await self._start_k8s_service_watch()

            # 注册回调
            self.registry.add_service_callback(self._on_service_change)
            self.health_manager.add_status_callback(self._on_health_status_change)

            logger.info("Kubernetes服务发现插件初始化完成")
            return True

        except Exception as e:
            logger.error(f"Kubernetes服务发现插件初始化失败: {e}")
            return False

    async def shutdown(self) -> None:
        """关闭插件"""
        try:
            if self.health_manager:
                await self.health_manager.stop()
            if self.registry:
                await self.registry.close()
            logger.info("Kubernetes服务发现插件已关闭")
        except Exception as e:
            logger.error(f"关闭Kubernetes服务发现插件失败: {e}")

    async def _initialize_k8s_client(self):
        """初始化Kubernetes客户端"""
        try:
            from kubernetes import client, config, watch

            # 加载Kubernetes配置
            try:
                config.load_kube_config()
            except Exception:
                # 如果没有配置文件，使用集群内配置
                config.load_incluster_config()

            self.k8s_client = client.CoreV1Api()
            logger.info("Kubernetes客户端初始化成功")

        except ImportError:
            logger.error("Kubernetes客户端库未安装")
            raise
        except Exception as e:
            logger.error(f"初始化Kubernetes客户端失败: {e}")
            raise

    async def _start_k8s_service_watch(self):
        """开始监听Kubernetes服务"""
        try:

            # 创建异步任务监听服务变化
            asyncio.create_task(self._watch_k8s_services())

        except Exception as e:
            logger.error(f"启动Kubernetes服务监听失败: {e}")

    async def _watch_k8s_services(self):
        """监听Kubernetes服务变化"""
        try:
            from kubernetes import watch

            w = watch.Watch()

            while True:
                try:
                    # 监听服务变化
                    for event in w.stream(
                        self.k8s_client.list_service_for_all_namespaces, timeout_seconds=60
                    ):
                        await self._handle_k8s_service_event(event)

                except Exception as e:
                    logger.error(f"监听Kubernetes服务失败: {e}")
                    await asyncio.sleep(5)  # 错误后等待重试

        except Exception as e:
            logger.error(f"Kubernetes服务监听异常: {e}")

    async def _handle_k8s_service_event(self, event):
        """处理Kubernetes服务事件"""
        try:
            service = event["object"]
            event_type = event["type"]

            if event_type == "ADDED":
                await self._register_k8s_service(service)
            elif event_type == "DELETED":
                await self._deregister_k8s_service(service)
            elif event_type == "MODIFIED":
                await self._update_k8s_service(service)

        except Exception as e:
            logger.error(f"处理Kubernetes服务事件失败: {e}")

    async def _register_k8s_service(self, service):
        """注册Kubernetes服务"""
        try:
            # 检查服务是否有合适的注解
            annotations = service.metadata.annotations or {}

            if not self._should_register_service(service, annotations):
                return

            # 创建服务实例
            instance = ServiceInstance(
                service_id=f"k8s-{service.metadata.namespace}-{service.metadata.name}",
                service_name=service.metadata.name,
                namespace=service.metadata.namespace,
                host=service.spec.cluster_ip,
                port=self._get_service_port(service),
                protocol=self._get_service_protocol(service, annotations),
                endpoints=self._get_service_endpoints(service),
                metadata={
                    "type": "kubernetes",
                    "uid": service.metadata.uid,
                    "labels": service.metadata.labels or {},
                    "annotations": annotations,
                    "cluster_ip": service.spec.cluster_ip,
                    "selector": service.spec.selector or {},
                },
            )

            # 注册服务
            await self.registry.register_service(instance)
            logger.info(
                f"Kubernetes服务已注册: {service.metadata.namespace}/{service.metadata.name}"
            )

        except Exception as e:
            logger.error(f"注册Kubernetes服务失败: {e}")

    async def _deregister_k8s_service(self, service):
        """注销Kubernetes服务"""
        try:
            service_id = f"k8s-{service.metadata.namespace}-{service.metadata.name}"
            await self.registry.deregister_service(service_id)
            logger.info(
                f"Kubernetes服务已注销: {service.metadata.namespace}/{service.metadata.name}"
            )

        except Exception as e:
            logger.error(f"注销Kubernetes服务失败: {e}")

    async def _update_k8s_service(self, service):
        """更新Kubernetes服务"""
        try:
            service_id = f"k8s-{service.metadata.namespace}-{service.metadata.name}"

            # 获取现有实例
            existing_instance = await self.registry.get_service_instance(service_id)
            if not existing_instance:
                # 如果不存在，则注册
                await self._register_k8s_service(service)
            else:
                # 更新现有实例
                updates = {
                    "host": service.spec.cluster_ip,
                    "port": self._get_service_port(service),
                    "protocol": self._get_service_protocol(
                        service, service.metadata.annotations or {}
                    ),
                    "updated_time": datetime.now(),
                }

                await self.registry.update_service_instance(service_id, updates)
                logger.info(
                    f"Kubernetes服务已更新: {service.metadata.namespace}/{service.metadata.name}"
                )

        except Exception as e:
            logger.error(f"更新Kubernetes服务失败: {e}")

    def _should_register_service(self, service, annotations) -> bool:
        """判断是否应该注册服务"""
        # 检查注解
        if annotations.get("athena-service-discovery/enabled") == "false":
            return False

        # 检查标签
        labels = service.metadata.labels or {}
        if labels.get("athena-service-discovery") == "disabled":
            return False

        # 只注册有ClusterIP的服务
        return service.spec.cluster_ip is not None

    def _get_service_port(self, service) -> int:
        """获取服务端口"""
        if not service.spec.ports:
            return 80

        # 优先获取HTTP端口
        for port in service.spec.ports:
            if port.port == 80 or port.name in ["http", "http-api"]:
                return port.port

        # 返回第一个端口
        return service.spec.ports[0].port

    def _get_service_protocol(self, service, annotations) -> ProtocolType:
        """获取服务协议"""
        # 从注解中获取协议
        protocol = annotations.get("athena-service-discovery/protocol")
        if protocol:
            return ProtocolType(protocol.lower())

        # 从端口名称推断
        if service.spec.ports:
            for port in service.spec.ports:
                if port.name and "grpc" in port.name.lower():
                    return ProtocolType.GRPC
                elif port.name and "http" in port.name.lower():
                    return ProtocolType.HTTP

        return ProtocolType.HTTP

    def _get_service_endpoints(self, service) -> list[str]:
        """获取服务端点"""
        endpoints = []

        if service.spec.cluster_ip:
            for port in service.spec.ports or []:
                endpoint = f"{service.spec.cluster_ip}:{port.port}"
                endpoints.append(endpoint)

        return endpoints

    async def on_service_register(self, instance: ServiceInstance) -> None:
        """服务注册回调"""
        logger.info(f"Plugin: Kubernetes service registered - {instance.service_id}")

    async def on_service_deregister(self, instance: ServiceInstance) -> None:
        """服务注销回调"""
        logger.info(f"Plugin: Kubernetes service deregistered - {instance.service_id}")

    async def on_health_change(
        self, service_id: str, old_status: HealthStatus, new_status: HealthStatus
    ) -> None:
        """健康状态变更回调"""
        logger.info(
            f"Plugin: Kubernetes service health changed - {service_id}: {old_status.value} -> {new_status.value}"
        )


class ServiceDiscoveryPluginManager:
    """服务发现插件管理器"""

    def __init__(self):
        self.plugins: dict[str, ServiceDiscoveryPlugin] = {}
        self.registry: ServiceRegistry | None = None
        self.health_manager: HealthCheckManager | None = None
        self.load_balancer: LoadBalancingManager | None = None
        self.config = {}

    async def initialize(self, config: dict) -> bool:
        """初始化插件管理器"""
        try:
            self.config = config

            # 创建核心组件
            registry_config = config.get("registry", {})
            self.registry = await create_service_discovery(registry_config)
            self.health_manager = create_health_check_manager(self.registry)
            self.load_balancer = create_load_balancing_manager()

            # 启动健康检查管理器
            await self.health_manager.start()

            # 加载插件
            await self._load_plugins(config.get("plugins", {}))

            logger.info("服务发现插件管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"服务发现插件管理器初始化失败: {e}")
            return False

    async def shutdown(self) -> None:
        """关闭插件管理器"""
        try:
            # 关闭所有插件
            for plugin in self.plugins.values():
                await plugin.shutdown()

            # 关闭核心组件
            if self.health_manager:
                await self.health_manager.stop()
            if self.registry:
                await self.registry.close()

            logger.info("服务发现插件管理器已关闭")
        except Exception as e:
            logger.error(f"关闭服务发现插件管理器失败: {e}")

    async def _load_plugins(self, plugins_config: dict):
        """加载插件"""
        for plugin_name, plugin_config in plugins_config.items():
            if not plugin_config.get("enabled", True):
                continue

            plugin_class = self._get_plugin_class(plugin_config.get("type"))
            if not plugin_class:
                logger.error(f"未知的插件类型: {plugin_config.get('type')}")
                continue

            try:
                # 创建插件实例
                plugin = plugin_class()

                # 初始化插件
                success = await plugin.initialize(plugin_config.get("config", {}))
                if success:
                    self.plugins[plugin_name] = plugin
                    logger.info(f"插件已加载: {plugin_name}")
                else:
                    logger.error(f"插件初始化失败: {plugin_name}")

            except Exception as e:
                logger.error(f"加载插件失败 {plugin_name}: {e}")

    def _get_plugin_class(self, plugin_type: str) -> type | None:
        """获取插件类"""
        plugin_classes = {
            "mcp": MCPServiceDiscoveryPlugin,
            "kubernetes": KubernetesServiceDiscoveryPlugin,
        }

        return plugin_classes.get(plugin_type.lower())

    def get_plugin(self, plugin_name: str) -> ServiceDiscoveryPlugin | None:
        """获取插件实例"""
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> list[ServiceDiscoveryPlugin]:
        """获取所有插件"""
        return list(self.plugins.values())

    async def discover_services(
        self, service_name: str, namespace: str = "default", healthy_only: bool = True
    ) -> list[ServiceInstance]:
        """发现服务（通过所有插件）"""
        try:
            # 通过服务注册中心发现服务
            instances = await self.registry.discover_services(service_name, namespace, healthy_only)

            logger.info(f"发现服务 {service_name}: {len(instances)} 个实例")
            return instances

        except Exception as e:
            logger.error(f"发现服务失败 {service_name}: {e}")
            return []

    async def route_request(
        self, service_name: str, request_context: RequestContext
    ) -> ServiceInstance | None:
        """路由请求到合适的服务实例"""
        try:
            # 发现服务实例
            instances = await self.discover_services(
                service_name,
                request_context.namespace if hasattr(request_context, "namespace") else "default",
            )

            if not instances:
                logger.error(f"没有可用的服务实例: {service_name}")
                return None

            # 使用负载均衡器选择实例
            selected_instance = await self.load_balancer.select_instance(
                service_name, instances, request_context
            )

            logger.info(f"请求已路由到: {selected_instance.service_id}")
            return selected_instance

        except Exception as e:
            logger.error(f"路由请求失败 {service_name}: {e}")
            return None

    async def update_service_metrics(self, service_id: str, response_time: float, success: bool):
        """更新服务指标"""
        if self.load_balancer:
            self.load_balancer.update_service_metrics(service_id, response_time, success)

    def get_service_metrics(self, service_id: str) -> ServiceMetrics | None:
        """获取服务指标"""
        if self.load_balancer:
            return self.load_balancer.get_service_metrics(service_id)
        return None


# 工厂函数
async def create_service_discovery_plugin_manager(config: dict) -> ServiceDiscoveryPluginManager:
    """创建服务发现插件管理器"""
    manager = ServiceDiscoveryPluginManager()
    await manager.initialize(config)
    return manager


# 使用示例
async def main():
    """主函数示例"""
    # 配置
    config = {
        "registry": {"storage": {"type": "redis", "redis_url": "redis://localhost:6379"}},
        "plugins": {
            "mcp": {
                "type": "mcp",
                "enabled": True,
                "config": {"mcp_config_path": "config/athena_mcp_config.json"},
            },
            "kubernetes": {
                "type": "kubernetes",
                "enabled": True,
                "config": {"namespace": "athena"},
            },
        },
    }

    # 创建插件管理器
    plugin_manager = await create_service_discovery_plugin_manager(config)

    try:
        # 测试服务发现
        from .load_balancing import RequestContext

        context = RequestContext(
            request_id="test-123",
            service_name="test-service",
            method="GET",
            path="/api/test",
            headers={},
            query_params={},
            timestamp=datetime.now(),
            client_ip="192.168.1.100",
            user_agent="test-client",
        )

        # 发现服务
        instances = await plugin_manager.discover_services("test-service")
        print(f"发现 {len(instances)} 个服务实例")

        # 路由请求
        if instances:
            selected = await plugin_manager.route_request("test-service", context)
            print(f"选择实例: {selected.service_id if selected else 'None'}")

        # 保持运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        await plugin_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
