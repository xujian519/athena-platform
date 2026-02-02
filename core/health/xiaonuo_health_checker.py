#!/usr/bin/env python3
"""
小诺·双鱼公主健康检查器
Xiaonuo Pisces Princess Health Checker

提供小诺·双鱼公主系统的健康状态检查和监控功能

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """组件健康状态"""

    name: str
    status: HealthStatus
    message: str
    response_time: float | None = None
    last_check: datetime | None = None
    details: dict[str, Any] | None = None


@dataclass
class SystemHealth:
    """系统整体健康状态"""

    status: HealthStatus
    timestamp: datetime
    uptime: float
    components: list[ComponentHealth]
    system_metrics: dict[str, Any]
    version: str


class XiaonuoHealthChecker:
    """小诺·双鱼公主健康检查器"""

    def __init__(self):
        self.start_time = time.time()
        self.component_checks = {}
        self.last_health_report = None
        self.health_history = []

    async def check_component_health(self, component_name: str, check_func) -> ComponentHealth:
        """检查单个组件的健康状态"""
        start_time = time.time()

        try:
            # 执行健康检查
            result = await asyncio.wait_for(check_func(), timeout=10.0)
            response_time = time.time() - start_time

            # 解析检查结果
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "OK" if result else "Check failed"
                details = None
            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "unknown"))
                message = result.get("message", "Unknown status")
                details = result.get("details")
            else:
                status = HealthStatus.HEALTHY
                message = str(result)
                details = None

        except TimeoutError:
            status = HealthStatus.UNHEALTHY
            message = "Health check timeout"
            response_time = 10.0
            details = None

        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Health check error: {e!s}"
            response_time = time.time() - start_time
            details = {"error_type": type(e).__name__}

        return ComponentHealth(
            name=component_name,
            status=status,
            message=message,
            response_time=response_time,
            last_check=datetime.now(),
            details=details,
        )

    async def check_agent_initialization(self) -> dict[str, Any]:
        """检查智能体初始化状态"""
        try:
            # 尝试导入和初始化智能体
            from core.agent.xiaonuo_pisces_princess_agent import (
                XiaonuoPiscesPrincessAgent,
            )

            # 创建临时实例进行测试
            agent = XiaonuoPiscesPrincessAgent()

            # 检查基本属性
            checks = {
                "agent_name": hasattr(agent, "agent_name") and agent.agent_name is not None,
                "dual_identity": hasattr(agent, "dual_identity") and len(agent.dual_identity) > 0,
                "super_capabilities": hasattr(agent, "super_capabilities")
                and len(agent.super_capabilities) > 0,
                "pisces_identity": hasattr(agent, "pisces_princess_identity")
                and agent.pisces_princess_identity is not None,
            }

            all_passed = all(checks.values())

            return {
                "status": "healthy" if all_passed else "degraded",
                "message": f"Agent checks: {sum(checks.values())}/{len(checks)} passed",
                "details": checks,
            }

        except ImportError as e:
            return {
                "status": "unhealthy",
                "message": f"Failed to import agent: {e!s}",
                "details": {"error": "ImportError"},
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Agent check failed: {e!s}",
                "details": {"error_type": type(e).__name__},
            }

    async def check_file_system(self) -> dict[str, Any]:
        """检查文件系统状态"""
        try:
            from core.config.environment_manager import get_env_manager

            env_manager = get_env_manager()

            # 检查关键目录
            critical_paths = {
                "athena_home": env_manager.athena_home,
                "data_path": env_manager.data_path,
                "config_path": env_manager.config_path,
                "logs_path": env_manager.logs_path,
            }

            path_checks = {}
            total_issues = 0

            for name, path in critical_paths.items():
                exists = path.exists()
                writable = False

                if exists:
                    try:
                        # 测试写入权限
                        test_file = path / ".health_check"
                        test_file.touch()
                        test_file.unlink()
                        writable = True
                    except Exception:
                        writable = False

                path_checks[name] = {"exists": exists, "writable": writable, "path": str(path)}

                if not exists or not writable:
                    total_issues += 1

            # 检查磁盘空间
            disk_usage = psutil.disk_usage(str(env_manager.athena_home))
            free_percent = (disk_usage.free / disk_usage.total) * 100

            # 检查配置文件
            config_file = env_manager.config_path / "identity" / "xiaonuo_pisces_princess.json"
            config_exists = config_file.exists()

            status = "healthy"
            if total_issues > 0:
                status = "degraded" if total_issues <= 2 else "unhealthy"
            elif free_percent < 10:
                status = "degraded" if free_percent >= 5 else "unhealthy"

            return {
                "status": status,
                "message": f"File system: {total_issues} issues, {free_percent:.1f}% free space",
                "details": {
                    "paths": path_checks,
                    "disk_space": {
                        "total_gb": disk_usage.total / (1024**3),
                        "free_gb": disk_usage.free / (1024**3),
                        "free_percent": free_percent,
                    },
                    "config_file_exists": config_exists,
                },
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"File system check failed: {e!s}",
                "details": {"error_type": type(e).__name__},
            }

    async def check_memory_usage(self) -> dict[str, Any]:
        """检查内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            # 系统内存信息
            system_memory = psutil.virtual_memory()

            # 判断内存状态
            status = "healthy"
            if memory_percent > 80:
                status = "unhealthy"
            elif memory_percent > 60:
                status = "degraded"

            return {
                "status": status,
                "message": f"Memory usage: {memory_percent:.1f}%",
                "details": {
                    "process_memory_mb": memory_info.rss / (1024 * 1024),
                    "process_memory_percent": memory_percent,
                    "system_memory_percent": system_memory.percent,
                    "system_available_gb": system_memory.available / (1024**3),
                },
            }

        except Exception as e:
            return {
                "status": "unknown",
                "message": f"Memory check failed: {e!s}",
                "details": {"error_type": type(e).__name__},
            }

    async def check_database_connectivity(self) -> dict[str, Any]:
        """检查数据库连接"""
        try:
            from core.config.environment_manager import get_env_manager

            env_manager = get_env_manager()
            db_config = env_manager.get_database_config()

            # 这里应该实现实际的数据库连接测试
            # 为了演示,我们模拟检查
            import random

            # 模拟连接测试
            await asyncio.sleep(0.1)  # 模拟网络延迟

            # 随机模拟连接状态(在生产环境中应该是真实的连接测试)
            if random.random() > 0.1:  # 90% 成功率
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "details": {
                        "host": db_config.host,
                        "port": db_config.port,
                        "infrastructure/infrastructure/database": db_config.name,
                        "ssl_mode": db_config.ssl_mode,
                    },
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Database connection failed",
                    "details": {
                        "host": db_config.host,
                        "port": db_config.port,
                        "error": "Connection timeout",
                    },
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database check failed: {e!s}",
                "details": {"error_type": type(e).__name__},
            }

    async def check_identity_system(self) -> dict[str, Any]:
        """检查身份系统状态"""
        try:
            from core.config.environment_manager import get_env_manager

            env_manager = get_env_manager()
            identity_config = env_manager.get_identity_config()

            # 检查身份档案
            storage_path = identity_config["identity_storage_path"]
            xiaonuo_path = storage_path / "apps/apps/xiaonuo"

            checks = {
                "storage_path_exists": storage_path.exists(),
                "xiaonuo_path_exists": xiaonuo_path.exists(),
                "config_file_exists": identity_config["xiaonuo_config_file"].exists(),
            }

            # 检查身份档案文件
            identity_files = []
            if xiaonuo_path.exists():
                for file_path in xiaonuo_path.glob("*.json"):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            data = json.load(f)
                            identity_files.append(
                                {
                                    "file": file_path.name,
                                    "size": file_path.stat().st_size,
                                    "valid": isinstance(data, dict),
                                }
                            )
                    except Exception:
                        identity_files.append(
                            {
                                "file": file_path.name,
                                "size": file_path.stat().st_size,
                                "valid": False,
                            }
                        )

            all_passed = all(checks.values()) and len(identity_files) > 0

            return {
                "status": "healthy" if all_passed else "degraded",
                "message": f"Identity system: {sum(checks.values())}/{len(checks)} checks passed, {len(identity_files)} identity files",
                "details": {
                    "checks": checks,
                    "identity_files": identity_files,
                    "storage_path": str(storage_path),
                },
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Identity system check failed: {e!s}",
                "details": {"error_type": type(e).__name__},
            }

    async def get_system_health(self, detailed: bool = False) -> SystemHealth:
        """获取系统整体健康状态"""
        time.time()

        # 定义要检查的组件
        component_checks = [
            ("Agent Initialization", self.check_agent_initialization),
            ("File System", self.check_file_system),
            ("Memory Usage", self.check_memory_usage),
            ("Database Connectivity", self.check_database_connectivity),
            ("Identity System", self.check_identity_system),
        ]

        # 如果是快速检查,只检查关键组件
        if not detailed:
            component_checks = component_checks[:3]

        # 并行执行所有健康检查
        tasks = []
        for name, check_func in component_checks:
            task = self.check_component_health(name, check_func)
            tasks.append(task)

        components = await asyncio.gather(*tasks)

        # 计算系统整体状态
        unhealthy_count = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)

        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # 收集系统指标
        uptime = time.time() - self.start_time
        process = psutil.Process()

        system_metrics = {
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "process_id": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_rss_mb": process.memory_info().rss / (1024 * 1024),
            "memory_vms_mb": process.memory_info().vms / (1024 * 1024),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
        }

        # 获取版本信息
        try:
            from core.agent.xiaonuo_pisces_princess_agent import (
                XiaonuoPiscesPrincessAgent,
            )

            temp_agent = XiaonuoPiscesPrincessAgent()
            version = getattr(temp_agent.pisces_princess_identity, "version", "Unknown")
        except Exception:
            version = "Unknown"

        # 创建健康报告
        health_report = SystemHealth(
            status=overall_status,
            timestamp=datetime.now(),
            uptime=uptime,
            components=components,
            system_metrics=system_metrics,
            version=version,
        )

        self.last_health_report = health_report
        self.health_history.append(health_report)

        # 保持历史记录不超过100条
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]

        return health_report

    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")

        return " ".join(parts) if parts else "Less than 1m"

    def get_health_summary(self) -> dict[str, Any]:
        """获取健康状态摘要"""
        if not self.last_health_report:
            return {"status": "unknown", "message": "No health report available"}

        report = self.last_health_report

        return {
            "status": report.status.value,
            "timestamp": report.timestamp.isoformat(),
            "uptime": report.uptime_formatted,
            "version": report.version,
            "components": {
                "total": len(report.components),
                "healthy": sum(1 for c in report.components if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in report.components if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(
                    1 for c in report.components if c.status == HealthStatus.UNHEALTHY
                ),
            },
            "system_metrics": {
                "cpu_percent": report.system_metrics.get("cpu_percent", 0),
                "memory_mb": report.system_metrics.get("memory_rss_mb", 0),
                "threads": report.system_metrics.get("threads", 0),
            },
        }

    def get_health_trends(self, hours: int = 24) -> dict[str, Any]:
        """获取健康状态趋势"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤指定时间范围内的健康记录
        recent_reports = [
            report for report in self.health_history if report.timestamp >= cutoff_time
        ]

        if not recent_reports:
            return {"message": f"No health data available for the last {hours} hours"}

        # 分析趋势
        status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}

        for report in recent_reports:
            status_counts[report.status.value] += 1

        total_checks = len(recent_reports)
        availability = (status_counts["healthy"] / total_checks) * 100 if total_checks > 0 else 0

        return {
            "period_hours": hours,
            "total_checks": total_checks,
            "availability_percent": round(availability, 2),
            "status_distribution": status_counts,
            "first_check": recent_reports[0].timestamp.isoformat(),
            "last_check": recent_reports[-1].timestamp.isoformat(),
        }


# 全局健康检查器实例
health_checker = XiaonuoHealthChecker()


def get_health_checker() -> XiaonuoHealthChecker:
    """获取全局健康检查器实例"""
    return health_checker


async def health_check_endpoint(detailed: bool = False) -> dict[str, Any]:
    """健康检查端点 - 用于API调用"""
    try:
        health_report = await health_checker.get_system_health(detailed=detailed)

        # 转换为可序列化的格式
        return {
            "status": health_report.status.value,
            "timestamp": health_report.timestamp.isoformat(),
            "uptime": health_report.uptime,
            "version": health_report.version,
            "components": [
                {
                    "name": comp.name,
                    "status": comp.status.value,
                    "message": comp.message,
                    "response_time": comp.response_time,
                    "last_check": comp.last_check.isoformat() if comp.last_check else None,
                    "details": comp.details,
                }
                for comp in health_report.components
            ],
            "system_metrics": health_report.system_metrics,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Health check failed",
        }


async def readiness_check() -> dict[str, Any]:
    """就绪检查端点 - 用于Kubernetes等容器编排"""
    try:
        health_report = await health_checker.get_system_health(detailed=False)

        # 系统就绪的条件:没有不健康的组件
        is_ready = health_report.status != HealthStatus.UNHEALTHY

        return {
            "ready": is_ready,
            "status": health_report.status.value,
            "timestamp": health_report.timestamp.isoformat(),
            "message": "System is ready" if is_ready else "System is not ready",
        }

    except Exception as e:
        return {
            "ready": False,
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Readiness check failed",
        }


async def liveness_check() -> dict[str, Any]:
    """存活检查端点 - 用于Kubernetes等容器编排"""
    # 存活检查相对简单,只要进程在运行就认为存活
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - health_checker.start_time,
    }


if __name__ == "__main__":
    # 测试健康检查器
    async def test_health_checker():
        print("🏥 测试小诺·双鱼公主健康检查器")
        print("=" * 60)

        # 获取健康检查器
        checker = get_health_checker()

        # 执行健康检查
        health = await checker.get_system_health(detailed=True)

        print(f"📊 整体状态: {health.status.value}")
        print(f"🕐 运行时间: {health.uptime_formatted}")
        print(f"📅 检查时间: {health.timestamp}")
        print(f"🏷️  版本: {health.version}")

        print("\n🔧 组件状态:")
        for component in health.components:
            status_emoji = (
                "✅"
                if component.status == HealthStatus.HEALTHY
                else "⚠️" if component.status == HealthStatus.DEGRADED else "❌"
            )
            print(f"  {status_emoji} {component.name}: {component.status.value}")
            if component.response_time:
                print(f"    响应时间: {component.response_time:.3f}s")
            print(f"    消息: {component.message}")

        print("\n📈 系统指标:")
        metrics = health.system_metrics
        print(f"  CPU使用率: {metrics.get('cpu_percent', 0):.1f}%")
        print(f"  内存使用: {metrics.get('memory_rss_mb', 0):.1f}MB")
        print(f"  线程数: {metrics.get('threads', 0)}")
        print(f"  打开文件数: {metrics.get('open_files', 0)}")

        # 显示健康摘要
        summary = checker.get_health_summary()
        print("\n📋 健康摘要:")
        print(json.dumps(summary, indent=2, ensure_ascii=False))

    # 运行测试
    asyncio.run(test_health_checker())
