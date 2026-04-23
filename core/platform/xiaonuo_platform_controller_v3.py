#!/usr/bin/env python3
from __future__ import annotations
"""
小诺全量平台控制器 v3.0
Xiaonuo Full Platform Controller v3.0

集成到统一网关的完整平台控制能力:
- 服务启停控制(Python进程、Docker容器)
- 跨智能体通信协议
- 智能体编排和调度引擎
- 平台全景监控仪表板

作者: 小诺·双鱼公主
版本: v3.0.0
创建: 2025-12-30
"""

import asyncio
import logging
import subprocess
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger("XiaonuoPlatformControllerV3")


# ==================== 数据模型 ====================


class ServiceAction(str, Enum):
    """服务操作"""

    START = "start"
    STOP = "stop"
    RESTART = "restart"
    STATUS = "status"


class ServiceType(str, Enum):
    """服务类型"""

    PYTHON = "python"
    DOCKER = "docker"
    AGENT = "agent"


class AgentInfo(BaseModel):
    """智能体信息"""

    name: str
    port: int
    status: str = "unknown"
    health_url: str
    description: str = ""
    capabilities: list[str] = []


class ServiceControlRequest(BaseModel):
    """服务控制请求"""

    service: str
    action: ServiceAction
    force: bool = False


class ServiceControlResponse(BaseModel):
    """服务控制响应"""

    success: bool
    service: str
    action: str
    message: str
    data: Optional[dict[str, Any]] = None


class OrchestrationRequest(BaseModel):
    """编排请求"""

    task: str
    agents: list[str]
    parallel: bool = False
    timeout: int = 300


# ==================== 平台控制器核心 ====================


