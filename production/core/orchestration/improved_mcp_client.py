#!/usr/bin/env python3
"""
改进的MCP客户端
Improved MCP Client

实现正确的MCP协议通信

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
from typing import Any


class ImprovedMCPClient:
    """改进的MCP客户端"""

    def __init__(self, service_path: str, service_type: str = "python"):
        self.service_path = service_path
        self.service_type = service_type
        self.process = None
        self.initialized = False
        self.logger = logging.getLogger(f"MCP-{os.path.basename(service_path)}-小诺·双鱼公主")

    async def start(self):
        """启动MCP服务"""
        if self.process:
            return True

        try:
            # 创建环境变量
            env = os.environ.copy()

            if self.service_type == "python":
                # Python服务
                env["PYTHONPATH"] = self.service_path
                if "gaode" in self.service_path:
                    # 使用环境变量获取API密钥
                    env["AMAP_API_KEY"] = os.getenv("AMAP_API_KEY", "")
                    if not env["AMAP_API_KEY"]:
                        self.logger.warning("AMAP_API_KEY环境变量未设置")
                    env["MCP_LOG_LEVEL"] = os.getenv("MCP_LOG_LEVEL", "INFO")

                # 使用python运行server
                cmd = ["python3", "run_server.py"]
            else:
                # Node.js服务
                cmd = ["node", "index.js"]

            # 启动进程
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.service_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # 初始化MCP会话
            success = await self._initialize_session()
            if success:
                self.initialized = True
                self.logger.info("MCP服务初始化成功")

            return success

        except Exception as e:
            self.logger.error(f"启动MCP服务失败: {e!s}")
            return False

    async def _initialize_session(self):
        """初始化MCP会话"""
        try:
            # 发送初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocol_version": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "client_info": {"name": "XiaonuoClient", "version": "1.0.0"},
                },
            }

            # 发送请求
            await self._send_message(init_request)

            # 读取响应
            response = await self._read_message()
            if response and "result" in response:
                # 发送initialized通知
                notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                await self._send_message(notification)

                # 获取工具列表
                await self._list_tools()

                return True

            return False

        except Exception as e:
            self.logger.error(f"初始化会话失败: {e!s}")
            return False

    async def _send_message(self, message: dict[str, Any]):
        """发送消息到MCP服务"""
        if not self.process:
            raise Exception("MCP服务未启动")

        message_str = json.dumps(message)
        self.process.stdin.write(message_str.encode() + b"\n")
        await self.process.stdin.drain()

    async def _read_message(self) -> dict[str, Any] | None:
        """从MCP服务读取消息"""
        if not self.process:
            return None

        try:
            line = await self.process.stdout.readline()
            if line:
                return json.loads(line.decode().strip())
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"读取消息失败: {e}")
            return None

        return None

    async def _list_tools(self):
        """获取工具列表"""
        request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

        await self._send_message(request)
        response = await self._read_message()

        if response and "result" in response:
            tools = response["result"].get("tools", [])
            self.logger.info(f"可用工具数量: {len(tools)}")
            for tool in tools:
                self.logger.info(f"  - {tool['name']}: {tool['description']}")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """调用工具"""
        if not self.initialized and not await self.start():
            return {"error": "无法初始化MCP服务"}

        request = {
            "jsonrpc": "2.0",
            "id": f"call_{tool_name}_{asyncio.get_event_loop().time()}",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        try:
            await self._send_message(request)
            response = await self._read_message()

            if response and "result" in response:
                return response["result"]
            elif response and "error" in response:
                return {"error": response["error"]}
            else:
                return {"error": "未收到有效响应"}

        except Exception as e:
            return {"error": f"调用失败: {e!s}"}

    async def close(self):
        """关闭MCP服务"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
            self.initialized = False


class XiaonuoMCPController:
    """小诺MCP控制器"""

    def __init__(self):
        self.mcp_base_path = "/Users/xujian/Athena工作平台/mcp-servers"
        self.clients = {}

    async def get_client(self, service_name: str) -> ImprovedMCPClient:
        """获取或创建MCP客户端"""
        if service_name not in self.clients:
            service_path = os.path.join(self.mcp_base_path, service_name)

            if not os.path.exists(service_path):
                raise Exception(f"服务不存在: {service_name}")

            # 确定服务类型
            service_type = "python" if service_name == "gaode-mcp-server" else "nodejs"

            client = ImprovedMCPClient(service_path, service_type)
            await client.start()
            self.clients[service_name] = client

        return self.clients[service_name]

    async def search_food(self, location: str, keywords: str = "美食") -> dict[str, Any]:
        """搜索美食"""
        try:
            client = await self.get_client("gaode-mcp-server")

            # 先进行POI搜索
            poi_result = await client.call_tool(
                "gaode_poi_search",
                {
                    "keywords": keywords,
                    "location": location,
                    "city": location,
                    "radius": 3000,  # 3公里范围
                },
            )

            if "error" in poi_result:
                return poi_result

            # 获取天气信息
            weather_result = await client.call_tool("gaode_weather", {"city": location})

            return {
                "poi_results": poi_result,
                "weather": weather_result.get("content", "无法获取天气信息"),
            }

        except Exception as e:
            return {"error": f"搜索美食失败: {e!s}"}

    async def get_location(self, address: str) -> dict[str, Any]:
        """获取地址坐标"""
        try:
            client = await self.get_client("gaode-mcp-server")

            result = await client.call_tool("gaode_geocode", {"address": address})

            return result

        except Exception as e:
            return {"error": f"获取位置失败: {e!s}"}

    async def plan_route(
        self, origin: str, destination: str, mode: str = "driving"
    ) -> dict[str, Any]:
        """规划路线"""
        try:
            client = await self.get_client("gaode-mcp-server")

            result = await client.call_tool(
                "gaode_route_planning",
                {"origin": origin, "destination": destination, "strategy": mode},
            )

            return result

        except Exception as e:
            return {"error": f"路线规划失败: {e!s}"}

    async def search_nearby(self, location: str, keywords: str) -> dict[str, Any]:
        """搜索附近"""
        try:
            client = await self.get_client("gaode-mcp-server")

            result = await client.call_tool(
                "gaode_poi_search", {"keywords": keywords, "location": location, "radius": 2000}
            )

            return result

        except Exception as e:
            return {"error": f"搜索附近失败: {e!s}"}

    async def close_all(self):
        """关闭所有客户端"""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()


# 导出主类
__all__ = ["ImprovedMCPClient", "XiaonuoMCPController"]
