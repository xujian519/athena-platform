#!/usr/bin/env python3
from __future__ import annotations
"""
推理引擎性能监控系统
Reasoning Engine Performance Monitoring System

作者: Athena AI团队
版本: v1.0.0
创建时间: 2026-01-26

功能:
1. 实时监控推理引擎性能
2. 收集性能指标
3. 生成性能报告
4. 性能异常检测
5. 优化建议生成
"""

import asyncio
import logging
import statistics
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

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表盘
    HISTOGRAM = "histogram"  # 直方图
    SUMMARY = "summary"  # 摘要


class AlertSeverity(Enum):
    """告警严重程度"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """指标数据"""

    name: str
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class PerformanceAlert:
    """性能告警"""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    suggested_action: Optional[str] = None


@dataclass
class EnginePerformanceReport:
    """引擎性能报告"""

    engine_name: str
    total_requests: int
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    success_rate: float
    error_rate: float
    cache_hit_rate: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # 趋势数据
    response_time_trend: list[float] = field(default_factory=list)
    throughput_trend: list[float] = field(default_factory=list)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(
        self,
        max_history_size: int = 1000,
        alert_check_interval: int = 60,  # 秒
    ):
        self.max_history_size = max_history_size
        self.alert_check_interval = alert_check_interval

        # 指标存储
        self.metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))

        # 引擎性能数据
        self.engine_data: dict[str, dict] = defaultdict(lambda: {
            "response_times": deque(maxlen=100),
            "success_count": 0,
            "error_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        })

        # 告警规则
        self.alert_rules: list[dict] = []
        self.active_alerts: list[PerformanceAlert] = []

        # 监控任务
        self._monitoring_task: asyncio.Task | None = None

        # 回调函数
        self.alert_callbacks: list[Callable] = []

        logger.info("🔍 性能监控系统初始化完成")

    def start_monitoring(self) -> None:
        """启动监控"""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("🚀 性能监控已启动")

    def stop_monitoring(self) -> None:
        """停止监控"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            logger.info("⏹️ 性能监控已停止")

    async def _monitoring_loop(self) -> None:
        """监控循环"""
        while True:
            try:
                await asyncio.sleep(self.alert_check_interval)
                await self._check_alerts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")

    def record_metric(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metric_type: MetricType = MetricType.GAUGE,
    ) -> None:
        """记录指标"""
        metric = MetricData(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metric_type=metric_type,
        )

        self.metrics[name].append(metric)

    def record_engine_call(
        self,
        engine_name: str,
        response_time: float,
        success: bool,
        cache_hit: bool = False,
    ) -> None:
        """记录引擎调用"""
        data = self.engine_data[engine_name]

        # 记录响应时间
        data["response_times"].append(response_time)

        # 记录成功/失败
        if success:
            data["success_count"] += 1
        else:
            data["error_count"] += 1

        # 记录缓存命中
        if cache_hit:
            data["cache_hits"] += 1
        else:
            data["cache_misses"] += 1

        # 同时记录为指标
        self.record_metric(
            f"engine_{engine_name}_response_time",
            response_time,
            {"engine": engine_name},
            MetricType.HISTOGRAM,
        )
        self.record_metric(
            f"engine_{engine_name}_success",
            1.0 if success else 0.0,
            {"engine": engine_name},
            MetricType.GAUGE,
        )

    def add_alert_rule(
        self,
        metric_name: str,
        condition: str,  # "gt", "lt", "eq", "gte", "lte"
        threshold: float,
        severity: AlertSeverity = AlertSeverity.WARNING,
        title: Optional[str] = None,
        suggested_action: Optional[str] = None,
    ) -> None:
        """添加告警规则"""
        self.alert_rules.append({
            "metric_name": metric_name,
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "title": title or f"{metric_name}告警",
            "suggested_action": suggested_action,
        })

        logger.info(f"添加告警规则: {metric_name} {condition} {threshold}")

    async def _check_alerts(self) -> None:
        """检查告警"""
        for rule in self.alert_rules:
            try:
                await self._evaluate_alert_rule(rule)
            except Exception as e:
                logger.error(f"评估告警规则失败: {e}")

    async def _evaluate_alert_rule(self, rule: dict) -> None:
        """评估告警规则"""
        metric_name = rule["metric_name"]
        condition = rule["condition"]
        threshold = rule["threshold"]

        # 获取最新的指标值
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return

        latest_metric = self.metrics[metric_name][-1]
        current_value = latest_metric.value

        # 检查条件
        should_alert = False

        if condition == "gt" and current_value > threshold:
            should_alert = True
        elif condition == "lt" and current_value < threshold:
            should_alert = True
        elif condition == "eq" and current_value == threshold:
            should_alert = True
        elif condition == "gte" and current_value >= threshold:
            should_alert = True
        elif condition == "lte" and current_value <= threshold:
            should_alert = True

        if should_alert:
            await self._trigger_alert(rule, current_value)

    async def _trigger_alert(self, rule: dict, current_value: float) -> None:
        """触发告警"""
        alert = PerformanceAlert(
            alert_id=f"{rule['metric_name']}_{int(time.time())}",
            severity=rule["severity"],
            title=rule["title"],
            description=f"{rule['metric_name']}当前值({current_value:.2f}){rule['condition']}阈值({rule['threshold']})",
            metric_name=rule["metric_name"],
            current_value=current_value,
            threshold=rule["threshold"],
            timestamp=datetime.now(),
            suggested_action=rule.get("suggested_action"),
        )

        self.active_alerts.append(alert)

        logger.warning(
            f"🚨 性能告警: {alert.title} | 当前值: {current_value:.2f} | 阈值: {alert.threshold}"
        )

        # 调用回调函数
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")

    def get_engine_report(self, engine_name: str) -> EnginePerformanceReport:
        """获取引擎性能报告"""
        data = self.engine_data.get(engine_name, {})

        if not data:
            return EnginePerformanceReport(
                engine_name=engine_name,
                total_requests=0,
                avg_response_time=0.0,
                p50_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                success_rate=0.0,
                error_rate=0.0,
            )

        response_times = list(data["response_times"])
        total_requests = data["success_count"] + data["error_count"]

        # 计算百分位数
        if response_times:
            sorted_times = sorted(response_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else p50
            p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else p50
            avg_time = statistics.mean(response_times)
        else:
            p50 = p95 = p99 = avg_time = 0.0

        # 计算成功率
        success_rate = (
            data["success_count"] / total_requests if total_requests > 0 else 0.0
        )
        error_rate = 1.0 - success_rate

        # 计算缓存命中率
        cache_total = data["cache_hits"] + data["cache_misses"]
        cache_hit_rate = (
            data["cache_hits"] / cache_total if cache_total > 0 else None
        )

        return EnginePerformanceReport(
            engine_name=engine_name,
            total_requests=total_requests,
            avg_response_time=avg_time,
            p50_response_time=p50,
            p95_response_time=p95,
            p99_response_time=p99,
            success_rate=success_rate,
            error_rate=error_rate,
            cache_hit_rate=cache_hit_rate,
            response_time_trend=response_times[-50:] if response_times else [],
        )

    def get_system_overview(self) -> dict[str, Any]:
        """获取系统概览"""
        overview = {
            "timestamp": datetime.now().isoformat(),
            "total_engines": len(self.engine_data),
            "total_metrics": sum(len(metrics) for metrics in self.metrics.values()),
            "active_alerts": len(self.active_alerts),
            "engines": {},
        }

        for engine_name in self.engine_data.keys():
            overview["engines"][engine_name] = self.get_engine_report(engine_name).__dict__

        return overview

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": 0,
            "avg_response_time": 0.0,
            "overall_success_rate": 0.0,
            "top_slowest_engines": [],
            "top_error_prone_engines": [],
            "recommendations": [],
        }

        total_requests = 0
        total_success = 0
        total_response_time = 0.0
        engine_times = []
        engine_errors = []

        for engine_name, data in self.engine_data.items():
            requests = data["success_count"] + data["error_count"]
            success = data["success_count"]
            response_times = list(data["response_times"])

            total_requests += requests
            total_success += success

            if response_times:
                avg_time = statistics.mean(response_times)
                total_response_time += avg_time * requests
                engine_times.append((engine_name, avg_time))

            error_rate = data["error_count"] / requests if requests > 0 else 0
            engine_errors.append((engine_name, error_rate, requests))

        # 计算全局指标
        if total_requests > 0:
            summary["total_requests"] = total_requests
            summary["avg_response_time"] = total_response_time / total_requests
            summary["overall_success_rate"] = total_success / total_requests

        # 找出最慢的引擎
        engine_times.sort(key=lambda x: x[1], reverse=True)
        summary["top_slowest_engines"] = [
            {"engine": name, "avg_time": time} for name, time in engine_times[:5]
        ]

        # 找出错误率最高的引擎
        engine_errors.sort(key=lambda x: x[1], reverse=True)
        summary["top_error_prone_engines"] = [
            {"engine": name, "error_rate": rate, "requests": req}
            for name, rate, req in engine_errors[:5]
            if req > 10  # 至少10次请求
        ]

        # 生成优化建议
        summary["recommendations"] = self._generate_recommendations(summary)

        return summary

    def _generate_recommendations(self, summary: dict) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 检查平均响应时间
        if summary["avg_response_time"] > 3.0:
            recommendations.append(
                "系统平均响应时间较高,建议启用缓存机制或优化推理算法"
            )

        # 检查成功率
        if summary["overall_success_rate"] < 0.95:
            recommendations.append(
                "系统成功率较低,建议检查错误日志并修复常见错误"
            )

        # 检查慢速引擎
        slow_engines = summary.get("top_slowest_engines", [])
        if slow_engines and slow_engines[0]["avg_time"] > 5.0:
            recommendations.append(
                f"{slow_engines[0]['engine']}响应时间较慢({slow_engines[0]['avg_time']:.2f}s),建议优化"
            )

        # 检查高错误率引擎
        error_prone = summary.get("top_error_prone_engines", [])
        if error_prone and error_prone[0]["error_rate"] > 0.1:
            recommendations.append(
                f"{error_prone[0]['engine']}错误率较高({error_prone[0]['error_rate']:.1%}),需要排查"
            )

        if not recommendations:
            recommendations.append("系统运行良好,暂无优化建议")

        return recommendations

    def clear_metrics(self, engine_name: Optional[str] = None) -> None:
        """清除指标"""
        if engine_name:
            # 清除特定引擎的指标
            if engine_name in self.engine_data:
                del self.engine_data[engine_name]

            metric_keys = [k for k in self.metrics.keys() if engine_name in k]
            for key in metric_keys:
                self.metrics[key].clear()

            logger.info(f"已清除引擎{engine_name}的指标")
        else:
            # 清除所有指标
            self.engine_data.clear()
            self.metrics.clear()
            logger.info("已清除所有指标")

    def export_metrics(self, format: str = "json") -> str:
        """导出指标"""
        overview = self.get_system_overview()

        if format == "json":
            import json

            return json.dumps(overview, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def register_alert_callback(self, callback: Callable) -> None:
        """注册告警回调函数"""
        self.alert_callbacks.append(callback)
        logger.info(f"注册告警回调函数: {callback.__name__}")


# 全局单例
_performance_monitor_instance: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _performance_monitor_instance
    if _performance_monitor_instance is None:
        _performance_monitor_instance = PerformanceMonitor()

        # 添加默认告警规则
        _performance_monitor_instance.add_alert_rule(
            "avg_response_time",
            "gt",
            5.0,
            AlertSeverity.WARNING,
            "平均响应时间过高",
            "优化推理算法或启用缓存",
        )
        _performance_monitor_instance.add_alert_rule(
            "error_rate",
            "gt",
            0.1,
            AlertSeverity.ERROR,
            "错误率过高",
            "检查错误日志并修复问题",
        )

    return _performance_monitor_instance


# 便捷函数
def record_engine_performance(
    engine_name: str,
    response_time: float,
    success: bool,
    cache_hit: bool = False,
) -> None:
    """记录引擎性能(便捷函数)"""
    monitor = get_performance_monitor()
    monitor.record_engine_call(engine_name, response_time, success, cache_hit)


# 测试代码
if __name__ == "__main__":
    async def test_performance_monitor():
        """测试性能监控"""
        print("=" * 80)
        print("🧪 测试性能监控系统")
        print("=" * 80)

        monitor = get_performance_monitor()
        monitor.start_monitoring()

        # 模拟引擎调用
        engines = ["athena_super", "semantic_v4", "dual_system"]

        for _i in range(10):
            for engine in engines:
                # 模拟响应时间
                import random

                response_time = random.uniform(0.5, 3.0)
                success = random.random() > 0.1  # 90%成功率
                cache_hit = random.random() > 0.7  # 30%缓存命中率

                record_engine_performance(engine, response_time, success, cache_hit)

            await asyncio.sleep(0.1)

        # 等待告警检查
        await asyncio.sleep(2)

        # 获取报告
        print("\n📊 引擎性能报告:")
        for engine in engines:
            report = monitor.get_engine_report(engine)
            print(f"\n{engine}:")
            print(f"  总请求数: {report.total_requests}")
            print(f"  平均响应时间: {report.avg_response_time:.3f}s")
            print(f"  P95响应时间: {report.p95_response_time:.3f}s")
            print(f"  成功率: {report.success_rate:.1%}")

        # 获取摘要
        print("\n📋 性能摘要:")
        summary = monitor.get_performance_summary()
        print(f"  总请求数: {summary['total_requests']}")
        print(f"  平均响应时间: {summary['avg_response_time']:.3f}s")
        print(f"  整体成功率: {summary['overall_success_rate']:.1%}")

        print("\n💡 优化建议:")
        for rec in summary["recommendations"]:
            print(f"  - {rec}")

        monitor.stop_monitoring()

    asyncio.run(test_performance_monitor())
