#!/usr/bin/env python3
"""
服务注册模块
Service Registry Module for Browser Automation Service

实现服务自动注册到统一网关

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

import aiohttp
from config.settings import logger, settings


class ServiceRegistryClient:
    """
    服务注册客户端

    负责与统一网关的服务发现系统通信
    """

    def __init__(
        self,
        gateway_url: str | None = None,
        service_discovery_url: str | None = None,
    ):
        """
        初始化服务注册客户端

        Args:
            gateway_url: 网关URL
            service_discovery_url: 服务发现API URL
        """
        self.gateway_url = gateway_url or os.getenv(
            "ATHENA_GATEWAY_URL",
            "http://localhost:8005",
        )

        self._http_client: aiohttp.ClientSession | None = None
        self._registered = False
        self._service_id: str | None = None

        # 从环境变量获取服务信息
        self.service_name = settings.SERVICE_NAME
        self.service_host = os.getenv("SERVICE_HOST", "localhost")
        self.service_port = settings.PORT
        self.service_version = settings.VERSION

    async def _get_http_client(self) -> aiohttp.ClientSession:
        """获取HTTP客户端"""
        if self._http_client is None or self._http_client.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._http_client = aiohttp.ClientSession(timeout=timeout)
        return self._http_client

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ):
        """执行HTTP请求"""
        client = await self._get_http_client()
        try:
            async with client.request(method, url, **kwargs) as response:
                yield response
                response.raise_for_status()
        except Exception as e:
            logger.error(f"HTTP请求失败: {method} {url} - {e}")
            raise

    async def register_service(self) -> dict[str, Any]:
        """
        注册服务到网关

        Returns:
            dict: 注册结果
        """
        try:
            # 构建服务注册数据（匹配统一网关的格式）
            service_data = {
                "services": [
                    {
                        "name": self.service_name,
                        "host": self.service_host,
                        "port": self.service_port,
                        "protocol": "http",
                        "health_check_path": "/health",
                        "metadata": {
                            "version": self.service_version,
                            "author": "小诺·双鱼公主",
                            "description": "浏览器自动化服务 - 基于Playwright的浏览器自动化API",
                            "capabilities": self._get_service_capabilities(),
                            "environment": settings.ENVIRONMENT,
                            "endpoints": self._get_service_endpoints(),
                            "tags": self._get_service_tags(),
                        },
                    }
                ],
            }

            # 发送注册请求到统一网关的批量注册端点
            async with self._request(
                "POST",
                f"{self.gateway_url}/api/services/batch_register",
                json=service_data,
            ) as response:
                result = await response.json()

                # 统一网关返回格式: {"success": true, "data": {"count": 1, ...}}
                if result.get("success"):
                    # 从响应中获取实际的服务ID
                    data = result.get("data", {})
                    registered_services = data.get("data", [])
                    if registered_services:
                        self._service_id = registered_services[0].get("id")
                    else:
                        self._service_id = f"{self.service_name}:{self.service_host}:{self.service_port}:0"

                    self._registered = True
                    logger.info(
                        f"✅ 服务已注册到网关: {self.service_name} "
                        f"(ID: {self._service_id})"
                    )
                    return {
                        "success": True,
                        "service_id": self._service_id,
                        "message": "Service registered successfully"
                    }
                else:
                    logger.error(f"❌ 服务注册失败: {result}")
                    return {"success": False, "message": str(result)}

        except Exception as e:
            logger.error(f"❌ 注册服务时发生异常: {e}")
            return {"success": False, "message": str(e)}

    async def deregister_service(self) -> dict[str, Any]:
        """
        从网关注销服务

        Returns:
            dict: 注销结果
        """
        try:
            if not self._registered or not self._service_id:
                return {"success": True, "message": "服务未注册"}

            # 发送注销请求到统一网关
            async with self._request(
                "DELETE",
                f"{self.gateway_url}/api/services/instances/{self._service_id}",
            ) as response:
                await response.json()

                # 统一网关返回格式: {"success": true, "data": {...}}
                self._registered = False
                old_id = self._service_id
                self._service_id = None
                logger.info(
                    f"✅ 服务已从网关注销: {self.service_name} (旧ID: {old_id})"
                )
                return {"success": True, "message": "Service deregistered successfully"}

        except Exception as e:
            # 即使失败也清空本地状态
            self._registered = False
            old_id = self._service_id
            self._service_id = None
            logger.warning(f"⚠️ 服务注销时出错: {e}，已清空本地状态")
            return {"success": True, "message": "Local state cleared"}

    async def send_heartbeat(self) -> dict[str, Any]:
        """
        发送心跳到网关（更新实例）

        Returns:
            dict: 心跳结果
        """
        try:
            if not self._registered or not self._service_id:
                return {"success": False, "message": "服务未注册"}

            # 发送心跳（更新服务实例状态）
            async with self._request(
                "PUT",
                f"{self.gateway_url}/api/services/instances/{self._service_id}",
                json={"status": "UP"},
            ) as response:
                result = await response.json()
                return result

        except Exception as e:
            logger.warning(f"⚠️ 发送心跳失败: {e}")
            return {"success": False, "message": str(e)}

    async def health_check_gateway(self) -> dict[str, Any]:
        """
        检查网关健康状态

        Returns:
            dict: 网关健康状态
        """
        try:
            async with self._request("GET", f"{self.gateway_url}/health") as response:
                return await response.json()
        except Exception as e:
            logger.error(f"❌ 网关健康检查失败: {e}")
            return {"status": "unreachable", "error": str(e)}

    def _generate_service_id(self) -> str:
        """生成服务ID"""
        import uuid

        return f"{self.service_name}-{uuid.uuid4().hex[:12]}"

    def _get_service_endpoints(self) -> list[str]:
        """获取服务端点列表"""
        return [
            "/api/v1/navigate",
            "/api/v1/click",
            "/api/v1/fill",
            "/api/v1/screenshot",
            "/api/v1/content",
            "/api/v1/evaluate",
            "/api/v1/task",
            "/api/v1/status",
            "/api/v1/config",
            "/health",
        ]

    def _get_service_tags(self) -> list[str]:
        """获取服务标签"""
        tags = [
            "browser",
            "automation",
            "playwright",
            "web-scraping",
            "testing",
        ]

        if settings.ENVIRONMENT == "production":
            tags.append("production")
        else:
            tags.append("development")

        if settings.BROWSER_HEADLESS:
            tags.append("headless")
        else:
            tags.append("headed")

        return tags

    def _get_service_capabilities(self) -> list[str]:
        """获取服务能力"""
        return [
            "page_navigation",
            "element_interaction",
            "form_filling",
            "screenshot",
            "content_extraction",
            "javascript_execution",
            "natural_language_task",
            "multi_session",
            "health_check",
        ]

    async def close(self):
        """关闭客户端"""
        if self._http_client and not self._http_client.closed:
            await self._http_client.close()

    @property
    def is_registered(self) -> bool:
        """检查服务是否已注册"""
        return self._registered

    @property
    def service_id(self) -> str | None:
        """获取服务ID"""
        return self._service_id


# 心跳维护任务
class HeartbeatManager:
    """心跳管理器"""

    def __init__(
        self,
        registry_client: ServiceRegistryClient,
        interval: int = 30,  # 心跳间隔（秒）
    ):
        """
        初始化心跳管理器

        Args:
            registry_client: 服务注册客户端
            interval: 心跳间隔
        """
        self.registry_client = registry_client
        self.interval = interval
        self._running = False
        self._heartbeat_task: asyncio.Task | None = None

    async def start(self):
        """启动心跳任务"""
        if self._running:
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info(f"💓 心跳任务已启动 (间隔: {self.interval}秒)")

    async def stop(self):
        """停止心跳任务"""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        logger.info("💓 心跳任务已停止")

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                await asyncio.sleep(self.interval)

                if not self._running:
                    break

                # 发送心跳
                result = await self.registry_client.send_heartbeat()

                if result.get("success"):
                    logger.debug(f"💓 心跳成功: {self.registry_client.service_id}")
                else:
                    logger.warning("⚠️ 心跳失败，尝试重新注册...")

                    # 尝试重新注册
                    await self.registry_client.register_service()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 心跳任务出错: {e}")

                # 出错后等待一段时间再继续
                await asyncio.sleep(5)


# 全局实例
_service_registry_client: ServiceRegistryClient | None = None
_heartbeat_manager: HeartbeatManager | None = None


def get_service_registry_client() -> ServiceRegistryClient:
    """获取全局服务注册客户端"""
    global _service_registry_client
    if _service_registry_client is None:
        _service_registry_client = ServiceRegistryClient()
    return _service_registry_client


def get_heartbeat_manager() -> HeartbeatManager:
    """获取全局心跳管理器"""
    global _heartbeat_manager
    if _heartbeat_manager is None:
        registry_client = get_service_registry_client()
        _heartbeat_manager = HeartbeatManager(
            registry_client=registry_client,
            interval=1800,  # 30分钟 = 1800秒
        )
    return _heartbeat_manager


# 导出
__all__ = [
    "ServiceRegistryClient",
    "HeartbeatManager",
    "get_service_registry_client",
    "get_heartbeat_manager",
]
