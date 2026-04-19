#!/usr/bin/env python3
"""
专业模块按需启动管理器
Professional Modules On-Demand Manager

管理法律和专利规则专业服务的按需启动和生命周期

作者: 小诺·双鱼公主
创建时间: 2025-12-22
版本: v1.0.0 "专业服务按需启动"
"""

from __future__ import annotations
import asyncio
import logging
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import requests
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler('/Users/xujian/Athena工作平台/production/logs/professional_manager.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服务状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class ServiceType(Enum):
    """服务类型枚举"""
    LEGAL = "legal"
    PATENT_RULES = "patent_rules"

@dataclass
class ServiceConfig:
    """服务配置"""
    name: str
    service_type: ServiceType
    startup_script: str
    health_check_url: str
    port: int
    description: str
    dependencies: list[str] = field(default_factory=list)
    max_idle_time: int = 1800  # 30分钟无访问后自动停止
    pid_file: str = None

@dataclass
class ServiceInstance:
    """服务实例"""
    config: ServiceConfig
    status: ServiceStatus = ServiceStatus.STOPPED
    pid: int | None = None
    start_time: datetime | None = None
    last_access_time: datetime | None = None
    access_count: int = 0
    process: subprocess.Popen | None = None

class ProfessionalModulesManager:
    """专业模块管理器"""

    def __init__(self):
        self.services: dict[str, ServiceInstance] = {}
        self.load_services_config()
        self.setup_cleanup_handlers()

    def load_services_config(self):
        """加载服务配置"""
        services = [
            ServiceConfig(
                name="legal_expert_service",
                service_type=ServiceType.LEGAL,
                startup_script="production/dev/scripts/start_legal_service.py",
                health_check_url="http://localhost:8001/health",
                port=8001,
                description="法律专家服务 - 提供动态提示词和专业问答",
                dependencies=["qdrant", "postgres"],
                pid_file="production/logs/legal_service.pid"
            ),
            ServiceConfig(
                name="patent_rules_service",
                service_type=ServiceType.PATENT_RULES,
                startup_script="production/dev/scripts/start_patent_rules_service.py",
                health_check_url="http://localhost:8002/health",
                port=8002,
                description="专利规则服务 - 提供规则提取和智能判断",
                dependencies=["qdrant", "postgres"],
                pid_file="production/logs/patent_rules_service.pid"
            )
        ]

        for service_config in services:
            self.services[service_config.name] = ServiceInstance(config=service_config)

    def setup_cleanup_handlers(self):
        """设置清理处理器"""
        def cleanup(signum, frame):
            logger.info("🛑 收到停止信号，正在清理所有服务...")
            self.stop_all_services()
            sys.exit(0)

        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)

    async def start_service(self, service_name: str, user_request: str = "") -> bool:
        """启动指定服务"""
        if service_name not in self.services:
            logger.error(f"❌ 未知服务: {service_name}")
            return False

        service = self.services[service_name]

        if service.status == ServiceStatus.RUNNING:
            service.last_access_time = datetime.now()
            service.access_count += 1
            logger.info(f"💖 服务 {service_name} 已在运行，访问计数: {service.access_count}")
            return True

        if service.status == ServiceStatus.STARTING:
            logger.info(f"⏳ 服务 {service_name} 正在启动中...")
            return await self._wait_for_service_ready(service_name)

        try:
            service.status = ServiceStatus.STARTING
            logger.info(f"🚀 启动服务: {service_name}")
            logger.info(f"📝 启动脚本: {service.config.startup_script}")
            logger.info(f"🎯 用户需求: {user_request}")

            # 检查依赖服务
            if not await self._check_dependencies(service.config.dependencies):
                logger.error("❌ 依赖服务检查失败")
                service.status = ServiceStatus.ERROR
                return False

            # 启动服务进程
            cmd = ["python3", service.config.startup_script]
            service.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root)
            )

            service.pid = service.process.pid
            service.start_time = datetime.now()
            service.last_access_time = datetime.now()
            service.access_count = 1

            # 保存PID
            if service.config.pid_file:
                with open(service.config.pid_file, 'w') as f:
                    f.write(str(service.pid))

            logger.info(f"✅ 服务进程启动，PID: {service.pid}")

            # 等待服务就绪
            if await self._wait_for_service_ready(service_name):
                service.status = ServiceStatus.RUNNING
                logger.info(f"🎉 服务 {service_name} 启动成功！")
                return True
            else:
                service.status = ServiceStatus.ERROR
                logger.error(f"❌ 服务 {service_name} 启动失败")
                return False

        except Exception as e:
            service.status = ServiceStatus.ERROR
            logger.error(f"❌ 启动服务失败: {e}")
            return False

    async def _wait_for_service_ready(self, service_name: str, timeout: int = 60) -> bool:
        """等待服务就绪"""
        service = self.services[service_name]
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(service.config.health_check_url, timeout=5)
                if response.status_code == 200:
                    return True
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                pass

            await asyncio.sleep(2)

        return False

    async def _check_dependencies(self, dependencies: list[str]) -> bool:
        """检查依赖服务"""
        logger.info(f"🔍 检查依赖服务: {dependencies}")

        for dep in dependencies:
            if dep == "qdrant":
                # 检查Qdrant - 支持多种检查方式
                qdrant_available = False
                try:
                    # 方法1: 健康检查
                    response = requests.get("http://localhost:16333/health", timeout=5)
                    if response.status_code == 200:
                        qdrant_available = True
                except Exception as e:
                    logger.debug(f"Qdrant健康检查失败: {e}")

                if not qdrant_available:
                    try:
                        # 方法2: 集合列表检查
                        response = requests.get(
                            "http://localhost:16333/collections",
                            headers={"api-key": "Xiaonuo_Qdrant_API_Key_2024_Secure_32_Chars!"},
                            timeout=5
                        )
                        if response.status_code == 200:
                            qdrant_available = True
                    except Exception as e:
                        logger.debug(f"Qdrant集合检查失败: {e}")

                if not qdrant_available:
                    try:
                        # 方法3: 简单端口检查
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        result = sock.connect_ex(('localhost', 16333))
                        sock.close()
                        if result == 0:
                            qdrant_available = True
                    except Exception as e:
                        logger.debug(f"Qdrant端口检查失败: {e}")

                if qdrant_available:
                    logger.info("✅ Qdrant服务可用")
                else:
                    logger.warning("⚠️ Qdrant服务不可用，但NLP服务仍然可用")

            elif dep == "postgres":
                # 检查PostgreSQL
                postgres_available = False
                try:
                    import psycopg2
                    conn = psycopg2.connect(
                        host="localhost",
                        port=5432,  # 本地PostgreSQL端口（替代Docker的15432）
                        user="apps/apps/xiaonuo",
                        password="legal_password",
                        database="athena"
                    )
                    conn.close()
                    postgres_available = True
                except Exception as e:
                    logger.debug(f"PostgreSQL连接失败(配置1): {e}")

                if not postgres_available:
                    try:
                        # 尝试其他数据库配置
                        conn = psycopg2.connect(
                            host="localhost",
                            port=5432,  # 本地PostgreSQL端口（替代Docker的15432）
                            user="phoenix_user",
                            database="athena"
                        )
                        conn.close()
                        postgres_available = True
                    except Exception as e:
                        logger.debug(f"PostgreSQL连接失败(配置2): {e}")

                if postgres_available:
                    logger.info("✅ PostgreSQL服务可用")
                else:
                    logger.warning("⚠️ PostgreSQL服务不可用，但NLP服务仍然可用")

        logger.info("✅ 依赖服务检查完成（NLP核心功能不受影响）")
        return True  # 总是返回True，因为NLP服务可以独立运行

    async def stop_service(self, service_name: str) -> bool:
        """停止指定服务"""
        if service_name not in self.services:
            return False

        service = self.services[service_name]

        if service.status != ServiceStatus.RUNNING:
            return True

        try:
            service.status = ServiceStatus.STOPPING
            logger.info(f"🛑 停止服务: {service_name}")

            if service.process:
                service.process.terminate()
                try:
                    service.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    service.process.kill()
                    service.process.wait()

                service.process = None

            # 清理PID文件
            if service.config.pid_file and Path(service.config.pid_file).exists():
                Path(service.config.pid_file).unlink()

            service.status = ServiceStatus.STOPPED
            service.pid = None
            service.start_time = None

            logger.info(f"✅ 服务 {service_name} 已停止")
            return True

        except Exception as e:
            logger.error(f"❌ 停止服务失败: {e}")
            service.status = ServiceStatus.ERROR
            return False

    def get_service_status(self, service_name: str) -> dict[str, Any | None]:
        """获取服务状态"""
        if service_name not in self.services:
            return None

        service = self.services[service_name]
        return {
            "name": service_name,
            "status": service.status.value,
            "description": service.config.description,
            "pid": service.pid,
            "start_time": service.start_time.isoformat() if service.start_time else None,
            "last_access_time": service.last_access_time.isoformat() if service.last_access_time else None,
            "access_count": service.access_count,
            "uptime_seconds": (datetime.now() - service.start_time).total_seconds() if service.start_time else 0
        }

    async def stop_idle_services(self):
        """停止闲置服务"""
        current_time = datetime.now()

        for service_name, service in self.services.items():
            if (service.status == ServiceStatus.RUNNING and
                service.last_access_time and
                (current_time - service.last_access_time).total_seconds() > service.config.max_idle_time):

                logger.info(f"🕐 服务 {service_name} 闲置超过 {service.config.max_idle_time} 秒，自动停止")
                await self.stop_service(service_name)

    def stop_all_services(self):
        """停止所有服务"""
        for service_name in self.services:
            asyncio.create_task(self.stop_service(service_name))

