#!/usr/bin/env python3
"""
小诺监控服务启动脚本
Xiaonuo Monitoring Service Startup Script

启动小诺的监控和指标收集服务

作者: Athena团队
创建时间: 2026-02-09
版本: v1.0.0
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Any, Optional

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx

# 导入日志配置
from production.logging.xiaonuo_logging import get_monitor_logger
from prometheus_client import start_http_server

# 导入指标收集器
try:
    from production.monitoring.xiaonuo_metrics import XiaonuoMetricsCollector
except ImportError:
    # 使用日志记录警告
    logger = get_monitor_logger()
    logger.warning("指标收集器模块未找到，使用基础指标")
    XiaonuoMetricsCollector = None


class MonitoringService:
    """监控服务"""

    metrics_port: int
    running: bool
    metrics_collector: Optional['XiaonuoMetricsCollector']
    health_check_url: str
    logger: logging.Logger

    def __init__(self, metrics_port: int = 9095) -> None:
        """
        初始化监控服务

        参数:
            metrics_port: Prometheus指标端口
        """
        self.metrics_port = metrics_port
        self.running = False
        self.logger = get_monitor_logger()

        # 创建指标收集器
        if XiaonuoMetricsCollector:
            self.metrics_collector = XiaonuoMetricsCollector(enabled=True)
        else:
            self.metrics_collector = None

        # 健康检查端点
        self.health_check_url = "http://127.0.0.1:8099/health"

    async def start(self) -> None:
        """启动监控服务"""
        self.logger.info("📊 启动小诺监控服务...")

        # 启动Prometheus HTTP服务器
        self.logger.info(f"   启动Prometheus指标服务器 (端口: {self.metrics_port})...")
        start_http_server(self.metrics_port)
        self.logger.info(f"   ✓ 指标端点: http://127.0.0.1:{self.metrics_port}/metrics")

        # 初始化指标
        if self.metrics_collector:
            self.logger.info("   ✓ 指标收集器已启用")
        else:
            self.logger.warning("   ⚠ 指标收集器未启用（使用基础指标）")

        self.running = True
        self.logger.info("✅ 监控服务已启动")

        # 开始监控循环
        await self._monitoring_loop()

    async def _monitoring_loop(self) -> None:
        """监控循环"""
        self.logger.info("🔄 开始监控循环...")
        self.logger.info("   按 Ctrl+C 停止")

        # 使用上下文管理器确保资源正确释放
        async with httpx.AsyncClient() as client:
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

                    except httpx.TimeoutException:
                        self.logger.warning("⚠ 健康检查超时")
                    except httpx.HTTPError as e:
                        self.logger.error(f"⚠ 健康检查HTTP错误: {e}")
                    except Exception as e:
                        self.logger.error(f"⚠ 健康检查失败: {e}")

                    # 等待10秒
                    await asyncio.sleep(10)

            except asyncio.CancelledError:
                self.logger.info("🛑 监控循环已停止")
            # 上下文管理器会自动关闭client

    def _print_status(self, health_data: dict[str, Any]) -> None:
        """打印状态"""
        uptime = health_data.get('uptime', 0)
        status = health_data.get('status', 'unknown')

        self.logger.info(f"📊 监控状态 (运行时间: {uptime:.0f}秒)")
        self.logger.info(f"   状态: {status}")

        components = health_data.get('components', {})
        for name, component in components.items():
            is_healthy = component.get('healthy', False)
            status_icon = "✓" if is_healthy else "✗"
            self.logger.info(f"   {status_icon} {name}: {is_healthy}")

    def stop(self) -> None:
        """停止监控服务"""
        self.logger.info("🛑 停止监控服务...")
        self.running = False


# =============================================================================
# 主程序
# =============================================================================


async def main() -> None:
    """主函数"""
    logger = get_monitor_logger()

    logger.info("=" * 60)
    logger.info("小诺监控服务")
    logger.info("=" * 60)

    # 创建监控服务
    service = MonitoringService(metrics_port=9095)

    # 设置信号处理
    def signal_handler(_sig: int, _frame: Any) -> None:
        """信号处理函数"""
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
