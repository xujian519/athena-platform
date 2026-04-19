#!/usr/bin/env python3
"""
无状态MCP客户端
Stateless MCP Client

用于独立请求的MCP服务(如学术搜索、专利检索)。

特性:
- 无状态设计,每次请求独立
- 动态连接池管理(使用DynamicConnectionPool)
- 请求级超时控制
- 自动资源清理
- 健康检查和TTL管理

作者: Athena平台团队
创建时间: 2026-01-20
版本: v2.0.0 "Phase 2 - 动态连接池集成"
"""

from __future__ import annotations
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

from core.communication.engine import ConnectionConfig, DynamicConnectionPool

logger = logging.getLogger(__name__)


class ConnectionTimeoutError(Exception):
    """连接超时异常"""

    pass


class StatelessMCPClient:
    """
    无状态MCP客户端

    适用于每次请求都是独立的场景,如:
    - 学术论文搜索(每次搜索是独立的)
    - 专利检索(不需要保持连接状态)
    - 向量嵌入服务(一次性的嵌入请求)
    - 地图API(每次查询独立)
    """

    def __init__(
        self,
        command: str,
        args: list[str],
        connection_timeout: float = 30.0,
        request_timeout: float = 60.0,
        min_pool_size: int = 2,
        max_pool_size: int = 10,
        enable_health_check: bool = True,
    ):
        """
        初始化无状态MCP客户端

        Args:
            command: 启动服务器的命令
            args: 命令参数
            connection_timeout: 连接超时时间(秒)
            request_timeout: 请求超时时间(秒)
            min_pool_size: 最小连接池大小
            max_pool_size: 最大连接池大小
            enable_health_check: 是否启用健康检查
        """
        self.command = command
        self.args = args
        self.connection_timeout = connection_timeout
        self.request_timeout = request_timeout
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.enable_health_check = enable_health_check

        # 连接池配置
        self._pool_config = ConnectionConfig(
            min_size=min_pool_size,
            max_size=max_pool_size,
            acquire_timeout=connection_timeout,
            idle_timeout=300.0,  # 5分钟空闲超时
            ttl=3600.0,  # 1小时TTL
            health_check_interval=60.0,  # 1分钟健康检查间隔
        )

        # 动态连接池(延迟初始化)
        self._connection_pool: DynamicConnectionPool | None = None
        self._pool_initialized = False

        # 统计信息
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._total_execution_time = 0.0

        logger.debug(
            f"🔧 StatelessMCPClient初始化: {command} "
            f"(conn_timeout: {connection_timeout}s, req_timeout: {request_timeout}s)"
        )

    async def _initialize_pool(self) -> None:
        """初始化连接池"""
        if self._pool_initialized:
            return

        async def connection_factory() -> dict[str, Any]:
            """创建MCP连接的工厂函数"""
            server_name = self.command.split("/")[-1] if "/" in self.command else self.command
            return await self._create_connection(server_name)

        async def connection_close(conn: dict[str, Any]) -> None:
            """关闭MCP连接的函数"""
            await self._close_connection(conn)

        async def health_check(conn: dict[str, Any]) -> bool:
            """健康检查函数"""
            if not self.enable_health_check:
                return True
            try:
                # 检查会话是否仍然活跃
                session = conn.get("session")
                if session and hasattr(session, "_initialized"):
                    # 简单的ping测试 - 尝试列出工具
                    await asyncio.wait_for(session.list_tools(), timeout=5.0)
                    return True
                return False
            except Exception:
                return False

        self._connection_pool = DynamicConnectionPool(
            connection_factory=connection_factory,
            connection_close=connection_close,
            health_check=health_check,
            config=self._pool_config,
        )

        await self._connection_pool.start()
        self._pool_initialized = True

        logger.info(f"✅ 动态连接池已初始化: {self.min_pool_size}-{self.max_pool_size}")

    async def connect_to_server(self, command: str, args: list[str] | None = None) -> dict[str, Any]:
        """
        连接到MCP服务器

        对于无状态客户端,这仅用于测试连接性。
        实际的工具调用会自动建立连接。

        Args:
            command: 启动服务器的命令
            args: 命令参数

        Returns:
            服务器信息
        """
        server_name = command.split("/")[-1] if "/" in command else command

        logger.info(f"🔗 测试连接(无状态): {server_name}")

        try:
            async with self._create_connection(server_name) as conn:
                # 发现工具
                tools = await conn["session"].list_tools()

                tool_list = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    }
                    for tool in tools.tools
                ]

                # 发现资源
                resources = await conn["session"].list_resources()
                resource_list = resources.resources if hasattr(resources, "resources") else []

                logger.info(f"✅ 连接测试成功: {server_name}")
                logger.info(f"   发现 {len(tool_list)} 个工具")
                logger.info(f"   发现 {len(resource_list)} 个资源")

                return {
                    "server_name": server_name,
                    "tools": tool_list,
                    "resources": resource_list,
                    "status": "connected",
                }

        except Exception as e:
            logger.error(f"❌ 连接测试失败: {e}", exc_info=True)
            return {"server_name": server_name, "status": "failed", "error": str(e)}

    async def _create_connection(self, server_name: str | None = None):
        """
        创建新的连接

        Args:
            server_name: 服务器名称(可选)

        Returns:
            连接上下文
        """
        if server_name is None:
            server_name = self.command.split("/")[-1] if "/" in self.command else self.command

        # 创建stdio客户端
        stdio_ctx = stdio_client(self.command, self.args if self.args else [])
        read_stream, write_stream = await stdio_ctx.__aenter__()

        # 创建会话
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()

        # 初始化
        await session.initialize()

        return {
            "server_name": server_name,
            "stdio_ctx": stdio_ctx,
            "session": session,
            "read_stream": read_stream,
            "write_stream": write_stream,
            "created_at": datetime.now(),
        }

    async def _close_connection(self, conn: dict[str, Any]) -> None:
        """
        关闭连接

        Args:
            conn: 连接对象
        """
        try:
            if conn.get("session"):
                await conn["session"].__aexit__(None, None, None)
            if conn.get("stdio_ctx"):
                await conn["stdio_ctx"].__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"关闭连接时出错: {e}")

    async def _get_connection_from_pool(self) -> dict[str, Any]:
        """
        从连接池获取连接

        Returns:
            连接对象
        """
        # 确保连接池已初始化
        if not self._pool_initialized:
            await self._initialize_pool()

        # 从动态连接池获取连接
        conn = await self._connection_pool.acquire(timeout=self.connection_timeout)
        return conn

    async def _return_connection_to_pool(self, conn: dict[str, Any]) -> None:
        """
        将连接返回池中

        Args:
            conn: 连接对象
        """
        # 返回到动态连接池
        if self._pool_initialized and self._connection_pool:
            await self._connection_pool.release(conn)

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        调用远程工具(无状态方式)

        每次调用都是独立的,使用连接池复用连接。

        Args:
            server_name: 服务器名称
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        start_time = datetime.now()
        self._total_requests += 1

        logger.info(f"🔧 调用工具(无状态): {server_name}.{tool_name}")
        logger.debug(f"   参数: {arguments}")

        conn = None
        try:
            # 获取连接
            conn = await asyncio.wait_for(
                self._get_connection_from_pool(), timeout=self.connection_timeout
            )

            # 调用工具
            result = await asyncio.wait_for(
                conn["session"].call_tool(tool_name, arguments), timeout=self.request_timeout
            )

            # 提取内容
            content_items = []
            for content in result.content:
                if hasattr(content, "text"):
                    content_items.append(content.text)
                elif isinstance(content, str):
                    content_items.append(content)

            # 尝试解析JSON
            execution_time = (datetime.now() - start_time).total_seconds()
            self._successful_requests += 1
            self._total_execution_time += execution_time

            if len(content_items) == 1:
                try:
                    parsed = json.loads(content_items[0])
                    # 将连接返回池中
                    await self._return_connection_to_pool(conn)
                    return parsed
                except json.JSONDecodeError:
                    await self._return_connection_to_pool(conn)
                    return {"result": content_items[0]}
            else:
                await self._return_connection_to_pool(conn)
                return {"results": content_items}

        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._failed_requests += 1
            self._total_execution_time += execution_time

            # 关闭超时的连接
            if conn:
                await self._close_connection(conn)

            error_msg = (
                f"超时 (连接: {self.connection_timeout}s, " f"请求: {self.request_timeout}s)"
            )
            logger.error(f"❌ 工具调用超时: {server_name}.{tool_name} - {error_msg}")

            return {"success": False, "error": error_msg, "tool": tool_name}

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._failed_requests += 1
            self._total_execution_time += execution_time

            # 关闭出错的连接
            if conn:
                await self._close_connection(conn)

            logger.error(f"❌ 工具调用失败: {e}", exc_info=True)

            return {"success": False, "error": str(e), "tool": tool_name}

    async def read_resource(self, server_name: str, uri: str) -> str:
        """
        读取远程资源

        Args:
            server_name: 服务器名称
            uri: 资源URI

        Returns:
            资源内容
        """
        logger.info(f"📄 读取资源(无状态): {server_name}:{uri}")

        try:
            conn = await asyncio.wait_for(
                self._get_connection_from_pool(), timeout=self.connection_timeout
            )

            try:
                result = await asyncio.wait_for(
                    conn["session"].read_resource(uri), timeout=self.request_timeout
                )

                content_items = []
                for content in result.contents:
                    if hasattr(content, "text"):
                        content_items.append(content.text)
                    elif isinstance(content, str):
                        content_items.append(content)

                await self._return_connection_to_pool(conn)
                return "\n".join(content_items)

            except Exception:
                await self._close_connection(conn)
                raise

        except asyncio.TimeoutError:
            return f"错误: 读取超时 ({self.connection_timeout}秒)"
        except Exception as e:
            logger.error(f"❌ 读取资源失败: {e}", exc_info=True)
            return f"错误: {e!s}"

    def get_available_tools(self) -> dict[str, list[dict]]:
        """
        获取可用的工具列表

        注意:无状态客户端不会缓存工具列表。
        需要通过connect_to_server来获取。

        Returns:
            空字典
        """
        return {}

    def get_available_resources(self) -> dict[str, list]:
        """
        获取可用的资源列表

        注意:无状态客户端不会缓存资源列表。

        Returns:
            空字典
        """
        return {}

    async def close(self) -> None:
        """关闭所有连接"""
        logger.info("⏹️ 关闭无状态客户端")

        if self._pool_initialized and self._connection_pool:
            await self._connection_pool.stop()
            self._pool_initialized = False
            logger.info("✅ 动态连接池已停止")

        logger.info("✅ 无状态客户端已关闭")

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "success_rate": (
                self._successful_requests / self._total_requests
                if self._total_requests > 0
                else 0.0
            ),
            "avg_execution_time": (
                self._total_execution_time / self._total_requests
                if self._total_requests > 0
                else 0.0
            ),
        }

        # 添加连接池统计
        if self._pool_initialized and self._connection_pool:
            pool_stats = self._connection_pool.get_stats()
            stats.update(
                {
                    "connection_pool": pool_stats,
                    "min_pool_size": self.min_pool_size,
                    "max_pool_size": self.max_pool_size,
                }
            )
        else:
            stats.update(
                {
                    "connection_pool": {
                        "status": "not_initialized",
                        "active_connections": 0,
                        "idle_connections": 0,
                        "total_connections": 0,
                    },
                    "min_pool_size": self.min_pool_size,
                    "max_pool_size": self.max_pool_size,
                }
            )

        return stats

    @asynccontextmanager
    async def request_context(self):
        """
        请求上下文管理器

        用法:
            async with client.request_context():
                result = await client.call_tool(...)
        """
        try:
            yield self
        finally:
            await self.close()


__all__ = ["ConnectionTimeoutError", "StatelessMCPClient"]
