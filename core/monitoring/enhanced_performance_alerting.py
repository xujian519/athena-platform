#!/usr/bin/env python3
from __future__ import annotations
"""
增强性能监控告警系统
Enhanced Performance Monitoring and Alerting System

实时监控系统性能指标,自动检测异常并触发告警

核心功能:
1. 实时性能指标监控
2. 智能阈值告警
3. 趋势异常检测
4. 告警通知和记录
5. 性能报告生成

作者: 小诺AI团队
创建时间: 2025-01-09
"""

import json
import logging
import smtplib
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """告警严重程度"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 紧急


@dataclass
class AlertRule:
    """告警规则"""

    rule_id: str
    name: str
    metric_name: str
    condition: Callable[[float], bool]
    severity: AlertSeverity
    message_template: str
    enabled: bool = True
    cooldown_seconds: int = 300  # 冷却时间
    last_triggered: datetime | None = None


@dataclass
class Alert:
    """告警"""

    alert_id: str
    rule_id: str
    severity: AlertSeverity
    message: str
    metric_value: float
    triggered_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class AlertChannel(ABC):
    """告警通道抽象基类"""

    @abstractmethod
    def send_alert(self, alert: Alert) -> bool:
        """发送告警"""
        pass


class ConsoleAlertChannel(AlertChannel):
    """控制台告警通道"""

    def send_alert(self, alert: Alert) -> bool:
        """在控制台输出告警"""
        try:
            severity_symbol = {
                AlertSeverity.INFO: "ℹ️",
                AlertSeverity.WARNING: "⚠️",
                AlertSeverity.ERROR: "❌",
                AlertSeverity.CRITICAL: "🚨",
            }

            symbol = severity_symbol.get(alert.severity, "⚠️")
            timestamp = alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n{symbol} [{alert.severity.value.upper()}] {alert.message}")
            print(f"   时间: {timestamp}")
            print(f"   指标值: {alert.metric_value}")
            print(f"   规则ID: {alert.rule_id}")

            return True
        except Exception as e:
            logger.error(f"控制台告警失败: {e}")
            return False


class FileAlertChannel(AlertChannel):
    """文件告警通道"""

    def __init__(self, log_file: str = "alerts.log"):
        self.log_file = Path(log_file)
        self.lock = threading.Lock()

    def send_alert(self, alert: Alert) -> bool:
        """写入告警到文件"""
        try:
            with self.lock, open(self.log_file, "a", encoding="utf-8") as f:
                timestamp = alert.triggered_at.isoformat()
                log_entry = {
                    "alert_id": alert.alert_id,
                    "rule_id": alert.rule_id,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "metric_value": alert.metric_value,
                    "triggered_at": timestamp,
                    "metadata": alert.metadata,
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            return True
        except Exception as e:
            logger.error(f"文件告警失败: {e}")
            return False


class EmailAlertChannel(AlertChannel):
    """邮件告警通道"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        from_email: str,
        to_emails: list[str],
        username: str | None = None,
        password: str | None = None,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_emails = to_emails
        self.username = username
        self.password = password

    def send_alert(self, alert: Alert) -> bool:
        """发送邮件告警"""
        try:
            msg = MIMEText(alert.message)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.rule_id}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.username and self.password:
                    server.starttls()
                    server.login(self.username, self.password)
                server.send_message(msg)

            return True
        except Exception as e:
            logger.error(f"邮件告警失败: {e}")
            return False


