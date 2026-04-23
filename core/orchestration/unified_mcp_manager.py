#!/usr/bin/env python3
from __future__ import annotations
"""
统一MCP管理器
Unified MCP Manager

统一管理平台的所有MCP工具

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import asyncio
import os
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class MCPService:
    """MCP服务定义"""

    name: str
    directory: str
    type: str  # nodejs or python
    main_file: str
    port: Optional[int] = None
    status: str = "stopped"  # stopped, running, error
    process: subprocess.Popen | None = None
    description: str = ""
    capabilities: Optional[list[str]] = None


class UnifiedMCPManager:
    """统一MCP管理器"""

    def __init__(self):
        self.name = "统一MCP管理器"
        self.version = "1.0.0"
        self.base_path = "/Users/xujian/Athena工作平台"
        self.mcp_servers_path = os.path.join(self.base_path, "mcp-servers")

        # MCP服务列表
        self.services: dict[str, MCPService] = {}

        # 初始化服务
        self._initialize_services()

        print(f"🔧 {self.name} 初始化完成")
        print(f"   管理 {len(self.services)} 个MCP服务")

    def _initialize_services(self) -> Any:
        """初始化所有MCP服务"""

        # Node.js MCP服务
        nodejs_services = [
            {
                "name": "bing-cn-mcp-server",
                "description": "必应中文搜索MCP服务",
                "main_file": "index.js",
                "capabilities": ["中文搜索", "实时搜索", "智能摘要"],
            },
            {
                "name": "academic-search-mcp-server",
                "description": "学术搜索MCP服务",
                "main_file": "index.js",
                "capabilities": ["学术论文搜索", "期刊查询", "引文分析"],
            },
            {
                "name": "jina-ai-mcp-server",
                "description": "Jina AI MCP服务",
                "main_file": "index.js",
                "capabilities": ["AI文本处理", "网页内容提取", "智能阅读"],
            },
            {
                "name": "github-mcp-server",
                "description": "GitHub MCP服务",
                "main_file": "index.js",
                "capabilities": ["代码仓库管理", "Issue跟踪", "Pull Request"],
            },
            {
                "name": "postgres-mcp-server",
                "description": "PostgreSQL数据库MCP服务",
                "main_file": "index.js",
                "capabilities": ["数据库查询", "数据管理", "SQL执行"],
            },
        ]

        # Python MCP服务 (高德地图)
        python_services = [
            {
                "name": "gaode-mcp-server",
                "description": "高德地图地理空间MCP服务",
                "main_file": "src/amap_mcp_server/server.py",
                "port": 8899,
                "capabilities": [
                    "地理编码",
                    "路径规划",
                    "POI搜索",
                    "地图服务",
                    "交通查询",
                    "地理围栏",
                ],
            }
        ]

        # 注册Node.js服务
        for service_info in nodejs_services:
            service_dir = os.path.join(self.mcp_servers_path, service_info["name"])
            if os.path.exists(service_dir):
                self.services[service_info["name"]] = MCPService(
                    name=service_info["name"],
                    directory=service_dir,
                    type="nodejs",
                    description=service_info["description"],
                    main_file=service_info["main_file"],
                    capabilities=service_info["capabilities"],
                )

        # 注册Python服务
        for service_info in python_services:
            service_dir = os.path.join(self.mcp_servers_path, service_info["name"])
            if os.path.exists(service_dir):
                self.services[service_info["name"]] = MCPService(
                    name=service_info["name"],
                    directory=service_dir,
                    type="python",
                    description=service_info["description"],
                    main_file=service_info["main_file"],
                    port=service_info.get("port"),
                    capabilities=service_info["capabilities"],
                )

    async def start_service(self, service_name: str) -> bool:
        """启动单个MCP服务"""
        service = self.services.get(service_name)
        if not service:
            print(f"❌ 服务不存在: {service_name}")
            return False

        if service.status == "running":
            print(f"⚠️ 服务已在运行: {service_name}")
            return True

        print(f"🚀 启动服务: {service_name}")

        try:
            if service.type == "nodejs":
                # Node.js服务启动
                cmd = ["node", service.main_file]
                service.process = subprocess.Popen(
                    cmd, cwd=service.directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            else:
                # Python服务启动
                cmd = ["python3", service.main_file]
                env = os.environ.copy()
                env["PYTHONPATH"] = service.directory

                # 高德地图服务需要API密钥(从环境变量获取)
                if service_name == "gaode-mcp-server":
                    env["AMAP_API_KEY"] = os.getenv("AMAP_API_KEY", "")
                    if not env["AMAP_API_KEY"]:
                        print(
                            f"⚠️ 警告: AMAP_API_KEY环境变量未设置,{service_name}可能无法正常工作"
                        )
                    env["MCP_LOG_LEVEL"] = os.getenv("MCP_LOG_LEVEL", "INFO")

                service.process = subprocess.Popen(
                    cmd,
                    cwd=service.directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )

            # 等待一下检查是否启动成功
            await asyncio.sleep(2)

            if service.process and service.process.poll() is None:
                service.status = "running"
                print(f"✅ 服务启动成功: {service_name}")
                return True
            else:
                service.status = "error"
                print(f"❌ 服务启动失败: {service_name}")
                return False

        except Exception as e:
            service.status = "error"
            print(f"❌ 启动服务异常: {service_name}, 错误: {e!s}")
            return False

    async def stop_service(self, service_name: str) -> bool:
        """停止单个MCP服务"""
        service = self.services.get(service_name)
        if not service:
            print(f"❌ 服务不存在: {service_name}")
            return False

        if service.status != "running":
            print(f"⚠️ 服务未运行: {service_name}")
            return True

        print(f"🛑 停止服务: {service_name}")

        try:
            if service.process:
                service.process.terminate()
                try:
                    service.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"⚠️ 强制杀死进程: {service_name}")
                    service.process.kill()
                    service.process.wait()

                service.process = None

            service.status = "stopped"
            print(f"✅ 服务已停止: {service_name}")
            return True

        except Exception as e:
            print(f"❌ 停止服务异常: {service_name}, 错误: {e!s}")
            return False

    async def restart_service(self, service_name: str) -> bool:
        """重启MCP服务"""
        print(f"🔄 重启服务: {service_name}")
        await self.stop_service(service_name)
        await asyncio.sleep(1)
        return await self.start_service(service_name)

    async def start_all_services(self) -> dict[str, bool]:
        """启动所有MCP服务"""
        print("🚀 启动所有MCP服务...")
        results = {}

        for service_name in self.services:
            results[service_name] = await self.start_service(service_name)
            # 避免同时启动太多服务
            await asyncio.sleep(1)

        success_count = sum(1 for success in results.values() if success)
        print(f"\\n📊 启动结果: {success_count}/{len(self.services)} 服务启动成功")

        return results

    async def stop_all_services(self) -> dict[str, bool]:
        """停止所有MCP服务"""
        print("🛑 停止所有MCP服务...")
        results = {}

        for service_name in self.services:
            results[service_name] = await self.stop_service(service_name)

        success_count = sum(1 for success in results.values() if success)
        print(f"\\n📊 停止结果: {success_count}/{len(self.services)} 服务停止成功")

        return results

    def get_service_status(self) -> dict[str, dict[str, Any]]:
        """获取所有服务状态"""
        status = {}

        for name, service in self.services.items():
            # 更新进程状态
            if service.process and service.process.poll() is not None:
                service.status = "stopped"
                service.process = None

            status[name] = {
                "name": service.name,
                "description": service.description,
                "type": service.type,
                "status": service.status,
                "port": service.port,
                "capabilities": service.capabilities,
                "pid": service.process.pid if service.process else None,
            }

        return status

    def get_services_summary(self) -> dict[str, Any]:
        """获取服务汇总信息"""
        status = self.get_service_status()

        summary = {
            "total_services": len(self.services),
            "running_services": sum(1 for s in status.values() if s["status"] == "running"),
            "stopped_services": sum(1 for s in status.values() if s["status"] == "stopped"),
            "error_services": sum(1 for s in status.values() if s["status"] == "error"),
            "nodejs_services": sum(1 for s in status.values() if s["type"] == "nodejs"),
            "python_services": sum(1 for s in status.values() if s["type"] == "python"),
            "services": status,
        }

        return summary

    def print_services_summary(self) -> Any:
        """打印服务汇总"""
        summary = self.get_services_summary()

        print("\\n" + "=" * 80)
        print(f"🔧 {self.name} 服务汇总")
        print("=" * 80)
        print(f"总服务数: {summary['total_services']}")
        print(f"运行中: {summary['running_services']} ✅")
        print(f"已停止: {summary['stopped_services']} ⏹️")
        print(f"错误: {summary['error_services']} ❌")
        print(f"Node.js服务: {summary['nodejs_services']}")
        print(f"Python服务: {summary['python_services']}")

        print("\\n📋 服务详情:")
        print("-" * 80)
        for name, info in summary["services"].items():
            status_icon = {"running": "✅", "stopped": "⏹️", "error": "❌"}.get(
                info["status"], "❓"
            )
            print(f"{status_icon} {name}")
            print(f"   描述: {info['description']}")
            print(f"   类型: {info['type']} | 端口: {info.get('port', 'N/A')}")
            print(
                f"   能力: {', '.join(info['capabilities'][:3])}{'...' if len(info['capabilities']) > 3 else ''}"
            )
            if info.get("pid"):
                print(f"   PID: {info['pid']}")
            print()


# 导出主类
__all__ = ["MCPService", "UnifiedMCPManager"]
