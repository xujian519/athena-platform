#!/usr/bin/env python3
"""
Athena API Gateway 核心服务
统一微服务接入和API管理平台
"""

import asyncio
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/api-gateway.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ==================== 数据模型 ====================


@dataclass
class ServiceInstance:
    """服务实例"""

    service_name: str
    instance_id: str
    host: str
    port: int
    protocol: str = "http"
    health_endpoint: str = "/health"
    metadata: dict[str, Any] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "unknown"  # healthy, unhealthy, unknown
    auto_registered: bool = False  # 新增字段：是否自动注册
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ServiceRegistry:
    """服务注册请求"""
    service_name: str
    instance_id: str
    host: str
    port: int
    protocol: str = "http"
    health_endpoint: str = "/health"
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass
class RouteConfig:
    """路由配置"""

    path: str
    service_name: str
    methods: list[str]
    strip_prefix: bool = True
    timeout: int = 30
    retries: int = 3
    rate_limit: dict[str, int] | None = None
    auth_required: bool = False
    cors_enabled: bool = True


@dataclass
class RouteDefinition:
    """路由定义"""
    path: str
    service_name: str
    methods: list[str]
    strip_prefix: bool = True
    timeout: int = 30
    retries: int = 3
    rate_limit: dict[str, int] | None = None
    auth_required: bool = False
    cors_enabled: bool = True


