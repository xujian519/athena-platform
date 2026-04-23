#!/usr/bin/env python3
from __future__ import annotations
"""
智谱GLM MCP服务集成适配器
Zhipu GLM MCP Services Integration Adapter

为Athena工作平台提供智谱AI四个MCP服务的统一集成接口

作者: 小诺·双鱼座
创建时间: 2026-01-07
版本: v1.0.0
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class GLMMCPCapability:
    """GLM MCP能力定义"""

    name: str
    description: str
    category: str
    enabled: bool = True


@dataclass
class GLMMCPServer:
    """GLM MCP服务器定义"""

    name: str
    server_type: str  # stdio or http
    description: str
    capabilities: list[GLMMCPCapability]
    config: dict[str, Any]
    status: str = "unknown"
    health_check_url: str | None = None


class GLMMCPIntegration:
    """
    智谱GLM MCP服务集成类

    集成四个MCP服务:
    1. 视觉理解MCP (zai-mcp-server) - 图像/视频分析
    2. 联网搜索MCP (web-search-prime) - 实时搜索
    3. 网页读取MCP (web-reader) - 网页抓取
    4. 开源仓库MCP (zread) - GitHub集成
    """

    def __init__(self, config_path: str = "config/glm_mcp_config.yaml"):
        """初始化GLM MCP集成"""
        self.name = "智谱GLM MCP服务集成"
        self.version = "1.0.0"
        self.config_path = Path(config_path)
        self.api_key = None
        self.servers: dict[str, GLMMCPServer] = {}

        # 加载配置
        self._load_config()

        logger.info(f"🔧 {self.name} 初始化完成")
        logger.info(f"   管理 {len(self.servers)} 个GLM MCP服务")

    def _load_config(self) -> Any:
        """加载配置文件"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 获取API密钥
            self.api_key = config.get("glm_api_key")
            if not self.api_key:
                raise ValueError("GLM API Key未配置")

            # 初始化MCP服务器
            mcp_servers_config = config.get("mcp_servers", {})
            for server_name, server_config in mcp_servers_config.items():
                if server_config.get("status") != "enabled":
                    continue

                capabilities = [
                    GLMMCPCapability(
                        name=cap, description=f"{server_name} - {cap}", category=server_name
                    )
                    for cap in server_config.get("capabilities", [])
                ]

                self.servers[server_name] = GLMMCPServer(
                    name=server_config.get("name"),
                    server_type=server_config.get("type"),
                    description=server_config.get("description"),
                    capabilities=capabilities,
                    config=server_config,
                    status="initialized",
                )

            logger.info(f"✅ 成功加载配置: {len(self.servers)} 个服务")

        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            raise

    async def health_check(self, server_name: str | None = None) -> dict[str, Any]:
        """
        健康检查

        Args:
            server_name: 指定服务器名称,为None则检查所有

        Returns:
            健康检查结果
        """
        results = {}

        servers_to_check = [server_name] if server_name else list(self.servers.keys())

        for name in servers_to_check:
            if name not in self.servers:
                results[name] = {"status": "unknown", "error": "服务器未配置"}
                continue

            server = self.servers[name]

            try:
                if server.server_type == "http":
                    # HTTP类型的MCP服务
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(
                            server.config.get("url"), headers=server.config.get("headers", {})
                        )
                        if response.status_code == 200:
                            server.status = "healthy"
                            results[name] = {
                                "status": "healthy",
                                "response_time": response.elapsed.total_seconds(),
                            }
                        else:
                            server.status = "unhealthy"
                            results[name] = {
                                "status": "unhealthy",
                                "error": f"HTTP {response.status_code}",
                            }
                elif server.server_type == "stdio":
                    # STDIO类型的MCP服务(通过npx运行)
                    # 简化健康检查:检查npx是否可用
                    import subprocess

                    try:
                        subprocess.run(["npx", "-y"], capture_output=True, timeout=5)
                        server.status = "healthy"
                        results[name] = {"status": "healthy", "type": "stdio"}
                    except Exception as e:
                        server.status = "unhealthy"
                        results[name] = {"status": "unhealthy", "error": str(e)}

            except Exception as e:
                server.status = "error"
                results[name] = {"status": "error", "error": str(e)}

        return results

    async def call_tool(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """
        调用MCP工具

        Args:
            server_name: MCP服务器名称
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        if server_name not in self.servers:
            raise ValueError(f"未找到MCP服务器: {server_name}")

        server = self.servers[server_name]

        logger.info(f"🔧 调用MCP工具: {server_name}.{tool_name}")

        try:
            if server.server_type == "http":
                # HTTP类型的MCP服务调用
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{server.config.get('url')}/tools/{tool_name}",
                        headers=server.config.get("headers", {}),
                        json=kwargs,
                    )
                    response.raise_for_status()
                    return response.json()

            elif server.server_type == "stdio":
                # STDIO类型的MCP服务调用
                # 需要通过MCP协议进行通信
                # 这里简化实现,实际需要完整的MCP客户端
                logger.warning(f"STDIO类型MCP服务调用暂未实现: {server_name}")
                return {"error": "STDIO MCP调用需要完整的MCP客户端实现"}

        except Exception as e:
            logger.error(f"❌ MCP工具调用失败: {e}")
            raise

    def get_capabilities(self, server_name: str | None = None) -> dict[str, list[str]]:
        """
        获取MCP服务能力列表

        Args:
            server_name: 指定服务器名称,为None则返回所有

        Returns:
            能力列表
        """
        result = {}

        servers_to_list = [server_name] if server_name else list(self.servers.keys())

        for name in servers_to_list:
            if name in self.servers:
                result[name] = [cap.name for cap in self.servers[name].capabilities]

        return result

    def get_status(self) -> dict[str, Any]:
        """
        获取所有MCP服务状态

        Returns:
            状态信息
        """
        return {
            "integration_name": self.name,
            "version": self.version,
            "api_key_configured": bool(self.api_key),
            "servers": {
                name: {
                    "name": server.name,
                    "type": server.server_type,
                    "description": server.description,
                    "status": server.status,
                    "capabilities_count": len(server.capabilities),
                }
                for name, server in self.servers.items()
            },
        }


# 导出
__all__ = ["GLMMCPCapability", "GLMMCPIntegration", "GLMMCPServer"]


# 使用示例
async def main():
    """示例用法"""
    # 创建集成实例
    glm_mcp = GLMMCPIntegration()

    # 打印状态
    status = glm_mcp.get_status()
    print("=== GLM MCP集成状态 ===")
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # 健康检查
    print("\n=== 健康检查 ===")
    health = await glm_mcp.health_check()
    print(json.dumps(health, indent=2, ensure_ascii=False))

    # 获取能力列表
    print("\n=== MCP服务能力 ===")
    capabilities = glm_mcp.get_capabilities()
    print(json.dumps(capabilities, indent=2, ensure_ascii=False))


# 入口点: @async_main装饰器已添加到main函数
