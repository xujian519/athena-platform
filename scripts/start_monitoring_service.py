#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺监控服务启动脚本
Xiaonuo Monitoring Service Startup Script

启动小诺的监控和指标收集服务

作者: Athena团队
创建时间: 2026-02-09
版本: v1.0.0
"""

import os
import sys
import time
import signal
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from prometheus_client import start_http_server, REGISTRY
from prometheus_client.core import CollectorRegistry

# 导入指标收集器
try:
    from production.monitoring.xiaonuo_metrics import XiaonuoMetricsCollector
except ImportError:
    print("警告: 指标收集器模块未找到，使用基础指标")
    XiaonuoMetricsCollector = None


class MonitoringService:
    """监控服务"""

    def __init__(self, metrics_port: int = 9095):
        """
        初始化监控服务

        参数:
            metrics_port: Prometheus指标端口
        """
        self.metrics_port = metrics_port
        self.running = False

        # 创建指标收集器
        if XiaonuoMetricsCollector:
            self.metrics_collector = XiaonuoMetricsCollector(enabled=True)
        else:
            self.metrics_collector = None

        # 健康检查端点
        self.health_check_url = "http://127.0.0.1:8099/health"

    async def start(self):
        """启动监控服务"""
        print("📊 启动小诺监控服务...")

        # 启动Prometheus HTTP服务器
        print(f"   启动Prometheus指标服务器 (端口: {self.metrics_port})...")
        start_http_server(self.metrics_port)
        print(f"   ✓ 指标端点: http://127.0.0.1:{self.metrics_port}/metrics")

        # 初始化指标
        if self.metrics_collector:
            print("   ✓ 指标收集器已启用")
        else:
            print("   ⚠ 指标收集器未启用（使用基础指标）")

        self.running = True
        print("\n✅ 监控服务已启动")

        # 开始监控循环
        await self._monitoring_loop()

    async def _monitoring_loop(self):
        """监控循环"""
        print("\n🔄 开始监控循环...")
        print("   按 Ctrl+C 停止\n")

        client = httpx.AsyncClient()

        try:
            iteration = 0
            while self.running:
                iteration += 1

                # 每10秒执行一次健康检查
                try:
                    response = await client.get(self.health_check_url, timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()

                        # 记录指标
                        if self.metrics_collector:
                            self.metrics_collector.update_uptime()
                            self.metrics_collector.update_active_connections(
                                data.get('components', {}).get('api', {}).get('active_connections', 0)
                            )

                        if iteration % 6 == 0:  # 每分钟打印一次状态
                            self._print_status(data)

                except Exception as e:
                    print(f"⚠ 健康检查失败: {e}")

                # 等待10秒
                await asyncio.sleep(10)

        except asyncio.CancelledError:
            print("\n🛑 监控循环已停止")
        finally:
            await client.aclose()

    def _print_status(self, health_data: dict):
        """打印状态"""
        print(f"\n📊 监控状态 (运行时间: {health_data.get('uptime', 0):.0f}秒)")
        print(f"   状态: {health_data.get('status', 'unknown')}")

        components = health_data.get('components', {})
        for name, component in components.items():
            status = "✓" if component.get('healthy') else "✗"
            print(f"   {status} {name}: {component.get('healthy', 'unknown')}")

    def stop(self):
        """停止监控服务"""
        print("\n🛑 停止监控服务...")
        self.running = False


# =============================================================================
# 主程序
# =============================================================================

import asyncio

async def main():
    """主函数"""
    print("=" * 60)
    print("小诺监控服务")
    print("=" * 60)
    print()

    # 创建监控服务
    service = MonitoringService(metrics_port=9095)

    # 设置信号处理
    def signal_handler(sig, frame):
        service.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 启动服务
        await service.start()
    except KeyboardInterrupt:
        service.stop()


if __name__ == "__main__":
    asyncio.run(main())
