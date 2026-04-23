#!/usr/bin/env python3
from __future__ import annotations
"""
MCP客户端管理器
MCP Client Manager

管理多个MCP客户端的生命周期,支持有状态和无状态客户端。

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .athena_mcp_client import AthenaMCPClient
from .stateful_client import StatefulMCPClient
from .stateless_client import StatelessMCPClient

logger = logging.getLogger(__name__)


class ClientType(str, Enum):
    """客户端类型"""

    STATEFUL = "stateful"  # 有状态客户端(持久连接)
    STATELESS = "stateless"  # 无状态客户端(独立请求)
    LEGACY = "legacy"  # 遗留客户端(AthenaMCPClient)


class ClientStatus(str, Enum):
    """客户端状态"""

    INITIALIZING = "initializing"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ClientConfig:
    """
    客户端配置

    定义MCP客户端的连接和运行参数。
    """

    client_id: str  # 客户端唯一标识
    client_type: ClientType  # 客户端类型
    command: str  # 启动命令
    args: list[str] = field(default_factory=list)  # 命令参数

    # 连接配置
    host: str = "localhost"  # 主机地址
    port: int = 8000  # 端口号
    protocol: str = "stdio"  # 协议 (stdio, http, ws)

    # 超时配置
    connection_timeout: float = 30.0  # 连接超时(秒)
    request_timeout: float = 60.0  # 请求超时(秒)

    # 重试配置
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟(秒)

    # 有状态客户端专用配置
    session_timeout: float = 3600.0  # 会话超时(秒)
    max_concurrent_requests: int = 10  # 最大并发请求数
    keepalive_interval: float = 60.0  # 心跳间隔(秒)

    # 自动重连
    auto_reconnect: bool = True  # 是否自动重连
    reconnect_delay: float = 5.0  # 重连延迟(秒)

    # 元数据
    description: str = ""  # 描述
    tags: list[str] = field(default_factory=list)  # 标签


@dataclass
class ClientInfo:
    """
    客户端信息

    跟踪客户端的运行状态和统计信息。
    """

    client_id: str
    config: ClientConfig
    status: ClientStatus = ClientStatus.DISCONNECTED
    client: StatefulMCPClient | StatelessMCPClient | AthenaMCPClient | None = None

    # 统计信息
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_execution_time: float = 0.0

    # 连接信息
    connected_at: datetime | None = None
    disconnected_at: datetime | None = None
    last_error: Optional[str] = None

    @property
    def success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def avg_execution_time(self) -> float:
        """获取平均执行时间"""
        if self.total_requests == 0:
            return 0.0
        return self.total_execution_time / self.total_requests


class MCPClientManager:
    """
    MCP客户端管理器

    统一管理所有MCP客户端的生命周期,包括连接、断开、重连和监控。
    """

    # 预定义的客户端配置
    PREDEFINED_CLIENTS = {
        "chrome-browser": ClientConfig(
            client_id="chrome-browser",
            client_type=ClientType.STATEFUL,
            command="python",
            args=["-m", "chrome_mcp_server"],
            description="Chrome浏览器自动化客户端",
            tags=["browser", "automation", "chrome"],
            session_timeout=7200.0,  # 2小时
            keepalive_interval=30.0,
        ),
        "academic-search": ClientConfig(
            client_id="academic-search",
            client_type=ClientType.STATELESS,
            command="python",
            args=["-m", "academic_search_mcp_server"],
            description="学术论文搜索客户端",
            tags=["academic", "search", "research"],
        ),
        "patent-search": ClientConfig(
            client_id="patent-search",
            client_type=ClientType.STATELESS,
            command="python",
            args=["-m", "patent_search_mcp_server"],
            description="专利搜索客户端",
            tags=["patent", "search"],
        ),
        "gaode-map": ClientConfig(
            client_id="gaode-map",
            client_type=ClientType.STATELESS,
            command="python",
            args=["-m", "gaode_mcp_server"],
            description="高德地图客户端",
            tags=["map", "location", "geocoding"],
        ),
        "jina-ai": ClientConfig(
            client_id="jina-ai",
            client_type=ClientType.STATELESS,
            command="python",
            args=["-m", "jina_ai_mcp_server"],
            description="Jina AI客户端",
            tags=["ai", "embedding", "rerank"],
        ),
    }

    def __init__(self):
        """初始化MCP客户端管理器"""
        self._clients: dict[str, ClientInfo] = {}
        self._lock = asyncio.Lock()

        logger.info("🔌 MCPClientManager初始化完成")

    async def register_client(self, config: ClientConfig) -> ClientInfo:
        """
        注册客户端

        Args:
            config: 客户端配置

        Returns:
            客户端信息
        """
        async with self._lock:
            if config.client_id in self._clients:
                logger.warning(f"⚠️ 客户端已存在: {config.client_id}")
                return self._clients[config.client_id]

            info = ClientInfo(client_id=config.client_id, config=config)
            self._clients[config.client_id] = info

            logger.info(f"✅ 客户端已注册: {config.client_id} " f"({config.client_type.value})")

            return info

    async def connect_client(self, client_id: str, force_reconnect: bool = False) -> bool:
        """
        连接客户端

        Args:
            client_id: 客户端ID
            force_reconnect: 是否强制重连

        Returns:
            是否成功连接
        """
        async with self._lock:
            info = self._clients.get(client_id)
            if not info:
                logger.error(f"❌ 客户端不存在: {client_id}")
                return False

            # 如果已经连接且不强制重连
            if info.status == ClientStatus.CONNECTED and not force_reconnect:
                logger.debug(f"客户端已连接: {client_id}")
                return True

            # 断开现有连接
            if info.client:
                try:
                    if hasattr(info.client, "close"):
                        await info.client.close()
                except Exception as e:
                    logger.warning(f"关闭现有连接时出错: {e}")

            # 创建新客户端
            info.status = ClientStatus.INITIALIZING

            try:
                if info.config.client_type == ClientType.STATEFUL:
                    info.client = StatefulMCPClient(
                        command=info.config.command,
                        args=info.config.args,
                        session_timeout=info.config.session_timeout,
                        keepalive_interval=info.config.keepalive_interval,
                    )
                elif info.config.client_type == ClientType.STATELESS:
                    info.client = StatelessMCPClient(
                        command=info.config.command,
                        args=info.config.args,
                        connection_timeout=info.config.connection_timeout,
                    )
                else:
                    # 遗留客户端
                    info.client = AthenaMCPClient()

                # 连接服务器
                await info.client.connect_to_server(info.config.command, info.config.args)

                info.status = ClientStatus.CONNECTED
                info.connected_at = datetime.now()
                info.last_error = None

                logger.info(f"✅ 客户端已连接: {client_id}")
                return True

            except Exception as e:
                info.status = ClientStatus.ERROR
                info.last_error = str(e)
                logger.error(f"❌ 客户端连接失败: {client_id} - {e}", exc_info=True)

                # 尝试自动重连
                if info.config.auto_reconnect:
                    logger.info(f"🔄 {info.config.reconnect_delay}秒后尝试重连...")
                    await asyncio.sleep(info.config.reconnect_delay)
                    return await self.connect_client(client_id, force_reconnect=True)

                return False

    async def disconnect_client(self, client_id: str) -> bool:
        """
        断开客户端

        Args:
            client_id: 客户端ID

        Returns:
            是否成功断开
        """
        async with self._lock:
            info = self._clients.get(client_id)
            if not info:
                logger.warning(f"客户端不存在: {client_id}")
                return False

            if info.client and hasattr(info.client, "close"):
                try:
                    await info.client.close()
                    logger.info(f"✅ 客户端已断开: {client_id}")
                except Exception as e:
                    logger.error(f"断开客户端时出错: {e}")

            info.status = ClientStatus.DISCONNECTED
            info.disconnected_at = datetime.now()

            return True

    async def call_tool(
        self, client_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        调用MCP工具

        Args:
            client_id: 客户端ID
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            调用结果
        """
        info = self._clients.get(client_id)
        if not info:
            return {"success": False, "error": f"客户端不存在: {client_id}"}

        # 确保客户端已连接
        if info.status != ClientStatus.CONNECTED:
            logger.info(f"客户端未连接,尝试连接: {client_id}")
            if not await self.connect_client(client_id):
                return {"success": False, "error": f"客户端连接失败: {client_id}"}

        # 调用工具
        start_time = datetime.now()
        info.total_requests += 1

        try:
            result = await asyncio.wait_for(
                info.client.call_tool(
                    info.config.command.split("/")[-1], tool_name, arguments  # server_name
                ),
                timeout=info.config.request_timeout,
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            info.successful_requests += 1
            info.total_execution_time += execution_time

            return {
                "success": True,
                "data": result,
                "execution_time": execution_time,
                "client_id": client_id,
            }

        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            info.failed_requests += 1
            info.total_execution_time += execution_time

            logger.error(f"❌ 工具调用超时: {client_id}.{tool_name}")

            return {
                "success": False,
                "error": f"请求超时 ({info.config.request_timeout}秒)",
                "client_id": client_id,
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            info.failed_requests += 1
            info.total_execution_time += execution_time
            info.last_error = str(e)

            logger.error(f"❌ 工具调用失败: {client_id}.{tool_name} - {e}")

            return {"success": False, "error": str(e), "client_id": client_id}

    def get_client_info(self, client_id: str) -> ClientInfo | None:
        """
        获取客户端信息

        Args:
            client_id: 客户端ID

        Returns:
            客户端信息,如果不存在返回None
        """
        return self._clients.get(client_id)

    def list_clients(self, status_filter: ClientStatus | None = None) -> list[ClientInfo]:
        """
        列出所有客户端

        Args:
            status_filter: 状态过滤器 (可选)

        Returns:
            客户端信息列表
        """
        clients = list(self._clients.values())

        if status_filter:
            clients = [c for c in clients if c.status == status_filter]

        return clients

    async def register_predefined_clients(self) -> None:
        """注册所有预定义的客户端"""
        for config in self.PREDEFINED_CLIENTS.values():
            await self.register_client(config)

        logger.info(f"✅ 已注册{len(self.PREDEFINED_CLIENTS)}个预定义客户端")

    async def connect_all_clients(self) -> dict[str, bool]:
        """
        连接所有已注册的客户端

        Returns:
            连接结果字典 {client_id: success}
        """
        results = {}

        for client_id in self._clients:
            results[client_id] = await self.connect_client(client_id)

        connected_count = sum(1 for v in results.values() if v)
        logger.info(f"✅ 批量连接完成: {connected_count}/{len(results)} 个客户端成功连接")

        return results

    async def disconnect_all_clients(self) -> None:
        """断开所有客户端"""
        for client_id in list(self._clients.keys()):
            await self.disconnect_client(client_id)

        logger.info("⏹️ 所有客户端已断开")

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        total_clients = len(self._clients)
        connected_clients = sum(
            1 for c in self._clients.values() if c.status == ClientStatus.CONNECTED
        )

        total_requests = sum(c.total_requests for c in self._clients.values())
        total_success = sum(c.successful_requests for c in self._clients.values())
        total_failures = sum(c.failed_requests for c in self._clients.values())

        return {
            "total_clients": total_clients,
            "connected_clients": connected_clients,
            "disconnected_clients": total_clients - connected_clients,
            "total_requests": total_requests,
            "successful_requests": total_success,
            "failed_requests": total_failures,
            "overall_success_rate": total_success / total_requests if total_requests > 0 else 0.0,
            "clients": [
                {
                    "client_id": c.client_id,
                    "status": c.status.value,
                    "requests": c.total_requests,
                    "success_rate": c.success_rate,
                    "avg_execution_time": c.avg_execution_time,
                }
                for c in self._clients.values()
            ],
        }


# ==================== 全局实例 ====================

_client_manager: MCPClientManager | None = None


def get_client_manager() -> MCPClientManager:
    """获取全局MCP客户端管理器"""
    global _client_manager
    if _client_manager is None:
        _client_manager = MCPClientManager()
    return _client_manager


__all__ = [
    "ClientConfig",
    "ClientInfo",
    "ClientStatus",
    "ClientType",
    "MCPClientManager",
    "get_client_manager",
]