class XiaonuoPlatformControllerV3:
    """小诺全量平台控制器 v3.0"""

    def __init__(self):
        """初始化控制器"""
        self.name = "小诺全量平台控制器"
        self.version = "v3.0.0"

        # 平台服务注册表
        self.services: dict[str, dict[str, Any]] = {
            "xiaonuo": {
                "name": "小诺统一网关",
                "type": ServiceType.PYTHON,
                "port": 8100,
                "description": "平台协调官 - 统一网关",
                "health_url": "http://localhost:8100/health",
                "startup_script": None,  # 自身服务
                "startup_order": 1,
            },
            "xiaona": {
                "name": "小娜·天秤女神",
                "type": ServiceType.AGENT,
                "port": 8001,
                "description": "专利法律专家",
                "health_url": "http://localhost:8001/health",
                "startup_script": None,  # 需要配置
                "startup_order": 2,
            },
            "yunxi": {
                "name": "云熙·Vega",
                "type": ServiceType.AGENT,
                "port": 8020,
                "description": "IP管理系统",
                "health_url": "http://localhost:8020/health",
                "startup_script": None,  # 需要配置
                "startup_order": 3,
            },
            "xiaochen": {
                "name": "小宸·星河射手",
                "type": ServiceType.AGENT,
                "port": 8030,
                "description": "自媒体运营专家",
                "health_url": "http://localhost:8030/health",
                "startup_script": None,  # 需要配置
                "startup_order": 4,
            },
        }

        # 智能体通信缓存
        self._agent_health_cache: dict[str, dict] = {}
        self._last_health_check: dict[str, datetime] = {}

        logger.info("🎛️ 小诺全量平台控制器 v3.0 初始化完成")

    # ==================== 服务控制 ====================

    async def start_service(self, service_name: str) -> ServiceControlResponse:
        """启动服务"""
        if service_name not in self.services:
            return ServiceControlResponse(
                success=False,
                service=service_name,
                action="start",
                message=f"未知服务: {service_name}",
            )

        service = self.services[service_name]

        # 检查服务是否已在运行
        is_running = await self._check_service_health(service_name)
        if is_running:
            return ServiceControlResponse(
                success=True,
                service=service_name,
                action="start",
                message=f"服务已在运行: {service['name']}",
                data={"status": "running", "port": service["port"]},
            )

        # 启动服务
        try:
            if service["type"] == ServiceType.DOCKER:
                result = await self._start_docker_service(service_name)
            elif service["type"] == ServiceType.PYTHON:
                result = await self._start_python_service(service_name)
            elif service["type"] == ServiceType.AGENT:
                result = await self._start_agent_service(service_name)
            else:
                result = {"success": False, "message": f"不支持的服务类型: {service['type']}"}

            if result["success"]:
                # 等待服务启动
                await asyncio.sleep(2)
                health = await self._check_service_health(service_name)
                result["health"] = health

            return ServiceControlResponse(
                success=result["success"],
                service=service_name,
                action="start",
                message=result.get("message", ""),
                data=result,
            )

        except Exception as e:
            logger.error(f"启动服务失败 {service_name}: {e}")
            return ServiceControlResponse(
                success=False, service=service_name, action="start", message=f"启动失败: {e!s}"
            )

    async def stop_service(self, service_name: str) -> ServiceControlResponse:
        """停止服务"""
        if service_name not in self.services:
            return ServiceControlResponse(
                success=False,
                service=service_name,
                action="stop",
                message=f"未知服务: {service_name}",
            )

        service = self.services[service_name]

        # 不允许停止小诺自己
        if service_name == "xiaonuo":
            return ServiceControlResponse(
                success=False, service=service_name, action="stop", message="不能停止小诺自己的服务"
            )

        try:
            if service["type"] == ServiceType.DOCKER:
                result = await self._stop_docker_service(service_name)
            elif service["type"] == ServiceType.PYTHON:
                result = await self._stop_python_service(service_name)
            elif service["type"] == ServiceType.AGENT:
                result = await self._stop_agent_service(service_name)
            else:
                result = {"success": False, "message": f"不支持的服务类型: {service['type']}"}

            return ServiceControlResponse(
                success=result["success"],
                service=service_name,
                action="stop",
                message=result.get("message", ""),
                data=result,
            )

        except Exception as e:
            logger.error(f"停止服务失败 {service_name}: {e}")
            return ServiceControlResponse(
                success=False, service=service_name, action="stop", message=f"停止失败: {e!s}"
            )

    async def restart_service(self, service_name: str) -> ServiceControlResponse:
        """重启服务"""
        # 先停止
        stop_result = await self.stop_service(service_name)
        if not stop_result.success and service_name != "xiaonuo":
            return ServiceControlResponse(
                success=False,
                service=service_name,
                action="restart",
                message=f"停止失败: {stop_result.message}",
            )

        # 等待停止完成
        await asyncio.sleep(2)

        # 再启动
        start_result = await self.start_service(service_name)
        return ServiceControlResponse(
            success=start_result.success,
            service=service_name,
            action="restart",
            message=start_result.message,
            data=start_result.data,
        )

    async def get_service_status(self, service_name: str) -> dict[str, Any]:
        """获取服务状态"""
        if service_name not in self.services:
            return {"error": f"未知服务: {service_name}"}

        service = self.services[service_name]

        # 健康检查
        is_healthy = await self._check_service_health(service_name)

        # 端口检查
        port_status = await self._check_port(service["port"])

        return {
            "name": service["name"],
            "service": service_name,
            "type": service["type"].value,
            "port": service["port"],
            "description": service["description"],
            "healthy": is_healthy,
            "port_open": port_status,
            "status": "running" if (is_healthy or port_status) else "stopped",
            "health_url": service["health_url"],
            "last_check": datetime.now().isoformat(),
        }

    async def get_all_services_status(self) -> dict[str, Any]:
        """获取所有服务状态"""
        services_status = {}
        summary = {"total": len(self.services), "running": 0, "healthy": 0, "stopped": 0}

        for service_name in self.services:
            status = await self.get_service_status(service_name)
            services_status[service_name] = status

            if status["status"] == "running":
                summary["running"] += 1
            else:
                summary["stopped"] += 1

            if status["healthy"]:
                summary["healthy"] += 1

        return {
            "controller": {
                "name": self.name,
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
            },
            "summary": summary,
            "services": services_status,
        }

    # ==================== 智能体通信 ====================

    async def communicate_with_agent(
        self, agent_name: str, message: str, context: dict | None = None
    ) -> dict[str, Any]:
        """与智能体通信"""
        if agent_name not in self.services:
            return {"success": False, "error": f"未知智能体: {agent_name}"}

        agent = self.services[agent_name]

        # 检查智能体是否在线
        is_healthy = await self._check_service_health(agent_name)
        if not is_healthy:
            return {
                "success": False,
                "error": f"智能体未在线: {agent['name']}",
                "suggestion": f"请先启动 {agent['name']} 服务",
            }

        # 发送请求
        try:
            chat_url = f"http://localhost:{agent['port']}/chat"
            response = requests.post(
                chat_url, json={"message": message, "context": context or {}}, timeout=30
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "agent": agent_name,
                    "agent_name": agent["name"],
                    "response": response.json(),
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "detail": response.text[:200],
                }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时", "agent": agent_name}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接", "agent": agent_name}
        except Exception as e:
            return {"success": False, "error": str(e), "agent": agent_name}

    async def orchestrate_agents(
        self, task: str, agents: list[str], parallel: bool = False, timeout: int = 300
    ) -> dict[str, Any]:
        """编排多个智能体执行任务"""
        results = {}
        start_time = datetime.now()

        # 验证智能体
        valid_agents = [a for a in agents if a in self.services]
        if not valid_agents:
            return {
                "success": False,
                "error": "没有有效的智能体",
                "requested_agents": agents,
                "available_agents": list(self.services.keys()),
            }

        if parallel:
            # 并行执行
            tasks = [self.communicate_with_agent(agent, task) for agent in valid_agents]
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)

            for agent, result in zip(valid_agents, agent_results, strict=False):
                if isinstance(result, Exception):
                    results[agent] = {"error": str(result)}
                else:
                    results[agent] = result
        else:
            # 串行执行
            for agent in valid_agents:
                result = await self.communicate_with_agent(agent, task)
                results[agent] = result

                # 如果失败且非并行模式,可以选择停止
                if not result.get("success"):
                    logger.warning(f"智能体 {agent} 执行失败")

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "success": True,
            "task": task,
            "duration_seconds": duration,
            "agents_count": len(valid_agents),
            "parallel": parallel,
            "results": results,
        }

    # ==================== 平台监控 ====================

    async def get_platform_dashboard(self) -> dict[str, Any]:
        """获取平台监控仪表板数据"""
        all_status = await self.get_all_services_status()

        return {
            "dashboard": {
                "title": "Athena平台监控仪表板",
                "controller": self.name,
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
                "refresh_interval": 30,  # 秒
            },
            "overview": {
                "total_services": all_status["summary"]["total"],
                "running_services": all_status["summary"]["running"],
                "healthy_services": all_status["summary"]["healthy"],
                "stopped_services": all_status["summary"]["stopped"],
                "health_percentage": round(
                    (
                        (all_status["summary"]["healthy"] / all_status["summary"]["total"] * 100)
                        if all_status["summary"]["total"] > 0
                        else 0
                    ),
                    2,
                ),
            },
            "services": all_status["services"],
            "alerts": self._generate_alerts(all_status),
            "recommendations": self._generate_recommendations(all_status),
        }

    def _generate_alerts(self, status: dict[str, Any]) -> list[dict[str, Any]]:
        """生成告警"""
        alerts = []
        summary = status["summary"]

        if summary["stopped"] > 0:
            alerts.append(
                {
                    "level": "warning",
                    "message": f"{summary['stopped']} 个服务已停止",
                    "services": [
                        name
                        for name, info in status["services"].items()
                        if info["status"] == "stopped"
                    ],
                }
            )

        if summary["healthy"] < summary["running"]:
            unhealthy = summary["running"] - summary["healthy"]
            alerts.append(
                {
                    "level": "error",
                    "message": f"{unhealthy} 个服务运行中但不健康",
                    "services": [
                        name
                        for name, info in status["services"].items()
                        if info["status"] == "running" and not info["healthy"]
                    ],
                }
            )

        return alerts

    def _generate_recommendations(self, status: dict[str, Any]) -> list[str]:
        """生成建议"""
        recommendations = []

        summary = status["summary"]
        if summary["stopped"] > 0:
            stopped_services = [
                info["name"]
                for name, info in status["services"].items()
                if info["status"] == "stopped"
            ]
            recommendations.append(f"建议启动已停止的服务: {', '.join(stopped_services)}")

        if summary["healthy"] < summary["total"]:
            recommendations.append("建议检查不健康服务的日志和配置")

        if not recommendations:
            recommendations.append("所有服务运行正常,继续保持!")

        return recommendations

    # ==================== 私有辅助方法 ====================

    async def _check_service_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        if service_name not in self.services:
            return False

        service = self.services[service_name]

        try:
            response = requests.get(service["health_url"], timeout=5)
            is_healthy = response.status_code == 200

            # 缓存结果
            self._agent_health_cache[service_name] = {
                "healthy": is_healthy,
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat(),
            }
            self._last_health_check[service_name] = datetime.now()

            return is_healthy

        except Exception:
            self._agent_health_cache[service_name] = {
                "healthy": False,
                "error": "connection_failed",
                "timestamp": datetime.now().isoformat(),
            }
            return False

    async def _check_port(self, port: int) -> bool:
        """检查端口是否开放"""
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _start_docker_service(self, service_name: str) -> dict[str, Any]:
        """启动Docker服务"""
        self.services[service_name]
        try:
            result = subprocess.run(
                ["docker", "start", service_name], capture_output=True, text=True, timeout=30
            )
            return {"success": result.returncode == 0, "message": result.stdout or result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _start_python_service(self, service_name: str) -> dict[str, Any]:
        """启动Python服务"""
        service = self.services[service_name]
        script = service.get("startup_script")

        if not script or not Path(script).exists():
            return {"success": False, "message": f"未配置启动脚本或脚本不存在: {script}"}

        try:
            # 后台启动
            process = subprocess.Popen(
                ["python3", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return {
                "success": True,
                "message": f"服务已启动,PID: {process.pid}",
                "pid": process.pid,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _start_agent_service(self, service_name: str) -> dict[str, Any]:
        """启动智能体服务"""
        # 智能体服务可能通过不同的方式启动
        # 这里返回提示信息
        service = self.services[service_name]
        return {
            "success": False,
            "message": f"请手动启动 {service['name']} 服务(端口 {service['port']})",
            "suggestion": "智能体服务需要手动启动或配置启动脚本",
        }

    async def _stop_docker_service(self, service_name: str) -> dict[str, Any]:
        """停止Docker服务"""
        try:
            result = subprocess.run(
                ["docker", "stop", service_name], capture_output=True, text=True, timeout=30
            )
            return {"success": result.returncode == 0, "message": result.stdout or result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _stop_python_service(self, service_name: str) -> dict[str, Any]:
        """停止Python服务"""
        service = self.services[service_name]

        # 通过端口查找进程
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{service['port']}"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip()
                subprocess.run(["kill", pid], timeout=5)
                return {"success": True, "message": f"服务已停止,PID: {pid}"}
            else:
                return {"success": True, "message": "服务未运行"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _stop_agent_service(self, service_name: str) -> dict[str, Any]:
        """停止智能体服务"""
        # 智能体服务停止逻辑与Python服务类似
        return await self._stop_python_service(service_name)


# ==================== 全局实例 ====================

_controller_instance: XiaonuoPlatformControllerV3 | None = None


def get_platform_controller() -> XiaonuoPlatformControllerV3:
    """获取平台控制器单例"""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = XiaonuoPlatformControllerV3()
    return _controller_instance
