from __future__ import annotations
import os

#!/usr/bin/env python3
"""
生产环境内存监控配置
Production Memory Monitor Configuration

集成内存监控到Athena工作平台的生产环境

功能:
- 自动启动内存监控
- Prometheus指标导出
- 告警配置
- 与FastAPI集成

作者: Athena AI Team
创建时间: 2026-01-26
版本: 1.0.0
"""

import asyncio
import logging
import time
from typing import Any

from core.monitoring.memory_monitor import MemoryAlert, MemoryMonitor

logger = logging.getLogger(__name__)


# =============================================================================
# 生产环境配置
# =============================================================================

PRODUCTION_MONITOR_CONFIG = {
    # 检查间隔（秒）
    "check_interval": 60,

    # 内存阈值（MB）
    "memory_threshold_mb": 1000,

    # 增长阈值（%）
    "growth_threshold_percent": 15,

    # GC对象阈值
    "gc_objects_threshold": 100000,

    # 快照历史大小
    "snapshot_history_size": 1440,  # 保留24小时历史

    # 自动垃圾回收
    "auto_gc": True,

    # 告警配置
    "alert_enabled": True,
    "alert_cooldown_minutes": 30,  # 同类型告警冷却时间
}


# =============================================================================
# Prometheus集成
# =============================================================================

class PrometheusMetricsExporter:
    """Prometheus指标导出器"""

    def __init__(self):
        """初始化Prometheus导出器"""
        try:
            from prometheus_client import Counter, Gauge, Histogram, start_http_server

            # 定义指标
            self.memory_usage_mb = Gauge(
                "athena_memory_usage_mb",
                "Athena内存使用量（MB）",
                ["service", "instance"],
            )

            self.memory_percent = Gauge(
                "athena_memory_percent",
                "Athena内存使用百分比",
                ["service", "instance"],
            )

            self.gc_objects_count = Gauge(
                "athena_gc_objects_count",
                "GC对象数量",
                ["service", "instance"],
            )

            self.memory_alerts_total = Counter(
                "athena_memory_alerts_total",
                "内存告警总数",
                ["service", "instance", "severity", "alert_type"],
            )

            self.tasks_total = Counter(
                "athena_tasks_total",
                "处理任务总数",
                ["service", "instance", "status"],
            )

            self.cache_operations_total = Counter(
                "athena_cache_operations_total",
                "缓存操作总数",
                ["service", "instance", "operation", "status"],
            )

            self._prometheus_available = True
            logger.info("✅ Prometheus指标已初始化")

        except ImportError:
            logger.warning("⚠️ prometheus_client未安装，Prometheus导出将不可用")
            self._prometheus_available = False

    def export_metrics(
        self,
        service_name: str = "athena",
        instance_id: str | None = None,
        memory_monitor: MemoryMonitor | None = None,
    ):
        """导出指标到Prometheus"""
        if not self._prometheus_available:
            return

        import os

        instance = instance_id or os.getenv("INSTANCE_ID", "default")

        if memory_monitor:
            # 导出内存指标
            stats = memory_monitor.get_stats()
            current = stats.get("current_memory", {})

            self.memory_usage_mb.labels(
                service=service_name, instance=instance
            ).set(current.get("rss_mb", 0))

            self.memory_percent.labels(
                service=service_name, instance=instance
            ).set(current.get("percent", 0))

            self.gc_objects_count.labels(
                service=service_name, instance=instance
            ).set(current.get("gc_objects", 0))

    def record_alert(
        self,
        alert: MemoryAlert,
        service_name: str = "athena",
        instance_id: str | None = None,
    ):
        """记录告警指标"""
        if not self._prometheus_available:
            return

        import os

        instance = instance_id or os.getenv("INSTANCE_ID", "default")

        self.memory_alerts_total.labels(
            service=service_name,
            instance=instance,
            severity=alert.severity,
            alert_type=alert.alert_type,
        ).inc()

    def start_server(self, port: int = 8000):
        """启动Prometheus HTTP服务器"""
        if not self._prometheus_available:
            logger.warning("⚠️ Prometheus不可用，无法启动HTTP服务器")
            return

        try:
            from prometheus_client import start_http_server

            start_http_server(port)
            logger.info(f"✅ Prometheus HTTP服务器已启动，端口: {port}")
        except Exception as e:
            logger.error(f"❌ 启动Prometheus服务器失败: {e}")


