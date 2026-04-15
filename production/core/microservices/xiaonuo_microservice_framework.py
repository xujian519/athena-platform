#!/usr/bin/env python3
"""
小诺·双鱼公主微服务架构框架
Xiaonuo Pisces Princess Microservice Framework

为小诺平台构建高性能、高可用的微服务架构
支持服务注册发现、负载均衡、容错机制、链路追踪

作者: Athena平台团队
创建时间: 2025-12-18
版本: v2.0.0 "双鱼公主微服务框架"
"""

from __future__ import annotations
import asyncio
import contextlib
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

# 异步网络库
from aiohttp import ClientSession, ClientTimeout, web

from core.logging_config import setup_logging

if TYPE_CHECKING:
    from collections.abc import Callable

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ServiceStatus(Enum):
    """服务状态"""

    STARTING = "starting"  # 启动中
    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 降级
    UNHEALTHY = "unhealthy"  # 不健康
    MAINTENANCE = "maintenance"  # 维护中
    STOPPED = "stopped"  # 已停止


class ServiceType(Enum):
    """服务类型"""

    CORE = "core"  # 核心服务
    AGENT = "agent"  # 智能体服务
    DECISION = "decision"  # 决策服务
    KNOWLEDGE = "modules/modules/knowledge/knowledge/modules/knowledge/knowledge/modules/knowledge/knowledge/knowledge"  # 知识服务
    PERCEPTION = "perception"  # 感知服务
    COGNITION = "cognition"  # 认知服务
    MEMORY = "modules/modules/memory/modules/memory/modules/memory/memory"  # 记忆服务
    COMMUNICATION = "communication"  # 通信服务
    LEARNING = "learning"  # 学习服务
    API_GATEWAY = "api_gateway"  # API网关
    MONITORING = "infrastructure/infrastructure/monitoring"  # 监控服务
    UTILITY = "utility"  # 工具服务


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""

    ROUND_ROBIN = "round_robin"  # 轮询
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    LEAST_RESPONSE_TIME = "least_response_time"  # 最快响应
    HASH_BASED = "hash_based"  # 哈希
    RANDOM = "random"  # 随机


