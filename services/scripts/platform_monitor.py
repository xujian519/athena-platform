#!/usr/bin/env python3
"""
Athena平台监控系统
Platform Monitoring System for Athena Multimodal File System
提供全面的系统监控、性能分析和运维自动化功能
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil
import requests
import uvicorn
import yaml

# FastAPI相关
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

# 导入统一认证模块

# 监控相关
try:
    import prometheus_client as prometheus
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = logging.getLogger('PlatformMonitor')

class AlertLevel(Enum):
    """告警级别"""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

class MetricType(Enum):
    """指标类型"""
    COUNTER = 'counter'
    GAUGE = 'gauge'
    HISTOGRAM = 'histogram'
    SUMMARY = 'summary'

@dataclass
class ServiceMetric:
    """服务指标"""
    service_name: str
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    request_count: int
    error_count: int
    response_time: float
    uptime: float
    status: str

@dataclass
class SystemAlert:
    """系统告警"""
    alert_id: str
    level: AlertLevel
    service: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: datetime | None = None

@dataclass
class PerformanceTrend:
    """性能趋势"""
    metric_name: str
    values: deque
    timestamps: deque
    unit: str

class PrometheusMetrics:
    """Prometheus指标收集器"""

    def __init__(self):
        if PROMETHEUS_AVAILABLE:
            # 创建指标
            self.request_count = prometheus.Counter(
                'athena_requests_total',
                'Total requests',
                ['service', 'method']
            )

            self.request_duration = prometheus.Histogram(
                'athena_request_duration_seconds',
                'Request duration',
                ['service'],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
            )

            self.active_connections = prometheus.Gauge(
                'athena_active_connections',
                'Active connections',
                ['service']
            )

            self.cpu_usage = prometheus.Gauge(
                'athena_cpu_usage_percent',
                'CPU usage percentage',
                ['service']
            )

            self.memory_usage = prometheus.Gauge(
                'athena_memory_usage_percent',
                'Memory usage percentage',
                ['service']
            )

            self.error_rate = prometheus.Gauge(
                'athena_error_rate_percent',
                'Error rate percentage',
                ['service']
            )

    def record_request(self, service: str, method: str, duration: float) -> Any:
        """记录请求"""
        if PROMETHEUS_AVAILABLE:
            self.request_count.labels(service=service, method=method).inc()
            self.request_duration.labels(service=service).observe(duration)

    def update_cpu_usage(self, service: str, usage: float) -> None:
        """更新CPU使用率"""
        if PROMETHEUS_AVAILABLE:
            self.cpu_usage.labels(service=service).set(usage)

    def update_memory_usage(self, service: str, usage: float) -> None:
        """更新内存使用率"""
        if PROMETHEUS_AVAILABLE:
            self.memory_usage.labels(service=service).set(usage)

class PlatformMonitor:
    """平台监控系统"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or '/Users/xujian/Athena工作平台/deploy/multimodal_platform_config.yaml'
        self.config = self._load_config()

        # 监控配置
        self.monitoring_config = self.config.get('monitoring', {})
        self.alerting_config = self.monitoring_config.get('alerting', {})

        # 服务监控
        self.services = self.config.get('services', {})

        # 数据存储
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.alerts = deque(maxlen=1000)

        # 告警阈值
        self.thresholds = {
            'cpu_usage': self.alerting_config.get('thresholds', {}).get('cpu_usage', 80),
            'memory_usage': self.alerting_config.get('thresholds', {}).get('memory_usage', 85),
            'disk_usage': self.alerting_config.get('thresholds', {}).get('disk_usage', 90),
            'error_rate': self.alerting_config.get('thresholds', {}).get('error_rate', 5),
            'response_time': 10.0  # 秒
        }

        # Prometheus指标
        self.prometheus_metrics = PrometheusMetrics()

        # WebSocket连接
        self.websocket_connections = []

        # 监控状态
        self.monitoring_active = False

        logger.info('平台监控系统初始化完成')

    def _load_config(self) -> dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return {}

    async def start_monitoring(self):
        """启动监控"""
        self.monitoring_active = True
        logger.info('平台监控启动')

        # 启动监控任务
        asyncio.create_task(self._monitor_services())
        asyncio.create_task(self._monitor_system())
        asyncio.create_task(self._check_alerts())
        asyncio.create_task(self._cleanup_old_data())

    async def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        logger.info('平台监控停止')

    async def _monitor_services(self):
        """监控服务状态"""
        while self.monitoring_active:
            try:
                current_time = datetime.now()

                for service_name, service_config in self.services.items():
                    if service_name == 'athena_platform_manager':
                        continue  # 跳过管理服务本身

                    port = service_config.get('port')
                    if not port:
                        continue

                    # 收集服务指标
                    metric = await self._collect_service_metrics(service_name, port, current_time)
                    if metric:
                        self.metrics_history[service_name].append(metric)

                        # 更新Prometheus指标
                        self.prometheus_metrics.update_cpu_usage(service_name, metric.cpu_usage)
                        self.prometheus_metrics.update_memory_usage(service_name, metric.memory_usage)

                await asyncio.sleep(self.monitoring_config.get('scrape_interval', 15))

            except Exception as e:
                logger.error(f"服务监控异常: {e}")
                await asyncio.sleep(30)

    async def _monitor_system(self):
        """监控系统资源"""
        while self.monitoring_active:
            try:
                system_metrics = {
                    'timestamp': datetime.now(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
                    'process_count': len(psutil.pids()),
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
                }

                self.metrics_history['system'].append(system_metrics)

                # 通知WebSocket客户端
                await self._notify_websocket_clients({
                    'type': 'system_metrics',
                    'data': system_metrics
                })

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"系统监控异常: {e}")
                await asyncio.sleep(30)

    async def _check_alerts(self):
        """检查告警"""
        while self.monitoring_active:
            try:
                datetime.now()

                # 检查服务告警
                for service_name, metrics in self.metrics_history.items():
                    if service_name == 'system' or not metrics:
                        continue

                    latest_metric = metrics[-1] if metrics else None
                    if not latest_metric:
                        continue

                    # CPU告警
                    if latest_metric.cpu_usage > self.thresholds['cpu_usage']:
                        await self._create_alert(
                            AlertLevel.WARNING,
                            service_name,
                            f"CPU使用率过高: {latest_metric.cpu_usage:.1f}%"
                        )

                    # 内存告警
                    if latest_metric.memory_usage > self.thresholds['memory_usage']:
                        await self._create_alert(
                            AlertLevel.WARNING,
                            service_name,
                            f"内存使用率过高: {latest_metric.memory_usage:.1f}%"
                        )

                    # 响应时间告警
                    if latest_metric.response_time > self.thresholds['response_time']:
                        await self._create_alert(
                            AlertLevel.WARNING,
                            service_name,
                            f"响应时间过长: {latest_metric.response_time:.2f}秒"
                        )

                    # 错误率告警
                    if latest_metric.request_count > 0:
                        error_rate = (latest_metric.error_count / latest_metric.request_count) * 100
                        if error_rate > self.thresholds['error_rate']:
                            await self._create_alert(
                                AlertLevel.ERROR,
                                service_name,
                                f"错误率过高: {error_rate:.1f}%"
                            )

                # 检查系统告警
                system_metrics = self.metrics_history.get('system', deque())
                if system_metrics:
                    latest_system = system_metrics[-1]

                    if latest_system['disk_percent'] > self.thresholds['disk_usage']:
                        await self._create_alert(
                            AlertLevel.CRITICAL,
                            'system',
                            f"磁盘使用率过高: {latest_system['disk_percent']:.1f}%"
                        )

                await asyncio.sleep(60)  # 每分钟检查一次告警

            except Exception as e:
                logger.error(f"告警检查异常: {e}")
                await asyncio.sleep(60)

    async def _cleanup_old_data(self):
        """清理旧数据"""
        while self.monitoring_active:
            try:
                # 清理超过24小时的数据
                cutoff_time = datetime.now() - timedelta(hours=24)

                for _service_name, metrics in self.metrics_history.items():
                    while metrics and metrics[0].timestamp < cutoff_time:
                        metrics.popleft()

                # 清理已解决的告警
                cutoff_alert_time = datetime.now() - timedelta(days=7)
                while self.alerts and self.alerts[0].timestamp < cutoff_alert_time:
                    if self.alerts[0].resolved:
                        self.alerts.popleft()
                    else:
                        break

                await asyncio.sleep(3600)  # 每小时清理一次

            except Exception as e:
                logger.error(f"数据清理异常: {e}")
                await asyncio.sleep(3600)

    async def _collect_service_metrics(self, service_name: str, port: int, timestamp: datetime) -> ServiceMetric | None:
        """收集服务指标"""
        try:
            # 调用健康检查接口
            health_url = f"http://localhost:{port}/health"
            response = requests.get(health_url, timeout=5)

            if response.status_code == 200:
                health_data = response.json()

                # 获取进程指标
                service_metric = ServiceMetric(
                    service_name=service_name,
                    timestamp=timestamp,
                    cpu_usage=self._get_service_cpu_usage(service_name),
                    memory_usage=self._get_service_memory_usage(service_name),
                    request_count=health_data.get('request_count', 0),
                    error_count=health_data.get('error_count', 0),
                    response_time=health_data.get('average_response_time', 0.0),
                    uptime=health_data.get('uptime', 0.0),
                    status='running'
                )

                return service_metric
            else:
                return ServiceMetric(
                    service_name=service_name,
                    timestamp=timestamp,
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    request_count=0,
                    error_count=1,
                    response_time=0.0,
                    uptime=0.0,
                    status='error'
                )

        except Exception as e:
            logger.warning(f"收集 {service_name} 指标失败: {e}")
            return None

    def _get_service_cpu_usage(self, service_name: str) -> float:
        """获取服务CPU使用率"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if service_name in cmdline or 'python3' in cmdline:
                        return proc.cpu_percent(interval=1)
        except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
        return 0.0

    def _get_service_memory_usage(self, service_name: str) -> float:
        """获取服务内存使用率"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_percent']):
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if service_name in cmdline or 'python3' in cmdline:
                        return proc.info['memory_percent']
        except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
        return 0.0

    async def _create_alert(self, level: AlertLevel, service: str, message: str):
        """创建告警"""
        alert = SystemAlert(
            alert_id=f"alert_{int(time.time())}_{len(self.alerts)}",
            level=level,
            service=service,
            message=message,
            timestamp=datetime.now()
        )

        self.alerts.append(alert)

        # 通知WebSocket客户端
        await self._notify_websocket_clients({
            'type': 'alert',
            'data': {
                'alert_id': alert.alert_id,
                'level': alert.level.value,
                'service': alert.service,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat()
            }
        })

        # 发送外部通知
        if self.alerting_config.get('enabled', False):
            await self._send_external_notification(alert)

        logger.warning(f"告警: [{level.value.upper()}] {service} - {message}")

    async def _send_external_notification(self, alert: SystemAlert):
        """发送外部通知"""
        channels = self.alerting_config.get('channels', [])

        for channel in channels:
            try:
                if channel == 'email':
                    await self._send_email_alert(alert)
                elif channel == 'slack':
                    await self._send_slack_alert(alert)
                elif channel == 'webhook':
                    await self._send_webhook_alert(alert)
            except Exception as e:
                logger.error(f"发送 {channel} 通知失败: {e}")

    async def _send_email_alert(self, alert: SystemAlert):
        """发送邮件告警"""
        # 实现邮件发送逻辑
        logger.info(f"发送邮件告警: {alert.message}")

    async def _send_slack_alert(self, alert: SystemAlert):
        """发送Slack告警"""
        # 实现Slack通知逻辑
        logger.info(f"发送Slack告警: {alert.message}")

    async def _send_webhook_alert(self, alert: SystemAlert):
        """发送Webhook告警"""
        # 实现Webhook通知逻辑
        logger.info(f"发送Webhook告警: {alert.message}")

    async def _notify_websocket_clients(self, message: dict):
        """通知WebSocket客户端"""
        if not self.websocket_connections:
            return

        message_str = json.dumps(message, ensure_ascii=False)
        disconnected_clients = []

        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message_str)
            except Exception:
                disconnected_clients.append(websocket)

        # 移除断开的连接
        for client in disconnected_clients:
            self.websocket_connections.remove(client)

    def get_metrics_summary(self, hours: int = 1) -> dict[str, Any]:
        """获取指标摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        summary = {}

        for service_name, metrics in self.metrics_history.items():
            if service_name == 'system':
                continue

            # 过滤指定时间范围内的指标
            recent_metrics = [
                m for m in metrics
                if m.timestamp > cutoff_time
            ]

            if not recent_metrics:
                continue

            # 计算统计信息
            cpu_values = [m.cpu_usage for m in recent_metrics]
            memory_values = [m.memory_usage for m in recent_metrics]
            response_times = [m.response_time for m in recent_metrics if m.response_time > 0]

            total_requests = sum(m.request_count for m in recent_metrics)
            total_errors = sum(m.error_count for m in recent_metrics)

            summary[service_name] = {
                'metric_count': len(recent_metrics),
                'cpu_usage': {
                    'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'max': max(cpu_values) if cpu_values else 0,
                    'min': min(cpu_values) if cpu_values else 0
                },
                'memory_usage': {
                    'avg': sum(memory_values) / len(memory_values) if memory_values else 0,
                    'max': max(memory_values) if memory_values else 0,
                    'min': min(memory_values) if memory_values else 0
                },
                'requests': {
                    'total': total_requests,
                    'errors': total_errors,
                    'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0
                },
                'response_time': {
                    'avg': sum(response_times) / len(response_times) if response_times else 0,
                    'max': max(response_times) if response_times else 0,
                    'min': min(response_times) if response_times else 0
                }
            }

        return summary

    def get_active_alerts(self) -> list[dict[str, Any]:
        """获取活跃告警"""
        return [
            {
                'alert_id': alert.alert_id,
                'level': alert.level.value,
                'service': alert.service,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'resolved': alert.resolved,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            for alert in self.alerts
            if not alert.resolved
        ]

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"告警已解决: {alert_id}")
                return True
        return False

    # WebSocket处理
    async def handle_websocket(self, websocket: WebSocket):
        """处理WebSocket连接"""
        await websocket.accept()
        self.websocket_connections.append(websocket)

        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理消息
                if message.get('type') == 'subscribe':
                    # 订阅特定事件
                    await self._handle_subscription(websocket, message.get('event'))
                elif message.get('type') == 'get_metrics':
                    # 获取指标
                    summary = self.get_metrics_summary()
                    await websocket.send_text(json.dumps({
                        'type': 'metrics_summary',
                        'data': summary
                    }, ensure_ascii=False))
                elif message.get('type') == 'get_alerts':
                    # 获取告警
                    alerts = self.get_active_alerts()
                    await websocket.send_text(json.dumps({
                        'type': 'active_alerts',
                        'data': alerts
                    }, ensure_ascii=False))

        except WebSocketDisconnect:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)
        except Exception as e:
            logger.error(f"WebSocket处理错误: {e}")
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)

    async def _handle_subscription(self, websocket: WebSocket, event: str):
        """处理客户端订阅"""
        await websocket.send_text(json.dumps({
            'type': 'subscription_confirmed',
            'event': event
        }, ensure_ascii=False))

# 创建FastAPI应用
monitor = None

def create_monitor() -> Any:
    """创建监控实例"""
    global monitor
    if monitor is None:
        monitor = PlatformMonitor()
    return monitor

app = FastAPI(
    title='Athena平台监控系统',
    description='Athena多模态文件系统监控和运维',
    version='1.0.0'
)

# Prometheus指标端点
if PROMETHEUS_AVAILABLE:
    app.add_route('/metrics', prometheus.generate_latest)

# API端点
@app.get('/')
async def root():
    """根端点"""
    return {
        'service': 'Athena平台监控系统',
        'status': 'running',
        'version': '1.0.0',
        'prometheus_enabled': PROMETHEUS_AVAILABLE,
        'monitoring_active': create_monitor().monitoring_active
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    monitor_instance = create_monitor()
    return {
        'status': 'healthy',
        'monitoring_active': monitor_instance.monitoring_active,
        'monitored_services': len(monitor_instance.services),
        'active_alerts': len([a for a in monitor_instance.alerts if not a.resolved])
    }

@app.get('/metrics/summary')
async def get_metrics_summary(hours: int = 1):
    """获取指标摘要"""
    monitor_instance = create_monitor()
    summary = monitor_instance.get_metrics_summary(hours)

    return {
        'summary': summary,
        'time_range_hours': hours,
        'timestamp': datetime.now().isoformat()
    }

@app.get('/alerts')
async def get_alerts():
    """获取活跃告警"""
    monitor_instance = create_monitor()
    alerts = monitor_instance.get_active_alerts()

    return {
        'alerts': alerts,
        'total_count': len(alerts),
        'timestamp': datetime.now().isoformat()
    }

@app.post('/alerts/{alert_id}/resolve')
async def resolve_alert(alert_id: str):
    """解决告警"""
    monitor_instance = create_monitor()
    success = monitor_instance.resolve_alert(alert_id)

    if success:
        return {'success': True, 'message': f"告警 {alert_id} 已解决"}
    else:
        raise HTTPException(status_code=404, detail='告警不存在')

@app.get('/services/status')
async def get_services_status():
    """获取服务状态"""
    monitor_instance = create_monitor()
    services_status = {}

    for service_name, _service_config in monitor_instance.services.items():
        if service_name == 'athena_platform_manager':
            continue

        metrics = monitor_instance.metrics_history.get(service_name, deque())
        if metrics:
            latest_metric = metrics[-1]
            services_status[service_name] = {
                'status': latest_metric.status,
                'cpu_usage': latest_metric.cpu_usage,
                'memory_usage': latest_metric.memory_usage,
                'uptime': latest_metric.uptime,
                'last_update': latest_metric.timestamp.isoformat()
            }
        else:
            services_status[service_name] = {
                'status': 'unknown',
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'uptime': 0.0,
                'last_update': None
            }

    return {
        'services': services_status,
        'timestamp': datetime.now().isoformat()
    }

@app.post('/monitoring/start')
async def start_monitoring():
    """启动监控"""
    monitor_instance = create_monitor()

    if monitor_instance.monitoring_active:
        return {'success': True, 'message': '监控已在运行'}

    await monitor_instance.start_monitoring()
    return {'success': True, 'message': '监控已启动'}

@app.post('/monitoring/stop')
async def stop_monitoring():
    """停止监控"""
    monitor_instance = create_monitor()

    if not monitor_instance.monitoring_active:
        return {'success': True, 'message': '监控已停止'}

    await monitor_instance.stop_monitoring()
    return {'success': True, 'message': '监控已停止'}

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    monitor_instance = create_monitor()
    await monitor_instance.handle_websocket(websocket)

# 启动事件
@app.on_event('startup')
async def startup_event():
    """应用启动事件"""
    monitor_instance = create_monitor()
    await monitor_instance.start_monitoring()
    logger.info('监控系统启动完成')

@app.on_event('shutdown')
async def shutdown_event():
    """应用关闭事件"""
    monitor_instance = create_monitor()
    await monitor_instance.stop_monitoring()
    logger.info('监控系统关闭')

# 启动服务
if __name__ == '__main__':
    monitor_config = {
        'host': '0.0.0.0',
        'port': 9090,
        'reload': False,
        'log_level': 'info'
    }

    uvicorn.run(
        'platform_monitor:app',
        **monitor_config
    )
