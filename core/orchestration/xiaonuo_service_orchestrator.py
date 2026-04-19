#!/usr/bin/env python3
from __future__ import annotations
"""
小诺·双鱼公主服务编排器 - 智能服务启动管理
Xiaonuo Service Orchestrator - Intelligent Service Startup Management

智能检测需求,自动启动多模态文件系统服务

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import asyncio
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import aiohttp
import psutil


class ServiceStatus(Enum):
    """服务状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    UNKNOWN = "unknown"

class StartupTrigger(Enum):
    """启动触发条件"""
    EXPLICIT_COMMAND = "explicit_command"    # 明确指令启动
    AUTO_DETECT = "auto_detect"              # 自动检测需求
    SCHEDULED = "scheduled"                  # 定时启动
    DEMAND_SPIKE = "demand_spike"           # 需求激增
    DEPENDENCY_REQUIRED = "dependency_required"  # 依赖需要

@dataclass
class ServiceConfig:
    """服务配置"""
    name: str
    port: int
    command: list[str]
    working_dir: str
    health_check_url: str
    startup_time: float = 10.0  # 启动超时时间(秒)
    auto_start: bool = False  # 是否允许自动启动
    dependencies: list[str] = field(default_factory=list)
    resource_requirements: dict[str, Any] = field(default_factory=dict)

@dataclass
class ServiceInstance:
    """服务实例"""
    config: ServiceConfig
    status: ServiceStatus = ServiceStatus.UNKNOWN
    process: subprocess.Popen | None = None
    pid: int | None = None
    start_time: datetime | None = None
    last_check: datetime | None = None
    health_status: dict[str, Any] = field(default_factory=dict)
    request_count: int = 0
    error_count: int = 0

