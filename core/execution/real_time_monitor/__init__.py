#!/usr/bin/env python3
"""
实时执行监控系统 - 公共接口
Real-time Execution Monitoring System - Public Interface

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0

提供系统运行状态监控、性能分析和告警功能。
"""

import logging

import websockets

logger = logging.getLogger(__name__)

from .monitor import RealTimeMonitor
from .resource_monitors import (
    CPUMonitor,
    DiskMonitor,
    MemoryMonitor,
    NetworkMonitor,
    ResourceMonitor,
)
from .types import (
    Alert,
    AlertLevel,
    Metric,
    MetricType,
    MonitoringConfig,
    PerformanceSnapshot,
    ResourceStatus,
)


class _RealTimeMonitorWithWebSocket(RealTimeMonitor):
    """带WebSocket支持的实时监控器"""

    async def start(self):
        """启动监控系统(包含WebSocket服务器)"""
        await super().start()

        # 启动WebSocket服务器
        import websockets

        self.websocket_server = await websockets.serve(
            self._handle_websocket_client, "localhost", self.config.websocket_port
        )

        logger.info(f"WebSocket服务器已启动,端口: {self.config.websocket_port}")

    async def stop(self):
        """停止监控系统(包含WebSocket服务器)"""
        await super().stop()

        # 关闭WebSocket服务器
        if hasattr(self, 'websocket_server') and self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()

        # 关闭所有WebSocket连接
        for client in self.websocket_clients.copy():
            await client.close()

    async def _handle_websocket_client(self, websocket, path):
        """处理WebSocket客户端连接"""
        self.websocket_clients.add(websocket)
        logger.info(f"新的WebSocket连接: {websocket.remote_address}")

        try:
            # 发送初始数据
            await self._send_initial_data(websocket)

            # 保持连接
            async for message in websocket:
                try:
                    import json
                    data = json.loads(message)
                    await self._handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"无效的JSON消息: {message}")

        except websockets.exceptions.ConnectionClosed:
            print(f"捕获websockets.exceptions.ConnectionClosed异常: {e}")
        finally:
            self.websocket_clients.remove(websocket)
            logger.info(f"WebSocket连接断开: {websocket.remote_address}")

    async def _send_initial_data(self, websocket):
        """发送初始数据给客户端"""
        import json
        from dataclasses import asdict

        # 发送当前指标
        current_metrics = {
            name: values[-1][1] if values else 0
            for name, values in self.metrics.items()
        }

        await websocket.send(json.dumps({"type": "metrics_update", "data": current_metrics}))

        # 发送活动告警
        active_alerts = [asdict(alert) for alert in self.alerts.values() if not alert.resolved_at]

        if active_alerts:
            await websocket.send(json.dumps({"type": "alert", "data": active_alerts}))

    async def _handle_client_message(self, websocket, data):
        """处理客户端消息"""
        import json
        from dataclasses import asdict

        message_type = data.get("type")

        if message_type == "get_metrics":
            requested_metrics = data.get("metrics", [])
            metrics_data = {}

            for metric_name in requested_metrics:
                if metric_name in self.metrics:
                    metrics_data[metric_name] = [
                        {"timestamp": ts.isoformat(), "value": value}
                        for ts, value in self.metrics[metric_name]
                    ]

            await websocket.send(json.dumps({"type": "metrics_history", "data": metrics_data}))

        elif message_type == "get_performance":
            # 发送性能历史
            performance_data = [asdict(snapshot) for snapshot in self.performance_snapshots]

            await websocket.send(
                json.dumps({"type": "performance_history", "data": performance_data})
            )

    async def _broadcast_metric_update(self, metric):
        """广播指标更新"""
        import json

        if not self.websocket_clients:
            return

        message = json.dumps(
            {
                "type": "metric_update",
                "data": {
                    "name": metric.name,
                    "value": metric.value,
                    "timestamp": metric.timestamp.isoformat(),
                    "unit": metric.unit,
                },
            }
        )

        import asyncio

        await asyncio.gather(
            *[client.send(message) for client in self.websocket_clients], return_exceptions=True
        )

    async def _broadcast_alert(self, alert):
        """广播告警"""
        import json
        from dataclasses import asdict

        if not self.websocket_clients:
            return

        message = json.dumps({"type": "alert_triggered", "data": asdict(alert, default=str)})

        import asyncio

        await asyncio.gather(
            *[client.send(message) for client in self.websocket_clients], return_exceptions=True
        )

    async def _broadcast_alert_resolved(self, alert):
        """广播告警解决"""
        import json

        if not self.websocket_clients:
            return

        message = json.dumps(
            {
                "type": "alert_resolved",
                "data": {
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "resolved_at": alert.resolved_at.isoformat(),
                },
            }
        )

        import asyncio

        await asyncio.gather(
            *[client.send(message) for client in self.websocket_clients], return_exceptions=True
        )

    async def record_metric(self, metric):
        """记录指标(包含WebSocket广播)"""
        await super().record_metric(metric)
        await self._broadcast_metric_update(metric)

    async def _trigger_alert(self, *args, **kwargs):
        """触发告警(包含WebSocket广播)"""
        await super()._trigger_alert(*args, **kwargs)
        # 广播告警
        rule_name = args[0] if args else kwargs.get('rule_name')
        if rule_name and rule_name in self.alerts:
            await self._broadcast_alert(self.alerts[rule_name])

    async def _resolve_alert(self, rule_name: str):
        """解决告警(包含WebSocket广播)"""
        await super()._resolve_alert(rule_name)
        # 广广播告解决
        if rule_name in self.alerts:
            await self._broadcast_alert_resolved(self.alerts[rule_name])


# 创建全局实时监控实例
real_time_monitor = _RealTimeMonitorWithWebSocket()


# 便捷函数
async def start_real_time_monitoring():
    """启动实时监控"""
    await real_time_monitor.start()


async def stop_real_time_monitoring():
    """停止实时监控"""
    await real_time_monitor.stop()


async def record_custom_metric(
    name: str, value: float, metric_type: MetricType = MetricType.GAUGE, unit: str = ""
):
    """记录自定义指标"""
    metric = Metric(
        name=name,
        metric_type=metric_type,
        description=f"自定义指标: {name}",
        value=value,
        unit=unit,
    )
    await real_time_monitor.record_metric(metric)


def get_monitoring_summary():
    """获取监控摘要"""
    return real_time_monitor.get_performance_summary()


__all__ = [
    # 类型定义
    "MetricType",
    "AlertLevel",
    "ResourceStatus",
    "Metric",
    "Alert",
    "PerformanceSnapshot",
    "MonitoringConfig",
    # 资源监控器
    "ResourceMonitor",
    "CPUMonitor",
    "MemoryMonitor",
    "DiskMonitor",
    "NetworkMonitor",
    # 主监控类
    "RealTimeMonitor",
    "_RealTimeMonitorWithWebSocket",
    # 全局实例和便捷函数
    "real_time_monitor",
    "start_real_time_monitoring",
    "stop_real_time_monitoring",
    "record_custom_metric",
    "get_monitoring_summary",
]