# =============================================================================
# 告警管理
# =============================================================================

class AlertManager:
    """告警管理器"""

    def __init__(
        self,
        enabled: bool = True,
        cooldown_minutes: int = 30,
        notification_channels: list[str] | None = None,
    ):
        """
        初始化告警管理器

        Args:
            enabled: 是否启用告警
            cooldown_minutes: 告警冷却时间（分钟）
            notification_channels: 通知渠道列表
        """
        self.enabled = enabled
        self.cooldown_seconds = cooldown_minutes * 60
        self.notification_channels = notification_channels or ["log"]

        # 告警历史
        self.alert_history: dict[str, float] = {}

        # Prometheus导出器
        self.metrics_exporter = PrometheusMetricsExporter()

    async def send_alert(self, alert: MemoryAlert):
        """发送告警"""
        if not self.enabled:
            return

        # 检查冷却时间
        alert_key = f"{alert.alert_type}_{alert.severity}"
        last_alert_time = self.alert_history.get(alert_key, 0)

        if time.time() - last_alert_time < self.cooldown_seconds:
            logger.debug(f"⏰ 告警冷却中，跳过: {alert_key}")
            return

        # 更新告警时间
        self.alert_history[alert_key] = time.time()

        # 记录到日志
        log_func = logger.warning if alert.severity == "warning" else logger.error
        log_func(f"🚨 内存告警: {alert.message}")

        # 导出到Prometheus
        self.metrics_exporter.record_alert(alert)

        # 发送到配置的通知渠道
        for channel in self.notification_channels:
            await self._send_to_channel(alert, channel)

    async def _send_to_channel(self, alert: MemoryAlert, channel: str):
        """发送到指定渠道"""
        if channel == "log":
            # 已在上面处理
            pass
        elif channel == "slack":
            await self._send_to_slack(alert)
        elif channel == "email":
            await self._send_to_email(alert)
        elif channel == "webhook":
            await self._send_to_webhook(alert)
        else:
            logger.warning(f"⚠️ 未知的告警渠道: {channel}")

    async def _send_to_slack(self, alert: MemoryAlert):
        """发送到Slack"""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")

        if not webhook_url:
            logger.debug("Slack webhook URL未配置")
            return

        try:
            import aiohttp

            color = {
                "info": "#36a64f",
                "warning": "#ff9900",
                "critical": "#ff0000",
            }.get(alert.severity, "#808080")

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"🚨 Athena内存告警 - {alert.severity.upper()}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "当前内存",
                                "value": f"{alert.current_snapshot.rss_mb:.2f} MB",
                                "short": True,
                            },
                            {
                                "title": "GC对象数",
                                "value": f"{alert.current_snapshot.gc_objects:,}",
                                "short": True,
                            },
                        ],
                        "footer": "Athena工作平台",
                        "ts": int(alert.timestamp),
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("✅ Slack告警已发送")
                    else:
                        logger.warning(f"⚠️ Slack告警发送失败: {response.status}")

        except Exception as e:
            logger.error(f"❌ 发送Slack告警失败: {e}")

    async def _send_to_email(self, alert: MemoryAlert):
        """发送邮件"""
        # TODO: 实现邮件发送
        logger.info("📧 邮件告警暂未实现")

    async def _send_to_webhook(self, alert: MemoryAlert):
        """发送到webhook"""
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")

        if not webhook_url:
            logger.debug("Webhook URL未配置")
            return

        try:
            import aiohttp

            payload = alert.to_dict()

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("✅ Webhook告警已发送")
                    else:
                        logger.warning(f"⚠️ Webhook告警发送失败: {response.status}")

        except Exception as e:
            logger.error(f"❌ 发送Webhook告警失败: {e}")


# =============================================================================
# FastAPI集成
# =============================================================================

