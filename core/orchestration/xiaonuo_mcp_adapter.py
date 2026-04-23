#!/usr/bin/env python3
from __future__ import annotations
"""
小诺·双鱼公主MCP工具适配器
Xiaonuo MCP Tool Adapter

使小诺能够直接调用和控制MCP工具

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    service: str
    parameters: dict[str, Any]
    category: str

class XiaonuoMCPAdapter:
    """小诺·双鱼公主MCP工具适配器"""

    def __init__(self):
        self.name = "小诺·双鱼公主MCP工具适配器"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # MCP服务客户端缓存
        self.mcp_clients = {}

        # 工具注册表
        self.tool_registry = {}

        # 初始化工具
        self._initialize_tools()

        print(f"🔧 {self.name} 初始化完成")
        print(f"   注册工具: {len(self.tool_registry)} 个")

    def _initialize_tools(self) -> Any:
        """初始化所有MCP工具"""

        # 1. 高德地图工具
        gaode_tools = [
            MCPTool(
                name="gaode_geocode",
                description="地理编码:地址转坐标",
                service="gaode-mcp-server",
                parameters={
                    "address": {"type": "string", "required": True, "description": "地址"},
                    "city": {"type": "string", "required": False, "description": "城市"}
                },
                category="地理服务"
            ),
            MCPTool(
                name="gaode_poi_search",
                description="POI搜索:查找兴趣点",
                service="gaode-mcp-server",
                parameters={
                    "keywords": {"type": "string", "required": True, "description": "关键词"},
                    "location": {"type": "string", "required": False, "description": "中心位置"}
                },
                category="地理服务"
            ),
            MCPTool(
                name="gaode_route_planning",
                description="路径规划:计算路线",
                service="gaode-mcp-server",
                parameters={
                    "origin": {"type": "string", "required": True, "description": "起点"},
                    "destination": {"type": "string", "required": True, "description": "终点"},
                    "strategy": {"type": "string", "required": False, "description": "策略"}
                },
                category="地理服务"
            )
        ]

        # 2. 搜索工具
        search_tools = [
            MCPTool(
                name="bing_search_cn",
                description="必应中文搜索",
                service="bing-cn-mcp-server",
                parameters={
                    "query": {"type": "string", "required": True, "description": "搜索关键词"},
                    "count": {"type": "integer", "required": False, "description": "结果数量", "default": 10}
                },
                category="搜索服务"
            ),
            MCPTool(
                name="academic_search",
                description="学术文献搜索",
                service="academic-search-mcp-server",
                parameters={
                    "query": {"type": "string", "required": True, "description": "学术关键词"},
                    "field": {"type": "string", "required": False, "description": "研究领域"}
                },
                category="学术服务"
            )
        ]

        # 3. AI处理工具
        ai_tools = [
            MCPTool(
                name="jina_ai_process",
                description="Jina AI文本处理",
                service="jina-ai-mcp-server",
                parameters={
                    "text": {"type": "string", "required": True, "description": "待处理文本"},
                    "task": {"type": "string", "required": True, "description": "处理任务类型"}
                },
                category="AI服务"
            )
        ]

        # 4. 开发工具
        dev_tools = [
            MCPTool(
                name="github_search_repo",
                description="GitHub仓库搜索",
                service="github-mcp-server",
                parameters={
                    "query": {"type": "string", "required": True, "description": "搜索查询"},
                    "language": {"type": "string", "required": False, "description": "编程语言"}
                },
                category="开发服务"
            )
        ]

        # 5. 数据库工具
        db_tools = [
            MCPTool(
                name="postgres_query",
                description="PostgreSQL查询",
                service="postgres-mcp-server",
                parameters={
                    "sql": {"type": "string", "required": True, "description": "SQL查询"},
                    "database": {"type": "string", "required": False, "description": "数据库名"}
                },
                category="数据服务"
            )
        ]

        # 注册所有工具
        all_tools = gaode_tools + search_tools + ai_tools + dev_tools + db_tools
        for tool in all_tools:
            self.tool_registry[tool.name] = tool

    async def start_mcp_service(self, service_name: str) -> bool:
        """启动MCP服务"""
        if service_name in self.mcp_clients:
            return True

        # 获取服务路径
        service_dir = f"/Users/xujian/Athena工作平台/mcp-servers/{service_name}"

        if not os.path.exists(service_dir):
            self.logger.error(f"服务目录不存在: {service_dir}")
            return False

        # 启动服务进程
        try:
            if service_name == "gaode-mcp-server":
                # Python服务
                cmd = ["python3", "src/amap_mcp_server/server.py"]
                env = os.environ.copy()
                env["PYTHONPATH"] = service_dir
                # 使用环境变量获取API密钥
                env["AMAP_API_KEY"] = os.getenv("AMAP_API_KEY", "")
                if not env["AMAP_API_KEY"]:
                    self.logger.warning("AMAP_API_KEY环境变量未设置,高德地图服务可能无法正常工作")
            else:
                # Node.js服务
                cmd = ["node", "index.js"]
                env = os.environ.copy()

            process = subprocess.Popen(
                cmd,
                cwd=service_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # 初始化MCP会话
            await self._initialize_mcp_session(service_name, process)

            self.mcp_clients[service_name] = process
            self.logger.info(f"MCP服务启动成功: {service_name}")
            return True

        except Exception as e:
            self.logger.error(f"启动MCP服务失败: {service_name}, 错误: {str(e)}")
            return False

    async def _initialize_mcp_session(self, service_name: str, process: subprocess.Popen):
        """初始化MCP会话"""
        # 发送初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocol_version": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "client_info": {
                    "name": "XiaonuoMCPAdapter",
                    "version": "1.0.0"
                }
            }
        }

        # 发送请求
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # 读取响应
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if response.get("result"):
                # 发送initialized通知
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                process.stdin.write(json.dumps(initialized_notification) + "\n")
                process.stdin.flush()

    async def call_tool(self, tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """调用MCP工具"""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return {"error": f"工具不存在: {tool_name}"}

        # 确保服务已启动
        service_name = tool.service
        if service_name not in self.mcp_clients:
            if not await self.start_mcp_service(service_name):
                return {"error": f"无法启动服务: {service_name}"}

        # 获取客户端
        client = self.mcp_clients[service_name]

        # 调用工具
        try:
            call_request = {
                "jsonrpc": "2.0",
                "id": tool_name + "_" + str(int(asyncio.get_event_loop().time())),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }

            # 发送请求
            client.stdin.write(json.dumps(call_request) + "\n")
            client.stdin.flush()

            # 读取响应
            response_line = client.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                if "result" in response:
                    return response["result"]
                elif "error" in response:
                    return {"error": response["error"]}

        except Exception as e:
            self.logger.error(f"调用工具失败: {tool_name}, 错误: {str(e)}")
            return {"error": str(e)}

        return {"error": "未收到响应"}

    def get_available_tools(self, category: Optional[str] = None) -> list[dict[str, Any]]:
        """获取可用工具列表"""
        tools = []
        for tool in self.tool_registry.values():
            if category and tool.category != category:
                continue
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "service": tool.service,
                "category": tool.category,
                "parameters": tool.parameters
            })
        return tools

    async def auto_use_tool(self, user_request: str) -> dict[str, Any]:
        """智能选择并使用工具"""
        # 简单的意图识别
        request_lower = user_request.lower()

        # 地理相关
        if any(keyword in request_lower for keyword in ["地址", "坐标", "地图", "路线", "导航"]):
            if "地址转坐标" in request_lower or "地理编码" in request_lower:
                return await self.call_tool("gaode_geocode", {"address": user_request})
            elif "搜索" in request_lower and ("位置" in request_lower or "poi" in request_lower):
                return await self.call_tool("gaode_poi_search", {"keywords": user_request})
            elif "路线" in request_lower or "导航" in request_lower:
                # 这里需要更复杂的解析提取起点和终点
                return await self.call_tool("gaode_route_planning", {
                    "origin": "北京市",
                    "destination": "上海市"
                })

        # 搜索相关
        elif any(keyword in request_lower for keyword in ["搜索", "查找", "百度"]):
            if "学术" in request_lower or "论文" in request_lower:
                return await self.call_tool("academic_search", {"query": user_request})
            else:
                return await self.call_tool("bing_search_cn", {"query": user_request})

        # AI处理相关
        elif any(keyword in request_lower for keyword in ["处理文本", "ai", "智能"]):
            return await self.call_tool("jina_ai_process", {
                "text": user_request,
                "task": "summarize"
            })

        # 开发相关
        elif any(keyword in request_lower for keyword in ["github", "代码", "仓库"]):
            return await self.call_tool("github_search_repo", {"query": user_request})

        # 数据库相关
        elif any(keyword in request_lower for keyword in ["数据库", "查询", "sql"]):
            return await self.call_tool("postgres_query", {"sql": "SELECT version()"})

        return {"error": "无法识别您的需求,请更具体地描述"}

    async def shutdown(self):
        """关闭所有MCP服务"""
        for _service_name, client in self.mcp_clients.items():
            try:
                client.terminate()
                client.wait(timeout=5)
            except Exception as e:
                try:
                    client.kill()
                except (Exception):
                    logger.error(f"捕获(Exception)异常: {e}", exc_info=True)
        self.mcp_clients.clear()

# 导出主类
__all__ = ['XiaonuoMCPAdapter', 'MCPTool']