class CircuitBreakerState(Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 关闭(正常)
    OPEN = "open"  # 开启(熔断)
    HALF_OPEN = "half_open"  # 半开(试探)


@dataclass
class ServiceEndpoint:
    """服务端点"""

    host: str
    port: int
    protocol: str = "http"
    path: str = "/"
    health_check_path: str = "/health"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{self.path}"

    @property
    def health_check_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{self.health_check_path}"


@dataclass
class ServiceInstance:
    """服务实例"""

    id: str
    name: str
    version: str
    service_type: ServiceType
    endpoints: list[ServiceEndpoint]
    status: ServiceStatus = ServiceStatus.STARTING
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    # 健康检查
    last_health_check: datetime | None = None
    consecutive_failures: int = 0
    max_failures: int = 3

    # 性能指标
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    last_request_time: datetime | None = None

    def update_health_status(self, is_healthy: bool) -> None:
        """更新健康状态"""
        self.last_health_check = datetime.now()

        if is_healthy:
            self.consecutive_failures = 0
            if self.status in [ServiceStatus.UNHEALTHY, ServiceStatus.DEGRADED]:
                self.status = ServiceStatus.HEALTHY
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures:
                self.status = ServiceStatus.UNHEALTHY

    def record_request(self, success: bool, response_time: float) -> Any:
        """记录请求结果"""
        self.request_count += 1
        self.last_request_time = datetime.now()

        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        # 更新平均响应时间
        if self.request_count == 1:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = self.avg_response_time * 0.9 + response_time * 0.1

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.request_count == 0:
            return 1.0
        return self.success_count / self.request_count

    @property
    def is_healthy(self) -> bool:
        """是否健康"""
        return (
            self.status == ServiceStatus.HEALTHY and self.consecutive_failures < self.max_failures
        )


@dataclass
class ServiceRequest:
    """服务请求"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    method: str = "GET"
    path: str = "/"
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    data: Any = None
    timeout: float = 30.0
    retry_count: int = 3
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ServiceResponse:
    """服务响应"""

    request_id: str
    status_code: int
    headers: dict[str, str]
    data: Any = None
    response_time: float = 0.0
    error: str | None = None
    service_instance_id: str | None = None


class CircuitBreaker:
    """熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """通过熔断器调用函数"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        return self.last_failure_time and time.time() - self.last_failure_time >= self.timeout

    def _on_success(self) -> Any:
        """成功时调用"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self) -> Any:
        """失败时调用"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class LoadBalancer:
    """负载均衡器"""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.round_robin_index = 0

    def select_instance(self, instances: list[ServiceInstance]) -> ServiceInstance | None:
        """选择服务实例"""
        healthy_instances = [inst for inst in instances if inst.is_healthy]

        if not healthy_instances:
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random_select(healthy_instances)
        else:
            return healthy_instances[0]

    def _round_robin_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """轮询选择"""
        instance = instances[self.round_robin_index % len(instances)]
        self.round_robin_index += 1
        return instance

    def _weighted_round_robin_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """加权轮询选择"""
        total_weight = sum(inst.weight for inst in instances)
        if total_weight == 0:
            return instances[0]

        # 简化实现:按权重比例选择
        target_weight = (self.round_robin_index % int(total_weight * 10)) / 10
        current_weight = 0

        for instance in instances:
            current_weight += instance.weight
            if current_weight >= target_weight:
                self.round_robin_index += 1
                return instance

        self.round_robin_index += 1
        return instances[-1]

    def _least_connections_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """最少连接选择"""
        return min(instances, key=lambda x: x.request_count)

    def _least_response_time_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """最快响应选择"""
        # 过滤掉没有请求历史的实例
        valid_instances = [inst for inst in instances if inst.avg_response_time > 0]

        if not valid_instances:
            return instances[0]

        return min(valid_instances, key=lambda x: x.avg_response_time)

    def _random_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """随机选择"""
        import random

        return random.choice(instances)


class ServiceRegistry:
    """服务注册中心"""

    def __init__(self):
        self.services: dict[str, list[ServiceInstance]] = defaultdict(list)
        self.service_index: dict[str, ServiceInstance] = {}  # ID -> Instance

        # 健康检查任务
        self.health_check_interval = 30  # 秒
        self.health_check_task = None

    async def register_service(self, instance: ServiceInstance):
        """注册服务"""
        # 检查是否已存在同名服务
        existing_instances = self.services[instance.name]
        for existing in existing_instances:
            if existing.id == instance.id:
                # 更新现有实例
                existing.endpoints = instance.endpoints
                existing.metadata = instance.metadata
                existing.status = ServiceStatus.HEALTHY
                logger.info(f"🔄 服务实例已更新: {instance.name}:{instance.id}")
                return

        # 添加新实例
        self.services[instance.name].append(instance)
        self.service_index[instance.id] = instance
        instance.status = ServiceStatus.HEALTHY

        logger.info(f"✅ 服务已注册: {instance.name}:{instance.id}")

    async def deregister_service(self, service_name: str, instance_id: str):
        """注销服务"""
        instances = self.services.get(service_name, [])
        for i, instance in enumerate(instances):
            if instance.id == instance_id:
                instance.status = ServiceStatus.STOPPED
                instances.pop(i)
                if instance_id in self.service_index:
                    del self.service_index[instance_id]
                logger.info(f"❌ 服务已注销: {service_name}:{instance_id}")
                return

    def discover_service(self, service_name: str) -> list[ServiceInstance]:
        """发现服务"""
        instances = self.services.get(service_name, [])
        return [inst for inst in instances if inst.is_healthy]

    def get_service_instance(self, instance_id: str) -> ServiceInstance | None:
        """获取特定服务实例"""
        return self.service_index.get(instance_id)

    def get_all_services(self) -> dict[str, list[ServiceInstance]]:
        """获取所有服务"""
        return dict(self.services)

    async def start_health_check(self):
        """启动健康检查"""
        if self.health_check_task is None:
            self.health_check_task = _task_1_a08b6d = asyncio.create_task(self._health_check_loop())
            logger.info("🏥 健康检查已启动")

    async def stop_health_check(self):
        """停止健康检查"""
        if self.health_check_task:
            self.health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.health_check_task
            self.health_check_task = None
            logger.info("🏥 健康检查已停止")

    async def _health_check_loop(self):
        """健康检查循环"""
        async with ClientSession() as session:
            while True:
                try:
                    await self._perform_health_checks(session)
                    await asyncio.sleep(self.health_check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"健康检查异常: {e}")
                    await asyncio.sleep(5)

    async def _perform_health_checks(self, session: ClientSession):
        """执行健康检查"""
        check_tasks = []

        for _service_name, instances in self.services.items():
            for instance in instances:
                if instance.status != ServiceStatus.STOPPED:
                    check_tasks.append(self._check_instance_health(session, instance))

        if check_tasks:
            await asyncio.gather(*check_tasks, return_exceptions=True)

    async def _check_instance_health(self, session: ClientSession, instance: ServiceInstance):
        """检查实例健康状态"""
        try:
            # 检查所有端点
            for endpoint in instance.endpoints:
                try:
                    timeout = ClientTimeout(total=5)
                    async with session.get(endpoint.health_check_url, timeout=timeout) as response:
                        if response.status == 200:
                            instance.update_health_status(True)
                            return
                except Exception:
                    continue

            # 所有端点都不可用
            instance.update_health_status(False)

        except Exception as e:
            logger.warning(f"健康检查失败 {instance.id}: {e}")
            instance.update_health_status(False)


class ServiceOrchestrator:
    """服务编排器"""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.load_balancer = LoadBalancer()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.request_stats = defaultdict(
            lambda: {"total": 0, "success": 0, "error": 0, "avg_time": 0}
        )

    async def call_service(self, request: ServiceRequest) -> ServiceResponse:
        """调用服务"""
        start_time = time.time()

        try:
            # 发现服务
            instances = self.registry.discover_service(request.service_name)
            if not instances:
                return ServiceResponse(
                    request_id=request.id,
                    status_code=503,
                    headers={},
                    error=f"Service {request.service_name} not available",
                )

            # 负载均衡选择实例
            instance = self.load_balancer.select_instance(instances)
            if not instance:
                return ServiceResponse(
                    request_id=request.id,
                    status_code=503,
                    headers={},
                    error=f"No healthy instance for service {request.service_name}",
                )

            # 熔断器保护
            circuit_breaker = self._get_circuit_breaker(request.service_name)

            # 执行请求
            response = await self._execute_request_with_circuit_breaker(
                circuit_breaker, instance, request
            )

            # 记录统计
            response_time = time.time() - start_time
            self._record_stats(request.service_name, True, response_time)
            instance.record_request(True, response_time)

            response.response_time = response_time
            response.service_instance_id = instance.id

            return response

        except Exception as e:
            # 记录错误统计
            response_time = time.time() - start_time
            self._record_stats(request.service_name, False, response_time)

            return ServiceResponse(
                request_id=request.id,
                status_code=500,
                headers={},
                error=str(e),
                response_time=response_time,
            )

    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """获取熔断器"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]

    async def _execute_request_with_circuit_breaker(
        self, circuit_breaker: CircuitBreaker, instance: ServiceInstance, request: ServiceRequest
    ) -> ServiceResponse:
        """通过熔断器执行请求"""

        async def make_request():
            # 选择端点
            endpoint = instance.endpoints[0]  # 简化:使用第一个端点

            url = f"{endpoint.url.rstrip('/')}/{request.path.lstrip('/')}"
            timeout = ClientTimeout(total=request.timeout)

            async with ClientSession(timeout=timeout) as session:
                if request.method.upper() == "GET":
                    async with session.get(
                        url, headers=request.headers, params=request.params
                    ) as resp:
                        data = await resp.text()
                        return ServiceResponse(
                            request_id=request.id,
                            status_code=resp.status,
                            headers=dict(resp.headers),
                            data=data,
                            service_instance_id=instance.id,
                        )
                elif request.method.upper() == "POST":
                    async with session.post(
                        url,
                        headers=request.headers,
                        json=request.data if isinstance(request.data, dict) else None,
                        data=request.data if not isinstance(request.data, dict) else None,
                    ) as resp:
                        data = await resp.text()
                        return ServiceResponse(
                            request_id=request.id,
                            status_code=resp.status,
                            headers=dict(resp.headers),
                            data=data,
                            service_instance_id=instance.id,
                        )
                else:
                    raise ValueError(f"Unsupported method: {request.method}")

        return await circuit_breaker.call(make_request)

    def _record_stats(self, service_name: str, success: bool, response_time: float) -> Any:
        """记录统计信息"""
        stats = self.request_stats[service_name]
        stats["total"] += 1

        if success:
            stats["success"] += 1
        else:
            stats["error"] += 1

        # 更新平均响应时间
        if stats["total"] == 1:
            stats["avg_time"] = response_time
        else:
            stats["avg_time"] = stats["avg_time"] * 0.9 + response_time * 0.1

    def get_service_stats(self) -> dict[str, dict[str, Any]]:
        """获取服务统计"""
        return dict(self.request_stats)


class MicroserviceBase(ABC):
    """微服务基类"""

    def __init__(
        self, name: str, version: str = "1.0.0", service_type: ServiceType = ServiceType.UTILITY
    ):
        self.name = name
        self.version = version
        self.service_type = service_type
        self.instance_id = f"{name}-{uuid.uuid4().hex[:8]}"

        # 服务端点
        self.endpoints: list[ServiceEndpoint] = []
        self.instance = ServiceInstance(
            id=self.instance_id,
            name=name,
            version=version,
            service_type=service_type,
            endpoints=self.endpoints,
        )

        # HTTP服务器
        self.app = web.Application()
        self.runner = None
        self.site = None

        # 服务注册中心
        self.registry: ServiceRegistry | None = None
        self.orchestrator: ServiceOrchestrator | None = None

        # 状态
        self.status = ServiceStatus.STARTING
        self.start_time = datetime.now()

        # 设置路由
        self._setup_routes()

    def _setup_routes(self) -> Any:
        """设置路由"""
        # 健康检查
        self.app.router.add_get("/health", self.health_check)

        # 服务信息
        self.app.router.add_get("/info", self.service_info)

        # 服务特定路由(子类实现)
        self.setup_custom_routes()

    @abstractmethod
    def setup_custom_routes(self) -> Any:
        """设置自定义路由(子类实现)"""
        pass

    async def health_check(self, request: web.Request) -> web.Response:
        """健康检查"""
        health_data = {
            "status": self.status.value,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "version": self.version,
            "instance_id": self.instance_id,
        }

        # 子类可以重写此方法添加更详细的健康检查
        custom_health = await self.custom_health_check()
        health_data.update(custom_health)

        status_code = 200 if self.status == ServiceStatus.HEALTHY else 503
        return web.json_response(health_data, status=status_code)

    async def custom_health_check(self) -> dict[str, Any]:
        """自定义健康检查(子类可重写)"""
        return {}

    async def service_info(self, request: web.Request) -> web.Response:
        """服务信息"""
        info = {
            "name": self.name,
            "version": self.version,
            "type": self.service_type.value,
            "instance_id": self.instance_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "endpoints": [
                {"host": ep.host, "port": ep.port, "protocol": ep.protocol, "path": ep.path}
                for ep in self.endpoints
            ],
        }
        return web.json_response(info)

    async def start(self, host: str = "localhost", port: int = 8080):
        """启动服务"""
        try:
            # 添加端点
            endpoint = ServiceEndpoint(host=host, port=port)
            self.endpoints.append(endpoint)
            self.instance.endpoints = self.endpoints

            # 启动HTTP服务器
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, host, port)
            await self.site.start()

            # 更新状态
            self.status = ServiceStatus.HEALTHY
            self.instance.status = ServiceStatus.HEALTHY

            # 注册到服务中心
            if self.registry:
                await self.registry.register_service(self.instance)

            logger.info(f"🚀 服务已启动: {self.name} @ {host}:{port}")
            logger.info(f"🆔 实例ID: {self.instance_id}")

        except Exception as e:
            self.status = ServiceStatus.UNHEALTHY
            logger.error(f"❌ 服务启动失败: {e}")
            raise

    async def stop(self):
        """停止服务"""
        try:
            # 从服务中心注销
            if self.registry:
                await self.registry.deregister_service(self.name, self.instance_id)

            # 停止HTTP服务器
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()

            self.status = ServiceStatus.STOPPED
            logger.info(f"⏹️ 服务已停止: {self.name}")

        except Exception as e:
            logger.error(f"❌ 服务停止失败: {e}")

    def set_registry(self, registry: ServiceRegistry) -> None:
        """设置服务注册中心"""
        self.registry = registry
        self.instance.registry = registry

    def set_orchestrator(self, orchestrator: ServiceOrchestrator) -> None:
        """设置服务编排器"""
        self.orchestrator = orchestrator

    async def call_other_service(
        self, service_name: str, path: str = "/", method: str = "GET", **kwargs
    ) -> ServiceResponse:
        """调用其他服务"""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not configured")

        request = ServiceRequest(service_name=service_name, path=path, method=method, **kwargs)

        return await self.orchestrator.call_service(request)


