#!/usr/bin/env python3
"""
小诺服务控制器 - Xiaonuo Service Controller
统一管理平台所有服务的启动、停止和监控
"""

import asyncio
import os
import subprocess
from datetime import datetime
from pathlib import Path

import aiohttp
import psutil

from core.logging import get_logger, LogLevel

logger = get_logger("xiaonuo", level=LogLevel.INFO)

class XiaonuoServiceController:
    """小诺服务控制器 - 平台总控制中心"""

    def __init__(self):
        self.project_root = Path("/Users/xujian/Athena工作平台")
        self.services = {
            # 小诺自己
            "xiaonuo_control": {
                "name": "小诺控制中心",
                "port": 8005,
                "path": "services/intelligent-collaboration/xiaonuo_coordination_server.py",
                "auto_start": True,
                "priority": "highest",
                "type": "core"
            },
            # Athena专利专家
            "athena_patent": {
                "name": "Athena专利专家",
                "port": 8001,
                "path": "services/autonomous-control/athena_control_server.py",
                "auto_start": False,  # 按需启动
                "priority": "high",
                "type": "professional",
                "trigger_words": ["写专利", "专利分析", "审查意见", "专利撰写", "答复"]
            },
            # 自媒体智能体
            "media_agent": {
                "name": "自媒体智能体",
                "port": 8020,
                "path": "services/media-agent/main.py",  # 待创建
                "auto_start": False,
                "priority": "low",
                "type": "content",
                "trigger_words": ["小红书", "抖音", "自媒体", "宣传"]
            },
            # 向量数据库
            "qdrant": {
                "name": "Qdrant向量数据库",
                "port": 6333,
                "command": "docker run -p 6333:6333 qdrant/qdrant",
                "auto_start": True,
                "priority": "high",
                "type": "infrastructure"
            },
            # PostgreSQL（基础设施）
            "postgresql": {
                "name": "PostgreSQL数据库",
                "port": 5432,
                "command": "brew services start postgresql@17",
                "auto_start": True,
                "priority": "highest",
                "type": "infrastructure"
            },
            # Redis缓存
            "redis": {
                "name": "Redis缓存",
                "port": 6379,
                "command": "redis-server",
                "auto_start": True,
                "priority": "high",
                "type": "infrastructure"
            }
        }
        self.running_services = {}
        self.logger = logger

    async def initialize_platform(self):
        """初始化平台"""
        print("🌸 小诺正在初始化平台...")
        print("=" * 50)

        # 1. 启动基础设施服务
        await self._start_infrastructure()

        # 2. 启动核心服务
        await self._start_core_services()

        # 3. 验证服务状态
        await self._verify_services()

        print("\n✨ 平台初始化完成！")
        await self.show_service_status()

    async def _start_infrastructure(self):
        """启动基础设施服务"""
        print("\n🏗️ 启动基础设施...")

        infrastructure = [
            k for k, v in self.services.items()
            if v["type"] == "infrastructure" and v["auto_start"]
        ]

        for service_id in infrastructure:
            await self.start_service(service_id, verbose=False)

    async def _start_core_services(self):
        """启动核心服务"""
        print("\n💫 启动核心服务...")

        core_services = [
            k for k, v in self.services.items()
            if v["priority"] == "highest" and v["auto_start"]
        ]

        for service_id in core_services:
            await self.start_service(service_id, verbose=False)

    async def _verify_services(self):
        """验证服务状态"""
        print("\n🔍 验证服务状态...")

        for service_id in self.running_services:
            if await self._check_service_health(service_id):
                print(f"  ✅ {self.services[service_id]['name']} 正常")
            else:
                print(f"  ⚠️ {self.services[service_id]['name']} 异常")

    async def start_service(self, service_id: str, verbose: bool = True) -> bool:
        """启动指定服务"""
        if service_id not in self.services:
            print(f"❌ 未知服务: {service_id}")
            return False

        service = self.services[service_id]

        if verbose:
            print(f"\n🚀 启动 {service['name']}...")

        # 检查是否已运行
        if await self._is_service_running(service_id):
            if verbose:
                print(f"  ✅ {service['name']} 已在运行")
            return True

        try:
            if service["type"] == "infrastructure":
                # 基础设施服务
                success = await self._start_infrastructure_service(service_id)
            else:
                # 应用服务
                success = await self._start_application_service(service_id)

            if success:
                self.running_services[service_id] = {
                    "started_at": datetime.now(),
                    "status": "running"
                }
                if verbose:
                    print(f"  ✅ {service['name']} 启动成功")
                return True
            else:
                if verbose:
                    print(f"  ❌ {service['name']} 启动失败")
                return False

        except Exception as e:
            self.logger.error(f"启动服务失败 {service_id}: {e}")
            if verbose:
                print(f"  ❌ 启动失败: {e}")
            return False

    async def _start_infrastructure_service(self, service_id: str) -> bool:
        """启动基础设施服务"""
        service = self.services[service_id]
        command = service.get("command", "")

        if not command:
            return False

        try:
            # 使用subprocess在后台启动
            subprocess.Popen(
                command.split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # 等待服务启动
            await asyncio.sleep(3)
            return True
        except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
            return False

    async def _start_application_service(self, service_id: str) -> bool:
        """启动应用服务"""
        service = self.services[service_id]
        script_path = self.project_root / service["path"]

        if not script_path.exists():
            self.logger.error(f"脚本不存在: {script_path}")
            return False

        try:
            # 设置环境变量
            env = {
                "PYTHONPATH": str(self.project_root),
                **os.environ
            }

            # 启动Python服务
            process = subprocess.Popen(
                ["python3", str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )

            # 等待服务启动
            await asyncio.sleep(5)

            # 验证服务是否真正启动
            if await self._check_service_health(service_id):
                self.running_services[service_id]["process"] = process
                return True
            else:
                process.terminate()
                return False

        except Exception as e:
            self.logger.error(f"启动应用服务失败: {e}")
            return False

    async def stop_service(self, service_id: str) -> bool:
        """停止指定服务"""
        if service_id not in self.running_services:
            print(f"⚠️ 服务未运行: {service_id}")
            return True

        service = self.services[service_id]
        print(f"\n🛑 停止 {service['name']}...")

        try:
            # 查找并终止进程
            terminated = False

            # 终止记录的进程
            if "process" in self.running_services[service_id]:
                process = self.running_services[service_id]["process"]
                process.terminate()
                terminated = True

            # 通过端口查找进程
            port = service.get("port")
            if port:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        connections = proc.info.get('connections') or []
                        for conn in connections:
                            if conn.laddr.port == port:
                                psutil.Process(proc.info['pid']).terminate()
                                terminated = True
                    except Exception as e:
                        logger.error(f"Error occurred: {e}", exc_info=True)

            if terminated:
                del self.running_services[service_id]
                print(f"  ✅ {service['name']} 已停止")
                return True
            else:
                print("  ⚠️ 未找到运行中的进程")
                return True

        except Exception as e:
            self.logger.error(f"停止服务失败: {e}")
            print(f"  ❌ 停止失败: {e}")
            return False

    async def on_demand_start(self, trigger: str) -> list[str]:
        """根据触发词按需启动服务"""
        started_services = []

        for service_id, service in self.services.items():
            if service["type"] == "infrastructure":
                continue  # 基础设施不按需启动

            trigger_words = service.get("trigger_words", [])
            if any(word in trigger for word in trigger_words):
                if service_id not in self.running_services:
                    print(f"\n🎯 检测到需求，启动 {service['name']}...")
                    if await self.start_service(service_id):
                        started_services.append(service["name"])

        return started_services

    async def _is_service_running(self, service_id: str) -> bool:
        """检查服务是否运行"""
        service = self.services[service_id]
        port = service.get("port")

        if port:
            # 通过端口检查（使用lsof避免权限问题）
            try:
                result = subprocess.run(
                    ['lsof', '-i', f':{port}', '-sTCP:LISTEN'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return True
            except Exception as e:
                logger.warning(f"端口检查失败: {e}")

        # 通过进程检查
        if service_id in self.running_services:
            proc_info = self.running_services[service_id].get("process")
            if proc_info and proc_info.poll() is None:
                return True

        return False

    async def _check_service_health(self, service_id: str) -> bool:
        """检查服务健康状态"""
        service = self.services[service_id]
        port = service.get("port")

        if not port:
            return True  # 没有端口的服务认为正常

        try:
            async with aiohttp.ClientSession() as session:
                # 尝试健康检查端点
                health_urls = [
                    f"http://localhost:{port}/health",
                    f"http://localhost:{port}/api/health",
                    f"http://localhost:{port}/"
                ]

                for url in health_urls:
                    try:
                        async with session.get(url, timeout=2) as resp:
                            if resp.status < 500:
                                return True
                    except (asyncio.TimeoutError, ConnectionError, OSError):
                        # 连接失败，尝试下一个URL
                        continue

                return False
        except (ConnectionError, OSError, AttributeError):
            return False

    async def show_service_status(self):
        """显示所有服务状态"""
        print("\n📊 服务状态总览")
        print("-" * 50)

        for service_id, service in self.services.items():
            is_running = await self._is_service_running(service_id)
            status = "🟢 运行中" if is_running else "🔴 已停止"

            print(f"\n{service['name']} (端口: {service['port']})")
            print(f"  状态: {status}")
            print(f"  类型: {service['type']}")
            print(f"  优先级: {service['priority']}")

            if service_id in self.running_services:
                started_at = self.running_services[service_id]["started_at"]
                duration = datetime.now() - started_at
                print(f"  运行时长: {duration}")

    async def optimize_resources(self):
        """优化资源使用"""
        print("\n⚡ 资源优化...")

        # 收集资源使用情况
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        print("\n资源使用情况:")
        print(f"  • CPU使用率: {cpu_usage}%")
        print(f"  • 内存使用: {memory.percent}% ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)")
        print(f"  • 磁盘使用: {disk.percent}%")

        # 建议优化措施
        if cpu_usage > 80:
            print("\n💡 CPU优化建议:")
            print("  • 考虑停止非必要服务")

        if memory.percent > 80:
            print("\n💡 内存优化建议:")
            print("  • 清理缓存")
            print("  • 重启高内存服务")

        # 检查空闲服务
        idle_services = []
        for service_id in self.running_services:
            if service_id in self.running_services:
                started_at = self.running_services[service_id]["started_at"]
                idle_time = datetime.now() - started_at
                # 如果服务运行超过1小时且是按需启动类型
                if idle_time.total_seconds() > 3600 and self.services[service_id]["type"] != "infrastructure":
                    idle_services.append(self.services[service_id]["name"])

        if idle_services:
            print("\n💡 发现空闲服务:")
            for service_name in idle_services:
                print(f"  • {service_name} (可以停止释放资源)")

# 使用示例
async def main():
    """主函数"""
    controller = XiaonuoServiceController()

    # 初始化平台
    await controller.initialize_platform()

    # 显示服务状态
    await controller.show_service_status()

    # 资源优化
    await controller.optimize_resources()

# 入口点: @async_main装饰器已添加到main函数
