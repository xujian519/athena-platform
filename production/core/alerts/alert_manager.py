#!/usr/bin/env python3
"""
告警管理器
Alert Manager

作者: Athena平台团队
版本: v1.0
创建: 2025-12-30

功能:
- 监控服务状态
- 发送告警通知
- 支持多种通知渠道
"""

from __future__ import annotations
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any

logger = logging.getLogger("AlertManager")


class AlertSeverity(Enum):
    """告警严重程度"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """告警渠道"""

    LOG = "log"  # 日志记录
    EMAIL = "email"  # 邮件通知
    WEBHOOK = "webhook"  # Webhook通知(企业微信等)
    CONSOLE = "console"  # 控制台输出


class Alert:
    """告警信息"""

    def __init__(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        service: str = "xiaonuo",
        metadata: dict | None = None,
    ):
        self.title = title
        self.message = message
        self.severity = severity
        self.service = service
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "service": self.service,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    def format_message(self) -> str:
        """格式化消息"""
        severity_icons = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }
        icon = severity_icons.get(self.severity, "📋")

        msg = f"""
{icon} {self.title}
{'=' * 50}

服务: {self.service}
级别: {self.severity.value.upper()}
时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{self.message}
"""

        if self.metadata:
            msg += "\n详细信息:\n"
            for key, value in self.metadata.items():
                msg += f"  {key}: {value}\n"

        return msg.strip()


class AlertManager:
    """告警管理器"""

    def __init__(
        self,
        enabled_channels: list[AlertChannel] | None = None,
        email_config: dict | None = None,
        webhook_url: str | None = None,
    ):
        """
        初始化告警管理器

        Args:
            enabled_channels: 启用的通知渠道
            email_config: 邮件配置
            webhook_url: Webhook URL
        """
        self.enabled_channels = enabled_channels or [AlertChannel.LOG, AlertChannel.CONSOLE]
        self.email_config = email_config or {}
        self.webhook_url = webhook_url
        self.alert_history: list[Alert] = []

        # 告警计数器(用于防止告警风暴)
        self.alert_counts: dict[str, int] = {}
        self.last_alert_time: dict[str, datetime] = {}

        logger.info(f"🚨 告警管理器已初始化,启用渠道: {[c.value for c in self.enabled_channels]}")

    async def send_alert(self, alert: Alert) -> bool:
        """
        发送告警

        Args:
            alert: 告警信息

        Returns:
            是否发送成功
        """
        try:
            # 检查告警频率限制
            if not self._should_send_alert(alert):
                logger.debug(f"告警被限流: {alert.title}")
                return False

            # 记录到历史
            self.alert_history.append(alert)
            if len(self.alert_history) > 1000:  # 最多保留1000条
                self.alert_history = self.alert_history[-1000:]

            # 发送到各个渠道
            success = True
            for channel in self.enabled_channels:
                try:
                    if channel == AlertChannel.LOG:
                        self._send_to_log(alert)
                    elif channel == AlertChannel.CONSOLE:
                        self._send_to_console(alert)
                    elif channel == AlertChannel.EMAIL:
                        await self._send_to_email(alert)
                    elif channel == AlertChannel.WEBHOOK:
                        await self._send_to_webhook(alert)
                except Exception as e:
                    logger.error(f"发送告警到{channel.value}失败: {e}")
                    success = False

            # 更新计数
            alert_key = f"{alert.service}:{alert.title}"
            self.alert_counts[alert_key] = self.alert_counts.get(alert_key, 0) + 1
            self.last_alert_time[alert_key] = alert.timestamp

            return success

        except Exception as e:
            logger.error(f"发送告警失败: {e}")
            return False

    def _should_send_alert(self, alert: Alert) -> bool:
        """判断是否应该发送告警(频率限制)"""
        alert_key = f"{alert.service}:{alert.title}"
        now = datetime.now()

        # 获取上次告警时间
        last_time = self.last_alert_time.get(alert_key)

        # 根据严重程度设置最小间隔
        min_intervals = {
            AlertSeverity.CRITICAL: 60,  # 1分钟
            AlertSeverity.ERROR: 300,  # 5分钟
            AlertSeverity.WARNING: 600,  # 10分钟
            AlertSeverity.INFO: 3600,  # 1小时
        }

        min_interval = min_intervals.get(alert.severity, 300)

        return not (last_time and (now - last_time).total_seconds() < min_interval)

    def _send_to_log(self, alert: Alert) -> Any:
        """发送到日志"""
        log_func = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical,
        }.get(alert.severity, logger.info)

        log_func(f"🚨 [{alert.service}] {alert.title}: {alert.message}")

    def _send_to_console(self, alert: Alert) -> Any:
        """发送到控制台"""
        print(alert.format_message())

    async def _send_to_email(self, alert: Alert):
        """发送到邮件"""
        if not self.email_config:
            logger.warning("邮件配置未设置,跳过邮件通知")
            return

        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg["From"] = self.email_config.get("from")
            msg["To"] = self.email_config.get("to")
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.service} - {alert.title}"

            # 添加正文
            msg.attach(MIMEText(alert.format_message(), "plain"))

            # 发送邮件
            with smtplib.SMTP(
                self.email_config.get("host", "localhost"), self.email_config.get("port", 25)
            ) as server:
                if self.email_config.get("use_tls", False):
                    server.starttls()
                    server.login(
                        self.email_config.get("username"), self.email_config.get("password")
                    )

                server.send_message(msg)
                logger.info(f"✅ 邮件告警已发送: {alert.title}")

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            raise

    async def _send_to_webhook(self, alert: Alert):
        """发送到Webhook(企业微信等)"""
        if not self.webhook_url:
            logger.warning("Webhook URL未设置,跳过Webhook通知")
            return

        try:
            import aiohttp

            # 构建企业微信消息格式
            payload = {
                "msgtype": "markdown",
                "markdown": {"content": f"### {alert.title}\n\n" f"{alert.format_message()}"},
            }

            async with aiohttp.ClientSession() as session, session.post(
                self.webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info(f"✅ Webhook告警已发送: {alert.title}")
                else:
                    logger.warning(f"Webhook返回错误: {response.status}")

        except ImportError:
            logger.warning("aiohttp未安装,跳过Webhook通知")
        except Exception as e:
            logger.error(f"Webhook发送失败: {e}")
            raise

    def get_alert_stats(self) -> dict:
        """获取告警统计"""
        return {
            "total_alerts": len(self.alert_history),
            "alert_counts": self.alert_counts.copy(),
            "recent_alerts": [alert.to_dict() for alert in self.alert_history[-10:]],
        }


# 全局告警管理器实例
_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """获取全局告警管理器实例"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def setup_alert_manager(
    enabled_channels: list[AlertChannel] | None = None,
    email_config: dict | None = None,
    webhook_url: str | None = None,
) -> AlertManager:
    """设置全局告警管理器"""
    global _alert_manager
    _alert_manager = AlertManager(
        enabled_channels=enabled_channels, email_config=email_config, webhook_url=webhook_url
    )
    return _alert_manager


