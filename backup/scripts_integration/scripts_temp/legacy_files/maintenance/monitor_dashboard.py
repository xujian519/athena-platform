#!/usr/bin/env python3
"""
Athena平台监控仪表板
Monitoring Dashboard for Athena Platform
提供实时的服务状态监控和性能指标展示
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# 添加父目录到Python路径
sys.path.append(str(Path(__file__).parent))

try:
    from deployment_manager import DeploymentManager
except ImportError:
    print("请确保deployment_manager.py在当前目录")
    sys.exit(1)

import psutil
import httpx
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.live import Live
from rich.align import Align
from rich.text import Text

class MonitoringDashboard:
    """监控仪表板"""

    def __init__(self):
        self.console = Console()
        self.deployment_manager = DeploymentManager()
        self.metrics_history = []
        self.start_time = datetime.now()

    def create_service_table(self) -> Table:
        """创建服务状态表格"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("服务名称", style="cyan", width=20)
        table.add_column("状态", style="green", width=10)
        table.add_column("端口", style="blue", width=6)
        table.add_column("PID", style="yellow", width=8)
        table.add_column("运行时间", style="white", width=12)
        table.add_column("CPU%", style="red", width=8)
        table.add_column("内存%", style="red", width=8)

        status = self.deployment_manager.get_service_status()

        for service_name, info in status.items():
            if "error" not in info:
                # 获取进程资源使用情况
                cpu_percent = "N/A"
                memory_percent = "N/A"

                if info.get("pid"):
                    try:
                        process = psutil.Process(info["pid"])
                        cpu_percent = f"{process.cpu_percent():.1f}"
                        memory_info = process.memory_info()
                        memory_percent = f"{process.memory_percent():.1f}"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # 状态图标
                status_text = info["status"]
                if info["status"] == "running":
                    status_text = "✅ 运行中"
                elif info["status"] == "stopped":
                    status_text = "⏹️ 已停止"
                elif info["status"] == "starting":
                    status_text = "🔄 启动中"
                else:
                    status_text = f"❌ {info['status']}"

                # 运行时间
                uptime = "N/A"
                if info.get("start_time"):
                    start_dt = datetime.fromisoformat(info["start_time"])
                    uptime = str(datetime.now() - start_dt).split(".")[0]

                table.add_row(
                    service_name,
                    status_text,
                    str(info.get("port", "N/A")),
                    str(info.get("pid", "N/A")),
                    uptime,
                    cpu_percent,
                    memory_percent
                )

        return table

    def create_system_info(self) -> Panel:
        """创建系统信息面板"""
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # 内存信息
        memory = psutil.virtual_memory()

        # 磁盘信息
        disk = psutil.disk_usage('/')

        # 系统负载
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

        info_text = f"""
[bold cyan]系统信息[/bold cyan]

CPU使用率: {cpu_percent:.1f}%
CPU核心数: {cpu_count}
CPU频率: {cpu_freq.current:.0f} MHz

内存使用: {memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB ({memory.percent:.1f}%)

磁盘使用: {disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB ({disk.percent:.1f}%)

系统负载: {load_avg[0]:.2f} (1分钟), {load_avg[1]:.2f} (5分钟), {load_avg[2]:.2f} (15分钟)

仪表板运行时间: {str(datetime.now() - self.start_time).split('.')[0]}
        """

        return Panel(info_text.strip(), title="系统信息", border_style="blue")

    def create_health_panel(self) -> Panel:
        """创建健康检查面板"""
        health_status = self.deployment_manager.health_check()

        healthy_count = sum(1 for s in health_status.values() if s.get("status") == "healthy")
        total_count = len(health_status)

        health_text = f"""
[bold green]健康服务: {healthy_count}/{total_count}[/bold green]

"""
        for name, info in health_status.items():
            status = info.get("status", "unknown")
            if status == "healthy":
                status_text = "[green]✅ 健康[/green]"
            elif status == "unreachable":
                status_text = "[red]❌ 无法访问[/red]"
            elif status == "running":
                status_text = "[yellow]🔄 运行中[/yellow]"
            else:
                status_text = f"[red]❌ {status}[/red]"

            health_text += f"{name}: {status_text}\n"

        return Panel(health_text.strip(), title="服务健康状态", border_style="green")

    def create_metrics_panel(self) -> Panel:
        """创建性能指标面板"""
        # 收集指标
        current_metrics = {
            "timestamp": datetime.now(),
            "services": {}
        }

        status = self.deployment_manager.get_service_status()
        running_services = 0
        total_memory = 0

        for name, info in status.items():
            if info.get("status") == "running":
                running_services += 1
                if info.get("pid"):
                    try:
                        process = psutil.Process(info["pid"])
                        total_memory += process.memory_info().rss
                    except:
                        pass

        current_metrics["services"]["running"] = running_services
        current_metrics["services"]["total"] = len(status)
        current_metrics["memory_usage"] = total_memory / 1024**2  # MB

        # 保存历史（保留最近100个数据点）
        self.metrics_history.append(current_metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

        # 计算趋势
        metrics_text = f"""
[bold cyan]性能指标[/bold cyan]

运行服务数: {running_services}/{len(status)}
服务运行率: {running_services/len(status)*100:.1f}%

服务总内存: {total_memory/1024:.1f} GB

历史数据点: {len(self.metrics_history)}
        """

        # 如果有历史数据，显示趋势
        if len(self.metrics_history) > 1:
            last_metrics = self.metrics_history[-2]
            memory_trend = current_metrics["memory_usage"] - last_metrics["memory_usage"]
            memory_trend_text = f"{memory_trend:+.1f} MB"
            if memory_trend > 0:
                memory_trend_text = f"[red]{memory_trend_text}[/red]"
            elif memory_trend < 0:
                memory_trend_text = f"[green]{memory_trend_text}[/green]"

            metrics_text += f"\n内存趋势: {memory_trend_text}"

        return Panel(metrics_text.strip(), title="性能指标", border_style="cyan")

    def create_layout(self) -> Layout:
        """创建仪表板布局"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )

        layout["left"].split_column(
            Layout(name="services", size=20),
            Layout(name="system", size=12)
        )

        layout["right"].split_column(
            Layout(name="health", size=12),
            Layout(name="metrics", size=12)
        )

        # 填充内容
        layout["header"].update(
            Panel(
                Align.center(
                    Text("Athena平台监控仪表板", style="bold blue")
                ),
                style="bold white on blue"
            )
        )

        layout["services"].update(
            Panel(
                self.create_service_table(),
                title="服务状态",
                border_style="yellow"
            )
        )

        layout["system"].update(self.create_system_info())
        layout["health"].update(self.create_health_panel())
        layout["metrics"].update(self.create_metrics_panel())

        layout["footer"].update(
            Panel(
                Align.center(
                    Text(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
                ),
                style="dim"
            )
        )

        return layout

    def run(self, refresh_interval: int = 5):
        """运行监控仪表板"""
        self.console.clear()

        try:
            with Live(self.create_layout(), refresh_per_second=1//refresh_interval) as live:
                while True:
                    live.update(self.create_layout())
                    time.sleep(refresh_interval)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]监控仪表板已停止[/yellow]")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Athena平台监控仪表板")
    parser.add_argument("--refresh", "-r", type=int, default=5, help="刷新间隔（秒）")

    args = parser.parse_args()

    # 创建并运行监控仪表板
    dashboard = MonitoringDashboard()
    dashboard.run(refresh_interval=args.refresh)

if __name__ == "__main__":
    main()