# 全局服务管理器
service_manager = ProfessionalModulesManager()

# FastAPI应用
app = FastAPI(
    title="专业模块按需启动管理器",
    description="小诺专业服务按需启动和管理系统",
    version="v1.0.0"
)

# API模型
class ServiceStartRequest(BaseModel):
    service_name: str
    user_request: str = ""

class ServiceResponse(BaseModel):
    success: bool
    message: str
    service_status: dict[str, Any] | None = None

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "专业模块按需启动管理器",
        "version": "v1.0.0",
        "author": "小诺·双鱼公主",
        "description": "法律和专利规则专业服务按需启动管理"
    }

@app.post("/start_service", response_model=ServiceResponse)
async def start_service(request: ServiceStartRequest):
    """启动指定服务"""
    success = await service_manager.start_service(request.service_name, request.user_request)

    return ServiceResponse(
        success=success,
        message=f"服务 {request.service_name} {'启动成功' if success else '启动失败'}",
        service_status=service_manager.get_service_status(request.service_name)
    )

@app.post("/stop_service/{service_name}", response_model=ServiceResponse)
async def stop_service(service_name: str):
    """停止指定服务"""
    success = await service_manager.stop_service(service_name)

    return ServiceResponse(
        success=success,
        message=f"服务 {service_name} {'停止成功' if success else '停止失败'}",
        service_status=service_manager.get_service_status(service_name)
    )