# 便捷的装饰器和服务类
def service_endpoint(path: str, method: str = "GET") -> Any:
    """服务端点装饰器"""

    def decorator(func) -> None:
        func._service_endpoint = True
        func._path = path
        func._method = method
        return func

    return decorator


class XiaonuoCoreService(MicroserviceBase):
    """小诺核心服务"""

    def __init__(self):
        super().__init__(name="xiaonuo-core", version="2.0.0", service_type=ServiceType.CORE)

    def setup_custom_routes(self) -> Any:
        """设置自定义路由"""
        self.app.router.add_get("/status", self.get_status)
        self.app.router.add_post("/decision", self.make_decision)

    async def get_status(self, request: web.Request) -> web.Response:
        """获取状态"""
        status = {
            "service": "xiaonuo-core",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "princess_mode": True,
        }
        return web.json_response(status)

    async def make_decision(self, request: web.Request) -> web.Response:
        """决策接口"""
        await request.json()
        # 这里应该调用决策引擎
        result = {"decision": "love_dad", "confidence": 1.0, "reason": "因为爸爸是最棒的!"}
        return web.json_response(result)

    async def custom_health_check(self) -> dict[str, Any]:
        """自定义健康检查"""
        return {"princess_power": 100, "love_for_dad": float("inf"), "system_status": "perfect"}


