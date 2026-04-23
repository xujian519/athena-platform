#!/usr/bin/env python3
from __future__ import annotations
"""
执行模块告警通知系统
Execution Module Alert Notification System

基于监控指标触发告警，并通过多种渠道发送通知。

支持的通知渠道：
- Webhook（钉钉、企业微信、Slack等）
- 邮件
- 短信
- 日志

作者: Athena AI系统
版本: 2.0.0
创建时间: 2026-01-27
"""

import asyncio
import logging
import smtplib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """告警严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警对象"""
    name: str                          # 告警名称
    severity: AlertSeverity            # 严重级别
    message: str                       # 告警消息
    instance: str = "default"          # 实例ID
    component: str = "execution"       # 组件名称
    timestamp: datetime = field(default_factory=datetime.now)
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    value: Optional[float] = None      # 触发告警的值
    threshold: Optional[float] = None  # 阈值


@dataclass
class NotificationConfig:
    """通知配置"""
    enabled: bool = True

    # Webhook配置
    webhook_url: Optional[str] = None
    webhook_timeout: int = 10

    # 邮件配置
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_to: list[str] = field(default_factory=list)

    # 短信配置
    sms_enabled: bool = False
    sms_api_key: Optional[str] = None
    sms_api_url: Optional[str] = None
    sms_recipients: list[str] = field(default_factory=list)

    # 通知过滤
    min_severity: AlertSeverity = AlertSeverity.WARNING
    cooldown_seconds: int = 300        # 相同告警的冷却时间


class AlertManager:
    """
    告警管理器

    管理告警规则、触发告警和发送通知。
    """

    def __init__(self, config: NotificationConfig):
        """
        初始化告警管理器

        Args:
            config: 通知配置
        """
        self.config = config
        self.alert_history: dict[str, datetime] = {}  # 用于冷却时间
        self.alert_handlers: list[Callable] = []
        self.running = False

    def add_handler(self, handler: Callable[[Alert], None]):
        """
        添加自定义告警处理器

        Args:
            handler: 处理函数，接收Alert对象
        """
        self.alert_handlers.append(handler)

    async def trigger_alert(self, alert: Alert):
        """
        触发告警

        Args:
            alert: 告警对象
        """
        # 检查是否应该发送此告警
        if not self._should_send_alert(alert):
            logger.debug(f"告警被过滤或冷却中: {alert.name}")
            return

        logger.warning(f"触发告警: {alert.name} - {alert.message}")

        # 记录告警时间（用于冷却）
        self.alert_history[alert.name] = datetime.now()

        # 调用自定义处理器
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"告警处理器失败: {e}")

        # 发送通知
        await self._send_notifications(alert)

    def _should_send_alert(self, alert: Alert) -> bool:
        """
        判断是否应该发送告警

        Args:
            alert: 告警对象

        Returns:
            bool: 是否应该发送
        """
        # 检查严重级别
        severity_order = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.ERROR: 2,
            AlertSeverity.CRITICAL: 3,
        }

        if severity_order[alert.severity] < severity_order[self.config.min_severity]:
            return False

        # 检查冷却时间
        if alert.name in self.alert_history:
            last_alert_time = self.alert_history[alert.name]
            cooldown_seconds = (datetime.now() - last_alert_time).total_seconds()

            if cooldown_seconds < self.config.cooldown_seconds:
                return False

        return True

    async def _send_notifications(self, alert: Alert):
        """
        发送通知到所有配置的渠道

        Args:
            alert: 告警对象
        """
        if not self.config.enabled:
            return

        tasks = []

        # Webhook通知
        if self.config.webhook_url:
            tasks.append(self._send_webhook(alert))

        # 邮件通知
        if self.config.smtp_host and self.config.smtp_to:
            tasks.append(self._send_email(alert))

        # 短信通知（仅严重告警）
        if (self.config.sms_enabled and
            alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]):
            tasks.append(self._send_sms(alert))

        # 并行发送所有通知
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for _i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"通知发送失败: {result}")

    async def _send_webhook(self, alert: Alert):
        """
        发送Webhook通知

        Args:
            alert: 告警对象
        """
        try:
            payload = self._format_webhook_payload(alert)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.config.webhook_timeout)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook通知发送成功: {alert.name}")
                    else:
                        logger.warning(
                            f"Webhook通知返回非200状态码: {response.status}"
                        )

        except Exception as e:
            logger.error(f"Webhook通知发送失败: {e}")
            raise

    def _format_webhook_payload(self, alert: Alert) -> dict[str, Any]:
        """
        格式化Webhook负载

        Args:
            alert: 告警对象

        Returns:
            Dict: Webhook负载
        """
        # 默认格式（通用JSON）
        return {
            "alert_name": alert.name,
            "severity": alert.severity.value,
            "message": alert.message,
            "instance": alert.instance,
            "component": alert.component,
            "timestamp": alert.timestamp.isoformat(),
            "value": alert.value,
            "threshold": alert.threshold,
            "labels": alert.labels,
            "annotations": alert.annotations,
        }

    async def _send_email(self, alert: Alert):
        """
        发送邮件通知

        Args:
            alert: 告警对象
        """
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.name}"
            msg['From'] = self.config.smtp_from
            msg['To'] = ', '.join(self.config.smtp_to)

            # 邮件内容
            text_content = self._format_email_text(alert)
            html_content = self._format_email_html(alert)

            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 发送邮件
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()

                if self.config.smtp_user and self.config.smtp_password:
                    server.login(self.config.smtp_user, self.config.smtp_password)

                server.send_message(msg)

            logger.info(f"邮件通知发送成功: {alert.name}")

        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")
            raise

    def _format_email_text(self, alert: Alert) -> str:
        """格式化邮件文本内容"""
        return f"""
Athena执行模块告警通知

告警名称: {alert.name}
严重级别: {alert.severity.value.upper()}
实例: {alert.instance}
组件: {alert.component}
时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

消息:
{alert.message}

"""

    def _format_email_html(self, alert: Alert) -> str:
        """格式化邮件HTML内容"""
        severity_colors = {
            AlertSeverity.INFO: "#0066cc",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#990000",
        }

        color = severity_colors.get(alert.severity, "#333333")

        return f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert-box {{
            border-left: 4px solid {color};
            padding: 15px;
            background-color: #f5f5f5;
        }}
        .header {{ color: {color}; }}
        .label {{ font-weight: bold; }}
    </style>