# 便捷函数
async def send_alert(
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.INFO,
    service: str = "xiaonuo",
    metadata: dict | None = None,
) -> bool:
    """发送告警的便捷函数"""
    manager = get_alert_manager()
    alert = Alert(
        title=title, message=message, severity=severity, service=service, metadata=metadata
    )
    return await manager.send_alert(alert)


# 预定义的告警模板
class AlertTemplates:
    """预定义告警模板"""

    @staticmethod
    def service_down(service_name: str, port: int) -> Alert:
        """服务宕机告警"""
        return Alert(
            title=f"服务宕机: {service_name}",
            message=f"服务 {service_name} (端口 {port}) 已宕机或无响应",
            severity=AlertSeverity.CRITICAL,
            service=service_name,
            metadata={"port": port, "action": "请立即检查服务状态"},
        )

    @staticmethod
    def high_error_rate(service_name: str, error_rate: float, threshold: float = 0.05) -> Alert:
        """高错误率告警"""
        return Alert(
            title=f"高错误率: {service_name}",
            message=f"服务 {service_name} 错误率为 {error_rate:.1%},超过阈值 {threshold:.1%}",
            severity=AlertSeverity.WARNING,
            service=service_name,
            metadata={"error_rate": error_rate, "threshold": threshold},
        )

    @staticmethod
    def high_response_time(service_name: str, p95_latency: float, threshold: float = 2.0) -> Alert:
        """高响应时间告警"""
        return Alert(
            title=f"响应时间过长: {service_name}",
            message=f"服务 {service_name} P95响应时间为 {p95_latency:.2f}秒,超过阈值 {threshold:.2f}秒",
            severity=AlertSeverity.WARNING,
            service=service_name,
            metadata={"p95_latency": p95_latency, "threshold": threshold},
        )

    @staticmethod
    def dependency_unavailable(service_name: str, dependency: str) -> Alert:
        """依赖服务不可用告警"""
        return Alert(
            title=f"依赖服务不可用: {service_name}",
            message=f"服务 {service_name} 的依赖服务 {dependency} 不可用",
            severity=AlertSeverity.ERROR,
            service=service_name,
            metadata={"dependency": dependency},
        )
