#!/usr/bin/env python3
"""
跨系统接口网关 - 统一对外服务接口
Cross System Gateway - Unified External Service Interface

统一管理外部系统API,提供安全、高效、可扩展的接口访问

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import asyncio
import base64
import hashlib
import hmac
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import aiohttp


class SystemType(Enum):
    """系统类型"""

    PATENT_OFFICE = "patent_office"  # 专利局系统
    MEDIA_PLATFORM = "media_platform"  # 自媒体平台
    LEGAL_DATABASE = "legal_database"  # 法律数据库
    CLOUD_STORAGE = "cloud_storage"  # 云存储
    AI_SERVICE = "ai_service"  # AI服务
    DATABASE = "database"  # 数据库
    NOTIFICATION = "notification"  # 通知服务


class AuthType(Enum):
    """认证类型"""

    NONE = "none"  # 无认证
    API_KEY = "api_key"  # API Key
    OAUTH2 = "oauth2"  # OAuth2
    JWT = "jwt"  # JWT Token
    SIGNATURE = "signature"  # 签名验证
    BASIC_AUTH = "basic_auth"  # 基础认证


@dataclass
class EndpointConfig:
    """端点配置"""

    system_type: SystemType
    name: str
    base_url: str
    auth_type: AuthType
    auth_config: dict[str, Any] = field(default_factory=dict)
    rate_limit: int = 100  # 每秒请求数
    timeout: float = 30.0  # 超时时间(秒)
    retry_count: int = 3  # 重试次数
    circuit_breaker_threshold: int = 5  # 熔断阈值
    headers: dict[str, str] = field(default_factory=dict)
    health_check_url: str | None = None


@dataclass
class RequestRecord:
    """请求记录"""

    id: str
    endpoint: str
    method: str
    url: str
    headers: dict[str, str]
    body: str
    timestamp: datetime
    duration: float
    status_code: int
    response_size: int
    success: bool
    error: str | None = None


class CircuitBreaker:
    """熔断器"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        """调用函数,带熔断保护"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

            raise e


class RateLimiter:
    """速率限制器"""

    def __init__(self, max_requests: int, time_window: float = 1.0):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def acquire(self):
        """获取请求许可"""
        now = time.time()
        # 清理过期请求
        self.requests = [r for r in self.requests if now - r < self.time_window]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.requests.append(now)


