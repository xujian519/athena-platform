"""
告警系统
提供智能告警、通知发送和告警管理功能
"""

from __future__ import annotations
import asyncio
import json
import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from enum import Enum
from typing import Any

import aiohttp
import websockets

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

class AlertStatus(Enum):
    """告警状态"""
    FIRING = 'firing'
    RESOLVED = 'resolved'
    SILENCED = 'silenced'

class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = 'email'
    WEBHOOK = 'webhook'
    SLACK = 'slack'
    WEBSOCKET = 'websocket'
    SMS = 'sms'

@dataclass
class Alert:
    """告警定义"""
    id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    details: dict[str, Any]
    service: str
    created_at: datetime
    resolved_at: datetime | None = None
    labels: dict[str, str] | None = None
    annotations: dict[str, str] | None = None
    fingerprint: str | None = None

@dataclass
class AlertRule:
    """告警规则"""
    id: str
    name: str
    expression: str
    severity: AlertSeverity
    for_duration: timedelta
    labels: dict[str, str]
    annotations: dict[str, str]
    enabled: bool = True
    last_evaluation: datetime | None = None
    current_state: bool = False

@dataclass
class NotificationConfig:
    """通知配置"""
    channel: NotificationChannel
    enabled: bool = True
    config: dict[str, Any] | None = None
    filters: dict[str, Any] | None = None  # 过滤条件

@dataclass
class Silence:
    """静默规则"""
    id: str
    matchers: list[dict[str, str]]
    starts_at: datetime
    ends_at: datetime
    created_by: str
    comment: str

