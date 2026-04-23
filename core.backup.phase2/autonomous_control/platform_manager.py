from __future__ import annotations
"""
平台管理器 - Athena和小诺控制平台的核心接口
提供对平台所有服务的统一管理和控制能力
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import requests

import docker
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ServiceStatus(Enum):
    """服务状态枚举"""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceInfo:
    """服务信息"""

    name: str
    container_name: str
    port: int
    status: ServiceStatus
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    health_check_url: str | None = None


class PlatformManager:
    """平台管理器 - Athena和小诺控制平台的核心"""

    def __init__(self):
        self.docker_client = docker.from_env()
        self.services = self._load_services_config()
        self.control_history = []

    def _load_services_config(self) -> dict[str, ServiceInfo]:
        """加载服务配置"""
        services = {
            # API网关
            "api-gateway": ServiceInfo(
                name="API网关",
                container_name="athena-api-gateway",
                port=8080,
                status=ServiceStatus.STOPPED,
                health_check_url="http://localhost:8080/health",
            ),
            # AI服务
            "ai-cognitive": ServiceInfo(
                name="认知服务",
                container_name="athena-ai-cognitive",
                port=8080,
                status=ServiceStatus.STOPPED,
                health_check_url="http://localhost:8080/health",
            ),
            "ai-perception": ServiceInfo(
                name="感知服务",
                container_name="athena-ai-perception",
                port=8087,
                status=ServiceStatus.STOPPED,
                health_check_url="http://localhost:8087/health",
            ),
            "memory-services": ServiceInfo(
                name="记忆服务",
                container_name="athena-memory-services",
                port=8008,
                status=ServiceStatus.STOPPED,
                health_check_url="http://localhost:8008/health",
            ),
            # DeepSeek服务
            "deepseek-grpo": ServiceInfo(
                name="DeepSeek GRPO优化器",
                container_name="deepseek-grpo-optimizer",
                port=8020,
                status=ServiceStatus.STOPPED,
            ),
            "deepseek-generator": ServiceInfo(
                name="DeepSeek数据生成器",
                container_name="deepseek-data-generator",
                port=8022,
                status=ServiceStatus.STOPPED,
            ),
            # 数据库服务
            "postgres": ServiceInfo(
                name="PostgreSQL数据库",
                container_name="athena-postgres",
                port=5432,
                status=ServiceStatus.STOPPED,
            ),
            "redis": ServiceInfo(
                name="Redis缓存",
                container_name="athena-redis",
                port=6379,
                status=ServiceStatus.STOPPED,
            ),
            "qdrant": ServiceInfo(
                name="Qdrant向量数据库",
                container_name="athena-qdrant",
                port=6333,
                status=ServiceStatus.STOPPED,
            ),
            # 监控服务
            "prometheus": ServiceInfo(
                name="Prometheus监控",
                container_name="athena-prometheus",
                port=9090,
                status=ServiceStatus.STOPPED,
            ),
            "grafana": ServiceInfo(
                name="Grafana仪表板",
                container_name="athena-grafana",
                port=3000,
                status=ServiceStatus.STOPPED,
            ),
            # 浏览器自动化
            "browser-automation": ServiceInfo(
                name="浏览器自动化服务",
                container_name="athena-browser-automation",
                port=8081,
                status=ServiceStatus.STOPPED,
                health_check_url="http://localhost:8081/health",
            ),
        }

        return services

    async def get_platform_status(self) -> dict[str, Any]:
        """获取平台整体状态"""
        try:
            # 更新服务状态
            await self._update_service_status()

            # 统计状态信息
            status_counts = {}
            for service in self.services.values():
                status = service.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            # 获取系统资源使用情况
            system_info = await self._get_system_info()

            return {
                "platform_status": "healthy" if status_counts.get("error", 0) == 0 else "degraded",
                "total_services": len(self.services),
                "service_status_counts": status_counts,
                "services": {
                    name: {
                        "name": info.name,
                        "status": info.status.value,
                        "port": info.port,
                        "cpu_usage": info.cpu_usage,
                        "memory_usage": info.memory_usage,
                    }
                    for name, info in self.services.items()
                },
                "system_info": system_info,
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            logger.error(f"获取平台状态失败: {e}")
            return {"error": str(e), "platform_status": "unknown"}

    async def _update_service_status(self):
        """更新所有服务状态"""
        try:
            containers = self.docker_client.containers.list(all=True)

            for service_name, service_info in self.services.items():
                try:
                    # 查找容器
                    container = next(
                        (c for c in containers if service_info.container_name in c.name), None
                    )

                    if container:
                        # 更新状态
                        status = container.status
                        if status == "running":
                            service_info.status = ServiceStatus.RUNNING
                            # 获取资源使用情况
                            stats = container.stats(stream=False)
                            if stats:
                                service_info.cpu_usage = self._calculate_cpu_usage(stats)
                                service_info.memory_usage = self._calculate_memory_usage(stats)
                        else:
                            service_info.status = ServiceStatus.STOPPED
                    else:
                        service_info.status = ServiceStatus.STOPPED

                except Exception as e:
                    logger.warning(f"更新服务 {service_name} 状态失败: {e}")
                    service_info.status = ServiceStatus.ERROR

        except Exception as e:
            logger.error(f"更新服务状态失败: {e}")

    def _calculate_cpu_usage(self, stats: dict) -> float:
        """计算CPU使用率"""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"]
            system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"]["total_usage"]

            if system_cpu_delta > 0:
                cpu_usage = (
                    (cpu_delta / system_cpu_delta)
                    * len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1]))
                    * 100
                )
                return round(cpu_usage, 2)
        except (KeyError, TypeError, ZeroDivisionError):
            # CPU统计计算失败,返回默认值
            pass
        return 0.0

    def _calculate_memory_usage(self, stats: dict) -> float:
        """计算内存使用率"""
        try:
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]

            if memory_limit > 0:
                return round((memory_usage / memory_limit) * 100, 2)
        except (KeyError, TypeError, ZeroDivisionError):
            # 内存统计计算失败,返回默认值
            pass
        return 0.0

    async def _get_system_info(self) -> dict[str, Any]:
        """获取系统信息"""
        try:
            import psutil

            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "load_average": (
                    list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None
                ),
            }
        except ImportError:
            # 如果没有psutil,返回默认值
            return {"cpu_percent": 0, "memory_percent": 0, "disk_usage": 0, "load_average": None}

    async def start_service(self, service_name: str) -> dict[str, Any]:
        """启动指定服务"""
        try:
            if service_name not in self.services:
                return {"success": False, "error": f"服务 {service_name} 不存在"}

            service_info = self.services[service_name]

            # 记录操作
            action = f"启动服务: {service_name}"
            self.control_history.append(
                {
                    "action": action,
                    "timestamp": asyncio.get_event_loop().time(),
                    "status": "executing",
                }
            )

            # 使用Docker Compose启动服务
            result = await self._run_docker_compose_command(
                f"docker-compose up -d {service_info.container_name}"
            )

            if result["success"]:
                service_info.status = ServiceStatus.STARTING
                # 等待服务启动完成
                await asyncio.sleep(5)
                await self._update_service_status()

                self.control_history[-1]["status"] = "completed"
                return {"success": True, "message": f"服务 {service_name} 启动成功"}
            else:
                self.control_history[-1]["status"] = "failed"
                return {"success": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"启动服务 {service_name} 失败: {e}")
            return {"success": False, "error": str(e)}

    async def stop_service(self, service_name: str) -> dict[str, Any]:
        """停止指定服务"""
        try:
            if service_name not in self.services:
                return {"success": False, "error": f"服务 {service_name} 不存在"}

            service_info = self.services[service_name]

            # 记录操作
            action = f"停止服务: {service_name}"
            self.control_history.append(
                {
                    "action": action,
                    "timestamp": asyncio.get_event_loop().time(),
                    "status": "executing",
                }
            )

            # 使用Docker Compose停止服务
            result = await self._run_docker_compose_command(
                f"docker-compose stop {service_info.container_name}"
            )

            if result["success"]:
                service_info.status = ServiceStatus.STOPPED
                self.control_history[-1]["status"] = "completed"
                return {"success": True, "message": f"服务 {service_name} 停止成功"}
            else:
                self.control_history[-1]["status"] = "failed"
                return {"success": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"停止服务 {service_name} 失败: {e}")
            return {"success": False, "error": str(e)}

    async def restart_service(self, service_name: str) -> dict[str, Any]:
        """重启指定服务"""
        try:
            # 先停止再启动
            stop_result = await self.stop_service(service_name)
            if stop_result["success"]:
                await asyncio.sleep(2)
                return await self.start_service(service_name)
            else:
                return stop_result

        except Exception as e:
            logger.error(f"重启服务 {service_name} 失败: {e}")
            return {"success": False, "error": str(e)}

    async def restart_platform(self) -> dict[str, Any]:
        """重启整个平台"""
        try:
            # 记录操作
            action = "重启整个平台"
            self.control_history.append(
                {
                    "action": action,
                    "timestamp": asyncio.get_event_loop().time(),
                    "status": "executing",
                }
            )

            # 停止所有服务
            result = await self._run_docker_compose_command("docker-compose down")

            if result["success"]:
                await asyncio.sleep(5)

                # 启动所有服务
                result = await self._run_docker_compose_command("docker-compose up -d")

                if result["success"]:
                    await asyncio.sleep(10)
                    await self._update_service_status()

                    self.control_history[-1]["status"] = "completed"
                    return {"success": True, "message": "平台重启成功"}
                else:
                    self.control_history[-1]["status"] = "failed"
                    return {"success": False, "error": result["error"]}
            else:
                self.control_history[-1]["status"] = "failed"
                return {"success": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"重启平台失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_service_logs(self, service_name: str, lines: int = 100) -> dict[str, Any]:
        """获取服务日志"""
        try:
            if service_name not in self.services:
                return {"success": False, "error": f"服务 {service_name} 不存在"}

            service_info = self.services[service_name]

            # 使用Docker Compose获取日志
            result = await self._run_docker_compose_command(
                f"docker-compose logs --tail={lines} {service_info.container_name}"
            )

            return result

        except Exception as e:
            logger.error(f"获取服务 {service_name} 日志失败: {e}")
            return {"success": False, "error": str(e)}

    async def _run_docker_compose_command(self, command: str) -> dict[str, Any]:
        """执行Docker Compose命令"""
        try:
            # 切换到项目根目录
            project_root = Path("/Users/xujian/Athena工作平台")

            process = await asyncio.create_subprocess_shell(
                command,
                cwd=project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {"success": True, "stdout": stdout.decode(), "stderr": stderr.decode()}
            else:
                return {"success": False, "error": stderr.decode(), "stdout": stdout.decode()}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_control_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """获取控制历史记录"""
        return self.control_history[-limit:] if limit > 0 else self.control_history

    async def health_check(self, service_name: str | None = None) -> dict[str, Any]:
        """健康检查"""
        try:
            if service_name:
                if service_name not in self.services:
                    return {"success": False, "error": f"服务 {service_name} 不存在"}

                service_info = self.services[service_name]
                if service_info.health_check_url:
                    try:
                        response = requests.get(service_info.health_check_url, timeout=5)
                        return {
                            "success": True,
                            "service": service_name,
                            "healthy": response.status_code == 200,
                            "status_code": response.status_code,
                            "response_time": response.elapsed.total_seconds(),
                        }
                    except requests.RequestException:
                        return {
                            "success": True,
                            "service": service_name,
                            "healthy": False,
                            "error": "连接失败",
                        }
                else:
                    return {
                        "success": True,
                        "service": service_name,
                        "healthy": service_info.status == ServiceStatus.RUNNING,
                        "note": "基于容器状态判断",
                    }
            else:
                # 检查所有服务
                results = {}
                for name, info in self.services.items():
                    if info.health_check_url:
                        try:
                            response = requests.get(info.health_check_url, timeout=5)
                            results[name] = {
                                "healthy": response.status_code == 200,
                                "status_code": response.status_code,
                                "response_time": response.elapsed.total_seconds(),
                            }
                        except requests.RequestException:
                            results[name] = {"healthy": False, "error": "连接失败"}
                    else:
                        results[name] = {
                            "healthy": info.status == ServiceStatus.RUNNING,
                            "note": "基于容器状态判断",
                        }

                return {"success": True, "services": results}

        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局平台管理器实例
platform_manager = PlatformManager()
