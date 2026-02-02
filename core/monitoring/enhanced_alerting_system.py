#!/usr/bin/env python3
"""
Athena增强监控告警系统
提供多渠道告警通知、Web仪表板、历史数据查询等功能

作者: Athena AI
创建时间: 2025-12-29
版本: v1.0.0

特性:
- 多渠道告警: Email、企业微信、钉钉、Slack
- 告警聚合: 避免告警风暴
- 告警分级: P0-P4优先级
- 告警静默: 支持维护期
- Web仪表板: 实时监控展示
- 历史数据查询: 时间序列查询
- 性能报告: 自动生成报告
"""

import json
import logging
import smtplib
import time
from collections import defaultdict, deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


# =============================================================================
# 告警级别枚举
# =============================================================================


class AlertSeverity(Enum):
    """告警严重程度"""

    P0_CRITICAL = "P0"  # 严重故障,立即处理
    P1_HIGH = "P1"  # 高优先级,1小时内处理
    P2_MEDIUM = "P2"  # 中等优先级,4小时内处理
    P3_LOW = "P3"  # 低优先级,24小时内处理
    P4_INFO = "P4"  # 信息通知


class AlertStatus(Enum):
    """告警状态"""

    FIRING = "firing"  # 触发中
    RESOLVED = "resolved"  # 已解决
    SILENCED = "silenced"  # 已静默
    ACKNOWLEDGED = "acknowledged"  # 已确认


# =============================================================================
# 告警数据结构
# =============================================================================


@dataclass
class Alert:
    """告警对象"""

    alert_id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.FIRING
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    resolved_at: float | None = None
    acknowledged_by: str | None = None
    acknowledged_at: float | None = None
    silence_until: float | None = None
    notification_sent: bool = False
    notification_channels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["severity"] = self.severity.value
        data["status"] = self.status.value
        return data

    def age_seconds(self) -> float:
        """告警持续时间(秒)"""
        if self.status == AlertStatus.RESOLVED and self.resolved_at:
            return self.resolved_at - self.started_at
        return time.time() - self.started_at

    def is_silenced(self) -> bool:
        """检查是否已静默"""
        if self.silence_until is None:
            return False
        return time.time() < self.silence_until


@dataclass
class AlertRule:
    """告警规则"""

    rule_id: str
    name: str
    severity: AlertSeverity
    condition: Callable[[dict[str, Any]], bool]
    message_template: str
    labels: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    cooldown_seconds: int = 300  # 冷却时间
    notification_channels: list[str] = field(default_factory=list)
    last_triggered: float | None = None

    def should_trigger(self, metrics: dict[str, Any]) -> bool:
        """检查是否应该触发"""
        if not self.enabled:
            return False

        # 检查冷却时间
        if self.last_triggered:
            elapsed = time.time() - self.last_triggered
            if elapsed < self.cooldown_seconds:
                return False

        # 检查条件
        return self.condition(metrics)

    def trigger(self) -> Alert:
        """触发告警"""
        self.last_triggered = time.time()

        return Alert(
            alert_id=f"{self.rule_id}_{int(time.time())}",
            name=self.name,
            severity=self.severity,
            message=self.message_template,
            labels=self.labels,
            notification_channels=self.notification_channels,
        )


# =============================================================================
# 通知渠道
# =============================================================================


class NotificationChannel:
    """通知渠道基类"""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled

    def send(self, alert: Alert) -> bool:
        """发送通知"""
        if not self.enabled:
            return False
        try:
            return self._send(alert)
        except Exception as e:
            logger.error(f"发送通知失败 ({self.name}): {e}")
            return False

    def _send(self, alert: Alert) -> bool:
        """实际发送方法(子类实现)"""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """邮件通知渠道"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        to_addrs: list[str],
        enabled: bool = True,
    ):
        super().__init__("email", enabled)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs

    def _send(self, alert: Alert) -> bool:
        """发送邮件"""
        try:
            # 构建邮件
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)
            msg["Subject"] = f"[{alert.severity.value}] {alert.name}"

            # 邮件正文
            body = self._format_email_body(alert)
            msg.attach(MIMEText(body, "html", "utf-8"))

            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"✅ 邮件通知已发送: {alert.name}")
            return True

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    def _format_email_body(self, alert: Alert) -> str:
        """格式化邮件正文"""
        return f"""