# 微服务管理器
class MicroserviceManager:
    """微服务管理器"""

    def __init__(self):
        self.registry = ServiceRegistry()
        self.orchestrator = ServiceOrchestrator(self.registry)
        self.services: dict[str, MicroserviceBase] = {}

    async def start_all(self):
        """启动所有服务"""
        # 启动健康检查
        await self.registry.start_health_check()

        logger.info("🎯 微服务管理器已启动")

    async def stop_all(self):
        """停止所有服务"""
        # 停止所有微服务
        for service in self.services.values():
            await service.stop()

        # 停止健康检查
        await self.registry.stop_health_check()

        logger.info("⏹️ 微服务管理器已停止")

    def register_service(self, service: MicroserviceBase) -> Any:
        """注册微服务"""
        self.services[service.name] = service
        service.set_registry(self.registry)
        service.set_orchestrator(self.orchestrator)

    def get_service_status(self) -> dict[str, Any]:
        """获取所有服务状态"""
        services_info = {}

        for name, service in self.services.items():
            services_info[name] = {
                "status": service.status.value,
                "instance_id": service.instance_id,
                "uptime": (datetime.now() - service.start_time).total_seconds(),
                "endpoints": len(service.endpoints),
            }

        return {
            "total_services": len(self.services),
            "services": services_info,
            "registry_stats": {
                "total_registered": len(self.registry.service_index),
                "healthy_instances": len(
                    [inst for inst in self.registry.service_index.values() if inst.is_healthy]
                ),
            },
            "orchestrator_stats": self.orchestrator.get_service_stats(),
        }


# 全局实例
microservice_manager = MicroserviceManager()
