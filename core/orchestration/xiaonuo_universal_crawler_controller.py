#!/usr/bin/env python3
from __future__ import annotations
"""
小诺·双鱼公主全量爬虫控制系统
Xiaonuo·Pisces Princess Universal Crawler Control System

统一管理和控制平台所有爬虫工具,实现智能决策和全量控制

作者: 小诺·双鱼公主
创建时间: 2025-12-14
版本: 1.0.0
"""

import asyncio
import logging
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class CrawlerStatus(Enum):
    """爬虫状态"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    PAUSED = "paused"
    UNKNOWN = "unknown"


class CrawlerType(Enum):
    """爬虫类型"""

    UNIVERSAL = "universal"  # 通用爬虫
    PATENT = "patent"  # 专利爬虫
    BROWSER_AUTOMATION = "browser_automation"  # 浏览器自动化爬虫
    DISTRIBUTED = "distributed"  # 分布式爬虫
    HYBRID = "hybrid"  # 混合爬虫
    API_CRAWLER = "api_crawler"  # API爬虫


@dataclass
class CrawlerService:
    """爬虫服务定义"""

    id: str
    name: str
    type: CrawlerType
    script_path: str
    working_dir: str
    config_file: str | None = None
    health_check_url: str | None = None
    dependencies: list[str] = field(default_factory=list)
    auto_start: bool = False
    max_instances: int = 1
    resource_requirements: dict[str, Any] = field(default_factory=dict)


@dataclass
class CrawlerInstance:
    """爬虫实例"""

    service_id: str
    instance_id: str
    process: subprocess.Popen | None = None
    pid: int | None = None
    status: CrawlerStatus = CrawlerStatus.UNKNOWN
    start_time: datetime | None = None
    last_check: datetime | None = None
    health_status: dict[str, Any] = field(default_factory=dict)
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_request: datetime | None = None


@dataclass
class CrawlerTask:
    """爬虫任务"""

    task_id: str
    service_type: CrawlerType
    target_urls: list[str]
    config: dict[str, Any]
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "pending"
    result: dict[str, Any] | None = None


class XiaonuoUniversalCrawlerController:
    """小诺·双鱼公主全量爬虫控制器"""

    def __init__(self):
        self.name = "小诺·双鱼公主全量爬虫控制系统"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 核心组件
        self.services: dict[str, CrawlerService] = {}
        self.instances: dict[str, list[CrawlerInstance]] = {}
        self.tasks: dict[str, CrawlerTask] = {}
        self.task_queue: list[str] = []

        # 执行器
        self.executor = ThreadPoolExecutor(max_workers=10)

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_instances": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "error_requests": 0,
        }

        # 控制配置
        self.control_config = {
            "max_concurrent_tasks": 10,
            "health_check_interval": 30,
            "task_timeout": 3600,  # 1小时
            "restart_on_failure": True,
            "auto_scaling": True,
            "load_balancing": True,
        }

        # 智能路由器
        self.router = None

        # 初始化服务
        self._initialize_crawler_services()

        print(f"🕷️ {self.name} 初始化完成")
        print(f"   注册服务: {len(self.services)} 个")

    def _initialize_crawler_services(self) -> Any:
        """初始化所有爬虫服务"""

        # 1. 通用爬虫服务
        self.services["universal_crawler"] = CrawlerService(
            id="universal_crawler",
            name="通用爬虫服务",
            type=CrawlerType.UNIVERSAL,
            script_path="/Users/xujian/Athena工作平台/services/crawler-service/core/universal_crawler.py",
            working_dir="/Users/xujian/Athena工作平台/services/crawler-service",
            health_check_url="http://localhost:8003/health",
            auto_start=True,
            max_instances=3,
            resource_requirements={"memory": "512MB", "cpu": "1 core"},
        )

        # 2. 专利爬虫服务
        self.services["patent_crawler"] = CrawlerService(
            id="patent_crawler",
            name="专利爬虫服务",
            type=CrawlerType.PATENT,
            script_path="/Users/xujian/Athena工作平台/patent-platform/workspace/enhanced_patent_crawler.py",
            working_dir="/Users/xujian/Athena工作平台/patent-platform/workspace",
            health_check_url="http://localhost:8004/health",
            auto_start=True,
            max_instances=2,
            resource_requirements={"memory": "1GB", "cpu": "2 cores"},
        )

        # 3. 浏览器自动化服务
        self.services["browser_automation"] = CrawlerService(
            id="browser_automation",
            name="浏览器自动化爬虫",
            type=CrawlerType.BROWSER_AUTOMATION,
            script_path="/Users/xujian/Athena工作平台/services/browser-automation-service/browser_automation_server.py",
            working_dir="/Users/xujian/Athena工作平台/services/browser-automation-service",
            health_check_url="http://localhost:8005/health",
            dependencies=["chromedriver"],
            max_instances=2,
            resource_requirements={"memory": "2GB", "cpu": "2 cores", "gpu": "optional"},
        )

        # 4. 分布式爬虫服务
        self.services["distributed_crawler"] = CrawlerService(
            id="distributed_crawler",
            name="分布式爬虫服务",
            type=CrawlerType.DISTRIBUTED,
            script_path="/Users/xujian/Athena工作平台/tools/advanced/distributed_crawler.py",
            working_dir="/Users/xujian/Athena工作平台/tools/advanced",
            health_check_url="http://localhost:8006/health",
            max_instances=5,
            resource_requirements={"memory": "1GB", "cpu": "2 cores"},
        )

        # 5. 混合爬虫管理器
        self.services["hybrid_manager"] = CrawlerService(
            id="hybrid_manager",
            name="智能混合爬虫管理器",
            type=CrawlerType.HYBRID,
            script_path="/Users/xujian/Athena工作平台/services/crawler-service/core/hybrid_crawler_manager.py",
            working_dir="/Users/xujian/Athena工作平台/services/crawler-service",
            health_check_url="http://localhost:8007/health",
            auto_start=True,
            resource_requirements={"memory": "1GB", "cpu": "2 cores"},
        )

        # 6. 抖音爬虫服务
        self.services["douyin_scraper"] = CrawlerService(
            id="douyin_scraper",
            name="抖音内容爬虫",
            type=CrawlerType.BROWSER_AUTOMATION,
            script_path="/Users/xujian/Athena工作平台/services/browser-automation-service/douyin_scraper.py",
            working_dir="/Users/xujian/Athena工作平台/services/browser-automation-service",
            max_instances=1,
            resource_requirements={"memory": "2GB", "cpu": "2 cores"},
        )

        # 7. 爬虫API服务
        self.services["crawler_api"] = CrawlerService(
            id="crawler_api",
            name="爬虫API网关服务",
            type=CrawlerType.API_CRAWLER,
            script_path="/Users/xujian/Athena工作平台/services/platform-integration-service/crawler_api_server.py",
            working_dir="/Users/xujian/Athena工作平台/services/platform-integration-service",
            health_check_url="http://localhost:8008/health",
            auto_start=True,
            resource_requirements={"memory": "512MB", "cpu": "1 core"},
        )

    async def initialize(self):
        """初始化控制器"""
        self.logger.info("初始化全量爬虫控制器...")

        # 检查服务依赖
        await self._check_dependencies()

        # 启动自动启动的服务
        await self._start_auto_services()

        # 初始化智能路由器
        await self._initialize_router()

        # 启动健康检查
        asyncio.create_task(self._health_check_loop())

        # 启动任务调度器
        asyncio.create_task(self._task_scheduler_loop())

        self.logger.info("全量爬虫控制器初始化完成")

    async def _check_dependencies(self):
        """检查服务依赖"""
        dependencies = {
            "python3": "python3 --version",
            "pip3": "pip3 --version",
            "node": "node --version",
            "npm": "npm --version",
            "chromedriver": "chromedriver --version",
        }

        for dep, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.logger.info(f"✅ {dep}: {result.stdout.strip()}")
                else:
                    self.logger.warning(f"⚠️ {dep}: 未找到")
            except Exception as e:
                self.logger.warning(f"⚠️ {dep}: 检查失败 - {e!s}")

    async def _start_auto_services(self):
        """启动自动启动的服务"""
        auto_services = [s for s in self.services.values() if s.auto_start]

        for service in auto_services:
            try:
                await self.start_service(service.id, instance_count=1)
                self.logger.info(f"自动启动服务: {service.name}")
            except Exception as e:
                self.logger.error(f"自动启动服务失败 {service.name}: {e}")

    async def _initialize_router(self):
        """初始化智能路由器"""
        try:
            # 这里可以导入并初始化智能路由器
            from .xiaonuo_crawler_intelligent_router import XiaonuoCrawlerIntelligentRouter

            self.router = XiaonuoCrawlerIntelligentRouter()
            await self.router.initialize()
            self.logger.info("智能路由器初始化成功")
        except Exception as e:
            self.logger.warning(f"智能路由器初始化失败: {e}")

    async def start_service(self, service_id: str, instance_count: int = 1) -> dict[str, bool]:
        """启动爬虫服务"""
        if service_id not in self.services:
            return {"success": False, "message": f"服务不存在: {service_id}"}

        service = self.services[service_id]
        results = {}

        # 检查当前实例数
        current_instances = self.instances.get(service_id, [])
        if len(current_instances) >= service.max_instances:
            return {"success": False, "message": f"已达到最大实例数: {service.max_instances}"}

        # 启动新实例
        for i in range(instance_count):
            if len(current_instances) >= service.max_instances:
                break

            instance = await self._start_service_instance(service, len(current_instances))
            if instance:
                current_instances.append(instance)
                results[instance.instance_id] = True
            else:
                results[f"instance_{i}"] = False

        self.instances[service_id] = current_instances
        return results

    async def _start_service_instance(
        self, service: CrawlerService, instance_num: int
    ) -> CrawlerInstance | None:
        """启动服务实例"""
        instance_id = f"{service.id}_{instance_num}"

        try:
            # 构建命令
            cmd = ["python3", service.script_path]

            # 检查文件是否存在
            if not os.path.exists(service.script_path):
                self.logger.error(f"脚本文件不存在: {service.script_path}")
                return None

            # 启动进程
            process = subprocess.Popen(
                cmd,
                cwd=service.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # 创建实例
            instance = CrawlerInstance(
                service_id=service.id,
                instance_id=instance_id,
                process=process,
                pid=process.pid,
                status=CrawlerStatus.STARTING,
                start_time=datetime.now(),
            )

            # 等待启动
            await asyncio.sleep(2)

            # 检查进程状态
            if process.poll() is None:
                instance.status = CrawlerStatus.RUNNING
                self.stats["active_instances"] += 1
                self.logger.info(f"服务实例启动成功: {instance_id}")
                return instance
            else:
                # 进程已退出
                _stdout, stderr = process.communicate()
                self.logger.error(f"服务实例启动失败 {instance_id}: {stderr}")
                return None

        except Exception as e:
            self.logger.error(f"启动服务实例失败 {instance_id}: {e}")
            return None

    async def stop_service(
        self, service_id: str, instance_id: str | None = None
    ) -> dict[str, bool]:
        """停止爬虫服务"""
        if service_id not in self.instances:
            return {"success": False, "message": f"服务未启动: {service_id}"}

        instances = self.instances[service_id]
        results = {}

        if instance_id:
            # 停止特定实例
            target_instances = [inst for inst in instances if inst.instance_id == instance_id]
        else:
            # 停止所有实例
            target_instances = instances

        for inst in target_instances:
            try:
                if inst.process and inst.process.poll() is None:
                    inst.process.terminate()
                    try:
                        inst.process.wait(timeout=10)
                        inst.status = CrawlerStatus.STOPPED
                        results[inst.instance_id] = True
                        self.stats["active_instances"] -= 1
                    except subprocess.TimeoutExpired:
                        inst.process.kill()
                        inst.status = CrawlerStatus.STOPPED
                        results[inst.instance_id] = True
                        self.stats["active_instances"] -= 1
                else:
                    results[inst.instance_id] = False
            except Exception as e:
                self.logger.error(f"停止实例失败 {inst.instance_id}: {e}")
                results[inst.instance_id] = False

        # 清理已停止的实例
        if not instance_id:
            self.instances[service_id] = []
        else:
            self.instances[service_id] = [
                inst
                for inst in instances
                if inst.instance_id != instance_id or not results.get(inst.instance_id)
            ]

        return results

    async def submit_task(self, task: CrawlerTask) -> dict[str, Any]:
        """提交爬虫任务"""
        self.logger.info(f"提交爬虫任务: {task.task_id}")

        # 验证任务
        validation_result = await self._validate_task(task)
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": validation_result["error"],
                "task_id": task.task_id,
            }

        # 智能路由
        if self.router:
            routing_decision = await self.router.route_task(task)
            task.service_type = routing_decision["service_type"]
            task.config.update(routing_decision.get("config_overrides", {}))

        # 添加到任务队列
        self.tasks[task.task_id] = task
        self.task_queue.append(task.task_id)
        self.stats["total_tasks"] += 1

        return {
            "success": True,
            "message": "任务已提交",
            "task_id": task.task_id,
            "queue_position": len(self.task_queue),
        }

    async def _validate_task(self, task: CrawlerTask) -> dict[str, Any]:
        """验证任务"""
        if not task.target_urls:
            return {"valid": False, "error": "没有指定目标URL"}

        # 检查URL格式
        valid_urls = []
        for url in task.target_urls:
            if url.startswith(("http://", "https://")):
                valid_urls.append(url)

        if not valid_urls:
            return {"valid": False, "error": "没有有效的URL"}

        task.target_urls = valid_urls
        return {"valid": True}

    async def _task_scheduler_loop(self):
        """任务调度循环"""
        while True:
            try:
                if (
                    self.task_queue
                    and len(
                        [
                            i
                            for instances in self.instances.values()
                            for i in instances
                            if i.status == CrawlerStatus.RUNNING
                        ]
                    )
                    > 0
                ):
                    task_id = self.task_queue.pop(0)
                    task = self.tasks.get(task_id)

                    if task and task.status == "pending":
                        await self._execute_task(task)

                await asyncio.sleep(1)  # 每秒检查一次
            except Exception as e:
                self.logger.error(f"任务调度错误: {e}")
                await asyncio.sleep(5)

    async def _execute_task(self, task: CrawlerTask):
        """执行任务"""
        self.logger.info(f"执行任务: {task.task_id}")

        task.status = "running"
        task.started_at = datetime.now()

        try:
            # 选择合适的实例
            instance = await self._select_instance_for_task(task)
            if not instance:
                task.status = "failed"
                task.completed_at = datetime.now()
                self.stats["failed_tasks"] += 1
                return

            # 执行任务
            result = await self._run_crawler_task(instance, task)

            # 更新任务状态
            if result["success"]:
                task.status = "completed"
                task.result = result
                self.stats["completed_tasks"] += 1
            else:
                task.status = "failed"
                task.result = result
                self.stats["failed_tasks"] += 1

            task.completed_at = datetime.now()

            # 更新实例统计
            instance.request_count += 1
            if result["success"]:
                instance.success_count += 1
            else:
                instance.error_count += 1
            instance.last_request = datetime.now()

        except Exception as e:
            self.logger.error(f"任务执行失败 {task.task_id}: {e}")
            task.status = "failed"
            task.result = {"error": str(e)}
            task.completed_at = datetime.now()
            self.stats["failed_tasks"] += 1

    async def _select_instance_for_task(self, task: CrawlerTask) -> CrawlerInstance | None:
        """为任务选择实例"""
        # 获取对应的运行中实例
        service_id = f"{task.service_type.value}_crawler"
        if service_id not in self.instances:
            # 尝试启动服务
            await self.start_service(service_id, 1)

        instances = self.instances.get(service_id, [])
        running_instances = [i for i in instances if i.status == CrawlerStatus.RUNNING]

        if not running_instances:
            return None

        # 选择负载最低的实例
        return min(running_instances, key=lambda i: i.request_count)

    async def _run_crawler_task(
        self, instance: CrawlerInstance, task: CrawlerTask
    ) -> dict[str, Any]:
        """运行爬虫任务"""
        try:
            # 这里简化实现,实际应该调用具体的爬虫接口
            await asyncio.sleep(1)  # 模拟执行时间

            # 模拟结果
            return {
                "success": True,
                "data": [
                    {"url": url, "status": "scraped", "data": f"Data from {url}"}
                    for url in task.target_urls
                ],
                "stats": {
                    "urls_count": len(task.target_urls),
                    "success_count": len(task.target_urls),
                    "execution_time": 1.0,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.control_config["health_check_interval"])
            except Exception as e:
                self.logger.error(f"健康检查错误: {e}")
                await asyncio.sleep(30)

    async def _perform_health_checks(self):
        """执行健康检查"""
        for service_id, instances in self.instances.items():
            for instance in instances:
                if instance.status == CrawlerStatus.RUNNING:
                    # 检查进程状态
                    if instance.process and instance.process.poll() is None:
                        # 进程运行中,检查健康接口
                        if self.services[service_id].health_check_url:
                            try:
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(
                                        self.services[service_id].health_check_url,
                                        timeout=aiohttp.ClientTimeout(total=5),
                                    ) as response:
                                        if response.status == 200:
                                            instance.health_status = await response.json()
                                        else:
                                            self.logger.warning(
                                                f"健康检查失败 {instance.instance_id}: HTTP {response.status}"
                                            )
                            except Exception as e:
                                self.logger.debug(f"健康检查异常 {instance.instance_id}: {e}")
                    else:
                        # 进程已退出
                        instance.status = CrawlerStatus.FAILED
                        self.stats["active_instances"] -= 1

                        # 自动重启
                        if self.control_config["restart_on_failure"]:
                            self.logger.info(f"尝试重启实例: {instance.instance_id}")
                            new_instance = await self._start_service_instance(
                                self.services[service_id], len(self.instances[service_id])
                            )
                            if new_instance:
                                instances.append(new_instance)

                instance.last_check = datetime.now()

    async def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        service_status = {}
        for service_id, service in self.services.items():
            instances = self.instances.get(service_id, [])
            running_count = len([i for i in instances if i.status == CrawlerStatus.RUNNING])

            service_status[service_id] = {
                "name": service.name,
                "type": service.type.value,
                "total_instances": len(instances),
                "running_instances": running_count,
                "max_instances": service.max_instances,
                "auto_start": service.auto_start,
                "health_check_url": service.health_check_url,
            }

        return {
            "controller_info": {
                "name": self.name,
                "version": self.version,
                "uptime": "N/A",  # 可以记录启动时间
            },
            "services": service_status,
            "statistics": self.stats.copy(),
            "task_queue": {"pending_tasks": len(self.task_queue), "total_tasks": len(self.tasks)},
            "config": self.control_config,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "service_type": task.service_type.value,
            "status": task.status,
            "target_urls": task.target_urls,
            "priority": task.priority,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
        }

    async def cancel_task(self, task_id: str) -> dict[str, Any]:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "message": "任务不存在"}

        if task.status == "completed":
            return {"success": False, "message": "任务已完成"}

        if task.status == "running":
            return {"success": False, "message": "任务正在执行,无法取消"}

        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
            task.status = "cancelled"
            return {"success": True, "message": "任务已取消"}

        return {"success": False, "message": "任务无法取消"}

    async def shutdown(self):
        """关闭控制器"""
        self.logger.info("关闭全量爬虫控制器...")

        # 停止所有服务
        for service_id in list(self.instances.keys()):
            await self.stop_service(service_id)

        # 关闭执行器
        self.executor.shutdown(wait=True)

        self.logger.info("全量爬虫控制器已关闭")


# 导出主类
__all__ = [
    "CrawlerInstance",
    "CrawlerService",
    "CrawlerStatus",
    "CrawlerTask",
    "CrawlerType",
    "XiaonuoUniversalCrawlerController",
]
