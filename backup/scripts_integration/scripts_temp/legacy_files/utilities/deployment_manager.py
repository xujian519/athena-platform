#!/usr/bin/env python3
"""
Athena平台统一部署管理器
Unified Deployment Manager for Athena Platform
支持一键部署、服务管理、监控和健康检查
"""

import os
import sys
import time
import json
import subprocess
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 添加父目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceConfig:
    """服务配置类"""
    def __init__(self, name: str, path: str, port: int,
                 command: str, env_file: str | None = None,
                 dependencies: List[str] = None,
                 health_endpoint: str = "/health"):
        self.name = name
        self.path = Path(path)
        self.port = port
        self.command = command
        self.env_file = env_file
        self.dependencies = dependencies or []
        self.health_endpoint = health_endpoint
        self.status = "stopped"
        self.pid = None
        self.start_time = None

class DeploymentManager:
    """统一部署管理器"""

    def __init__(self, base_path: str = "/Users/xujian/Athena工作平台/services"):
        self.base_path = Path(base_path)
        self.services: Dict[str, ServiceConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.load_services_config()

    def load_services_config(self):
        """加载所有服务配置"""
        # 定义服务配置
        services_config = [
            # 核心基础设施
            {
                "name": "core-services",
                "path": "core-services",
                "command": "./start_all.sh",
                "port": None,  # 多个端口
                "dependencies": []
            },

            # AI服务层
            {
                "name": "ai-models",
                "path": "ai-models",
                "command": "python main.py",
                "port": 9000,
                "dependencies": ["core-services"],
                "env_file": ".env"
            },
            {
                "name": "ai-services",
                "path": "ai-services",
                "command": "python main.py",
                "port": 9001,
                "dependencies": ["core-services"]
            },

            # 智能体层
            {
                "name": "yunpat-agent",
                "path": "yunpat-agent",
                "command": "python app/main.py",
                "port": 8000,
                "dependencies": ["core-services", "data-services"]
            },
            {
                "name": "agent-services",
                "path": "agent-services",
                "command": "python agent_manager.py",
                "port": 9002,
                "dependencies": ["core-services"]
            },

            # 核心服务层
            {
                "name": "api-gateway",
                "path": "api-gateway",
                "command": "npm start",
                "port": 3000,
                "dependencies": ["core-services"],
                "env_file": ".env"
            },
            {
                "name": "athena-platform",
                "path": "athena-platform",
                "command": "python main.py",
                "port": 8001,
                "dependencies": ["core-services"]
            },
            {
                "name": "browser-automation-service",
                "path": "browser-automation-service",
                "command": "python main.py",
                "port": 8002,
                "dependencies": ["core-services"]
            },
            {
                "name": "crawler-service",
                "path": "crawler-service",
                "command": "python main.py",
                "port": 8003,
                "dependencies": ["core-services"]
            },
            {
                "name": "optimization-service",
                "path": "optimization-service",
                "command": "python main.py",
                "port": 8004,
                "dependencies": ["core-services"]
            },

            # 数据服务层
            {
                "name": "data-services",
                "path": "data-services",
                "command": "./start_all.sh",
                "port": None,  # 多个端口
                "dependencies": ["core-services"]
            },
            {
                "name": "visualization-tools",
                "path": "visualization-tools",
                "command": "python main.py",
                "port": 8005,
                "dependencies": ["core-services", "data-services"]
            },

            # 集成服务层
            {
                "name": "platform-integration-service",
                "path": "platform-integration-service",
                "command": "python main.py",
                "port": 8006,
                "dependencies": ["core-services"]
            }
        ]

        # 创建服务配置对象
        for config in services_config:
            self.services[config["name"]] = ServiceConfig(**config)

    def start_service(self, service_name: str) -> bool:
        """启动单个服务"""
        if service_name not in self.services:
            logger.error(f"未知服务: {service_name}")
            return False

        service = self.services[service_name]

        # 检查服务是否已运行
        if service.status == "running":
            logger.info(f"服务 {service_name} 已在运行")
            return True

        # 检查依赖
        for dep in service.dependencies:
            if dep not in self.services or self.services[dep].status != "running":
                logger.error(f"服务 {service_name} 的依赖 {dep} 未运行")
                return False

        # 切换到服务目录
        original_dir = os.getcwd()
        service_dir = self.base_path / service.path

        if not service_dir.exists():
            logger.error(f"服务目录不存在: {service_dir}")
            return False

        try:
            os.chdir(service_dir)

            # 准备环境变量
            env = os.environ.copy()
            if service.env_file and (service_dir / service.env_file).exists():
                logger.info(f"加载环境文件: {service.env_file}")
                with open(service.env_file) as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env[key] = value

            # 启动服务
            if service.command.startswith("./"):
                # Shell脚本
                process = subprocess.Popen(
                    service.command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
            else:
                # Python或Node.js命令
                cmd = service.command.split()
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )

            # 更新服务状态
            service.status = "starting"
            service.pid = process.pid
            service.start_time = datetime.now()
            self.processes[service_name] = process

            logger.info(f"服务 {service_name} 启动中 (PID: {process.pid})")

            # 等待服务启动
            time.sleep(2)

            # 检查服务是否成功启动
            if process.poll() is None:
                service.status = "running"
                logger.info(f"✅ 服务 {service_name} 启动成功")
                return True
            else:
                # 读取错误输出
                stderr = process.stderr.read().decode()
                logger.error(f"❌ 服务 {service_name} 启动失败: {stderr}")
                service.status = "failed"
                return False

        except Exception as e:
            logger.error(f"启动服务 {service_name} 时出错: {e}")
            service.status = "failed"
            return False
        finally:
            os.chdir(original_dir)

    def stop_service(self, service_name: str) -> bool:
        """停止单个服务"""
        if service_name not in self.services:
            logger.error(f"未知服务: {service_name}")
            return False

        service = self.services[service_name]

        if service.status == "stopped":
            logger.info(f"服务 {service_name} 已停止")
            return True

        # 检查哪些服务依赖此服务
        dependents = [
            name for name, s in self.services.items()
            if service_name in s.dependencies and s.status == "running"
        ]

        if dependents:
            logger.warning(f"以下服务依赖 {service_name}，请先停止: {', '.join(dependents)}")
            return False

        # 停止进程
        if service_name in self.processes:
            process = self.processes[service_name]
            process.terminate()

            # 等待进程结束
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"强制终止服务 {service_name}")
                process.kill()
                process.wait()

            del self.processes[service_name]

        # 更新状态
        service.status = "stopped"
        service.pid = None
        service.start_time = None

        logger.info(f"✅ 服务 {service_name} 已停止")
        return True

    def start_all(self) -> Dict[str, bool]:
        """启动所有服务（按依赖顺序）"""
        results = {}

        # 按依赖顺序启动
        started = set()

        # 首先启动无依赖的服务
        for name, service in self.services.items():
            if not service.dependencies:
                results[name] = self.start_service(name)
                started.add(name)

        # 然后启动有依赖的服务
        max_attempts = len(self.services)
        attempt = 0

        while len(started) < len(self.services) and attempt < max_attempts:
            attempt += 1
            for name, service in self.services.items():
                if name not in started:
                    # 检查所有依赖是否已启动
                    if all(dep in started for dep in service.dependencies):
                        results[name] = self.start_service(name)
                        started.add(name)

        # 输出结果
        success_count = sum(1 for r in results.values() if r)
        logger.info(f"启动完成: {success_count}/{len(self.services)} 个服务成功")

        return results

    def stop_all(self) -> Dict[str, bool]:
        """停止所有服务（按依赖逆序）"""
        results = {}

        # 按依赖逆序停止
        stopped = set()

        # 首先停止没有其他服务依赖的服务
        for name, service in self.services.items():
            if not any(name in s.dependencies for s in self.services.values()):
                results[name] = self.stop_service(name)
                stopped.add(name)

        # 然后停止其他服务
        max_attempts = len(self.services)
        attempt = 0

        while len(stopped) < len(self.services) and attempt < max_attempts:
            attempt += 1
            for name, service in self.services.items():
                if name not in stopped:
                    # 检查是否有正在运行的服务依赖此服务
                    if not any(
                        name in s.dependencies and s.status == "running"
                        for s in self.services.values()
                    ):
                        results[name] = self.stop_service(name)
                        stopped.add(name)

        # 输出结果
        success_count = sum(1 for r in results.values() if r)
        logger.info(f"停止完成: {success_count}/{len(self.services)} 个服务成功")

        return results

    def restart_service(self, service_name: str) -> bool:
        """重启单个服务"""
        logger.info(f"重启服务: {service_name}")
        if self.stop_service(service_name):
            return self.start_service(service_name)
        return False

    def get_service_status(self, service_name: str = None) -> Dict:
        """获取服务状态"""
        if service_name:
            if service_name not in self.services:
                return {"error": f"未知服务: {service_name}"}
            service = self.services[service_name]

            # 检查进程是否仍在运行
            if service_name in self.processes:
                process = self.processes[service_name]
                if process.poll() is not None:
                    service.status = "stopped"
                    service.pid = None

            return {
                "name": service.name,
                "status": service.status,
                "port": service.port,
                "pid": service.pid,
                "start_time": service.start_time.isoformat() if service.start_time else None
            }
        else:
            # 返回所有服务状态
            return {
                name: self.get_service_status(name)
                for name in self.services.keys()
            }

    def health_check(self) -> Dict[str, Dict]:
        """健康检查所有服务"""
        import httpx
        health_status = {}

        with httpx.Client(timeout=5.0) as client:
            for name, service in self.services.items():
                if service.status == "running" and service.port:
                    url = f"http://localhost:{service.port}/health"
                    try:
                        response = client.get(url)
                        health_status[name] = {
                            "status": "healthy" if response.status_code == 200 else "unhealthy",
                            "response_time": response.elapsed.total_seconds(),
                            "status_code": response.status_code
                        }
                    except Exception as e:
                        health_status[name] = {
                            "status": "unreachable",
                            "error": str(e)
                        }
                else:
                    health_status[name] = {
                        "status": service.status,
                        "port": service.port
                    }

        return health_status

    def get_logs(self, service_name: str, lines: int = 100) -> str:
        """获取服务日志"""
        if service_name not in self.services:
            return f"未知服务: {service_name}"

        service = self.services[service_name]

        # 如果服务正在运行，尝试获取实时日志
        if service_name in self.processes:
            process = self.processes[service_name]
            # 读取输出缓冲区
            stdout = process.stdout.read().decode() if process.stdout else ""
            stderr = process.stderr.read().decode() if process.stderr else ""

            logs = []
            if stdout:
                logs.append("STDOUT:")
                logs.append(stdout[-2000:] if len(stdout) > 2000 else stdout)
            if stderr:
                logs.append("\nSTDERR:")
                logs.append(stderr[-2000:] if len(stderr) > 2000 else stderr)

            return "\n".join(logs) if logs else "无日志输出"
        else:
            return f"服务 {service_name} 未运行"