class ProductionMemoryMonitor:
    """生产环境内存监控"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化生产环境监控

        Args:
            config: 监控配置
        """
        self.config = {**PRODUCTION_MONITOR_CONFIG, **(config or {})}

        # 创建内存监控器
        self.monitor = MemoryMonitor(
            check_interval=self.config["check_interval"],
            memory_threshold_mb=self.config["memory_threshold_mb"],
            growth_threshold_percent=self.config["growth_threshold_percent"],
            gc_objects_threshold=self.config["gc_objects_threshold"],
            snapshot_history_size=self.config["snapshot_history_size"],
            auto_gc=self.config["auto_gc"],
        )

        # 创建告警管理器
        self.alert_manager = AlertManager(
            enabled=self.config["alert_enabled"],
            cooldown_minutes=self.config["alert_cooldown_minutes"],
        )

        # 创建Prometheus导出器
        self.metrics_exporter = PrometheusMetricsExporter()

        # 设置告警回调
        self.monitor.alert_callback = self._handle_alert

        logger.info("✅ 生产环境内存监控初始化完成")

    async def _handle_alert(self, alert: MemoryAlert):
        """处理告警"""
        await self.alert_manager.send_alert(alert)

    async def start(self, prometheus_port: int | None = None):
        """
        启动监控

        Args:
            prometheus_port: Prometheus HTTP服务器端口
        """
        logger.info("🚀 启动生产环境内存监控...")

        # 启动内存监控
        await self.monitor.start()

        # 启动Prometheus服务器
        if prometheus_port:
            self.metrics_exporter.start_server(prometheus_port)

        logger.info("✅ 生产环境内存监控已启动")

    async def stop(self):
        """停止监控"""
        logger.info("🛑 停止生产环境内存监控...")
        await self.monitor.stop()
        logger.info("✅ 生产环境内存监控已停止")

    def export_metrics(self, service_name: str = "athena", instance_id: str | None = None):
        """导出Prometheus指标"""
        self.metrics_exporter.export_metrics(
            service_name=service_name,
            instance_id=instance_id,
            memory_monitor=self.monitor,
        )

    def get_monitor(self) -> MemoryMonitor:
        """获取内存监控器"""
        return self.monitor


# =============================================================================
# FastAPI端点
# =============================================================================

def create_monitoring_routes(app, monitor: ProductionMemoryMonitor):
    """创建监控相关的FastAPI路由"""


    @app.get("/api/monitoring/memory/stats")
    async def get_memory_stats():
        """获取内存统计"""
        return monitor.get_monitor().get_stats()

    @app.get("/api/monitoring/memory/alerts")
    async def get_memory_alerts(limit: int = 10):
        """获取内存告警"""
        return monitor.get_monitor().get_recent_alerts(limit=limit)

    @app.get("/api/monitoring/memory/snapshot")
    async def get_memory_snapshot():
        """获取当前内存快照"""
        snapshot = monitor.get_monitor().get_current_snapshot()
        return snapshot.to_dict()

    @app.post("/api/monitoring/memory/clear")
    async def clear_memory_history():
        """清空监控历史"""
        monitor.get_monitor().clear_history()
        return {"status": "cleared"}

    @app.get("/api/monitoring/health")
    async def health_check():
        """健康检查"""
        stats = monitor.get_monitor().get_stats()

        # 判断健康状态
        current_memory = stats.get("current_memory", {})
        is_healthy = current_memory.get("rss_mb", 0) < monitor.config["memory_threshold_mb"]

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "memory_mb": current_memory.get("rss_mb", 0),
            "threshold_mb": monitor.config["memory_threshold_mb"],
        }


# =============================================================================
# 使用示例
# =============================================================================

async def main():
    """主函数示例"""
    # 创建生产环境监控
    monitor = ProductionMemoryMonitor()

    # 启动监控（包括Prometheus）
    await monitor.start(prometheus_port=9090)

    # 模拟运行
    print("监控运行中，按 Ctrl+C 停止...")
    try:
        await asyncio.sleep(3600)  # 运行1小时
    except KeyboardInterrupt:
        pass

    # 停止监控
    await monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())
