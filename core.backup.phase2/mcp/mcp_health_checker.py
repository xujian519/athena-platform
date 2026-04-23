#!/usr/bin/env python3
"""
MCP服务健康检查器
MCP Service Health Checker

为MCP服务器提供专门的健康检查功能,支持进程检查和HTTP检查。

作者: Athena平台团队
创建时间: 2026-04-21
版本: v1.0.0
"""
from __future__ import annotations

import asyncio
import logging
import psutil
from datetime import datetime
from typing import Any

import httpx

from core.service_registry import ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)


class MCPHealthChecker:
    """
    MCP服务健康检查器

    提供进程级别的健康检查和HTTP端点检查。
    """

    def __init__(self):
        """初始化健康检查器"""
        self.check_results: dict[str, dict[str, Any]] = {}
        logger.info("🔧 MCP健康检查器初始化完成")

    async def check_process_health(self, service_name: str, process) -> ServiceHealth:
        """
        检查进程健康状态

        Args:
            service_name: 服务名称
            process: 进程对象

        Returns:
            服务健康状态
        """
        health = ServiceHealth()

        try:
            # 检查进程是否存在
            if process is None:
                health.status = ServiceStatus.STOPPED
                health.error_message = "进程未启动"
                return health

            # 检查进程是否运行
            if not self._is_process_running(process):
                health.status = ServiceStatus.ERROR
                health.error_message = "进程已终止"
                return health

            # 检查进程资源使用
            try:
                proc = psutil.Process(process.pid)
                cpu_percent = proc.cpu_percent(interval=0.1)
                memory_info = proc.memory_info()

                health.metrics = {
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_info.rss / 1024 / 1024,
                    "num_threads": proc.num_threads(),
                    "pid": process.pid,
                }

                # 健康检查阈值
                if cpu_percent > 90:
                    health.status = ServiceStatus.DEGRADED
                    health.error_message = f"CPU使用率过高: {cpu_percent:.1f}%"
                elif memory_info.rss > 1024 * 1024 * 1024:  # 1GB
                    health.status = ServiceStatus.DEGRADED
                    health.error_message = f"内存使用过高: {memory_info.rss / 1024 / 1024:.1f}MB"
                else:
                    health.status = ServiceStatus.RUNNING

            except psutil.NoSuchProcess:
                health.status = ServiceStatus.ERROR
                health.error_message = "进程不存在"
            except Exception as e:
                health.status = ServiceStatus.DEGRADED
                health.error_message = f"无法获取进程信息: {e}"

        except Exception as e:
            logger.error(f"❌ 健康检查异常: {service_name}, 错误: {e}")
            health.status = ServiceStatus.ERROR
            health.error_message = str(e)

        health.last_check = datetime.now()
        return health

    async def check_http_health(
        self, service_name: str, url: str, timeout: float = 5.0
    ) -> ServiceHealth:
        """
        检查HTTP端点健康状态

        Args:
            service_name: 服务名称
            url: 健康检查URL
            timeout: 超时时间(秒)

        Returns:
            服务健康状态
        """
        health = ServiceHealth()

        try:
            async with httpx.AsyncClient() as client:
                start_time = asyncio.get_event_loop().time()

                response = await client.get(url, timeout=timeout)

                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒

                health.metrics = {
                    "response_time_ms": response_time,
                    "status_code": response.status_code,
                }

                if response.status_code == 200:
                    health.status = ServiceStatus.RUNNING
                elif response.status_code >= 500:
                    health.status = ServiceStatus.ERROR
                    health.error_message = f"HTTP {response.status_code}"
                else:
                    health.status = ServiceStatus.DEGRADED
                    health.error_message = f"HTTP {response.status_code}"

        except httpx.TimeoutException:
            health.status = ServiceStatus.ERROR
            health.error_message = f"请求超时({timeout}s)"
        except httpx.ConnectError:
            health.status = ServiceStatus.ERROR
            health.error_message = "连接失败"
        except Exception as e:
            logger.error(f"❌ HTTP健康检查异常: {service_name}, 错误: {e}")
            health.status = ServiceStatus.ERROR
            health.error_message = str(e)

        health.last_check = datetime.now()
        return health

    async def check_stdio_health(self, service_name: str, process) -> ServiceHealth:
        """
        检查stdio类型服务的健康状态

        Args:
            service_name: 服务名称
            process: 进程对象

        Returns:
            服务健康状态
        """
        # stdio服务使用进程健康检查
        return await self.check_process_health(service_name, process)

    def _is_process_running(self, process) -> bool:
        """
        检查进程是否运行中

        Args:
            process: 进程对象

        Returns:
            是否运行中
        """
        if process is None:
            return False

        try:
            # 检查进程返回码
            return process.poll() is None
        except Exception:
            return False

    async def check_all_mcp_services(
        self, mcp_manager
    ) -> dict[str, ServiceHealth]:
        """
        检查所有MCP服务的健康状态

        Args:
            mcp_manager: MCP管理器

        Returns:
            健康状态字典 {service_name: health}
        """
        results = {}

        for service_name, mcp_service in mcp_manager.services.items():
            try:
                if mcp_service.port:
                    # HTTP服务
                    health = await self.check_http_health(
                        service_name=service_name,
                        url=f"http://localhost:{mcp_service.port}/health",
                    )
                else:
                    # stdio服务
                    health = await self.check_stdio_health(
                        service_name=service_name,
                        process=mcp_service.process,
                    )

                results[service_name] = health

                # 保存检查结果
                self.check_results[service_name] = {
                    "health": health,
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"❌ 健康检查异常: {service_name}, 错误: {e}")
                results[service_name] = ServiceHealth(
                    status=ServiceStatus.ERROR,
                    error_message=str(e),
                )

        return results

    def get_check_history(self, service_name: str) -> list[dict[str, Any]]:
        """
        获取服务的健康检查历史

        Args:
            service_name: 服务名称

        Returns:
            检查历史列表
        """
        # 这里可以实现更复杂的历史记录功能
        # 目前只返回最新结果
        if service_name in self.check_results:
            return [self.check_results[service_name]]
        return []


# 全局单例
_mcp_health_checker: MCPHealthChecker | None = None


def get_mcp_health_checker() -> MCPHealthChecker:
    """
    获取MCP健康检查器单例

    Returns:
        MCP健康检查器
    """
    global _mcp_health_checker

    if _mcp_health_checker is None:
        _mcp_health_checker = MCPHealthChecker()

    return _mcp_health_checker
