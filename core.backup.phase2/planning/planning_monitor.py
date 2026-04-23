#!/usr/bin/env python3
from __future__ import annotations
"""
规划系统性能监控
Planning System Performance Monitor

实时监控规划系统的性能指标,提供分析和优化建议

作者: 小诺·双鱼座
版本: v1.0.0 "性能监控"
创建时间: 2025-12-17
"""

import json
import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标"""

    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class PlanningEvent:
    """规划事件"""

    event_type: str
    planner_id: str
    plan_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """性能告警"""

    alert_type: str
    severity: str  # info, warning, critical
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    threshold: float = 0.0
    current_value: float = 0.0
    suggestions: list[str] = field(default_factory=list)


class PlanningMonitor:
    """规划系统性能监控器"""

    def __init__(self, max_history=10000):
        # 性能指标存储
        self.metrics_history = defaultdict(lambda: deque(maxlen=max_history))

        # 事件日志
        self.events_log = deque(maxlen=max_history)

        # 告警列表
        self.active_alerts = []
        self.alert_history = deque(maxlen=1000)

        # 阈值配置
        self.thresholds = {
            "planning_time": 5.0,  # 规划时间阈值(秒)
            "memory_usage": 80.0,  # 内存使用率阈值(%)
            "cpu_usage": 90.0,  # CPU使用率阈值(%)
            "error_rate": 5.0,  # 错误率阈值(%)
            "concurrent_plans": 10,  # 并发规划数阈值
            "queue_size": 100,  # 队列大小阈值
        }

        # 统计数据
        self.stats = {
            "total_plans": 0,
            "successful_plans": 0,
            "failed_plans": 0,
            "avg_planning_time": 0.0,
            "peak_memory": 0.0,
            "peak_cpu": 0.0,
        }

        # 性能回调函数
        self.callbacks = defaultdict(list)

        # 监控线程
        self.monitoring_active = False
        self.monitor_thread = None

        # 规划器性能追踪
        self.planner_stats = defaultdict(
            lambda: {
                "plans_created": 0,
                "avg_duration": 0.0,
                "success_rate": 1.0,
                "last_activity": None,
                "total_duration": 0.0,
            }
        )

        print("📊 规划系统性能监控器初始化完成")

    def start_monitoring(self, interval=5) -> None:
        """启动性能监控"""
        if self.monitoring_active:
            print("⚠️ 监控已在运行中")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self.monitor_thread.start()
        print(f"✅ 性能监控已启动 (间隔: {interval}秒)")

    def stop_monitoring(self) -> Any:
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("⏹️ 性能监控已停止")

    def _monitor_loop(self, interval) -> None:
        """监控循环"""
        while self.monitoring_active:
            try:
                # 收集系统指标
                self._collect_system_metrics()

                # 检查告警
                self._check_alerts()

                # 清理过期数据
                self._cleanup_expired_data()

                time.sleep(interval)
            except Exception as e:
                logger.error(f"监控循环出错: {e}")

    def _collect_system_metrics(self) -> Any:
        """收集系统性能指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self.record_metric("cpu_usage", cpu_percent, "%", {"component": "system"})

        # 内存使用
        memory = psutil.virtual_memory()
        self.record_metric("memory_usage", memory.percent, "%", {"component": "system"})

        # 当前进程信息
        process = psutil.Process()
        self.record_metric(
            "process_memory", process.memory_info().rss / 1024 / 1024, "MB"
        )  # TODO: 确保除数不为零
        self.record_metric("process_cpu", process.cpu_percent(), "%")

    def record_metric(self, name: str, value: float, unit: str, tags: dict[str, str] | None = None) -> Any:
        """记录性能指标"""
        metric = PerformanceMetric(name=name, value=value, unit=unit, tags=tags or {})
        self.metrics_history[name].append(metric)

        # 触发回调
        for callback in self.callbacks[name]:
            try:
                callback(metric)
            except Exception as e:
                logger.warning(f"回调执行失败: {e}")

    def record_planning_event(self, event: PlanningEvent) -> Any:
        """记录规划事件"""
        self.events_log.append(event)

        # 更新统计
        self.stats["total_plans"] += 1

        if event.success:
            self.stats["successful_plans"] += 1
        else:
            self.stats["failed_plans"] += 1

        # 更新规划器统计
        planner_stats = self.planner_stats[event.planner_id]
        planner_stats["plans_created"] += 1
        planner_stats["total_duration"] += event.duration
        planner_stats["avg_duration"] = (
            planner_stats["total_duration"] / planner_stats["plans_created"]
        )
        planner_stats["last_activity"] = event.timestamp

        # 更新成功率
        total_events = sum(1 for e in self.events_log if e.planner_id == event.planner_id)
        successful_events = sum(
            1 for e in self.events_log if e.planner_id == event.planner_id and e.success
        )
        planner_stats["success_rate"] = (
            successful_events / total_events if total_events > 0 else 1.0
        )

        # 更新平均规划时间
        if self.stats["total_plans"] > 0:
            total_duration = sum(e.duration for e in self.events_log)
            self.stats["avg_planning_time"] = total_duration / self.stats["total_plans"]

    def start_planning_timer(self, planner_id: str, plan_id: str) -> str:
        """开始规划计时"""
        timer_id = f"{planner_id}_{plan_id}_{int(time.time() * 1000)}"
        return timer_id

    def end_planning_timer(
        self, timer_id: str, planner_id: str, plan_id: str, success: bool | None = None, error: str | None = None
    ) -> float:
        """结束规划计时"""
        try:
            # 提取开始时间
            start_time = float(timer_id.split("_")[-1]) / 1000
            duration = time.time() - start_time

            # 记录事件
            event = PlanningEvent(
                event_type="planning_completed",
                planner_id=planner_id,
                plan_id=plan_id,
                duration=duration,
                success=success,
                error=error,
            )
            self.record_planning_event(event)

            # 记录规划时间指标
            self.record_metric(
                "planning_time", duration, "s", {"planner": planner_id, "success": str(success)}
            )

            return duration
        except Exception:
            return 0.0

    def _check_alerts(self) -> Any:
        """检查性能告警"""
        current_time = datetime.now()

        # 检查各项指标
        for metric_name, threshold in self.thresholds.items():
            if metric_name in self.metrics_history:
                recent_metrics = [
                    m
                    for m in self.metrics_history[metric_name]
                    if current_time - m.timestamp < timedelta(minutes=5)
                ]

                if recent_metrics:
                    sum(m.value for m in recent_metrics) / len(recent_metrics)
                    latest_value = recent_metrics[-1].value

                    # 检查是否超过阈值
                    if latest_value > threshold:
                        self._create_alert(
                            alert_type=f"threshold_exceeded_{metric_name}",
                            severity="warning" if latest_value < threshold * 1.5 else "critical",
                            message=f"{metric_name} 超过阈值: {latest_value:.2f}{recent_metrics[-1].unit} > {threshold}",
                            current_value=latest_value,
                            threshold=threshold,
                        )

    def _create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float = 0.0,
        threshold: float = 0.0,
    ):
        """创建告警"""
        # 检查是否已有相同类型的活跃告警
        for alert in self.active_alerts:
            if alert.alert_type == alert_type:
                # 更新现有告警
                alert.current_value = current_value
                alert.timestamp = datetime.now()
                return

        # 创建新告警
        alert = PerformanceAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold=threshold,
            suggestions=self._get_alert_suggestions(alert_type),
        )

        self.active_alerts.append(alert)
        self.alert_history.append(alert)

        # 输出告警
        alert_icon = "⚠️" if severity == "warning" else "🚨"
        print(f"{alert_icon} 性能告警: {message}")

    def _get_alert_suggestions(self, alert_type: str) -> list[str]:
        """获取告警建议"""
        suggestions = {
            "threshold_exceeded_planning_time": [
                "考虑优化规划算法",
                "增加缓存机制",
                "减少不必要的步骤",
            ],
            "threshold_exceeded_memory_usage": ["检查内存泄漏", "优化数据结构", "考虑使用内存池"],
            "threshold_exceeded_cpu_usage": [
                "优化计算密集型操作",
                "考虑使用多线程/异步",
                "分析CPU热点",
            ],
            "threshold_exceeded_error_rate": ["检查错误日志", "增强错误处理", "实施重试机制"],
        }
        return suggestions.get(alert_type, ["联系系统管理员"])

    def _cleanup_expired_data(self) -> Any:
        """清理过期数据"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # 清理旧的指标
        for metric_name, metrics in self.metrics_history.items():
            self.metrics_history[metric_name] = deque(
                [m for m in metrics if m.timestamp > cutoff_time], maxlen=metrics.maxlen
            )

        # 清理活跃告警(超过1小时未更新的)
        self.active_alerts = [
            alert
            for alert in self.active_alerts
            if datetime.now() - alert.timestamp < timedelta(hours=1)
        ]

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        current_time = datetime.now()
        last_5min = current_time - timedelta(minutes=5)
        current_time - timedelta(hours=1)

        summary = {
            "timestamp": current_time.isoformat(),
            "statistics": self.stats.copy(),
            "planner_performance": dict(self.planner_stats),
            "recent_metrics": {},
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
        }

        # 最近5分钟的指标
        for metric_name, metrics in self.metrics_history.items():
            recent = [m for m in metrics if m.timestamp > last_5min]
            if recent:
                summary["recent_metrics"][metric_name] = {
                    "current": recent[-1].value,
                    "average": sum(m.value for m in recent) / len(recent),
                    "min": min(m.value for m in recent),
                    "max": max(m.value for m in recent),
                    "unit": recent[-1].unit,
                }

        return summary

    def get_planner_performance(self, planner_id: str) -> dict[str, Any]:
        """获取特定规划器的性能数据"""
        planner_events = [e for e in self.events_log if e.planner_id == planner_id]

        if not planner_events:
            return {"error": "没有找到该规划器的数据"}

        # 计算性能指标
        total_plans = len(planner_events)
        successful_plans = sum(1 for e in planner_events if e.success)
        failed_plans = total_plans - successful_plans

        durations = [e.duration for e in planner_events if e.duration > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "planner_id": planner_id,
            "total_plans": total_plans,
            "successful_plans": successful_plans,
            "failed_plans": failed_plans,
            "success_rate": successful_plans / total_plans if total_plans > 0 else 0,
            "avg_duration": avg_duration,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "last_activity": max(e.timestamp for e in planner_events).isoformat(),
            "recent_trend": (
                self._calculate_trend(durations[-10:]) if len(durations) >= 2 else "stable"
            ),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return "stable"

        # 简单的线性回归判断趋势
        x = list(range(len(values)))
        avg_x = sum(x) / len(x)
        avg_y = sum(values) / len(values)

        numerator = sum((x[i] - avg_x) * (values[i] - avg_y) for i in range(len(values)))
        denominator = sum((x[i] - avg_x) ** 2 for i in range(len(values)))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"

    def register_callback(
        self, metric_name: str, callback: Callable[[PerformanceMetric], None]
    ) -> Any:
        """注册性能指标回调"""
        self.callbacks[metric_name].append(callback)

    def export_metrics(self, filename: str, format: str = "json") -> Any:
        """导出性能指标"""
        data = {
            "export_time": datetime.now().isoformat(),
            "summary": self.get_performance_summary(),
            "metrics_history": {
                name: [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "value": m.value,
                        "unit": m.unit,
                        "tags": m.tags,
                    }
                    for m in metrics
                ]
                for name, metrics in self.metrics_history.items()
            },
            "events_log": [
                {
                    "event_type": e.event_type,
                    "planner_id": e.planner_id,
                    "plan_id": e.plan_id,
                    "timestamp": e.timestamp.isoformat(),
                    "duration": e.duration,
                    "success": e.success,
                    "error": e.error,
                }
                for e in list(self.events_log)[-1000:]  # 最近1000条
            ],
        }

        filepath = Path(filename)
        if format.lower() == "json":
            with open(filepath.with_suffix(".json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            # 导出CSV格式的摘要数据
            import csv

            with open(filepath.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Current Value", "Average", "Min", "Max", "Unit"])
                for name, metrics in data.get("recent_metrics").items():
                    writer.writerow(
                        [
                            name,
                            metrics["current"],
                            metrics["average"],
                            metrics["min"],
                            metrics["max"],
                            metrics["unit"],
                        ]
                    )

        print(f"✅ 性能指标已导出到: {filepath}")

    def generate_report(self) -> str:
        """生成性能报告"""
        summary = self.get_performance_summary()

        report = f"""
