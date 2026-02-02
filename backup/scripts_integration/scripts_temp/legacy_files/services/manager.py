#!/usr/bin/env python3
"""
统一服务管理器
管理所有Athena服务的生命周期
"""

import os
import sys
import signal
import time
import subprocess
import logging
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from core.config import config
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker


class ServiceStatus(Enum):
    """服务状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    command: str
    pid: int | None = None
    status: ServiceStatus = ServiceStatus.STOPPED
    port: int | None = None
    health_check_url: str | None = None
    dependencies: List[str] = None
    start_time: float | None = None
    restart_count: int = 0
    last_error: str | None = None


class ServiceManager:
    """服务管理器"""

    def __init__(self):
        self.logger = ScriptLogger("ServiceManager")
        self.services: Dict[str, ServiceInfo] = {}
        self.running_services: Dict[str, int] = {}
        self.stop_event = threading.Event()
        self.load_services_config()

    def load_services_config(self):
        """加载服务配置"""
        self.logger.info("加载服务配置...")

        # 从配置文件加载
        services_config = config.get('services', {})

        # 默认服务配置
        default_services = {
            'core_server': {
                'command': 'python -m core.app',
                'port': 8000,
                'dependencies': [],
                'health_check': 'http://localhost:8000/health'
            },
            'ai_service': {
                'command': 'python -m services.ai_app',
                'port': 8001,
                'dependencies': ['core_server'],
                'health_check': 'http://localhost:8001/health'
            },
            'patent_api': {
                'command': 'python -m services.patent_api',
                'port': 8002,
                'dependencies': ['core_server'],
                'health_check': 'http://localhost:8002/health'
            },
            'storage_service': {
                'command': 'python -m storage-system.main',
                'dependencies': ['core_server'],
                'port': None,
                'health_check': None
            }
        }

        # 合并配置
        services_config.update(default_services)

        # 转换为ServiceInfo对象
        for name, cfg in services_config.items():
            self.services[name] = ServiceInfo(
                name=name,
                command=cfg.get('command', f'python -m {name}'),
                port=cfg.get('port'),
                health_check_url=cfg.get('health_check'),
                dependencies=cfg.get('dependencies', [])
            )

        self.logger.info(f"加载了 {len(self.services)} 个服务配置")

    def start_service(self, service_name: str) -> bool:
        """启动单个服务"""
        if service_name not in self.services:
            self.logger.error(f"服务 {service_name} 未在配置中")
            return False

        service = self.services[service_name]

        # 检查依赖
        if not self._check_dependencies(service_name):
            self.logger.error(f"服务 {service_name} 的依赖未满足")
            return False

        self.logger.info(f"启动服务: {service_name}")

        # 更新状态
        service.status = ServiceStatus.STARTING
        service.start_time = time.time()

        try:
            # 检查端口是否已被占用
            if service.port and self._is_port_in_use(service.port):
                self.logger.warning(f"端口 {service.port} 已被占用")
                return False

            # 启动服务
            env = os.environ.copy()
            env['PYTHONPATH'] = config.get('python.path', '')

            # 切换到项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            os.chdir(project_root)

            process = subprocess.Popen(
                service.command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            service.pid = process.pid
            service.status = ServiceStatus.RUNNING
            self.running_services[service_name] = process.pid

            # 启动监控线程
            self._start_service_monitor(service_name, process)

            self.logger.info(f"服务 {service_name} 启动成功 (PID: {service.pid})")

            return True

        except Exception as e:
            service.status = ServiceStatus.ERROR
            service.last_error = str(e)
            self.logger.error(f"启动服务 {service_name} 失败: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """停止单个服务"""
        if service_name not in self.services:
            self.logger.error(f"服务 {service_name} 不存在")
            return False

        service = self.services[service_name]

        if service.status == ServiceStatus.STOPPED:
            self.logger.info(f"服务 {service_name} 已经停止")
            return True

        self.logger.info(f"停止服务: {service_name}")
        service.status = ServiceStatus.STOPPING

        try:
            if service_name in self.running_services:
                pid = self.running_services[service_name]

                # 先发送SIGTERM信号
                os.kill(pid, signal.SIGTERM)

                # 等待5秒
                time.sleep(5)

                # 如果还在运行，强制终止
                try:
                    os.kill(pid, 0)
except Exception:  # TODO: 根据上下文指定具体异常类型

                del self.running_services[service_name]

            service.status = ServiceStatus.STOPPED
            service.pid = None
            self.logger.info(f"服务 {service_name} 已停止")

            return True

        except Exception as e:
            self.logger.error(f"停止服务 {service_name} 失败: {e}")
            return False

    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        self.logger.info(f"重启服务: {service_name}")

        # 先停止
        if self.stop_service(service_name):
            # 等待一段时间
            time.sleep(2)
            # 再启动
            return self.start_service(service_name)

        return False

    def start_all_services(self) -> Dict[str, bool]:
        """启动所有服务"""
        self.logger.info("启动所有服务...")

        # 按依赖顺序启动
        sorted_services = self._get_start_order()
        results = {}

        for service_name in sorted_services:
            result = self.start_service(service_name)
            results[service_name] = result

            if not result:
                self.logger.error(f"服务 {service_name} 启动失败，停止启动过程")
                # 停止已启动的服务
                for started_service in results:
                    if results[started_service]:
                        self.stop_service(started_service)
                return results

        self.logger.info(f"所有服务启动完成")
        self._show_services_status()
        return results

    def stop_all_services(self) -> Dict[str, bool]:
        """停止所有服务"""
        self.logger.info("停止所有服务...")

        results = {}

        # 按反向顺序停止
        services = list(self.running_services.keys())
        services.reverse()

        for service_name in services:
            results[service_name] = self.stop_service(service_name)

        self.logger.info(f"所有服务已停止")
        return results

    def get_service_status(self, service_name: str) -> ServiceInfo | None:
        """获取服务状态"""
        return self.services.get(service_name)

    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有服务状态"""
        status = {}

        for name, service in self.services.items():
            # 检查进程是否还在运行
            if service.pid and name in self.running_services:
                try:
                    # 发送信号0检查进程是否存在
                    os.kill(service.pid, 0)
                    # 进程还在
                    if service.health_check_url:
                        # TODO: 实际的健康检查
                        pass
                except ProcessLookupError:
                    # 进程已停止
                    service.status = ServiceStatus.STOPPED
                    service.pid = None
                    if name in self.running_services:
                        del self.running_services[name]

            status[name] = {
                'status': service.status.value,
                'pid': service.pid,
                'port': service.port,
                'uptime': time.time() - service.start_time if service.start_time else 0,
                'restart_count': service.restart_count,
                'last_error': service.last_error
            }

        return status

    def _check_dependencies(self, service_name: str) -> bool:
        """检查服务依赖"""
        service = self.services[service_name]
        if not service.dependencies:
            return True

        for dep in service.dependencies:
            if dep not in self.services:
                self.logger.error(f"依赖服务 {dep} 未配置")
                return False

            dep_service = self.services[dep]
            if dep_service.status != ServiceStatus.RUNNING:
                self.logger.error(f"依赖服务 {dep} 未运行 (状态: {dep_service.status.value})")
                return False

        return True

    def _get_start_order(self) -> List[str]:
        """获取服务启动顺序（按依赖关系排序）"""
        visited = set()
        order = []

        def visit(name: str):
            if name not in visited:
                visited.add(name)
                if name in self.services:
                    service = self.services[name]
                    if service.dependencies:
                        for dep in service.dependencies:
                            visit(dep)
                    order.append(name)

        for name in self.services.keys():
            visit(name)

        return order

    def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                s.close()
                return False
        except:
            return True

    def _start_service_monitor(self, service_name: str, process):
        """启动服务监控"""
        def monitor():
            try:
                # 等待进程结束
                return_code = process.wait()

                if return_code != 0:
                    self.logger.warning(f"服务 {service_name} 异常退出 (退出码: {return_code})")

                service.status = ServiceStatus.STOPPED
                service.last_error = f"异常退出: {return_code}"

                if service_name in self.running_services:
                    del self.running_services[service_name]

            except Exception as e:
                self.logger.error(f"服务 {service_name} 监控出错: {e}")

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def _show_services_status(self):
        """显示服务状态"""
        print("\n" + "="*60)
        print("🔧 服务状态总览")
        print("="*60)

        status = self.get_all_status()
        for name, info in status.items():
            status_icon = {
                ServiceStatus.RUNNING: "✅",
                ServiceStatus.STARTING: "🔄",
                ServiceStatus.STOPPING: "⏹️",
                ServiceStatus.STOPPED: "⬜",
                ServiceStatus.ERROR: "❌"
            }.get(info['status'], "❓")

            uptime = f"{info['uptime']:.1f}s" if info['uptime'] > 0 else "0s"

            print(f"{status_icon} {name:20} "
                  f"状态: {info['status']:10} "
                  f"PID: {info['pid']:8} "
                  f"端口: {info['port']:6} "
                  f"运行时间: {uptime}")

        print("="*60)

    def list_services(self):
        """列出所有配置的服务"""
        print("\n📋 配置的服务:")
        print("-" * 40)

        for name, service in self.services.items():
            deps = ", ".join(service.dependencies) if service.dependencies else "无"
            print(f"  - {name}")
            print(f"    命令: {service.command}")
            print(f"    端口: {service.port}")
            print(f"    依赖: {deps}")

    @classmethod
    def instance(cls):
        """获取单例实例"""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_instance(cls):
        """获取单例实例（兼容方法）"""
        return cls.instance()


# 全局实例
service_manager = ServiceManager()