<html>
<body>
    <h2>🚨 Athena告警通知</h2>
    <table border="1" cellpadding="5" cellspacing="0">
        <tr><td><b>告警名称</b></td><td>{alert.name}</td></tr>
        <tr><td><b>严重程度</b></td><td>{alert.severity.value}</td></tr>
        <tr><td><b>状态</b></td><td>{alert.status.value}</td></tr>
        <tr><td><b>消息</b></td><td>{alert.message}</td></tr>
        <tr><td><b>开始时间</b></td><td>{datetime.fromtimestamp(alert.started_at).strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        <tr><td><b>持续时间</b></td><td>{alert.age_seconds():.0f}秒</td></tr>
    </table>

    <h3>详细信息</h3>
    <pre>{json.dumps(alert.details, indent=2, ensure_ascii=False)}</pre>

    <h3>标签</h3>
    <pre>{json.dumps(alert.labels, indent=2, ensure_ascii=False)}</pre>
</body>
</html>
        """


class WebhookNotificationChannel(NotificationChannel):
    """Webhook通知渠道(支持企业微信、钉钉、Slack等)"""

    def __init__(self, webhook_url: str, message_type: str = "markdown", enabled: bool = True):
        super().__init__("webhook", enabled)
        self.webhook_url = webhook_url
        self.message_type = message_type

    def _send(self, alert: Alert) -> bool:
        """发送Webhook"""
        try:
            payload = self._format_payload(alert)

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"✅ Webhook通知已发送: {alert.name}")
            return True

        except Exception as e:
            logger.error(f"发送Webhook失败: {e}")
            return False

    def _format_payload(self, alert: Alert) -> dict[str, Any]:
        """格式化Webhook负载"""
        # 通用格式
        return {
            "msgtype": self.message_type,
            "markdown": {
                "title": f"[{alert.severity.value}] {alert.name}",
                "text": self._format_markdown(alert),
            },
        }

    def _format_markdown(self, alert: Alert) -> str:
        """格式化Markdown消息"""
        details_md = "\n".join([f"- **{k}**: {v}" for k, v in alert.details.items()])

        labels_md = ", ".join([f"{k}={v}" for k, v in alert.labels.items()])

        return f"""
# 🚨 Athena告警通知

**告警名称**: {alert.name}
**严重程度**: {alert.severity.value}
**状态**: {alert.status.value}

## 消息
{alert.message}

## 详细信息
{details_md}

## 标签
{labels_md}

## 时间信息
- **开始时间**: {datetime.fromtimestamp(alert.started_at).strftime('%Y-%m-%d %H:%M:%S')}
- **持续时间**: {alert.age_seconds():.0f}秒
        """


class LogNotificationChannel(NotificationChannel):
    """日志通知渠道(用于测试和调试)"""

    def __init__(self, enabled: bool = True):
        super().__init__("log", enabled)

    def _send(self, alert: Alert) -> bool:
        """记录到日志"""
        logger.warning(f"🚨 告警: [{alert.severity.value}] {alert.name} - {alert.message}")
        if alert.details:
            logger.warning(f"详细信息: {json.dumps(alert.details)}")
        return True


# =============================================================================
# 告警聚合器
# =============================================================================


class AlertAggregator:
    """告警聚合器 - 避免告警风暴"""

    def __init__(self, aggregation_window_seconds: int = 60, max_alerts_per_window: int = 10):
        """
        初始化告警聚合器

        Args:
            aggregation_window_seconds: 聚合窗口时间(秒)
            max_alerts_per_window: 每个窗口最大告警数
        """
        self.aggregation_window = aggregation_window_seconds
        self.max_alerts = max_alerts_per_window
        self.alert_windows: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_alerts_per_window)
        )

    def should_send(self, alert: Alert) -> bool:
        """
        判断是否应该发送告警

        Args:
            alert: 告警对象

        Returns:
            是否应该发送
        """
        key = f"{alert.name}_{alert.severity.value}"
        window = self.alert_windows[key]

        # 清理过期告警
        cutoff_time = time.time() - self.aggregation_window
        while window and window[0] < cutoff_time:
            window.popleft()

        # 检查是否超过阈值
        if len(window) >= self.max_alerts:
            logger.debug(f"告警被聚合: {alert.name} (窗口内已有{len(window)}个告警)")
            return False

        # 记录当前告警
        window.append(time.time())
        return True


# =============================================================================
# 增强告警系统
# =============================================================================


class EnhancedAlertingSystem:
    """增强告警系统"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化告警系统

        Args:
            config: 配置字典
        """
        config = config or {}

        # 告警规则
        self.rules: dict[str, AlertRule] = {}

        # 活跃告警
        self.active_alerts: dict[str, Alert] = {}

        # 已解决告警历史
        self.alert_history: deque = deque(maxlen=10000)

        # 通知渠道
        self.notification_channels: list[NotificationChannel] = []

        # 告警聚合器
        self.aggregator = AlertAggregator(
            aggregation_window_seconds=config.get("aggregation_window_seconds", 60),
            max_alerts_per_window=config.get("max_alerts_per_window", 10),
        )

        # 线程池(用于异步发送通知)
        self.executor = ThreadPoolExecutor(max_workers=5)

        # 数据目录
        self.data_dir = Path(config.get("data_dir", "data/monitoring/alerts"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 运行状态
        self._running = False

        logger.info("✅ 增强告警系统初始化完成")

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        self.rules[rule.rule_id] = rule
        logger.info(f"📋 添加告警规则: {rule.name} ({rule.severity.value})")

    def remove_rule(self, rule_id: str) -> None:
        """移除告警规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"🗑️ 移除告警规则: {rule_id}")

    def add_notification_channel(self, channel: NotificationChannel) -> None:
        """添加通知渠道"""
        self.notification_channels.append(channel)
        logger.info(f"📢 添加通知渠道: {channel.name}")

    def evaluate_rules(self, metrics: dict[str, Any]) -> Any:
        """
        评估所有告警规则

        Args:
            metrics: 当前指标
        """
        for rule in self.rules.values():
            try:
                if rule.should_trigger(metrics):
                    alert = rule.trigger()
                    self.fire_alert(alert)
            except Exception as e:
                logger.error(f"评估告警规则失败 ({rule.name}): {e}")

    def fire_alert(self, alert: Alert) -> Any:
        """
        触发告警

        Args:
            alert: 告警对象
        """
        # 检查是否已存在相同告警
        existing_key = f"{alert.name}_{alert.severity.value}"
        if existing_key in self.active_alerts:
            # 更新现有告警
            existing = self.active_alerts[existing_key]
            existing.details.update(alert.details)
            logger.debug(f"更新现有告警: {alert.name}")
            return

        # 检查告警聚合
        if not self.aggregator.should_send(alert):
            return

        # 添加到活跃告警
        self.active_alerts[existing_key] = alert

        logger.warning(f"🚨 告警触发: [{alert.severity.value}] {alert.name} - {alert.message}")

        # 异步发送通知
        self._send_notifications(alert)

    def resolve_alert(self, alert_id: str) -> Any:
        """解决告警"""
        for key, alert in self.active_alerts.items():
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = time.time()

                # 移动到历史记录
                self.alert_history.append(alert.to_dict())
                del self.active_alerts[key]

                logger.info(f"✅ 告警已解决: {alert.name}")
                return

        logger.warning(f"未找到告警: {alert_id}")

    def acknowledge_alert(self, alert_id: str, user: str) -> Any:
        """确认告警"""
        for alert in self.active_alerts.values():
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = user
                alert.acknowledged_at = time.time()
                logger.info(f"👤 告警已确认: {alert.name} by {user}")
                return

    def silence_alert(self, alert_id: str, duration_seconds: int) -> Any:
        """静默告警"""
        for alert in self.active_alerts.values():
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.SILENCED
                alert.silence_until = time.time() + duration_seconds
                logger.info(f"🔇 告警已静默: {alert.name} ({duration_seconds}秒)")
                return

    def _send_notifications(self, alert: Alert) -> Any:
        """发送通知(异步)"""

        def send() -> Any:
            for channel in self.notification_channels:
                try:
                    if channel.send(alert):
                        alert.notification_sent = True
                        alert.notification_channels.append(channel.name)
                except Exception as e:
                    logger.error(f"发送通知失败 ({channel.name}): {e}")

        # 在线程池中异步执行
        self.executor.submit(send)

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """获取活跃告警"""
        return [alert.to_dict() for alert in self.active_alerts.values()]

    def get_alert_history(
        self, limit: int = 100, severity: AlertSeverity | None = None
    ) -> list[dict[str, Any]]:
        """
        获取告警历史

        Args:
            limit: 返回数量限制
            severity: 严重程度过滤

        Returns:
            告警历史列表
        """
        history = list(self.alert_history)

        # 按严重程度过滤
        if severity:
            history = [a for a in history if a["severity"] == severity.value]

        # 按时间倒序排序
        history.sort(key=lambda x: x["started_at"], reverse=True)

        return history[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """获取告警统计"""
        total_history = list(self.alert_history)

        # 按严重程度统计
        severity_counts = defaultdict(int)
        for alert in total_history:
            severity_counts[alert["severity"]] += 1

        # 按状态统计
        status_counts = defaultdict(int)
        for alert in self.active_alerts.values():
            status_counts[alert.status.value] += 1

        # 计算MTTR (Mean Time To Resolve)
        resolved_alerts = [a for a in total_history if a["resolved_at"]]
        if resolved_alerts:
            mttr_seconds = sum(a["resolved_at"] - a["started_at"] for a in resolved_alerts) / len(
                resolved_alerts
            )
        else:
            mttr_seconds = 0

        return {
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(total_history),
            "severity_distribution": dict(severity_counts),
            "status_distribution": dict(status_counts),
            "mttr_seconds": round(mttr_seconds, 2),
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "notification_channels": [c.name for c in self.notification_channels if c.enabled],
        }

    def export_report(self, output_path: Path | None = None) -> Any:
        """
        导出告警报告

        Args:
            output_path: 输出路径,None表示使用默认路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"alert_report_{timestamp}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "active_alerts": self.get_active_alerts(),
            "recent_history": self.get_alert_history(limit=100),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 告警报告已导出: {output_path}")

    def cleanup(self) -> Any:
        """清理资源"""
        logger.info("🧹 正在清理告警系统...")
        self.executor.shutdown(wait=True)
        logger.info("✅ 告警系统清理完成")


# =============================================================================
# 默认告警规则
# =============================================================================


def create_default_rules() -> list[AlertRule]:
    """创建默认告警规则"""
    return [
        # 工具调用失败率过高
        AlertRule(
            rule_id="tool_error_rate_high",
            name="工具调用失败率过高",
            severity=AlertSeverity.P1_HIGH,
            condition=lambda m: m.get("error_rate", 0) > 5.0,
            message_template="工具调用失败率超过5%,当前值: {error_rate:.2f}%",
            labels={"category": "tool", "type": "error_rate"},
        ),
        # 工具响应时间过长
        AlertRule(
            rule_id="tool_latency_high",
            name="工具响应时间过长",
            severity=AlertSeverity.P2_MEDIUM,
            condition=lambda m: m.get("p95_latency_ms", 0) > 1000,
            message_template="工具P95延迟超过1000ms,当前值: {p95_latency_ms:.0f}ms",
            labels={"category": "tool", "type": "latency"},
        ),
        # 内存使用率过高
        AlertRule(
            rule_id="memory_usage_high",
            name="内存使用率过高",
            severity=AlertSeverity.P1_HIGH,
            condition=lambda m: m.get("system.memory_usage_percent", 0) > 85,
            message_template="内存使用率超过85%,当前值: {system.memory_usage_percent:.1f}%",
            labels={"category": "system", "type": "memory"},
        ),
        # CPU使用率过高
        AlertRule(
            rule_id="cpu_usage_high",
            name="CPU使用率过高",
            severity=AlertSeverity.P2_MEDIUM,
            condition=lambda m: m.get("system.cpu_usage_percent", 0) > 80,
            message_template="CPU使用率超过80%,当前值: {system.cpu_usage_percent:.1f}%",
            labels={"category": "system", "type": "cpu"},
        ),
        # 缓存命中率过低
        AlertRule(
            rule_id="cache_hit_rate_low",
            name="缓存命中率过低",
            severity=AlertSeverity.P3_LOW,
            condition=lambda m: m.get("cache_hit_rate", 100) < 70,
            message_template="缓存命中率低于70%,当前值: {cache_hit_rate:.1f}%",
            labels={"category": "cache", "type": "hit_rate"},
        ),
        # 队列积压过多
        AlertRule(
            rule_id="queue_backlog_high",
            name="队列积压过多",
            severity=AlertSeverity.P2_MEDIUM,
            condition=lambda m: m.get("queue_size", 0) > 1000,
            message_template="队列积压超过1000,当前值: {queue_size}",
            labels={"category": "queue", "type": "backlog"},
        ),
        # 批处理吞吐量过低
        AlertRule(
            rule_id="batch_throughput_low",
            name="批处理吞吐量过低",
            severity=AlertSeverity.P3_LOW,
            condition=lambda m: m.get("throughput", 1000) < 10,
            message_template="批处理吞吐量低于10 texts/sec,当前值: {throughput:.1f}",
            labels={"category": "performance", "type": "throughput"},
        ),
    ]


# =============================================================================
# 全局单例
# =============================================================================

_alerting_system: EnhancedAlertingSystem | None = None


def get_alerting_system() -> EnhancedAlertingSystem:
    """获取告警系统单例"""
    global _alerting_system
    if _alerting_system is None:
        _alerting_system = EnhancedAlertingSystem()

        # 添加默认规则
        for rule in create_default_rules():
            _alerting_system.add_rule(rule)

        # 添加日志通知渠道(默认启用)
        _alerting_system.add_notification_channel(LogNotificationChannel())

    return _alerting_system