def main():
    """主函数 - 命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="Athena平台部署管理器")
    parser.add_argument("command", choices=[
        "start", "stop", "restart", "status", "health", "logs", "start-all", "stop-all"
    ], help="执行的命令")
    parser.add_argument("--service", "-s", help="服务名称")
    parser.add_argument("--lines", "-n", type=int, default=100, help="日志行数")

    args = parser.parse_args()

    # 创建部署管理器
    manager = DeploymentManager()

    # 执行命令
    if args.command == "start":
        if args.service:
            success = manager.start_service(args.service)
            sys.exit(0 if success else 1)
        else:
            print("请指定要启动的服务名称 (--service)")

    elif args.command == "stop":
        if args.service:
            success = manager.stop_service(args.service)
            sys.exit(0 if success else 1)
        else:
            print("请指定要停止的服务名称 (--service)")

    elif args.command == "restart":
        if args.service:
            success = manager.restart_service(args.service)
            sys.exit(0 if success else 1)
        else:
            print("请指定要重启的服务名称 (--service)")

    elif args.command == "start-all":
        results = manager.start_all()
        for name, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {name}")

    elif args.command == "stop-all":
        results = manager.stop_all()
        for name, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {name}")

    elif args.command == "status":
        status = manager.get_service_status(args.service)
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.command == "health":
        health = manager.health_check()
        print("服务健康状态:")
        for name, info in health.items():
            status_icon = "✅" if info.get("status") in ["healthy", "running"] else "❌"
            print(f"{status_icon} {name}: {info.get('status', 'unknown')}")

    elif args.command == "logs":
        if args.service:
            logs = manager.get_logs(args.service, args.lines)
            print(logs)
        else:
            print("请指定要查看日志的服务名称 (--service)")

if __name__ == "__main__":
    main()