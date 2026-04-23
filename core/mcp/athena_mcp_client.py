#!/usr/bin/env python3
from __future__ import annotations
"""
Athena平台MCP客户端
Athena Platform MCP Client

连接到MCP服务器并使用其提供的工具和资源

功能:
1. 连接到MCP服务器
2. 发现可用工具
3. 调用远程工具
4. 读取资源

作者: 小诺·双鱼座
版本: v1.0.0 "MCP客户端"
创建时间: 2025-01-05
"""

import json
import logging
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class AthenaMCPClient:
    """
    Athena平台的MCP客户端

    用于连接和使用MCP服务器提供的工具和资源
    """

    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.server_tools: dict[str, list[dict]] = {}
        self.server_resources: dict[str, list[str]] = {}

    async def connect_to_server(self, command: str, args: Optional[list[str]] = None) -> dict[str, Any]:
        """
        连接到MCP服务器

        Args:
            command: 启动服务器的命令(如 python -m module.server)
            args: 命令参数

        Returns:
            服务器信息(工具列表、资源列表等)
        """
        server_name = command.split("/")[-1] if "/" in command else command

        logger.info(f"🔗 连接到MCP服务器: {server_name}")

        try:
            # 创建stdio客户端
            stdio_ctx = stdio_client(command, args if args else [])
            read_stream, write_stream = await stdio_ctx.__aenter__()

            # 创建会话
            session = ClientSession(read_stream, write_stream)
            await session.__aenter__()

            # 初始化
            await session.initialize()

            # 保存会话
            self.sessions[server_name] = session

            # 发现工具
            tools = await session.list_tools()
            self.server_tools[server_name] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in tools.tools
            ]

            # 发现资源
            resources = await session.list_resources()
            self.server_resources[server_name] = (
                resources.resources if hasattr(resources, "resources") else []
            )

            logger.info(f"✅ 成功连接到 {server_name}")
            logger.info(f"   发现 {len(self.server_tools[server_name])} 个工具")
            logger.info(f"   发现 {len(self.server_resources[server_name])} 个资源")

            return {
                "server_name": server_name,
                "tools": self.server_tools[server_name],
                "resources": self.server_resources[server_name],
                "status": "connected",
            }

        except Exception as e:
            logger.error(f"❌ 连接失败: {e}", exc_info=True)
            return {"server_name": server_name, "status": "failed", "error": str(e)}

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
        if server_name not in self.sessions:
            return {"success": False, "error": f"服务器未连接: {server_name}"}

        session = self.sessions[server_name]

        logger.info(f"🔧 调用工具: {server_name}.{tool_name}")
        logger.debug(f"   参数: {arguments}")

        try:
            result = await session.call_tool(tool_name, arguments)

            # 提取文本内容
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
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
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
        if server_name not in self.sessions:
            return f"错误: 服务器未连接 - {server_name}"

        session = self.sessions[server_name]

        logger.info(f"📄 读取资源: {server_name}:{uri}")

        try:
            result = await session.read_resource(uri)

            # 提取内容
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

    def get_available_tools(self, server_name: Optional[str] = None) -> dict[str, list[dict]]:
        """
        获取可用的工具列表

        Args:
            server_name: 服务器名称,None表示所有服务器

        Returns:
            工具列表
        """
        if server_name:
            return {server_name: self.server_tools.get(server_name, [])}
        else:
            return self.server_tools.copy()

    def get_available_resources(self, server_name: Optional[str] = None) -> dict[str, list]:
        """
        获取可用的资源列表

        Args:
            server_name: 服务器名称,None表示所有服务器

        Returns:
            资源列表
        """
        if server_name:
            return {server_name: self.server_resources.get(server_name, [])}
        else:
            return self.server_resources.copy()

    async def close(self, server_name: Optional[str] = None):
        """
        关闭连接

        Args:
            server_name: 服务器名称,None表示关闭所有连接
        """
        if server_name:
            if server_name in self.sessions:
                await self.sessions[server_name].__aexit__(None, None, None)
                del self.sessions[server_name]
                logger.info(f"✅ 已关闭连接: {server_name}")
        else:
            for name in list(self.sessions.keys()):
                await self.sessions[name].__aexit__(None, None, None)
                del self.sessions[name]
                logger.info(f"✅ 已关闭连接: {name}")


class MCPToolInvoker:
    """
    MCP工具调用器

    提供便捷的方法来调用MCP工具
    """

    def __init__(self, client: AthenaMCPClient):
        self.client = client

    async def search_patents(self, query: str, database: str = "all", limit: int = 20) -> dict:
        """便捷方法:专利检索"""
        return await self.client.call_tool(
            "athena_mcp_server.py",
            "patent_search",
            {"query": query, "database": database, "limit": limit},
        )

    async def analyze_patent(self, patent_id: str, analysis_type: str = "comprehensive") -> dict:
        """便捷方法:专利分析"""
        return await self.client.call_tool(
            "athena_mcp_server.py",
            "patent_analysis",
            {"patent_id": patent_id, "analysis_type": analysis_type},
        )

    async def vector_search(self, query: str, top_k: int = 10) -> dict:
        """便捷方法:向量搜索"""
        return await self.client.call_tool(
            "athena_mcp_server.py", "vector_search", {"query": query, "top_k": top_k}
        )

    async def query_knowledge_graph(self, entity: str, depth: int = 2) -> dict:
        """便捷方法:知识图谱查询"""
        return await self.client.call_tool(
            "athena_mcp_server.py", "knowledge_graph_query", {"entity": entity, "depth": depth}
        )


# ==================== 全局实例 ====================

mcp_client = None
mcp_invoker = None


def get_mcp_client() -> AthenaMCPClient:
    """获取MCP客户端单例"""
    global mcp_client
    if mcp_client is None:
        mcp_client = AthenaMCPClient()
    return mcp_client


def get_mcp_invoker() -> MCPToolInvoker:
    """获取MCP工具调用器单例"""
    global mcp_client, mcp_invoker
    if mcp_invoker is None:
        if mcp_client is None:
            mcp_client = get_mcp_client()
        mcp_invoker = MCPToolInvoker(mcp_client)
    return mcp_invoker
