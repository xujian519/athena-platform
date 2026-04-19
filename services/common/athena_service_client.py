"""
Athena服务通信客户端库
Athena Service Communication Client Library
提供统一的服务间通信接口和标准
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel

# 配置日志
logger = logging.getLogger(__name__)

class ServiceStatus(str, Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    url: str
    port: int
    version: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: datetime | None = None
    health_endpoint: str = "/health"

class ServiceRequest(BaseModel):
    """标准服务请求"""
    service_name: str
    endpoint: str
    method: str = "GET"
    data: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    headers: dict[str, str] | None = None
    timeout: int = 30

class ServiceResponse(BaseModel):
    """标准服务响应"""
    success: bool
    status_code: int
    data: dict[str, Any] | None = None
    error: str | None = None
    response_time: float = 0.0
    timestamp: datetime

class AthenaServiceClient:
    """Athena服务通信客户端"""

    def __init__(self):
        self.services: dict[str, ServiceInfo] = {}
        self.http_client: httpx.AsyncClient | None = None
        self._initialize_default_services()

    def _initialize_default_services(self) -> Any:
        """初始化默认服务配置"""
        default_services = {
            "api-gateway": ServiceInfo(
                name="api-gateway",
                url="http://localhost",
                port=3000,
                version="1.0.0"
            ),
            "athena-platform": ServiceInfo(
                name="athena-platform",
                url="http://localhost",
                port=8001,
                version="2.0.0"
            ),
            "ai-models": ServiceInfo(
                name="ai-models",
                url="http://localhost",
                port=9000,
                version="1.0.0"
            ),
            "ai-services": ServiceInfo(
                name="ai-services",
                url="http://localhost",
                port=9001,
                version="1.0.0"
            ),
            "crawler-service": ServiceInfo(
                name="crawler-service",
                url="http://localhost",
                port=8003,
                version="2.0.0"
            ),
            "common-tools-service": ServiceInfo(
                name="common-tools-service",
                url="http://localhost",
                port=8007,
                version="1.0.0"
            ),
            "athena-iterative-search": ServiceInfo(
                name="athena-iterative-search",
                url="http://localhost",
                port=8008,
                version="2.0.0"
            ),
            "data-services": ServiceInfo(
                name="data-services",
                url="http://localhost",
                port=8005,
                version="1.0.0"
            ),
            "visualization-tools": ServiceInfo(
                name="visualization-tools",
                url="http://localhost",
                port=8006,
                version="1.0.0"
            ),
            "core-services": ServiceInfo(
                name="core-services",
                url="http://localhost",
                port=9001,
                version="1.0.0"
            )
        }

        self.services.update(default_services)

    async def initialize(self):
        """初始化客户端"""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        logger.info("Athena服务客户端初始化完成")

    async def close(self):
        """关闭客户端"""
        if self.http_client:
            await self.http_client.aclose()
        logger.info("Athena服务客户端已关闭")

    def register_service(self, service_info: ServiceInfo) -> Any:
        """注册新服务"""
        self.services[service_info.name] = service_info
        logger.info(f"注册服务: {service_info.name}")

    async def check_service_health(self, service_name: str) -> ServiceStatus:
        """检查服务健康状态"""
        if service_name not in self.services:
            logger.warning(f"未知服务: {service_name}")
            return ServiceStatus.UNKNOWN

        service = self.services[service_name]
        health_url = f"{service.url}:{service.port}{service.health_endpoint}"

        try:
            start_time = datetime.now()
            response = await self.http_client.get(health_url, timeout=5.0)
            response_time = (datetime.now() - start_time).total_seconds()

            if response.status_code == 200:
                service.status = ServiceStatus.HEALTHY
            else:
                service.status = ServiceStatus.DEGRADED

            service.last_check = datetime.now()
            logger.debug(f"服务 {service_name} 健康检查: {service.status.value} ({response_time:.2f}s)")
            return service.status

        except Exception as e:
            service.status = ServiceStatus.UNHEALTHY
            service.last_check = datetime.now()
            logger.error(f"服务 {service_name} 健康检查失败: {e}")
            return ServiceStatus.UNHEALTHY

    async def check_all_services(self) -> dict[str, ServiceStatus]:
        """检查所有服务健康状态"""
        tasks = [self.check_service_health(name) for name in self.services.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_status = {}
        for i, service_name in enumerate(self.services.keys()):
            if isinstance(results[i], Exception):
                health_status[service_name] = ServiceStatus.UNKNOWN
            else:
                health_status[service_name] = results[i]

        return health_status

    async def call_service(
        self,
        request: ServiceRequest
    ) -> ServiceResponse:
        """调用服务"""
        if not self.http_client:
            raise RuntimeError("客户端未初始化")

        if request.service_name not in self.services:
            raise ValueError(f"未知服务: {request.service_name}")

        service = self.services[request.service_name]
        service_url = f"{service.url}:{service.port}{request.endpoint}"

        # 准备请求头
        headers = request.headers or {}
        headers.update({
            "X-Service-Name": "athena-client",
            "X-Request-ID": f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(self)}",
            "Content-Type": "application/json"
        })

        try:
            start_time = datetime.now()

            # 发送请求
            if request.method.upper() == "GET":
                response = await self.http_client.get(
                    service_url,
                    params=request.params,
                    headers=headers,
                    timeout=request.timeout
                )
            elif request.method.upper() == "POST":
                response = await self.http_client.post(
                    service_url,
                    json=request.data,
                    params=request.params,
                    headers=headers,
                    timeout=request.timeout
                )
            elif request.method.upper() == "PUT":
                response = await self.http_client.put(
                    service_url,
                    json=request.data,
                    params=request.params,
                    headers=headers,
                    timeout=request.timeout
                )
            elif request.method.upper() == "DELETE":
                response = await self.http_client.delete(
                    service_url,
                    params=request.params,
                    headers=headers,
                    timeout=request.timeout
                )
            else:
                raise ValueError(f"不支持的HTTP方法: {request.method}")

            response_time = (datetime.now() - start_time).total_seconds()

            # 处理响应
            if response.status_code < 400:
                try:
                    data = response.json()
                except (json.JSONDecodeError, TypeError, ValueError):
                    data = {"text": response.text}

                return ServiceResponse(
                    success=True,
                    status_code=response.status_code,
                    data=data,
                    response_time=response_time,
                    timestamp=datetime.now()
                )
            else:
                return ServiceResponse(
                    success=False,
                    status_code=response.status_code,
                    error=response.text,
                    response_time=response_time,
                    timestamp=datetime.now()
                )

        except httpx.TimeoutException:
            return ServiceResponse(
                success=False,
                status_code=408,
                error="请求超时",
                response_time=request.timeout,
                timestamp=datetime.now()
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                status_code=500,
                error=str(e),
                response_time=0.0,
                timestamp=datetime.now()
            )

    # 便捷方法
    async def get(self, service_name: str, endpoint: str, params: dict | None = None) -> ServiceResponse:
        """GET请求"""
        request = ServiceRequest(
            service_name=service_name,
            endpoint=endpoint,
            method="GET",
            params=params
        )
        return await self.call_service(request)

    async def post(self, service_name: str, endpoint: str, data: dict | None = None) -> ServiceResponse:
        """POST请求"""
        request = ServiceRequest(
            service_name=service_name,
            endpoint=endpoint,
            method="POST",
            data=data
        )
        return await self.call_service(request)

    async def put(self, service_name: str, endpoint: str, data: dict | None = None) -> ServiceResponse:
        """PUT请求"""
        request = ServiceRequest(
            service_name=service_name,
            endpoint=endpoint,
            method="PUT",
            data=data
        )
        return await self.call_service(request)

    async def delete(self, service_name: str, endpoint: str) -> ServiceResponse:
        """DELETE请求"""
        request = ServiceRequest(
            service_name=service_name,
            endpoint=endpoint,
            method="DELETE"
        )
        return await self.call_service(request)

    # 高级功能
    async def broadcast_message(
        self,
        endpoint: str,
        message: dict[str, Any],
        services: list[str] | None = None
    ) -> dict[str, ServiceResponse]:
        """广播消息到多个服务"""
        if not services:
            services = list(self.services.keys())

        tasks = []
        for service_name in services:
            request = ServiceRequest(
                service_name=service_name,
                endpoint=endpoint,
                method="POST",
                data=message
            )
            tasks.append(self.call_service(request))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses = {}
        for i, service_name in enumerate(services):
            if isinstance(results[i], Exception):
                responses[service_name] = ServiceResponse(
                    success=False,
                    status_code=500,
                    error=str(results[i]),
                    timestamp=datetime.now()
                )
            else:
                responses[service_name] = results[i]

        return responses

    async def orchestrate_workflow(
        self,
        workflow_steps: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """执行工作流"""
        results = []

        for i, step in enumerate(workflow_steps):
            service_name = step.get("service")
            endpoint = step.get("endpoint")
            method = step.get("method", "POST")
            data = step.get("data", {})

            # 如果有依赖前一步的结果
            if "use_previous_result" in step and results:
                previous_result = results[-1]
                if previous_result.success:
                    data["previous_result"] = previous_result.data

            request = ServiceRequest(
                service_name=service_name,
                endpoint=endpoint,
                method=method,
                data=data
            )

            result = await self.call_service(request)
            results.append(result)

            # 如果失败且不允许继续
            if not result.success and not step.get("continue_on_failure", False):
                logger.error(f"工作流步骤 {i+1} 失败: {result.error}")
                break

        return {
            "total_steps": len(workflow_steps),
            "completed_steps": len(results),
            "success": all(r.success for r in results),
            "results": [asdict(r) for r in results]
        }

# 全局客户端实例
_service_client: AthenaServiceClient | None = None

async def get_service_client() -> AthenaServiceClient:
    """获取全局服务客户端实例"""
    global _service_client
    if _service_client is None:
        _service_client = AthenaServiceClient()
        await _service_client.initialize()
    return _service_client

# 装饰器：用于服务间通信
def service_call(service_name: str, endpoint: str, method: str = "POST") -> Any:
    """服务调用装饰器"""
    def decorator(func) -> None:
        async def wrapper(*args, **kwargs):
            client = await get_service_client()

            # 提取函数参数作为请求数据
            request_data = kwargs if kwargs else {}

            request = ServiceRequest(
                service_name=service_name,
                endpoint=endpoint,
                method=method,
                data=request_data
            )

            response = await client.call_service(request)

            if response.success:
                return response.data
            else:
                raise Exception(f"服务调用失败: {response.error}")

        return wrapper
    return decorator

# 使用示例
"""
# 初始化客户端
client = AthenaServiceClient()
await client.initialize()

# 简单调用
response = await client.get("athena-platform", "/health")
if response.success:
    print("服务健康")

# POST请求
response = await client.post("ai-services", "/api/v1/inference", {
    "model": "gpt-3.5-turbo",
    "prompt": "Hello, Athena!"
})

# 广播消息
responses = await client.broadcast_message(
    "/api/v1/notify",
    {"message": "System maintenance scheduled"},
    services=["api-gateway", "ai-services", "crawler-service"]
)

# 工作流执行
workflow = [
    {"service": "crawler-service", "endpoint": "/api/v1/crawl", "data": {"url": "https://example.com"}},
    {"service": "ai-services", "endpoint": "/api/v1/analyze", "data": {}, "use_previous_result": True},
    {"service": "athena-platform", "endpoint": "/api/v1/store", "data": {}, "use_previous_result": True}
]
result = await client.orchestrate_workflow(workflow)
"""
