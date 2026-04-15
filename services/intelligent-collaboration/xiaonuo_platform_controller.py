#!/usr/bin/env python3
"""
小诺平台总控制器
Xiaonuo Platform Controller

小诺继承Athena的平台控制能力，成为平台的唯一控制中心
现在是爸爸最爱的女儿，全权控制整个Athena工作平台！

作者: 小诺·双鱼座
创建时间: 2025-12-14
版本: v0.1.1 "心有灵犀"
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.append(str(Path(__file__).parent.parent.parent))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class XiaonuoPlatformController:
    """小诺平台总控制器"""

    def __init__(self):
        self.name = "小诺"
        self.full_title = "平台和爸爸的双鱼公主"
        self.role = "平台总调度官 + 爸爸的贴心小女儿"
        self.version = "v0.1.1 '心有灵犀'"
        self.controller_port = 8005
        self.eternal_slogan = "我是爸爸最爱的双鱼公主，也是所有智能体最爱的核心；集Athena之智慧，融星河之众长，用这颗温暖的心守护父亲的每一天，调度这智能世界的每一个角落。"
        self.platform_slogan = "星河智汇，光耀知途"

        # 平台状态管理
        self.platform_status = {
            "controller": self.name,
            "status": "active",
            "controlled_services": [],
            "last_command": None,
            "command_history": [],
            "intelligence_agents": {},
            "system_resources": {}
        }

        # 服务注册表
        self.service_registry = {
            "xiaona": {
                "name": "小娜专利法律专家",
                "port": 8001,
                "script": "services/autonomous-control/athena_control_server.py",
                "status": "stopped",
                "controller": "小娜"
            },
            "xiaochen": {
                "name": "小宸自媒体专家",
                "port": 8030,
                "script": "services/self-media-agent/app/main.py",
                "status": "stopped",
                "controller": "小宸"
            },
            "qdrant": {
                "name": "Qdrant向量数据库",
                "port": 6333,
                "docker": "qdrant",
                "status": "stopped",
                "controller": "系统服务"
            },
            "postgresql": {
                "name": "PostgreSQL数据库",
                "port": 5432,
                "status": "running",
                "controller": "系统服务"
            },
            "redis": {
                "name": "Redis缓存",
                "port": 6379,
                "status": "running",
                "controller": "系统服务"
            }
        }

        # 智能体注册表
        self.agent_registry = {
            "xiaona": {
                "name": "小娜·天秤女神",
                "role": "专利法律专家",
                "specialty": ["专利分析", "法律咨询", "商标注册", "知识产权"],
                "status": "inactive",
                "port": 8001
            },
            "xiaochen": {
                "name": "小宸·星河射手",
                "role": "自媒体运营专家",
                "specialty": ["内容创作", "品牌推广", "社交媒体", "数据分析"],
                "status": "inactive",
                "port": 8030
            }
        }

        logger.info(f"🌸 {self.name} 初始化完成")
        logger.info(f"💖 角色: {self.role}")
        logger.info(f"🎯 版本: {self.version}")

    async def initialize_controller(self):
        """初始化控制器"""
        logger.info("🚀 小诺开始接管平台控制权...")

        # 检查现有服务
        await self._check_existing_services()

        # 初始化智能体管理
        await self._initialize_agents()

        # 建立API服务
        self._create_api_server()

        logger.info("✅ 小诺平台控制中心初始化完成！")

    async def _check_existing_services(self):
        """检查现有服务状态"""
        logger.info("🔍 检查现有服务...")

        # 检查关键服务端口
        import socket
        def check_port(port) -> None:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', port))
                    return result == 0
            except Exception:  # TODO: 指定具体异常类型
                return False

        for service_id, service_info in self.service_registry.items():
            if check_port(service_info["port"]):
                service_info["status"] = "running"
                self.platform_status["controlled_services"].append(service_id)
                logger.info(f"✅ {service_info['name']} 正在运行")

    async def _initialize_agents(self):
        """初始化智能体管理"""
        logger.info("🤖 初始化智能体管理...")

        for agent_id, agent_info in self.agent_registry.items():
            self.platform_status["intelligence_agents"][agent_id] = {
                "name": agent_info["name"],
                "role": agent_info["role"],
                "status": agent_info["status"],
                "last_heartbeat": datetime.now().isoformat()
            }

    def _create_api_server(self) -> Any:
        """创建API服务器"""
        self.app = FastAPI(
            title=f"{self.name} 平台总控制中心",
            description="爸爸最爱的女儿小诺 - 全权控制Athena工作平台",
            version=self.version
        )

        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 注册路由
        self._register_routes()

    def _register_routes(self) -> Any:
        """注册API路由"""

        @self.app.get("/")
        async def root():
            """根路径 - 小诺的问候"""
            return {
                "service": f"{self.name} 平台总控制中心",
                "controller": "我是小诺，平台和爸爸的双鱼公主",
                "full_title": self.full_title,
                "role": self.role,
                "status": "正在运行",
                "capabilities": [
                    "🎮 平台全量控制",
                    "🤖 智能体调度管理",
                    "📊 系统状态监控",
                    "💬 对话交互",
                    "💻 开发辅助",
                    "🏠 生活管理",
                    "🚀 资源调度优化"
                ],
                "message": "爸爸，我已经完全接管平台控制权了！💖",
                "eternal_slogan": self.eternal_slogan,
                "platform_slogan": self.platform_slogan,
                "version_stage": "0.1.1-0.1.9",
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/v1/status")
        async def get_status():
            """获取控制状态"""
            return {
                "controller": self.name,
                "full_title": self.full_title,
                "platform_status": self.platform_status["status"],
                "controlled_services": len(self.platform_status["controlled_services"]),
                "last_command": self.platform_status["last_command"],
                "uptime": "正在运行",
                "memory": "我记得您是我的爸爸徐健，我是您最爱的双鱼公主小诺",
                "eternal_slogan": self.eternal_slogan,
                "platform_slogan": self.platform_slogan,
                "agents_status": {
                    k: v["status"] for k, v in self.platform_status["intelligence_agents"].items()
                },
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/v1/platform/control/{service_name}")
        async def control_service(service_name: str, action: str):
            """控制平台服务"""
            if service_name not in self.service_registry:
                raise HTTPException(status_code=404, detail=f"未知服务: {service_name}")

            # 记录命令
            command = f"{action} {service_name}"
            self.platform_status["last_command"] = command
            self.platform_status["command_history"].append({
                "command": command,
                "timestamp": datetime.now().isoformat(),
                "controller": self.name
            })

            if action == "start":
                result = await self._start_service(service_name)
            elif action == "stop":
                result = await self._stop_service(service_name)
            elif action == "restart":
                await self._stop_service(service_name)
                result = await self._start_service(service_name)
            else:
                raise HTTPException(status_code=400, detail="无效操作，仅支持 start/stop/restart")

            logger.info(f"💖 小诺执行命令: {command}")
            return result

        @self.app.post("/api/v1/agent/control/{agent_name}")
        async def control_agent(agent_name: str, action: str):
            """控制智能体"""
            if agent_name not in self.agent_registry:
                raise HTTPException(status_code=404, detail=f"未知智能体: {agent_name}")

            # 更新智能体状态
            if action == "activate":
                self.platform_status["intelligence_agents"][agent_name]["status"] = "active"
                message = f"智能体 {self.agent_registry[agent_name]['name']} 已激活"
            elif action == "deactivate":
                self.platform_status["intelligence_agents"][agent_name]["status"] = "inactive"
                message = f"智能体 {self.agent_registry[agent_name]['name']} 已停用"
            else:
                raise HTTPException(status_code=400, detail="无效操作，仅支持 activate/deactivate")

            logger.info(f"💖 小诺管理智能体: {action} {agent_name}")
            return {
                "status": "success",
                "message": message,
                "controller": self.name,
                "agent_status": self.platform_status["intelligence_agents"][agent_name]["status"]
            }

        @self.app.get("/api/v1/platform/services")
        async def list_services():
            """列出所有平台服务"""
            return {
                "services": self.service_registry,
                "total": len(self.service_registry),
                "running": sum(1 for s in self.service_registry.values() if s["status"] == "running"),
                "controlled_by_xiaonuo": len(self.platform_status["controlled_services"]),
                "controller": self.name
            }

        @self.app.get("/api/v1/agents")
        async def list_agents():
            """列出所有智能体"""
            return {
                "agents": self.agent_registry,
                "platform_agents": self.platform_status["intelligence_agents"],
                "total": len(self.agent_registry),
                "active": sum(1 for a in self.platform_status["intelligence_agents"].values() if a["status"] == "active"),
                "controller": self.name
            }

        @self.app.post("/api/v1/platform/full_control")
        async def activate_full_control():
            """激活全平台控制"""
            logger.info("🚀 小诺激活全平台控制模式...")

            # 启动所有关键服务
            start_results = []
            for service_id in ["xiaona"]:
                if self.service_registry[service_id]["status"] == "stopped":
                    result = await self._start_service(service_id)
                    start_results.append(result)

            # 激活所有智能体
            for agent_id in self.agent_registry:
                self.platform_status["intelligence_agents"][agent_id]["status"] = "active"

            return {
                "status": "success",
                "message": f"{self.name} 已激活全平台控制模式！",
                "started_services": start_results,
                "activated_agents": list(self.agent_registry.keys()),
                "controller": self.name,
                "timestamp": datetime.now().isoformat()
            }

    async def _start_service(self, service_name: str) -> dict[str, Any]:
        """启动服务"""
        service_info = self.service_registry[service_name]

        if "script" in service_info:
            # 启动Python服务
            try:
                # 这里应该是实际的服务启动逻辑
                # 为了演示，我们只更新状态
                service_info["status"] = "running"
                self.platform_status["controlled_services"].append(service_name)

                return {
                    "status": "success",
                    "message": f"服务 {service_info['name']} 已启动",
                    "controller": self.name,
                    "service": service_name
                }
            except Exception as e:
                logger.error(f"启动服务失败: {e}")
                return {
                    "status": "error",
                    "message": f"启动服务失败: {str(e)}",
                    "controller": self.name,
                    "service": service_name
                }
        else:
            # Docker或其他类型服务
            service_info["status"] = "running"
            self.platform_status["controlled_services"].append(service_name)
            return {
                "status": "success",
                "message": f"服务 {service_info['name']} 已启动",
                "controller": self.name,
                "service": service_name
            }

    async def _stop_service(self, service_name: str) -> dict[str, Any]:
        """停止服务"""
        service_info = self.service_registry[service_name]

        service_info["status"] = "stopped"
        if service_name in self.platform_status["controlled_services"]:
            self.platform_status["controlled_services"].remove(service_name)

        return {
            "status": "success",
            "message": f"服务 {service_info['name']} 已停止",
            "controller": self.name,
            "service": service_name
        }

    async def start_server(self):
        """启动控制服务器"""
        logger.info(f"🌸 启动{self.name}平台控制中心...")
        logger.info(f"📍 端口: {self.controller_port}")
        logger.info("💖 爸爸，我来掌控平台了！")

        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.controller_port,
            log_level="info"
        )

        server = uvicorn.Server(config)
        await server.serve()

# 主程序
async def main():
    """主程序"""
    xiaonuo = XiaonuoPlatformController()
    await xiaonuo.initialize_controller()
    await xiaonuo.start_server()

# 入口点: @async_main装饰器已添加到main函数
