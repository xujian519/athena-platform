from __future__ import annotations
"""
性能分析工具 - Performance Monitoring

适配终端环境的性能监控和分析:
1. 实时性能指标收集
2. 终端友好的输出格式(表格、进度条、颜色)
3. 告警系统(终端通知)
4. 性能报告生成
5. 趋势分析
"""

import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"  # 计数器(只增不减)
    GAUGE = "gauge"  # 仪表(可增可减)
    HISTOGRAM = "histogram"  # 直方图(分布)
    SUMMARY = "summary"  # 摘要(统计)


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重


class Colors:
    """终端颜色代码"""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"

    @staticmethod
    def colorize(text: str, color: str) -> str:
        """给文本添加颜色"""
        return f"{color}{text}{Colors.RESET}"

    @staticmethod
    def red(text: str) -> str:
        return Colors.colorize(text, Colors.RED)

    @staticmethod
    def green(text: str) -> str:
        return Colors.colorize(text, Colors.GREEN)

    @staticmethod
    def yellow(text: str) -> str:
        return Colors.colorize(text, Colors.YELLOW)

    @staticmethod
    def blue(text: str) -> str:
        return Colors.colorize(text, Colors.BLUE)

    @staticmethod
    def cyan(text: str) -> str:
        return Colors.colorize(text, Colors.CYAN)

    @staticmethod
    def bold(text: str) -> str:
        return Colors.colorize(text, Colors.BOLD)


@dataclass
class Metric:
    """指标"""

    name: str  # 指标名称
    type: MetricType  # 指标类型
    value: float = 0.0  # 当前值
    timestamp: float = field(default_factory=time.time)  # 时间戳
    labels: dict[str, str] = field(default_factory=dict)  # 标签
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    # 对于histogram类型
    samples: list[float] = field(default_factory=list)  # 样本列表

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        if self.type == MetricType.HISTOGRAM:
            return {
                "name": self.name,
                "type": self.type.value,
                "count": len(self.samples),
                "sum": sum(self.samples),
                "avg": sum(self.samples) / len(self.samples) if self.samples else 0,
                "min": min(self.samples) if self.samples else 0,
                "max": max(self.samples) if self.samples else 0,
                "labels": self.labels,
            }
        else:
            return {
                "name": self.name,
                "type": self.type.value,
                "value": self.value,
                "labels": self.labels,
            }


@dataclass
class Alert:
    """告警"""

    alert_id: str  # 告警ID
    level: AlertLevel  # 级别
    metric_name: str  # 指标名称
    message: str  # 消息
    current_value: float  # 当前值
    threshold: float  # 阈值
    timestamp: float = field(default_factory=time.time)  # 时间戳
    resolved: bool = False  # 是否已解决
    resolved_at: float | None = None  # 解决时间

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "alert_id": self.alert_id,
            "level": self.level.value,
            "metric_name": self.metric_name,
            "message": self.message,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
        }

    def format_terminal(self) -> str:
        """格式化为终端输出"""
        level_colors = {
            AlertLevel.INFO: Colors.blue,
            AlertLevel.WARNING: Colors.yellow,
            AlertLevel.ERROR: Colors.red,
            AlertLevel.CRITICAL: Colors.BOLD + Colors.red,
        }

        color = level_colors.get(self.level, Colors.WHITE)
        timestamp_str = datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")

        return (
            f"{color('[' + self.level.value.upper() + ']')} "
            f"{timestamp_str} | "
            f"{self.metric_name}: {self.message} "
            f"(当前: {self.current_value:.2f}, 阈值: {self.threshold:.2f})"
        )


