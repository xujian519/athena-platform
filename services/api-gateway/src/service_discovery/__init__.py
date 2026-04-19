import asyncio
import json
import logging
from datetime import datetime

# Service Discovery System Package
# 服务发现系统包
from typing import Any, Dict, List, Optional

from aiohttp import web

from .core_service_registry import (
    HealthCheckConfig,
    HealthStatus,
    ProtocolType,
    ServiceConfig,
    ServiceInstance,
    ServiceRegistry,
    ServiceState,
    create_service_discovery,
)
from .health_check import (
    HealthCheckConfig,
    HealthChecker,
    HealthCheckManager,
    HealthCheckResult,
    create_health_check_manager,
)
from .load_balancing import (
    LoadBalanceAlgorithm,
    LoadBalancer,
    LoadBalancingManager,
    RequestContext,
    ServiceMetrics,
    create_load_balancing_manager,
)
from .plugin_integration import (
    KubernetesServiceDiscoveryPlugin,
    MCPServiceDiscoveryPlugin,
    ServiceDiscoveryPlugin,
    ServiceDiscoveryPluginManager,
    create_service_discovery_plugin_manager,
)

logger = logging.getLogger(__name__)


class AthenaServiceDiscovery:
    """Athena服务发现系统主类"""

    def __init__(self, config: dict):
        self.config = config
        self.registry: ServiceRegistry | None = None
        self.health_manager: HealthCheckManager | None = None
        self.load_balancer: LoadBalancingManager | None = None
        self.plugin_manager: ServiceDiscoveryPluginManager | None = None
        self.api_server = None
        self.running = False

    async def initialize(self) -> bool:
        """初始化服务发现系统"""
        try:
            logger.info("正在初始化Athena服务发现系统...")

            # 初始化核心组件
            await self._initialize_core_components()

            # 初始化插件管理器
            await self._initialize_plugin_manager()

            # 启动API服务
            await self._start_api_server()

            self.running = True
            logger.info("Athena服务发现系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"Athena服务发现系统初始化失败: {e}")
            return False

    async def shutdown(self) -> None:
        """关闭服务发现系统"""
        try:
            logger.info("正在关闭Athena服务发现系统...")
            self.running = False

            # 关闭API服务
            if self.api_server:
                await self.api_server.stop()

            # 关闭插件管理器
            if self.plugin_manager:
                await self.plugin_manager.shutdown()

            # 关闭核心组件
            if self.health_manager:
                await self.health_manager.stop()
            if self.registry:
                await self.registry.close()

            logger.info("Athena服务发现系统已关闭")

        except Exception as e:
            logger.error(f"关闭Athena服务发现系统失败: {e}")

    async def _initialize_core_components(self):
        """初始化核心组件"""
        # 创建服务注册中心
        registry_config = self.config.get("registry", {})
        self.registry = await create_service_discovery(registry_config)

        # 创建健康检查管理器
        self.health_manager = create_health_check_manager(self.registry)
        await self.health_manager.start()

        # 创建负载均衡管理器
        self.load_balancer = create_load_balancing_manager()

        logger.info("核心组件初始化完成")

    async def _initialize_plugin_manager(self):
        """初始化插件管理器"""
        plugin_config = self.config.get("plugins", {})
        self.plugin_manager = await create_service_discovery_plugin_manager(
            {"registry": self.config.get("registry", {}), "plugins": plugin_config}
        )

        logger.info("插件管理器初始化完成")

    async def _start_api_server(self):
        """启动API服务"""
        from .core_service_registry import ServiceDiscoveryAPI

        api_config = self.config.get("api", {})
        self.api_server = ServiceDiscoveryAPI(
            self.registry, host=api_config.get("host", "0.0.0.0"), port=api_config.get("port", 8080)
        )

        await self.api_server.start()
        logger.info(
            f"API服务已启动: {api_config.get('host', '0.0.0.0')}:{api_config.get('port', 8080)}"
        )

    async def discover_services(
        self, service_name: str, namespace: str = "default", healthy_only: bool = True
    ) -> list[ServiceInstance]:
        """发现服务"""
        try:
            if self.plugin_manager:
                return await self.plugin_manager.discover_services(
                    service_name, namespace, healthy_only
                )
            elif self.registry:
                return await self.registry.discover_services(service_name, namespace, healthy_only)
            else:
                return []

        except Exception as e:
            logger.error(f"发现服务失败 {service_name}: {e}")
            return []

    async def route_request(
        self,
        service_name: str,
        method: str,
        path: str,
        headers: dict[str, str],
        query_params: dict[str, str],
        client_ip: str,
        user_agent: str,
        namespace: str = "default",
    ) -> ServiceInstance | None:
        """路由请求到服务实例"""
        try:
            # 创建请求上下文
            context = RequestContext(
                request_id=f"req-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                service_name=service_name,
                method=method,
                path=path,
                headers=headers,
                query_params=query_params,
                timestamp=datetime.now(),
                client_ip=client_ip,
                user_agent=user_agent,
            )

            # 路由请求
            if self.plugin_manager:
                return await self.plugin_manager.route_request(service_name, context)
            elif self.load_balancer:
                instances = await self.discover_services(service_name, namespace)
                if instances:
                    return await self.load_balancer.select_instance(
                        service_name, instances, context
                    )

            return None

        except Exception as e:
            logger.error(f"路由请求失败 {service_name}: {e}")
            return None

    async def register_service(self, service_data: dict) -> dict[str, Any]:
        """注册服务"""
        try:
            # 创建服务实例
            instance = ServiceInstance(
                service_id=service_data.get("service_id"),
                service_name=service_data["service_name"],
                version=service_data.get("version", "1.0.0"),
                namespace=service_data.get("namespace", "default"),
                host=service_data["host"],
                port=service_data["port"],
                protocol=self._get_protocol_type(service_data.get("protocol", "http")),
                endpoints=service_data.get("endpoints", []),
                weight=service_data.get("weight", 100),
                tags=service_data.get("tags", []),
                metadata=service_data.get("metadata", {}),
                health_check_url=service_data.get("health_check_url"),
            )

            # 注册服务
            success = await self.registry.register_service(instance)

            if success:
                return {
                    "success": True,
                    "service_id": instance.service_id,
                    "message": "Service registered successfully",
                }
            else:
                return {"success": False, "message": "Failed to register service"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def deregister_service(self, service_id: str) -> dict[str, Any]:
        """注销服务"""
        try:
            success = await self.registry.deregister_service(service_id)

            if success:
                return {"success": True, "message": "Service deregistered successfully"}
            else:
                return {"success": False, "message": "Service not found or deregistration failed"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_service_health(
        self, service_name: str, namespace: str = "default"
    ) -> dict[str, Any]:
        """获取服务健康状态"""
        try:
            if self.health_manager:
                return await self.health_manager.get_service_health_summary(service_name, namespace)
            else:
                return {"error": "Health manager not available"}

        except Exception as e:
            return {"error": str(e)}

    async def update_service_metrics(self, service_id: str, response_time: float, success: bool):
        """更新服务指标"""
        try:
            if self.load_balancer:
                self.load_balancer.update_service_metrics(service_id, response_time, success)
            if self.plugin_manager:
                await self.plugin_manager.update_service_metrics(service_id, response_time, success)

        except Exception as e:
            logger.error(f"更新服务指标失败 {service_id}: {e}")

    def _get_protocol_type(self, protocol_str: str):
        """获取协议类型"""

        protocol_map = {
            "http": ProtocolType.HTTP,
            "https": ProtocolType.HTTPS,
            "grpc": ProtocolType.GRPC,
            "graphql": ProtocolType.GRAPHQL,
            "tcp": ProtocolType.TCP,
        }
        return protocol_map.get(protocol_str.lower(), ProtocolType.HTTP)

    async def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        try:
            status = {
                "system": "Athena Service Discovery",
                "version": "2.0.0",
                "running": self.running,
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "registry": {
                        "running": self.registry is not None,
                        "service_count": len(self.registry.registered_services)
                        if self.registry
                        else 0,
                    },
                    "health_manager": {
                        "running": self.health_manager is not None,
                        "active_checks": len(self.health_manager.health_check_tasks)
                        if self.health_manager
                        else 0,
                    },
                    "load_balancer": {
                        "running": self.load_balancer is not None,
                        "algorithm_count": len(self.load_balancer.balancers)
                        if self.load_balancer
                        else 0,
                    },
                    "plugin_manager": {
                        "running": self.plugin_manager is not None,
                        "plugin_count": len(self.plugin_manager.plugins)
                        if self.plugin_manager
                        else 0,
                    },
                },
                "api": {
                    "running": self.api_server is not None,
                    "url": f"http://{self.config.get('api', {}).get('host', '0.0.0.0')}:{self.config.get('api', {}).get('port', 8080)}",
                },
            }

            return status

        except Exception as e:
            return {"error": str(e)}


# 全局服务发现实例
_athena_service_discovery: AthenaServiceDiscovery | None = None


async def get_service_discovery() -> AthenaServiceDiscovery:
    """获取全局服务发现实例"""
    global _athena_service_discovery
    if _athena_service_discovery is None:
        # 加载配置
        config = await _load_config()
        _athena_service_discovery = AthenaServiceDiscovery(config)
        await _athena_service_discovery.initialize()
    return _athena_service_discovery


async def _load_config() -> dict:
    """加载配置"""
    try:
        import json as _json

        with open("config/service_discovery.json", encoding="utf-8") as f:
            return _json.load(f)
    except FileNotFoundError:
        # 默认配置
        return {
            "registry": {"storage": {"type": "redis", "redis_url": "redis://localhost:6379"}},
            "api": {"host": "0.0.0.0", "port": 8080},
            "plugins": {
                "mcp": {
                    "type": "mcp",
                    "enabled": True,
                    "config": {"mcp_config_path": "config/athena_mcp_config.json"},
                }
            },
        }


# API端点处理器
async def handle_discover_services(request: web.Request) -> web.Response:
    """处理服务发现请求"""
    try:
        service_name = request.match_info["service_name"]
        namespace = request.query.get("namespace", "default")
        healthy_only = request.query.get("healthy_only", "true").lower() == "true"

        service_discovery = await get_service_discovery()
        instances = await service_discovery.discover_services(service_name, namespace, healthy_only)

        return web.json_response(
            {
                "service_name": service_name,
                "namespace": namespace,
                "instances": [instance.to_dict() for instance in instances],
                "count": len(instances),
            }
        )

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_route_request(request: web.Request) -> web.Response:
    """处理请求路由"""
    try:
        service_name = request.match_info["service_name"]

        service_discovery = await get_service_discovery()
        selected_instance = await service_discovery.route_request(
            service_name=service_name,
            method=request.method,
            path=request.path,
            headers=dict(request.headers),
            query_params=dict(request.query),
            client_ip=request.remote,
            user_agent=request.headers.get("User-Agent", ""),
            namespace=request.query.get("namespace", "default"),
        )

        if selected_instance:
            return web.json_response(
                {
                    "success": True,
                    "instance": selected_instance.to_dict(),
                    "message": "Request routed successfully",
                }
            )
        else:
            return web.json_response(
                {"success": False, "message": "No available service instances"}, status=503
            )

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_register_service(request: web.Request) -> web.Response:
    """处理服务注册请求"""
    try:
        service_data = await request.json()

        service_discovery = await get_service_discovery()
        result = await service_discovery.register_service(service_data)

        return web.json_response(result)

    except Exception as e:
        return web.json_response({"success": False, "message": str(e)}, status=400)


async def handle_deregister_service(request: web.Request) -> web.Response:
    """处理服务注销请求"""
    try:
        service_id = request.match_info["service_id"]

        service_discovery = await get_service_discovery()
        result = await service_discovery.deregister_service(service_id)

        return web.json_response(result)

    except Exception as e:
        return web.json_response({"success": False, "message": str(e)}, status=400)


async def handle_get_status(request: web.Request) -> web.Response:
    """处理状态查询请求"""
    try:
        service_discovery = await get_service_discovery()
        status = await service_discovery.get_system_status()

        return web.json_response(status)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# 创建API应用
def create_service_discovery_app() -> web.Application:
    """创建服务发现API应用"""
    app = web.Application()

    # 注册路由
    app.router.add_get("/health", lambda r: web.json_response({"status": "healthy"}))
    app.router.add_get("/status", handle_get_status)
    app.router.add_get("/services/{service_name}/discover", handle_discover_services)
    app.router.add_post("/services/{service_name}/route", handle_route_request)
    app.router.add_post("/services/register", handle_register_service)
    app.router.add_delete("/services/{service_id}", handle_deregister_service)

    return app


# 主函数
async def main():
    """主函数"""
    try:
        # 创建API应用
        app = create_service_discovery_app()

        # 加载配置
        config = await _load_config()

        # 启动服务
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(
            runner,
            host=config.get("api", {}).get("host", "0.0.0.0"),
            port=config.get("api", {}).get("port", 8080),
        )

        await site.start()

        print(f"""
🚀 Athena Service Discovery System 启动成功

📍 API地址: http://{config.get("api", {}).get("host", "0.0.0.0")}:{config.get("api", {}).get("port", 8080)}
🔍 健康检查: http://{config.get("api", {}).get("host", "0.0.0.0")}:{config.get("api", {}).get("port", 8080)}/health
📊 系统状态: http://{config.get("api", {}).get("host", "0.0.0.0")}:{config.get("api", {}).get("port", 8080)}/status

📋 可用端点:
  GET  /health                    - 健康检查
  GET  /status                    - 系统状态
  GET  /services/{{service_name}}/discover  - 发现服务
  POST /services/{{service_name}}/route     - 路由请求
  POST /services/register           - 注册服务
  DELETE /services/{{service_id}}    - 注销服务

⏰ 启动时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """)

        # 保持运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 正在关闭服务...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())
