#!/usr/bin/env python3
"""
专利行动层监控告警系统
Patent Action Layer Monitoring and Alert System

提供详细的性能指标监控、智能告警、实时状态追踪、
异常检测和自动化恢复等功能。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import json
import logging
import smtplib
import statistics
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from enum import Enum
from typing import Any

import psutil
import requests

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """告警严重程度"""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class MetricType(str, Enum):
    """指标类型"""
    COUNTER = 'counter'
    GAUGE = 'gauge'
    HISTOGRAM = 'histogram'
    TIMER = 'timer'


@dataclass
class MetricValue:
    """指标值"""
    name: str
    value: int | float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """告警"""
    id: str
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ''
    metrics: dict[str, float] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: datetime | None = None
    acknowledged: bool = False
    acknowledged_by: str = ''
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """健康检查"""
    name: str
    status: str  # 'healthy', 'unhealthy', 'degraded'
    message: str = ''
    last_check: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class AlertChannel(ABC):
    """告警通道基类"""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """发送告警"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass


class EmailAlertChannel(AlertChannel):
    """邮件告警通道"""

    def __init__(self, smtp_config: dict[str, Any], recipients: list[str]):
        self.smtp_config = smtp_config
        self.recipients = recipients
        self.logger = logging.getLogger(f"{__name__}.EmailAlertChannel")

    async def send_alert(self, alert: Alert) -> bool:
        """发送邮件告警"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.smtp_config['from']
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = f"[{alert.severity.upper()}] {alert.name}"

            body = f"""
告警名称: {alert.name}
严重程度: {alert.severity}
时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
来源: {alert.source}

消息:
{alert.message}

相关指标:
{json.dumps(alert.metrics, indent=2)}

