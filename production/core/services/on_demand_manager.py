#!/usr/bin/env python3
"""
按需服务管理器
On-demand Service Manager for Athena Platform
"""

from __future__ import annotations
import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

class OnDemandService:
    """按需服务类"""
    def __init__(self, name: str, port: int, script_path: str, health_endpoint: str = "/"):
        self.name = name
        self.port = port
        self.script_path = Path(script_path)
        self.health_endpoint = health_endpoint
        self.base_url = f"http://localhost:{port}"
        self.process: subprocess.Popen | None = None
        self.start_time: float | None = None
        self.last_used: float | None = None
        self.max_idle_time = 300  # 5分钟无访问后自动停止

    def is_running(self) -> bool:
        """检查服务是否运行"""
        try:
            response = requests.get(f"{self.base_url}{self.health_endpoint}", timeout=3)
            return response.status_code == 200
        except Exception:  # TODO
            return False

    async def start(self) -> bool:
        """启动服务"""
        if self.is_running():
            self.last_used = time.time()
            return True

        print(f"🚀 启动服务 {self.name} (端口 {self.port})...")

        # 确保脚本存在
        if not self.script_path.exists():
            print(f"❌ 服务脚本不存在: {self.script_path}")
            return False

        try:
            cmd = ["python3", str(self.script_path)]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.script_path.parent
            )

            # 等待服务启动
            for _ in range(30):  # 最多等待30秒
                if self.is_running():
                    self.start_time = time.time()
                    self.last_used = time.time()
                    elapsed = time.time() - self.start_time
                    print(f"✅ {self.name} 启动成功!耗时: {elapsed:.2f}秒")
                    return True
                await asyncio.sleep(0.5)

            print(f"❌ {self.name} 启动超时")
            self.stop()
            return False

        except Exception as e:
            print(f"❌ 启动 {self.name} 失败: {e}")
            return False

    def stop(self) -> None:
        """停止服务"""
        if self.process:
            try:
                print(f"🛑 停止服务 {self.name}...")
                self.process.terminate()
                self.process.wait(timeout=5)
                print(f"✅ {self.name} 已停止")
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            finally:
                self.process = None
                self.start_time = None

    async def ensure_running(self) -> bool:
        """确保服务运行(按需启动)"""
        if not self.is_running():
            success = await self.start()
            if not success:
                return False

        self.last_used = time.time()
        return True

    def should_stop(self) -> bool:
        """检查是否应该停止(长时间未使用)"""
        if not self.last_used or not self.is_running():
            return False
        return time.time() - self.last_used > self.max_idle_time

class OnDemandManager:
    """按需服务管理器"""

    def __init__(self):
        self.services: dict[str, OnDemandService] = {}
        self._init_services()
        self._cleanup_task: asyncio.Task | None = None

    def _init_services(self) -> Any:
        """初始化按需服务"""
        # 法律API服务
        self.services["laws"] = OnDemandService(
            name="法律知识库API",
            port=8099,
            script_path="/Users/xujian/Athena工作平台/services/laws-knowledge-base/api/laws_api.py",
            health_endpoint="/health"
        )

        # 小宸对话API(开发中)
        self.services["xiaochen"] = OnDemandService(
            name="小宸对话API",
            port=8006,
            script_path="/Users/xujian/Athena工作平台/xiaochen_simple_api.py",
            health_endpoint="/"
        )


        # 其他可能需要的按需服务
        # self.services["crawler"] = OnDemandService(
        #     name="专利爬虫服务",
        #     port=9000,
        #     script_path="/path/to/crawler_api.py",
        #     health_endpoint="/health"
        # )

    async def get_service(self, service_name: str) -> str | None:
        """获取服务URL(确保服务运行)"""
        if service_name not in self.services:
            print(f"❌ 未知服务: {service_name}")
            return None

        service = self.services[service_name]
        success = await service.ensure_running()

        if success:
            return service.base_url
        return None

    async def stop_service(self, service_name: str):
        """停止指定服务"""
        if service_name in self.services:
            self.services[service_name].stop()

    async def check_idle_services(self):
        """检查并停止空闲服务"""
        for name, service in self.services.items():
            if service.should_stop():
                print(f"📝 检测到服务 {name} 空闲超过5分钟,正在停止...")
                service.stop()

    async def start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            print("✅ 按需服务清理任务已启动")

    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await self.check_idle_services()
                await asyncio.sleep(60)  # 每分钟检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ 清理任务错误: {e}")

    def get_status(self) -> dict[str, dict]:
        """获取所有服务状态"""
        status = {}
        for name, service in self.services.items():
            status[name] = {
                "name": service.name,
                "port": service.port,
                "running": service.is_running(),
                "start_time": service.start_time,
                "last_used": service.last_used,
                "idle_time": time.time() - service.last_used if service.last_used else None
            }
        return status

    async def stop_all(self):
        """停止所有服务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                # 任务被取消，正常退出
                pass

        for service in self.services.values():
            service.stop()

# 全局管理器实例
_manager: OnDemandManager | None = None

def get_on_demand_manager() -> OnDemandManager:
    """获取按需服务管理器"""
    global _manager
    if _manager is None:
        _manager = OnDemandManager()
        # 启动清理任务
        asyncio.create_task(_manager.start_cleanup_task())
    return _manager

# 便捷函数
async def get_laws_api_url() -> str | None:
    """获取法律API URL(按需启动)"""
    manager = get_on_demand_manager()
    return await manager.get_service("laws")

async def get_xiaochen_api_url() -> str | None:
    """获取小宸API URL(按需启动)"""
    manager = get_on_demand_manager()
    return await manager.get_service("xiaochen")


async def stop_laws_api():
    """停止法律API"""
    manager = get_on_demand_manager()
    await manager.stop_service("laws")

async def stop_xiaochen_api():
    """停止小宸API"""
    manager = get_on_demand_manager()
    await manager.stop_service("xiaochen")


# 批量管理
async def stop_all_ondemand_apis():
    """停止所有按需API服务"""
    manager = get_on_demand_manager()
    await manager.stop_all()

if __name__ == "__main__":
    async def test():
        """测试按需服务管理"""
        print("🧪 测试按需服务管理器")
        print("-" * 40)

        manager = get_on_demand_manager()

        # 测试启动法律API
        print("\n1. 请求法律API...")
        url = await get_laws_api_url()
        if url:
            print(f"✅ 法律API已启动: {url}")

            # 测试API
            try:
                response = requests.get(f"{url}/api/stats")
                if response.status_code == 200:
                    stats = response.json()
                    print(f"📚 法律文档数量: {stats.get('total_laws')}")
            except (asyncio.CancelledError, Exception):
                print("⚠️ API测试失败")

        # 显示状态
        print("\n2. 服务状态:")
        status = manager.get_status()
        for name, info in status.items():
            print(f"   - {name}: {'运行中' if info['running'] else '已停止'}")

        # 等待手动停止
        print("\n按回车键停止所有服务...")
        input()

        # 停止服务
        await manager.stop_all()
        print("✅ 测试完成")

    asyncio.run(test())