class CrossSystemGateway:
    """跨系统接口网关"""

    def __init__(self):
        self.name = "小诺跨系统接口网关"
        self.version = "1.0.0"

        # 端点配置
        self.endpoints: dict[str, EndpointConfig] = {}

        # 熔断器
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        # 速率限制器
        self.rate_limiters: dict[str, RateLimiter] = {}

        # 会话管理
        self.session: aiohttp.ClientSession | None = None

        # 请求日志
        self.request_logs: list[RequestRecord] = []

        # 性能指标
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "p95_response_time": 0.0,
            "throughput": 0.0,
        }

        # 注册默认端点
        self._register_default_endpoints()

        print(f"🌐 {self.name} 初始化完成")

    def _register_default_endpoints(self) -> Any:
        """注册默认端点配置"""
        # 专利局API
        self.register_endpoint(
            EndpointConfig(
                system_type=SystemType.PATENT_OFFICE,
                name="CNIPA_API",
                base_url="https://api.cnipa.gov.cn/v1",
                auth_type=AuthType.API_KEY,
                auth_config={"api_key": "patent_api_key_placeholder"},
                rate_limit=50,
                timeout=30.0,
                health_check_url="/health",
            )
        )

        # 自媒体平台
        self.register_endpoint(
            EndpointConfig(
                system_type=SystemType.MEDIA_PLATFORM,
                name="WEIBO_PLATFORM",
                base_url="https://api.weibo.com/2",
                auth_type=AuthType.OAUTH2,
                auth_config={
                    "client_id": "weibo_client_id",
                    "client_secret": "weibo_client_secret",
                },
                rate_limit=100,
                timeout=10.0,
            )
        )

        # 法律数据库
        self.register_endpoint(
            EndpointConfig(
                system_type=SystemType.LEGAL_DATABASE,
                name="PKULAW_API",
                base_url="https://api.pkulaw.cn/v1",
                auth_type=AuthType.SIGNATURE,
                auth_config={"app_key": "pku_app_key", "secret_key": "pku_secret_key"},
                rate_limit=30,
                timeout=15.0,
            )
        )

        # AI服务
        self.register_endpoint(
            EndpointConfig(
                system_type=SystemType.AI_SERVICE,
                name="OPENAI_API",
                base_url="https://api.openai.com/v1",
                auth_type=AuthType.JWT,
                auth_config={"token": "openai_token_placeholder"},
                rate_limit=200,
                timeout=60.0,
            )
        )

        # 云存储
        self.register_endpoint(
            EndpointConfig(
                system_type=SystemType.CLOUD_STORAGE,
                name="ALIYUN_OSS",
                base_url="https://oss-cn-beijing.aliyuncs.com",
                auth_type=AuthType.SIGNATURE,
                auth_config={"access_key": "ali_access_key", "secret_key": "ali_secret_key"},
                rate_limit=1000,
                timeout=30.0,
            )
        )

        # 数据库
        self.register_endpoint(
            EndpointConfig(
                system_type=SystemType.DATABASE,
                name="PATENT_DB",
                base_url="http://localhost:5432",
                auth_type=AuthType.BASIC_AUTH,
                auth_config={"username": "patent_user", "password": "patent_pass"},
                rate_limit=500,
                timeout=5.0,
            )
        )

        # 通知服务
        self.register_endpoint(
            EndpointConfig(
                system_type=SystemType.NOTIFICATION,
                name="EMAIL_SERVICE",
                base_url="https://api.email-service.com/v1",
                auth_type=AuthType.API_KEY,
                auth_config={"api_key": "email_api_key"},
                rate_limit=20,
                timeout=10.0,
            )
        )

    async def initialize(self):
        """初始化网关"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=60.0)
            self.session = aiohttp.ClientSession(timeout=timeout)

        # 初始化熔断器和速率限制器
        for endpoint_id, config in self.endpoints.items():
            self.circuit_breakers[endpoint_id] = CircuitBreaker(
                failure_threshold=config.circuit_breaker_threshold
            )
            self.rate_limiters[endpoint_id] = RateLimiter(config.rate_limit)

        print("✅ 网关初始化完成")

    async def close(self):
        """关闭网关"""
        if self.session:
            await self.session.close()

    def register_endpoint(self, config: EndpointConfig) -> Any:
        """注册端点"""
        endpoint_id = f"{config.system_type.value}_{config.name}"
        self.endpoints[endpoint_id] = config
        print(f"📝 注册端点: {endpoint_id}")

    async def request(
        self,
        system_type: SystemType,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: str | bytes | None = None,
    ) -> dict[str, Any]:
        """发送HTTP请求"""
        # 查找端点配置
        endpoint_id = None
        endpoint_config = None

        for eid, config in self.endpoints.items():
            if config.system_type == system_type:
                endpoint_id = eid
                endpoint_config = config
                break

        if not endpoint_config:
            raise ValueError(f"未找到系统类型 {system_type} 的端点配置")

        # 构建完整URL
        url = f"{endpoint_config.base_url.rstrip('/')}/{path.lstrip('/')}"

        # 合并请求头
        request_headers = endpoint_config.headers.copy()
        if headers:
            request_headers.update(headers)

        # 添加认证信息
        auth_headers = self._get_auth_headers(endpoint_config)
        request_headers.update(auth_headers)

        # 速率限制
        await self.rate_limiters[endpoint_id].acquire()

        # 记录请求开始时间
        start_time = time.time()

        # 使用熔断器
        circuit_breaker = self.circuit_breakers[endpoint_id]
        request_id = hashlib.md5(f"{url}{time.time()}".encode(), usedforsecurity=False).hexdigest()

        try:
            response = await circuit_breaker.call(
                self._make_request,
                method,
                url,
                request_headers,
                params,
                json_data,
                data,
                endpoint_config.timeout,
            )

            response_data = await self._parse_response(response)

            # 记录成功请求
            duration = time.time() - start_time
            self._log_request(
                request_id,
                endpoint_id,
                method,
                url,
                request_headers,
                None,
                duration,
                response.status,
                len(str(response_data)),
                True,
                None,
            )

            # 更新指标
            self._update_metrics(duration, True)

            return response_data

        except Exception as e:
            # 记录失败请求
            duration = time.time() - start_time
            self._log_request(
                request_id,
                endpoint_id,
                method,
                url,
                request_headers,
                None,
                duration,
                0,
                0,
                False,
                str(e),
            )

            # 更新指标
            self._update_metrics(duration, False)

            raise e

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any],        json_data: dict[str, Any],        data: str | Optional[bytes],
        timeout: float,
    ):
        """执行HTTP请求"""
        async with self.session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            data=data,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            # 检查响应状态
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"HTTP {response.status}: {error_text}")

            return response

    async def _parse_response(self, response) -> dict[str, Any]:
        """解析响应"""
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            return await response.json()
        elif "text/" in content_type:
            return {"text": await response.text()}
        else:
            return {"data": await response.read()}

    def _get_auth_headers(self, config: EndpointConfig) -> dict[str, str]:
        """获取认证头"""
        if config.auth_type == AuthType.NONE:
            return {}

        elif config.auth_type == AuthType.API_KEY:
            key = config.auth_config.get("api_key")
            if key:
                return {"X-API-Key": key}

        elif config.auth_type == AuthType.JWT:
            token = config.auth_config.get("token")
            if token:
                return {"Authorization": f"Bearer {token}"}

        elif config.auth_type == AuthType.BASIC_AUTH:
            username = config.auth_config.get("username")
            password = config.auth_config.get("password")
            if username and password:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                return {"Authorization": f"Basic {credentials}"}

        elif config.auth_type == AuthType.SIGNATURE:
            # 简化的签名实现
            app_key = config.auth_config.get("app_key")
            secret_key = config.auth_config.get("secret_key")
            if app_key and secret_key:
                timestamp = str(int(time.time()))
                nonce = str(int(time.time() * 1000))
                signature = hmac.new(
                    secret_key.encode(), f"{timestamp}{nonce}".encode(), hashlib.sha256
                ).hexdigest()
                return {
                    "X-App-Key": app_key,
                    "X-Timestamp": timestamp,
                    "X-Nonce": nonce,
                    "X-Signature": signature,
                }

        return {}

    def _log_request(
        self,
        request_id: str,
        endpoint_id: str,
        method: str,
        url: str,
        headers: dict[str, str],
        body: str,
        duration: float,
        status_code: int,
        response_size: int,
        success: bool,
        error: str,
    ):
        """记录请求日志"""
        record = RequestRecord(
            id=request_id,
            endpoint=endpoint_id,
            method=method,
            url=url,
            headers=headers,
            body=body,
            timestamp=datetime.now(),
            duration=duration,
            status_code=status_code,
            response_size=response_size,
            success=success,
            error=error,
        )

        self.request_logs.append(record)

        # 保持日志数量在合理范围
        if len(self.request_logs) > 10000:
            self.request_logs = self.request_logs[-5000:]

    def _update_metrics(self, duration: float, success: bool) -> Any:
        """更新性能指标"""
        self.metrics["total_requests"] += 1

        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        # 更新平均响应时间
        total = self.metrics["total_requests"]
        current_avg = self.metrics["avg_response_time"]
        self.metrics["avg_response_time"] = (current_avg * (total - 1) + duration) / total

        # 计算吞吐量(过去1分钟的请求数)
        now = time.time()
        recent_requests = [r for r in self.request_logs if (now - r.timestamp.timestamp()) < 60]
        self.metrics["throughput"] = len(recent_requests) / 60.0

        # 计算P95响应时间
        if self.request_logs:
            durations = sorted([r.duration for r in self.request_logs])
            index = int(len(durations) * 0.95)
            self.metrics["p95_response_time"] = durations[min(index, len(durations) - 1)]

    async def health_check(self, endpoint_id: str | None = None) -> dict[str, Any]:
        """健康检查"""
        if endpoint_id:
            # 检查特定端点
            if endpoint_id not in self.endpoints:
                return {"status": "ERROR", "message": f"端点 {endpoint_id} 不存在"}

            config = self.endpoints[endpoint_id]
            if not config.health_check_url:
                return {"status": "OK", "message": "端点未配置健康检查"}

            try:
                url = f"{config.base_url}{config.health_check_url}"
                async with self.session.get(url, timeout=5.0) as response:
                    if response.status == 200:
                        return {
                            "status": "OK",
                            "response_time": response.headers.get("X-Response-Time"),
                        }
                    else:
                        return {"status": "ERROR", "http_status": response.status}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}
        else:
            # 检查所有端点
            results = {}
            for eid in self.endpoints:
                results[eid] = await self.health_check(eid)

            return results

    def get_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        return {
            "basic_metrics": self.metrics.copy(),
            "endpoint_count": len(self.endpoints),
            "circuit_breaker_status": {eid: cb.state for eid, cb in self.circuit_breakers.items()},
            "recent_errors": [
                {"timestamp": r.timestamp.isoformat(), "endpoint": r.endpoint, "error": r.error}
                for r in self.request_logs[-100:]
                if not r.success
            ],
        }

    async def batch_request(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量请求"""
        tasks = []
        for req in requests:
            task = self.request(
                system_type=req["system_type"],
                method=req["method"],
                path=req["path"],
                headers=req.get("headers"),
                params=req.get("params"),
                json_data=req.get("json_data"),
                data=req.get("data"),
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({"success": False, "error": str(result), "index": i})
            else:
                processed_results.append({"success": True, "data": result, "index": i})

        return processed_results


# 导出主类
__all__ = [
    "AuthType",
    "CircuitBreaker",
    "CrossSystemGateway",
    "EndpointConfig",
    "RateLimiter",
    "RequestRecord",
    "SystemType",
]