# 规划系统性能报告
生成时间: {summary['timestamp']}

## 📊 总体统计
- 总规划数: {summary['statistics']['total_plans']}
- 成功规划: {summary['statistics']['successful_plans']}
- 失败规划: {summary['statistics']['failed_plans']}
- 平均规划时间: {summary['statistics']['avg_planning_time']:.2f}秒
- 当前活跃告警: {summary['active_alerts']}个

## 🔧 最近性能指标
"""

        for metric_name, metrics in summary["recent_metrics"].items():
            report += f"### {metric_name}\n"
            report += f"- 当前值: {metrics['current']:.2f}{metrics['unit']}\n"
            report += f"- 平均值: {metrics['average']:.2f}{metrics['unit']}\n"
            report += f"- 最小值: {metrics['min']:.2f}{metrics['unit']}\n"
            report += f"- 最大值: {metrics['max']:.2f}{metrics['unit']}\n\n"

        report += "\n## 🎯 规划器性能\n"
        for planner_id, stats in summary["planner_performance"].items():
            report += f"### {planner_id}\n"
            report += f"- 创建计划数: {stats['plans_created']}\n"
            report += f"- 平均耗时: {stats['avg_duration']:.2f}秒\n"
            report += f"- 成功率: {stats['success_rate']*100:.1f}%\n\n"

        if self.active_alerts:
            report += "\n## 🚨 活跃告警\n"
            for alert in self.active_alerts:
                report += f"- {alert.severity.upper()}: {alert.message}\n"
                if alert.suggestions:
                    for suggestion in alert.suggestions:
                        report += f"  - 建议: {suggestion}\n"
                report += "\n"

        return report


# 全局监控实例(延迟初始化)
monitor = None


def get_monitor() -> Any | None:
    """获取全局监控实例(延迟初始化)"""
    global monitor
    if monitor is None:
        monitor = PlanningMonitor()
    return monitor


# 便捷函数
def start_monitoring(interval=5) -> None:
    """启动全局监控"""
    get_monitor().start_monitoring(interval)


def stop_monitoring() -> Any:
    """停止全局监控"""
    if monitor is not None:
        monitor.stop_monitoring()


def get_performance_summary() -> Any | None:
    """获取性能摘要"""
    return get_monitor().get_performance_summary()