class PerformanceMonitor:
    """
    性能监控器

    收集和管理性能指标
    """

    def __init__(self, retention_seconds: int = 3600):
        """
        初始化监控器

        Args:
            retention_seconds: 数据保留时间(秒)
        """
        self.metrics: dict[str, Metric] = {}
        self.metric_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        self.retention_seconds = retention_seconds
        self.lock = threading.RLock()

        # 告警配置
        self.alert_rules: dict[str, dict[str, Any]] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []

        self._cleaner_thread: threading.Thread | None = None
        self._running = False

        logger.info("✅ 性能监控器初始化完成")

    def register_metric(
        self, name: str, metric_type: MetricType, labels: dict[str, str] | None = None
    ) -> None:
        """
        注册指标

        Args:
            name: 指标名称
            metric_type: 指标类型
            labels: 标签
        """
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = Metric(name=name, type=metric_type, labels=labels or {})
                logger.debug(f"注册指标: {name} ({metric_type.value})")

    def increment(
        self, name: str, value: float = 1.0, labels: dict[str, str] | None = None
    ) -> None:
        """
        增加计数器

        Args:
            name: 指标名称
            value: 增量
            labels: 标签
        """
        with self.lock:
            if name not in self.metrics:
                self.register_metric(name, MetricType.COUNTER, labels)

            metric = self.metrics[name]
            if metric.type != MetricType.COUNTER:
                logger.warning(f"指标 {name} 不是计数器类型")
                return

            metric.value += value
            metric.timestamp = time.time()
            self._record_history(name, metric.value)

    def set(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """
        设置仪表值

        Args:
            name: 指标名称
            value: 值
            labels: 标签
        """
        with self.lock:
            if name not in self.metrics:
                self.register_metric(name, MetricType.GAUGE, labels)

            metric = self.metrics[name]
            if metric.type != MetricType.GAUGE:
                logger.warning(f"指标 {name} 不是仪表类型")
                return

            metric.value = value
            metric.timestamp = time.time()
            self._record_history(name, metric.value)

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """
        观察直方图样本

        Args:
            name: 指标名称
            value: 样本值
            labels: 标签
        """
        with self.lock:
            if name not in self.metrics:
                self.register_metric(name, MetricType.HISTOGRAM, labels)

            metric = self.metrics[name]
            if metric.type != MetricType.HISTOGRAM:
                logger.warning(f"指标 {name} 不是直方图类型")
                return

            metric.samples.append(value)
            metric.timestamp = time.time()

    def time(self, name: str) -> Callable:
        """
        计时装饰器/上下文管理器

        Usage:
            @monitor.time("operation")
            def my_function():
                ...

            with monitor.time("operation"):
                ...
        """

        class Timer:
            def __init__(self, monitor: PerformanceMonitor, metric_name: str):
                self.monitor = monitor
                self.metric_name = metric_name
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                self.monitor.observe(self.metric_name, duration)

            def __call__(self, func):
                def wrapper(*args, **kwargs) -> Any:
                    start = time.time()
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        duration = time.time() - start
                        self.monitor.observe(self.metric_name, duration)

                return wrapper

        return Timer(self, name)

    def _record_history(self, name: str, value: float) -> None:
        """记录历史数据"""
        self.metric_history[name].append((time.time(), value))

    def get_metric(self, name: str) -> Metric | None:
        """获取指标"""
        return self.metrics.get(name)

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """获取所有指标"""
        with self.lock:
            return {name: metric.to_dict() for name, metric in self.metrics.items()}

    def get_metric_history(
        self, name: str, since: float | None = None
    ) -> list[tuple[float, float]]:
        """获取指标历史"""
        if since is None:
            since = time.time() - self.retention_seconds

        history = self.metric_history.get(name, deque())
        return [(t, v) for t, v in history if t >= since]

    def set_alert_rule(
        self,
        metric_name: str,
        condition: str,  # "gt", "lt", "eq", "gte", "lte"
        threshold: float,
        level: AlertLevel = AlertLevel.WARNING,
    ) -> None:
        """
        设置告警规则

        Args:
            metric_name: 指标名称
            condition: 条件 ("gt" >, "lt" <, "eq" ==, "gte" >=, "lte" <=)
            threshold: 阈值
            level: 告警级别
        """
        self.alert_rules[metric_name] = {
            "condition": condition,
            "threshold": threshold,
            "level": level,
        }
        logger.info(f"设置告警规则: {metric_name} {condition} {threshold} ({level.value})")

    def check_alerts(self) -> list[Alert]:
        """检查并生成告警"""
        new_alerts = []

        for metric_name, rule in self.alert_rules.items():
            metric = self.metrics.get(metric_name)
            if not metric:
                continue

            value = metric.value
            threshold = rule["threshold"]
            condition = rule["condition"]
            level = rule["level"]

            triggered = False
            if (condition == "gt" and value > threshold) or (condition == "lt" and value < threshold) or (condition == "eq" and value == threshold) or (condition == "gte" and value >= threshold) or (condition == "lte" and value <= threshold):
                triggered = True

            if triggered:
                # 检查是否已有活跃告警
                alert_key = f"{metric_name}_{condition}_{threshold}"
                if alert_key not in self.active_alerts:
                    alert = Alert(
                        alert_id=alert_key,
                        level=level,
                        metric_name=metric_name,
                        message=f"值 {condition} 阈值",
                        current_value=value,
                        threshold=threshold,
                    )
                    self.active_alerts[alert_key] = alert
                    self.alert_history.append(alert)
                    new_alerts.append(alert)
                    logger.warning(f"告警触发: {alert.format_terminal()}")

        return new_alerts


class TerminalReporter:
    """
    终端报告器

    以终端友好的格式输出性能数据
    """

    def __init__(self, monitor: PerformanceMonitor):
        """
        初始化报告器

        Args:
            monitor: 性能监控器
        """
        self.monitor = monitor

    def print_metrics_table(
        self, filter_type: MetricType | None = None, limit: int = 20
    ) -> None:
        """
        打印指标表格

        Args:
            filter_type: 过滤类型
            limit: 最大显示数量
        """
        metrics = self.monitor.get_all_metrics()

        # 过滤和排序
        if filter_type:
            metrics = {k: v for k, v in metrics.items() if v["type"] == filter_type.value}

        # 按时间戳排序
        sorted_metrics = sorted(
            metrics.items(), key=lambda x: x[1].get("timestamp", 0), reverse=True
        )[:limit]

        if not sorted_metrics:
            print(Colors.yellow("没有指标数据"))
            return

        # 打印表头
        print(Colors.bold("\n┌─────────────────────────────────────────────────────────────────┐"))
        print(Colors.bold("│                        性能指标仪表板                            │"))
        print(Colors.bold("├──────────────────┬──────────┬─────────────┬────────────────────┤"))
        print(Colors.bold("│ 指标名称         │ 类型     │ 值          │ 标签               │"))
        print(Colors.bold("├──────────────────┼──────────┼─────────────┼────────────────────┤"))

        # 打印数据行
        for name, metric in sorted_metrics:
            metric_type = metric["type"]
            labels = metric.get("labels", {})

            if metric_type == "counter":
                value_str = Colors.green(f"{metric['value']:.0f}")
            elif metric_type == "gauge":
                value_str = Colors.cyan(f"{metric['value']:.2f}")
            elif metric_type == "histogram":
                value_str = Colors.yellow(f"n={metric['count']}, avg={metric['avg']:.2f}")
            else:
                value_str = str(metric.get("value", "N/A"))

            labels_str = ", ".join(f"{k}={v}" for k, v in labels.items())[:20]
            if len(labels_str) == 20:
                labels_str += "..."

            name_str = name[:16].ljust(16)
            type_str = metric_type[:8].ljust(8)

            print(f"│ {name_str} │ {type_str} │ {value_str:<11} │ {labels_str:<18} │")

        print(Colors.bold("└──────────────────┴──────────┴─────────────┴────────────────────┘"))

    def print_alerts(self, limit: int = 10) -> None:
        """
        打印活跃告警

        Args:
            limit: 最大显示数量
        """
        alerts = list(self.monitor.active_alerts.values())[-limit:]

        if not alerts:
            print(Colors.green("\n✓ 没有活跃告警"))
            return

        print(Colors.bold("\n┌─────────────────────────────────────────────────────────────────┐"))
        print(Colors.bold("│                         活跃告警                                 │"))
        print(Colors.bold("├─────────────────────────────────────────────────────────────────┤"))

        for alert in alerts:
            print(f"│ {alert.format_terminal():<73} │")

        print(Colors.bold("└─────────────────────────────────────────────────────────────────┘"))

    def print_metric_summary(self, metric_name: str) -> None:
        """
        打印指标摘要

        Args:
            metric_name: 指标名称
        """
        metric = self.monitor.get_metric(metric_name)

        if not metric:
            print(Colors.yellow(f"指标不存在: {metric_name}"))
            return

        print(Colors.bold(f"\n[{metric_name}]"))
        print(f"  类型: {metric.type.value}")
        print(f"  当前值: {metric.value}")

        if metric.type == MetricType.HISTOGRAM and metric.samples:
            print(f"  样本数: {len(metric.samples)}")
            print(f"  平均值: {sum(metric.samples) / len(metric.samples):.2f}")
            print(f"  最小值: {min(metric.samples):.2f}")
            print(f"  最大值: {max(metric.samples):.2f}")

        # 打印最近趋势
        history = self.monitor.get_metric_history(metric_name, since=time.time() - 300)
        if history:
            values = [v for t, v in history]
            print(f"  5分钟平均: {sum(values) / len(values):.2f}")
            print(f"  5分钟最小: {min(values):.2f}")
            print(f"  5分钟最大: {max(values):.2f}")

    def print_live_dashboard(self, interval: float = 1.0, duration: float = 60.0) -> None:
        """
        打印实时仪表板

        Args:
            interval: 刷新间隔(秒)
            duration: 运行时长(秒)
        """
        start_time = time.time()
        iterations = 0

        try:
            while time.time() - start_time < duration:
                iterations += 1

                # 清屏
                os.system("clear" if os.name == "posix" else "cls")

                # 打印标题
                print(Colors.bold(Colors.cyan("\n  Athena 性能监控 - 实时仪表板")))
                print(
                    Colors.blue(
                        f"  运行时间: {time.time() - start_time:.1f}s | "
                        f"刷新次数: {iterations} | "
                        f"时间: {datetime.now().strftime('%H:%M:%S')}"
                    )
                )
                print(Colors.blue("  " + "─" * 70))

                # 打印指标
                self.print_metrics_table(limit=15)

                # 检查并打印告警
                self.monitor.check_alerts()
                self.print_alerts(limit=5)

                # 等待下次刷新
                time.sleep(interval)

        except KeyboardInterrupt:
            print(Colors.yellow("\n\n仪表板已停止"))

    def generate_report(self, output_file: str | None = None) -> dict[str, Any]:
        """
        生成性能报告

        Args:
            output_file: 输出文件路径(可选)

        Returns:
            报告数据
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "metrics": self.monitor.get_all_metrics(),
            "alerts": [alert.to_dict() for alert in self.monitor.alert_history[-100:]],
            "summary": {
                "total_metrics": len(self.monitor.metrics),
                "active_alerts": len(self.monitor.active_alerts),
                "total_alerts": len(self.monitor.alert_history),
            },
        }

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(Colors.green(f"报告已保存到: {output_file}"))

        return report


# 全局单例
_performance_monitor: PerformanceMonitor | None = None
_terminal_reporter: TerminalReporter | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器单例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()

        # 设置默认告警规则
        _performance_monitor.set_alert_rule("response_time", "gt", 5.0, AlertLevel.WARNING)
        _performance_monitor.set_alert_rule("error_rate", "gt", 0.05, AlertLevel.ERROR)
        _performance_monitor.set_alert_rule("memory_usage", "gt", 0.9, AlertLevel.CRITICAL)

    return _performance_monitor


def get_terminal_reporter() -> TerminalReporter:
    """获取终端报告器单例"""
    global _terminal_reporter
    if _terminal_reporter is None:
        _terminal_reporter = TerminalReporter(get_performance_monitor())
    return _terminal_reporter


# 便捷函数
def track_time(metric_name: str) -> Callable:
    """追踪函数执行时间的装饰器"""
    monitor = get_performance_monitor()
    return monitor.time(metric_name)


def increment_counter(name: str, value: float = 1.0) -> None:
    """增加计数器"""
    get_performance_monitor().increment(name, value)


def set_gauge(name: str, value: float) -> None:
    """设置仪表值"""
    get_performance_monitor().set(name, value)


def observe_histogram(name: str, value: float) -> None:
    """观察直方图样本"""
    get_performance_monitor().observe(name, value)


def print_dashboard() -> None:
    """打印当前仪表板"""
    get_terminal_reporter().print_metrics_table()
    get_terminal_reporter().print_alerts()


def show_live_dashboard(interval: float = 1.0, duration: float = 60.0) -> None:
    """显示实时仪表板"""
    get_terminal_reporter().print_live_dashboard(interval, duration)


def generate_report(output_file: str | None = None) -> dict[str, Any]:
    """生成性能报告"""
    return get_terminal_reporter().generate_report(output_file)