详细信息:
{json.dumps(alert.metadata, indent=2)}
            """

            msg.attach(MimeText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config.get('port', 587))
            if self.smtp_config.get('use_tls', True):
                server.starttls()

            if 'username' in self.smtp_config:
                server.login(self.smtp_config['username'], self.smtp_config['password'])

            server.send_message(msg)
            server.quit()

            self.logger.info(f"邮件告警发送成功: {alert.name}")
            return True

        except Exception as e:
            self.logger.error(f"邮件告警发送失败: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """测试SMTP连接"""
        try:
            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config.get('port', 587))
            if self.smtp_config.get('use_tls', True):
                server.starttls()
            if 'username' in self.smtp_config:
                server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.quit()
            return True
        except Exception as e:
            self.logger.error(f"SMTP连接测试失败: {str(e)}")
            return False


class WebhookAlertChannel(AlertChannel):
    """Webhook告警通道"""

    def __init__(self, webhook_url: str, headers: dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.logger = logging.getLogger(f"{__name__}.WebhookAlertChannel")

    async def send_alert(self, alert: Alert) -> bool:
        """发送Webhook告警"""
        try:
            payload = {
                'alert_id': alert.id,
                'name': alert.name,
                'severity': alert.severity,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'source': alert.source,
                'metrics': alert.metrics,
                'metadata': alert.metadata,
                'resolved': alert.resolved
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )

            response.raise_for_status()
            self.logger.info(f"Webhook告警发送成功: {alert.name}")
            return True

        except Exception as e:
            self.logger.error(f"Webhook告警发送失败: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """测试Webhook连接"""
        try:
            response = requests.post(
                self.webhook_url,
                json={'test': True},
                headers=self.headers,
                timeout=5
            )
            return response.status_code < 400
        except Exception:
            return False


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = defaultdict(float)
        self.histograms: dict[str, list[float] = defaultdict(list)
        self.timers: dict[str, list[float] = defaultdict(list)
        self.logger = logging.getLogger(f"{__name__}.MetricsCollector")

    def increment_counter(self, name: str, value: int = 1, tags: dict[str, str] = None):
        """增加计数器"""
        key = self._make_key(name, tags)
        self.counters[key] += value
        self._record_metric(MetricValue(name, self.counters[key], MetricType.COUNTER, tags=tags))

    def set_gauge(self, name: str, value: float, tags: dict[str, str] = None):
        """设置仪表盘值"""
        key = self._make_key(name, tags)
        self.gauges[key] = value
        self._record_metric(MetricValue(name, value, MetricType.GAUGE, tags=tags))

    def record_histogram(self, name: str, value: float, tags: dict[str, str] = None):
        """记录直方图值"""
        key = self._make_key(name, tags)
        self.histograms[key].append(value)
        # 保留最近1000个值
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
        self._record_metric(MetricValue(name, value, MetricType.HISTOGRAM, tags=tags))

    def record_timer(self, name: str, duration: float, tags: dict[str, str] = None):
        """记录计时器值"""
        key = self._make_key(name, tags)
        self.timers[key].append(duration)
        # 保留最近1000个值
        if len(self.timers[key]) > 1000:
            self.timers[key] = self.timers[key][-1000:]
        self._record_metric(MetricValue(name, duration, MetricType.TIMER, tags=tags))

    def _make_key(self, name: str, tags: dict[str, str] = None) -> str:
        """生成指标键"""
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name},{tag_str}"

    def _record_metric(self, metric: MetricValue):
        """记录指标"""
        key = self._make_key(metric.name, metric.tags)
        self.metrics[key].append(metric)

    def get_metric_stats(self, name: str, tags: dict[str, str] = None, duration_minutes: int = 5) -> dict[str, Any]:
        """获取指标统计"""
        key = self._make_key(name, tags)

        if key not in self.metrics:
            return {}

        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [
            m for m in self.metrics[key]
            if m.timestamp > cutoff_time
        ]

        if not recent_metrics:
            return {}

        values = [m.value for m in recent_metrics]

        stats = {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': statistics.mean(values),
            'sum': sum(values)
        }

        if len(values) > 1:
            stats['median'] = statistics.median(values)
            stats['stdev'] = statistics.stdev(values)
            stats['p95'] = statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values)
            stats['p99'] = statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values)

        return stats


class RuleEngine:
    """规则引擎"""

    def __init__(self):
        self.rules: list[dict[str, Any] = []
        self.logger = logging.getLogger(f"{__name__}.RuleEngine")

    def add_rule(self, rule: dict[str, Any]):
        """添加规则"""
        self.rules.append(rule)
        self.logger.info(f"添加告警规则: {rule['name']}")

    def evaluate_rules(self, metrics_collector: MetricsCollector) -> list[Alert]:
        """评估规则"""
        alerts = []

        for rule in self.rules:
            try:
                alert = self._evaluate_rule(rule, metrics_collector)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                self.logger.error(f"规则评估失败 {rule['name']}: {str(e)}")

        return alerts

    def _evaluate_rule(self, rule: dict[str, Any], metrics_collector: MetricsCollector) -> Alert | None:
        """评估单个规则"""
        metric_name = rule['metric']
        condition = rule['condition']
        threshold = rule['threshold']
        duration_minutes = rule.get('duration', 5)

        # 获取指标统计
        stats = metrics_collector.get_metric_stats(metric_name, duration_minutes=duration_minutes)

        if not stats:
            return None

        # 评估条件
        triggered = False
        current_value = 0

        if condition == 'gt':
            current_value = stats['max']
            triggered = current_value > threshold
        elif condition == 'lt':
            current_value = stats['min']
            triggered = current_value < threshold
        elif condition == 'avg_gt':
            current_value = stats['avg']
            triggered = current_value > threshold
        elif condition == 'avg_lt':
            current_value = stats['avg']
            triggered = current_value < threshold

        if triggered:
            return Alert(
                id=f"alert_{int(time.time())}_{hash(rule['name']) % 10000}",
                name=rule['name'],
                severity=AlertSeverity(rule.get('severity', 'warning')),
                message=f"{rule['message']} (当前值: {current_value:.2f}, 阈值: {threshold})",
                source=rule.get('source', 'system'),
                metrics={metric_name: current_value},
                metadata={
                    'rule': rule,
                    'threshold': threshold,
                    'current_value': current_value,
                    'condition': condition
                }
            )

        return None


class AnomalyDetector:
    """异常检测器"""

    def __init__(self):
        self.baseline_stats: dict[str, dict[str, float] = {}
        self.logger = logging.getLogger(f"{__name__}.AnomalyDetector")

    def update_baseline(self, metric_name: str, stats: dict[str, float]):
        """更新基线"""
        self.baseline_stats[metric_name] = {
            'avg': stats.get('avg', 0),
            'stdev': stats.get('stdev', 0),
            'min': stats.get('min', 0),
            'max': stats.get('max', 0),
            'updated_at': datetime.now().isoformat()
        }

    def detect_anomalies(self, metric_name: str, current_value: float) -> Alert | None:
        """检测异常"""
        if metric_name not in self.baseline_stats:
            return None

        baseline = self.baseline_stats[metric_name]
        avg = baseline['avg']
        stdev = baseline['stdev']

        if stdev == 0:
            return None

        # 使用3-sigma规则检测异常
        z_score = abs(current_value - avg) / stdev

        if z_score > 3:  # 异常阈值
            severity = AlertSeverity.CRITICAL if z_score > 5 else AlertSeverity.WARNING

            return Alert(
                id=f"anomaly_{int(time.time())}_{hash(metric_name) % 10000}",
                name=f"异常检测 - {metric_name}",
                severity=severity,
                message=f"指标 {metric_name} 出现异常 (当前值: {current_value:.2f}, 基线: {avg:.2f}±{stdev:.2f}, Z-score: {z_score:.2f})",
                source='anomaly_detector',
                metrics={metric_name: current_value},
                metadata={
                    'baseline_avg': avg,
                    'baseline_stdev': stdev,
                    'z_score': z_score
                }
            )

        return None


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.health_checks: dict[str, Callable] = {}
        self.logger = logging.getLogger(f"{__name__}.HealthChecker")

    def register_health_check(self, name: str, check_func: Callable):
        """注册健康检查"""
        self.health_checks[name] = check_func
        self.logger.info(f"注册健康检查: {name}")

    async def run_health_checks(self) -> dict[str, HealthCheck]:
        """运行健康检查"""
        results = {}

        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                response_time = time.time() - start_time

                if isinstance(result, dict):
                    health_check = HealthCheck(
                        name=name,
                        status=result.get('status', 'healthy'),
                        message=result.get('message', ''),
                        response_time=response_time,
                        details=result.get('details', {})
                    )
                else:
                    health_check = HealthCheck(
                        name=name,
                        status='healthy' if result else 'unhealthy',
                        response_time=response_time
                    )

                results[name] = health_check

            except Exception as e:
                self.logger.error(f"健康检查失败 {name}: {str(e)}")
                results[name] = HealthCheck(
                    name=name,
                    status='unhealthy',
                    message=str(e)
                )

        return results


class RecoveryAction:
    """恢复动作"""

    def __init__(self, name: str, action_func: Callable, conditions: list[str]):
        self.name = name
        self.action_func = action_func
        self.conditions = conditions
        self.logger = logging.getLogger(f"{__name__}.RecoveryAction.{name}")

    async def execute(self, alert: Alert) -> bool:
        """执行恢复动作"""
        try:
            # 检查条件是否满足
            if not self._check_conditions(alert):
                self.logger.info(f"恢复动作条件不满足: {self.name}")
                return False

            self.logger.info(f"执行恢复动作: {self.name}")

            if asyncio.iscoroutinefunction(self.action_func):
                result = await self.action_func(alert)
            else:
                result = self.action_func(alert)

            self.logger.info(f"恢复动作执行完成: {self.name}, 结果: {result}")
            return True

        except Exception as e:
            self.logger.error(f"恢复动作执行失败 {self.name}: {str(e)}")
            return False

    def _check_conditions(self, alert: Alert) -> bool:
        """检查执行条件"""
        for condition in self.conditions:
            if condition == 'critical_only' and alert.severity != AlertSeverity.CRITICAL:
                return False
            elif condition == 'unacknowledged_only' and alert.acknowledged:
                return False

        return True


class MonitoringSystem:
    """监控系统主类"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.rule_engine = RuleEngine()
        self.anomaly_detector = AnomalyDetector()
        self.health_checker = HealthChecker()
        self.alert_channels: list[AlertChannel] = []
        self.recovery_actions: list[RecoveryAction] = []
        self.active_alerts: dict[str, Alert] = {}
        self.monitoring_active = False
        self.logger = logging.getLogger(f"{__name__}.MonitoringSystem")

        # 注册默认规则
        self._register_default_rules()

    def add_alert_channel(self, channel: AlertChannel):
        """添加告警通道"""
        self.alert_channels.append(channel)
        self.logger.info(f"添加告警通道: {type(channel).__name__}")

    def add_recovery_action(self, action: RecoveryAction):
        """添加恢复动作"""
        self.recovery_actions.append(action)
        self.logger.info(f"添加恢复动作: {action.name}")

    def start_monitoring(self, interval_seconds: int = 30):
        """启动监控"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        threading.Thread(target=self._monitoring_loop, args=(interval_seconds,), daemon=True).start()
        self.logger.info('监控系统已启动')

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        self.logger.info('监控系统已停止')

    def _monitoring_loop(self, interval_seconds: int):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 收集系统指标
                self._collect_system_metrics()

                # 评估告警规则
                alerts = self.rule_engine.evaluate_rules(self.metrics_collector)

                # 异常检测
                anomaly_alerts = self._detect_anomalies()

                # 合并告警
                all_alerts = alerts + anomaly_alerts

                # 处理告警
                asyncio.run(self._process_alerts(all_alerts))

                # 清理过期告警
                self._cleanup_expired_alerts()

            except Exception as e:
                self.logger.error(f"监控循环错误: {str(e)}")

            time.sleep(interval_seconds)

    def _collect_system_metrics(self):
        """收集系统指标"""
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics_collector.set_gauge('system_cpu_usage', cpu_percent)

        # 内存指标
        memory = psutil.virtual_memory()
        self.metrics_collector.set_gauge('system_memory_usage', memory.percent)
        self.metrics_collector.set_gauge('system_memory_available_gb', memory.available / (1024**3))

        # 磁盘指标
        disk = psutil.disk_usage('/')
        self.metrics_collector.set_gauge('system_disk_usage', disk.percent)
        self.metrics_collector.set_gauge('system_disk_free_gb', disk.free / (1024**3))

        # 网络指标
        network = psutil.net_io_counters()
        if network:
            self.metrics_collector.set_gauge('system_network_bytes_sent', network.bytes_sent)
            self.metrics_collector.set_gauge('system_network_bytes_recv', network.bytes_recv)

        # 进程指标
        process_count = len(psutil.pids())
        self.metrics_collector.set_gauge('system_process_count', process_count)

    def _detect_anomalies(self) -> list[Alert]:
        """检测异常"""
        anomalies = []

        # 检测CPU使用率异常
        cpu_stats = self.metrics_collector.get_metric_stats('system_cpu_usage')
        if cpu_stats:
            self.anomaly_detector.update_baseline('system_cpu_usage', cpu_stats)
            anomaly = self.anomaly_detector.detect_anomalies('system_cpu_usage', cpu_stats.get('avg', 0))
            if anomaly:
                anomalies.append(anomaly)

        # 检测内存使用率异常
        memory_stats = self.metrics_collector.get_metric_stats('system_memory_usage')
        if memory_stats:
            self.anomaly_detector.update_baseline('system_memory_usage', memory_stats)
            anomaly = self.anomaly_detector.detect_anomalies('system_memory_usage', memory_stats.get('avg', 0))
            if anomaly:
                anomalies.append(anomaly)

        return anomalies

    async def _process_alerts(self, alerts: list[Alert]):
        """处理告警"""
        for alert in alerts:
            # 检查是否为活跃告警
            if alert.id in self.active_alerts:
                continue

            # 添加到活跃告警
            self.active_alerts[alert.id] = alert

            # 发送告警
            await self._send_alert(alert)

            # 执行恢复动作
            await self._execute_recovery_actions(alert)

    async def _send_alert(self, alert: Alert):
        """发送告警"""
        for channel in self.alert_channels:
            try:
                await channel.send_alert(alert)
            except Exception as e:
                self.logger.error(f"告警发送失败 {type(channel).__name__}: {str(e)}")

    async def _execute_recovery_actions(self, alert: Alert):
        """执行恢复动作"""
        for action in self.recovery_actions:
            try:
                await action.execute(alert)
            except Exception as e:
                self.logger.error(f"恢复动作执行失败 {action.name}: {str(e)}")

    def _cleanup_expired_alerts(self):
        """清理过期告警"""
        expired_time = datetime.now() - timedelta(hours=24)
        expired_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.timestamp < expired_time
        ]

        for alert_id in expired_alerts:
            del self.active_alerts[alert_id]

    def _register_default_rules(self):
        """注册默认告警规则"""
        self.rule_engine.add_rule({
            'name': 'CPU使用率过高',
            'metric': 'system_cpu_usage',
            'condition': 'avg_gt',
            'threshold': 80.0,
            'duration': 5,
            'severity': 'warning',
            'message': 'CPU使用率持续过高',
            'source': 'system_monitor'
        })

        self.rule_engine.add_rule({
            'name': '内存使用率过高',
            'metric': 'system_memory_usage',
            'condition': 'avg_gt',
            'threshold': 85.0,
            'duration': 5,
            'severity': 'warning',
            'message': '内存使用率持续过高',
            'source': 'system_monitor'
        })

        self.rule_engine.add_rule({
            'name': '磁盘使用率过高',
            'metric': 'system_disk_usage',
            'condition': 'gt',
            'threshold': 90.0,
            'duration': 1,
            'severity': 'critical',
            'message': '磁盘使用率过高',
            'source': 'system_monitor'
        })

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.active_alerts[alert_id].acknowledged_by = acknowledged_by
            self.logger.info(f"告警已确认: {alert_id} by {acknowledged_by}")
            return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.active_alerts[alert_id].resolved_at = datetime.now()
            self.logger.info(f"告警已解决: {alert_id}")
            return True
        return False

    async def run_health_checks(self) -> dict[str, HealthCheck]:
        """运行健康检查"""
        return await self.health_checker.run_health_checks()

    def get_monitoring_status(self) -> dict[str, Any]:
        """获取监控状态"""
        return {
            'monitoring_active': self.monitoring_active,
            'active_alerts_count': len(self.active_alerts),
            'alert_channels_count': len(self.alert_channels),
            'recovery_actions_count': len(self.recovery_actions),
            'rules_count': len(self.rule_engine.rules),
            'active_alerts': [
                {
                    'id': alert.id,
                    'name': alert.name,
                    'severity': alert.severity,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved
                }
                for alert in self.active_alerts.values()
            ]
        }

    def record_business_metric(self, metric_name: str, value: float, tags: dict[str, str] = None):
        """记录业务指标"""
        self.metrics_collector.set_gauge(f"business_{metric_name}", value, tags)

    def record_task_metric(self, task_type: str, metric_name: str, value: float, tags: dict[str, str] = None):
        """记录任务指标"""
        full_tags = {'task_type': task_type}
        if tags:
            full_tags.update(tags)
        self.metrics_collector.set_gauge(f"task_{metric_name}", value, full_tags)


# 测试代码
async def test_monitoring_system():
    """测试监控系统"""
    monitoring = MonitoringSystem()

    # 添加邮件告警通道（示例配置）
    # email_config = {
    #     "host": "smtp.gmail.com",
    #     "port": 587,
    #     "use_tls": True,
    #     "from": "alerts@example.com",
    #     "username": "user@example.com",
    #     "password": "password"
    # }
    # email_channel = EmailAlertChannel(email_config, ["admin@example.com"])
    # monitoring.add_alert_channel(email_channel)

    # 添加Webhook告警通道
    webhook_channel = WebhookAlertChannel('http://localhost:9000/api/v1/alerts/webhook')
    monitoring.add_alert_channel(webhook_channel)

    # 注册健康检查
    def check_database():
        return {'status': 'healthy', 'message': '数据库连接正常'}

    def check_api_service():
        return {'status': 'healthy', 'message': 'API服务正常'}

    monitoring.health_checker.register_health_check('database', check_database)
    monitoring.health_checker.register_health_check('api_service', check_api_service)

    # 添加恢复动作
    def restart_service(alert):
        logger.info(f"模拟重启服务，告警: {alert.name}")
        return True

    recovery_action = RecoveryAction('restart_service', restart_service, ['critical_only'])
    monitoring.add_recovery_action(recovery_action)

    # 启动监控
    monitoring.start_monitoring(interval_seconds=10)

    # 记录一些测试指标
    for i in range(20):
        monitoring.record_business_metric('user_count', 100 + i * 10)
        monitoring.record_task_metric('patent_analysis', 'duration', 30 + i * 2)
        await asyncio.sleep(1)

    # 运行健康检查
    health_results = await monitoring.run_health_checks()
    logger.info(f"健康检查结果: {health_results}")

    # 获取监控状态
    status = monitoring.get_monitoring_status()
    logger.info(f"监控状态: {json.dumps(status, indent=2, default=str)}")

    # 停止监控
    monitoring.stop_monitoring()


if __name__ == '__main__':
    asyncio.run(test_monitoring_system())
