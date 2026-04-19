#!/usr/bin/env python3
"""
生产环境监控脚本
Production Monitoring Script

作者: Athena AI系统
创建时间: 2026-01-27
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import psutil

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.execution.execution_engine.engine import ExecutionEngine


class ProductionMonitor:
    """生产环境监控器"""

    def __init__(self):
        self.process = psutil.Process()

    def get_system_metrics(self):
        """获取系统指标"""
        cpu_percent = self.process.cpu_percent(interval=1)
        memory_info = self.process.memory_info()

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": self.process.memory_percent(),
            "num_threads": self.process.num_threads(),
            "open_files": len(self.process.open_files()),
            "connections": len(self.process.connections())
        }

    def check_service_health(self):
        """检查服务健康状态"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }

        # 检查执行引擎
        pid_file = Path("production/pids/execution_engine.pid")
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            if psutil.pid_exists(pid):
                health_status["services"]["execution_engine"] = {
                    "status": "running",
                    "pid": pid
                }
            else:
                health_status["services"]["execution_engine"] = {
                    "status": "stopped",
                    "pid": pid
                }
        else:
            health_status["services"]["execution_engine"] = {
                "status": "not_initialized"
            }

        return health_status

    async def check_execution_engine_health(self):
        """检查执行引擎内部健康状态"""
        try:
            engine = ExecutionEngine(agent_id="health_check")
            await engine.initialize()
            health = await engine.health_check()
            await engine.shutdown()

            return {
                "status": health.value,
                "details": health.details if hasattr(health, 'details') else {}
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_log_stats(self):
        """获取日志统计"""
        log_files = {
            "execution_engine": Path("production/logs/execution_engine.log"),
            "cap02_data_prep": Path("production/logs/cap02_data_prep.log")
        }

        stats = {}
        for name, path in log_files.items():
            if path.exists():
                stat = path.stat()
                stats[name] = {
                    "size_mb": stat.st_size / 1024 / 1024,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                stats[name] = {"status": "not_found"}

        return stats

    def print_dashboard(self):
        """打印监控仪表板"""
        print("\n" + "=" * 80)
        print("Athena平台 - 生产环境监控仪表板")
        print("=" * 80)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

        # 系统指标
        system_metrics = self.get_system_metrics()
        print("📊 系统指标:")
        print(f"  CPU使用率: {system_metrics['cpu_percent']:.1f}%")
        print(f"  内存使用: {system_metrics['memory_mb']:.1f}MB ({system_metrics['memory_percent']:.1f}%)")
        print(f"  线程数: {system_metrics['num_threads']}")
        print(f"  打开文件数: {system_metrics['open_files']}")
        print(f"  网络连接数: {system_metrics['connections']}")
        print("")

        # 服务健康状态
        health = self.check_service_health()
        print("🔍 服务状态:")
        for service, status in health["services"].items():
            status_icon = "✅" if status["status"] == "running" else "❌"
            print(f"  {status_icon} {service}: {status['status']}")
            if "pid" in status:
                print(f"     PID: {status['pid']}")
        print("")

        # 日志统计
        log_stats = self.get_log_stats()
        print("📝 日志文件:")
        for name, stats in log_stats.items():
            if "size_mb" in stats:
                print(f"  {name}: {stats['size_mb']:.2f}MB (更新于 {stats['modified']})")
            else:
                print(f"  {name}: {stats['status']}")
        print("")

        # 输出目录
        output_dir = Path("production/output")
        if output_dir.exists():
            files = list(output_dir.glob("*"))
            print(f"📂 输出文件: {len(files)}个")
            if files:
                total_size = sum(f.stat().st_size for f in files) / 1024 / 1024
                print(f"  总大小: {total_size:.1f}MB")
        print("")

        print("=" * 80)


def main():
    """主函数"""
    monitor = ProductionMonitor()

    # 打印仪表板
    monitor.print_dashboard()

    # 检查执行引擎内部健康
    print("🔬 执行引擎深度健康检查...")
    try:
        engine_health = asyncio.run(monitor.check_execution_engine_health())
        print(f"  状态: {engine_health['status']}")
        if "details" in engine_health and engine_health["details"]:
            print(f"  详情: {json.dumps(engine_health['details'], indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"  检查失败: {e}")

    print("")


if __name__ == "__main__":
    main()
