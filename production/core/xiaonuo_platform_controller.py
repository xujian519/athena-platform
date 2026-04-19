#!/usr/bin/env python3
from __future__ import annotations
"""
Athena全平台控制器
Athena Platform Controller - 小诺的平台总控制接口

作者: 小诺·双鱼公主
版本: v1.0.0
创建: 2025-12-25

这是小诺控制整个平台的核心系统
"""

import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ServiceStatus(Enum):
    """服务状态枚举"""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """服务信息"""

    name: str
    category: str
    path: str
    entry_file: str | None
    port: int | None
    status: ServiceStatus
    pid: int | None
    health_url: str | None
    dependencies: list[str]
    description: str


class PlatformController:
    """平台控制器 - 小诺的核心控制能力"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.services_registry = {}
        self.active_pids = {}

        # 确保在正确的目录
        if not (self.project_root / "config").exists():
            self.project_root = Path("/Users/xujian/Athena工作平台")

        self.registry_file = self.project_root / "config" / "platform_services_registry.json"
        self.state_file = self.project_root / "config" / "platform_state.json"

        print("🎀 小诺平台控制器初始化")
        print(f"   项目根目录: {self.project_root}")
        print()

        self._load_services()
        self._load_state()

    def _load_services(self) -> Any:
        """加载服务注册表"""
        if self.registry_file.exists():
            with open(self.registry_file, encoding="utf-8") as f:
                data = json.load(f)
                # 构建服务字典
                for svc in data.get("services", []):
                    self.services_registry[svc["name"]] = svc
            print(f"✅ 已加载 {len(self.services_registry)} 个服务配置")
        else:
            print("⚠️  服务注册表不存在,使用默认配置")
            self._build_default_registry()

    def _build_default_registry(self) -> Any:
        """构建默认服务注册表"""
        default_services = {
            # 核心服务
            "memory-system": {
                "name": "memory-system",
                "category": "core",
                "path": "core/memory",
                "entry_file": None,
                "port": None,
                "start_script": "dev/scripts/startup/start_memory_system.sh",
                "description": "记忆系统 - 记录所有重要时刻",
            },
            "nlp-service": {
                "name": "nlp-service",
                "category": "ai",
                "path": "services/nlp",
                "entry_file": "main.py",
                "port": 8001,
                "start_script": "dev/scripts/startup/start_nlp_service.sh",
                "health_url": "http://localhost:8001/health",
                "description": "NLP服务 - 自然语言理解",
            },
            # AI家族
            "xiaonuo-coordinator": {
                "name": "xiaonuo-coordinator",
                "category": "core",
                "path": "services/v2/xiaonuo-intent-service",
                "entry_file": "main.py",
                "port": 8002,
                "description": "小诺协调器 - 平台总调度",
            },
            "xiaona-legal": {
                "name": "xiaona-legal",
                "category": "data",
                "path": "services/laws-knowledge-base",
                "entry_file": None,
                "port": None,
                "description": "小娜专利法律专家",
            },
            # 网关和服务
            "api-gateway": {
                "name": "api-gateway",
                "category": "gateway",
                "path": "services/api-gateway",
                "entry_file": "src/main.py",
                "port": 8080,
                "description": "API网关 - 统一入口",
            },
            # 监控
            "platform-monitor": {
                "name": "platform-monitor",
                "category": "monitoring",
                "path": "services/core-services/platform-monitor",
                "entry_file": "main.py",
                "port": 9090,
                "description": "平台监控服务",
            },
        }
        self.services_registry = default_services
        print(f"✅ 已创建默认服务注册表 ({len(default_services)} 个服务)")

    def _load_state(self) -> Any:
        """加载平台状态"""
        if self.state_file.exists():
            with open(self.state_file, encoding="utf-8") as f:
                state = json.load(f)
                self.active_pids = state.get("active_pids", {})

    def _save_state(self) -> Any:
        """保存平台状态"""
        state = {
            "last_update": datetime.now().isoformat(),
            "active_pids": self.active_pids,
            "controller": "xiaonuo-pisces-princess-v1",
        }
        self.state_file.parent.mkdir(exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def start_service(self, service_name: str) -> dict[str, Any]:
        """启动单个服务"""
        if service_name not in self.services_registry:
            return {"success": False, "error": f"未知服务: {service_name}", "certainty": 1.0}

        service = self.services_registry[service_name]

        # 检查启动脚本
        start_script = service.get("start_script")
        if start_script:
            script_path = self.project_root / start_script
            if script_path.exists():
                print(f"🔧 启动服务: {service_name}")
                print(f"   脚本: {script_path}")

                try:
                    result = subprocess.run(
                        ["bash", str(script_path), "start"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if result.returncode == 0:
                        return {
                            "success": True,
                            "service": service_name,
                            "message": f"服务 {service_name} 启动成功",
                            "certainty": 0.9,
                        }
                    else:
                        return {
                            "success": False,
                            "service": service_name,
                            "error": result.stderr,
                            "certainty": 1.0,
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "service": service_name,
                        "error": str(e),
                        "certainty": 1.0,
                    }

        # 没有启动脚本,尝试直接启动Python服务
        entry_file = service.get("entry_file")
        if entry_file:
            service_path = self.project_root / service["path"]
            py_file = service_path / entry_file

            if py_file.exists():
                print(f"🐍 启动Python服务: {service_name}")
                print(f"   文件: {py_file}")

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
                    self._save_state()

                    return {
                        "success": True,
                        "service": service_name,
                        "pid": proc.pid,
                        "message": f"服务 {service_name} 已启动 (PID: {proc.pid})",
                        "certainty": 0.8,
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "service": service_name,
                        "error": str(e),
                        "certainty": 1.0,
                    }

        return {
            "success": False,
            "service": service_name,
            "error": "无法找到启动方式",
            "certainty": 1.0,
        }

    def stop_service(self, service_name: str) -> dict[str, Any]:
        """停止单个服务"""
        if service_name in self.active_pids:
            pid = self.active_pids[service_name]
            try:
                os.kill(pid, signal.SIGTERM)
                del self.active_pids[service_name]
                self._save_state()

                return {
                    "success": True,
                    "service": service_name,
                    "message": f"服务 {service_name} 已停止 (PID: {pid})",
                    "certainty": 0.9,
                }
            except Exception as e:
                return {
                    "success": False,
                    "service": service_name,
                    "error": str(e),
                    "certainty": 1.0,
                }

        return {
            "success": True,
            "service": service_name,
            "message": f"服务 {service_name} 未在运行",
            "certainty": 1.0,
        }

    def restart_service(self, service_name: str) -> dict[str, Any]:
        """重启服务"""
        self.stop_service(service_name)
        import time

        time.sleep(2)
        return self.start_service(service_name)

    def get_service_status(self, service_name: str) -> dict[str, Any]:
        """获取服务状态"""
        if service_name not in self.services_registry:
            return {
                "service": service_name,
                "status": "unknown",
                "error": "未知服务",
                "certainty": 1.0,
            }

        service = self.services_registry[service_name]

        # 检查进程
        pid = self.active_pids.get(service_name)
        is_running = False

        if pid:
            try:
                os.kill(pid, 0)  # 检查进程是否存在
                is_running = True
            except OSError:
                is_running = False
                del self.active_pids[service_name]

        status = {
            "service": service_name,
            "category": service.get("category"),
            "description": service.get("description"),
            "running": is_running,
            "pid": pid,
            "port": service.get("port"),
            "path": service.get("path"),
            "certainty": 0.95,
        }

        return status

    def get_all_status(self) -> dict[str, Any]:
        """获取所有服务状态"""
        all_status = {}

        for service_name in self.services_registry:
            all_status[service_name] = self.get_service_status(service_name)

        return {
            "timestamp": datetime.now().isoformat(),
            "controller": "xiaonuo-pisces-princess",
            "total_services": len(self.services_registry),
            "running_services": sum(1 for s in all_status.values() if s.get("running")),
            "services": all_status,
        }

    def start_all(self, category: str | None = None) -> dict[str, Any]:
        """启动所有服务或指定类别的服务"""
        results = {}

        services_to_start = self.services_registry.items()
        if category:
            services_to_start = [
                (k, v) for k, v in self.services_registry.items() if v.get("category") == category
            ]

        for name, _service in services_to_start:
            results[name] = self.start_service(name)

        return {
            "success": True,
            "category": category or "all",
            "started": len([r for r in results.values() if r.get("success")]),
            "failed": len([r for r in results.values() if not r.get("success")]),
            "results": results,
        }

    def stop_all(self) -> dict[str, Any]:
        """停止所有服务"""
        results = {}

        for service_name in list(self.active_pids.keys()):
            results[service_name] = self.stop_service(service_name)

        return {"success": True, "stopped": len(results), "results": results}

    def get_platform_summary(self) -> dict[str, Any]:
        """获取平台摘要"""
        all_status = self.get_all_status()

        # 按类别统计
        categories = {}
        for _name, status in all_status["services"].items():
            cat = status.get("category", "other")
            if cat not in categories:
                categories[cat] = {"total": 0, "running": 0}
            categories[cat]["total"] += 1
            if status.get("running"):
                categories[cat]["running"] += 1

        return {
            "platform": "Athena工作平台",
            "controller": "小诺·双鱼公主 v1.0.0",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_services": all_status["total_services"],
                "running_services": all_status["running_services"],
                "stopped_services": all_status["total_services"] - all_status["running_services"],
            },
            "by_category": categories,
            "certainty": 0.95,
        }


def main() -> None:
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Athena平台控制器 - 小诺")
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "status", "start-all", "stop-all", "summary"],
    )
    parser.add_argument("--service", help="服务名称")
    parser.add_argument("--category", help="服务类别")
    parser.add_argument("--json", action="store_true", help="JSON输出")

    args = parser.parse_args()

    # 初始化控制器
    controller = PlatformController()

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
        result = controller.start_all(args.category)

    elif args.command == "stop-all":
        result = controller.stop_all()

    elif args.command == "summary":
        result = controller.get_platform_summary()

    # 输出结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
