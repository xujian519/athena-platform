#!/usr/bin/env python3
"""
部署管理器
Deployment Manager

负责生产环境部署、服务管理、健康检查

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    """部署环境"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ServiceStatus(Enum):
    """服务状态"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    status: ServiceStatus
    container_id: str = ""
    ports: str = ""
    uptime: str = ""
    health: str = "unknown"


@dataclass
class DeploymentResult:
    """部署结果"""
    success: bool
    environment: DeploymentEnvironment
    deployed_services: list[str] = field(default_factory=list)
    failed_services: list[str] = field(default_factory=list)
    deployment_time: float = 0.0
    error_message: str | None = None
    endpoints: dict[str, str] = field(default_factory=dict)


class DeploymentManager:
    """
    部署管理器

    功能:
    - Docker Compose服务管理
    - 环境变量管理
    - 健康检查
    - 日志查看
    """

    def __init__(
        self,
        compose_file: str = "docker-compose.yml",
        environment: DeploymentEnvironment = DeploymentEnvironment.PRODUCTION
    ):
        """
        初始化部署管理器

        Args:
            compose_file: Docker Compose文件路径
            environment: 部署环境
        """
        self.compose_file = Path(compose_file)
        self.environment = environment
        self.project_name = "patent_full_text"

        # 服务端点
        self.service_ports = {
            "qdrant": "6333",
            "nebula-graphd": "9669",
            "redis": "6379",
            "app": "8000"
        }

    def check_prerequisites(self) -> dict[str, bool]:
        """
        检查部署前置条件

        Returns:
            {prerequisite: satisfied}
        """
        results = {}

        # 检查Docker
        try:
            result = subprocess.run(
                ["infrastructure/infrastructure/docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            results["infrastructure/infrastructure/docker"] = result.returncode == 0
            if results["infrastructure/infrastructure/docker"]:
                logger.info(f"✅ Docker: {result.stdout.strip()}")
            else:
                logger.error("❌ Docker未安装")
        except Exception as e:
            results["infrastructure/infrastructure/docker"] = False
            logger.error(f"❌ Docker检查失败: {e}")

        # 检查Docker Compose
        try:
            result = subprocess.run(
                ["infrastructure/infrastructure/docker", "compose", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            results["docker_compose"] = result.returncode == 0
            if results["docker_compose"]:
                logger.info(f"✅ Docker Compose: {result.stdout.strip()}")
            else:
                logger.error("❌ Docker Compose未安装")
        except Exception as e:
            results["docker_compose"] = False
            logger.error(f"❌ Docker Compose检查失败: {e}")

        # 检查docker-compose.yml文件
        results["compose_file"] = self.compose_file.exists()
        if results["compose_file"]:
            logger.info(f"✅ docker-compose.yml: {self.compose_file}")
        else:
            logger.error(f"❌ docker-compose.yml不存在: {self.compose_file}")

        # 检查模型目录
        model_dir = Path(__file__).parent.parent.parent.parent / "models"
        results["models_dir"] = model_dir.exists()
        if results["models_dir"]:
            logger.info(f"✅ 模型目录: {model_dir}")
        else:
            logger.warning(f"⚠️  模型目录不存在: {model_dir}")

        return results

    def load_env_file(self, env_file: str = ".env") -> Any | None:
        """
        加载环境变量文件

        Args:
            env_file: 环境变量文件路径
        """
        env_path = Path(env_file)
        if not env_path.exists():
            logger.warning(f"⚠️  环境变量文件不存在: {env_file}")
            return

        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

        logger.info(f"✅ 已加载环境变量: {env_file}")

    def deploy(
        self,
        build: bool = True,
        detach: bool = True,
        force_recreate: bool = False
    ) -> DeploymentResult:
        """
        部署服务

        Args:
            build: 是否构建镜像
            detach: 是否后台运行
            force_recreate: 是否强制重建容器

        Returns:
            DeploymentResult
        """
        start_time = time.time()
        result = DeploymentResult(
            success=False,
            environment=self.environment
        )

        logger.info(f"🚀 开始部署到 {self.environment.value} 环境...")

        try:
            # 构建命令
            cmd = ["infrastructure/infrastructure/docker", "compose", "-f", str(self.compose_file)]
            cmd.extend(["up", "-d"])  # -d = detach

            if build:
                cmd.append("--build")

            if force_recreate:
                cmd.append("--force-recreate")

            # 执行部署
            logger.info(f"执行命令: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(timeout=600)  # 10分钟超时

            if process.returncode == 0:
                logger.info(stdout)

                # 等待服务启动
                time.sleep(10)

                # 获取服务状态
                services = self.get_services_status()
                result.deployed_services = [
                    s.name for s in services
                    if s.status == ServiceStatus.RUNNING
                ]
                result.failed_services = [
                    s.name for s in services
                    if s.status != ServiceStatus.RUNNING
                ]

                # 获取端点
                result.endpoints = self.get_service_endpoints()

                result.success = len(result.failed_services) == 0
                result.deployment_time = time.time() - start_time

                if result.success:
                    logger.info(f"✅ 部署成功! 耗时{result.deployment_time:.2f}秒")
                else:
                    logger.warning(f"⚠️  部署部分成功，失败服务: {result.failed_services}")

            else:
                result.error_message = stderr
                logger.error(f"❌ 部署失败: {stderr}")

        except subprocess.TimeoutExpired:
            result.error_message = "部署超时(10分钟)"
            logger.error("❌ 部署超时")
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"❌ 部署异常: {e}")

        return result

    def stop(self, services: list[str] | None = None) -> bool:
        """
        停止服务

        Args:
            services: 要停止的服务列表，None表示停止所有

        Returns:
            是否成功
        """
        try:
            cmd = ["infrastructure/infrastructure/docker", "compose", "-f", str(self.compose_file), "stop"]
            if services:
                cmd.extend(services)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            success = result.returncode == 0

            if success:
                logger.info("✅ 服务已停止")
            else:
                logger.error(f"❌ 停止服务失败: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"❌ 停止服务异常: {e}")
            return False

    def start(self, services: list[str] | None = None) -> bool:
        """
        启动服务

        Args:
            services: 要启动的服务列表，None表示启动所有

        Returns:
            是否成功
        """
        try:
            cmd = ["infrastructure/infrastructure/docker", "compose", "-f", str(self.compose_file), "start"]
            if services:
                cmd.extend(services)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            success = result.returncode == 0

            if success:
                logger.info("✅ 服务已启动")
            else:
                logger.error(f"❌ 启动服务失败: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"❌ 启动服务异常: {e}")
            return False

    def restart(self, services: list[str] | None = None) -> bool:
        """
        重启服务

        Args:
            services: 要重启的服务列表，None表示重启所有

        Returns:
            是否成功
        """
        try:
            cmd = ["infrastructure/infrastructure/docker", "compose", "-f", str(self.compose_file), "restart"]
            if services:
                cmd.extend(services)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            success = result.returncode == 0

            if success:
                logger.info("✅ 服务已重启")
            else:
                logger.error(f"❌ 重启服务失败: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"❌ 重启服务异常: {e}")
            return False

    def down(self, volumes: bool = False) -> bool:
        """
        停止并删除容器

        Args:
            volumes: 是否删除数据卷

        Returns:
            是否成功
        """
        try:
            cmd = ["infrastructure/infrastructure/docker", "compose", "-f", str(self.compose_file), "down"]
            if volumes:
                cmd.append("-v")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            success = result.returncode == 0

            if success:
                logger.info("✅ 容器已删除")
            else:
                logger.error(f"❌ 删除容器失败: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"❌ 删除容器异常: {e}")
            return False

    def get_services_status(self) -> list[ServiceInfo]:
        """
        获取服务状态

        Returns:
            服务信息列表
        """
        services = []

        try:
            cmd = ["infrastructure/infrastructure/docker", "compose", "-f", str(self.compose_file), "ps"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # 解析输出
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # 跳过标题行
                    if not line.strip():
                        continue

                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[0]
                        status_str = parts[1].lower()

                        if "running" in status_str or "up" in status_str:
                            status = ServiceStatus.RUNNING
                        elif "exited" in status_str or "stopped" in status_str:
                            status = ServiceStatus.STOPPED
                        else:
                            status = ServiceStatus.UNKNOWN

                        services.append(ServiceInfo(
                            name=name,
                            status=status,
                            container_id=parts[2] if len(parts) > 2 else "",
                            ports=parts[3] if len(parts) > 3 else ""
                        ))

        except Exception as e:
            logger.error(f"❌ 获取服务状态失败: {e}")

        return services

    def get_service_endpoints(self) -> dict[str, str]:
        """获取服务端点"""
        endpoints = {}
        host = "localhost"

        for service, port in self.service_ports.items():
            endpoints[service] = f"http://{host}:{port}"

        return endpoints

    def get_logs(
        self,
        service: str | None = None,
        tail: int = 100,
        follow: bool = False
    ) -> str:
        """
        获取服务日志

        Args:
            service: 服务名称
            tail: 显示最后N行
            follow: 是否持续跟踪

        Returns:
            日志内容
        """
        try:
            cmd = ["infrastructure/infrastructure/docker", "compose", "-f", str(self.compose_file), "logs"]
            cmd.extend(["--tail", str(tail)])

            if follow:
                cmd.append("--follow")

            if service:
                cmd.append(service)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout

        except Exception as e:
            return f"获取日志失败: {e}"

    def health_check(self) -> dict[str, bool]:
        """
        健康检查所有服务

        Returns:
            {service: healthy}
        """
        health_status = {}

        services = self.get_services_status()
        for service in services:
            health_status[service.name] = service.status == ServiceStatus.RUNNING

        return health_status

    def get_metrics(self) -> dict[str, Any]:
        """
        获取系统指标

        Returns:
            系统指标
        """
        metrics = {
            "services": {},
            "containers": {},
            "timestamp": time.time()
        }

        # 获取容器统计
        try:
            cmd = ["infrastructure/infrastructure/docker", "stats", "--no-stream", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line:
                        try:
                            stats = json.loads(line)
                            container_name = stats.get("Name", "")
                            if container_name.startswith("patent_"):
                                metrics["containers"][container_name] = {
                                    "cpu": stats.get("CPUPerc", "N/A"),
                                    "modules/modules/memory/modules/memory/modules/memory/memory": stats.get("MemUsage", "N/A"),
                                    "net_io": stats.get("NetIO", "N/A"),
                                    "block_io": stats.get("BlockIO", "N/A")
                                }
                        except json.JSONDecodeError:
                            pass

        except Exception as e:
            logger.error(f"❌ 获取指标失败: {e}")

        # 服务状态
        metrics["services"] = self.health_check()

        return metrics


# ========== 便捷函数 ==========

def create_deployment_manager(
    compose_file: str = "docker-compose.yml",
    environment: str = "production"
) -> DeploymentManager:
    """创建部署管理器"""
    env = DeploymentEnvironment(environment)
    return DeploymentManager(compose_file, env)


def deploy_service(
    compose_file: str = "docker-compose.yml",
    environment: str = "production",
    **kwargs
) -> DeploymentResult:
    """
    快速部署

    Args:
        compose_file: Docker Compose文件路径
        environment: 环境名称
        **kwargs: 传递给deploy()的参数

    Returns:
        DeploymentResult
    """
    manager = create_deployment_manager(compose_file, environment)
    return manager.deploy(**kwargs)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("部署管理器示例")
    print("=" * 70)

    # 创建部署管理器
    manager = create_deployment_manager(
        compose_file="docker-compose.yml",
        environment="production"
    )

    # 检查前置条件
    print("\n🔍 检查部署前置条件...")
    prerequisites = manager.check_prerequisites()

    all_satisfied = all(prerequisites.values())
    if not all_satisfied:
        print("\n⚠️  部署前置条件不满足，请先解决以下问题:")
        for name, satisfied in prerequisites.items():
            if not satisfied:
                print(f"  ❌ {name}")
        return

    print("\n✅ 所有前置条件满足")

    # 获取当前服务状态
    print("\n📊 当前服务状态:")
    services = manager.get_services_status()
    for service in services:
        status_emoji = "✅" if service.status == ServiceStatus.RUNNING else "❌"
        print(f"  {status_emoji} {service.name}: {service.status.value}")

    # 端点信息
    print("\n🔗 服务端点:")
    endpoints = manager.get_service_endpoints()
    for service, endpoint in endpoints.items():
        print(f"  {service}: {endpoint}")

    # 健康检查
    print("\n🏥 健康检查:")
    health = manager.health_check()
    for service, healthy in health.items():
        status_emoji = "✅" if healthy else "❌"
        print(f"  {status_emoji} {service}")


if __name__ == "__main__":
    main()
