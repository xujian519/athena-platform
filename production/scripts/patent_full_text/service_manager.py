#!/usr/bin/env python3
"""
专利全文处理系统 - 服务管理器
Patent Full Text Processing System - Service Manager

支持按需启动、停止和管理专利处理服务

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import argparse
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

# 模块级日志
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    status: ServiceStatus
    pid: int | None = None
    uptime: float = 0.0
    last_check: str = ""
    error: str | None = None
    details: dict = field(default_factory=dict)


class PatentServiceManager:
    """专利服务管理器"""

    def __init__(self, root_dir: Path | None = None):
        """
        初始化服务管理器

        Args:
            root_dir: 专利系统根目录
        """
        if root_dir is None:
            root_dir = Path(__file__).parent
        self.root_dir = Path(root_dir)
        self.config_dir = self.root_dir / "config"
        self.pid_dir = self.root_dir / "pids"
        self.log_dir = self.root_dir / "logs"

        # 确保目录存在
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 服务配置
        self.services = {
            "qdrant": {
                "name": "Qdrant向量数据库",
                "docker_name": "patent_qdrant",
                "ports": [6333, 6334],
                "check_url": "http://localhost:6333/health"
            },
            "nebula": {
                "name": "NebulaGraph图数据库",
                "docker_name": "patent_nebula_graphd",
                "ports": [9669],
                "check_port": 9669
            },
            "redis": {
                "name": "Redis缓存",
                "docker_name": "patent_redis",
                "ports": [6379],
                "check_port": 6379
            },
            "app": {
                "name": "专利处理应用",
                "docker_name": "patent_app",
                "ports": [8000],
                "check_url": "http://localhost:8000/health"
            }
        }

        self.pid_file = self.pid_dir / "service_manager.pid"

    def get_status(self, service: str | None = None) -> dict[str, ServiceInfo]:
        """
        获取服务状态

        Args:
            service: 服务名称（None表示获取所有服务）

        Returns:
            服务状态字典
        """
        results = {}

        services_to_check = [service] if service else self.services.keys()

        for svc_name in services_to_check:
            svc_config = self.services.get(svc_name)
            if not svc_config:
                continue

            info = ServiceInfo(
                name=svc_name,
                status=ServiceStatus.STOPPED,
                last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # 检查Docker容器状态
            docker_name = svc_config.get("docker_name")
            if docker_name:
                is_running = self._check_docker_container(docker_name)
                if is_running:
                    info.status = ServiceStatus.RUNNING
                    # 获取运行时间
                    info.uptime = self._get_container_uptime(docker_name)
                else:
                    info.status = ServiceStatus.STOPPED

            results[svc_name] = info

        return results

    def start_service(self, service: str, wait: bool = True, timeout: int = 60) -> bool:
        """
        启动服务

        Args:
            service: 服务名称或"all"
            wait: 是否等待服务就绪
            timeout: 等待超时时间

        Returns:
            是否启动成功
        """
        print(f"\n{'='*60}")
        print(f"  启动服务: {service}")
        print(f"{'='*60}")

        if service == "all":
            return self._start_all_services(wait, timeout)

        svc_config = self.services.get(service)
        if not svc_config:
            print(f"❌ 未知服务: {service}")
            return False

        # 检查服务状态
        status = self.get_status(service)
        if status[service].status == ServiceStatus.RUNNING:
            print(f"⚠️  服务已在运行: {service}")
            return True

        # 启动服务
        print(f"🚀 启动 {svc_config['name']}...")

        # 使用docker-compose启动
        if self._docker_compose_start(service):
            print(f"✅ {svc_config['name']} 启动成功")

            # 等待服务就绪
            if wait:
                return self._wait_for_service(service, timeout)
            return True
        else:
            print(f"❌ {svc_config['name']} 启动失败")
            return False

    def stop_service(self, service: str) -> bool:
        """
        停止服务

        Args:
            service: 服务名称或"all"

        Returns:
            是否停止成功
        """
        print(f"\n{'='*60}")
        print(f"  停止服务: {service}")
        print(f"{'='*60}")

        if service == "all":
            return self._stop_all_services()

        svc_config = self.services.get(service)
        if not svc_config:
            print(f"❌ 未知服务: {service}")
            return False

        print(f"🛑 停止 {svc_config['name']}...")

        # 使用docker-compose停止
        if self._docker_compose_stop(service):
            print(f"✅ {svc_config['name']} 已停止")
            return True
        else:
            print(f"❌ {svc_config['name']} 停止失败")
            return False

    def restart_service(self, service: str, wait: bool = True) -> bool:
        """
        重启服务

        Args:
            service: 服务名称
            wait: 是否等待服务就绪

        Returns:
            是否重启成功
        """
        print(f"\n{'='*60}")
        print(f"  重启服务: {service}")
        print(f"{'='*60}")

        if not self.stop_service(service):
            return False

        return self.start_service(service, wait)

    def start_on_demand(
        self,
        task_type: str,
        task_params: dict,
        auto_stop: bool = False,
        idle_timeout: int = 300
    ) -> bool:
        """
        按需启动服务

        Args:
            task_type: 任务类型 (process_patent/download_pdf等)
            task_params: 任务参数
            auto_stop: 是否在任务完成后自动停止
            idle_timeout: 空闲超时时间（秒）

        Returns:
            是否启动成功
        """
        print(f"\n{'='*60}")
        print("  按需启动服务")
        print(f"{'='*60}")
        print(f"任务类型: {task_type}")
        print(f"自动停止: {auto_stop}")
        print(f"空闲超时: {idle_timeout}秒")

        # 判断需要启动的服务
        required_services = self._get_required_services(task_type)

        print(f"\n需要启动的服务: {', '.join(required_services)}")

        # 启动必要的服务
        for service in required_services:
            if not self.start_service(service, wait=True):
                return False

        print("\n✅ 所有必要服务已启动")
        print(f"服务列表: {', '.join([self.services[s]['name'] for s in required_services])}")

        return True

    def _start_all_services(self, wait: bool, timeout: int) -> bool:
        """启动所有服务"""
        # 按依赖顺序启动
        start_order = ["qdrant", "nebula", "redis", "app"]

        for service in start_order:
            if not self.start_service(service, wait, timeout):
                return False

        return True

    def _stop_all_services(self) -> bool:
        """停止所有服务"""
        # 按反向依赖顺序停止
        stop_order = ["app", "redis", "nebula", "qdrant"]

        for service in stop_order:
            if not self.stop_service(service):
                return False

        return True

    def _get_required_services(self, task_type: str) -> list[str]:
        """
        获取任务所需的服务列表

        Args:
            task_type: 任务类型

        Returns:
            需要启动的服务列表
        """
        # 所有任务都需要的基础服务
        base_services = []

        # 根据任务类型添加特定服务
        if task_type in ["process_patent", "search_patents"]:
            # 需要向量数据库
            base_services.append("qdrant")

        if task_type in ["process_patent", "get_patent_triples"]:
            # 需要图数据库
            base_services.append("nebula")

        if task_type in ["search_patents", "cache_stats"]:
            # 需要缓存
            base_services.append("redis")

        # 应用服务
        if task_type != "download_pdfs":  # PDF下载不需要app服务
            base_services.append("app")

        return base_services

    def _check_docker_container(self, container_name: str) -> bool:
        """检查Docker容器是否运行"""
        try:
            result = subprocess.run(
                ["infrastructure/infrastructure/docker", "inspect", "-f", "{{.State.Running}}", container_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == "true"
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return False

    def _get_container_uptime(self, container_name: str) -> float:
        """获取容器运行时间"""
        try:
            result = subprocess.run(
                ["infrastructure/infrastructure/docker", "inspect", "-f", "{{.State.StartedAt}}", container_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                start_time_str = result.stdout.strip()
                if start_time_str:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    uptime = (datetime.now(start_time.tzinfo) - start_time).total_seconds()
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
        return 0.0

    def _docker_compose_start(self, service: str) -> bool:
        """使用docker-compose启动服务"""
        try:
            cmd = ["docker-compose", "up", "-d", service]
            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception as e:
            print(f"启动异常: {e}")
            return False

    def _docker_compose_stop(self, service: str) -> bool:
        """使用docker-compose停止服务"""
        try:
            cmd = ["docker-compose", "stop", service]
            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            print(f"停止异常: {e}")
            return False

    def _wait_for_service(self, service: str, timeout: int = 60) -> bool:
        """等待服务就绪"""
        svc_config = self.services.get(service)
        if not svc_config:
            return True

        print("⏳ 等待服务就绪...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查HTTP端点
            check_url = svc_config.get("check_url")
            if check_url:
                if self._check_http_endpoint(check_url):
                    print("✅ 服务就绪")
                    return True

            # 检查端口
            check_port = svc_config.get("check_port")
            if check_port:
                if self._check_port_open(check_port):
                    print("✅ 服务就绪")
                    return True

            time.sleep(2)

        print("⚠️  服务启动超时")
        return False

    def _check_http_endpoint(self, url: str, timeout: int = 5) -> bool:
        """检查HTTP端点"""
        try:
            pass
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return False

    def _check_port_open(self, port: int, host: str = "localhost") -> bool:
        """检查端口是否开放"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return False

    def print_status(self) -> None:
        """打印服务状态"""
        print("\n" + "="*60)
        print("  专利全文处理系统 - 服务状态")
        print("="*60)

        status = self.get_status()

        for service, info in status.items():
            svc_config = self.services.get(service, {})
            icon = {
                ServiceStatus.RUNNING: "✅",
                ServiceStatus.STARTING: "🔄",
                ServiceStatus.STOPPED: "⭕",
                ServiceStatus.ERROR: "❌"
            }.get(info.status, "❓")

            uptime_str = f" ({int(info.uptime)}s)" if info.uptime > 0 else ""
            print(f"{icon} {svc_config.get('name', service)}: {info.status.value}{uptime_str}")

        print("="*60)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="专利全文处理系统 - 服务管理器"
    )
    parser.add_argument(
        "action",
        choices=["status", "start", "stop", "restart", "on-demand"],
        help="操作: status(状态)/start(启动)/stop(停止)/restart(重启)/on-demand(按需启动)"
    )
    parser.add_argument(
        "--service",
        default="all",
        help="服务名称（默认为all）"
    )
    parser.add_argument(
        "--task",
        help="任务类型（用于on-demand）"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="启动服务时不等待就绪"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="启动超时时间（秒）"
    )

    args = parser.parse_args()

    # 创建服务管理器
    manager = PatentServiceManager()

    # 执行操作
    if args.action == "status":
        manager.print_status()
    elif args.action == "start":
        manager.start_service(args.service, wait=not args.no_wait, timeout=args.timeout)
    elif args.action == "stop":
        manager.stop_service(args.service)
    elif args.action == "restart":
        manager.restart_service(args.service, wait=not args.no_wait)
    elif args.action == "on-demand":
        if not args.task:
            print("❌ 按需启动需要指定任务类型 (--task)")
            return
        manager.start_on_demand(args.task, {})


if __name__ == "__main__":
    main()
