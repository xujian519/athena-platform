"""
连接池管理器
提供HTTP连接池的管理和优化
"""

from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class PoolConfig:
    """连接池配置"""

    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 5.0
    max_timeout: float = 30.0
    retries: int = 3
    backoff_factor: float = 0.3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class ConnectionStats:
    """连接统计信息"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_success_time: datetime | None = None
    last_error_time: datetime | None = None
    consecutive_failures: int = 0
    circuit_open: bool = False
    circuit_open_time: datetime | None = None


class CircuitBreaker:
    """熔断器"""

    def __init__(self, threshold: int = 5, timeout: float = 60.0):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call_allowed(self) -> bool:
        """检查是否允许调用"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if (datetime.now() - self.last_failure_time).total_seconds() > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self) -> Any:
        """记录成功"""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> Any:
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.threshold:
            self.state = "OPEN"


class ConnectionPoolManager:
    """连接池管理器"""

    def __init__(self, config: PoolConfig | None = None):
        self.config = config or PoolConfig()
        self.pools: dict[str, httpx.AsyncClient] = {}
        self.stats: dict[str, ConnectionStats] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_client(self, base_url: str) -> httpx.AsyncClient:
        """获取或创建连接池客户端"""
        async with self._lock:
            if base_url not in self.pools:
                # 创建新的连接池
                limits = httpx.Limits(
                    max_keepalive_connections=self.config.max_keepalive_connections,
                    max_connections=self.config.max_connections,
                )

                timeout = httpx.Timeout(
                    connect=self.config.max_timeout,
                    read=self.config.max_timeout,
                    write=self.config.max_timeout,
                    pool=self.config.max_timeout,
                )

                client = httpx.AsyncClient(
                    limits=limits,
                    timeout=timeout,
                    http2=True,  # 启用HTTP/2
                    verify=False,  # 开发环境禁用SSL验证
                )

                self.pools[base_url] = client
                self.stats[base_url] = ConnectionStats()
                self.circuit_breakers[base_url] = CircuitBreaker(
                    threshold=self.config.circuit_breaker_threshold,
                    timeout=self.config.circuit_breaker_timeout,
                )

                logger.info(f"创建新的连接池: {base_url}")

            return self.pools[base_url]

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """发送HTTP请求"""
        base_url = self._extract_base_url(url)
        circuit_breaker = self.circuit_breakers.get(base_url)
        stats = self.stats.get(base_url)

        # 检查熔断器
        if circuit_breaker and not circuit_breaker.call_allowed():
            raise Exception(f"熔断器开启,暂时无法访问: {base_url}")

        # 获取客户端
        client = await self.get_client(base_url)

        # 记录请求开始
        start_time = time.time()
        stats.total_requests += 1

        # 重试机制
        last_exception = None
        for attempt in range(self.config.retries + 1):
            try:
                response = await client.request(method, url, **kwargs)

                # 更新统计信息
                response_time = time.time() - start_time
                stats.successful_requests += 1
                stats.last_success_time = datetime.now()
                stats.consecutive_failures = 0

                # 更新平均响应时间(指数移动平均)
                alpha = 0.1  # 平滑因子
                stats.avg_response_time = (
                    alpha * response_time + (1 - alpha) * stats.avg_response_time
                )

                # 记录成功
                if circuit_breaker:
                    circuit_breaker.record_success()

                # 检查响应状态
                if response.status_code >= 400:
                    stats.failed_requests += 1
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}", request=response.request, response=response
                    )

                return response

            except Exception as e:
                last_exception = e

                # 记录失败
                if attempt == self.config.retries:  # 最后一次尝试
                    stats.failed_requests += 1
                    stats.consecutive_failures += 1
                    stats.last_error_time = datetime.now()

                    if circuit_breaker:
                        circuit_breaker.record_failure()

                # 计算退避时间
                if attempt < self.config.retries:
                    backoff_time = self.config.backoff_factor * (2**attempt)
                    await asyncio.sleep(backoff_time)

        # 所有重试都失败
        raise last_exception

    def _extract_base_url(self, url: str) -> str:
        """提取基础URL"""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def close_all(self):
        """关闭所有连接池"""
        for client in self.pools.values():
            await client.aclose()
        self.pools.clear()
        logger.info("所有连接池已关闭")

    def get_stats(self) -> dict[str, dict[str, Any]]:
        """获取连接池统计信息"""
        stats_dict = {}
        for url, stats in self.stats.items():
            stats_dict[url] = {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "success_rate": (
                    stats.successful_requests / stats.total_requests * 100
                    if stats.total_requests > 0
                    else 0
                ),
                "avg_response_time": stats.avg_response_time,
                "last_success_time": (
                    stats.last_success_time.isoformat() if stats.last_success_time else None
                ),
                "consecutive_failures": stats.consecutive_failures,
                "circuit_open": stats.circuit_open,
                "connections": len(self.pools.get(url, []).__dict__.get("_connections", [])),
            }
        return stats_dict

    async def health_check(self) -> dict[str, bool]:
        """健康检查"""
        health_status = {}

        for base_url, client in self.pools.items():
            try:
                # 发送简单的健康检查请求
                response = await client.get(f"{base_url}/health", timeout=5.0)
                health_status[base_url] = response.status_code == 200
            except Exception:
                health_status[base_url] = False

        return health_status

    async def cleanup_idle_connections(self):
        """清理空闲连接"""
        for client in self.pools.values():
            # httpx会自动管理连接,这里主要是记录日志
            active_connections = len(client._mounts)
            logger.debug(f"活跃连接数: {active_connections}")

    async def get_pool_info(self) -> dict[str, Any]:
        """获取连接池详细信息"""
        pool_info = {
            "config": {
                "max_connections": self.config.max_connections,
                "max_keepalive_connections": self.config.max_keepalive_connections,
                "keepalive_expiry": self.config.keepalive_expiry,
                "max_timeout": self.config.max_timeout,
                "retries": self.config.retries,
            },
            "pools": {},
            "stats": self.get_stats(),
        }

        for base_url, client in self.pools.items():
            pool_info["pools"][base_url] = {
                "max_connections": client._limits.max_connections,
                "max_keepalive_connections": client._limits.max_keepalive_connections,
                "timeout": client._timeout,
                "http2": client._http2,
            }

        return pool_info


# 全局连接池管理器
connection_manager = ConnectionPoolManager()


# 便捷函数
async def http_request(method: str, url: str, **kwargs) -> httpx.Response:
    """便捷的HTTP请求函数"""
    return await connection_manager.request(method, url, **kwargs)


async def http_get(url: str, **kwargs) -> httpx.Response:
    """GET请求"""
    return await http_request("GET", url, **kwargs)


async def http_post(url: str, **kwargs) -> httpx.Response:
    """POST请求"""
    return await http_request("POST", url, **kwargs)


async def http_put(url: str, **kwargs) -> httpx.Response:
    """PUT请求"""
    return await http_request("PUT", url, **kwargs)


async def http_delete(url: str, **kwargs) -> httpx.Response:
    """DELETE请求"""
    return await http_request("DELETE", url, **kwargs)


# 定期清理任务
async def start_cleanup_task():
    """启动定期清理任务"""
    while True:
        await connection_manager.cleanup_idle_connections()
        await asyncio.sleep(300)  # 每5分钟清理一次