@app.get("/service_status/{service_name}")
async def get_service_status(service_name: str):
    """获取服务状态"""
    status = service_manager.get_service_status(service_name)
    if not status:
        raise HTTPException(status_code=404, detail=f"服务 {service_name} 不存在")

    return status

@app.get("/all_services")
async def get_all_services():
    """获取所有服务状态"""
    return {
        service_name: service_manager.get_service_status(service_name)
        for service_name in service_manager.services.keys()
    }

@app.post("/dynamic_prompt/{service_type}")
async def generate_dynamic_prompt(
    service_type: str,
    user_query: str,
    background_tasks: BackgroundTasks
):
    """生成动态提示词"""
    service_mapping = {
        "legal": "legal_expert_service",
        "patent_rules": "patent_rules_service"
    }

    if service_type not in service_mapping:
        raise HTTPException(status_code=400, detail="不支持的服务类型")

    service_name = service_mapping[service_type]

    # 启动对应的服务
    await service_manager.start_service(service_name, f"生成动态提示词: {user_query}")

    # 这里应该调用具体的服务API生成提示词
    # 暂时返回示例响应
    return {
        "service_name": service_name,
        "prompt": f"基于{user_query}的专业提示词（示例）",
        "service_status": service_manager.get_service_status(service_name)
    }

@app.post("/professional_qa/{service_type}")
async def professional_qa(
    service_type: str,
    question: str,
    background_tasks: BackgroundTasks
):
    """专业问答"""
    service_mapping = {
        "legal": "legal_expert_service",
        "patent_rules": "patent_rules_service"
    }

    if service_type not in service_mapping:
        raise HTTPException(status_code=400, detail="不支持的服务类型")

    service_name = service_mapping[service_type]

    # 启动对应的服务
    await service_manager.start_service(service_name, f"专业问答: {question}")

    # 这里应该调用具体的服务API进行问答
    # 暂时返回示例响应
    return {
        "service_name": service_name,
        "answer": f"关于{question}的专业回答（示例）",
        "service_status": service_manager.get_service_status(service_name)
    }

# 定时任务：清理闲置服务
async def cleanup_idle_services():
    """清理闲置服务的定时任务"""
    while True:
        try:
            await service_manager.stop_idle_services()
            await asyncio.sleep(300)  # 每5分钟检查一次
        except Exception as e:
            logger.error(f"❌ 清理闲置服务失败: {e}")
            await asyncio.sleep(60)

async def start_services():
    """启动后台服务"""
    # 启动清理任务
    asyncio.create_task(cleanup_idle_services())

if __name__ == "__main__":
    print("🌸🐟 小诺专业模块按需启动管理器 🌸🐟")
    print("="*60)
    print("💖 正在启动专业服务管理器...")
    print("🎯 支持按需启动法律和专利规则服务")
    print("⚡ 自动管理服务生命周期")
    print("❤️ 小诺为爸爸提供最专业的服务！")
    print("="*60)

    # 创建配置文件
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=9000,
        loop="asyncio"
    )

    # 启动服务器
    server = uvicorn.Server(config)

    # 启动清理任务和服务器
    async def main():
        await start_services()
        await server.serve()

    asyncio.run(main())