class XiaonuoServiceOrchestrator:
    """小诺·双鱼公主服务编排器"""

    def __init__(self):
        self.name = "小诺·双鱼公主服务编排器"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 服务注册表
        self.services: dict[str, ServiceInstance] = {}

        # 初始化服务配置
        self._initialize_services()

        # 启动策略配置
        self.startup_strategy = {
            "auto_start_enabled": True,
            "auto_start_threshold": 0.7,  # 70%的需求触发自动启动
            "health_check_interval": 30,   # 30秒健康检查
            "max_concurrent_starts": 3,     # 最大并发启动数
            "graceful_shutdown_timeout": 30  # 优雅关闭超时
        }

        # 需求监控
        self.demand_monitor = {
            "file_parse_requests": [],
            "multimodal_requests": [],
            "processing_tasks": []
        }

        # 启动历史
        self.startup_history: list[dict[str, Any]] = []

        print(f"🎛️ {self.name} 初始化完成")

    def _initialize_services(self) -> Any:
        """初始化服务配置"""
        # yunpat-agent 服务
        self.services["yunpat-agent"] = ServiceInstance(
            config=ServiceConfig(
                name="yunpat-agent",
                port=8000,
                command=["python", "app/main.py"],
                working_dir="/Users/xujian/Athena工作平台/services/yunpat-agent",
                health_check_url="http://localhost:8000/health",
                auto_start=True,
                dependencies=[],
                resource_requirements={"memory": "1GB", "cpu": "1 core"}
            )
        )

        # 多模态处理服务
        self.services["multimodal_processor"] = ServiceInstance(
            config=ServiceConfig(
                name="multimodal_processor",
                port=8012,
                command=["python", "multimodal_processor.py"],
                working_dir="/Users/xujian/Athena工作平台/services/optimization-service",
                health_check_url="http://localhost:8012/health",
                auto_start=True,
                dependencies=[],
                resource_requirements={"memory": "2GB", "cpu": "2 cores", "gpu": "optional"}
            )
        )

        # 统一多模态API
        self.services["unified_multimodal_api"] = ServiceInstance(
            config=ServiceConfig(
                name="unified_multimodal_api",
                port=8020,
                command=["python", "unified_multimodal_api.py"],
                working_dir="/Users/xujian/Athena工作平台/services/scripts",
                health_check_url="http://localhost:8020/health",
                auto_start=True,
                dependencies=["multimodal_processor"],
                resource_requirements={"memory": "1GB", "cpu": "1 core"}
            )
        )

        # GLM-4视觉服务
        self.services["glm_vision_service"] = ServiceInstance(
            config=ServiceConfig(
                name="glm_vision_service",
                port=8091,
                command=["python", "glm_vision_server.py"],
                working_dir="/Users/xujian/Athena工作平台/services/vision-service",
                health_check_url="http://localhost:8091/health",
                auto_start=False,  # GLM视觉服务需要明确启动
                dependencies=[],
                resource_requirements={"memory": "2GB", "cpu": "2 cores", "gpu": "required"}
            )
        )

    async def check_service_needs(self, task_type: str, context: dict[str, Any]) -> bool:
        """检查是否需要启动多模态服务"""
        self.logger.info(f"检查任务需求: {task_type}")

        # 需求打分
        need_score = 0

        # 1. 任务类型评分
        if task_type in ["file_upload", "file_parse", "multimodal_analysis"]:
            need_score += 40
            self.logger.info("  任务类型需要多模态服务 (+40分)")

        # 2. 文件类型评分
        file_types = context.get("file_types", [])
        multimodal_types = {"image", "video", "audio", "pdf", "docx"}
        if any(ft in multimodal_types for ft in file_types):
            need_score += 30
            self.logger.info("  包含多模态文件类型 (+30分)")

        # 3. 复杂度评分
        complexity = context.get("complexity", "low")
        if complexity == "high":
            need_score += 20
            self.logger.info("  高复杂度任务 (+20分)")
        elif complexity == "medium":
            need_score += 10
            self.logger.info("  中等复杂度任务 (+10分)")

        # 4. 用户意图评分
        if context.get("explicit_multimodal", False):
            need_score += 50
            self.logger.info("  用户明确需要多模态处理 (+50分)")

        # 5. 历史需求评分
        recent_needs = self._get_recent_needs(minutes=10)
        if len(recent_needs) >= 3:
            need_score += 15
            self.logger.info("  最近需求频繁 (+15分)")

        # 记录需求
        self.demand_monitor["multimodal_requests"].append({
            "task_type": task_type,
            "context": context,
            "need_score": need_score,
            "timestamp": datetime.now()
        })

        # 决策阈值
        threshold = self.startup_strategy["auto_start_threshold"] * 100
        should_start = need_score >= threshold

        self.logger.info(f"需求评分: {need_score}/{threshold} -> {'启动服务' if should_start else '使用现有服务'}")

        return should_start

    async def start_services_on_demand(self, service_names: list[str] | None = None) -> dict[str, bool]:
        """按需启动服务"""
        if not service_names:
            # 默认启动所有自动启动的服务
            service_names = [
                name for name, instance in self.services.items()
                if instance.config.auto_start
            ]

        self.logger.info(f"按需启动服务: {service_names}")

        results = {}
        concurrent_starts = 0
        max_concurrent = self.startup_strategy["max_concurrent_starts"]

        # 检查依赖关系
        startup_order = self._resolve_dependencies(service_names)

        for service_name in startup_order:
            if concurrent_starts >= max_concurrent:
                self.logger.warning("达到最大并发启动数,等待完成...")
                await self._wait_for_startup_completion()
                concurrent_starts = 0

            instance = self.services.get(service_name)
            if not instance:
                results[service_name] = False
                continue

            # 检查是否已经运行
            if await self._is_service_running(instance):
                self.logger.info(f"服务 {service_name} 已在运行")
                results[service_name] = True
                continue

            # 启动服务
            success = await self._start_service(instance)
            results[service_name] = success

            if success:
                concurrent_starts += 1
                self.logger.info(f"服务 {service_name} 启动成功")
            else:
                self.logger.error(f"服务 {service_name} 启动失败")

        return results

    async def _start_service(self, instance: ServiceInstance) -> bool:
        """启动单个服务"""
        self.logger.info(f"启动服务: {instance.config.name}")

        instance.status = ServiceStatus.STARTING
        instance.start_time = datetime.now()

        try:
            # 检查端口占用
            if await self._is_port_in_use(instance.config.port):
                self.logger.warning(f"端口 {instance.config.port} 已被占用")
                return False

            # 启动进程
            process = subprocess.Popen(
                instance.config.command,
                cwd=instance.config.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            instance.process = process
            instance.pid = process.pid

            # 等待启动完成
            success = await self._wait_for_startup(instance)

            if success:
                instance.status = ServiceStatus.RUNNING
                self._record_startup(instance, "success")
            else:
                instance.status = ServiceStatus.FAILED
                self._record_startup(instance, "failed")

            return success

        except Exception as e:
            self.logger.error(f"启动服务失败: {str(e)}")
            instance.status = ServiceStatus.FAILED
            return False

    async def _wait_for_startup(self, instance: ServiceInstance) -> bool:
        """等待服务启动完成"""
        timeout = instance.config.startup_time
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 检查进程是否还在运行
            if instance.process and instance.process.poll() is not None:
                self.logger.error("服务进程意外退出")
                return False

            # 检查健康状态
            if await self._check_service_health(instance):
                self.logger.info(f"服务 {instance.config.name} 健康检查通过")
                return True

            await asyncio.sleep(1)

        self.logger.error("服务启动超时")
        return False

    async def _check_service_health(self, instance: ServiceInstance) -> bool:
        """检查服务健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get(instance.config.health_check_url, timeout=timeout) as response:
                    if response.status == 200:
                        instance.health_status = await response.json()
                        return True
                    else:
                        self.logger.warning(f"健康检查失败: HTTP {response.status}")
                        return False
        except Exception as e:
            self.logger.debug(f"健康检查异常: {str(e)}")
            return False

    async def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except Exception:  # TODO
            return False

    async def _is_service_running(self, instance: ServiceInstance) -> bool:
        """检查服务是否正在运行"""
        if not instance.pid:
            return False

        try:
            process = psutil.Process(instance.pid)
            return process.is_running() and process.status() == psutil.STATUS_RUNNING
        except psutil.NoSuchProcess:
            return False

    def _resolve_dependencies(self, service_names: list[str]) -> list[str]:
        """解析服务依赖关系,返回启动顺序"""
        resolved = []
        visited = set()

        def dfs(name) -> None:
            if name in visited:
                return
            visited.add(name)

            instance = self.services.get(name)
            if not instance:
                return

            # 先启动依赖
            for dep in instance.config.dependencies:
                dfs(dep)

            # 再启动自己
            resolved.append(name)

        for name in service_names:
            dfs(name)

        return resolved

    def _get_recent_needs(self, minutes: int) -> list[dict[str, Any]]:
        """获取最近的需求"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            need for need in self.demand_monitor["multimodal_requests"]
            if need["timestamp"] > cutoff
        ]

    def _record_startup(self, instance: ServiceInstance, result: str) -> Any:
        """记录启动历史"""
        history_entry = {
            "service": instance.config.name,
            "result": result,
            "timestamp": datetime.now(),
            "duration": (datetime.now() - instance.start_time).total_seconds() if instance.start_time else 0,
            "trigger": "auto_detect"
        }

        self.startup_history.append(history_entry)

        # 保持历史记录在合理范围
        if len(self.startup_history) > 1000:
            self.startup_history = self.startup_history[-500:]

    async def _wait_for_startup_completion(self):
        """等待某个服务启动完成"""
        # 简化实现:等待2秒
        await asyncio.sleep(2)

    async def shutdown_service(self, service_name: str, graceful: bool = True) -> bool:
        """关闭服务"""
        instance = self.services.get(service_name)
        if not instance or not instance.process:
            return True

        self.logger.info(f"关闭服务: {service_name}")

        try:
            if graceful:
                # 优雅关闭
                instance.process.terminate()
                try:
                    instance.process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    self.logger.warning("优雅关闭超时,强制关闭")
                    instance.process.kill()
            else:
                # 强制关闭
                instance.process.kill()

            instance.status = ServiceStatus.STOPPED
            instance.process = None
            instance.pid = None

            return True

        except Exception as e:
            self.logger.error(f"关闭服务失败: {str(e)}")
            return False

    def get_service_status(self) -> dict[str, dict[str, Any]]:
        """获取所有服务状态"""
        status = {}

        for name, instance in self.services.items():
            status[name] = {
                "status": instance.status.value,
                "pid": instance.pid,
                "port": instance.config.port,
                "auto_start": instance.config.auto_start,
                "request_count": instance.request_count,
                "error_count": instance.error_count,
                "last_check": instance.last_check.isoformat() if instance.last_check else None
            }

        return status

    def get_startup_statistics(self) -> dict[str, Any]:
        """获取启动统计"""
        if not self.startup_history:
            return {}

        total_starts = len(self.startup_history)
        successful_starts = sum(1 for h in self.startup_history if h["result"] == "success")
        success_rate = successful_starts / total_starts if total_starts > 0 else 0

        recent_starts = [
            h for h in self.startup_history
            if (datetime.now() - h["timestamp"]).total_seconds() < 3600
        ]

        return {
            "total_starts": total_starts,
            "successful_starts": successful_starts,
            "success_rate": success_rate,
            "recent_starts": len(recent_starts),
            "avg_startup_time": sum(h["duration"] for h in self.startup_history) / total_starts if total_starts > 0 else 0
        }

# 导出主类
__all__ = [
    'XiaonuoServiceOrchestrator',
    'ServiceStatus',
    'StartupTrigger',
    'ServiceConfig',
    'ServiceInstance'
]
