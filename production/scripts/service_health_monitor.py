#!/usr/bin/env python3
"""
小诺服务健康监控系统
Xiaonuo Service Health Monitoring System
"""

from __future__ import annotations
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
import requests

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

class ServiceHealthMonitor:
    """服务健康监控器"""

    def __init__(self):
        self.session_id = f"health_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.monitoring_interval = 30  # 30秒检查一次
        self.services = {
            "xiaonuo_service": {"name": "小诺主服务", "pid_file": "xiaonuo.pid"},
            "expert_rule_engine": {"name": "专家规则推理引擎", "pid_file": "expert_rule_engine.pid"},
            "patent_rule_chain": {"name": "专利规则链引擎", "pid_file": "patent_rule_chain.pid"},
            "prior_art_analyzer": {"name": "现有技术分析器", "pid_file": "prior_art_analyzer.pid"},
            "llm_enhanced_judgment": {"name": "LLM增强判断系统", "pid_file": "llm_enhanced_judgment.pid"}
        }

        self.logs_dir = project_root / "production" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # 健康状态历史
        self.health_history = []

    def print_pink(self, message: str) -> Any:
        """打印粉色消息"""
        print(f"💖 {message}")

    def print_success(self, message: str) -> Any:
        """打印成功消息"""
        print(f"✅ {message}")

    def print_warning(self, message: str) -> Any:
        """打印警告消息"""
        print(f"⚠️  {message}")

    def print_error(self, message: str) -> Any:
        """打印错误消息"""
        print(f"❌ {message}")

    async def check_service_health(self, service_key: str) -> dict[str, Any]:
        """检查单个服务健康状态"""
        service_info = self.services[service_key]
        pid_file = self.logs_dir / service_info["pid_file"]

        health_status = {
            "service_key": service_key,
            "service_name": service_info["name"],
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "pid": None,
            "cpu_percent": 0,
            "memory_mb": 0,
            "uptime": 0,
            "last_check": datetime.now().isoformat(),
            "error_message": ""
        }

        try:
            if pid_file.exists():
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                    health_status["pid"] = pid

                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    health_status["status"] = "running"
                    health_status["cpu_percent"] = process.cpu_percent()
                    health_status["memory_mb"] = process.memory_info().rss / 1024 / 1024
                    health_status["uptime"] = time.time() - process.create_time()
                else:
                    health_status["status"] = "stopped"
                    health_status["error_message"] = "进程不存在"
            else:
                health_status["status"] = "no_pid_file"
                health_status["error_message"] = "PID文件不存在"

        except Exception as e:
            health_status["status"] = "error"
            health_status["error_message"] = str(e)

        return health_status

    async def check_database_health(self) -> dict[str, Any]:
        """检查数据库健康状态"""
        db_health = {
            "timestamp": datetime.now().isoformat(),
            "postgresql": {"status": "unknown", "response_time": 0},
            "redis": {"status": "unknown", "response_time": 0},
            "elasticsearch": {"status": "unknown", "response_time": 0},
            "qdrant": {"status": "unknown", "response_time": 0}
        }

        # 检查PostgreSQL (安全方式)
        try:
            start_time = time.time()
            result = subprocess.run(
                ['pg_isready', '-q'],
                capture_output=True,
                timeout=5
            )
            response_time = time.time() - start_time
            db_health["postgresql"]["response_time"] = response_time
            db_health["postgresql"]["status"] = "healthy" if result.returncode == 0 else "unhealthy"
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            db_health["postgresql"]["status"] = f"error: {e}"

        # 检查Redis (安全方式)
        try:
            start_time = time.time()
            result = subprocess.run(
                ['redis-cli', 'ping'],
                capture_output=True,
                timeout=5
            )
            response_time = time.time() - start_time
            db_health["redis"]["response_time"] = response_time
            db_health["redis"]["status"] = "healthy" if result.returncode == 0 and b'PONG' in result.stdout else "unhealthy"
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            db_health["redis"]["status"] = f"error: {e}"

        # 检查Elasticsearch
        try:
            start_time = time.time()
            response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
            response_time = time.time() - start_time
            db_health["elasticsearch"]["response_time"] = response_time
            if response.status_code == 200:
                db_health["elasticsearch"]["status"] = "healthy"
            else:
                db_health["elasticsearch"]["status"] = "unhealthy"
        except Exception as e:
            db_health["elasticsearch"]["status"] = f"error: {e}"

        # 检查Qdrant
        try:
            start_time = time.time()
            response = requests.get("http://localhost:6333/health", timeout=5)
            response_time = time.time() - start_time
            db_health["qdrant"]["response_time"] = response_time
            if response.status_code == 200:
                db_health["qdrant"]["status"] = "healthy"
            else:
                db_health["qdrant"]["status"] = "unhealthy"
        except Exception as e:
            db_health["qdrant"]["status"] = f"error: {e}"

        return db_health

    async def get_system_metrics(self) -> dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = os.getloadavg()

            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / 1024 / 1024 / 1024,
                "memory_total_gb": memory.total / 1024 / 1024 / 1024,
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / 1024 / 1024 / 1024,
                "disk_total_gb": disk.total / 1024 / 1024 / 1024,
                "load_average": {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2]
                }
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def save_health_report(self, health_data: dict[str, Any]):
        """保存健康报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.logs_dir / f"health_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(health_data, f, indent=2, ensure_ascii=False)

        # 保持最新的报告
        latest_report = self.logs_dir / "latest_health_report.json"
        with open(latest_report, 'w', encoding='utf-8') as f:
            json.dump(health_data, f, indent=2, ensure_ascii=False)

    async def auto_heal_service(self, service_key: str, health_status: dict[str, Any]):
        """自动修复服务"""
        if health_status["status"] in ["stopped", "error", "no_pid_file"]:
            self.print_warning(f"🔧 尝试自动修复服务: {health_status['service_name']}")

            # 这里可以添加自动重启逻辑
            # 目前只是记录，避免自动重启造成的问题
            self.print_info(f"📋 服务 {health_status['service_name']} 需要手动检查")

            # 记录到修复日志
            heal_log = {
                "timestamp": datetime.now().isoformat(),
                "service": service_key,
                "service_name": health_status["service_name"],
                "status": health_status["status"],
                "error": health_status["error_message"],
                "action": "manual_intervention_required"
            }

            heal_log_file = self.logs_dir / "auto_heal.log"
            with open(heal_log_file, 'a', encoding='utf-8') as f:
                json.dump(heal_log, f, ensure_ascii=False)
                f.write('\n')

    def print_info(self, message: str) -> Any:
        """打印信息消息"""
        print(f"ℹ️ {message}")

    async def run_health_check(self):
        """运行健康检查"""
        print("🏥 小诺服务健康监控系统启动")
        print(f"📅 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  监控间隔: {self.monitoring_interval}秒")
        print("=" * 60)

        while True:
            try:
                # 收集所有健康数据
                health_data = {
                    "session_id": self.session_id,
                    "check_time": datetime.now().isoformat(),
                    "services": {},
                    "databases": {},
                    "system_metrics": {},
                    "overall_health": {
                        "total_services": len(self.services),
                        "healthy_services": 0,
                        "unhealthy_services": 0,
                        "overall_score": 0
                    }
                }

                # 检查所有服务
                healthy_count = 0
                for service_key in self.services:
                    service_health = await self.check_service_health(service_key)
                    health_data["services"][service_key] = service_health

                    if service_health["status"] == "running":
                        healthy_count += 1
                        self.print_success(f"✅ {service_health['service_name']} - 运行正常")
                    else:
                        self.print_error(f"❌ {service_health['service_name']} - {service_health['status']}")

                        # 尝试自动修复
                        await self.auto_heal_service(service_key, service_health)

                # 检查数据库
                print("\n📊 数据库状态:")
                db_health = await self.check_database_health()
                health_data["databases"] = db_health

                for db_name, db_info in db_health.items():
                    if db_name == "timestamp":
                        continue
                    if db_info["status"] == "healthy":
                        self.print_success(f"✅ {db_name} - 正常 ({db_info['response_time']:.3f}s)")
                    else:
                        self.print_warning(f"⚠️  {db_name} - {db_info['status']}")

                # 获取系统指标
                print("\n💻 系统指标:")
                system_metrics = await self.get_system_metrics()
                health_data["system_metrics"] = system_metrics

                if "error" not in system_metrics:
                    self.print_info(f"🔥 CPU: {system_metrics['cpu_percent']:.1f}%")
                    self.print_info(f"💾 内存: {system_metrics['memory_percent']:.1f}% ({system_metrics['memory_used_gb']:.1f}GB)")
                    self.print_info(f"💿 磁盘: {system_metrics['disk_percent']:.1f}%")
                    self.print_info(f"⚖️  负载: {system_metrics['load_average']['1min']:.2f}")

                # 计算整体健康分数
                health_data["overall_health"]["healthy_services"] = healthy_count
                health_data["overall_health"]["unhealthy_services"] = len(self.services) - healthy_count
                health_data["overall_health"]["overall_score"] = (healthy_count / len(self.services)) * 100

                # 保存健康报告
                await self.save_health_report(health_data)

                # 显示整体健康状态
                overall_score = health_data["overall_health"]["overall_score"]
                print(f"\n🎯 整体健康分数: {overall_score:.1f}%")

                if overall_score >= 90:
                    self.print_pink("🎉 系统状态优秀！")
                elif overall_score >= 75:
                    self.print_success("👍 系统状态良好")
                elif overall_score >= 50:
                    self.print_warning("⚠️ 系统状态一般，需要关注")
                else:
                    self.print_error("❌ 系统状态异常，需要立即处理")

                print("\n" + "=" * 60)
                print(f"⏰ 下次检查时间: {(datetime.now() + datetime.timedelta(seconds=self.monitoring_interval)).strftime('%H:%M:%S')}")

                # 等待下一次检查
                await asyncio.sleep(self.monitoring_interval)

            except KeyboardInterrupt:
                self.print_info("\n🛑 健康监控系统停止")
                break
            except Exception as e:
                self.print_error(f"❌ 监控系统错误: {e}")
                await asyncio.sleep(5)

async def main():
    """主函数"""
    print("🌸🐟 小诺服务健康监控系统")
    print("=" * 60)

    monitor = ServiceHealthMonitor()
    await monitor.run_health_check()

if __name__ == "__main__":
    asyncio.run(main())
