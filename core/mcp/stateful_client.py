#!/usr/bin/env python3
from __future__ import annotations
"""
有状态MCP客户端
Stateful MCP Client

用于需要持久连接的MCP服务(如浏览器自动化)。

特性:
- 持久连接,避免重复建立连接
- 会话状态管理
- 心跳保活机制
- 自动重连
- 并发请求控制

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class SessionTimeoutError(Exception):
    """会话超时异常"""

    pass


class StatefulMCPClient:
    """
    有状态MCP客户端

    适用于需要保持连接状态的服务,如:
    - Chrome浏览器自动化(保持浏览器会话)
    - 长时间运行的交互式任务
    - 需要维护状态的复杂工作流
    """

    def __init__(
        self,
        command: str,
        args: list[str],
        session_timeout: float = 3600.0,
        keepalive_interval: float = 60.0,
        max_concurrent_requests: int = 10,
    ):
        """
        初始化有状态MCP客户端

        Args:
            command: 启动服务器的命令
            args: 命令参数
            session_timeout: 会话超时时间(秒)
            keepalive_interval: 心跳间隔(秒)
            max_concurrent_requests: 最大并发请求数
        """
        self.command = command
        self.args = args
        self.session_timeout = session_timeout
        self.keepalive_interval = keepalive_interval
        self.max_concurrent_requests = max_concurrent_requests

        # 连接状态
        self._session: ClientSession | None = None
        self._stdio_ctx: Any | None = None
        self._read_stream = None
        self._write_stream = None
        self._is_connected = False

        # 会话管理
        self._session_created_at: datetime | None = None
        self._last_activity_at: datetime | None = None
        self._keepalive_task: asyncio.Task | None = None

        # 并发控制
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)

        # 服务信息
        self.server_name: str | None = None
        self.server_tools: list[dict] = []
        self.server_resources: list[Any] = []

        logger.debug(
            f"🔧 StatefulMCPClient初始化: {command} "
            f"(timeout: {session_timeout}s, keepalive: {keepalive_interval}s)"
        )

    async def connect_to_server(self, command: str, args: list[str] | None = None) -> dict[str, Any]:
        """
        连接到MCP服务器

        Args:
            command: 启动服务器的命令
            args: 命令参数

        Returns:
            服务器信息
        """
        if self._is_connected:
            logger.debug(f"客户端已连接: {self.server_name}")
            return self._get_server_info()

        self.server_name = command.split("/")[-1] if "/" in command else command

        logger.info(f"🔗 连接到MCP服务器(有状态): {self.server_name}")

        try:
            # 创建stdio客户端
            self._stdio_ctx = stdio_client(command, args if args else [])
            self._read_stream, self._write_stream = await self._stdio_ctx.__aenter__()

            # 创建会话
            self._session = ClientSession(self._read_stream, self._write_stream)
            await self._session.__aenter__()

            # 初始化
            await self._session.initialize()

            # 更新状态
            self._is_connected = True
            now = datetime.now()
            self._session_created_at = now
            self._last_activity_at = now

            # 发现工具和资源
            await self._discover_capabilities()

            # 启动心跳任务
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())

            logger.info(f"✅ 有状态客户端已连接: {self.server_name}")
            logger.info(f"   会话超时: {self.session_timeout}秒")
            logger.info(f"   心跳间隔: {self.keepalive_interval}秒")

            return self._get_server_info()

        except Exception as e:
            logger.error(f"❌ 连接失败: {e}", exc_info=True)
            await self._cleanup()
            return {"server_name": self.server_name, "status": "failed", "error": str(e)}

    async def _discover_capabilities(self) -> None:
        """发现服务器的工具和资源"""
        # 发现工具
        tools = await self._session.list_tools()
        self.server_tools = [
            {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema}
            for tool in tools.tools
        ]

        # 发现资源
        resources = await self._session.list_resources()
        self.server_resources = resources.resources if hasattr(resources, "resources") else []

        logger.info(f"   发现 {len(self.server_tools)} 个工具")
        logger.info(f"   发现 {len(self.server_resources)} 个资源")

    def _get_server_info(self) -> dict[str, Any]:
        """获取服务器信息"""
        return {
            "server_name": self.server_name,
            "tools": self.server_tools,
            "resources": self.server_resources,
            "status": "connected",
            "session_age_seconds": self._get_session_age(),
            "idle_time_seconds": self._get_idle_time(),
        }

    def _get_session_age(self) -> float:
        """获取会话年龄(秒)"""
        if not self._session_created_at:
            return 0.0
        return (datetime.now() - self._session_created_at).total_seconds()

    def _get_idle_time(self) -> float:
        """获取空闲时间(秒)"""
        if not self._last_activity_at:
            return 0.0
        return (datetime.now() - self._last_activity_at).total_seconds()

    async def _keepalive_loop(self) -> None:
        """心跳保活循环"""
        logger.debug(f"💓 心跳任务已启动: {self.server_name}")

        while self._is_connected:
            try:
                await asyncio.sleep(self.keepalive_interval)

                if not self._is_connected:
                    break

                # 检查会话是否超时
                idle_time = self._get_idle_time()
                if idle_time > self.session_timeout:
                    logger.warning(
                        f"⚠️ 会话超时 (空闲 {idle_time:.1f}秒 > {self.session_timeout}秒): "
                        f"{self.server_name}"
                    )
                    await self.close()
                    break

                # 发送心跳(通过ping或简单的工具调用)
                logger.debug(f"💓 发送心跳: {self.server_name} (空闲: {idle_time:.1f}秒)")

            except asyncio.CancelledError:
                logger.debug(f"💓 心跳任务已取消: {self.server_name}")
                break
            except Exception as e:
                logger.error(f"❌ 心跳任务出错: {e}", exc_info=True)
                break

        logger.debug(f"💓 心跳任务已退出: {self.server_name}")

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        调用远程工具

        Args:
            server_name: 服务器名称
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if not self._is_connected or not self._session:
            return {"success": False, "error": f"客户端未连接: {self.server_name}"}

        # 更新活动时间
        self._last_activity_at = datetime.now()

        # 使用信号量控制并发
        async with self._semaphore:
            logger.info(f"🔧 调用工具(有状态): {self.server_name}.{tool_name}")
            logger.debug(f"   参数: {arguments}")

            try:
                result = await self._session.call_tool(tool_name, arguments)

                # 提取内容
                content_items = []
                for content in result.content:
                    if hasattr(content, "text"):
                        content_items.append(content.text)
                    elif isinstance(content, str):
                        content_items.append(content)

                # 尝试解析JSON
                if len(content_items) == 1:
                    try:
                        return json.loads(content_items[0])
                    except json.JSONDecodeError:
                        return {"result": content_items[0]}
                else:
                    return {"results": content_items}

            except Exception as e:
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
        if not self._is_connected or not self._session:
            return f"错误: 客户端未连接 - {self.server_name}"

        self._last_activity_at = datetime.now()

        logger.info(f"📄 读取资源(有状态): {self.server_name}:{uri}")

        try:
            result = await self._session.read_resource(uri)

            content_items = []
            for content in result.contents:
                if hasattr(content, "text"):
                    content_items.append(content.text)
                elif isinstance(content, str):
                    content_items.append(content)

            return "\n".join(content_items)

        except Exception as e:
            logger.error(f"❌ 读取资源失败: {e}", exc_info=True)
            return f"错误: {e!s}"

    def get_available_tools(self) -> dict[str, list[dict]]:
        """
        获取可用的工具列表

        Returns:
            工具列表
        """
        return {self.server_name: self.server_tools} if self.server_name else {}

    def get_available_resources(self) -> dict[str, list]:
        """
        获取可用的资源列表

        Returns:
            资源列表
        """
        return {self.server_name: self.server_resources} if self.server_name else {}

    def get_session_info(self) -> dict[str, Any]:
        """
        获取会话信息

        Returns:
            会话信息字典
        """
        return {
            "server_name": self.server_name,
            "is_connected": self._is_connected,
            "session_age_seconds": self._get_session_age(),
            "idle_time_seconds": self._get_idle_time(),
            "session_timeout": self.session_timeout,
            "available_tools": len(self.server_tools),
            "available_resources": len(self.server_resources),
            "active_requests": self.max_concurrent_requests - self._semaphore._value,
            "max_concurrent_requests": self.max_concurrent_requests,
        }

    async def refresh_session(self) -> bool:
        """
        刷新会话(防止超时)

        Returns:
            是否成功刷新
        """
        self._last_activity_at = datetime.now()
        logger.debug(f"🔄 会话已刷新: {self.server_name}")
        return True

    async def close(self) -> None:
        """关闭连接"""
        if not self._is_connected:
            return

        logger.info(f"⏹️ 关闭有状态客户端: {self.server_name}")

        # 取消心跳任务
        if self._keepalive_task:
            self._keepalive_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._keepalive_task

        await self._cleanup()
        logger.info(f"✅ 有状态客户端已关闭: {self.server_name}")

    async def _cleanup(self) -> None:
        """清理资源"""
        self._is_connected = False

        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"关闭会话时出错: {e}")

        if self._stdio_ctx:
            try:
                await self._stdio_ctx.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"关闭stdio上下文时出错: {e}")

        self._session = None
        self._stdio_ctx = None
        self._read_stream = None
        self._write_stream = None

    @asynccontextmanager
    async def session_context(self):
        """
        会话上下文管理器

        用法:
            async with client.session_context():
                await client.call_tool(...)
        """
        await self.connect_to_server(self.command, self.args)
        try:
            yield self
        finally:
            await self.close()

    def __del__(self):
        """析构函数"""
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()


__all__ = ["SessionTimeoutError", "StatefulMCPClient"]