class EmailNotifier:
    """邮件通知器"""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    async def send(self, alert: Alert, recipients: list[str]):
        """发送邮件通知"""
        try:
            # 创建邮件
            msg = MimeMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.name}"

            # 邮件正文
            body = self._format_email_body(alert)
            msg.attach(MimeText(body, 'html', 'utf-8'))

            # 发送邮件
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()

            logger.info(f"邮件告警已发送: {alert.name}")

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")

    def _format_email_body(self, alert: Alert) -> str:
        """格式化邮件正文"""
        severity_color = {
            AlertSeverity.INFO: '#17a2b8',
            AlertSeverity.WARNING: '#ffc107',
            AlertSeverity.ERROR: '#fd7e14',
            AlertSeverity.CRITICAL: '#dc3545'
        }

        color = severity_color.get(alert.severity, '#6c757d')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{
                    border-left: 4px solid {color};
                    padding: 15px;
                    margin: 20px 0;
                    background-color: #f8f9fa;
                }}
                .severity {{ color: {color}; font-weight: bold; }}
                .details {{ margin-top: 15px; }}
                .label {{ background-color: #e9ecef; padding: 2px 6px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h2>🚨 系统告警</h2>

            <div class='alert-box'>
                <h3>{alert.name}</h3>
                <p><span class='severity'>严重程度: {alert.severity.value.upper()}</span></p>
                <p><strong>状态:</strong> {alert.status.value}</p>
                <p><strong>服务:</strong> {alert.service}</p>
                <p><strong>时间:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>消息:</strong> {alert.message}</p>

                <div class='details'>
                    <h4>详细信息:</h4>
                    <pre>{json.dumps(alert.details, indent=2, ensure_ascii=False)}</pre>
                </div>

                {self._format_labels(alert.labels) if alert.labels else ''}
            </div>
        </body>
        </html>
        """
        return html

    def _format_labels(self, labels: dict[str, str]) -> str:
        """格式化标签"""
        if not labels:
            return ''

        label_html = '<h4>标签:</h4>'
        for key, value in labels.items():
            label_html += f'<span class="label">{key}: {value}</span> '

        return label_html

class WebhookNotifier:
    """Webhook通知器"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def send(self, alert: Alert, webhook_url: str, headers: dict[str, str] | None = None):
        """发送Webhook通知"""
        try:
            payload = {
                'alert_id': alert.id,
                'alert_name': alert.name,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'message': alert.message,
                'service': alert.service,
                'created_at': alert.created_at.isoformat(),
                'details': alert.details,
                'labels': alert.labels or {},
                'annotations': alert.annotations or {}
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=headers or {}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook告警已发送: {alert.name}")
                    else:
                        logger.error(f"Webhook发送失败: {response.status}")

        except Exception as e:
            logger.error(f"发送Webhook失败: {e}")

class SlackNotifier:
    """Slack通知器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, alert: Alert, channel: str | None = None):
        """发送Slack通知"""
        try:
            severity_emoji = {
                AlertSeverity.INFO: 'ℹ️',
                AlertSeverity.WARNING: '⚠️',
                AlertSeverity.ERROR: '🚨',
                AlertSeverity.CRITICAL: '🔴'
            }

            emoji = severity_emoji.get(alert.severity, '📢')

            payload = {
                'text': f"{emoji} {alert.name}",
                'channel': channel,
                'attachments': [
                    {
                        'color': self._get_color(alert.severity),
                        'fields': [
                            {
                                'title': '严重程度',
                                'value': alert.severity.value.upper(),
                                'short': True
                            },
                            {
                                'title': '服务',
                                'value': alert.service,
                                'short': True
                            },
                            {
                                'title': '状态',
                                'value': alert.status.value,
                                'short': True
                            },
                            {
                                'title': '时间',
                                'value': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                                'short': True
                            }
                        ],
                        'text': alert.message,
                        'fields': [
                            {
                                'title': '详细信息',
                                'value': json.dumps(alert.details, indent=2, ensure_ascii=False),
                                'short': False
                            }
                        ] if alert.details else []
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack告警已发送: {alert.name}")

        except Exception as e:
            logger.error(f"发送Slack失败: {e}")

    def _get_color(self, severity: AlertSeverity) -> str:
        """获取颜色"""
        colors = {
            AlertSeverity.INFO: '#36a64f',
            AlertSeverity.WARNING: '#ff9500',
            AlertSeverity.ERROR: '#ff0000',
            AlertSeverity.CRITICAL: '#8b0000'
        }
        return colors.get(severity, '#808080')

class WebSocketNotifier:
    """WebSocket通知器"""

    def __init__(self, ws_server_url: str):
        self.ws_server_url = ws_server_url
        self.connections: dict[str, websockets.WebSocketServerProtocol] = {}

    async def send(self, alert: Alert):
        """发送WebSocket通知"""
        message = {
            'type': 'alert',
            'data': {
                'id': alert.id,
                'name': alert.name,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'message': alert.message,
                'service': alert.service,
                'created_at': alert.created_at.isoformat(),
                'details': alert.details
            }
        }

        # 广播给所有连接的客户端
        disconnected = []
        for conn_id, ws in self.connections.items():
            try:
                await ws.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(conn_id)

        # 清理断开的连接
        for conn_id in disconnected:
            del self.connections[conn_id]

    def register_connection(self, conn_id: str, websocket: websockets.WebSocketServerProtocol):
        """注册WebSocket连接"""
        self.connections[conn_id] = websocket

    def unregister_connection(self, conn_id: str):
        """注销WebSocket连接"""
        if conn_id in self.connections:
            del self.connections[conn_id]

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: dict[str, AlertRule] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.silences: dict[str, Silence] = {}
        self.notifications: dict[str, NotificationConfig] = {}
        self.notifiers: dict[NotificationChannel, Any] = {}
        self.alert_history: list[Alert] = []
        self._evaluation_loop_task: asyncio.Task | None = None

    def register_notifier(self, channel: NotificationChannel, notifier: Any):
        """注册通知器"""
        self.notifiers[channel] = notifier
        logger.info(f"注册通知器: {channel.value}")

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules[rule.id] = rule
        logger.info(f"添加告警规则: {rule.name}")

    def remove_rule(self, rule_id: str):
        """移除告警规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"移除告警规则: {rule_id}")

    def add_notification(self, name: str, config: NotificationConfig):
        """添加通知配置"""
        self.notifications[name] = config
        logger.info(f"添加通知配置: {name}")

    def add_silence(self, silence: Silence):
        """添加静默规则"""
        self.silences[silence.id] = silence
        logger.info(f"添加静默规则: {silence.id}")

    def remove_silence(self, silence_id: str):
        """移除静默规则"""
        if silence_id in self.silences:
            del self.silences[silence_id]
            logger.info(f"移除静默规则: {silence_id}")

    def is_silenced(self, alert: Alert) -> bool:
        """检查告警是否被静默"""
        for silence in self.silences.values():
            if self._matches_silence(alert, silence):
                return True
        return False

    def _matches_silence(self, alert: Alert, silence: Silence) -> bool:
        """检查告警是否匹配静默规则"""
        now = datetime.utcnow()

        # 检查时间范围
        if not (silence.starts_at <= now <= silence.ends_at):
            return False

        # 检查匹配条件
        for matcher in silence.matchers:
            label_name = matcher.get('name')
            label_value = matcher.get('value')
            is_regex = matcher.get('is_regex', False)
            is_equal = matcher.get('is_equal', True)

            # 获取标签值
            alert_value = alert.labels.get(label_name) if alert.labels else None

            if alert_value is None:
                return False

            # 匹配逻辑
            if is_equal:
                if is_regex:
                    import re
                    if not re.match(label_value, alert_value):
                        return False
                else:
                    if alert_value != label_value:
                        return False
            else:
                if alert_value == label_value:
                    return False

        return True

    async def evaluate_rules(self):
        """评估告警规则"""
        # 这里应该集成实际的指标评估逻辑
        # 简化实现,模拟一些告警

        now = datetime.utcnow()

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # 模拟规则评估
            is_firing = self._evaluate_expression(rule.expression)

            # 检查状态变化
            if is_firing and not rule.current_state:
                # 告警触发
                await self._fire_alert(rule)
                rule.current_state = True
            elif not is_firing and rule.current_state:
                # 告警恢复
                await self._resolve_alert(rule)
                rule.current_state = False

            rule.last_evaluation = now

    def _evaluate_expression(self, expression: str) -> bool:
        """评估表达式(简化实现)"""
        # 这里应该集成实际的Prometheus查询或其他指标系统
        # 简化实现,返回一些模拟值
        import random
        return random.random() > 0.9  # 10%的概率触发告警

    async def _fire_alert(self, rule: AlertRule):
        """触发告警"""
        alert = Alert(
            id=f"alert_{rule.id}_{datetime.utcnow().timestamp()}",
            name=rule.name,
            severity=rule.severity,
            status=AlertStatus.FIRING,
            message=f"告警规则触发: {rule.annotations.get('summary', rule.name)}",
            details=rule.annotations,
            service=rule.labels.get('service', 'unknown'),
            created_at=datetime.utcnow(),
            labels=rule.labels,
            annotations=rule.annotations
        )

        # 检查静默规则
        if self.is_silenced(alert):
            alert.status = AlertStatus.SILENCED
            logger.info(f"告警被静默: {alert.name}")
            return

        # 保存活跃告警
        self.active_alerts[rule.id] = alert
        self.alert_history.append(alert)

        # 发送通知
        await self._send_notifications(alert)

        logger.warning(f"告警触发: {alert.name}")

    async def _resolve_alert(self, rule: AlertRule):
        """解决告警"""
        if rule.id in self.active_alerts:
            alert = self.active_alerts[rule.id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()

            # 移除活跃告警
            del self.active_alerts[rule.id]

            # 发送恢复通知
            await self._send_notifications(alert)

            logger.info(f"告警已解决: {alert.name}")

    async def _send_notifications(self, alert: Alert):
        """发送通知"""
        for _name, config in self.notifications.items():
            if not config.enabled:
                continue

            # 检查过滤条件
            if not self._passes_filters(alert, config.filters):
                continue

            # 根据渠道发送通知
            notifier = self.notifiers.get(config.channel)
            if notifier:
                try:
                    if config.channel == NotificationChannel.EMAIL:
                        await notifier.send(
                            alert,
                            config.config.get('recipients', [])
                        )
                    elif config.channel == NotificationChannel.WEBHOOK:
                        await notifier.send(
                            alert,
                            config.config.get('url'),
                            config.config.get('headers')
                        )
                    elif config.channel == NotificationChannel.SLACK:
                        await notifier.send(
                            alert,
                            config.config.get('channel')
                        )
                    elif config.channel == NotificationChannel.WEBSOCKET:
                        await notifier.send(alert)
                except Exception as e:
                    logger.error(f"发送通知失败 {config.channel.value}: {e}")

    def _passes_filters(self, alert: Alert, filters: dict[str, Any] | None = None) -> bool:
        """检查是否通过过滤条件"""
        if not filters:
            return True

        # 严重程度过滤
        if 'severities' in filters:
            if alert.severity.value not in filters['severities']:
                return False

        # 服务过滤
        if 'services' in filters:
            if alert.service not in filters['services']:
                return False

        # 标签过滤
        if 'labels' in filters:
            for key, value in filters['labels'].items():
                if alert.labels and alert.labels.get(key) != value:
                    return False

        return True

    async def start_evaluation_loop(self, interval: int = 30):
        """启动评估循环"""
        logger.info(f"启动告警评估循环,间隔: {interval}秒")

        async def evaluation_loop():
            while True:
                try:
                    await self.evaluate_rules()
                    await asyncio.sleep(interval)
                except Exception as e:
                    logger.error(f"告警评估错误: {e}")
                    await asyncio.sleep(interval)

        self._evaluation_loop_task = asyncio.create_task(evaluation_loop())

    async def stop_evaluation_loop(self):
        """停止评估循环"""
        if self._evaluation_loop_task:
            self._evaluation_loop_task.cancel()
            try:
                await self._evaluation_loop_task
            except asyncio.CancelledError:
                # 任务被取消，正常退出
                pass
            logger.info('告警评估循环已停止')

    def get_active_alerts(self) -> list[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> list[Alert]:
        """获取告警历史"""
        return self.alert_history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """获取告警统计"""
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)

        severity_counts = {
            severity.value: 0
            for severity in AlertSeverity
        }

        for alert in self.active_alerts.values():
            severity_counts[alert.severity.value] += 1

        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'rules_count': len(self.rules),
            'silences_count': len(self.silences),
            'severity_breakdown': severity_counts,
            'last_evaluation': max(
                (rule.last_evaluation for rule in self.rules.values() if rule.last_evaluation),
                default=None
            )
        }

# 全局告警管理器
alert_manager = AlertManager()

# 默认告警规则
DEFAULT_ALERT_RULES = [
    AlertRule(
        id='high_error_rate',
        name='高错误率',
        expression='rate(errors_total[5m]) > 0.1',
        severity=AlertSeverity.WARNING,
        for_duration=timedelta(minutes=2),
        labels={'service': 'api_gateway'},
        annotations={
            'summary': 'API网关错误率过高',
            'description': '5分钟内错误率超过10%'
        }
    ),
    AlertRule(
        id='high_memory_usage',
        name='高内存使用',
        expression='memory_usage_bytes / (1024*1024*1024) > 2',
        severity=AlertSeverity.WARNING,
        for_duration=timedelta(minutes=5),
        labels={'service': 'fusion_platform'},
        annotations={
            'summary': '内存使用过高',
            'description': '内存使用超过2GB'
        }
    ),
    AlertRule(
        id='circuit_breaker_open',
        name='熔断器开启',
        expression='circuit_breaker_state == 1',
        severity=AlertSeverity.CRITICAL,
        for_duration=timedelta(minutes=1),
        labels={'service': 'service_discovery'},
        annotations={
            'summary': '熔断器已开启',
            'description': '服务的熔断器处于开启状态'
        }
    )
]

# 初始化函数
async def initialize_alerting():
    """初始化告警系统"""
    # 添加默认规则
    for rule in DEFAULT_ALERT_RULES:
        alert_manager.add_rule(rule)

    # 启动评估循环
    await alert_manager.start_evaluation_loop()

    logger.info('告警系统初始化完成')