class PerformanceAlertingSystem:
    """性能监控告警系统"""

    def __init__(self, config_path: str | None = None):
        """
        初始化性能监控告警系统

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.alert_rules: list[AlertRule] = []
        self.alert_history: list[Alert] = []
        self.alert_channels: list[AlertChannel] = []

        # 线程锁
        self.rules_lock = threading.RLock()
        self.history_lock = threading.RLock()

        # 初始化
        self._setup_default_rules()
        self._setup_default_channels()

        logger.info("✅ 性能监控告警系统初始化完成")

    def _load_config(self, config_path: str,) -> dict:
        """加载配置"""
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")

        return {
            "alerting": {"enabled": True, "max_history": 10000, "channels": ["console", "file"]}
        }

    def _setup_default_rules(self) -> None:
        """设置默认告警规则"""
        default_rules = [
            # 向量搜索告警
            AlertRule(
                rule_id="slow_vector_search",
                name="向量搜索过慢",
                metric_name="vector_search_time",
                condition=lambda x: x > 2.0,
                severity=AlertSeverity.WARNING,
                message_template="向量搜索耗时过长: {value:.2f}秒",
            ),
            # 内存使用告警
            AlertRule(
                rule_id="high_memory_usage",
                name="内存使用率过高",
                metric_name="memory_usage",
                condition=lambda x: x > 0.8,
                severity=AlertSeverity.CRITICAL,
                message_template="内存使用率过高: {value:.1%}",
            ),
            # CPU使用告警
            AlertRule(
                rule_id="high_cpu_usage",
                name="CPU使用率过高",
                metric_name="cpu_usage",
                condition=lambda x: x > 0.9,
                severity=AlertSeverity.WARNING,
                message_template="CPU使用率过高: {value:.1%}",
            ),
            # 缓存命中率告警
            AlertRule(
                rule_id="low_cache_hit_rate",
                name="缓存命中率过低",
                metric_name="cache_hit_rate",
                condition=lambda x: x < 0.3,
                severity=AlertSeverity.WARNING,
                message_template="缓存命中率过低: {value:.1%}",
            ),
            # 响应时间告警
            AlertRule(
                rule_id="slow_response_time",
                name="API响应时间过慢",
                metric_name="response_time_p95",
                condition=lambda x: x > 3.0,
                severity=AlertSeverity.ERROR,
                message_template="API响应时间过慢: {value:.2f}秒",
            ),
            # 错误率告警
            AlertRule(
                rule_id="high_error_rate",
                name="错误率过高",
                metric_name="error_rate",
                condition=lambda x: x > 0.05,
                severity=AlertSeverity.CRITICAL,
                message_template="错误率过高: {value:.1%}",
            ),
            # NLP推理时间告警
            AlertRule(
                rule_id="slow_nlp_inference",
                name="NLP推理过慢",
                metric_name="nlp_inference_time",
                condition=lambda x: x > 1.5,
                severity=AlertSeverity.WARNING,
                message_template="NLP推理过慢: {value:.2f}秒",
            ),
        ]

        self.alert_rules.extend(default_rules)
        logger.info(f"✅ 已加载 {len(default_rules)} 个默认告警规则")

    def _setup_default_channels(self) -> None:
        """设置默认告警通道"""
        # 控制台通道(始终启用)
        self.alert_channels.append(ConsoleAlertChannel())

        # 文件通道
        log_file = self.config.get("alerting", {}).get("log_file", "alerts.log")
        self.alert_channels.append(FileAlertChannel(log_file))

        logger.info(f"✅ 已设置 {len(self.alert_channels)} 个告警通道")

    def add_alert_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        with self.rules_lock:
            self.alert_rules.append(rule)
            logger.info(f"✅ 添加告警规则: {rule.name}")

    def remove_alert_rule(self, rule_id: str) -> bool:
        """移除告警规则"""
        with self.rules_lock:
            for i, rule in enumerate(self.alert_rules):
                if rule.rule_id == rule_id:
                    self.alert_rules.pop(i)
                    logger.info(f"✅ 移除告警规则: {rule_id}")
                    return True
            return False

    def add_alert_channel(self, channel: AlertChannel) -> None:
        """添加告警通道"""
        self.alert_channels.append(channel)
        logger.info(f"✅ 添加告警通道: {channel.__class__.__name__}")

    def check_metric(
        self, metric_name: str, metric_value: float, metadata: dict | None = None
    ) -> None:
        """
        检查指标并触发告警

        Args:
            metric_name: 指标名称
            metric_value: 指标值
            metadata: 额外元数据
        """
        if not self.config.get("alerting", {}).get("enabled", True):
            return

        with self.rules_lock:
            for rule in self.alert_rules:
                if not rule.enabled:
                    continue

                if rule.metric_name != metric_name:
                    continue

                # 检查冷却时间
                if rule.last_triggered:
                    time_since_last = (datetime.now() - rule.last_triggered).total_seconds()
                    if time_since_last < rule.cooldown_seconds:
                        continue

                # 检查条件
                if rule.condition(metric_value):
                    self._trigger_alert(rule, metric_value, metadata)

    def _trigger_alert(
        self, rule: AlertRule, metric_value: float, metadata: dict | None = None
    ) -> None:
        """触发告警"""
        # 生成告警
        alert = Alert(
            alert_id=f"{rule.rule_id}_{int(time.time())}",
            rule_id=rule.rule_id,
            severity=rule.severity,
            message=rule.message_template.format(value=metric_value),
            metric_value=metric_value,
            metadata=metadata or {},
        )

        # 记录告警历史
        with self.history_lock:
            self.alert_history.append(alert)

            # 限制历史记录数量
            max_history = self.config.get("alerting", {}).get("max_history", 10000)
            if len(self.alert_history) > max_history:
                self.alert_history = self.alert_history[-max_history:]

        # 更新规则触发时间
        rule.last_triggered = datetime.now()

        # 发送告警
        for channel in self.alert_channels:
            try:
                channel.send_alert(alert)
            except Exception as e:
                logger.error(f"告警发送失败: {e}")

    def get_alert_history(
        self, limit: int = 100, severity: AlertSeverity | None = None
    ) -> list[Alert]:
        """获取告警历史"""
        with self.history_lock:
            history = self.alert_history

            if severity:
                history = [a for a in history if a.severity == severity]

            return history[-limit:] if limit > 0 else history

    def get_alert_stats(self) -> dict[str, Any]:
        """获取告警统计"""
        with self.history_lock:
            total = len(self.alert_history)

            # 按严重程度统计
            by_severity = {}
            for severity in AlertSeverity:
                count = sum(1 for a in self.alert_history if a.severity == severity)
                by_severity[severity.value] = count

            # 最近24小时告警
            yesterday = datetime.now() - timedelta(hours=24)
            recent = sum(1 for a in self.alert_history if a.triggered_at > yesterday)

            return {
                "total_alerts": total,
                "by_severity": by_severity,
                "last_24h": recent,
                "enabled_rules": sum(1 for r in self.alert_rules if r.enabled),
                "total_rules": len(self.alert_rules),
                "active_channels": len(self.alert_channels),
            }

    def clear_history(self) -> None:
        """清空告警历史"""
        with self.history_lock:
            self.alert_history.clear()
            logger.info("🧹 告警历史已清空")

    def generate_report(self, output_file: str | None = None) -> str:
        """生成性能告警报告"""
        stats = self.get_alert_stats()
        recent_alerts = self.get_alert_history(limit=50)

        report_lines = [
            "# 性能监控告警报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 告警统计",
            f"- 总告警数: {stats['total_alerts']}",
            f"- 最近24小时: {stats['last_24h']}",
            f"- 启用规则: {stats['enabled_rules']}/{stats['total_rules']}",
            "",
            "## 按严重程度分布",
        ]

        for severity, count in stats["by_severity"].items():
            report_lines.append(f"- {severity.upper()}: {count}")

        report_lines.extend(["", "## 最近告警", ""])

        for alert in recent_alerts:
            timestamp = alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S")
            report_lines.append(
                f"### [{alert.severity.value.upper()}] {alert.message}\n"
                f"- 时间: {timestamp}\n"
                f"- 规则ID: {alert.rule_id}\n"
                f"- 指标值: {alert.metric_value}\n"
            )

        report_content = "\n".join(report_lines)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"📄 报告已保存到: {output_file}")

        return report_content


# 全局实例
_global_alerting_system: PerformanceAlertingSystem | None = None


def get_alerting_system() -> PerformanceAlertingSystem:
    """获取全局告警系统实例"""
    global _global_alerting_system
    if _global_alerting_system is None:
        _global_alerting_system = PerformanceAlertingSystem()
    return _global_alerting_system


if __name__ == "__main__":
    # 测试告警系统
    system = PerformanceAlertingSystem()

    print("🧪 测试性能监控告警系统...")

    # 模拟触发告警
    system.check_metric("vector_search_time", 2.5)
    system.check_metric("memory_usage", 0.85)
    system.check_metric("cache_hit_rate", 0.25)

    # 查看统计
    stats = system.get_alert_stats()
    print("\n📊 告警统计:")
    print(f"  总告警数: {stats['total_alerts']}")
    print(f"  最近24小时: {stats['last_24h']}")