</head>
<body>
    <div class="alert-box">
        <h2 class="header">[{alert.severity.value.upper()}] {alert.name}</h2>
        <table>
            <tr><td class="label">实例:</td><td>{alert.instance}</td></tr>
            <tr><td class="label">组件:</td><td>{alert.component}</td></tr>
            <tr><td class="label">时间:</td><td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>
        <h3>消息</h3>
        <p>{alert.message}</p>
    </div>
</body>
</html>
"""

    async def _send_sms(self, alert: Alert):
        """
        发送短信通知

        Args:
            alert: 告警对象
        """
        if not self.config.sms_api_url:
            logger.warning("短信API URL未配置，跳过短信通知")
            return

        try:
            # 构建短信内容
            message = f"[Athena告警] {alert.name}: {alert.message}"

            # 调用短信API（这里使用通用格式，实际需要根据具体提供商调整）
            payload = {
                "api_key": self.config.sms_api_key,
                "recipients": self.config.sms_recipients,
                "message": message,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.sms_api_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"短信通知发送成功: {alert.name}")
                    else:
                        logger.warning(
                            f"短信通知返回非200状态码: {response.status}"
                        )

        except Exception as e:
            logger.error(f"短信通知发送失败: {e}")
            raise


class ThresholdChecker:
    """
    阈值检查器

    定期检查指标是否超过阈值并触发告警。
    """

    def __init__(
        self,
        alert_manager: AlertManager,
        check_interval: int = 30
    ):
        """
        初始化阈值检查器

        Args:
            alert_manager: 告警管理器
            check_interval: 检查间隔（秒）
        """
        self.alert_manager = alert_manager
        self.check_interval = check_interval
        self.running = False
        self.check_tasks: list[Callable] = []

    def add_check(self, check_func: Callable[[], Alert]):
        """
        添加检查函数

        Args:
            check_func: 检查函数，返回Alert对象或None
        """
        self.check_tasks.append(check_func)

    async def start(self):
        """启动阈值检查"""
        if self.running:
            logger.warning("阈值检查器已在运行")
            return

        self.running = True
        logger.info(f"启动阈值检查器，间隔: {self.check_interval}秒")

        asyncio.create_task(self._check_loop())

    async def stop(self):
        """停止阈值检查"""
        self.running = False
        logger.info("阈值检查器已停止")

    async def _check_loop(self):
        """检查循环"""
        while self.running:
            try:
                for check_func in self.check_tasks:
                    try:
                        alert = check_func()
                        if alert:
                            await self.alert_manager.trigger_alert(alert)
                    except Exception as e:
                        logger.error(f"检查函数执行失败: {e}")

            except Exception as e:
                logger.error(f"阈值检查失败: {e}")

            await asyncio.sleep(self.check_interval)


# 预定义的检查函数
def create_queue_size_check(
    get_queue_size_func: Callable[[], int],
    get_max_size_func: Callable[[], int],
    warning_threshold: float = 0.7,
    critical_threshold: float = 0.9,
    instance: str = "default"
) -> Callable[[Optional[str], Alert]]:
    """
    创建队列大小检查函数

    Args:
        get_queue_size_func: 获取当前队列大小的函数
        get_max_size_func: 获取最大队列大小的函数
        warning_threshold: 警告阈值（比例）
        critical_threshold: 严重阈值（比例）
        instance: 实例ID

    Returns:
        Callable: 检查函数
    """
    def check() -> Alert | None:
        try:
            current_size = get_queue_size_func()
            max_size = get_max_size_func()

            if max_size == 0:
                return None

            usage_ratio = current_size / max_size

            if usage_ratio >= critical_threshold:
                return Alert(
                    name="QueueSizeCritical",
                    severity=AlertSeverity.CRITICAL,
                    message=f"队列使用率严重告警: {usage_ratio:.1%} ({current_size}/{max_size})",
                    instance=instance,
                    component="execution_engine",
                    value=usage_ratio,
                    threshold=critical_threshold,
                )
            elif usage_ratio >= warning_threshold:
                return Alert(
                    name="QueueSizeWarning",
                    severity=AlertSeverity.WARNING,
                    message=f"队列使用率过高: {usage_ratio:.1%} ({current_size}/{max_size})",
                    instance=instance,
                    component="execution_engine",
                    value=usage_ratio,
                    threshold=warning_threshold,
                )

        except Exception as e:
            logger.error(f"队列大小检查失败: {e}")

        return None

    return check


def create_error_rate_check(
    get_total_tasks_func: Callable[[], int],
    get_failed_tasks_func: Callable[[], int],
    warning_threshold: float = 0.05,
    critical_threshold: float = 0.1,
    instance: str = "default"
) -> Callable[[Optional[str], Alert]]:
    """
    创建错误率检查函数

    Args:
        get_total_tasks_func: 获取总任务数的函数
        get_failed_tasks_func: 获取失败任务数的函数
        warning_threshold: 警告阈值（比例）
        critical_threshold: 严重阈值（比例）
        instance: 实例ID

    Returns:
        Callable: 检查函数
    """
    def check() -> Alert | None:
        try:
            total = get_total_tasks_func()
            failed = get_failed_tasks_func()

            if total == 0:
                return None

            error_rate = failed / total

            if error_rate >= critical_threshold:
                return Alert(
                    name="ErrorRateCritical",
                    severity=AlertSeverity.CRITICAL,
                    message=f"任务错误率严重告警: {error_rate:.1%} ({failed}/{total})",
                    instance=instance,
                    component="execution_engine",
                    value=error_rate,
                    threshold=critical_threshold,
                )
            elif error_rate >= warning_threshold:
                return Alert(
                    name="ErrorRateWarning",
                    severity=AlertSeverity.WARNING,
                    message=f"任务错误率过高: {error_rate:.1%} ({failed}/{total})",
                    instance=instance,
                    component="execution_engine",
                    value=error_rate,
                    threshold=warning_threshold,
                )

        except Exception as e:
            logger.error(f"错误率检查失败: {e}")

        return None

    return check


if __name__ == "__main__":
    # 测试告警系统
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def test_alert():
        # 创建配置
        config = NotificationConfig(
            enabled=True,
            min_severity=AlertSeverity.INFO,
            webhook_url=None,  # 设置实际的webhook URL
        )

        # 创建告警管理器
        alert_manager = AlertManager(config)

        # 添加自定义处理器
        def handler(alert: Alert):
            print(f"收到告警: {alert.name} - {alert.message}")

        alert_manager.add_handler(handler)

        # 触发测试告警
        test_alert = Alert(
            name="TestAlert",
            severity=AlertSeverity.WARNING,
            message="这是一个测试告警",
            instance="test_instance",
        )

        await alert_manager.trigger_alert(test_alert)

    try:
        asyncio.run(test_alert())
    except KeyboardInterrupt:
        print("\n停止测试")
        sys.exit(0)
