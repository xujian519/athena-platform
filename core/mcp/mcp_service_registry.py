#!/usr/bin/env python3
"""
MCP服务注册中心集成
MCP Service Registry Integration

将MCP服务器集成到统一服务注册中心,提供服务发现和健康检查功能。

作者: Athena平台团队
创建时间: 2026-04-21
版本: v1.0.0
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.service_registry import (
    ServiceInfo,
    ServiceStatus,
    get_service_registry,
    get_health_checker,
)
from core.orchestration.unified_mcp_manager import UnifiedMCPManager, MCPService

logger = logging.getLogger(__name__)


class MCPServiceRegistryBridge:
    """
    MCP服务注册中心桥接器

    将UnifiedMCPManager管理的MCP服务注册到ServiceRegistry中。
    """

    def __init__(self, mcp_manager: UnifiedMCPManager | None = None):
        """
        初始化桥接器

        Args:
            mcp_manager: MCP管理器(可选,默认创建新实例)
        """
        self.mcp_manager = mcp_manager or UnifiedMCPManager()
        self.service_registry = get_service_registry()
        self.health_checker = get_health_checker()

        logger.info("🔧 MCP服务注册中心桥接器初始化完成")

    async def register_all_mcp_services(self) -> dict[str, bool]:
        """
        注册所有MCP服务到服务注册中心

        Returns:
            注册结果字典 {service_name: success}
        """
        results = {}

        for service_name, mcp_service in self.mcp_manager.services.items():
            try:
                success = await self._register_mcp_service(mcp_service)
                results[service_name] = success

                if success:
                    logger.info(f"✅ MCP服务注册成功: {service_name}")
                else:
                    logger.warning(f"⚠️ MCP服务注册失败: {service_name}")

            except Exception as e:
                logger.error(f"❌ MCP服务注册异常: {service_name}, 错误: {e}")
                results[service_name] = False

        return results

    async def _register_mcp_service(self, mcp_service: MCPService) -> bool:
        """
        注册单个MCP服务

        Args:
            mcp_service: MCP服务定义

        Returns:
            是否注册成功
        """
        # 构建健康检查URL
        if mcp_service.port:
            # 有端口的服务,使用HTTP健康检查
            health_check_url = f"http://localhost:{mcp_service.port}/health"
        else:
            # 无端口的服务(stdio),使用进程健康检查
            health_check_url = f"process://{mcp_service.name}"

        # 创建服务信息
        service_info = ServiceInfo(
            id=f"mcp-{mcp_service.name}",
            name=mcp_service.name,
            type="mcp",
            version="1.0.0",
            host="localhost",
            port=mcp_service.port or 8000,  # 默认端口
            protocol="stdio" if not mcp_service.port else "http",
            health_check_url=health_check_url,
            health_check_interval=30,  # 30秒检查一次
            tags=["mcp", mcp_service.type] + (mcp_service.capabilities or []),
            metadata={
                "description": mcp_service.description,
                "main_file": mcp_service.main_file,
                "capabilities": ",".join(mcp_service.capabilities or []),
            },
        )

        # 注册到服务注册中心
        self.service_registry.register(service_info)

        return True

    async def sync_mcp_service_status(self) -> dict[str, str]:
        """
        同步MCP服务状态到服务注册中心

        Returns:
            服务状态字典 {service_name: status}
        """
        status_map = {}

        for service_name, mcp_service in self.mcp_manager.services.items():
            try:
                # 映射状态
                status = self._map_mcp_status(mcp_service.status)
                status_map[service_name] = status

                # 更新服务注册中心中的状态
                service_id = f"mcp-{service_name}"
                service = self.service_registry.get_service(service_id)

                if service:
                    service.health.status = status
                    logger.debug(f"🔄 状态同步: {service_name} -> {status}")
                else:
                    logger.warning(f"⚠️ 服务未注册: {service_name}")

            except Exception as e:
                logger.error(f"❌ 状态同步异常: {service_name}, 错误: {e}")
                status_map[service_name] = "error"

        return status_map

    def _map_mcp_status(self, mcp_status: str) -> ServiceStatus:
        """
        映射MCP服务状态到服务注册中心状态

        Args:
            mcp_status: MCP服务状态

        Returns:
            服务注册中心状态
        """
        mapping = {
            "running": ServiceStatus.RUNNING,
            "stopped": ServiceStatus.STOPPED,
            "error": ServiceStatus.ERROR,
            "starting": ServiceStatus.STARTING,
            "stopping": ServiceStatus.STOPPING,
        }

        return mapping.get(mcp_status, ServiceStatus.ERROR)

    async def start_mcp_service(self, service_name: str) -> bool:
        """
        启动MCP服务并注册到服务注册中心

        Args:
            service_name: 服务名称

        Returns:
            是否启动成功
        """
        # 启动服务
        success = await self.mcp_manager.start_service(service_name)

        if success:
            # 同步状态
            await self.sync_mcp_service_status()

        return success

    async def stop_mcp_service(self, service_name: str) -> bool:
        """
        停止MCP服务并更新状态

        Args:
            service_name: 服务名称

        Returns:
            是否停止成功
        """
        # 停止服务
        success = await self.mcp_manager.stop_service(service_name)

        if success:
            # 同步状态
            await self.sync_mcp_service_status()

        return success

    async def get_mcp_service_health(self) -> dict[str, dict[str, Any]]:
        """
        获取所有MCP服务的健康状态

        Returns:
            健康状态字典 {service_name: health_info}
        """
        health_info = {}

        for service_name, mcp_service in self.mcp_manager.services.items():
            service_id = f"mcp-{service_name}"
            service = self.service_registry.get_service(service_id)

            if service:
                health_info[service_name] = {
                    "status": service.health.status.value,
                    "last_check": service.health.last_check.isoformat(),
                    "error_message": service.health.error_message,
                    "metrics": service.health.metrics,
                }
            else:
                health_info[service_name] = {
                    "status": "not_registered",
                    "last_check": None,
                    "error_message": "服务未注册",
                    "metrics": {},
                }

        return health_info


# 全局单例
_mcp_registry_bridge: MCPServiceRegistryBridge | None = None


def get_mcp_registry_bridge() -> MCPServiceRegistryBridge:
    """
    获取MCP服务注册中心桥接器单例

    Returns:
        MCP服务注册中心桥接器
    """
    global _mcp_registry_bridge

    if _mcp_registry_bridge is None:
        _mcp_registry_bridge = MCPServiceRegistryBridge()

    return _mcp_registry_bridge


async def register_all_mcp_services() -> dict[str, bool]:
    """
    注册所有MCP服务的便捷函数

    Returns:
        注册结果字典
    """
    bridge = get_mcp_registry_bridge()
    return await bridge.register_all_mcp_services()


async def sync_mcp_service_status() -> dict[str, str]:
    """
    同步MCP服务状态的便捷函数

    Returns:
        服务状态字典
    """
    bridge = get_mcp_registry_bridge()
    return await bridge.sync_mcp_service_status()
