#!/usr/bin/env python3
from __future__ import annotations
"""
Athena增强平台控制器
Enhanced Platform Controller - 小诺的完整平台控制能力

作者: 小诺·双鱼公主
版本: v2.0.0
创建: 2025-12-25

新增功能:
1. Docker/Podman容器集成
2. 服务健康检查端点
3. 服务依赖关系图
4. 自动重启和故障恢复
"""

import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import requests

# 配置日志
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    UNKNOWN = "unknown"
    UNHEALTHY = "unhealthy"


class ServiceType(Enum):
    """服务类型"""

    PYTHON = "python"
    DOCKER = "docker"
    PODMAN = "podman"
    SCRIPT = "script"
    SYSTEMD = "systemd"


@dataclass
class ServiceDependency:
    """服务依赖关系"""

    service_name: str
    depends_on: list[str] = field(default_factory=list)
    required: bool = True  # 是否必须依赖
    startup_order: int = 0  # 启动顺序


@dataclass
class HealthCheckConfig:
    """健康检查配置"""

    enabled: bool = True
    url: Optional[str] = None
    interval: int = 30  # 检查间隔(秒)
    timeout: int = 5  # 超时时间
    retries: int = 3  # 重试次数
    endpoint: str = "/health"


@dataclass
class ServiceInfo:
    """服务信息"""

    name: str
    category: str
    service_type: ServiceType
    path: str
    entry_file: Optional[str]
    port: Optional[int]
    status: ServiceStatus = ServiceStatus.UNKNOWN
    pid: Optional[int] = None
    container_id: Optional[str] = None
    health_url: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)
    startup_order: int = 0
    description: str = ""
    health_config: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    last_check: datetime | None = None
    check_failures: int = 0
    auto_restart: bool = True
    max_restarts: int = 3
    restart_count: int = 0