class ServiceRegistryManager:
    """服务注册管理器基类"""

    def __init__(self, config_file: str = None):
        self.services: dict[str, list[ServiceInstance]] = {}
        self.config_file = config_file or "data/services.yaml"  # 设置默认配置文件路径
        self._load_services()

    def _load_services(self):
        """加载已保存的服务配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.services = data.get('services', {})
                    logger.info(f"加载了 {len(self.services)} 个服务配置")
            except Exception as e:
                logger.error(f"加载服务配置失败: {e}")
                self.services = {}

    def _save_services(self):
        """保存认证配置"""
        if not self.services:
            return

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        services_dict = {}
        for service_name, instances in self.services.items():
            services_dict[service_name] = [asdict(s) for s in instances]
        data = {'services': services_dict}

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"保存了 {len(self.services)} 个服务配置")
        except Exception as e:
            logger.error(f"保存认证配置失败: {e}")

    def register_service(self, registration: ServiceRegistry) -> bool:
        """注册单个服务实例"""
        if registration.service_name not in self.services:
            self.services[registration.service_name] = []

        # 创建新实例
        instance = ServiceInstance(
            service_name=registration.service_name,
            instance_id=registration.instance_id,
            host=registration.host,
            port=registration.port,
            protocol= registration.protocol,
            health_endpoint=registration.health_endpoint,
            metadata=registration.metadata,
            tags=registration.tags,
            created_at=datetime.now(timezone.utc),
            status="registered",
            auto_registered=False
        )

        # 添加到服务列表
        self.services[registration.service_name].append(instance)

        # 保存配置
        self._save_services()

        logger.info(f"注册服务成功: {registration.service_name} ({registration.instance_id})")
        return True

    def deregister_service(self, service_name: str, instance_id: str) -> bool:
        """注销服务实例"""
        if service_name not in self.services:
            logger.warning(f"服务不存在: {service_name}")
            return False

        # 查找实例
        found_index = None
        for i, instance in enumerate(self.services[service_name]):
            if instance.instance_id == instance_id:
                found_index = i
                break

        if found_index is None:
            logger.warning(f"服务实例不存在: {service_name}/{instance_id}")
            return False

        # 从服务列表中删除
        del self.services[service_name][found_index]

        # 保存配置
        self._save_services()

        logger.info(f"注销服务成功: {service_name}/{instance_id}")
        return True

    def batch_register_services(self, registrations: list[ServiceRegistry]) -> dict:
        """批量注册多个服务"""
        results = []

        for registration in registrations:
            result = self.register_service(registration)
            results.append({
                "service_name": registration.service_name,
                "instance_id": registration.instance_id,
                "status": "success" if result else "failed"
            })

        return {
            "registered": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "details": results
        }

    def get_service(self, service_name: str) -> list[ServiceInstance] | None:
        """获取服务的所有实例"""
        return self.services.get(service_name, [])

    def get_instance(self, service_name: str, instance_id: str) -> ServiceInstance | None:
        """获取指定服务实例"""
        if service_name in self.services:
            for instance in self.services[service_name]:
                if instance.instance_id == instance_id:
                    return instance
        return None

    def get_all_services(self) -> dict[str, list[ServiceInstance]]:
        """获取所有服务"""
        return dict(self.services)

    def get_healthy_instances(self, service_name: str) -> list[ServiceInstance]:
        """获取健康的服务实例"""
        if service_name in self.services:
            return [inst for inst in self.services[service_name] if inst.status == "healthy"]
        return []

    def update_service_instance(self, service_name: str, instance_id: str, updates: dict) -> bool:
        """更新服务实例信息"""
        if service_name not in self.services:
            return False

        for _i, instance in enumerate(self.services[service_name]):
            if instance.instance_id == instance_id:
                # 更新字段
                for key, value in updates.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)

                instance.last_heartbeat = datetime.now(timezone.utc)
                # 保存配置
                self._save_services()
                logger.info(f"服务实例更新成功: {service_name}/{instance_id}")
                return True

        logger.warning(f"服务实例不存在: {service_name}/{instance_id}")
        return False
        """更新服务实例信息"""
        if service_name in self.services:
            for _i, instance in enumerate(self.services[service_name]):
                if instance.instance_id == instance_id:
                    # 更新字段
                    for key, value in updates.items():
                        if hasattr(instance, key):
                            setattr(instance, key, value)

                    instance.last_heartbeat = datetime.now(timezone.utc)
                    logger.info(f"更新服务实例: {service_name}/{instance_id}")

            # 保存配置
            self._save_services()
            logger.info(f"服务实例更新成功: {service_name}/{instance_id}")
            return True

        return False

    def get_healthy_instances(self, service_name: str) -> list[ServiceInstance]:
        """获取健康的服务实例"""
        if service_name not in self.services:
            return []

        healthy_instances = [
            inst for inst in self.services[service_name] if inst.status == "healthy"
        ]

        return healthy_instances

    async def health_check_all(self):
        """健康检查所有服务"""
        async with aiohttp.ClientSession() as session:
            for service_name, instances in self.services.items():
                for instance in instances:
                    try:
                        health_url = f"{instance.protocol}://{instance.host}:{instance.port}{instance.health_endpoint}"
                        async with session.get(
                            health_url, timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            if response.status == 200:
                                instance.status = "healthy"
                                instance.last_heartbeat = datetime.now(timezone.utc)
                            else:
                                instance.status = "unhealthy"
                    except Exception as e:
                        logger.warning(f"健康检查失败 {service_name}/{instance.instance_id}: {e}")
                        instance.status = "unhealthy"

        self._save_services()

    def get_all_services(self) -> dict[str, list[dict]]:
        """获取所有服务状态"""
        return {
            name: [asdict(inst) for inst in instances] for name, instances in self.services.items()
        }


class RouteManager:
    """路由管理器"""

    def __init__(self):
        self.routes: dict[str, RouteConfig] = {}
        self.config_file = Path("data/gateway_routes.yaml")
        self._load_routes()

    def _load_routes(self):
        """加载路由配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    for path, route_data in data.get("routes", {}).items():
                        self.routes[path] = RouteConfig(path=path, **route_data)
                logger.info(f"加载了 {len(self.routes)} 个路由配置")
        except Exception as e:
            logger.error(f"加载路由配置失败: {e}")

    def _save_routes(self):
        """保存路由配置"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "routes": {path: asdict(route) for path, route in self.routes.items()},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"保存路由配置失败: {e}")

    def add_route(self, route_def: RouteDefinition) -> bool:
        """添加路由"""
        route = RouteConfig(
            path=route_def.path,
            service_name=route_def.service_name,
            methods=route_def.methods,
            strip_prefix=route_def.strip_prefix,
            timeout=route_def.timeout,
            retries=route_def.retries,
            rate_limit=route_def.rate_limit,
            auth_required=route_def.auth_required,
            cors_enabled=route_def.cors_enabled,
        )

        self.routes[route_def.path] = route
        self._save_routes()
        logger.info(f"添加路由: {route_def.path} -> {route_def.service_name}")
        return True

    def remove_route(self, path: str) -> bool:
        """移除路由"""
        if path in self.routes:
            del self.routes[path]
            self._save_routes()
            logger.info(f"移除路由: {path}")
            return True
        return False

    def find_route(self, request_path: str, method: str) -> RouteConfig | None:
        """查找匹配的路由"""
        for path, route in self.routes.items():
            if method in route.methods and self._path_matches(request_path, path):
                return route
        return None

    def _path_matches(self, request_path: str, route_path: str) -> bool:
        """检查路径是否匹配"""
        # 简单的路径匹配，支持路径参数
        if route_path == request_path:
            return True

        # 处理通配符路径
        if route_path.endswith("/*"):
            prefix = route_path[:-2]
            return request_path.startswith(prefix + "/") or request_path == prefix

        return False

    def get_all_routes(self) -> dict[str, dict]:
        """获取所有路由配置"""
        return {path: asdict(route) for path, route in self.routes.items()}


class LoadBalancer:
    """负载均衡器"""

    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.round_robin_counters = {}

    def select_instance(
        self, instances: list[ServiceInstance], service_name: str
    ) -> ServiceInstance | None:
        """选择服务实例"""
        if not instances:
            return None

        if self.strategy == "round_robin":
            return self._round_robin_selection(instances, service_name)
        elif self.strategy == "random":
            return self._random_selection(instances)
        else:
            return instances[0]

    def _round_robin_selection(
        self, instances: list[ServiceInstance], service_name: str
    ) -> ServiceInstance:
        """轮询选择"""
        if service_name not in self.round_robin_counters:
            self.round_robin_counters[service_name] = 0

        index = self.round_robin_counters[service_name] % len(instances)
        self.round_robin_counters[service_name] += 1
        return instances[index]

    def _random_selection(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """随机选择"""
        import random

        return random.choice(instances)


# ==================== FastAPI 应用 ====================

# 初始化组件
service_registry = ServiceRegistryManager()
route_manager = RouteManager()
load_balancer = LoadBalancer()

# 导入认证模块
from auth_api import auth_router
from auth_middleware import api_key_middleware, jwt_middleware, permission_middleware

# 导入多模态文件处理系统
from multimodal_endpoints import setup_multimodal_integration

# 创建FastAPI应用
app = FastAPI(
    title="Athena API Gateway",
    description="统一微服务接入和API管理平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 集成多模态文件处理系统（路由需要在应用启动前注册）
try:
    multimodal_config = {
        "multimodal_service_url": "http://localhost:8021",
        "enabled": True
    }
    setup_multimodal_integration(app, multimodal_config)
    logger.info("✅ 多模态文件处理系统路由已注册")
except Exception as e:
    logger.warning(f"⚠️ 多模态文件处理系统集成失败: {e}")

# 添加认证中间件
@app.middleware("http")
async def auth_middleware_wrapper(request: Request, call_next):
    """认证中间件包装器"""
    # 首先尝试JWT认证
    try:
        return await jwt_middleware(request, call_next)
    except HTTPException as e:
        # 如果JWT失败，尝试API密钥认证
        if e.status_code == 401:
            try:
                return await api_key_middleware(request, call_next)
            except HTTPException:
                # API密钥也失败，返回JWT的错误
                raise e from None
        raise


# 添加权限检查中间件
@app.middleware("http")
async def permission_middleware_wrapper(request: Request, call_next):
    """权限检查中间件包装器"""
    return await permission_middleware(request, call_next)


# 注册认证路由
app.include_router(auth_router)

# ==================== 后台任务 ====================


async def periodic_health_check():
    """定期健康检查任务"""
    while True:
        try:
            await service_registry.health_check_all()
            await asyncio.sleep(service_registry.health_check_interval)
        except Exception as e:
            logger.error(f"健康检查任务失败: {e}")
            await asyncio.sleep(5)


# ==================== API 端点 ====================


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "Athena API Gateway",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services_count": len(service_registry.services),
        "routes_count": len(route_manager.routes),
    }


# ==================== 服务注册 API ====================


@app.post("/api/v1/services/register")
async def register_service(registry: ServiceRegistry):
    """注册服务"""
    success = service_registry.register_service(registry)
    if success:
        return {"message": "服务注册成功", "service": registry.service_name}
    else:
        raise HTTPException(status_code=400, detail="服务注册失败")


@app.delete("/api/v1/services/{service_name}/instances/{instance_id}")
async def deregister_service(service_name: str, instance_id: str):
    """注销服务"""
    success = service_registry.deregister_service(service_name, instance_id)
    if success:
        return {"message": "服务注销成功"}
    else:
        raise HTTPException(status_code=404, detail="服务实例不存在")


@app.get("/api/v1/services")
async def get_services():
    """获取所有服务"""
    return service_registry.get_all_services()


@app.get("/api/v1/services/{service_name}/instances")
async def get_service_instances(service_name: str):
    """获取指定服务的实例"""
    instances = service_registry.services.get(service_name, [])
    return [asdict(inst) for inst in instances]


@app.get("/api/v1/services/{service_name}/healthy")
async def get_healthy_instances(service_name: str):
    """获取健康的服务实例"""
    instances = service_registry.get_healthy_instances(service_name)
    return [asdict(inst) for inst in instances]


# ==================== 路由管理 API ====================


@app.post("/api/v1/routes")
async def add_route(route: RouteDefinition):
    """添加路由"""
    success = route_manager.add_route(route)
    if success:
        return {"message": "路由添加成功", "path": route.path}
    else:
        raise HTTPException(status_code=400, detail="路由添加失败")


@app.delete("/api/v1/routes/{path:path}")
async def remove_route(path: str):
    """移除路由"""
    success = route_manager.remove_route(path)
    if success:
        return {"message": "路由移除成功"}
    else:
        raise HTTPException(status_code=404, detail="路由不存在")


@app.get("/api/v1/routes")
async def get_routes():
    """获取所有路由"""
    return route_manager.get_all_routes()


# ==================== 工具系统 API ====================

# 全局工具注册中心实例
_tool_registry = None

def get_tool_registry():
    """获取工具注册中心实例"""
    global _tool_registry
    if _tool_registry is None:
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from core.governance.unified_tool_registry import get_unified_registry
            _tool_registry = get_unified_registry()
            logger.info("✅ 工具注册中心已初始化")
        except Exception as e:
            logger.error(f"❌ 工具注册中心初始化失败: {e}")
    return _tool_registry


@app.get("/api/v1/tools")
async def list_tools(
    category: str = None,
    status: str = None,
    limit: int = 100
):
    """
    列出可用工具

    Args:
        category: 工具类别过滤 (builtin, mcp, search, utility, domain, agent)
        status: 工具状态过滤 (available, busy, error)
        limit: 返回数量限制
    """
    registry = get_tool_registry()
    if not registry:
        raise HTTPException(status_code=503, detail="工具注册中心未就绪")

    try:
        from core.governance.unified_tool_registry import ToolCategory, ToolStatus

        category_enum = ToolCategory(category) if category else None
        status_enum = ToolStatus(status) if status else None

        tools = registry.list_tools(category=category_enum, status=status_enum)

        return {
            "success": True,
            "data": {
                "tools": tools[:limit],
                "total": len(tools),
                "category": category,
                "status": status
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"列出工具失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出工具失败: {str(e)}") from e


@app.get("/api/v1/tools/{tool_id}")
async def get_tool_info(tool_id: str):
    """获取工具详细信息"""
    registry = get_tool_registry()
    if not registry:
        raise HTTPException(status_code=503, detail="工具注册中心未就绪")

    try:
        info = registry.get_tool_info(tool_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"工具不存在: {tool_id}")

        return {
            "success": True,
            "data": info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具信息失败 {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取工具信息失败: {str(e)}") from e


@app.post("/api/v1/tools/discover")
async def discover_tools(request: Request):
    """
    智能发现工具

    Body:
        query: 查询描述 (如 "搜索专利", "读取文件")
        category: 工具类别过滤 (可选)
        limit: 返回数量限制 (默认5)
        use_vector: 是否使用向量搜索 (默认False)
    """
    registry = get_tool_registry()
    if not registry:
        raise HTTPException(status_code=503, detail="工具注册中心未就绪")

    try:
        data = await request.json()
        query = data.get("query", "")
        category = data.get("category")
        limit = data.get("limit", 5)
        use_vector = data.get("use_vector", False)

        from core.governance.unified_tool_registry import ToolCategory

        category_enum = ToolCategory(category) if category else None

        tools = await registry.discover_tools(
            query=query,
            category=category_enum,
            limit=limit,
            use_vector=use_vector
        )

        return {
            "success": True,
            "data": {
                "query": query,
                "tools": tools,
                "found": len(tools),
                "category": category
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"工具发现失败: {e}")
        raise HTTPException(status_code=500, detail=f"工具发现失败: {str(e)}") from e


@app.post("/api/v1/tools/{tool_id}/execute")
async def execute_tool(tool_id: str, request: Request):
    """
    执行工具

    Body:
        parameters: 工具执行参数
        context: 执行上下文 (可选)
    """
    registry = get_tool_registry()
    if not registry:
        raise HTTPException(status_code=503, detail="工具注册中心未就绪")

    try:
        data = await request.json()
        parameters = data.get("parameters", {})
        context = data.get("context", {})

        result = await registry.execute_tool(tool_id, parameters, context)

        return {
            "success": result.success,
            "data": {
                "tool_id": tool_id,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "timestamp": result.timestamp.isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"工具执行失败 {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=f"工具执行失败: {str(e)}") from e


@app.get("/api/v1/tools/stats")
async def get_tool_statistics():
    """获取工具统计信息"""
    registry = get_tool_registry()
    if not registry:
        raise HTTPException(status_code=503, detail="工具注册中心未就绪")

    try:
        stats = registry.get_statistics()

        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"获取工具统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工具统计失败: {str(e)}") from e


# ==================== 法律世界模型 API ====================

    # 法律世界模型实例

    # 场景规划器实例

    def get_legal_world_generator():
        """获取法律世界模型生成器实例"""
        global legal_world_generator
        if legal_world_generator is None:
            try:
                from core.intelligence.legal_world_prompt_generator import LegalWorldPromptGenerator
                legal_world_generator = LegalWorldPromptGenerator()
                logger.info("✅ 法律世界模型初始化成功")
            except Exception as e:
                logger.error(f"❌ 法律世界模型初始化失败: {e}")
        return legal_world_generator

    def get_task_planner():
        """获取智能体任务规划器实例"""
        global task_planner
        if task_planner is None:
            try:
                from core.cognition.agentic_task_planner import AgenticTaskPlanner
                task_planner = AgenticTaskPlanner()
                logger.info("✅ 智能体任务规划器初始化成功")
            except Exception as e:
                logger.error(f"❌ 智能体任务规划器初始化失败: {e}")
        return task_planner

    @app.post("/api/v1/legal/prompt/generate")
    async def generate_legal_prompt(request: Request):
        """生成法律动态提示词"""
        try:
            data = await request.json()
            try:
                from core.intelligence.legal_world_prompt_generator import LegalWorldPromptGenerator
                LegalWorldPromptGenerator()
                logger.info("✅ 法律世界模型初始化成功")
            except Exception as e:
                logger.error(f"❌ 法律世界模型初始化失败: {e}")
                raise HTTPException(status_code=503, detail="法律世界模型未就绪") from e

            # 生成动态提示词
            from core.intelligence.legal_world_prompt_generator import LegalContext
            context = LegalContext(
                business_type=data.get("business_type", ""),
                domain=data.get("domain", "patent_law"),
                keywords=data.get("keywords", []),
                user_query=data.get("user_query", ""),
                urgency_level=data.get("urgency_level", "medium"),
                complexity_level=data.get("complexity_level", "medium")
            )

            from core.intelligence.legal_world_prompt_generator import DynamicPromptGenerator
            generator = DynamicPromptGenerator()
            dynamic_prompt = generator.generate_dynamic_prompt(context)

            return {
                "success": True,
                "data": {
                    "prompt": dynamic_prompt.get("prompt", ""),
                    "confidence_score": dynamic_prompt.get("confidence_score", 0.0),
                    "business_type": context.business_type,
                    "matched_rules_count": len(dynamic_prompt.get("matched_rules", []))
                },
                "message": "法律动态提示词生成成功",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"生成法律提示词失败: {e}")
            raise HTTPException(status_code=500, detail=f"生成法律提示词失败: {str(e)}") from e

    @app.post("/api/v1/legal/planner/plan")
    async def generate_execution_plan(request: Request):
        """生成智能体执行计划"""
        try:
            data = await request.json()
            planner = get_task_planner()

            if not planner:
                raise HTTPException(status_code=503, detail="场景规划器未就绪")

            # 生成执行计划
            context_data = {
                "goal": data.get("goal", ""),
                "domain": data.get("domain", "patent_law"),
                "complexity": data.get("complexity", "medium"),
                "available_agents": data.get("available_agents", [])
            }

            execution_plan = planner.plan_task(context_data)

            return {
                "success": True,
                "data": {
                    "execution_plan": {
                        "steps": [
                            {
                                "id": step.id,
                                "description": step.description,
                                "agent": step.agent,
                                "estimated_time": step.estimated_time,
                                "dependencies": step.dependencies,
                                "success_criteria": step.success_criteria,
                                "failure_recovery": step.failure_recovery
                            }
                            for step in execution_plan.steps
                        ],
                        "total_steps": len(execution_plan.steps),
                        "total_time": sum(step.estimated_time for step in execution_plan.steps)
                    },
                    "goal": context_data["goal"],
                    "domain": context_data["domain"]
                },
                "message": "智能体执行计划生成成功",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"生成执行计划失败: {e}")
            raise HTTPException(status_code=500, detail=f"生成执行计划失败: {str(e)}") from e

    @app.get("/api/v1/legal/health")
    async def legal_health_check():
        """法律世界模型健康检查"""
        try:
            generator = get_legal_world_generator()
            planner = get_task_planner()

            return {
                "status": "healthy",
                "components": {
                    "legal_world_prompt_generator": generator is not None,
                    "task_planner": planner is not None,
                    "neo4j": True,  # 假设Neo4j可用
                    "postgres": True,  # 假设PostgreSQL可用
                    "redis": True,  # 假设Redis可用
                    "qdrant": True   # 假设Qdrant可用
                },
                "message": "法律世界模型服务健康",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# ==================== 法律世界模型 API ====================

    # 法律世界模型实例

    # 场景规划器实例


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    """代理转发请求"""
    # 查找匹配的路由
    route = route_manager.find_route(f"/{path}", request.method)
    if not route:
        raise HTTPException(status_code=404, detail="路由未找到")

    # 获取健康的服务实例
    healthy_instances = service_registry.get_healthy_instances(route.service_name)
    if not healthy_instances:
        raise HTTPException(status_code=503, detail="服务不可用")

    # 负载均衡选择实例
    selected_instance = load_balancer.select_instance(healthy_instances, route.service_name)
    if not selected_instance:
        raise HTTPException(status_code=503, detail="无可用的服务实例")

    # 构建目标URL
    target_path = f"/{path}"
    if route.strip_prefix:
        # 移除路由前缀
        target_path = f"/{path}"

    target_url = f"{selected_instance.protocol}://{selected_instance.host}:{selected_instance.port}{target_path}"

    # 转发请求
    try:
        async with aiohttp.ClientSession() as session:
            # 准备请求头
            headers = dict(request.headers)
            headers.pop("host", None)  # 移除host头

            # 获取请求体
            body = await request.body()

            # 发送请求
            async with session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=body if body else None,
                timeout=aiohttp.ClientTimeout(total=route.timeout),
            ) as response:
                # 读取响应
                response_body = await response.read()

                # 构建响应
                return Response(
                    content=response_body,
                    status_code=response.status,
                    headers=dict(response.headers),
                    media_type=response.content_type,
                )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="网关超时") from None
    except Exception as e:
        logger.error(f"代理请求失败: {e}")
        raise HTTPException(status_code=502, detail="网关错误") from e


# ==================== 启动配置 ====================


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 创建必要的目录
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    # 启动后台任务
    asyncio.create_task(periodic_health_check())

    logger.info("Athena API Gateway 启动成功")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Athena API Gateway 正在关闭")


# ==================== 主函数 ====================

if __name__ == "__main__":
    # 创建必要目录
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    # 启动服务
    uvicorn.run(
        "athena_gateway:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info",
        access_log=True,
    )