class ContainerManager:
    """容器管理器 - 支持Docker和Podman"""

    def __init__(self):
        self.docker_available = self._check_command("docker")
        self.podman_available = self._check_command("podman")
        self.preferred = "docker" if self.docker_available else "podman"

    def _check_command(self, cmd: str) -> bool:
        """检查命令是否可用"""
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_available(self) -> bool:
        """检查是否有容器引擎可用"""
        return self.docker_available or self.podman_available

    def get_command(self) -> str:
        """获取可用的容器命令"""
        if self.docker_available:
            return "docker"
        elif self.podman_available:
            return "podman"
        raise RuntimeError("没有可用的容器引擎(Docker/Podman)")

    def list_containers(self, all: bool = True) -> list[dict]:
        """列出所有容器"""
        cmd = self.get_command()
        try:
            result = subprocess.run(
                [cmd, "ps", "-a", "--format", "json"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                containers = json.loads(result.stdout)
                return containers
            return []
        except Exception as e:
            logging.warning(f"列出容器失败: {e}")
            return []

    def get_container_status(self, container_name: str) -> dict:
        """获取容器状态"""
        cmd = self.get_command()
        try:
            result = subprocess.run(
                [cmd, "inspect", container_name], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data:
                    container = data[0]
                    return {
                        "name": container_name,
                        "id": container["Id"][:12],
                        "status": container["State"]["Status"],
                        "running": container["State"]["Running"],
                        "health": container["State"].get("Health", {"Status": "unknown"})["Status"],
                        "created": container["Created"],
                    }
        except Exception as e:
            logging.warning(f"获取容器状态失败 {container_name}: {e}")

        return {"name": container_name, "status": "unknown", "running": False}

    def start_container(self, container_name: str) -> dict[str, Any]:
        """启动容器"""
        cmd = self.get_command()
        try:
            result = subprocess.run(
                [cmd, "start", container_name], capture_output=True, text=True, timeout=30
            )

            return {
                "success": result.returncode == 0,
                "container": container_name,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except Exception as e:
            return {"success": False, "container": container_name, "error": str(e)}

    def stop_container(self, container_name: str) -> dict[str, Any]:
        """停止容器"""
        cmd = self.get_command()
        try:
            result = subprocess.run(
                [cmd, "stop", container_name], capture_output=True, text=True, timeout=30
            )

            return {
                "success": result.returncode == 0,
                "container": container_name,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except Exception as e:
            return {"success": False, "container": container_name, "error": str(e)}

    def restart_container(self, container_name: str) -> dict[str, Any]:
        """重启容器"""
        cmd = self.get_command()
        try:
            result = subprocess.run(
                [cmd, "restart", container_name], capture_output=True, text=True, timeout=60
            )

            return {
                "success": result.returncode == 0,
                "container": container_name,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except Exception as e:
            return {"success": False, "container": container_name, "error": str(e)}


class DependencyGraph:
    """服务依赖关系图"""

    def __init__(self):
        self.dependencies: dict[str, ServiceDependency] = {}
        self.reverse_deps: dict[str, set[str]] = defaultdict(set)

    def add_dependency(self, service: str, depends_on: str, required: bool = True) -> None:
        """添加依赖关系"""
        if service not in self.dependencies:
            self.dependencies[service] = ServiceDependency(service)

        if depends_on not in self.dependencies[service].depends_on:
            self.dependencies[service].depends_on.append(depends_on)

        self.reverse_deps[depends_on].add(service)

    def get_startup_order(self) -> list[str]:
        """获取启动顺序(拓扑排序)"""
        visited = set()
        temp_visited = set()
        order = []

        def visit(service: str) -> Any:
            if service in temp_visited:
                raise ValueError(f"检测到循环依赖: {service}")
            if service in visited:
                return

            temp_visited.add(service)

            # 先访问依赖项
            deps = self.dependencies.get(service, ServiceDependency(service))
            for dep in deps.depends_on:
                if dep in self.dependencies:
                    visit(dep)

            temp_visited.remove(service)
            visited.add(service)
            order.append(service)

        # 访问所有服务
        for service in self.dependencies:
            if service not in visited:
                visit(service)

        return order

    def get_dependents(self, service: str) -> set[str]:
        """获取依赖于指定服务的所有服务"""
        return self.reverse_deps.get(service, set())

    def can_stop(self, service: str) -> tuple[bool, list[str]]:
        """检查是否可以停止服务(没有运行中的依赖者)"""
        dependents = self.get_dependents(service)
        blocking = []
        for dep in dependents:
            # 这里需要检查依赖者是否在运行
            # 简化处理,返回所有依赖者
            blocking.append(dep)

        return len(blocking) == 0, blocking


class HealthChecker:
    """服务健康检查器"""

    def __init__(self):
        self.check_results: dict[str, dict] = {}
        self.last_check: dict[str, datetime] = {}

    def check_health(self, service_info: ServiceInfo) -> dict[str, Any]:
        """执行健康检查"""
        config = service_info.health_config

        if not config.enabled:
            return {"service": service_info.name, "status": "disabled", "healthy": True}

        # HTTP健康检查
        if config.url:
            return self._check_http(service_info)

        # TCP端口检查
        if service_info.port:
            return self._check_port(service_info)

        # 进程检查
        if service_info.pid:
            return self._check_process(service_info)

        return {
            "service": service_info.name,
            "status": "no_check",
            "healthy": False,
            "message": "没有配置健康检查方式",
        }

    def _check_http(self, service_info: ServiceInfo) -> dict[str, Any]:
        """HTTP健康检查"""
        url = (
            service_info.health_config.url
            or f"http://localhost:{service_info.port}{service_info.health_config.endpoint}"
        )

        try:
            response = requests.get(url, timeout=service_info.health_config.timeout)

            is_healthy = response.status_code == 200

            result = {
                "service": service_info.name,
                "status": "healthy" if is_healthy else "unhealthy",
                "healthy": is_healthy,
                "url": url,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.now().isoformat(),
            }

            # 尝试解析JSON响应
            try:
                result["data"] = response.json()
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                result["data"] = response.text[:200]

            return result

        except requests.exceptions.Timeout:
            return {
                "service": service_info.name,
                "status": "timeout",
                "healthy": False,
                "url": url,
                "error": "请求超时",
            }
        except requests.exceptions.ConnectionError:
            return {
                "service": service_info.name,
                "status": "unreachable",
                "healthy": False,
                "url": url,
                "error": "无法连接",
            }
        except Exception as e:
            return {
                "service": service_info.name,
                "status": "error",
                "healthy": False,
                "error": str(e),
            }

    def _check_port(self, service_info: ServiceInfo) -> dict[str, Any]:
        """检查端口是否开放"""
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(service_info.health_config.timeout)
            result = sock.connect_ex(("localhost", service_info.port))
            sock.close()

            is_healthy = result == 0

            return {
                "service": service_info.name,
                "status": "healthy" if is_healthy else "unhealthy",
                "healthy": is_healthy,
                "check": "port",
                "port": service_info.port,
            }
        except Exception as e:
            return {
                "service": service_info.name,
                "status": "error",
                "healthy": False,
                "error": str(e),
            }

    def _check_process(self, service_info: ServiceInfo) -> dict[str, Any]:
        """检查进程是否存在"""
        try:
            os.kill(service_info.pid, 0)
            return {
                "service": service_info.name,
                "status": "healthy",
                "healthy": True,
                "check": "process",
                "pid": service_info.pid,
            }
        except OSError:
            return {
                "service": service_info.name,
                "status": "unhealthy",
                "healthy": False,
                "check": "process",
                "pid": service_info.pid,
                "error": "进程不存在",
            }


class AutoRestartManager:
    """自动重启管理器"""

    def __init__(self, controller):
        self.controller = controller
        self.restart_history: dict[str, list[datetime]] = defaultdict(list)
        self.running = False
        self.monitor_thread = None

    def should_restart(self, service_info: ServiceInfo) -> bool:
        """判断是否应该重启服务"""
        if not service_info.auto_restart:
            return False

        if service_info.restart_count >= service_info.max_restarts:
            logging.warning(f"服务 {service_info.name} 已达到最大重启次数")
            return False

        # 检查重启频率
        now = datetime.now()
        recent_restarts = [
            t for t in self.restart_history[service_info.name] if t > now - timedelta(minutes=5)
        ]

        if len(recent_restarts) >= 3:
            logging.warning(f"服务 {service_info.name} 5分钟内重启过于频繁")
            return False

        return True

    def record_restart(self, service_name: str) -> Any:
        """记录重启"""
        self.restart_history[service_name].append(datetime.now())

        # 清理旧记录
        cutoff = datetime.now() - timedelta(hours=1)
        self.restart_history[service_name] = [
            t for t in self.restart_history[service_name] if t > cutoff
        ]

    def start_monitoring(self, interval: int = 30) -> Any:
        """启动监控线程"""
        if self.running:
            return

        self.running = True

        def monitor_loop() -> Any:
            while self.running:
                try:
                    self.check_and_restart()
                except Exception as e:
                    logging.error(f"监控循环错误: {e}")

                time.sleep(interval)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self) -> Any:
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

    def check_and_restart(self) -> bool:
        """检查并重启不健康的服务"""
        for name, service_info in self.controller.services.items():
            if service_info.status != ServiceStatus.RUNNING:
                continue

            # 执行健康检查
            health_result = self.controller.health_checker.check_health(service_info)

            if not health_result.get("healthy", False):
                service_info.check_failures += 1

                # 连续失败达到阈值,重启服务
                if service_info.check_failures >= service_info.health_config.retries:
                    if self.should_restart(service_info):
                        logging.warning(f"服务 {name} 不健康,准备重启...")
                        self.controller.restart_service(name)
                        self.record_restart(name)
                        service_info.check_failures = 0
            else:
                service_info.check_failures = 0


class EnhancedPlatformController:
    """增强版平台控制器 - 小诺的完整控制能力"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.services: dict[str, ServiceInfo] = {}
        self.active_pids: dict[str, int] = {}
        self.active_containers: dict[str, str] = {}

        # 子系统
        self.container_manager = ContainerManager()
        self.dependency_graph = DependencyGraph()
        self.health_checker = HealthChecker()
        self.restart_manager = AutoRestartManager(self)

        # 配置文件
        self.registry_file = self.project_root / "config" / "platform_services_registry_v2.json"
        self.state_file = self.project_root / "config" / "platform_state_v2.json"
        self.dependencies_file = self.project_root / "config" / "service_dependencies.json"

        print("🎀 小诺增强平台控制器 v2.0")
        print(f"   项目根目录: {self.project_root}")
        print(
            f"   容器引擎: {self.container_manager.get_command() if self.container_manager.is_available() else '未安装'}"
        )
        print()

        self._load_services()
        self._load_dependencies()
        self._load_state()

    def _load_services(self) -> Any:
        """加载服务配置"""
        if self.registry_file.exists():
            with open(self.registry_file, encoding="utf-8") as f:
                data = json.load(f)
                for svc_data in data.get("services", []):
                    service_info = ServiceInfo(
                        name=svc_data["name"],
                        category=svc_data.get("category", "other"),
                        service_type=ServiceType.PYTHON,  # 默认
                        path=svc_data["path"],
                        entry_file=svc_data.get("entry_file"),
                        port=svc_data.get("port"),
                        description=svc_data.get("description", ""),
                    )

                    # 健康检查配置
                    if "health_check" in svc_data:
                        hc = svc_data["health_check"]
                        service_info.health_config = HealthCheckConfig(
                            enabled=hc.get("enabled", True),
                            url=hc.get("url"),
                            interval=hc.get("interval", 30),
                            timeout=hc.get("timeout", 5),
                            endpoint=hc.get("endpoint", "/health"),
                        )

                    self.services[service_info.name] = service_info

            print(f"✅ 已加载 {len(self.services)} 个服务")
        else:
            self._build_default_services()

    def _build_default_services(self) -> Any:
        """构建默认服务配置"""
        default_services = [
            ServiceInfo(
                name="memory-system",
                category="core",
                service_type=ServiceType.SCRIPT,
                path="core/memory",
                entry_file=None,
                port=None,
                description="记忆系统",
                health_config=HealthCheckConfig(enabled=False),
            ),
            ServiceInfo(
                name="nlp-service",
                category="ai",
                service_type=ServiceType.SCRIPT,
                path="services/nlp",
                entry_file=None,
                port=8001,
                description="NLP服务",
                health_config=HealthCheckConfig(enabled=True, endpoint="/health", interval=30),
            ),
            ServiceInfo(
                name="xiaonuo-coordinator",
                category="core",
                service_type=ServiceType.PYTHON,
                path="services/v2/xiaonuo-intent-service",
                entry_file="main.py",
                port=8002,
                description="小诺协调器",
                startup_order=10,
            ),
            ServiceInfo(
                name="api-gateway",
                category="gateway",
                service_type=ServiceType.DOCKER,
                path="services/api-gateway",
                entry_file="src/main.py",
                port=8080,
                description="API网关",
                startup_order=1,
            ),
        ]

        for svc in default_services:
            self.services[svc.name] = svc

        # 添加依赖关系
        self.dependency_graph.add_dependency("xiaonuo-coordinator", "memory-system")
        self.dependency_graph.add_dependency("xiaonuo-coordinator", "nlp-service")
        self.dependency_graph.add_dependency("api-gateway", "xiaonuo-coordinator")

        print(f"✅ 已创建默认服务配置 ({len(default_services)} 个)")

    def _load_dependencies(self) -> Any:
        """加载依赖关系"""
        if self.dependencies_file.exists():
            with open(self.dependencies_file, encoding="utf-8") as f:
                data = json.load(f)
                for dep_data in data.get("dependencies", []):
                    service = dep_data["service"]
                    for dep in dep_data.get("depends_on", []):
                        self.dependency_graph.add_dependency(
                            service, dep, dep_data.get("required", True)
                        )

            print("✅ 已加载依赖关系图")

    def _load_state(self) -> Any:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, encoding="utf-8") as f:
                state = json.load(f)
                self.active_pids = state.get("active_pids", {})
                self.active_containers = state.get("active_containers", {})

                # 更新服务状态
                for name, pid in self.active_pids.items():
                    if name in self.services:
                        try:
                            os.kill(pid, 0)
                            self.services[name].status = ServiceStatus.RUNNING
                            self.services[name].pid = pid
                        except OSError:
                            self.services[name].status = ServiceStatus.STOPPED

    def _save_state(self) -> Any:
        """保存状态"""
        state = {
            "last_update": datetime.now().isoformat(),
            "active_pids": self.active_pids,
            "active_containers": self.active_containers,
            "controller_version": "v2.0.0",
        }

        self.state_file.parent.mkdir(exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def start_service(self, service_name: str) -> dict[str, Any]:
        """启动服务"""
        if service_name not in self.services:
            return {"success": False, "error": f"未知服务: {service_name}", "certainty": 1.0}

        service_info = self.services[service_name]

        # 检查依赖
        deps = self.dependency_graph.dependencies.get(service_name)
        if deps:
            for dep_name in deps.depends_on:
                dep_status = self.get_service_status(dep_name)
                if not dep_status.get("running") and deps.required:
                    # 尝试启动依赖
                    dep_result = self.start_service(dep_name)
                    if not dep_result.get("success"):
                        return {
                            "success": False,
                            "error": f"依赖服务 {dep_name} 启动失败",
                            "dependency": dep_name,
                            "certainty": 1.0,
                        }

        # 根据服务类型启动
        if service_info.service_type == ServiceType.DOCKER:
            return self._start_container_service(service_name)
        elif service_info.service_type == ServiceType.SCRIPT:
            return self._start_script_service(service_name)
        else:
            return self._start_python_service(service_name)

    def _start_container_service(self, service_name: str) -> dict[str, Any]:
        """启动容器服务"""
        if not self.container_manager.is_available():
            return {"success": False, "error": "容器引擎不可用", "certainty": 1.0}

        service_info = self.services[service_name]
        container_name = f"athena-{service_name}"

        # 检查容器是否存在
        containers = self.container_manager.list_containers()
        container_exists = any(
            c.get("Names", [""])[0].strip("/") in [container_name, service_name] for c in containers
        )

        if container_exists:
            result = self.container_manager.start_container(container_name)
        else:
            # 需要先创建容器(这里简化处理)
            return {
                "success": False,
                "error": f"容器 {container_name} 不存在,需要先创建",
                "certainty": 1.0,
            }

        if result["success"]:
            service_info.status = ServiceStatus.RUNNING
            self.active_containers[service_name] = container_name
            self._save_state()

        return result

    def _start_script_service(self, service_name: str) -> dict[str, Any]:
        """启动脚本服务"""
        service_info = self.services[service_name]

        # 查找启动脚本
        script_path = self.project_root / "dev/scripts/startup" / f"start_{service_name}.sh"

        if script_path.exists():
            try:
                result = subprocess.run(
                    ["bash", str(script_path), "start"], capture_output=True, text=True, timeout=30
                )

                success = result.returncode == 0

                if success:
                    service_info.status = ServiceStatus.RUNNING

                return {
                    "success": success,
                    "service": service_name,
                    "message": f"脚本服务 {service_name} {'启动成功' if success else '启动失败'}",
                    "output": result.stdout,
                    "error": result.stderr if not success else None,
                }
            except Exception as e:
                return {"success": False, "service": service_name, "error": str(e)}

        return {"success": False, "error": f"找不到启动脚本: {script_path}"}

    def _start_python_service(self, service_name: str) -> dict[str, Any]:
        """启动Python服务"""
        service_info = self.services[service_name]

        if not service_info.entry_file:
            return {"success": False, "error": "没有指定入口文件"}

        service_path = self.project_root / service_info.path
        py_file = service_path / service_info.entry_file

        if not py_file.exists():
            return {"success": False, "error": f"入口文件不存在: {py_file}"}

        try:
            # 后台启动
            proc = subprocess.Popen(
                [sys.executable, str(py_file)],
                cwd=str(service_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            self.active_pids[service_name] = proc.pid
            service_info.pid = proc.pid
            service_info.status = ServiceStatus.RUNNING
            self._save_state()

            return {
                "success": True,
                "service": service_name,
                "pid": proc.pid,
                "message": f"服务 {service_name} 已启动 (PID: {proc.pid})",
                "certainty": 0.9,
            }
        except Exception as e:
            return {"success": False, "service": service_name, "error": str(e)}

    def stop_service(self, service_name: str) -> dict[str, Any]:
        """停止服务"""
        if service_name not in self.services:
            return {"success": False, "error": "未知服务"}

        service_info = self.services[service_name]

        # 检查是否有其他服务依赖此服务
        can_stop, blocking = self.dependency_graph.can_stop(service_name)
        if not can_stop and blocking:
            return {
                "success": False,
                "error": f"无法停止,以下服务依赖此服务: {', '.join(blocking)}",
                "blocking_services": list(blocking),
            }

        # 停止容器
        if service_name in self.active_containers:
            result = self.container_manager.stop_container(self.active_containers[service_name])
            if result["success"]:
                del self.active_containers[service_name]
                service_info.status = ServiceStatus.STOPPED
                self._save_state()
            return result

        # 停止进程
        if service_name in self.active_pids:
            pid = self.active_pids[service_name]
            try:
                os.kill(pid, signal.SIGTERM)
                del self.active_pids[service_name]
                service_info.status = ServiceStatus.STOPPED
                service_info.pid = None
                self._save_state()

                return {
                    "success": True,
                    "service": service_name,
                    "message": f"服务 {service_name} 已停止",
                }
            except OSError as e:
                return {"success": False, "error": str(e)}

        return {
            "success": True,
            "service": service_name,
            "message": f"服务 {service_name} 未在运行",
        }

    def restart_service(self, service_name: str) -> dict[str, Any]:
        """重启服务"""
        self.stop_service(service_name)
        time.sleep(2)
        return self.start_service(service_name)

    def get_service_status(self, service_name: str) -> dict[str, Any]:
        """获取服务状态"""
        if service_name not in self.services:
            return {"service": service_name, "error": "未知服务"}

        service_info = self.services[service_name]

        # 执行健康检查
        health_result = self.health_checker.check_health(service_info)
        service_info.last_check = datetime.now()

        return {
            "service": service_name,
            "category": service_info.category,
            "type": service_info.service_type.value,
            "status": service_info.status.value,
            "running": service_info.status == ServiceStatus.RUNNING,
            "healthy": health_result.get("healthy", False),
            "pid": service_info.pid,
            "container": self.active_containers.get(service_name),
            "port": service_info.port,
            "health_check": health_result,
            "last_check": service_info.last_check.isoformat() if service_info.last_check else None,
            "restart_count": service_info.restart_count,
        }

    def get_all_status(self) -> dict[str, Any]:
        """获取所有服务状态"""
        all_status = {}

        for name in self.services:
            all_status[name] = self.get_service_status(name)

        return {
            "timestamp": datetime.now().isoformat(),
            "controller": "小诺·双鱼公主 v2.0",
            "container_engine": (
                self.container_manager.get_command()
                if self.container_manager.is_available()
                else "未安装"
            ),
            "total_services": len(self.services),
            "running_services": sum(
                1 for s in self.services.values() if s.status == ServiceStatus.RUNNING
            ),
            "healthy_services": sum(1 for s in all_status.values() if s.get("healthy")),
            "services": all_status,
        }

    def start_all(self) -> dict[str, Any]:
        """按依赖顺序启动所有服务"""
        # 获取启动顺序
        startup_order = self.dependency_graph.get_startup_order()

        results = {}
        success_count = 0
        failed_count = 0

        for service_name in startup_order:
            if service_name in self.services:
                result = self.start_service(service_name)
                results[service_name] = result

                if result.get("success"):
                    success_count += 1
                else:
                    failed_count += 1

        return {
            "success": True,
            "startup_order": startup_order,
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }

    def stop_all(self) -> dict[str, Any]:
        """按逆序停止所有服务"""
        # 获取启动顺序的逆序
        startup_order = self.dependency_graph.get_startup_order()
        shutdown_order = list(reversed(startup_order))

        results = {}
        for service_name in shutdown_order:
            if service_name in self.services:
                results[service_name] = self.stop_service(service_name)

        return {
            "success": True,
            "shutdown_order": shutdown_order,
            "stopped": len([r for r in results.values() if r.get("success")]),
            "results": results,
        }

    def enable_auto_monitoring(self, interval: int = 30) -> Any:
        """启用自动监控和重启"""
        self.restart_manager.start_monitoring(interval)
        return {"success": True, "message": f"自动监控已启用,检查间隔: {interval}秒"}

    def disable_auto_monitoring(self) -> Any:
        """禁用自动监控"""
        self.restart_manager.stop_monitoring()
        return {"success": True, "message": "自动监控已禁用"}

    def get_platform_summary(self) -> dict[str, Any]:
        """获取平台摘要"""
        all_status = self.get_all_status()

        # 按类别统计
        categories = defaultdict(lambda: {"total": 0, "running": 0, "healthy": 0})
        for _name, status in all_status["services"].items():
            cat = status.get("category", "other")
            categories[cat]["total"] += 1
            if status.get("running"):
                categories[cat]["running"] += 1
            if status.get("healthy"):
                categories[cat]["healthy"] += 1

        return {
            "platform": "Athena工作平台",
            "controller": "小诺·双鱼公主 v2.0.0",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "container_management": self.container_manager.is_available(),
                "health_checking": True,
                "dependency_management": True,
                "auto_restart": self.restart_manager.running,
            },
            "summary": {
                "total_services": all_status["total_services"],
                "running_services": all_status["running_services"],
                "healthy_services": all_status["healthy_services"],
                "unhealthy_services": all_status["running_services"]
                - all_status["healthy_services"],
            },
            "by_category": dict(categories),
            "dependency_graph": {
                "total_dependencies": len(self.dependency_graph.dependencies),
                "startup_order": self.dependency_graph.get_startup_order(),
            },
        }


def main() -> None:
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Athena增强平台控制器 v2.0 - 小诺")
    parser.add_argument(
        "command",
        choices=[
            "start",
            "stop",
            "restart",
            "status",
            "start-all",
            "stop-all",
            "summary",
            "health",
            "enable-monitoring",
            "disable-monitoring",
        ],
    )
    parser.add_argument("--service", help="服务名称")
    parser.add_argument("--json", action="store_true", help="JSON输出")

    args = parser.parse_args()

    # 初始化控制器
    controller = EnhancedPlatformController()

    result = None

    if args.command == "start":
        if not args.service:
            print("❌ 请指定服务名称: --service <name>")
            return
        result = controller.start_service(args.service)

    elif args.command == "stop":
        if not args.service:
            print("❌ 请指定服务名称: --service <name>")
            return
        result = controller.stop_service(args.service)

    elif args.command == "restart":
        if not args.service:
            print("❌ 请指定服务名称: --service <name>")
            return
        result = controller.restart_service(args.service)

    elif args.command == "status":
        if args.service:
            result = controller.get_service_status(args.service)
        else:
            result = controller.get_all_status()

    elif args.command == "start-all":
        result = controller.start_all()

    elif args.command == "stop-all":
        result = controller.stop_all()

    elif args.command == "summary":
        result = controller.get_platform_summary()

    elif args.command == "health":
        result = {
            service: controller.health_checker.check_health(service_info)
            for service, service_info in controller.services.items()
        }

    elif args.command == "enable-monitoring":
        result = controller.enable_auto_monitoring()

    elif args.command == "disable-monitoring":
        result = controller.disable_auto_monitoring()

    # 输出结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
